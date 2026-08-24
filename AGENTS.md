# AGENTS.md — working on old-time-maps

Instructions for AI agents (and human contributors) working in this
repository. Everything here was learned the hard way while building the
first fifteen sheets; treat the gates as gates, not suggestions.

## What this project is

Historical map scans, georeferenced **without hand-picked control points**
and draped over open elevation data in a one-file WebGL viewer. Each sheet
is a self-contained directory: a Python pipeline that reproduces the assets
from public sources, and a viewer build that opens from disk. A pure-stdlib
`assemble_all.py` builds the whole gallery into `dist/`.

## Ground rules

1. **Public domain only.** LOC "free to use", USGS/HTMC/GNIS/federal works,
   and Internet Archive–hosted Rumsey uploads (`dr_` items; the underlying
   works must be PD by age — credit "scan via the David Rumsey Map
   Collection"). No CC-NC/SA material, no fair-use gambles.
2. **No hand-picked control points.** Automated detection (border-tick
   combs, silhouette ICP, correlation) supplies every fitted point.
   *Seeds* are allowed: printed values read once and documented in code —
   two townsite symbols, a graticule corner — as long as correlation or a
   printed-graticule construction does the actual fitting.
3. **Honest residuals.** Every About panel states the fit numbers and what
   they mean. Same-lineage registrations (a folio plate over the quad it
   was printed on) must reach **≤ 6 px RMS**; redrawn/sketch/commercial
   sources plateau at their true disagreement (150 m – 8 km across this
   gallery) — accept the plateau and *say the number*, never hide it.
4. **The land's history is stated plainly.** Every sheet stands on
   Indigenous homeland; at least one tour caption and the About sources
   paragraph say so specifically (nation, treaty, event — not vaguely).
   Allotment, removal, massacre and cession materials are presented with
   plain provenance, never omitted, never decorated.
5. **Committed generated assets.** `assets/` (drape/height/alt webp +
   meta.json + card.webp) and the one-file `<sheet>.html` are committed;
   `work/`, `dist/`, `vendor/` are gitignored. Rebuilding pulls hundreds
   of MB — the committed assets are the point.
6. **Don't push, don't publish.** Commit locally with clear messages;
   pushing and PRs happen only when the maintainer asks.

## Repo map

```
assemble_all.py     builds every sheet + the grouped landing page into dist/
lib/                shared pipeline modules:
  proj.py             Lambert conic (unit sphere!), polyconic, Molodensky
                      NAD27<->WGS84, inverse TM, poly_basis
  dem.py              Terrarium tiles: fetch/mosaic/void-repair/sample;
                      shared cache work/dem/ (env OTM_DEM_CACHE)
  georef.py           QuadGeoref (HTMC GeoTIFF geokeys -> to_px), Fit,
                      fit_report, overlay QA renderer
  reg.py              correlation registration: register(), fit_trimmed(),
                      feature_mask (black+blue — see mask note below)
  encode.py           Grid, encode_height/drape, snap_places, write_meta
<sheet>/            montana, gold, missouri, paradise, yellowstone, glacier,
                    bitterroot, front, rails, flathead, libby, tacoma,
                    coeurdalene, silverton, nome — each:
  pipeline/build.py   stages: fetch, georef, resample, encode (chained:
                      running an early stage runs everything after it)
  pipeline/places.py  PEAKS/CITIES/FEATURES/TOURS (+ data-layer lists)
  src/                body.html, style.css, app1.js, app2.js, assemble.py
  assets/             committed build products
  work/               gitignored caches + QA renders
art/                the Flat Wing: flat pieces, stdlib-typeset page
docs/               README heroes, research plans, candidates memos
```

## Environment & commands

- Python ≥ 3.10 with `numpy scipy pillow pyshp pypdfium2` (per-sheet
  `requirements.txt`). No node needed; `assemble.py` fetches three.js r155
  into `vendor/` on first run.
- Build one sheet: `cd <sheet> && python3 pipeline/build.py` (or name a
  stage to start there — stages cache into `work/` and **chain onward**).
- Assemble one sheet: `python3 src/assemble.py` (from the sheet dir).
- Whole gallery: `python3 assemble_all.py`, serve with
  `python3 -m http.server -d dist 8000`.
- Concurrent builds of different sheets are safe: they touch disjoint
  directories and the shared DEM cache tolerates parallel writers of
  different tiles.

## The viewer chassis

- Source of truth: `flathead/src/app1.js` + `app2.js`. Edit there, copy to
  every other v2 sheet, and re-run each sheet's `assemble.py`.
  **`montana/src` is a diverged fork** — port changes to it by hand.
- Everything sheet-specific is data-driven from `assets/meta.json`
  (written by `encode.py write_meta`): grid, ramp, places, tours, `mines`
  (the data layer), and `ui`:
  - `sheetA` / `altName` — crossfade layer names (short: "1912 network")
  - `mineGlyph` — data-layer glyph (⚒ default; ♨ ⚓ ∩ in use)
  - `contourM` — the sheet's own contour interval in metres
  - `rampLo`/`rampHi` — hypsometric ramp span in feet.
    **rampLo 0 is treated as unset (JS falsy) — use 1 for sea-level sheets.**
  - `exagDef`, `exagMax`, `mineDist`, `tourEx`
- The shader "re-inks" at magnification: unsharp gated by texel density
  (`smoothstep(0.08, 0.30, tpp)`) so halftone dot-screens don't amplify,
  plus an ink-gradient emboss with a tapered bell. `window.TUNE` exposes
  the uniforms for live tuning in the console.
- Alt (middle) layers load via `window.MT_ALT`; a sheet without one simply
  omits it and the slider becomes two-stop.

## Adding a sheet — the recipe

1. Scaffold: `mkdir -p <dir>/{pipeline,src,work}`; copy
   `yellowstone/src/{app1.js,app2.js,style.css,assemble.py}` into `src/`;
   copy any sheet's `requirements.txt`.
2. Pick the closest pipeline as a template and keep its skeleton exactly:
   - 4 plates over 4 own-lineage quads → `yellowstone/pipeline/build.py`
   - 1 plate over 1 base (base doubles as alt) → `libby/…` (with the
     high-pass ink mask, not lib/reg's colour mask)
   - 2 quads joined N–S / E–W (+ anchor-seeded alt) → `bitterroot/…`,
     `missouri/…`; 2×2 → `front/…`
   - non-georeferenced maps on another sheet's grid → `rails/…`
     (registers against **montana's own drape** as correlation target)
   - printed-graticule fit, no georeferenced base → `nome/…`
3. Texture sizing: ~25–40 m/texel (TEX_W 2048–4096 by block size);
   HGT_W ≈ ⅔·TEX_W; ALT_W ≈ 0.6–0.75·TEX_W; DEM zoom 12 for ≤ 2° blocks;
   CLAMP just outside the block's real range (check `hmin/hmax` after the
   first encode — a tight ceiling decapitates summits into infill).
4. `places.py`, `src/body.html` (derive from `front/src/body.html`, replace
   the whole About div), `src/assemble.py` TITLE/BLURB/ONE.
5. Integration (maintainer loop, not build agents): `assemble_all.py` card
   with a `g=` state group, `vercel.json` route alternation,
   `.gitattributes` linguist-generated line for the one-file build, README
   table row + section, `docs/` hero webp from a browser capture.

## Registration playbook

- **Masks.** `lib/reg.feature_mask` sees black culture + blue drainage —
  it goes *blind* on brown contour plates under colour washes. For
  engraved siblings use the **local high-pass ink mask** (pixels darker
  than their 12-px neighbourhood by >30, then gaussian 1.4; copy from
  `yellowstone/pipeline/build.py`). It took folio-over-base fits from
  9 control points to 85+, at 1–2 px.
- **Anchor seeds.** Copy the SeedAff construction from
  `bitterroot/pipeline/build.py` **exactly** — `m_scan` needs the
  `6371000.0 *` factor because `Lcc.fwd` returns unit-sphere coordinates;
  `1/s_` alone yields 0.00 m/px and a PiB `ndimage.zoom` crash.
- **Ladders widen before they tighten.** Each seeded pass's search window
  must exceed the previous pass's *worst* residual, or matches clamp and
  the fit silently plateaus. Typical: sw 130–260 → deg-1 trim → sw 70–110
  → deg-2 (same lineage) or deg-3 (sketch/commercial).
- **Restrict candidates to shared ink.** If matches scatter uniformly at
  km scale on a sketch source, the mountain hatching is lying to you —
  lattice only where both maps drew the same things (valley grids,
  drainage). This took Leiberg 1898 from 1.4 km to 150 m.
- **Uniform residuals with nothing trimmed = real disagreement**, not a
  bad fit. De Lacy's manuscript sits ~7 km from the print; Ayres' 1899
  reconnaissance sits ~a mile from the quads; Cram 1884 is off by five
  miles in the east. Bend a cubic, accept, and write it in the About.
- **Atlas book spreads**: detect the binding fold (darkest smoothed column
  mid-span) and fit each page separately (`rails/`).
- **Printed-graticule fit** (no georeferenced base, e.g. Alaska): measure
  every drawn graticule crossing via ruler-grid crops, deg-1 Fit, trim
  warped corners, state the era-datum caveat (`nome/`).

## Source cookbook (all verified in production)

- **HTMC GeoTIFFs** (georeferenced, polyconic/NAD27 — the backbone):
  inventory via S3 listing
  `https://prd-tnm.s3.amazonaws.com/?list-type=2&prefix=StagedProducts/Maps/HistoricalTopo/GeoTIFF/{ST}/{ST}_{Name}&max-keys=200`;
  filenames `{ST}_{Name}_{scanid}_{year}_{scale}_geo.tif`. Verify
  neatlines with `lib/georef.QuadGeoref` corner probes before trusting.
  **Alaska HTMC is Transverse Mercator and QuadGeoref rejects it.**
- **Geologic Atlas folios**: `https://pubs.usgs.gov/gf/{NNN}/`
  (zero-padded) → `quad-*_*.pdf` plates + `text.pdf` (page 1 states the
  quad's bounds — extract with pypdfium2). PPs/Bulletins/Monographs:
  `/pp/00NN/`, `/bul/0NNN/`, `/mono/NN/` (`plate-N.pdf` or `report.pdf`;
  some plates are hundreds of MB — render at the resolution you need).
- **Annual-report forest atlases**: `/ar/19-5/`, `/ar/20-5/`, `/ar/21-5/`.
  **File numbers are sequential and do NOT match the plate numerals** —
  identify by rasterizing the title strip. (Bitterroot Reserve =
  ar/20-5/plate-59.pdf, printed "PL. CXIV".)
- **Library of Congress**: JSON API needs a full browser User-Agent.
  Search `/search/?q=…&fa=original-format:map&fo=json`; item
  `/item/{id}/?fo=json` → `resources[].files` full JP2s on tile.loc.gov.
  Collections: panoramic-maps (bird's-eyes), sanborn-maps.
- **Internet Archive**: `advancedsearch.php` + `metadata/{id}`. Rumsey
  `dr_` items sometimes carry full JP2s, sometimes **only unreadable
  .sid** — check the file list before promising an edition.
- **GNIS**: `StagedProducts/GeographicNames/DomesticNames/DomesticNames_{ST}_Text.zip`
  (pipe-delimited, decimal coords). **The live product retired the Mine
  feature class (~2021)** — for mine layers use the frozen 2021 archive
  (`Archive/MainDomestic/{ST}_Features_20210825`) or USGS USMIN, and say
  which in the About.
- **MRDS mines**: WFS at mrdata.usgs.gov (cached repo-wide in
  `gold/work/mrds.json` for Montana).
- **Terrain**: Terrarium tiles (AWS open data), z10–12; shared cache
  `work/dem/`. The DEM is truth — when a "known" summit elevation
  disagrees with it, the DEM has been right every single time.

## Places & prose quality gates

- Coordinates come from **GNIS only** — never from memory. (Memory once
  placed Electric Peak 13 km wrong; the DEM caught it.)
- Every PEAK must verify against the model within **±130 m** of its
  claimed feet (argmax hunt within ~600 m). Drop failures — never guess
  feet. `snap_places` at encode must print **zero warnings**.
- Tours: 4–5 per sheet, four keys each `(lat, lon, d km, az, el 13–18)`,
  captions in the house voice — specific years, names, numbers, checkable
  claims, no purple filler. Read `bitterroot/pipeline/places.py` and
  `yellowstone/src/body.html` before writing a word.

## QA checklist (browser, before any commit)

Serve `dist/` and, per sheet: boots with zero console errors; all three
crossfade stops show the right labels; the data glyph renders; one flight
flown (60 fps: p95 frame time < 20 ms via a rAF probe); plan view is
north-up; About panel renders with real numbers. Gallery page shows every
card under its state header; the Flat Wing counts its figures. One-file
builds stay ≲ 12 MB.

## Git conventions

Commit messages: a short title in the project's plain-spoken voice, then a
body that says what was built and what the numbers are. One commit per
sheet; integration (gallery/README/routes) separate. End with the
Co-Authored-By trailer your harness specifies. Never push or open PRs
unprompted.
