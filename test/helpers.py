from nose.tools import *
from mock import MagicMock, patch

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
