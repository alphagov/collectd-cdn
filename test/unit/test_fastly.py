from ..helpers import *

class TestFastly(object):
    def setup(self):
        self.collectd = MagicMock()
        self.modules = patch.dict('sys.modules', {'collectd': self.collectd})
        self.modules.start()

        from collectd_cdn import fastly
        self.fastly = fastly.CdnFastly()

    def teardown(self):
        self.modules.stop()

    def test_config_all_valid_options(self):
        config = CollectdConfig('root', (), (
            ('ApiKey', 'abc123', ()),
            ('ApiTimeout', 13, ()),
            ('DelayMins', 17, ()),
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

    def test_config_no_apikey(self):
        config = CollectdConfig('root', (), (
            ('Service', (), (
                ('Name', 'one', ()),
                ('Id', '111', ()),
            )),
        ))
        assert_raises(Exception, self.fastly.config, config)

    def test_config_no_services(self):
        config = CollectdConfig('root', (), (
            ('ApiKey', 'abc123', ()),
        ))
        assert_raises(Exception, self.fastly.config, config)

    @patch('collectd_cdn.fastly.collectd.warning')
    def test_config_unknown_key(self, warning_mock):
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
