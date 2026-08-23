# old-time-maps

Old sheets, put back on the earth.

![Montana in Relief — Allan Cartography's 1991 shaded-relief sheet of Montana, georeferenced and draped over the elevation model it was drawn to describe](docs/montana-in-relief.webp)

<sub>*Montana in Relief* — the 1991 sheet on its own terrain, looking north at ×5 vertical exaggeration, with the sun in the northwest where the engraver put it.</sub>

Each sheet in this repository is a self-contained project: a pipeline that
georeferences a scan **without hand-picked control points**, and a one-file
WebGL build you can open straight from disk. There are four, spanning a
century and a quarter of Montana cartography:

| | sheet | year | the trick that georeferences it |
|---|---|---|---|
| [`gold/`](gold/) | *The Gold Regions* — W.W. de Lacy's map of Montana Territory | 1865 | border-tick combs; the degree labelling is chosen by laying the surveyed state boundary along his red territory line (it agrees to 98 %) |
| [`glacier/`](glacier/) | *Glacier in Contours* — the USGS-engraved park sheet | 1900–15 | image correlation against four already-georeferenced sibling quadrangles of the same survey — 2.7 px RMS |
| [`flathead/`](flathead/) | *The Flathead Country* — two Army Progressive Military Map sheets | 1920 & 1943 | the scans carry their own polyconic/NAD27 georeference; the pipeline datum-shifts, crops to the neatlines and tone-matches the join |
| [`montana/`](montana/) | *Montana in Relief* — Allan Cartography's shaded-relief sheet | 1991 | the state silhouette, ICP-fitted through a Lambert conic |

```bash
git clone https://github.com/johnymontana/old-time-maps.git
open old-time-maps/montana/montana-in-relief.html    # or any of:
open old-time-maps/glacier/glacier-in-contours.html
open old-time-maps/flathead/the-flathead.html
open old-time-maps/gold/gold-regions-1865.html
```

One self-contained file each — textures and all — no server and no build step.
They need a browser with WebGL; the labels want three web fonts from Google
Fonts and fall back cleanly if you are offline. On a machine that can't keep
up they shed pixel ratio and then cast shadows rather than frame rate, and
they honour `prefers-reduced-motion` by skipping the opening flight.

Every explorer shares the same instruments: a crossfade between the sheet and
a modern relief render toned in the sheet's own inks, per-pixel ray-marched
cast shadows under a draggable sun, click-two-points cross-sections, guided
flights, typographic labels placed by projection and de-collided every frame,
plan view, and a live lat/lon/elevation readout. Sources, methods and fit
residuals live in each sheet's **About** panel.

## montana — *Montana in Relief*

Allan Cartography's 1991 shaded-relief map of Montana (1:600,000, revised
1991, scanned at 15,000 × 9,521 px by the [American Geographical Society
Library at UWM](https://collections.lib.uwm.edu/digital/collection/agdm/id/17590/rec/20)),
georeferenced and draped over the elevation model it was drawn to describe.

The scan carries no coordinates. The printed map body is isolated from the
paper by saturation, its silhouette matched against the surveyed boundary
(US Census 2021) through a Lambert conformal conic — standard parallels 45°
and 49°, central meridian 109°30′ W — and a cubic polynomial fitted by ICP
against 8,700 densified boundary points. Residual: **1.3 px median, 2.8 px
RMS** on the 7,500 px working scan — about 180 m on the ground.

Special to this sheet: the modern-relief layer's hypsometric tints are
sampled from the elevation legend printed on the sheet itself, and six guided
flights tour the state's ranges.

![The same view with the layer slider pulled to the modern relief render](docs/montana-modern-relief.webp)

## glacier — *Glacier in Contours*

![Glacier in Contours — the 1915 USGS-engraved park sheet draped over its terrain, glacier margins riding the crest](docs/glacier-in-contours.webp)

The USGS-engraved topographic sheet of Glacier National Park — 100-ft
contours and hand-laid relief from the surveys of 1900–1912; this is the
Interior Department's 1915 administrative printing, scanned at 9,788 × 8,492
px by the [Library of Congress](https://www.loc.gov/item/2016586564/).
Going-to-the-Sun Road does not exist on it.

The sheet is registered against the survey's own 30-minute quadrangles —
Chief Mountain (1904), Kintla Lakes (1906), Nyack (1914), Marias Pass (1913),
which the USGS distributes already georeferenced. The 49th-parallel boundary
line seeds the alignment; shared linework (black culture, blue drainage) is
matched by image correlation at two scales, giving 38 control points.
Residual: **2.2 px median, 2.7 px RMS** — about 30 m on the ground.

Special to this sheet: the park's named glaciers ride the terrain as vector
overlays — their Little-Ice-Age maxima and their 2015 outlines, from USGS
ScienceBase — beside the ice the surveyors drew.

## flathead — *The Flathead Country*

![The Flathead Country — the Army's 1920 and 1943 sheets joined at the 48th parallel, draped over the valley](docs/flathead-country.webp)

Flathead Lake and its valley — Somers, Bigfork, Kalispell, Whitefish — on two
sheets of the U.S. Army's **Progressive Military Map**: the *Flathead Lake*
quadrangle (advance sheet 146-N-E/2, printed 1920 on tan paper) and the
*Kalispell* quadrangle (1669:30/31, compiled 1919, Army Map Service printing
1943), from the [USGS Historical Topographic Map
Collection](https://ngmdb.usgs.gov/topoview/). Planimetric compilations from
GLO plats and forest atlases — no contours; a pencilled note on the 1920
sheet reads *"not mapped by USGS."*

Both scans carry their georeference (polyconic on NAD27, 10.58 m/px); the
pipeline datum-shifts the grid, crops each sheet to its neatline, tone-matches
the 1943 printing to the 1920 paper, and draws their join at 48°00′ as a
visible hairline — checked against a dozen townsites to within about one scan
pixel. The steamboat route from Somers to Polson rides the lake as an
overlay, and the About panel says plainly what the township grid on the
reservation half of the lake meant in 1910.

## gold — *The Gold Regions, 1865*

![The Gold Regions — de Lacy's 1865 territory map as a state-shaped inlay, the MRDS mines layer over the western camps](docs/gold-regions.webp)

W.W. de Lacy's map of Montana Territory, drawn for its First Legislature in
the winter of 1864–65 — *"showing the gulch or placer diggings actually
worked, and districts where quartz (gold & silver) lodes have been
discovered to January 1st 1865"* — scanned at 8,984 × 6,634 px by the
[Library of Congress](https://www.loc.gov/item/2006629609/).

The sheet draws no internal graticule, only degree ticks along its borders
(Greenwich longitudes above, Washington longitudes below). Tick combs solve a
similarity; the degree labelling is chosen automatically as the one that lays
the surveyed state boundary along de Lacy's heavy red territory line — they
agree to 98 %, and the bottom border yields the sheet's own prime meridian
(de Lacy put Washington at 77°05′ W of Greenwich). Residual across 27 ticks:
about **5 px**. East of the divide his boundary tracks the modern survey
almost perfectly; in the northwest the fit exposes his guesswork, which is
the story. The terrain, grid and state-line mask are shared with `montana/`
verbatim — same state, same conic.

Special to this sheet: a *Mines & lodes* layer — four hundred gold and silver
producers from the USGS [MRDS](https://mrdata.usgs.gov/mrds/) database,
fetched over WFS at build time — over the map that started the rush.

## Controls

| | |
|---|---|
| drag | orbit |
| scroll | zoom toward the cursor |
| shift-drag | pan |
| **Cross-section**, then two clicks on the terrain | a profile between them; hover along the profile to run a marker down the line in 3-D |
| drag the sun dial — or focus it and use the arrow keys | move the light |
| click the sheet index, bottom right | fly to that corner of the sheet |
| <kbd>S</kbd> <kbd>C</kbd> <kbd>R</kbd> <kbd>P</kbd> | shadows · contours · reset view · plan view |
| <kbd>Esc</kbd> | end a flight, clear a cross-section, close the about panel |

![The explorer's interface: surface, illumination and label controls on the left, guided flights on the right](docs/montana-interface.webp)

## Layout

```
LICENSE                        MIT — the code only, not the scans
assemble_all.py                builds every sheet + the gallery into dist/
docs/                          screenshots used by this README, and the
                               research plan behind the expansion
lib/                           shared pipeline modules (projections, datums,
                               Terrarium DEM, georeferencing fits, encoders)
work/dem/                      Terrarium tile cache shared by all sheets
                               (gitignored)
<sheet>/                       montana, glacier, flathead, gold — each:
  <sheet>.html                 one-file build — just open it
  assets/                      drape.webp, height.webp, meta.json, card.webp
                               (committed; regenerating pulls big downloads)
  src/                         body.html, style.css, app1.js, app2.js,
                               assemble.py
  pipeline/                    build.py, places.py
  requirements.txt
vercel.json                    build assemble_all.py, serve dist/
```

The three newer sheets share one viewer chassis (`app1.js`/`app2.js` are
copies with all scale-dependent constants derived from the plate size, and
overlays, mines and UI defaults data-driven from `meta.json`); `montana/`
keeps its original code untouched. Height is decoded on the CPU into a
half-float RG texture (elevation in R, signed distance to the sheet or state
line in G) so the GPU can filter it.

`assets/` are committed even though they are generated: rebuilding them pulls
hundreds of MB and wants the scientific-Python stack, and the whole point of
the one-file builds is that they work for someone who wants neither.

## Rebuilding

```bash
pip install -r <sheet>/requirements.txt    # numpy, scipy, pillow (+ pyshp)
cd <sheet>
python3 pipeline/build.py     # fetches scans, DEM tiles, fits, re-encodes
python3 src/assemble.py       # writes the one-file build and dist/
python3 -m http.server -d dist 8000
```

Each `build.py` runs named stages (`fetch`, `georef`, `resample`, `encode` —
montana's differ slightly) that cache into `work/`; name a stage to start
there. DEM tiles cache once for all sheets in `work/dem/` at the repo root.
Every pipeline prints its fit residuals and writes QA overlays into `work/`
so you can see the georeference laid over the scan.

`assemble.py` fetches three.js r155 into `vendor/` on first run.

## Deploying

`vercel.json` builds the whole gallery. `assemble_all.py` is pure standard
library — Vercel runs it, gets `dist/`, and serves the landing page at the
root with each sheet at `/montana/`, `/glacier/`, `/flathead/`, `/gold/`:

```bash
vercel        # preview
vercel --prod
```

Any other static host works the same way: run `python3 assemble_all.py` and
upload `dist/`.

## Rights

The code here is yours: [MIT](LICENSE). The scans belong to their libraries:

- *Montana in Relief*: American Geographical Society Library, University of
  Wisconsin–Milwaukee — see their
  [rights statement](https://uwm.edu/libraries/digital-collections/copyright-digcoll/)
  before reusing the scan or anything derived from it.
- *Glacier in Contours* and *The Gold Regions*: Library of Congress,
  Geography and Map Division — "free to use and reuse."
- *The Flathead Country*: USGS Historical Topographic Map Collection — U.S.
  government work, public domain.
- Glacier margins: USGS NOROCK via ScienceBase; mines: USGS MRDS; elevation
  tiles: [Terrarium, open data](https://registry.opendata.aws/terrain-tiles/);
  boundaries: US Census. All public domain.

The research that chose these sheets — with a much longer list of candidates,
sources and archives — is in
[docs/expand-montana-plan.md](docs/expand-montana-plan.md).
