## Workflow for updating the USKPA website
[:arrow_left: Back to USKPA
Documentation](../docs)

This is only relevant to USKPA administrators who wish
to modify a deployed instance of the website.

### Git

All changes to the USKPA website must be performed
via commits to this Git repository.

Changing the USKPA website requires a basic knowledge of Github commits, branching and merging.

For a brief introduction to these topics: https://services.github.com/on-demand/intro-to-github/

### Workflow

We recommend a simplified Git Flow approach for all changes:

1. Create a new branch from [master]
2. Commit changes to new branch
3. Create pull request to merge into master
4. Review changes, deploying to a non-production Heroku instance for testing if desired.
5. Ensure test suite passes
6. Approve merge request and merge into master


### Presented below is a basic workflow for modifying the USKPA website.

For this example, we would like to update the `About Us` text on the homepage.

#### Making changes

1. Create a new branch from `master`, for this example lets call it `update-about-us`.
2. Locate the code which requires updating.
    *  [../kpc/templates/home.html](../kpc/templates/home.html) in this case.
3. Make our desired changes and commit them to `update-about-us`.
4. Create a Pull Request to merge `update-about-us` into `master`
5. Review changes and ensure test suite passes
6. Approve request and merge into `master`


#### Deploying changes

**Note**: The deploy process herein is for low-impact, largely, cosmetic changes to the website. Changes requiring
structural modification of the production database
are not covered here.

A two step release process is recommended to minimize the potential impact
to the production instance resulting from unexpected errors stemming from a
code change.

1. Automated deploy to `uskpa-dev`
    * Once the `update-about-us` branch has been merged into `master`
    the test suite will be automatically executed via [CircleCI].
    * Upon successful execution of the test suite, the `master` branch will be
    automatically deployed to the `uskpa-dev` Heroku instance.

At this point in the work-flow we **highly recommend** accessing the development
instance at https://uskpa-dev.herokuapp.com and confirming your change behaves and appears as expected.

2. Manually deploy `master` to `uskpa-prod`
    * Accessible via the `Manual Deploy` section of the Heroku dashboard `Deploy` tab
    * Heroku will retrieve and build the application.
    * If the build is successful, the updated application will be deployed at `uskpa-prod`


#### Troubleshooting


1. The checks on my pull request are failing.

    a. Examine the output for each `check`. Detailed output is provided which will assist in identifying
    the root cause of the issue.

[CircleCI]: https://circleci.com/
