import sublime

from timesheets.tests.base import BasePluginTestCase


class TestSublimeHelper(BasePluginTestCase):
    def test_iter_lines(self):
        lines = ['line 1', '', 'line 2', ' ']
        self.append_text('\n'.join(lines))

        self.assertEqual(list(self.sublime_helper.iter_lines()), lines)

    def test_iter_lines_reversed(self):
        lines = ['line 1', '', 'line 2', ' ']
        self.append_text('\n'.join(lines))

        self.assertEqual(
            list(self.sublime_helper.iter_lines_reversed()),
            list(reversed(lines))
        )

    def test_iter_lines_regions_reversed(self):
        lines = ['line 1', '', 'line 2', ' ']
        self.append_text('\n'.join(lines))

        self.assertEqual(
            list(self.sublime_helper.iter_lines_regions_reversed()),
            [
                sublime.Region(15, 16),
                sublime.Region(8, 14),
                sublime.Region(7, 7),
                sublime.Region(0, 6)
            ]
        )

    def test_get_current_line_content(self):
        lines = ['line 1', 'current line', 'line 3']
        self.append_text('\n'.join(lines))

        self.move_cursor(1, 0)

        self.assertEqual(
            self.sublime_helper.get_current_line_content(),
            'current line'
        )
