import webbrowser

import sublime
import sublime_plugin

from timesheets.typing.typing import Optional
from timesheets.helpers import SublimeHelper, TimesheetHelper


class GotoTicketCommand(sublime_plugin.TextCommand):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.sublime_helper = SublimeHelper(self.view)
        self.timesheet_helper = TimesheetHelper(self.sublime_helper)

    def run(self, edit):
        """Entry-point, called when command is executed"""
        line_content = self.sublime_helper.get_current_line_content()
        timesheet_info = self.timesheet_helper.extract_timesheet_info(
            line_content
        )

        if timesheet_info:
            ticket_url = self.generate_ticket_url(timesheet_info)

            if ticket_url:
                self.view.window().status_message(
                    'Opening {}'.format(ticket_url)
                )
                webbrowser.open(ticket_url)
        else:
            self.view.window().status_message(
                "Can't find ticket in current line"
            )

    def is_visible(self, *args) -> bool:
        """
        Called when context menu is appeared.
        Return True if current line has ticket info
        and Goto Ticket menu item should appear.
        Return False otherwise.
        """
        return self.timesheet_helper.is_valid_timesheet_under_cursor()

    def generate_ticket_url(self, timesheet_info: dict) -> Optional[str]:
        """
        Generate and return ticket URL to given `ticket_info`.
        If required setting isn't set, or doesn't have template,
        show error message and return None.
        """
        error_prefix = 'Timesheets plugin'

        bug_tracker, ticket_id = timesheet_info['issue']

        settings = sublime.load_settings('timesheets.sublime-settings')

        option_name = '{}_ticket_url'.format(bug_tracker)
        ticket_url_template = settings.get(option_name)

        if not ticket_url_template:
            sublime.error_message(
                '{}: in order to open ticket in browser '
                'please specify valid "{}" option'.format(
                    error_prefix,
                    option_name
                )
            )
            return

        ticket_url = ticket_url_template.format(ticket_id)

        # If formatted template and raw template are the same,
        # looks like template missing placeholder ("{}")
        if ticket_url == ticket_url_template:
            sublime.error_message(
                '{}: in order to open ticket in browser '
                'please specify valid "{}" option'.format(
                    error_prefix,
                    option_name
                )
            )
            return

        return ticket_url
