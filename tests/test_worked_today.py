import sublime

from freezegun import freeze_time

from timesheets.tests.base import BasePluginTestCase


@freeze_time('2018-07-10 12:00')
class TestTimeWorkedStatusBar(BasePluginTestCase):
    def test_update_worked_on_activate(self):
        """
        Worked today status message is updated when timesheet tab is activated.
        """
        self.append_text('2018-07-10,10:00,12:10,PROJECT-123,"comment"')
        # Tab is not activated or saved,
        # so no "worked today" message should appear
        self.assertFalse(self.view.get_status('timesheet'))

        self.simulate_on_activated()

        # After activation "worked today" message should appear
        self.assertEqual(
            'Worked today 02:10, week 02:10',
            self.view.get_status('timesheet')
        )

    def test_update_worked_on_activate_not_today(self):
        """
        Worked today status message is updated when timesheet tab is activated.
        """
        self.append_text('2018-07-09,10:00,12:10,PROJECT-123,"comment"')
        # Tab is not activated or saved,
        # so no "worked today" message should appear
        self.assertFalse(self.view.get_status('timesheet'))

        self.simulate_on_activated()

        # After activation "worked today" message should appear
        self.assertEqual(
            'Worked today 00:00, week 02:10',
            self.view.get_status('timesheet')
        )

    def simulate_on_activated(self):
        """
        Simulate activating tab by switching to new file and back to timesheet.
        """
        sublime.active_window().new_file()
        self.view.window().run_command('close_file')
