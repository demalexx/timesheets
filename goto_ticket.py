import re
import webbrowser

import sublime
import sublime_plugin


class GotoTicketCommand(sublime_plugin.TextCommand):
    def run(self, edit):
        """Entry-point, called when command is executed"""
        line_content = self.get_current_line_content()
        ticket_info = self.extract_ticket_from_str(line_content)

        if ticket_info:
            ticket_url = self.generate_ticket_url(ticket_info)

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
        line_content = self.get_current_line_content()
        return bool(self.extract_ticket_from_str(line_content))

    def get_current_line_content(self) -> str:
        """
        Return content of line where cursor is placed.
        If there are few cursors, use only first cursor.
        """
        current_selection = self.view.sel()[0]
        line = self.view.line(current_selection)
        return self.view.substr(line)

    def extract_ticket_from_str(self, content: str) -> tuple:
        """
        Extract ticket info from given `content`
        and return it as tuple ("<bug tracker>", "<ticket id>").
        Ticket should be placed between commas.
        Supported formats:
        - RT ("RT:<ticket id>", e.g. "RT:12345");
        - Jira ("<project>-<id>", e.g. "PROJECT_NAME-123").
        If ticket info doesn't exist, return None.
        """
        match = re.search(r',RT:(\d+),', content)
        if match:
            return ('rt', match.group(1))

        match = re.search(r',([\w_]+-\d+),', content)
        if match:
            return ('jira', match.group(1))

    def generate_ticket_url(self, ticket_info: tuple) -> str:
        """
        Generate and return ticket URL to given `ticket_info`.
        If required setting isn't set, or doesn't have template,
        show error message and return None.
        """
        error_prefix = 'Timesheets plugin'

        bug_tracker, ticket_id = ticket_info

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
