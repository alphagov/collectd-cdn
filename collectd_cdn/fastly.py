#!/usr/bin/env python
"""
Read plugin for Fastly CDN stats.

TODO:
    - Track last query date so that we can fill in blanks?
"""

import collectd
import json
import time
import requests
import cookielib
import datetime
import calendar
import fastly

# Must be rounded to 1min because that's the highest resolution that Fastly
# provide data for. collectd will only call the plugin this often.
# Ref: http://docs.fastly.com/api/stats#Range
INTERVAL = 60

class CdnFastly(object):
    def __init__(self):
        self.LOGIN_URL = "https://api.fastly.com/login"
        self.STATS_URL = "https://api.fastly.com/stats/service/%(service_id)s"
        self.PLUGIN_NAME = "cdn_fastly"
        self.COOKIE_EXPIRE = 15

        self.delay_mins = 10
        self.api_timeout = 5
        self.api_key = None
        self.api_user = None
        self.api_pass = None
        self.session = requests.Session()
        self.services = {}

    def _warn(self, message):
        collectd.warning("cdn_fastly plugin: %s" % message)

    def _raise(self, message):
        raise Exception("cdn_fastly plugin: %s" % message)

    def _now(self):
        return datetime.datetime.now()

    def config(self, conf):
        """
        Configure the plugin.
        """
        # Reset any previously configured services.
        self.services = {}
        # Reset session (incl. authentication)
        self.session = requests.Session()

        for node in conf.children:
            if node.key == 'ApiUser':
                self.api_user = node.values[0]
            elif node.key == 'ApiPass':
                self.api_pass = node.values[0]
            elif node.key == 'ApiTimeout':
                self.api_timeout = int(node.values[0])
            elif node.key == 'DelayMins':
                self.delay_mins = int(node.values[0])
            elif node.key == 'Service':
                s_name, s_id = (None, None)
                for s_node in node.children:
                    if s_node.key == 'Name':
                        s_name = s_node.values[0]
                    elif s_node.key == 'Id':
                        s_id = s_node.values[0]
                    else:
                        self._warn("Unknown config key: %s" % node.key)
                if not (s_name and s_id):
                    self._raise("Invalid 'Service' config")
                self.services[s_name] = s_id
            else:
                self._warn("Unknown config key: %s" % node.key)

        if not (self.api_user or self.api_pass):
            self._raise("No username or password supplied")

        if (self.api_key and (self.api_user or self.api_pass)):
            self._raise("API key auth is no longer supported. Use username and password.")

        if len(self.services) < 1:
            self._raise("No Service blocks configured")

    def read(self):
        """
        Fetch and submit data. Called once per INTERVAL.
        """
        time_from, time_to = self.get_time_range()

        for service_name, service_id in self.services.items():
            try:
                service_data = self.request(service_id, time_from, time_to)
            except:
                self._warn("Failed to query service: %s" % service_name)
                continue

            for service_period in service_data:
                vtime = service_period.pop('start_time')
                del service_period['service_id']

                for key, val in service_period.items():
                    val, vtype = self.scale_and_type(key, val)
                    self.submit(service_name, key, vtype, val, vtime)

    def scale_and_type(self, key, val):
        """
        Find the appropriate data type and scale the value by INTERVAL
        where required.

        Ref: http://collectd.org/documentation/manpages/types.db.5.shtml
        """
        if key.endswith('_time'):
            vtype = 'response_time'
        elif key.endswith('_ratio'):
            vtype = 'cache_ratio'
            val = float(val)
        elif key.endswith('_size') or key == 'bandwidth':
            vtype = 'bytes'
            val = val / INTERVAL
        else:
            vtype = 'requests'
            val = val / INTERVAL

        return val, vtype

    def get_time_range(self):
        """
        Construct a time range for which to query stats for.

        This is called once per `self.read()` so that we query the same time
        period for all services consistently no matter how long the request
        takes.

        A delay of `self.delay_mins` is applied because Fastly's data from
        edge is 10~15 mins behind the present time.

        Ref: http://docs.fastly.com/api/stats#Availability
        """
        # Timestamp rounded down to the minute.
        now = calendar.timegm(
            self._now().replace(
                second=0, microsecond=0
            ).utctimetuple()
        )

        time_to = now - (self.delay_mins * 60)
        time_from = time_to - INTERVAL

        return time_from, time_to

    def submit(self, service_name, metric_name, metric_type, value, time):
        """
        Submit a single metric with the appropriate properties.
        """
        v = collectd.Values()
        v.plugin = self.PLUGIN_NAME
        v.plugin_instance = service_name

        v.type = metric_type
        v.type_instance = metric_name

        v.time = time
        v.values = [value, ]
        v.interval = INTERVAL

        v.dispatch()

    def auth(self):
        """
        Setup authentication headers or cookies for the session.
        """

        if self.api_user and self.api_pass:
            # Force a new cookie if it's going to expire soon.
            valid_until = time.time() + self.COOKIE_EXPIRE
            valid_cookies = [
                c for c in self.session.cookies
                if not c.is_expired(valid_until)
            ]

            if len(valid_cookies) < 1:
                payload = {
                    'user': self.api_user,
                    'password': self.api_pass,
                }
                resp = self.session.post(
                    self.LOGIN_URL,
                    data=payload,
                    timeout=self.api_timeout
                )
                if resp.status_code != 200:
                    self._raise("Non-200 response from /login")

            return

        if self.api_user:
          self._raise("No username specified")
        return

        if self.api_password:
          self._raise("No password specified")
        return

    def request(self, service_id, time_from, time_to):
        """
        Requests stats from Fastly's API and return a dict of data. May
        contain multiple time periods.
        """
        params = {
            'from': time_from,
            'to': time_to,
            'by': "minute",
        }
        url = self.STATS_URL % {
            'service_id': service_id,
        }
        headers = {
            'Fastly-Key': self.api_key,
        }

        self.auth()
        resp = self.session.get(
            url,
            params=params,
            timeout=self.api_timeout
        )
        if resp.status_code != 200:
            self._raise("Non-200 response")

        data = resp.json()['data']
        return data

cdn_fastly = CdnFastly()
collectd.register_config(cdn_fastly.config)
collectd.register_read(cdn_fastly.read, INTERVAL)
