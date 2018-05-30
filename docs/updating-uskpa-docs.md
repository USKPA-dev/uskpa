## Application monitoring for the production instance
[:arrow_left: Back to USKPA
Documentation](../docs)

This is only relevant to administrators of the USKPA site.

### IRS Form 990
The USKPA, being a non-profit organization, files an IRS Form 990 every year.  To meet the requirement in making these documents available to the public, the last 3 years of filings are posted to the uskpa.org site.  As such, each year the site needs to include the new filings. This change, along with all others to the site, must be committed to this
git repository. Please see the [change workflow](./change-workflow.md).


To facilitate updating IRS Form 990 documents, the USKPA site renders links to any documents within the
[../static/uskpa_documents/irs](../static/uskpa_documents/irs)
folder on the homepage under the heading `IRS Form 990`.

To *add* a new IRS Form 990 document:
  * Following the [change workflow], ADD the desired pdf file within the `../static/uskpa_documents/irs` folder.

To *remove* an existing IRS Form 990 document:
  * Following the [change workflow], DELETE the desired pdf file from the `../static/uskpa_documents/irs` folder.

To *modify* an existing IRS Form 990 document:
  * Following the [change workflow], REPLACE the desired pdf file from the `../static/uskpa_documents/irs` folder.

To *rename* an existing IRS Form 990 document:
  * Following the [change workflow], RENAME the desired pdf file from the `../static/uskpa_documents/irs` folder.

**Notes**

Filename is used for the link text. Files should be named as you would like them to appear on the website.

Files are ordered in reverse alphanumeric order by filename. We recommend following the existing naming convention
to display the most recent files first.

Files are inventoried when the application initializes, if you're modifying the files in local development
you will need to restart your development server for the changes to take effect.


[change workflow]: ../static/uskpa_documents/irs
