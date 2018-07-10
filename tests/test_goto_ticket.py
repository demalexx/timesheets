from unittest.mock import patch

import sublime

from timesheets.tests.base import BasePluginTestCase
from timesheets.goto_ticket import GotoTicketCommand


class TestGotoTicket(BasePluginTestCase):
    def setUp(self):
        super().setUp()

        self.settings = sublime.load_settings('timesheets.sublime-settings')
        self.command = GotoTicketCommand(self.view)

    def test_jira_url(self):
        timesheet_info = self.timesheet_helper.extract_timesheet_info(
            '2018-07-01,10:00,11:10,PROJECT-123,"comment"'
        )

        ticket_url_template = self.settings.get('{}_ticket_url'.format('jira'))
        expected_url = ticket_url_template.format('PROJECT-123')

        self.assertEqual(
            self.command.generate_ticket_url(timesheet_info),
            expected_url
        )

    def test_rt_url(self):
        timesheet_info = self.timesheet_helper.extract_timesheet_info(
            '2018-07-01,10:00,11:10,queue,RT:123,"comment"'
        )

        ticket_url_template = self.settings.get('{}_ticket_url'.format('rt'))
        expected_url = ticket_url_template.format('123')

        self.assertEqual(
            self.command.generate_ticket_url(timesheet_info),
            expected_url
        )

    def test_jira_url_opening(self):
        self.append_text('2018-07-01,10:00,11:10,PROJECT-123,"comment"')
        self.move_cursor(0, 0)

        settings = sublime.load_settings('timesheets.sublime-settings')
        ticket_url_template = settings.get('{}_ticket_url'.format('jira'))
        ticket_url = ticket_url_template.format('PROJECT-123')

        with patch('timesheets.goto_ticket.webbrowser.open') as open_mock:
            self.view.run_command('goto_ticket')

            open_mock.assert_called_once_with(ticket_url)

    def test_rt_url_opening(self):
        self.append_text('2018-07-01,10:00,11:10,queue,RT:123,"comment"')
        self.move_cursor(0, 0)

        settings = sublime.load_settings('timesheets.sublime-settings')
        ticket_url_template = settings.get('{}_ticket_url'.format('rt'))
        ticket_url = ticket_url_template.format('123')

        with patch('timesheets.goto_ticket.webbrowser.open') as open_mock:
            self.view.run_command('goto_ticket')

            open_mock.assert_called_once_with(ticket_url)


class TestIsVisibleAndCommand(BasePluginTestCase):
    def setUp(self):
        super().setUp()

        # List of lines and whether Goto Ticket menu item should be visible
        self.lines = [
            # Valid Jira
            ('2018-07-01,10:00,11:10,PROJECT-123,"comment"', True),
            # Valid RT
            ('2018-07-01,10:00,11:10,queue,RT:123,"comment"', True),
            # Comment
            ('# comment', False),
            # Empty string
            ('', False),
            # Invalid line
            ('2018-07-01 10:00 11:10 PROJECT-123 "comment"', False),
        ]
        self.append_text(
            '\n'.join(
                line
                for line, is_visible in self.lines
            )
        )

        self.command = GotoTicketCommand(self.view)

    def test_is_visible_and_command(self):
        """
        Check that visibility of menu item has expected values,
        and that executing command produces expected results.
        """
        with patch('timesheets.goto_ticket.webbrowser.open') as open_mock:
            # Iterate all lines
            for line_index, (_, expected_is_visible) in enumerate(self.lines):
                # Put cursor to every position of current line -
                # visibility should not depend on it
                for col_index in range(len(self.lines[line_index])):
                    self.move_cursor(line_index, col_index)
                    self.assertIs(
                        self.command.is_visible(),
                        expected_is_visible
                    )

                    # Execute command and check whether URL is opened
                    self.view.run_command('goto_ticket')
                    if expected_is_visible:
                        open_mock.assert_called()
                    else:
                        open_mock.assert_not_called()
