[:arrow_left: Back to USKPA
Documentation](../docs)

## Python

The USKPA site uses [Pipenv] to manage development and production dependencies.
In both development and continuous integration, the Python environment is
established with `pipenv install --dev`.

To accommodate third-party tools that do not yet support [Pipenv], [Pipenv] generates a `requirements.txt` file (containing
only production dependencies) and includes it in the repository.

You can update development and production dependencies locally with the following:

```sh
pipenv update --dev
pipenv lock --requirements > requirements.txt
```

This will generate updated `Pipfile`, `Pipfile.lock`, and `requirements.txt` files which must be committed to the git repository.

[Pipenv]: https://docs.pipenv.org/
