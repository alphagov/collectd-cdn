from ..helpers import *

import json
import copy
import datetime

class TestFastly(object):
    def setup(self):
        self.collectd = MagicMock()
        self.modules = patch.dict('sys.modules', {'collectd': self.collectd})
        self.modules.start()

        from collectd_cdn import fastly
        self.fastly = fastly.CdnFastly()

    def teardown(self):
        self.modules.stop()


class TestConfig(TestFastly):
    def test_all_valid_ints_as_strings(self):
        config = CollectdConfig('root', (), (
            ('ApiKey', 'abc123', ()),
            ('ApiTimeout', '13', ()),
            ('DelayMins', '17', ()),
            ('Service', (), (
                ('Name', 'one', ()),
                ('Id', '111', ()),
            )),
            ('Service', (), (
                ('Name', 'two', ()),
                ('Id', '222', ()),
            )),
        ))
        self.fastly.config(config)

        assert_equal(self.fastly.api_key, 'abc123')
        assert_equal(self.fastly.api_timeout, 13)
        assert_equal(self.fastly.delay_mins, 17)
        assert_equal(self.fastly.services, {
            'one': '111',
            'two': '222',
        })

    def test_service_reconfig(self):
        config = CollectdConfig('root', (), (
            ('ApiKey', 'abc123', ()),
            ('Service', (), (
                ('Name', 'one', ()),
                ('Id', '111', ()),
            )),
        ))
        self.fastly.config(config)
        assert_equal(self.fastly.services, { 'one': '111' })

        config = CollectdConfig('root', (), (
            ('ApiKey', 'abc123', ()),
            ('Service', (), (
                ('Name', 'two', ()),
                ('Id', '222', ()),
            )),
        ))
        self.fastly.config(config)
        assert_equal(self.fastly.services, { 'two': '222' })

    def test_apikey(self):
        config = CollectdConfig('root', (), (
            ('ApiKey', 'abc123', ()),
            ('Service', (), (
                ('Name', 'one', ()),
                ('Id', '111', ()),
            )),
        ))
        self.fastly.config(config)

        assert_equal(self.fastly.api_key, 'abc123')

    def test_apiuser_and_apipass(self):
        config = CollectdConfig('root', (), (
            ('ApiUser', 'abc', ()),
            ('ApiPass', '123', ()),
            ('Service', (), (
                ('Name', 'one', ()),
                ('Id', '111', ()),
            )),
        ))
        self.fastly.config(config)

        assert_equal(self.fastly.api_user, 'abc')
        assert_equal(self.fastly.api_pass, '123')

    def test_apiuser_no_apipass(self):
        config = CollectdConfig('root', (), (
            ('ApiUser', 'abc', ()),
            ('Service', (), (
                ('Name', 'one', ()),
                ('Id', '111', ()),
            )),
        ))
        assert_raises(Exception, self.fastly.config, config)

    def test_apipass_no_apiuser(self):
        config = CollectdConfig('root', (), (
            ('ApiPass', '123', ()),
            ('Service', (), (
                ('Name', 'one', ()),
                ('Id', '111', ()),
            )),
        ))
        assert_raises(Exception, self.fastly.config, config)

    def test_no_credentials(self):
        config = CollectdConfig('root', (), (
            ('Service', (), (
                ('Name', 'one', ()),
                ('Id', '111', ()),
            )),
        ))
        assert_raises(Exception, self.fastly.config, config)

    def test_all_credentials(self):
        config = CollectdConfig('root', (), (
            ('ApiKey', 'abc123', ()),
            ('ApiUser', 'abc', ()),
            ('ApiPass', '123', ()),
            ('Service', (), (
                ('Name', 'one', ()),
                ('Id', '111', ()),
            )),
        ))
        assert_raises(Exception, self.fastly.config, config)

    def test_no_services(self):
        config = CollectdConfig('root', (), (
            ('ApiKey', 'abc123', ()),
        ))
        assert_raises(Exception, self.fastly.config, config)

    @patch('collectd_cdn.fastly.collectd.warning')
    def test_unknown_key(self, warning_mock):
        config = CollectdConfig('root', (), (
            ('Zebra', 'stripes', ()),
            ('ApiKey', 'abc123', ()),
            ('Service', (), (
                ('Name', 'one', ()),
                ('Id', '111', ()),
            )),
        ))
        self.fastly.config(config)
        warning_mock.assert_called_with("cdn_fastly plugin: Unknown config key: Zebra")


