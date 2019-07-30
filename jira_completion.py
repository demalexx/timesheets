"""
Sublime Text 3 Plugin to autocomplete JIRA issues numbers
by ticket titles.

How to use:

Type "JI" with an optional filter, e.g. "JIauthgoogle", press Alt+/.
Completion menu should pop up.

How to set up:
1. Add your username and password to ~/.netrc, e.g.:

    machine jira.iponweb.net login vpetrov password topsecretpassword

CAUTION: async requests are not supported, so your editor will freeze
until reply from JIRA is received.
Also, minimal error handling, sorry.
"""

import base64
import datetime
import json
import netrc
import sublime
import sublime_plugin
import urllib

from urllib.error import HTTPError


class Settings:
    def __init__(self, settings):
        self._settings = settings

    @property
    def hostname(self):
        return self._settings.get('hostname', 'jira.iponweb.net')

    @property
    def trigger(self):
        return self._settings.get('trigger', 'JI')

    @property
    def jira_completion_url(self):
        return self._settings.get(
            'jira_completion_url',
            'https://jira.iponweb.net/rest/api/2/search?'
            'jql=(watcher+in+({username})+'
                'OR+assignee+in+({username})+'
                'OR+reporter+in+({username}))+'
                'ORDER+BY+updated+DESC,+created+DESC'
                '&maxResults=100&fields=id,key,summary'
        )

    @property
    def timeout(self):
        return self._settings.get('timeout', 5)

    @property
    def log_filename(self):
        return self._settings.get('log_filename', None)


def load_settings():
    return Settings(sublime.load_settings('timesheets.sublime-settings'))


class JiraCompleter:
    def __init__(self, settings):
        self._settings = settings

    def _log(self, message):
        if not self._settings.log_filename:
            return

        with open(self._settings.log_filename, 'a') as file_:
            file_.write('%s %s\n' % (datetime.datetime.now(), message))

    def _read_credentials(self):
        username, _account, password = \
            netrc.netrc().hosts[self._settings.hostname]
        return username, password

    def _build_url(self):
        username, _password = self._read_credentials()
        return self._settings.jira_completion_url.format(username=username)

    def _get_url(self, url):
        username, password = self._read_credentials()
        opener = urllib.request.build_opener()
        header = base64.b64encode(
            ('%s:%s' % (username, password)).encode('ascii')).decode('ascii')
        opener.addheaders = [('Content-Type', 'application/json')]
        opener.addheaders = [('Authorization', 'Basic %s' % header)]
        try:
            response_body = opener.open(
                url, timeout=self._settings.timeout
            ).read()
        except HTTPError as e:
            self._log('Network error: %s %s' % (e, e.read()))
            raise
        return response_body.decode('utf-8')

    def _get_tickets(self):
        body = self._get_url(self._build_url())
        response = json.loads(body)
        return [
            (entry['key'], entry['fields']['summary'])
            for entry in response['issues']
        ]

    def get_jira_suggestions_online(self):
        self._log('getting online')
        pairs = self._get_tickets()
        suggestions = [
            ('%s %s\t%s' % (self._settings.trigger, subject, key,), key)
            for key, subject in pairs
        ]
        self._log('# suggestions %s' % len(suggestions))
        return suggestions

    def get_suggestions(self):
        try:
            return self.get_jira_suggestions_online()
        except Exception as e:
            self._log('Error getting suggestions: {}'.format(e))
            return []


class JiraAutocomplete(sublime_plugin.EventListener):
    def on_query_completions(self, view, prefix, locations):
        settings = load_settings()

        if not prefix.startswith(settings.trigger):
            return []

        completer = JiraCompleter(settings)
        return completer.get_suggestions()
