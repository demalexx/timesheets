import sublime_plugin

from timesheets.helpers import prettify_minutes
from timesheets.helpers import SublimeHelper, TimesheetHelper


class TimeWorked(sublime_plugin.ViewEventListener):
    """
    Display today and week worked time in status bar for opened timesheet file.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.sublime_helper = SublimeHelper(self.view)
        self.timesheet_helper = TimesheetHelper(self.sublime_helper)

        # Remember if current view contains timesheet file.
        # This needed to save resources and don't process non-timesheet files.
        self.is_timesheet = None

    def on_activated(self):
        """
        Called when file is opened, tab is activated by clicking,
        or when minimized Sublime is restored (e.g. by Alt-Tab).
        """
        if not self.detect_is_timesheet():
            return

        self.update_worked_message()

    def on_post_save(self):
        if not self.detect_is_timesheet():
            return

        self.update_worked_message()

    def detect_is_timesheet(self) -> bool:
        """
        If it's unknown whether content of current view is timesheet or not,
        detect it. Otherwise use saved value.
        In both cases return whether content of current view
        looks like timesheet.
        """
        if self.is_timesheet is None:
            self.is_timesheet = self.timesheet_helper.is_timesheet()
        return self.is_timesheet

    def update_worked_message(self):
        """Calculate and update worked today time in status bar."""
        worked_today_minutes = self.timesheet_helper.worked_today_minutes()
        worked_week_minutes = self.timesheet_helper.worked_week_minutes()

        message = 'Worked today {}, week {}'.format(
            prettify_minutes(worked_today_minutes),
            prettify_minutes(worked_week_minutes),
        )

        self.view.set_status('timesheet', message)
