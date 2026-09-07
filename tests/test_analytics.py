from html.parser import HTMLParser
import json
import os
from pathlib import Path
import unittest
from unittest.mock import patch

from lib.analytics import analytics_script


class Scripts(HTMLParser):
    def __init__(self):
        super().__init__()
        self.tags = []

    def handle_starttag(self, tag, attrs):
        self.tags.append((tag, dict(attrs)))


class AnalyticsTests(unittest.TestCase):
    def test_local_and_preview_builds_do_not_load_analytics(self):
        for environment in ('', 'development', 'preview'):
            with self.subTest(environment=environment), patch.dict(
                os.environ, {'VERCEL_ENV': environment}, clear=True
            ), patch.object(Path, 'read_text', side_effect=AssertionError('read analytics bundle')):
                self.assertEqual(analytics_script(), '')

    def test_production_uses_installed_sdks_and_public_configuration_only(self):
        public = {
            'analytics': {'scriptSrc': '/metrics/script.js', 'viewEndpoint': '/metrics/view'},
            'speedInsights': {'scriptSrc': '/speed/script.js', 'endpoint': '/speed/vitals'},
        }
        with patch.dict(os.environ, {
            'VERCEL_ENV': 'production',
            'VERCEL_OBSERVABILITY_CLIENT_CONFIG': json.dumps({**public, 'unrelated': 'do-not-publish'}),
        }, clear=True):
            result = analytics_script()
        parsed = Scripts()
        parsed.feed(result)
        self.assertEqual(len(parsed.tags), 1)
        self.assertEqual(parsed.tags[0][0], 'script')
        self.assertEqual(json.loads(parsed.tags[0][1]['data-config']), public)
        self.assertNotIn('do-not-publish', result)
        self.assertIn('@vercel/analytics', result)
        self.assertIn('@vercel/speed-insights', result)

    def test_configuration_cannot_break_out_of_html_attribute(self):
        value = '/metrics/\"><script>alert(1)</script>&script.js'
        with patch.dict(os.environ, {
            'VERCEL_ENV': 'production',
            'VERCEL_OBSERVABILITY_CLIENT_CONFIG': json.dumps({'analytics': {'scriptSrc': value}}),
        }, clear=True):
            parsed = Scripts()
            parsed.feed(analytics_script())
        self.assertEqual(len(parsed.tags), 1)
        self.assertEqual(json.loads(parsed.tags[0][1]['data-config'])['analytics']['scriptSrc'], value)

    def test_missing_configuration_uses_sdk_defaults_and_invalid_config_fails(self):
        with patch.dict(os.environ, {'VERCEL_ENV': 'production'}, clear=True):
            self.assertIn('data-config="{}"', analytics_script())
        for value in ('not json', '[]', '{"analytics": []}'):
            with self.subTest(value=value), patch.dict(os.environ, {
                'VERCEL_ENV': 'production', 'VERCEL_OBSERVABILITY_CLIENT_CONFIG': value,
            }, clear=True), self.assertRaises(ValueError):
                analytics_script()


if __name__ == '__main__':
    unittest.main()
