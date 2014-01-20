# collectd-cdn_fastly

Fastly CDN plugin for collectd.

## Configuration

```xml
<LoadPlugin python>
  Globals true
</LoadPlugin>

<Plugin python>
  ModulePath "/usr/lib/collectd/python"
  Import "cdn_fastly"

  <Module cdn_fastly>
    ApiKey "68b329da9893e34099c7d8ad5cb9c940"

    <Service "www">
      Id "6IqS8vK4QRMAlb1ByyjrJF"
    </Service>
    <Service "assets">
      Id "qd8G3pOP2nGw0UlSE04t8v
    </Service>
  </Module>
</Plugin>
```
