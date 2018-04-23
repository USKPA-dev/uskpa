from django.test import SimpleTestCase
from django.http.request import QueryDict

from kpc.utils import _filterable_params


class UtilTests(SimpleTestCase):

    def test_remove_array_append(self):
        """Appended multi-value notation is trimmed from keys"""
        raw = QueryDict.fromkeys(['a[]', 'b[]', 'c'], value=[1, 2, 3])
        processed = _filterable_params(raw)
        for key in processed.keys():
            self.assertFalse(key.endswith('[]'))
