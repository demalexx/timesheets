import re
from datetime import datetime

import sublime

from timesheets.typing.typing import Optional, Generator, Iterable, List


class SublimeHelper:
    """Utility class with convenient methods to work with given `view`."""

    def __init__(self, view: sublime.View):
        self.view = view

    def get_current_line_content(self) -> str:
        """
        Return content of line where cursor is placed.
        If there are few cursors, use only first cursor.
        """
        current_selection = self.view.sel()[0]
        line = self.view.line(current_selection)
        return self.view.substr(line)

    def iter_lines(self) -> Generator[str, None, None]:
        """
        Iterate content of view line by line.
        Trailing newline character not included.
        """
        pos = 0
        while pos < self.view.size():
            line_region = self.view.line(pos)
            line_content = self.view.substr(line_region)

            yield line_content

            pos = line_region.end() + 1

    def iter_lines_regions_reversed(self) -> Iterable[sublime.Region]:
        """
        Iterate regions of view line by line in reverse order
        (from last line to first).
        Trailing newline character not included.
        """
        pos = self.view.size()
        while pos >= 0:
            line_region = self.view.line(pos)

            yield line_region

            pos = line_region.begin() - 1

    def iter_lines_reversed(self) -> Generator[str, None, None]:
        """
        Iterate content of view line by line in reverse order
        (from last line to first).
        Trailing newline character not included.
        """
        for line_region in self.iter_lines_regions_reversed():
            line_content = self.view.substr(line_region)

            yield line_content


class TimesheetHelper:
    """
    Utility class with convenient methods to work with timesheet
    from view that's attached to given `sublime_helper`.
    """

    def __init__(self, sublime_helper: SublimeHelper):
        self.sublime_helper = sublime_helper

    def extract_timesheet_info(self, line: str) -> Optional[dict]:
        """
        Try to extract timesheet info from given `line`.
        Return it as dict if content contains timesheet,
        or None otherwise.
        Jira and partly RT lines are supported.
        """
        match = re.search(
            r'^(?P<year>\d{4})-(?P<month>\d{2})-(?P<day>\d{2}),'
            r'(?P<from_hour>\d{2}):(?P<from_min>\d{2}),'
            r'(?P<to>\d{2}:\d{2}|[\s]*),'
            r'((?P<jira_issue>[\w_\-\d]+)|((?P<rt_queue>[^,]+),(RT:)(?P<rt_ticket_id>\d+))),'
            r'"(?P<comment>[^"]*)"$',
            line
        )

        if not match:
            return

        try:
            from_dt = datetime(
                int(match.group('year')),
                int(match.group('month')),
                int(match.group('day')),
                int(match.group('from_hour')),
                int(match.group('from_min')),
            )
        except ValueError:
            return

        if match.group('to').strip():
            to_hour, to_min = match.group('to').split(':')

            try:
                to_dt = datetime(
                    int(match.group('year')),
                    int(match.group('month')),
                    int(match.group('day')),
                    int(to_hour),
                    int(to_min),
                )
            except ValueError:
                return
        else:
            to_dt = None

        issue = None

        jira_issue = match.group('jira_issue')
        if jira_issue:
            issue = ('jira', jira_issue)

        rt_issue = match.group('rt_queue')
        rt_ticket_id = match.group('rt_ticket_id')
        if rt_issue and rt_ticket_id:
            issue = ('rt', rt_ticket_id)

        return {
            'from_dt': from_dt,
            'to_dt': to_dt,
            'issue': issue,
            'comment': match.group('comment'),
        }

    def is_timesheet(self) -> bool:
        """
        Return True if current file is timesheet, False otherwise.
        Very simple heuristic is used to determine it:
        if more than 90% of first 100 lines are valid timesheet lines
        (except empty lines and comments), then file considered timesheet.
        """
        valid_timesheet_lines = 0
        invalid_timesheet_lines = 0
        for count, line in enumerate(self.sublime_helper.iter_lines()):
            if count >= 100:
                break

            if not line.strip():
                continue

            if self.is_comment(line):
                continue

            if self.extract_timesheet_info(line):
                valid_timesheet_lines += 1
            else:
                invalid_timesheet_lines += 1

        if not valid_timesheet_lines:
            return False

        valid_to_invalid_lines_ratio = (
            valid_timesheet_lines /
            (valid_timesheet_lines + invalid_timesheet_lines)
        )

        return valid_to_invalid_lines_ratio >= 0.9

    def is_today(self, timesheet_info: dict) -> bool:
        """Return true if given `timesheet_info` relates to today."""
        return \
            timesheet_info and \
            timesheet_info['from_dt'].date() == datetime.now().date()

    def worked_today_minutes(self) -> float:
        """Iterate lines backward and count how much time is worked today."""
        today_timesheet_info = []

        for line in self.sublime_helper.iter_lines_reversed():
            timesheet_info = self.extract_timesheet_info(line)
            if not timesheet_info:
                continue

            if timesheet_info['from_dt'].date() == datetime.today().date():
                today_timesheet_info.append(timesheet_info)
            else:
                break

        return self.timesheets_info_to_minutes(today_timesheet_info)

    def worked_week_minutes(self) -> float:
        """
        Iterate lines backward and count how much time is worked this week.
        """
        week_timesheet_info = []

        today_year, today_week, _ = datetime.today().isocalendar()

        for line in self.sublime_helper.iter_lines_reversed():
            timesheet_info = self.extract_timesheet_info(line)
            if not timesheet_info:
                continue

            line_year, line_week, _ = timesheet_info['from_dt'].isocalendar()

            if line_year == today_year and line_week == today_week:
                week_timesheet_info.append(timesheet_info)
            else:
                break

        return self.timesheets_info_to_minutes(week_timesheet_info)

    def timesheets_info_to_minutes(self, timesheets_info:  List[dict]) -> float:
        """
        Return how much time is worked based on given list
        of timesheet info objects.
        """
        worked_minutes = 0
        for timesheet_info in timesheets_info:
            to_dt = timesheet_info['to_dt'] or datetime.now()
            timesheet_line_worked_minutes = (
                to_dt - timesheet_info['from_dt']
            ).total_seconds() / 60
            worked_minutes += timesheet_line_worked_minutes

        return worked_minutes

    def is_comment(self, line: str) -> bool:
        """Return True if given `line` is comment."""
        return line.lstrip().startswith('#')

    def is_valid_timesheet_under_cursor(self) -> bool:
        """Return True if line under cursor is valid timesheet line."""
        return bool(
            self.extract_timesheet_info(
                self.sublime_helper.get_current_line_content()
            )
        )


def prettify_minutes(minutes_total: float) -> str:
    """
    Return time in format "<hours>:<minutes>" from given `minutes_total`.
    E.g. 65 minutes -> "01:05".
    """
    hours, minutes = divmod(minutes_total, 60)
    return '{:02}:{:02}'.format(int(hours), int(minutes))
