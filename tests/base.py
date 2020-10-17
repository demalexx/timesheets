from unittest import TestCase

import sublime

from timesheets.helpers import SublimeHelper, TimesheetHelper


class BasePluginTestCase(TestCase):
    """
    Convenient class that creates view for tests and close it after test run.
    Also contains utility methods.
    """

    def setUp(self):
        # Create view that will be used by tests
        self.view = sublime.active_window().new_file()

        self.sublime_helper = SublimeHelper(self.view)
        self.timesheet_helper = TimesheetHelper(self.sublime_helper)

    def tearDown(self):
        if self.view:
            # Set scratch flag so view with content could be closed
            # without saving prompt
            self.view.set_scratch(True)
            self.view.window().run_command('close_file')

    def get_valid_line(self):
        valid_line = '2018-07-01,10:00,12:10,PROJECT-123,comment'
        self.assertTrue(
            self.timesheet_helper.extract_timesheet_info(valid_line)
        )
        return valid_line

    def get_invalid_line(self):
        invalid_line = '2018-07-01 10:00 12:10 PROJECT-123 comment'
        self.assertFalse(
            self.timesheet_helper.extract_timesheet_info(invalid_line)
        )
        return invalid_line

    def append_text(self, text: str):
        """Appends given text to view."""
        self.view.run_command('insert', {'characters': text})

    def get_text(self) -> str:
        """Return full content of current view."""
        return self.view.substr(sublime.Region(0, self.view.size()))

    def move_cursor(self, row: int, col: int):
        pos = self.view.text_point(row, col)
        self.view.sel().clear()
        self.view.sel().add(pos)
