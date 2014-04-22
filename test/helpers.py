from nose.tools import *
from mock import MagicMock, patch, call

import os
import Cookie
import datetime
import httpretty

HERE = os.path.dirname(__file__)

def fixture(name):
    return open(os.path.join(HERE, 'fixtures', name)).read()

def fastly_cookie(value, period=300):
    c = Cookie.SimpleCookie()
    c['fastly.session'] = value
    sc = c['fastly.session']

    expires = datetime.datetime.utcnow() + datetime.timedelta(seconds=period)
    sc['Expires'] = expires.strftime("%a, %d %b %Y %H:%M:%S GMT")
    sc['Path'] = '/'
    sc['secure'] = True
    sc['HttpOnly'] = True

    return sc.OutputString()

class CollectdConfig(object):
    """
    Quacks like collectd Config object.
    """
    def __init__(self, key, vals, children):
        self.key = key
        self.values = (vals,)
        self.children = [
            CollectdConfig(k,v,c)
            for k,v,c in children
        ]
