from datetime import datetime

import sublime

from timesheets.tests.base import BasePluginTestCase
from timesheets.duplicate_timesheet_line import DuplicateTimesheetLineCommand


class TestDuplicateTimesheetLine(BasePluginTestCase):
    def setUp(self):
        super().setUp()

        self.command = DuplicateTimesheetLineCommand(self.view)

    def test_floor_time(self):
        source_and_expected = []
        for minute in range(0, 9 + 1):
            source_and_expected.append((
                datetime(2018, 7, 4, 12, minute),
                datetime(2018, 7, 4, 12, 0)
            ))

        for source, expected in source_and_expected:
            self.assertEqual(self.command.floor_time(source), expected)

    def test_ceil_time(self):
        source_and_expected = []
        for minute in range(0, 9 + 1):
            source_and_expected.append((
                datetime(2018, 7, 4, 12, minute),
                datetime(2018, 7, 4, 12, 10)
            ))

        for source, expected in source_and_expected:
            self.assertEqual(self.command.ceil_time(source), expected)

    def test_get_last_non_empty_line_region_no_content(self):
        self.assertIs(self.command.get_last_non_empty_line_region(), None)

    def test_get_last_non_empty_line_region_content(self):
        expected_line = 'line 2'
        self.append_text(
            'line 1\n'
            '\n'
            '{}\n'
            ' \t\n'
            ''.format(expected_line)
        )
        expected_region = sublime.Region(8, 14)
        self.assertEqual(
            self.command.get_last_non_empty_line_region(),
            expected_region
        )
        self.assertEqual(self.view.substr(expected_region), expected_line)

    def test_get_last_timesheet_line_region_no_content(self):
        self.assertIs(self.command.get_last_timesheet_line_region(), None)

    def test_get_last_timesheet_line_region_content(self):
        expected_line = \
            '2018-07-04,10:00,12:10,PROJECT-123,"valid timesheet line"'
        self.append_text(
            'line 1\n'
            '\n'
            '# comment\n'
            '{}\n'
            '2018-07-04 10:00 12:10 PROJECT-123 "invalid timesheet line"\n'
            ' \t\n'
            ''.format(expected_line)
        )
        expected_region = sublime.Region(18, 75)
        self.assertEqual(
            self.command.get_last_timesheet_line_region(),
            expected_region
        )
        self.assertEqual(self.view.substr(expected_region), expected_line)


