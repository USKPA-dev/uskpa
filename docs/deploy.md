## Deploying the USKPA Website
[:arrow_left: Back to USKPA
Documentation](../docs)

Two instances of the USKPA website are hosted by [Heroku].

* Staging - https://uskpa-staging.herokuapp.com/
* Production - https://uskpa.herokuapp.com/

### Heroku

At this early stage we're using the [Heroku CLI]
to manage all user-facing instances of the application. In the future we
will transition to automated deployments via continuous integration.

Please see the Heroku CLI docs on [deploying with git](https://devcenter.heroku.com/articles/git).

**Note:** Interacting with the specific Heroku Applications
dicussed below is limited to those with the necessary permissions.

### Staging
*Heroku app: uskpa-staging*

Deployed from: [master](https://github.com/18F/uskpa/tree/master)

The staging environment exists to test new releases prior
to their production deployment.

The staging database and application are indepedent of
and share no data with the production instance.

Example using the [Heroku CLI]:

```shell
$ heroku login
$ heroku git:remote -a uskpa-staging
$ git push heroku master

# If migrations are required
$ heroku run python manage.py migrate
```

### Production
*Heroku app: uskpa*

Deployed from: Tagged release

Future host of the production USKPA website.

[Heroku]: https://heroku.com
[Heroku CLI]: https://devcenter.heroku.com/articles/heroku-cli
