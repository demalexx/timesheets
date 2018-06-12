import re
from datetime import datetime, time, timedelta
from time import time as unixtime

from .typing import Optional

import sublime
import sublime_plugin


class DuplicateTimesheetLineCommand(sublime_plugin.TextCommand):
    """
    Duplicate timesheet line under cursor,
    insert it into appropriate place,
    fill time_from and/or time_to fields.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.regions_to_highlight = []

    def run(self, edit, copy_issue_and_comment: bool=True):
        """Entry-point, called when command is executed."""

        # Extract timesheet info from line under cursor
        timesheet_info = self.extract_timesheet_info(
            self.get_current_line_content()
        )

        # Do nothing if current line is not a timesheet line
        if not timesheet_info:
            self.view.window().status_message(
                'No valid timesheet line under cursor to work with'
            )
            return

        # Fill time_to if needed,
        # remember it to later fill time_from of new timesheet line
        new_time_to = self.fill_time_to(edit)

        new_time_to = new_time_to or self.floor_time(datetime.now())

        # Get last lines
        last_non_empty_line = self.get_last_non_empty_line_region()
        last_timesheet_line = self.get_last_timesheet_line_region()

        last_timesheet_line_info = self.extract_timesheet_info(
            self.view.substr(last_timesheet_line)
        )

        # Determine line after which new timesheet line should be inserted,
        # and if extra new line is needed.
        # Extra new line divides timesheet lines of different days,
        # or acts like separator from latest comment
        if self.is_today(last_timesheet_line_info):
            insert_after_line = last_timesheet_line
            extra_newline = False
        else:
            insert_after_line = last_non_empty_line
            extra_newline = True

        # Compose new timesheet line content
        new_timesheet_line_content = '\n{},{},{},{},"{}"'.format(
            new_time_to.strftime('%Y-%m-%d'),
            new_time_to.strftime('%H:%M'),
            ' ' * len('12:00'),
            timesheet_info['issue'] if copy_issue_and_comment else '',
            timesheet_info['comment'] if copy_issue_and_comment else '',
        )

        # Insert extra new line if needed
        if extra_newline:
            self.view.insert(edit, insert_after_line.end(), '\n')
            self.regions_to_highlight.append(sublime.Region(
                insert_after_line.end() + len('\n'),
                insert_after_line.end() + len('\n') + len('\n')
            ))
            insert_after_line = self.view.line(insert_after_line.end() + 1)

        # Insert new line
        self.view.insert(
            edit,
            insert_after_line.end(),
            new_timesheet_line_content
        )

        self.regions_to_highlight.append(sublime.Region(
            insert_after_line.end() + len('\n'),
            insert_after_line.end() + len('\n') + len(new_timesheet_line_content),
        ))

        # Move cursor to new inserted timesheet line,
        # keep column position same as original cursor
        row, column = self.view.rowcol(self.view.sel()[0].begin())
        self.view.sel().clear()
        self.view.sel().add(insert_after_line.end() + len('\n') + column)

        self.highlight_regions()

        self.view.window().status_message('Added new timesheet line')

    def fill_time_to(self, edit: sublime.Edit) -> Optional[datetime]:
        """
        If latest timesheet line is today and has empty time_to field,
        fill it with current time. Otherwise return time_to value.
        If there is no timesheet line, return None.
        """

        last_timesheet_line_region = self.get_last_timesheet_line_region()
        last_timesheet_line_info = self.extract_timesheet_info(
            self.view.substr(last_timesheet_line_region)
        )

        # If latest timesheet line isn't today, do nothing
        if not self.is_today(last_timesheet_line_info):
            return

        # If time_to already filled, return it
        if last_timesheet_line_info['to_dt']:
            return last_timesheet_line_info['to_dt']

        # Find start position of time_to field (it's fixed)
        time_to_start = len('2000-01-01,12:00,')

        # Find end position of time_to field
        # which could be any number of space chars
        pos = last_timesheet_line_region.begin() + time_to_start
        while pos < last_timesheet_line_region.end():
            if self.view.substr(pos) == ',':
                break
            pos += 1

        new_time_to = self.ceil_time(datetime.now())

        # Replace empty time_to with current time
        self.view.replace(
            edit,
            sublime.Region(
                last_timesheet_line_region.begin() + time_to_start,
                pos
            ),
            new_time_to.strftime('%H:%M')
        )

        # Add modified piece of line to highlight
        self.regions_to_highlight.append(sublime.Region(
            last_timesheet_line_region.begin() + time_to_start,
            last_timesheet_line_region.begin() + time_to_start + len('12:00'),
        ))

        return new_time_to

    def highlight_regions(self):
        """
        Highlight new inserted content so user knows what was modified.
        Also remove that highlight after short time so it won't bother user.
        """
        # For each inserted line generate unique key
        regions_key = 'timesheets-{}'.format(unixtime())

        # Highlight regions
        self.view.add_regions(
            regions_key,
            self.regions_to_highlight,
            'text',
            'dot',
            sublime.DRAW_NO_FILL
        )

        self.regions_to_highlight.clear()

        # Schedule regions clear
        sublime.set_timeout(lambda: self.view.erase_regions(regions_key), 1000)

    def get_current_line_content(self) -> str:
        """
        Return content of line where cursor is placed.
        If there are few cursors, use only first cursor.
        """
        current_selection = self.view.sel()[0]
        line = self.view.line(current_selection)
        return self.view.substr(line)

    def get_last_non_empty_line_region(self) -> Optional[sublime.Region]:
        """
        Return line region of latest non-empty string (including comments).
        """
        pos = self.view.size()
        while pos >= 0:
            line_region = self.view.line(pos)
            line_content = self.view.substr(line_region)

            if line_content.strip():
                return line_region

            pos = line_region.begin() - 1

    def get_last_timesheet_line_region(self) -> Optional[sublime.Region]:
        """Return line region of latest timesheet line (excluding comments)."""
        pos = self.view.size()
        while pos >= 0:
            line_region = self.view.line(pos)
            line_content = self.view.substr(line_region)

            if self.extract_timesheet_info(line_content):
                return line_region

            pos = line_region.begin() - 1

    def extract_timesheet_info(self, content: str) -> Optional[dict]:
        """
        Try to extract timesheet info.
        Return it as dict if given `content` contains timesheet,
        or None otherwise.
        Only Jira lines are supported.
        """
        match = re.search(
            r'^(?P<year>\d{4})-(?P<month>\d{2})-(?P<day>\d{2}),'
            r'(?P<from_hour>\d{2}):(?P<from_min>\d{2}),'
            r'(?P<to>\d{2}:\d{2}|[\s]*),'
            r'(?P<jira_issue>[\w_\-\d]+),'
            r'"(?P<comment>[^"]*)"$',
            content
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

        return {
            'from_dt': from_dt,
            'to_dt': to_dt,
            'issue': match.group('jira_issue'),
            'comment': match.group('comment'),
        }

    def is_today(self, timesheet_info: dict) -> bool:
        """Return true if given `timesheet_info` relates to today."""
        return \
            timesheet_info and \
            timesheet_info['from_dt'].date() == datetime.now().date()

    def floor_time(self, dt: datetime) -> datetime:
        """
        Return earliest time to given `dt` with rounding to 10 minutes.
        E.g.:
        12:01 -> 12:00
        12:09 -> 12:00
        """
        return datetime.combine(dt.date(), time(dt.hour, dt.minute // 10 * 10))

    def ceil_time(self, dt: datetime) -> datetime:
        """
        Return closest time in future to given `dt` with rounding to 10 minutes.
        E.g.:
        12:01 -> 12:10
        12:09 -> 12:10
        """
        return self.floor_time(dt) + timedelta(minutes=10)
