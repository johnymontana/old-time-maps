# old-time-maps

Old sheets, put back on the earth.

![Montana in Relief — Allan Cartography's 1991 shaded-relief sheet of Montana, georeferenced and draped over the elevation model it was drawn to describe](docs/montana-in-relief.webp)

<sub>*Montana in Relief* — the 1991 sheet on its own terrain, looking north at ×5 vertical exaggeration, with the sun in the northwest where the engraver put it.</sub>

Each sheet in this repository is a self-contained project: a pipeline that
georeferences a scan, and a one-file WebGL build you can open straight from
disk. There is one so far.

## montana — *Montana in Relief*

Allan Cartography's 1991 shaded-relief map of Montana (1:600,000, revised 1991,
scanned at 15,000 × 9,521 px by the [American Geographical Society Library at
UWM](https://collections.lib.uwm.edu/digital/collection/agdm/id/17590/rec/20)),
georeferenced and draped over the elevation model it was drawn to describe.

```bash
git clone https://github.com/johnymontana/old-time-maps.git
open old-time-maps/montana/montana-in-relief.html   # or just double-click it
```

One self-contained file — 7.8 MB, textures and all — no server and no build
step. It needs a browser with WebGL (any Chrome, Safari, Firefox or Edge from
the last few years); the labels want three web fonts from Google Fonts and fall
back cleanly if you are offline. On a machine that can't keep up it sheds the
pixel ratio and then the cast shadows rather than the frame rate, and it honours
`prefers-reduced-motion` by skipping the opening flight.

### What it does

- **Crossfade** between the 1991 engraving and a modern hypsometric render whose
  tints are sampled from the elevation legend printed on the sheet itself. The
  sheet is masked to the state line, so the historic map reads as an inlay in
  the surrounding terrain.
- **Per-pixel cast shadows**, ray-marched against the height field, under a sun
  you can drag around a compass dial. It starts in the northwest, where the
  sheet's own engraved light comes from.
- **Cross-sections** — click two points, get a profile with a curtain dropped
  through the terrain, and scrub it to move a marker along the line in 3-D.
- **Six guided flights** (Glacier, the Beartooths, the Bitterroot Front, the
  Missouri Breaks, the Rocky Mountain Front, the southwest ranges), each easing
  the exaggeration down as it drops into a range.
- Labels set the way a cartographer would: summits in letterspaced caps, waters
  in serif italic, ranges in wide small caps, towns in condensed sans — placed
  by projection, culled by terrain occlusion, and de-collided every frame.
- Contours, adjustable exaggeration, a plan view that flattens the sheet for
  reading, and a live lat/lon/elevation readout under the cursor.

![The same view with the layer slider pulled to the modern relief render](docs/montana-modern-relief.webp)

<sub>The same camera, layer slider pulled all the way over: the modern
hypsometric render, tinted from the legend printed on the 1991 sheet. The
slider crossfades between these two renderings of one palette.</sub>

### Controls

| | |
|---|---|
| drag | orbit |
| scroll | zoom toward the cursor |
| shift-drag | pan |
| **Cross-section**, then two clicks on the terrain | a profile between them; hover along the profile to run a marker down the line in 3-D |
| drag the sun dial — or focus it and use the arrow keys | move the light |
| click the sheet index, bottom right | fly to that corner of the state |
| <kbd>S</kbd> <kbd>C</kbd> <kbd>R</kbd> <kbd>P</kbd> | shadows · contours · reset view · plan view |
| <kbd>Esc</kbd> | end a flight, clear a cross-section, close the about panel |

![The explorer's interface: surface, illumination and label controls on the left, guided flights on the right](docs/montana-interface.webp)

### How the georeferencing works

The scan carries no coordinates. Rather than pick control points by hand:

1. The printed map body is isolated from the paper by saturation — Montana is
   tinted, the margins are not — giving a clean silhouette of the state.
2. That silhouette is matched against the surveyed boundary (US Census 2021
   cartographic boundary file) through a Lambert conformal conic projection with
   standard parallels 45° and 49° and central meridian 109°30′ W — the USGS
   state-base convention the sheet was compiled from.
3. A cubic polynomial in projected coordinates is fitted by ICP against 8,700
   densified boundary points, absorbing the paper's distortion and the seam
   where the two sheets were joined.

Residual: **1.3 px median, 2.8 px RMS** on the 7,500 px working scan — about
180 m on the ground, which is roughly the generalisation error of the boundary
file itself. Ridge for ridge, the 1991 engraving and the modern elevation model
line up.

Elevations are [Terrarium tiles](https://registry.opendata.aws/terrain-tiles/)
(SRTM/NED lineage) at zoom 10, resampled onto the same conic grid: 987 × 602 km
at 241 m per texture pixel and 362 m per height sample.

### Layout

```
LICENSE                        MIT — the code only, not the scan
docs/                          screenshots used by this README
montana/
  montana-in-relief.html       one-file build — just open it
  assets/                      drape.webp, height.webp, meta.json  (committed)
  src/                         body.html, style.css, app1.js, app2.js, assemble.py
  pipeline/                    build.py, places.py
  requirements.txt
vercel.json                    build assemble.py, serve montana/dist/
```

`app1.js` holds the data decode, projection and shaders; `app2.js` the camera
rig, labels, instruments, tools and flights. Height is decoded on the CPU into a
half-float RG texture (elevation in R, signed distance to the state line in G)
so the GPU can filter it — the packed 12-bit source can't be interpolated.

`assets/` is committed even though it is generated: rebuilding it pulls about
250 MB and wants the scientific-Python stack, and the whole point of the
one-file build is that it works for someone who wants neither.

### Rebuilding

```bash
pip install -r montana/requirements.txt   # numpy, scipy, pillow, pyshp
cd montana
python3 pipeline/build.py     # fetches the scan, ~1,000 DEM tiles, refits, re-encodes
python3 src/assemble.py       # writes montana-in-relief.html and dist/
python3 -m http.server -d dist 8000
```

`build.py` runs five stages — `fetch`, `mask`, `fit`, `resample`, `encode` —
each caching into `work/` (gitignored; set `MT_WORK` to put it elsewhere). Name
a stage to start there: `python3 pipeline/build.py encode` re-encodes without
re-downloading. Want more detail? Raise `TEX_W` / `HGT_W` in
`pipeline/build.py` — 4096/2730 is tuned to keep the one-file build near 8 MB,
which is what the hosted Artifact version needs. Served from `dist/`, there is
no such ceiling.

`assemble.py` fetches three.js r155 into `vendor/` on first run, so that step
wants a network connection once.

### Deploying

`vercel.json` deploys the served build. `assemble.py` is pure standard library,
so there is nothing to install — Vercel runs it, gets `montana/dist/`, and
serves that at the root:

```bash
vercel        # preview
vercel --prod
```

Import the repository at Vercel and leave the project's root directory at the
repository root; `vercel.json` handles the rest. `dist/` is deliberately
gitignored and rebuilt on every deploy, which takes under a second, so the
served build can never drift from `src/`. Any other static host works the same
way: run the two commands under **Rebuilding** and upload `montana/dist/`.

### Rights

The scan belongs to the American Geographical Society Library, University of
Wisconsin–Milwaukee; see their
[rights statement](https://uwm.edu/libraries/digital-collections/copyright-digcoll/)
before reusing it — that covers `montana/assets/drape.webp` and the screenshots
in this README, both of which are derived from it. Elevation tiles are
[open data](https://registry.opendata.aws/terrain-tiles/); the boundary file is
US Census public domain. The code here is yours: [MIT](LICENSE).
