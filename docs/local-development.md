## Getting Started with Local USKPA Website Development

[:arrow_left: Back to USKPA
Documentation](../docs)

1. Install [Docker]. If you're on OS X, install Docker for Mac. If you're on Windows, install Docker for Windows.

1. Clone this repository and move into the root folder.

1. Build and start the required docker containers:

    ```shell
    $ docker-compose build
    $ docker-compose up
    ```

1. If desired, create a super-user account:

    ```shell
    $ docker-compose run app python manage.py createsuperuser
    ```

1. Visit [http://localhost:8000/] to access the site.


### Running static analysis tools

We run two linting tools in continuous integration,
[`flake8`](http://flake8.pycqa.org/en/latest/) for general linting of unused
variables, style, etc. and [`bandit`](https://pypi.python.org/pypi/bandit), a
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
[18F Docker guide]: https://pages.18f.gov/dev-environment-standardization/virtualization/docker/
