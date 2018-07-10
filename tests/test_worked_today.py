from datetime import datetime, timedelta

import sublime

from timesheets.tests.base import BasePluginTestCase


class TestWorkedTodayMinutes(BasePluginTestCase):
    def test_single_line(self):
        self.append_text(
            '{:%Y-%m-%d},10:00,11:10,PROJECT-123,"comment"'.format(
                datetime.now()
            )
        )

        self.assertEqual(self.timesheet_helper.worked_today_minutes(), 70)

    def test_unfinished_line(self):
        # Test won't work in common case - it requires that today
        # is at least 10 minutes after midnight.
        from_dt = datetime.now().replace(
            second=0, microsecond=0
        ) - timedelta(minutes=10)

        self.append_text(
            '{:%Y-%m-%d},{:%H}:{:%M},     ,PROJECT-123,"comment"'.format(
                from_dt, from_dt, from_dt,
            )
        )

        self.assertAlmostEqual(
            self.timesheet_helper.worked_today_minutes(),
            (datetime.now() - from_dt).total_seconds() / 60,
            2
        )

    def test_finished_and_unfinished_lines(self):
        # Test won't work in common case - it requires that today
        # is at least 20 minutes after midnight.
        from_dt_1 = datetime.now().replace(
            second=0, microsecond=0
        ) - timedelta(minutes=20)
        to_dt_1 = from_dt_1 + timedelta(minutes=5)
        from_dt_2 = datetime.now().replace(
            second=0, microsecond=0
        ) - timedelta(minutes=10)

        self.append_text(
            '{:%Y-%m-%d},{},{},PROJECT-123,"comment"\n'
            '{:%Y-%m-%d},{},  ,PROJECT-123,"comment"'.format(
                from_dt_1, from_dt_1.strftime('%H:%M'),
                to_dt_1.strftime('%H:%M'),
                from_dt_2, from_dt_2.strftime('%H:%M'),
            )
        )

        self.assertAlmostEqual(
            self.timesheet_helper.worked_today_minutes(),
            5 + (datetime.now() - from_dt_2).total_seconds() / 60,
            2
        )

    def test_not_today(self):
        self.append_text(
            '{:%Y-%m-%d},10:00,11:10,PROJECT-123,"comment"'.format(
                datetime.now() - timedelta(days=1)
            )
        )

        self.assertEqual(self.timesheet_helper.worked_today_minutes(), 0)


class TestWorkedTodayStatusBar(BasePluginTestCase):
    def test_update_worked_on_activate(self):
        """
        Worked today status message is updated when timesheet tab is activated.
        """
        self.append_text('{:%Y-%m-%d},10:00,12:10,PROJECT-123,"comment"'.format(
            datetime.now()
        ))
        # Tab is not activated or saved,
        # so no "worked today" message should appear
        self.assertFalse(self.view.get_status('timesheet'))

        self.simulate_on_activated()

        # After activation "worked today" message should appear
        self.assertEqual(
            'Worked today 02:10',
            self.view.get_status('timesheet')
        )

    def test_update_worked_on_activate_not_today(self):
        """
        Worked today status message is updated when timesheet tab is activated.
        """
        self.append_text('{:%Y-%m-%d},10:00,12:00,PROJECT-123,"comment"'.format(
            datetime.now() - timedelta(days=1)
        ))
        # Tab is not activated or saved,
        # so no "worked today" message should appear
        self.assertFalse(self.view.get_status('timesheet'))

        self.simulate_on_activated()

        # After activation "worked today" message should appear
        self.assertEqual('Not worked today', self.view.get_status('timesheet'))

    def simulate_on_activated(self):
        """
        Simulate activating tab by switching to new file and back to timesheet.
        """
        sublime.active_window().new_file()
        self.view.window().run_command('close_file')
