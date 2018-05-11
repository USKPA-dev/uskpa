## Deploying the USKPA Website
[:arrow_left: Back to USKPA
Documentation](../docs)

All instances are hosted by [Heroku].

* Development - https://uskpa-dev.herokuapp.com/
* Production - TBD

### Heroku

We use the [Heroku CLI], Heroku dashboard, and Heroku Github
Integration to manage instances and automate releases.

Currently, the [master] branch is deployed to the `Development` environment
on each commit for which the unit test suite executes without error.

Please see the Heroku CLI docs on [deploying with git](https://devcenter.heroku.com/articles/git).

**Note:** Interacting with the specific Heroku Applications
dicussed below is limited to those with the necessary permissions.

### Development
*Heroku app: uskpa-dev*

Deployed via Heroku Github Deploy from the [master] branch.

The staging environment exists to test new releases prior
to their production deployment.

The staging database and application are indepedent of
and share no data with the production instance.

Example of a manual deploy using the [Heroku CLI]:

```shell
$ heroku login
$ heroku git:remote -a uskpa-dev
$ git push heroku master

# If migrations are required
$ heroku run python manage.py migrate
```

### Production
*Heroku app: TBD*

Deployed from: Tagged release

Future host of the production USKPA website.

### Initial Data

The USKPA system depends on several models being populated
to enable a complete environment for both users and adminitrators.

To load this initial data upon release to a new environment we
use functionality provided by Django.

Additional data will be included as development continues.

```shell
$ heroku run python manage.py loaddata initial-data.json
```

### Environment Variables

We leverage Heroku Config variables for instance configuration.

The following variables can be set in Heroku to alter the site's behavior.

Var | Value | Destination
--- | --- | ---
ADMINS | Comma delimited list of email addresses | ``settings.ADMINS``
DEBUG | TRUE | ``settings.DEBUG``


### Email - One time Setup

Additional steps are required to enable outgoing email functionality from a new Heroku instance.

Please see the [Email documentation](email.md) for detailed instructions.

[Heroku]: https://heroku.com
[Heroku CLI]: https://devcenter.heroku.com/articles/heroku-cli
[master]: https://github.com/18F/uskpa/tree/master
