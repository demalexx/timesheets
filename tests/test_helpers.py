from timesheets.tests.base import BasePluginTestCase
from timesheets.helpers import prettify_minutes


class TestTimesheetHelper(BasePluginTestCase):
    def test_prettify_minutes(self):
        self.assertEqual('01:05', prettify_minutes(65))
