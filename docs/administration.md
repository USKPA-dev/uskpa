## Administration of USKPA.org
[:arrow_left: Back to USKPA
Documentation](../docs)

All of the following tasks require an authorized user account, with `is_superuser` and `is_staff` set to `True`.

# Common administration tasks

## Add a new user
1. Access the django admin page via the `Admin` navigation link.
2. Follow the `+ Add` link for `Users`
3. Enter in the desired `Email Address` and `Username`
    * Recommended that email address and username be identical and lowercase.
4. New user will receive a notification email at the specified address containing a link to set their password and login.

## Add a licensee
1. Access the django admin page via the `Admin` navigation link.
2. Follow the `+ Add` link for `Licensees`
3. Enter all required fields for the new licensee and click save.

## Add a user as a contact for a licensee
Contacts for a given licensee are able to view,
prepare, update, and void all certificates, associated
with that licensee.

1. Access the django admin page via the `Admin` navigation link.
2. Follow the link for `Licensees`
3. Select the desired licensee from the listing of `Licensees`.
4. Select the desired user from the list of `Available Contacts` and save
5. Save

## Deactivate/disable a user account
Should a user no longer require access to the site,
their account should be _disabled_, not _deleted_, from the database.

1. Access the django admin page via the `Admin` navigation link.
2. Follow the link for `Users`
3. Select the desired user from the listing of `Users`.
4. Un-check `Active`
5. Save

## Deactivate/disable a licensee
Should a licensee no longer require access to the site,
their account should be _disabled_, not _deleted_, from the database.

1. Access the django admin page via the `Admin` navigation link.
2. Follow the link for `Licensees`
3. Click on the desired licensee from the listing of `Users`.
4. Uncheck `Is active`
5. Save

Contacts associated to a disabled licensee will still be able to access the site, but will not see any certificates.

## Add a user as an Auditor
Auditors have access to all certificate data
but are unable to make modifications.

1. Access the django admin page via the `Admin` navigation link.
2. Follow the link for `Users`
3. Select the desired user from the listing of `Users`.
4. Select the `Auditor` group under the `Available groups` field
5. Save

## Add a user as a Reviewer
Reviewers have access to all certificate data and certificate
edit requests and are able to approve or reject those edit requests.

1. Access the django admin page via the `Admin` navigation link.
2. Follow the link for `Users`
3. Select the desired user from the listing of `Users`.
4. Select the `Reviewer` group under the `Available groups` field
5. Save

**Note:** Edit requests must be enabled under KPC/Certificate Configuration/Certificate Edit Requests to allow licensees to submit edit requests.

## Add a user as a Administrator/Superuser
Administrators have unrestricted access to the site and are able to
view and modify any certificate, licensee, user, etc. They also
have full access to the Django admin panel allowing them to modify
the configuration of the site and its behavior.

1. Access the django admin page via the `Admin` navigation link.
2. Follow the link for `Users`
3. Select the desired user from the listing of `Users`.
4. Check the `Staff status` and `Superuser status` boxes.
5. Save

## Configuring KP Certificate values
Certain fields associated to KP certificates allow only a specific set of values:

1. Harmonized System Codes
2. Ports of export
3. Void reasons
4. Certificate Configuration - Days to expiry
5. Certificate Configuration - Price
6. Certificate Configuration - KP Countries (used for Country of Origin and Addresses)

An administrator can configure the allowed values for each of these fields via the admin panel.

## Avoid using the admin panel to edit the following:

1. Certificates - Have licensees submit edit requests to keep an audit trail of requests.
2. Receipts - Use `View on site` link to render the receipt.
3. Edit requests - Have reviewers approve / reject requests from the site to keep an audit trail of approvals.
