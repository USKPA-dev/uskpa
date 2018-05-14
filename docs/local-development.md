## Getting Started with Local USKPA Website Development

[:arrow_left: Back to USKPA
Documentation](../docs)

1. Install [Docker]. If you're on OS X, install Docker for Mac. If you're on Windows, install Docker for Windows.

1. Clone this repository and move into the root folder.

1. Build and start the required docker containers:

    ```shell
    $ docker-compose build
    $ docker-compose up
    $ docker-compose run app python manage.py migrate
    ```

1. Load initial data:

    ```shell
    $ docker-compose run app python manage.py loaddata initial_data.json
    ```
1. If desired, create a super-user account:

    ```shell
    $ docker-compose run app python manage.py createsuperuser
    ```

1. Visit [http://localhost:8000/] to access the site.

### Continuous Integration

We use [CircleCI](https://circleci.com) for continuous integration testing.

On each build, the CI suite will:
1. Execute the project's test suite: `python manage.py test`
1. Execute [flake8] linting: `flake8`
1. Execute [bandit] linting: `bandit -r .`
1. Execute [Pipenv's package vulnerability scan](https://docs.pipenv.org/advanced/#detection-of-security-vulnerabilities): `pipenv check --dev`

The CI suite can be executed locally using the
[CircleCI Local CLI](https://circleci.com/docs/2.0/local-cli/) tool. Once Installed, run from the project's root directory:

```shell
$circleci build
```

### Testing Email functionality

We use [Mailhog](https://github.com/mailhog/MailHog) for testing email
functionality in a development environment.

In development, all outbound email will be intercepted by mailhog and is available
for review at http://localhost:8025

### Running static analysis tools

We run two linting tools in continuous integration,
[flake8] for general linting of unused
variables, style, etc. and [bandit], a
security-focused linter.

To run these within the docker container, run:
```sh
docker-compose run app bandit -r .
docker-compose run app flake8
```

As the repository root is mounted within the docker container,
these tools may also be executed locally.
```sh
pipenv install --dev
pipenv run bandit -r .
pipenv run flake8
```

### Accessing the app container

To run an interactive bash session inside the main app container from where `manage.py` or other commands may be executed:

```shell
docker-compose run app bash
```

[Docker]: https://www.docker.com/
[http://localhost:8000/]: http://localhost:8000/
[flake8]: http://flake8.pycqa.org/en/latest/
[bandit]: https://pypi.python.org/pypi/bandit/


### Change Tracking

We use [django-simple-history](https://github.com/treyhunner/django-simple-history) to record history for **all** models.

- ModelAdmins must be integrated with history.
    - Inherit from `simple_history.admin.SimpleHistoryAdmin`
    - https://django-simple-history.readthedocs.io/en/latest/usage.html#integration-with-django-admin

- Models must be configured to record history.
  - Add a `simple_history.models.HistoricalRecords` field on the model
  - https://django-simple-history.readthedocs.io/en/latest/usage.html#models

- Third party models must be configured to record history.
  - Use `simple_history.register` and `makemigrations`
  - https://django-simple-history.readthedocs.io/en/latest/advanced.html#history-for-a-third-party-model
