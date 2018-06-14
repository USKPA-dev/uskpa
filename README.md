# USKPA

The United States Kimberley Process Authority (USKPA) is a not-for-profit trade association in the United States formed for the purpose of administering and controlling the usage of U.S. Kimberley Process (KP) certificates for the export of rough diamonds from the U.S.

The USKPA is governed by a Board of Directors and is located in New York City.

## USKPA.org

[![CircleCI](https://circleci.com/gh/USKPA-dev/uskpa.svg?style=svg)](https://circleci.com/gh/USKPA-dev/uskpa)
[![codecov](https://codecov.io/gh/USKPA-dev/uskpa/branch/master/graph/badge.svg)](https://codecov.io/gh/USKPA-dev/uskpa)

This repository hosts the code that powers the uskpa.org website.  A key component of the site is a system that administers the usage of KP certificates.

### Open Source Frameworks

There are limited developer resources on this project; for both development and maintenance.  Thus the aim is to minimize custom code by leveraging as many open source frameworks (i.e. reuse) and their associated default services.  

The project intentionally uses open source frameworks also allows USKPA.org to engage community at large of skilled developers that can contribute to feature enhancements and bug fixes going forward.

The frameworks this site uses are:

**Front end** 
* [Django](https://www.djangoproject.com/) web framework that includes an admin panel for user, group management.
* [U.S. Web Design System](https://designsystem.digital.gov/) that follows [design principles](https://designsystem.digital.gov/design-principles/) that create better experiences for USKPA.org's users.

**Back end** 
* [PostgreSQL](https://www.postgresql.org/) database.

### Hosting and Deployment

The development and production instances of the uskpa.org are hosted on the cloud platform, Heroku. Deployment pipelines (using [CircleCI](https://circleci.com/)) and processes are [documented here](docs/deploy.md).  The deployment pipelines includes automatically running the following checks to preserve quality:
* Static code analysis using [Flake8](http://flake8.pycqa.org/en/latest/#) 
* Vulnerability scans using [Snyk](https://snyk.io/)
* Regression test suite
* Test code coverage using [Codecov](https://codecov.io/)

In addition to Heroku's monitoring, USKPA.org also uses [New Relic](https://newrelic.com/) monitoring  to keep administrators appraised of any operational issues with the site.

### Documentation

Documentation is located wthin in the [docs](docs/) directory.  This documentation includes developer and site administration documentation.  As code changes are introduced, this documentation should be kept up to date to facilitate engagement by future contributors.

### Contributing

See [CONTRIBUTING](CONTRIBUTING.md) for additional information.

## Public domain

This project is in the worldwide [public domain](LICENSE.md). As stated in [CONTRIBUTING](CONTRIBUTING.md):

> This project is in the public domain within the United States, and copyright and related rights in the work worldwide are waived through the [CC0 1.0 Universal public domain dedication](https://creativecommons.org/publicdomain/zero/1.0/).
>
> All contributions to this project will be released under the CC0 dedication. By submitting a pull request, you are agreeing to comply with this waiver of copyright interest.