class TestDuplicateTimesheetLineCommand(BasePluginTestCase):
    """
    Target functionality tests:
    compose source content, call command, check final content.
    """

    def setUp(self):
        super().setUp()

        self.command = DuplicateTimesheetLineCommand(self.view)

        self.today_str = datetime.now().strftime('%Y-%m-%d')
        self.floor_time_str = self.command.floor_time(
            datetime.now()
        ).strftime('%H:%M')
        self.ceil_time_str = self.command.ceil_time(
            datetime.now()
        ).strftime('%H:%M')

    def test_empty(self):
        """Nothing happens on empty file."""
        self.view.run_command('duplicate_timesheet_line')
        self.assertEqual(self.get_text(), '')

    def test_no_timesheet_line_under_cursor(self):
        """Nothing happens if current line is comment."""
        self.append_text('# comment')

        self.move_cursor(0, 0)
        self.view.run_command('duplicate_timesheet_line')

        self.assertEqual(self.get_text(), '# comment')

    def test_old_jira_under_cursor(self):
        """
        Duplicating old line adds newline-separator
        and compose new line based on original line.
        """
        self.append_text('2018-07-01,10:00,12:10,PROJECT-123,"comment"\n')

        self.move_cursor(0, 0)
        self.view.run_command('duplicate_timesheet_line')

        self.assertEqual(
            self.get_text(),
            '2018-07-01,10:00,12:10,PROJECT-123,"comment"\n'
            '\n'
            '{},{},     ,PROJECT-123,"comment"\n'.format(
                self.today_str,
                self.floor_time_str
            )
        )

    def test_old_jira_under_cursor_no_copy(self):
        """
        Duplicating old line without copying issue and comment
        adds newline-separator
        and compose new line based on original line.
        """
        self.append_text('2018-07-01,10:00,12:10,PROJECT-123,"comment"\n')

        self.move_cursor(0, 0)
        self.view.run_command('duplicate_timesheet_line', {
            'copy_issue_and_comment': False
        })

        self.assertEqual(
            self.get_text(),
            '2018-07-01,10:00,12:10,PROJECT-123,"comment"\n'
            '\n'
            '{},{},     ,,""\n'.format(
                self.today_str,
                self.floor_time_str
            )
        )

    def test_old_jira_under_cursor_comment(self):
        """
        Duplicating old line with trailing comment
        inserts content after comment.
        """
        self.append_text(
            '2018-07-01,10:00,12:10,PROJECT-123,"comment"\n'
            '# comment\n'
        )

        self.move_cursor(0, 0)
        self.view.run_command('duplicate_timesheet_line')

        self.assertEqual(
            self.get_text(),
            '2018-07-01,10:00,12:10,PROJECT-123,"comment"\n'
            '# comment\n'
            '\n'
            '{},{},     ,PROJECT-123,"comment"\n'.format(
                self.today_str,
                self.floor_time_str
            )
        )

    def test_old_jira_under_cursor_same_day(self):
        """
        Duplicating old line when today line exists
        doesn't adds newline-separator
        and compose new line based on original line.
        """

        self.append_text(
            '2018-07-01,10:00,12:10,PROJECT-1,"comment 1"\n'
            '\n'
            '{},10:00,12:10,PROJECT-2,"comment 2"\n'.format(
                self.today_str
            )
        )

        self.move_cursor(0, 0)
        self.view.run_command('duplicate_timesheet_line')

        self.assertEqual(
            self.get_text(),
            '2018-07-01,10:00,12:10,PROJECT-1,"comment 1"\n'
            '\n'
            '{},10:00,12:10,PROJECT-2,"comment 2"\n'
            '{},12:10,     ,PROJECT-1,"comment 1"\n'.format(
                self.today_str,
                self.today_str,
            )
        )

    def test_old_jira_under_cursor_same_day_comment(self):
        """
        Duplicating old line with trailing comment and today line
        doesn't add newline-separator and inserts content
        before comment.
        """
        self.append_text(
            '2018-07-01,10:00,12:10,PROJECT-1,"comment 1"\n'
            '\n'
            '{},10:00,12:10,PROJECT-2,"comment 2"\n'
            '# comment\n'.format(
                self.today_str
            )
        )

        self.move_cursor(0, 0)
        self.view.run_command('duplicate_timesheet_line')

        self.assertEqual(
            self.get_text(),
            '2018-07-01,10:00,12:10,PROJECT-1,"comment 1"\n'
            '\n'
            '{},10:00,12:10,PROJECT-2,"comment 2"\n'
            '{},12:10,     ,PROJECT-1,"comment 1"\n'
            '# comment\n'.format(
                self.today_str,
                self.today_str,
            )
        )

    def test_jira_under_cursor_fill_time_to(self):
        """
        Duplicating today line with empty time_to fills it
        and compose new line based on original line.
        """
        self.append_text(
            '{},10:00,     ,PROJECT-123,"comment"\n'.format(self.today_str)
        )

        self.move_cursor(0, 0)
        self.view.run_command('duplicate_timesheet_line')

        self.assertEqual(
            self.get_text(),
            '{},10:00,{},PROJECT-123,"comment"\n'
            '{},{},     ,PROJECT-123,"comment"\n'.format(
                self.today_str,
                self.floor_time_str,
                self.today_str,
                self.floor_time_str,
            )
        )

    def test_old_jira_under_cursor_no_fill_time_to(self):
        """
        Duplicating old line with empty time_to doesn't fill it
        and appends new line based on original line.
        """
        self.append_text(
            '2018-07-01,10:00,     ,PROJECT-123,"comment"\n'.format(self.today_str)
        )

        self.move_cursor(0, 0)
        self.view.run_command('duplicate_timesheet_line')

        self.assertEqual(
            self.get_text(),
            '2018-07-01,10:00,     ,PROJECT-123,"comment"\n'
            '\n'
            '{},{},     ,PROJECT-123,"comment"\n'.format(
                self.today_str,
                self.floor_time_str,
            )
        )

    def test_today_jira_under_cursor_no_fill_existing_time_to(self):
        """
        Duplicating today line with filled time_to doesn't fill it,
        but uses time_to value in new appended line.
        """
        self.append_text(
            '{},10:00,12:10,PROJECT-123,"comment"\n'.format(self.today_str)
        )

        self.move_cursor(0, 0)
        self.view.run_command('duplicate_timesheet_line')

        self.assertEqual(
            self.get_text(),
            '{},10:00,12:10,PROJECT-123,"comment"\n'
            '{},12:10,     ,PROJECT-123,"comment"\n'.format(
                self.today_str,
                self.today_str,
            )
        )
