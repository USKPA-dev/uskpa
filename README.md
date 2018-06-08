# USKPA

The United States Kimberley Process Authority (USKPA) is a not-for-profit trade association in the United States formed for the purpose of administering and controlling the usage of U.S. Kimberley Process (KP) certificates for the export of rough diamonds from the U.S.

The USKPA is governed by a Board of Directors and is located in New York City.

## USKPA.org

[![CircleCI](https://circleci.com/gh/USKPA-dev/uskpa.svg?style=svg)](https://circleci.com/gh/USKPA-dev/uskpa)
[![codecov](https://codecov.io/gh/USKPA-dev/uskpa/branch/master/graph/badge.svg)](https://codecov.io/gh/USKPA-dev/uskpa)

This repository hosts the code that powers the uskpa.org website.  A key component of the site is a system that administers the usage of KP certificates.

### Frameworks

Uskpa.org uses the [Django](https://www.djangoproject.com/) web framework along with a PostgreSQL(https://www.postgresql.org/) backend.  Given the limited developer resources on this project, the aim is to leverage the default services from these frameworks (for example: the Django admin panel) and minimize custom code.

### Hosting

The development and production instances of the uskpa.org are hosted on the cloud platform, Heroku. Deployment pipelines and processes are [documented here](docs/deploy.md).

### Documentation

Documentation is located wthin in the [docs](docs/) directory.  This documentation includes developer and site administration documentation.

### Contributing

See [CONTRIBUTING](CONTRIBUTING.md) for additional information.

## Public domain

This project is in the worldwide [public domain](LICENSE.md). As stated in [CONTRIBUTING](CONTRIBUTING.md):

> This project is in the public domain within the United States, and copyright and related rights in the work worldwide are waived through the [CC0 1.0 Universal public domain dedication](https://creativecommons.org/publicdomain/zero/1.0/).
>
> All contributions to this project will be released under the CC0 dedication. By submitting a pull request, you are agreeing to comply with this waiver of copyright interest.
