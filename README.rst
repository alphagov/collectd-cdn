collectd_cdn
============

CDN stats plugin(s) for collectd.

Fastly
------

.. code:: xml

    <LoadPlugin python>
      Globals true
    </LoadPlugin>

    <Plugin python>
      Import "collectd_cdn.fastly"

      <Module "collectd_cdn.fastly">
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
