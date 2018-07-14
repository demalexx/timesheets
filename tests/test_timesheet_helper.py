from datetime import datetime, timedelta

from freezegun import freeze_time

from timesheets.tests.base import BasePluginTestCase


class TestTimesheetHelper(BasePluginTestCase):
    def test_is_comment(self):
        self.assertTrue(self.timesheet_helper.is_comment('# comment'))
        self.assertTrue(self.timesheet_helper.is_comment(' # comment'))
        self.assertFalse(self.timesheet_helper.is_comment('not-a-comment'))
        self.assertFalse(
            self.timesheet_helper.is_comment('not-a-comment # comment')
        )

    def test_is_valid_timesheet_under_cursor_jira(self):
        self.append_text('2018-07-01,10:00,12:10,PROJECT-123,"comment"')
        self.assertTrue(self.timesheet_helper.is_valid_timesheet_under_cursor())

    def test_is_valid_timesheet_under_cursor_rt(self):
        self.append_text('2018-07-01,10:00,12:10,queue,RT:123,"comment"')
        self.assertTrue(self.timesheet_helper.is_valid_timesheet_under_cursor())

    def test_is_not_valid_timesheet_under_cursor(self):
        self.append_text('2018-07-01 10:00 12:10 PROJECT-123 "comment"')
        self.assertFalse(
            self.timesheet_helper.is_valid_timesheet_under_cursor()
        )

    def test_is_today(self):
        timesheet_info = self.timesheet_helper.extract_timesheet_info(
            '{:%Y-%m-%d},10:00,12:10,PROJECT-123,"comment"'.format(
                datetime.now()
            )
        )
        self.assertTrue(self.timesheet_helper.is_today(timesheet_info))

        timesheet_info = self.timesheet_helper.extract_timesheet_info(
            '{:%Y-%m-%d},10:00,12:10,queue,RT:123,"comment"'.format(
                datetime.now()
            )
        )
        self.assertTrue(self.timesheet_helper.is_today(timesheet_info))

    def test_is_not_today(self):
        timesheet_info = self.timesheet_helper.extract_timesheet_info(
            '{:%Y-%m-%d},10:00,12:10,PROJECT-123,"comment"'.format(
                datetime.now() - timedelta(days=1)
            )
        )
        self.assertFalse(self.timesheet_helper.is_today(timesheet_info))

        timesheet_info = self.timesheet_helper.extract_timesheet_info(
            '{:%Y-%m-%d},10:00,12:10,queue,RT:123,"comment"'.format(
                datetime.now() - timedelta(days=1)
            )
        )
        self.assertFalse(self.timesheet_helper.is_today(timesheet_info))


class TestExtractTimesheetInfo(BasePluginTestCase):
    def test_jira(self):
        self.assertEqual(
            self.timesheet_helper.extract_timesheet_info(
                '2018-07-01,10:00,12:10,PROJECT-123,"comment"'
            ), {
                'from_dt': datetime(2018, 7, 1, 10, 0),
                'to_dt': datetime(2018, 7, 1, 12, 10),
                'issue': ('jira', 'PROJECT-123'),
                'comment': 'comment',
            }
        )

    def test_jira_empty_time_to(self):
        self.assertEqual(
            self.timesheet_helper.extract_timesheet_info(
                '2018-07-01,10:00,,PROJECT-123,"comment"'
            ), {
                'from_dt': datetime(2018, 7, 1, 10, 0),
                'to_dt': None,
                'issue': ('jira', 'PROJECT-123'),
                'comment': 'comment',
            }
        )

        self.assertEqual(
            self.timesheet_helper.extract_timesheet_info(
                '2018-07-01,10:00,     ,PROJECT-123,"comment"'
            ), {
                'from_dt': datetime(2018, 7, 1, 10, 0),
                'to_dt': None,
                'issue': ('jira', 'PROJECT-123'),
                'comment': 'comment',
            }
        )

    def test_rt(self):
        self.assertEqual(
            self.timesheet_helper.extract_timesheet_info(
                '2018-07-01,10:00,12:10,queue,RT:123,"comment"'
            ), {
                'from_dt': datetime(2018, 7, 1, 10, 0),
                'to_dt': datetime(2018, 7, 1, 12, 10),
                'issue': ('rt', '123'),
                'comment': 'comment',
            }
        )

    def test_rt_empty_time_to(self):
        self.assertEqual(
            self.timesheet_helper.extract_timesheet_info(
                '2018-07-01,10:00,,queue,RT:123,"comment"'
            ), {
                'from_dt': datetime(2018, 7, 1, 10, 0),
                'to_dt': None,
                'issue': ('rt', '123'),
                'comment': 'comment',
            }
        )

        self.assertEqual(
            self.timesheet_helper.extract_timesheet_info(
                '2018-07-01,10:00,     ,queue,RT:123,"comment"'
            ), {
                'from_dt': datetime(2018, 7, 1, 10, 0),
                'to_dt': None,
                'issue': ('rt', '123'),
                'comment': 'comment',
            }
        )