class TestScaleAndType(TestFastly):
    def test_time(self):
        v, t = self.fastly.scale_and_type('hits_time', 946.1020896459992)
        assert_equal(v, 946.1020896459992)
        assert_equal(t, 'response_time')

    def test_ratio(self):
        v, t = self.fastly.scale_and_type('hit_ratio', '0.9836E0')
        assert_equal(v, 0.9836)
        assert_equal(t, 'cache_ratio')

    def test_size(self):
        v, t = self.fastly.scale_and_type('body_size', 219004331934)
        # FIXME: Should be float 3650072198.9 ?
        assert_equal(v, 3650072198)
        assert_equal(t, 'bytes')

    def test_other(self):
        v, t = self.fastly.scale_and_type('status_2xx', 11152796)
        # FIXME: Should be float 185879.93333333332 ?
        assert_equal(v, 185879)
        assert_equal(t, 'requests')


class TestGetTimeRange(TestFastly):
    @patch('collectd_cdn.fastly.CdnFastly._now')
    def test_delay(self, now_mock):
        self.fastly.delay_mins = 30

        now_mock.return_value = datetime.datetime(2014, 2, 1, 12, 30, 0, 0)
        t_from, t_to = self.fastly.get_time_range()
        t_to = datetime.datetime.fromtimestamp(t_to)
        t_from = datetime.datetime.fromtimestamp(t_from)

        assert_equal(t_to, datetime.datetime(2014, 2, 1, 12, 0, 0, 0))
        assert_equal(t_from, datetime.datetime(2014, 2, 1, 11, 59, 0, 0))

    @patch('collectd_cdn.fastly.CdnFastly._now')
    def test_round_down(self, now_mock):
        now_mock.return_value = datetime.datetime(2014, 2, 1, 12, 13, 14, 15)
        t_from, t_to = self.fastly.get_time_range()
        t_to = datetime.datetime.fromtimestamp(t_to)
        t_from = datetime.datetime.fromtimestamp(t_from)

        assert_equal(t_to, datetime.datetime(2014, 2, 1, 12, 3, 0, 0))
        assert_equal(t_from, datetime.datetime(2014, 2, 1, 12, 2, 0, 0))


