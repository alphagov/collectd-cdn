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