class TestIsTimesheet(BasePluginTestCase):
    def test_not_timesheet_1(self):
        """Not timesheet if empty file."""
        self.append_text('')
        self.assertFalse(self.timesheet_helper.is_timesheet())

    def test_not_timesheet_2(self):
        """Not timesheet if single comment line."""
        self.append_text('# comment')
        self.assertFalse(self.timesheet_helper.is_timesheet())

    def test_not_timesheet_3(self):
        """Not timesheet if single invalid timesheet line."""
        self.append_text('2018-07-01 10:00 12:00 PROJECT-123 "comment"')
        self.assertFalse(self.timesheet_helper.is_timesheet())

    def test_not_timesheet_4(self):
        """Not timesheet if 1 line is valid out of 2 - 50% is not enough."""
        self.append_text('{}\n{}'.format(
            self.get_valid_line(),
            '2018-07-01 10:00 12:00 PROJECT-123 "comment"',
        ))
        self.assertFalse(self.timesheet_helper.is_timesheet())

    def test_timesheet_1(self):
        """Timesheet if single valid timesheet line (100%)."""
        self.append_text(self.get_valid_line())
        self.assertTrue(self.timesheet_helper.is_timesheet())

    def test_timesheet_2(self):
        """Timesheet if comment and valid timesheet line."""
        self.append_text('{}\n{}'.format(
            '# comment',
            self.get_valid_line()
        ))
        self.assertTrue(self.timesheet_helper.is_timesheet())

    def test_timesheet_3(self):
        """Timesheet if 9 lines are valid, 1 is invalid (90%)."""
        self.append_text('{}\n{}'.format(
            '\n'.join([self.get_valid_line()] * 9),
            self.get_invalid_line()
        ))
        self.assertTrue(self.timesheet_helper.is_timesheet())


@freeze_time('2018-07-01 12:00')
class TestWorkedToday(BasePluginTestCase):
    def test_single_line(self):
        self.append_text('2018-07-01,10:00,11:10,PROJECT-123,"comment"')
        self.assertEqual(self.timesheet_helper.worked_today_minutes(), 70)

    def test_unfinished_line(self):
        self.append_text('2018-07-01,10:00,     ,PROJECT-123,"comment"')
        self.assertEqual(self.timesheet_helper.worked_today_minutes(), 120)

    def test_finished_and_unfinished_lines(self):
        self.append_text(
            '2018-07-01,10:00,10:10,PROJECT-123,"comment"\n'
            '2018-07-01,11:00,     ,PROJECT-123,"comment"'
        )

        self.assertEqual(self.timesheet_helper.worked_today_minutes(), 10 + 60)

    def test_not_today(self):
        self.append_text('2018-07-02,10:00,11:10,PROJECT-123,"comment"')
        self.assertEqual(self.timesheet_helper.worked_today_minutes(), 0)


@freeze_time('2018-07-10 12:00')
class TestWorkedThisWeek(BasePluginTestCase):
    """Today (2018-07-10) is set to tuesday."""

    def test_this_week(self):
        """
        Week before isn't counted.
        Only 2018-07-10 (tuesday) and 2018-07-09 (monday) are counted.
        2018-07-08 (sunday of week before) isn't counted.
        """
        self.append_text(
            '2018-07-08,10:00,11:10,PROJECT-123,"comment"\n'
            '2018-07-09,10:00,11:10,PROJECT-123,"comment"\n'
            '2018-07-10,10:00,11:10,PROJECT-123,"comment"\n'
        )
        self.assertEqual(self.timesheet_helper.worked_week_minutes(), 70 + 70)
