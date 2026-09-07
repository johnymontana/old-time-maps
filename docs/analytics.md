# Vercel analytics

The site uses `@vercel/analytics` 2.0.1 for Web Analytics and
`@vercel/speed-insights` 2.0.0 for performance measurements. These were the
latest stable npm releases when installed on September 7, 2026; exact
versions are recorded in `package.json` and `package-lock.json`.

## What is collected

Web Analytics provides page views, visitors and traffic breakdowns such as
pages, referrers, countries, browsers and devices. Speed Insights provides
page-performance measurements. The available metrics, retention and usage
allowances depend on the Vercel plan. This integration uses the SDK defaults
and does not add custom click or download events.

The gallery, all 25 terrain viewers and the Flat Wing load both SDKs when
built with `VERCEL_ENV=production`. Preview deployments and ordinary local
builds omit them. The committed one-file HTML viewers always omit analytics;
even a production served page opened locally cannot start collection over
`file://`, HTTP or a loopback hostname.

## Build and maintain

From the repository root, with Node.js and Python 3.10+ available:

```sh
npm ci --include=dev --ignore-scripts
npm run build
npm test
python3 -m http.server -d dist 8000
```

`npm run build:analytics` bundles `web/analytics.js` with esbuild into the
committed `web/analytics.min.js` and refreshes its license notices. The
bundle includes the installed Vercel packages and is inlined only into
production served pages by `lib/analytics.py`. Website assembly itself
remains stdlib Python: `python3 assemble_all.py` can use the committed
bundle without Node. Printing continues to use its separate uv project.

Vercel runs `npm ci --include=dev --ignore-scripts` and `npm run build`, as configured in
`vercel.json`; `--include=dev` keeps esbuild available even when
`NODE_ENV=production`. Its `VERCEL_OBSERVABILITY_CLIENT_CONFIG` JSON is forwarded to
the SDKs for deployment-specific script and intake routes. Only its public
`analytics` and `speedInsights` sections are embedded. Without that config,
the packages use their `/_vercel/insights/` and `/_vercel/speed-insights/`
defaults. No analytics token is embedded in the site.

To update the packages deliberately:

```sh
npm install --save-exact @vercel/analytics@latest @vercel/speed-insights@latest --ignore-scripts
npm run build
npm test
```

Commit package manifests, the generated bundle and license notices together.
When adding a page, call the shared `analytics_script()` helper in its
served HTML builder. Keep that call out of one-file artifact builds.

## Vercel dashboard

Enable **Web Analytics** for the Vercel project, then deploy the integration
when the maintainer requests deployment. Open **Analytics** for traffic and
**Speed Insights** for performance; any plan upgrade is a separate account
choice. Package installation does not itself enable the dashboard or
publish the site.

After deployment, verify both SDK scripts load on the production domain
and collection requests succeed. Metrics appear after real visits; local
browser checks only verify integration and cannot confirm live ingestion.

Official references: [Web Analytics setup](https://vercel.com/docs/analytics/quickstart),
[Analytics configuration](https://vercel.com/docs/analytics/package),
[Speed Insights setup](https://vercel.com/docs/speed-insights/quickstart),
[Web Analytics pricing](https://vercel.com/docs/analytics/limits-and-pricing),
and [Speed Insights pricing](https://vercel.com/docs/speed-insights/limits-and-pricing).
