# 0.5.0 (2018-07-14)

* Also show how much time is worked this week.

# 0.4.0 (2018-07-10)

* Added info about how much time is worked today into status bar;
* Fixed bug when SublimeLinter is installed
  (it crashed when timesheets plugin is installed);
* Added syntax and unit tests.

# 0.3.0 (2018-06-12)

* Added feature to insert timesheet lines
  based on already existing lines and fill time fields,
  using single shortcut (improved "duplicate line");
* Improved syntax highlight: now it doesn't highlight
  lines with invalid dates and times (e.g. "2018-13-35", "24:60").
  Still it's still just dumb regexp.

# 0.2.0 (2018-06-10)

* Added feature to checkout and commit timesheets
  directly from Sublime Text.
  Sublime's Build System is used for this.

# 0.1.0 (2018-06-02)

* Initial release.