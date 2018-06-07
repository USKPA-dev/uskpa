import os
from operator import itemgetter

from django.apps import AppConfig
from django.conf import settings


class KpcConfig(AppConfig):
    name = 'kpc'

    def ready(self):
        self.irs_docs = self._get_irs_docs()

    def _get_irs_docs(self):
        """
        Return list of (path, filename) IRS docs to display on home page
        """
        irs_docs = [(os.path.join('uskpa_documents', 'irs', f), f)
                    for f in os.listdir(settings.IRS_DOCS_DIRECTORY)]
        irs_docs.sort(key=itemgetter(1), reverse=True)
        return irs_docs
