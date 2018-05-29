## Application monitoring for the production instance
[:arrow_left: Back to USKPA
Documentation](../docs)

The USKPA website leverages Heroku and [New Relic] (at the [Wayne](https://elements.heroku.com/addons/newrelic#wayne) tier) for application availability and performance monitoring.

As an authenticated administrator of the USKPA site, [New Relic] may be accessed via the Heroku application dashboard.

### What is monitored?

1. New Relic:
    * Availability of the site is provided via a [New Relic]
    synthetics monitor which pings the production site every 30
    minutes. If no response is received, indicating the
    site is unavailable, an email alert is sent to site
    administrators.


This alert may be accessed and configured via the Synthetics->Monitors tab within [New Relic].

[New Relic]: https://newrelic.com/
