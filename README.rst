collectd_cdn
============

.. image:: https://travis-ci.org/gds-operations/collectd-cdn.svg?branch=master
    :target: https://travis-ci.org/gds-operations/collectd-cdn

A collectd plugin to fetch edge stats from CDN vendors. So that you can
store and graph them to your heart's content.

Installation
------------

The latest stable version can be installed from PyPI_. Either by hand:

.. code:: shell

    $ pip install collectd-cdn

Or configuration management, such as Puppet:

.. code:: puppet

    package { 'collectd-cdn':
      ensure   => present,
      provider => 'pip',
    }

.. _PyPI: https://pypi.python.org/pypi

Vendors
-------

A single CDN vendor is currently supported.

Fastly
~~~~~~

To configure the plugin:

.. code:: xml

    <LoadPlugin python>
      Globals true
    </LoadPlugin>

    <Plugin python>
      Import "collectd_cdn.fastly"

      <Module "collectd_cdn.fastly">
        # Authenticate using user/pass (recommended)
        ApiUser "user@example.com"
        ApiPass "password"

        # OR using an API key
        ApiKey "68b329da9893e34099c7d8ad5cb9c940"

        <Service>
          Name "www"
          Id "6IqS8vK4QRMAlb1ByyjrJF"
        </Service>
        <Service>
          Name "assets"
          Id "qd8G3pOP2nGw0UlSE04t8v"
        </Service>
      </Module>
    </Plugin>

The highest resolution of data that Fastly provide is per-minute. So you'll
need to configure your storage, such as Graphite's Carbon_, with a retention
rate to match:

.. code:: ini

    [cdn_fastly]
    pattern = ^[^.]+\.cdn_fastly-.+\.
    retentions = 1m:31d,…

.. _Carbon: http://graphite.readthedocs.org/en/0.9.x/config-carbon.html#storage-schemas-conf
