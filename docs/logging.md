## Logging for the production instance
[:arrow_left: Back to USKPA
Documentation](../docs)

The USKPA website leverages Heroku and Django's provided
logging functionality to capture platform and website activity along with selected application events of interest.


### What is logged?

  1. Django Application logs:
      * Certificate status change actions
      * Certificate void actions
      * User login events
      * User logout events
      * Failed user login events
      * Server start-up events
      * All HTTP requests
  2. Heroku system and add-on logs:
      * https://devcenter.heroku.com/articles/logging


### Where is it logged?

Upon release, the USKPA site utilizes [Papertrail] add-on at the [Choklad](https://elements.heroku.com/addons/papertrail#choklad) tier.

As an authenticated administrator of the USKPA site, [Papertrail] may be accessed via the Heroku application dashboard.

### Logging Alerts

  [Papertrail] Alerts have been configured to notify site administrators upon the detection of an `ERROR` log message produced by the application.

  At release time, the logs are scanned every 10 minutes for new errors.

  This alert is accessible and configurable via the alerts tab within [Papertrail].

[Papertrail]: https://papertrailapp.com/
