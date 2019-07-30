from datetime import datetime, timedelta
from json import dumps
from unittest.mock import MagicMock, Mock, patch
from urllib.error import HTTPError

import sublime
from freezegun import freeze_time
from timesheets.jira_completion import JiraAutocomplete, Settings
from timesheets.tests.base import BasePluginTestCase


class TestJiraCompletion(BasePluginTestCase):
    @patch('timesheets.jira_completion.load_settings')
    def test_no_trigger(self, settings_mock):
        settings_mock.return_value = Settings({'trigger': 'HEY'})

        completer = JiraAutocomplete()
        suggestions = completer.on_query_completions(
            view=None, prefix='something', locations=None,
        )

        self.assertEqual(suggestions, [])

    @patch('timesheets.jira_completion.JiraCompleter._get_url')
    @patch('timesheets.jira_completion.load_settings')
    def test_simple_trigger_ok(self, settings_mock, get_url_mock):
        response = dumps({
            "maxResults": 3,
            "total": 10,
            "issues": [
                {
                    "id": "100",
                    "key": "PROJECT-1",
                    "fields": {"summary": "Summary 1"}
                },
                {
                    "id": "200",
                    "key": "PROJECT-2",
                    "fields": {"summary": "Summary 2"}
                },
                {
                    "id": "300",
                    "key": "PROJECT-3",
                    "fields": {"summary": "Summary 3"}
                }
            ]
        })

        settings_mock.return_value = Settings({'trigger': 'HEY'})
        get_url_mock.return_value = response

        completer = JiraAutocomplete()
        suggestions = completer.on_query_completions(
            view=None, prefix='HEY', locations=None,
        )

        self.assertEqual(suggestions, [
            ('HEY' + ' Summary 1\tPROJECT-1', 'PROJECT-1'),
            ('HEY' + ' Summary 2\tPROJECT-2', 'PROJECT-2'),
            ('HEY' + ' Summary 3\tPROJECT-3', 'PROJECT-3'),
        ])

    @patch('timesheets.jira_completion.JiraCompleter._get_url')
    @patch('timesheets.jira_completion.load_settings')
    def test_simple_trigger_network_error(self, settings_mock, get_url_mock):
        settings_mock.return_value = Settings({'trigger': 'HEY'})
        get_url_mock.side_effect = HTTPError(
            Mock(status=400), 'mock error', None, None, None,
        )

        completer = JiraAutocomplete()
        suggestions = completer.on_query_completions(
            view=None, prefix='HEY', locations=None,
        )

        self.assertEqual(suggestions, [])
