del release\timesheets.sublime-package
7z a -r -tzip -mx=0 release\timesheets.sublime-package *.sublime-* *.py *.md -x!tests -x!sublime.py -x!sublime_plugin.py -x!.idea