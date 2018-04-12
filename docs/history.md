## Change Tracking and Data Lineage

[:arrow_left: Back to USKPA
Documentation](../docs)

The USKPA website maintains a record of each insert,
update, or deletion made to the database from within the application.

This information is preserved to aid discrepancy resolution and data analysis. Should the need arise, it also allows us to roll-back data to previous values.

As a user, your website experience will not be impacted.

### For Developers

We use [django-simple-history](https://github.com/treyhunner/django-simple-history), please see [change tracking](./local-development.md#change-tracking) in the development documentation for additional details.