class TestRequest(TestFastly):
    def __init__(self):
        self.MOCK_LOGIN_URL = "https://api.fastly.com/login"
        self.MOCK_STATS_URL = "https://api.fastly.com/stats/service/mocked"

    @httpretty.activate
    def test_request_invalid_response(self):
        httpretty.register_uri(
            httpretty.GET,
            self.MOCK_STATS_URL,
            body='',
            status=500
        )

        assert_raises(Exception, self.fastly.request, 'mocked', 1, 2)

    @httpretty.activate
    def test_request_service_and_range(self):
        httpretty.register_uri(
            httpretty.GET,
            self.MOCK_STATS_URL,
            body='{"data": {}}'
        )

        self.fastly.api_key = 'abc123'
        self.fastly.request('mocked', 1390320360, 1390320420)

        assert_equal(httpretty.last_request().querystring, {
            'by': ['minute'],
            'to': ['1390320420'],
            'from': ['1390320360'],
        })

    @httpretty.activate
    def test_request_api_key(self):
        httpretty.register_uri(
            httpretty.GET,
            self.MOCK_STATS_URL,
            body='{"data": {}}'
        )

        self.fastly.api_key = 'abc123'
        self.fastly.request('mocked', 1, 2)

        assert_equal(httpretty.last_request().headers.get('Fastly-Key'), 'abc123')

    @httpretty.activate
    def test_request_user_pass_login_once(self):
        cookie = fastly_cookie('just-one')
        expected_cookie = 'fastly.session=just-one'

        httpretty.register_uri(
            httpretty.POST,
            self.MOCK_LOGIN_URL,
            responses=[
                httpretty.Response(
                    body='{"user": {}}', status=200,
                    adding_headers={ 'Set-Cookie': cookie }),
                httpretty.Response(
                    body='should not be called',
                    status=400),
            ]
        )
        httpretty.register_uri(
            httpretty.GET,
            self.MOCK_STATS_URL,
            body='{"data": {}}'
        )

        self.fastly.api_user = 'abc'
        self.fastly.api_pass = '123'
        self.fastly.request('mocked', 1, 2)
        assert_equal(httpretty.last_request().headers.get('Cookie'), expected_cookie)

        self.fastly.request('mocked', 3, 4)
        assert_equal(httpretty.last_request().headers.get('Cookie'), expected_cookie)

    @httpretty.activate
    def test_request_user_pass_cookie_expiring_15secs(self):
        short_cookie = fastly_cookie('short', 10)
        long_cookie  = fastly_cookie('long', 30)

        httpretty.register_uri(
            httpretty.POST,
            self.MOCK_LOGIN_URL,
            responses=[
                httpretty.Response(
                    body='{"user": {}}', status=200,
                    adding_headers={ 'Set-Cookie': short_cookie }),
                httpretty.Response(
                    body='{"user": {}}', status=200,
                    adding_headers={ 'Set-Cookie': long_cookie }),
                httpretty.Response(
                    body='should not be called',
                    status=400),
            ]
        )
        httpretty.register_uri(
            httpretty.GET,
            self.MOCK_STATS_URL,
            body='{"data": {}}'
        )

        self.fastly.api_user = 'abc'
        self.fastly.api_pass = '123'
        self.fastly.request('mocked', 1, 2)
        assert_equal(
            httpretty.last_request().headers.get('Cookie'),
            'fastly.session=short'
        )

        self.fastly.request('mocked', 3, 4)
        assert_equal(
            httpretty.last_request().headers.get('Cookie'),
            'fastly.session=long'
        )

        self.fastly.request('mocked', 5, 6)
        assert_equal(
            httpretty.last_request().headers.get('Cookie'),
            'fastly.session=long'
        )

    @httpretty.activate
    def test_response_json(self):
        fixture_json = fixture('api_response.json')
        fixture_data = json.loads(fixture_json)['data']

        httpretty.register_uri(
            httpretty.GET,
            self.MOCK_STATS_URL,
            body=fixture_json
        )

        self.fastly.api_key = 'abc123'
        t_from, t_to = self.fastly.get_time_range()
        resp_json = self.fastly.request('mocked', t_from, t_to)

        assert_equal(resp_json, fixture_data)


class TestRead(TestFastly):
    @patch('collectd_cdn.fastly.CdnFastly.get_time_range')
    @patch('collectd_cdn.fastly.CdnFastly.request')
    @patch('collectd_cdn.fastly.CdnFastly.submit')
    @patch('collectd_cdn.fastly.collectd.warning')
    def test_three_services_one_error(self, warn_mock, submit_mock, req_mock, range_mock):
        self.fastly.services = {
            'one': '111',
            'two': '222',
            'three': '333',
        }

        range_mock.return_value = (1390320360, 1390320420)
        fixture_data = json.loads(fixture('simple_service.json'))
        req_mock.side_effect = [
            copy.deepcopy(fixture_data),
            ValueError("No JSON object could be decoded"),
            copy.deepcopy(fixture_data),
        ]

        self.fastly.read()

        req_calls = [
            call('111', *range_mock),
            call('222', *range_mock),
            call('333', *range_mock),
        ]
        submit_calls = [
            call('three', 'hits', 'requests', 777, 1390320360),
            call('three', 'hits_time', 'response_time', 3.5722524239999993, 1390320360),
            call('one', 'hits', 'requests', 777, 1390320360),
            call('one', 'hits_time', 'response_time', 3.5722524239999993, 1390320360),
        ]

        assert_equal(req_mock.call_count, len(req_calls))
        submit_mock.assert_has_calls(submit_calls)
        assert_equal(submit_mock.call_count, len(submit_calls))
        warn_mock.assert_called_with("cdn_fastly plugin: Failed to query service: two")
