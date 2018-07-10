from datetime import datetime, time, timedelta
from time import time as unixtime

import sublime
import sublime_plugin

from timesheets.typing.typing import Optional
from timesheets.helpers import SublimeHelper, TimesheetHelper


class DuplicateTimesheetLineCommand(sublime_plugin.TextCommand):
    """
    Duplicate timesheet line under cursor,
    insert it into appropriate place,
    fill time_from and/or time_to fields.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.sublime_helper = SublimeHelper(self.view)
        self.timesheet_helper = TimesheetHelper(self.sublime_helper)

        self.regions_to_highlight = []

    def run(self, edit: sublime.Edit, copy_issue_and_comment: bool=True):
        """Entry-point, called when command is executed."""

        # Extract timesheet info from line under cursor
        timesheet_info = self.timesheet_helper.extract_timesheet_info(
            self.sublime_helper.get_current_line_content()
        )

        # Do nothing if current line is not a timesheet line
        if not timesheet_info:
            self.view.window().status_message(
                'No valid timesheet line under cursor to duplicate'
            )
            return

        # Fill time_to if needed,
        # remember it to later fill time_from of new timesheet line
        new_time_to = self.fill_time_to(edit)

        new_time_to = new_time_to or self.floor_time(datetime.now())

        # Get last lines
        last_non_empty_line = self.get_last_non_empty_line_region()
        last_timesheet_line = self.get_last_timesheet_line_region()

        last_timesheet_line_info = self.timesheet_helper.extract_timesheet_info(
            self.view.substr(last_timesheet_line)
        )

        # Determine line after which new timesheet line should be inserted,
        # and if extra new line is needed.
        # Extra new line divides timesheet lines of different days,
        # or acts like separator from latest comment
        if self.timesheet_helper.is_today(last_timesheet_line_info):
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
            timesheet_info['issue'][1] if copy_issue_and_comment else '',
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

        added_line_region = sublime.Region(
            insert_after_line.end() + len('\n'),
            insert_after_line.end() + len('\n') + len(
                new_timesheet_line_content
            ),
        )

        self.regions_to_highlight.append(added_line_region)

        # Move cursor to new inserted timesheet line,
        # keep column position same as original cursor
        row, column = self.view.rowcol(self.view.sel()[0].begin())
        self.view.sel().clear()
        self.view.sel().add(insert_after_line.end() + len('\n') + column)

        self.view.show(added_line_region)

        self.highlight_regions()

        self.view.window().status_message('Added new timesheet line')

    def is_visible(self, *args, **kwargs):
        """
        Called when context menu is appeared.
        Return True if current line has ticket info
        and Duplicate Timesheet Line menu item should appear.
        Return False otherwise.
        """
        return self.timesheet_helper.is_valid_timesheet_under_cursor()

    def fill_time_to(self, edit: sublime.Edit) -> Optional[datetime]:
        """
        If latest timesheet line is today and has empty time_to field,
        fill it with current time. Otherwise return time_to value.
        If there is no timesheet line, return None.
        """

        last_timesheet_line_region = self.get_last_timesheet_line_region()
        last_timesheet_line_info = self.timesheet_helper.extract_timesheet_info(
            self.view.substr(last_timesheet_line_region)
        )

        # If latest timesheet line isn't today, do nothing
        if not self.timesheet_helper.is_today(last_timesheet_line_info):
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

        new_time_to = self.floor_time(datetime.now())

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
        sublime.set_timeout(lambda: self.view.erase_regions(regions_key), 750)

    def get_last_non_empty_line_region(self) -> Optional[sublime.Region]:
        """
        Return line region of latest non-empty string (including comments).
        """
        for line_region in self.sublime_helper.iter_lines_regions_reversed():
            line_content = self.view.substr(line_region)

            if line_content.strip():
                return line_region

    def get_last_timesheet_line_region(self) -> Optional[sublime.Region]:
        """Return line region of latest timesheet line (excluding comments)."""
        for line_region in self.sublime_helper.iter_lines_regions_reversed():
            line_content = self.view.substr(line_region)

            if self.timesheet_helper.extract_timesheet_info(line_content):
                return line_region

    def floor_time(self, dt: datetime) -> datetime:
        """
        Return earliest time to given `dt` with rounding to 10 minutes.
        E.g.:
        12:00 -> 12:00
        12:01 -> 12:00
        12:09 -> 12:00
        """
        return datetime.combine(dt.date(), time(dt.hour, dt.minute // 10 * 10))

    def ceil_time(self, dt: datetime) -> datetime:
        """
        Return closest time in future to given `dt` with rounding to 10 minutes.
        E.g.:
        12:00 -> 12:10
        12:01 -> 12:10
        12:09 -> 12:10
        """
        return self.floor_time(dt) + timedelta(minutes=10)
