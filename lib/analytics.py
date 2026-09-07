"""Attach the committed Vercel SDK bundle to production served pages only."""
from html import escape
import json
import os
from pathlib import Path

WEB = Path(__file__).resolve().parents[1] / 'web'


def analytics_script():
    if os.environ.get('VERCEL_ENV') != 'production':
        return ''
    config = json.loads(os.environ.get('VERCEL_OBSERVABILITY_CLIENT_CONFIG') or '{}')
    if not isinstance(config, dict):
        raise ValueError('VERCEL_OBSERVABILITY_CLIENT_CONFIG must be a JSON object')
    # Only these public SDK settings belong in browser HTML.
    config = {key: config[key] for key in ('analytics', 'speedInsights') if key in config}
    for value in config.values():
        if not isinstance(value, dict):
            raise ValueError('Vercel analytics settings must be JSON objects')
    config_attr = escape(json.dumps(config, separators=(',', ':')), quote=True)
    bundle = (WEB / 'analytics.min.js').read_text()
    if '</script' in bundle.lower():
        raise ValueError('Analytics bundle contains an unsafe inline script terminator')
    return f'<script data-otm-analytics data-config="{config_attr}">{bundle}</script>'
