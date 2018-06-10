# Timesheets

Sublime Text 3 package to help working with IPONWEB timesheets.
Features:

* Syntax highlight;
* Can open ticket, that's under cursor, in browser;
* Can checkout and commit timesheets from Sublime Text
  (using Sublime's Build System).

![Screenshot](images/screenshot.png)

Both RT and Jira tickets are supported.

# Installation

Copy file `timesheets.sublime-package` into
`<data_path>/Installed Packages/` folder:

* `~/Library/Application Support/Sublime Text 3/Installed Packages/`
  (MacOS);
* `~/.config/sublime-text-3/Installed Packages/` (Ubuntu);
* `~/AppData/Roaming/Sublime Text 3/Installed Packages/` (Windows).

# Usage

## Syntax highlight

To use syntax highlight select Timesheet from right bottom menu
of available syntaxes, or type "Set syntax: Timesheet"
in command palette (`Ctrl+Shift+P`, or `Cmd+Shift+P` on Mac).

If timesheet line has invalid format, it won't be highlighted
(e.g. missing comma or quote, letter instead of digit etc).
There is one exception - "time to" field could be filled with spaces
and line is highlighted as valid. Because it's considered as
ticket you're working on right now and finish time is not known yet.

## Open ticket in browser

If line contains valid ticket, you could open it in browser by:

* `Ctrl+Click` (`Alt+Click` on Mac) on any place on line;
* Select `Goto Ticket` in context menu. This menu item
  is visible only if line contains valid ticket;
* Type "Goto Ticket" in command pallete
  (`Ctr+Shift+P`, or `Cmd+Shit+P` on Mac). This command is also
  visible only if line contains valid ticket.

## Checkout and commit

This feature works on top of already configured setup of CVS timesheets,
so it should be configured first as described in docs.

Checkout and commit are done as extension of standard
Sublime's Build System. It just executes CVS commands
that usually are executed manually.

There are several ways to perform checkout/commit:

* By hotkeys (customizable in settings):
  * Checkout: `Ctrl+Alt+I` ("incoming" thus "I");
  * Commit: `Ctrl+Alt+O` ("outgoing", thus "O").
* From `Tools` menu: `Tools → Timesheets: Checkout` or
  `Tools → Timesheets: Commit`;
* Using command palette: press `Ctr+Shift+P` (`Cmd+Shit+P` on Mac)
  and type "Timesheets: Checkout" or "Timesheets: Commit";
* Using Build System shortcuts: `Ctrl+Shift+B` (`Cmd+Shift+B` on Mac)
  and select "Timesheets - Checkout" or "Timesheets - Commit".
  "Timesheets" option performs checkout.

After command is run output panel with results will appear.

![Checkout](images/checkout.png)

![Commit](images/commit.png)

# Customization

Plugin has few URLs settings accessible in
`Preferences → Package Settings → Timesheets → Settings`:

```json
{
    // Request Tracker (RT) ticket URL, e.g.
    // "https://rt.example.com/Ticket/Display.html?id={}"
    "rt_ticket_url": "https://www.iponweb.net/rt/Ticket/Display.html?id={}",

    // Jira ticket URL, e.g.
    // "https://jira.example.com/browse/{}"
    "jira_ticket_url": "https://jira.iponweb.net/browse/{}"
}
```

Mouse bindings could be changed in
`Preferences → Package Settings → Timesheets → Mouse Bindings`:

```javascript
[
    {
        "button": "button1",
        "modifiers": ["alt"],
        "count": 1,
        "press_command": "drag_select",
        "command": "goto_ticket"
    }
]
```

Key bindings could be changed in
`Preferences → Package Settings → Timesheets → Key Bindings`:

```javascript
[
    {
        "keys": ["ctrl+alt+i"],
        "command": "timesheets_checkout"
    },
    {
        "keys": ["ctrl+alt+o"],
        "command": "timesheets_commit"
    }
]
```