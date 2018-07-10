import sublime_plugin


class TimesheetsCheckoutCommand(sublime_plugin.WindowCommand):
    """Simple custom command to run checkout through Sublime's Build System"""

    def run(self, *args):
        self.window.run_command('build', {
            'build_system': 'Packages/timesheets/build-systems/Timesheets.sublime-build',
            'variant': 'Checkout'
        })


class TimesheetsCommitCommand(sublime_plugin.WindowCommand):
    """Simple custom command to run commit through Sublime's Build System"""

    def run(self, *args):
        self.window.run_command('build', {
            'build_system': 'Packages/timesheets/build-systems/Timesheets.sublime-build',
            'variant': 'Commit'
        })
