## Email

[:arrow_left: Back to USKPA
Documentation](../docs)

The USKPA website relies on email for account
registration and notifications to users.

Heroku add-ons and the [django-anymail](https://anymail.readthedocs.io/en/stable/) package are leveraged to provide
this functionality in production and staging environments.


### SendGrid

We default to using the [SendGrid Add-on]([https://elements.heroku.com/addons/sendgrid)
and its free [starter tier] of service.

The [starter tier] provides up to 12,000 emails per month, ~394/day. This is expected to provide ample
volume for both development and a production instance during normal operation.

[starter tier]: https://elements.heroku.com/addons/sendgrid#starter


### Configuration

A few one-time steps are required to set-up email functionality on a newly deployed Heroku instance.

**Prerequisite**:
Heroku requires account verification
prior to add-on installation. A payment method must be added to the account associated with the Heroku instance being deployed.


1. Add the SendGrid [starter tier] add-on
    * This can be done via the Heroku dashboard
    * Or the command line:
        ```shell
        $ heroku addons:create sendgrid:starter
        ```
2. Follow the Heroku instructions to create and set a `SENDGRID_API_KEY` value in the deployed application.
    * https://devcenter.heroku.com/articles/sendgrid#obtaining-an-api-key
    * https://devcenter.heroku.com/articles/sendgrid#setup-api-key-environment-variable

3. Set additional environment variables via the Heroku CLI or Dashboard:
    ```shell
    DJANGO_EMAIL_BACKEND=anymail.backends.sendgrid.EmailBackend
    DJANGO_FROM_EMAIL=
    DJANGO_EMAIL_SUBJECT_PREFIX=
    ```
    `DJANGO_FROM_EMAIL` - Defaults to `CONTACT_US` value as configured in environment. Will be the address which recipients see on the `FROM` line of incoming emails. It should be set to a monitored inbox unless reply instructions are included within the message.

    `DJANGO_EMAIL_SUBJECT_PREFIX` helps differentiate deployed instances when the system generates emails to site administrators and should be set to the name of the Heroku instance.

### Cost

Mail volume in excess of 12,000 emails a month is not anticipated.

Should the need arise
* The SendGrid add-on can be upgraded to a paid tier providing additional volume.
* Another email add-on can be selected and configured.

