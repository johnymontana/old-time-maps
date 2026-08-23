# Expand Montana — the Flathead & Glacier sheets

*Working plan for the `expand-montana` branch. Researched August 2026 against the
David Rumsey Collection, Library of Congress, USGS (TopoView / NGMDB / Pubs
Warehouse), Montana Memory Project, MBMG, BLM GLO records, NPS History eLibrary
and the American Geographical Society Library. Every URL below was fetched and
verified live unless marked otherwise.*

The goal: grow the gallery from one sheet to a small wing of northwest
Montana — Flathead Lake, Bigfork, Kalispell and Glacier National Park — with a
second wing for the maps that drew people here in the first place: the gold and
mineral sheets. Each new sheet keeps the house rules: a pipeline that
georeferences the scan without hand-picked control points, a one-file WebGL
build you can open from disk, honest residuals in the About panel, and the
original's cartographic language reproduced — then quietly extended — rather
than replaced.

---

## 1 · What the montana sheet already gives us

Read of the existing code (`montana/pipeline/build.py`, `src/app1.js`,
`src/app2.js`, `src/assemble.py`):

**Reusable as-is (roughly 60 % of the pipeline):**
- Terrarium DEM fetch → mosaic → void repair → conic-grid resample
  (`fetch_dem`, `resample`) — parameterised only by bbox, zoom and grid.
- The Lambert conformal conic forward/inverse and the polynomial basis.
- The encode stage: 12-bit height + signed-distance packing into `height.webp`,
  drape resample → `drape.webp`, `meta.json` with places snapped to summits.
- The whole viewer chassis: camera rig, ray-marched shadows, labels with
  occlusion culling and de-collision, cross-sections, tours, sun dial,
  minimap, perf watchdog, `assemble.py`'s two-build output.

**Montana-specific (needs a per-sheet replacement):**
- The georeferencing strategy (state-silhouette ICP — only works when the sheet
  shows the whole state).
- The hypsometric legend sampler (`legend_ramp` hard-codes swatch pixel rows).
- `places.py` (labels + tours), masthead/About copy, the elevation void
  thresholds `(300, 4200)`, DEM zoom 10, standard parallels 45°/49°.

**Proposed refactor (small, honest):** keep every sheet self-contained in its
own directory, but lift the truly generic pipeline pieces into a top-level
`lib/` (`lib/proj.py`, `lib/dem.py`, `lib/georef.py`, `lib/encode.py`) that
each sheet's `pipeline/build.py` imports via a two-line `sys.path` shim — the
same way `build.py` already imports `places.py`. Viewers stay copied and
bespoke per sheet; that duplication is the point of the project. The shipped
HTML remains dependency-free either way.

---

## 2 · The sheets

### Tier 1 — the three new hero sheets

#### `glacier/` — *Glacier in Contours* (USGS, surveyed 1900–1912)

The engraved topographic map of Glacier National Park: 100-ft contours over the
Lewis and Livingston ranges, blue glaciers at their Little-Ice-Age size, drawn
by the survey parties that mapped the park before the road existed.

| | |
|---|---|
| Primary scan | *Administrative map of Glacier National Park* (Interior/USGS, 1915; R.B. Marshall & H.L. Baldwin) — LOC item [2016586564](https://www.loc.gov/item/2016586564/), JP2 9,788 × 8,492 px (24 MB), TIFF master 249 MB, IIIF Image API on tile.loc.gov, LOC G&M "free to use and reuse" |
| Alternate editions | The same engraved base exists in four states on the Montana History Portal (all free full-res JPEG via its `downloadwiz` endpoint; portal labels "Copyright Not Evaluated" but these are US-government works, public domain by nature): **1911 first edition** [nodes/view/87649](https://www.mtmemory.org/nodes/view/87649) (surveys 1900–1910), **1914** [nodes/view/87650](https://www.mtmemory.org/nodes/view/87650) (6,160 × 5,480 px), **1922** [nodes/view/45381](https://www.mtmemory.org/nodes/view/45381) (7,345 × 6,585 px, roads/trails updated). Stanford holds a 1914 JPEG2000 marked public domain ([stacks rz850sg4562](https://stacks.stanford.edu/object/rz850sg4562)). The LOC 1915 scan is the sharpest; the 1911 is the purist's first state; pick by scan quality at fetch time. Not in TopoView — confirmed a collection gap, so we georeference it ourselves. |
| Georeferencing | graticule/neatline fit (§4-B) — the sheet's corners and internal graticule are exact coordinates |
| Terrain | Terrarium z13 (~13 m/px at 48.6°N); sheet spans ~96 × 88 km |
| Signature features | crossfade sheet ↔ modern relief as today; **glacier-margin overlay** — USGS vector perimeters for the 37 named glaciers: Little-Ice-Age maxima ([ScienceBase 5b194f1c](https://www.sciencebase.gov/catalog/item/5b194f1ce4b092d965237f5f)) and the 1966/1998/2005/2015 time series ([ScienceBase 58af7022](https://www.sciencebase.gov/catalog/item/58af7022e4b01ccd54f9f542)) draped as lines over the engraved blue of 1912 — the sheet becomes a measurement, not a picture. Optional third layer, stretch: Ross's colored geologic map of the park (PP 296 Plate 1, [pubs.usgs.gov/pp/0296/plate-1.pdf](https://pubs.usgs.gov/pp/0296/plate-1.pdf), 1:125,000, same footprint) for a three-way crossfade: engraving ↔ geology ↔ modern relief. |
| Tours | Going-to-the-Sun (absent from the 1914 sheet — completed 1933, which *is* the story), Many Glacier & Grinnell, Sperry/Blackfoot ice, Chief Mountain klippe, Marias Pass |
| Contour interval | 100 ft — wire `uContourInt` to 30.48 m so the synthetic contours land on the engraved ones |

#### `flathead/` — *The Flathead Country* (USGS 30′ quads, 1920 + 1943)

Flathead Lake and its valley — Somers, Bigfork, Kalispell, Whitefish — from the
engraved 1:125,000 series. Two sheets joined at the 48th parallel, which
crosses the lake just north of Big Arm: the *Flathead Lake* quad (1920, the
earliest sheet of the lake) below the line, the *Kalispell* quad (1943, its
only edition) above it. The montana sheet was itself two sheets joined at a
seam; this one wears its seam as a date line, and the About panel says so.

| | |
|---|---|
| Scans | TopoView HTMC GeoTIFFs, 300 dpi, **already georeferenced**, verified: [MT_Flathead Lake_472710_1920](https://prd-tnm.s3.amazonaws.com/StagedProducts/Maps/HistoricalTopo/GeoTIFF/MT/MT_Flathead%20Lake_472710_1920_125000_geo.tif) (5.0 MB) · [MT_Kalispell_472788_1943](https://prd-tnm.s3.amazonaws.com/StagedProducts/Maps/HistoricalTopo/GeoTIFF/MT/MT_Kalispell_472788_1943_125000_geo.tif) (3.9 MB) |
| Georeferencing | embedded in the GeoTIFF (§4-A); neatline-corner detection crops the collar and cross-checks the embedded transform |
| Terrain | Terrarium z12 (~25 m/px); mosaic spans ~60 × 110 km (two 30′ cells) |
| Signature features | tone-matched mosaic across the 1920/1943 seam (histogram match in the overlap-free join, seam drawn honestly as a hairline); steamboat-era story labels — Demersville (the head-of-navigation town that died when the railroad chose Kalispell, absent from both sheets), Somers mill, the 1902 Bigfork dam; a note that Kerr Dam (1938) raised the lake ~10 ft between the two sheets' dates, so the 1920 shoreline is the *natural* lake. Stretch: a third crossfade skin from the **Jaqueth & Walters 1908 map of Flathead County** ([mtmemory 87673](https://www.mtmemory.org/nodes/view/87673), 5,889 × 6,538 px) — same country two decades earlier, with steamboat routes, coal/oil symbols and the *proposed* Glacier park drawn in |
| Tours | Around-the-lake steamboat run, Bigfork & the Swan front, Kalispell vs Demersville, Whitefish & the Great Northern |
| Extension ring | six more verified early quads tile outward when wanted: Chief Mountain 1904, Kintla Lakes 1906, Nyack 1914, Stryker 1916, Marias Pass 1913, Browning 1903 (same S3 URL pattern, all 300-dpi georeferenced GeoTIFFs) |

#### `gold/` — *The Gold Regions, 1865* (W.W. de Lacy)

The first map of Montana Territory, drawn by its first surveyor the year after
the territory was created: "showing the gulch or placer diggings actually
worked and districts where quartz (gold & silver) lodges have been discovered
to January 1st 1865." Hachured ranges, wrong rivers, and the gold camps that
were the entire point.

| | |
|---|---|
| Primary scan | LOC item [2006629609](https://www.loc.gov/item/2006629609/) (1865 first state) — JP2 8,984 × 6,634 px, TIFF master 179 MB, IIIF verified, LOC G&M free-to-use, no rights advisory |
| Alternate states | Four other lives of the same map, all verified: de Lacy's **original pen-and-pencil manuscript on linen** at the Montana Historical Society ([mtmemory 87729](https://www.mtmemory.org/nodes/view/87729), 7,165 × 5,506 px — hand-drawn hachures, visually extraordinary); a 400-dpi print copy on the portal ([mtmemory 45333](https://www.mtmemory.org/nodes/view/45333), 8,000 × 6,160); LOC [2006629627](https://www.loc.gov/item/2006629627/) — the same stone annotated in manuscript to Feb 1871 (9,637 × 7,120); and Rumsey's 1872 Colton re-engraving with a color key for gold/silver/copper/iron/coal mines ([RUMSEY~8~1~1779~180060](https://www.davidrumsey.com/luna/servlet/detail/RUMSEY~8~1~1779~180060), 12,834 × 9,015, CC BY-NC-SA 3.0). A "states of one map: manuscript → 1865 → 1871 → 1872" toggle is a natural stretch feature. |
| Georeferencing | silhouette ICP as for montana (the 1864 territory boundary *is* the state boundary) **anchored by graticule intersections** (§4-C), degree ≤ 2 — the drawn geography is 1865-crude in the northwest, and the residual map is part of the story, not a bug to hide |
| Terrain | reuse the montana conic grid and DEM verbatim — same footprint |
| Signature features | the crossfade companion is a **sepia relief** in the sheet's own inks (paper cream, hachure brown); a **mines & districts layer** from USGS [MRDS](https://mrdata.usgs.gov/mrds/) (public domain, shapefile/CSV) filtered to gold/silver within the sheet, so the 1865 diggings sit beside every mine that came after; label class for the named gulches (Alder, Last Chance, Confederate…) |
| Tours | Alder Gulch & Virginia City, Last Chance & Helena, the Kootenai trail northwest (where the map runs out of facts), Fort Benton & the river road |

### Tier 2 — supporting sheets & overlay layers (post-hero backlog, in rough order)

1. **Libby gold & geology** — *Geology and ore deposits of the Libby
   quadrangle* (USGS Bulletin 956, 1948; colored geologic quad map,
   [plate 1](https://pubs.usgs.gov/bul/0956/plate-1.pdf) 4.4 MB) over Cabinet
   Mountains terrain, with *Gold-quartz veins south of Libby* (Circular 7,
   1934, [report](https://pubs.usgs.gov/circ/0007/report.pdf)) for the
   district story — the real northwest-Montana gold country. A fourth sheet
   when the wing wants deepening.
2. **Ross PP 296 geology plates** (1959) — beyond Plate 1's park geology,
   [Plate 2](https://pubs.usgs.gov/pp/0296/plate-2.pdf) covers the Flathead
   region quads; candidate alternate skin for *both* hero sheets.
3. **Northern Boundary Commission, Joint Map XXIV** (1878, 1:126,720 hachured
   strip along the 49th parallel at Glacier's north edge; Rumsey
   [RUMSEY~8~1~231814~5509054](https://www.davidrumsey.com/luna/servlet/detail/RUMSEY~8~1~231814~5509054),
   11,851 × 7,966) — a draped band overlay for `glacier/`.
4. **Ayres forest-reserve classification plates** (USGS Annual Reports,
   1898–1900, public domain) — *Lewis and Clark Forest Reserve* as a clean
   standalone plate PDF ([pubs.usgs.gov/ar/21-5/plate-003.pdf](https://pubs.usgs.gov/ar/21-5/plate-003.pdf),
   3.4 MB, Julius Bien litho; also at Rumsey, 6,412 × 7,070); the **Flathead
   Forest Reserve 1898** plates (the future Glacier NP classified by timber and
   burns) live inside the 20th Annual Report Part V volume PDF
   ([pubs.usgs.gov/ar/20-5/report.pdf](https://pubs.usgs.gov/ar/20-5/report.pdf),
   Plate LXXVII at PDF p. 336 plus species-distribution plates; extract with
   `pdfimages` — the archive.org copy of the atlas was scanned still folded and
   is unusable).
5. **Alden, *Physiography and glacial geology of western Montana*** (PP 231,
   1953, [plate 1](https://pubs.usgs.gov/pp/0231/plate-1.pdf) 12.3 MB) — the
   ice-age Flathead Lobe as an overlay for `flathead/`.
6. **GLO territory sheets** — Roeser 1879 (LOC [2007627959](https://www.loc.gov/item/2007627959/),
   9,891 × 7,542, free-to-use) or the finer 1883 Bien printing (Rumsey
   [RUMSEY~8~1~2237~200008](https://www.davidrumsey.com/luna/servlet/detail/RUMSEY~8~1~2237~200008),
   10,426 × 8,352) — the survey-grid counterpoint to de Lacy: same silhouette
   fit, township lattice instead of hachures.
7. **Stevens Pacific Railroad Survey, Milk R.–Columbia R.** (1855, LOC
   [2022585173](https://www.loc.gov/item/2022585173/), 19,092 × 7,323) — the
   pre-territorial Flathead corridor; atmospheric, metrically loose.
8. **Simpson *Aerial Map of Glacier National Park and the Flathead Valley***
   (1954, painted shaded relief of exactly our footprint; Rumsey
   [RUMSEY~8~1~260532~5522882](https://www.davidrumsey.com/luna/servlet/detail/RUMSEY~8~1~260532~5522882),
   9,836 × 11,604, CC BY-NC-SA) — the mid-century bookend, and the closest
   cousin to the 1991 montana sheet's genre.

### Tier 3 — the flat-art wing (oblique views; never draped)

Bird's-eyes and pictorials can't be orthorectified honestly. Present them as
sheets on a table — a lit, tilted plane in the same viewer chassis, or a
gallery page — not as terrain skins:

- **Renshawe, *Panoramic View of the Glacier National Park*** (USGS, 1914) —
  the government's own painted panorama, public domain. Best copy: AGSL
  direct-download JP2, 9,605 × 8,659 px
  ([collections.lib.uwm.edu agdm:20](https://collections.lib.uwm.edu/digital/collection/agdm/id/20));
  also at Rumsey (9,863 × 9,061) and LOC.
- **Great Northern *aeroplane* views of Glacier** (1910s–1925, public domain
  by age): AGSL JP2 12,934 × 7,101
  ([agdm:16505](https://collections.lib.uwm.edu/digital/collection/agdm/id/16505)),
  the 1914 McGill-Warner printing as a 22.9 MB JP2 on Internet Archive
  ([direct file](https://archive.org/download/dr_aeroplane-view-of-glacier-national-park-see-america-first-great-norther-8707003/8707003.jp2)),
  the 1925 *Route of the Empire Builder* edition as a 22.5 MB JP2
  ([direct file](https://archive.org/download/dr_aeroplane-map-glacier-national-park-montana-and-waterton-lakes-park-alb-9001002/9001002.jp2)),
  and the huge Rumsey scan (19,458 × 10,994, CC BY-NC-SA).
- **Scheuerle's Great Northern recreational pictorial** (1925 at Rumsey
  [RUMSEY~8~1~260298~5522932](https://www.davidrumsey.com/luna/servlet/detail/RUMSEY~8~1~260298~5522932),
  14,652 × 8,522; 1930 edition on the Montana History Portal,
  [mtmemory 87755](https://www.mtmemory.org/nodes/view/87755), 300-ppi TIFF)
  and the **1939 GNR *Pictorial Map* / *Peace Park* sheets** —
  [mtmemory 87648](https://www.mtmemory.org/nodes/view/87648) (50 MB download)
  and a 33.8 MB JP2 on Internet Archive
  ([direct file](https://archive.org/download/dr_map-of-glacier-national-park-waterton-lakes-national-park-international-pea-8867003/8867003.jp2)).
  The 1939 sheets are planimetric pictorials, so a *loose* drape is possible if
  the cartoon distortion amuses rather than offends; 1939 GNR copyright is
  unevaluated by the archives — treat as gallery material, not core assets.
- **Wellge's 1904 Butte panorama** — "the largest mining camp on earth" (LOC
  [2015589008](https://www.loc.gov/item/2015589008/), 10,026 × 5,526) — the
  mineral wing's pin-up.
- **Sanborn fire-insurance sheets** (all public domain, LOC): Kalispell
  1892/1894/1899/1903/1910, Whitefish 1905–1932, Columbia Falls 1894–1932,
  Somers 1910, **Bigfork 1916 & 1927** (single sheets,
  [sanborn04936_001](https://www.loc.gov/item/sanborn04936_001/),
  [sanborn04936_002](https://www.loc.gov/item/sanborn04936_002/)) — block-level
  town portraits; best as story panels inside `flathead/`, not drapes.

### Additional finds — Montana collections, forests, and the NPS shelf

All on the Montana History Portal unless noted; every entry has a free full-res
JPEG at `https://www.mtmemory.org/assets/downloadwiz/{assetId}` (no IIIF; the
portal is Recollect, discovered best via `site:mtmemory.org` web searches).
Portal rights labels are "Copyright Not Evaluated"; the US-government items are
public domain regardless, and the pre-1930 commercial ones by age.

- **Jaqueth & Walters, *Map of Flathead County and the Flathead Indian
  Reservation*** (1908, ~1:252,000, 91 × 101 cm;
  [mtmemory 87673](https://www.mtmemory.org/nodes/view/87673), 5,889 × 6,538 px)
  — Kalispell, Bigfork, the whole lake, steamboat routes, coal and oil
  symbols, township grid, and the *proposed* Glacier NP boundary. The best
  single whole-region sheet found anywhere; earmarked as the `flathead/`
  alternate skin (above) and a candidate to promote to its own sheet.
- **Flathead National Forest** (USFS, c. 1912–1920, ~1:126,720, hachures;
  [mtmemory 87874](https://www.mtmemory.org/nodes/view/87874), 7,099 × 5,716)
  — fills the Swan/Mission country the Glacier topos miss. Sibling:
  **Blackfeet (now Kootenai) National Forest, 1929** —
  [mtmemory 87789](https://www.mtmemory.org/nodes/view/87789), 5,733 × 6,398 —
  the Whitefish Range/Libby corner, adjacent to the gold districts.
- **GLO *Sectionized map of the Flathead Indian Reservation*** (1904;
  [mtmemory 45365](https://www.mtmemory.org/nodes/view/45365), 6,842 × 7,728)
  — the section grid drawn to administer allotment and the 1910 opening of
  Salish, Kootenai and Pend d'Oreille lands. Cartographically it
  georeferences beautifully off the PLSS grid; historically it documents a
  dispossession, and any use must say so plainly (decision 6 below).
- **NPS Glacier brochure fold-out maps, 1916–1942** (public domain; NPS
  History eLibrary [index](http://npshistory.com/publications/glac/brochures/index.htm),
  direct PDFs verified e.g. [1938](https://npshistory.com/publications/glac/brochures/1938.pdf))
  — graticuled planimetric park maps, ~3,000 px wide; a year-by-year
  time-series of the park's trails/roads, good for story panels or a small
  multiples strip. Plus the **1948 Waterton-Glacier guide map** at AGSL
  ([agdm:27962](https://collections.lib.uwm.edu/digital/collection/agdm/id/27962),
  JP2 9,816 × 7,730, public domain).
- **Philipsburg mining exemplar** — *Topographic map of the Philipsburg
  quadrangle showing locations of mines* (USGS PP 78 plate, 1912;
  [mtmemory 45537](https://www.mtmemory.org/nodes/view/45537), 6,502 × 7,980)
  with the matching **Philipsburg geologic folio GF-196** sheets at
  [pubs.usgs.gov/gf/196](https://pubs.usgs.gov/gf/196/quad-topography.pdf) —
  outside the Flathead, but the archetypal "mines on real topography" sheet if
  the gold wing wants a precision counterpart to de Lacy.
- **Whitefish townsite plat, 1903** ([mtmemory 45272](https://www.mtmemory.org/nodes/view/45272),
  3,500 × 2,112) and de Lacy's **manuscript** (listed under `gold/`) round out
  the portal finds. A Bigfork bird's-eye exists on the portal but exposes no
  download asset (node 124824) — dead end for now.
- **MBMG reality check**: the classic placer-gold literature (Lyden Memoir 26,
  Hog Heaven Memoir 17, Johns Bulletin 79) is print-only — no scans exist to
  drape. What MBMG gives away free is modern and *useful as data*: the
  abandoned-mines inventories for the Flathead NF
  ([MBMG 462](https://mbmg.mtech.edu/pdf-open-files/MBMG462.pdf)) and Kootenai
  NF ([MBMG 395](https://mbmg.mtech.edu/pdf-open-files/MBMG395.pdf)) — district
  names, histories and locations to enrich the MRDS mines layer.
- **BLM GLO township plats** (Somers/Bigfork townships, T26–28N R19–21W):
  BLM replaced the records system in July 2026 with a JS-only portal
  ([glorecords.blm.gov/s/](https://glorecords.blm.gov/s/)); plats are still
  free but need a browser session to fetch — a small interactive errand, not
  a pipeline step. Park for a possible future `plats/` micro-sheet.

---

## 3 · Reference & enhancement datasets (all verified, all open)

| Dataset | Source | Use |
|---|---|---|
| Glacier margins: LIA max + 1966/98/05/15 | USGS ScienceBase ([58af7022](https://www.sciencebase.gov/catalog/item/58af7022e4b01ccd54f9f542), [5b194f1c](https://www.sciencebase.gov/catalog/item/5b194f1ce4b092d965237f5f)) | retreat overlay on `glacier/` |
| Mines & prospects (name, commodity, lat/lon) | USGS [MRDS](https://mrdata.usgs.gov/mrds/) | mines layer on `gold/` (and Libby later) |
| Terrarium terrain tiles | AWS open data (already in use) | z12/z13 for the local sheets |
| State boundary | US Census cb_2021 (already in use) | silhouette fits |
| Lake/river shorelines | NHD waterbody polygons (TNM) | optional shoreline-assisted fits, water masks |
| Historical topo index | TopoView ArcGIS layer: `energy.usgs.gov/arcgis/rest/services/topoview/ustOverlay/MapServer/0/query` + S3 template `prd-tnm.s3.amazonaws.com/StagedProducts/Maps/HistoricalTopo/GeoTIFF/MT/MT_{Name}_{scan_id}_{year}_{scale}_geo.tif` | scripted quad discovery/fetch (the documented `connect/apiv1` is dead) |
| Montana History Portal downloads | `mtmemory.org/assets/downloadwiz/{assetId}` (free, full-res JPEG; no IIIF) | scripted scan fetch for portal items |
| NW-MT mining districts (names, histories, locations) | MBMG [462](https://mbmg.mtech.edu/pdf-open-files/MBMG462.pdf) / [395](https://mbmg.mtech.edu/pdf-open-files/MBMG395.pdf) abandoned-mines inventories | enrich the MRDS mines layer |
| Carto-bibliography of Flathead-area federal maps | [Forest Service Museum, *Names, Boundaries, and Maps… Northern Region*](https://forestservicemuseum.org/wp-content/uploads/2019/11/Northern-Region-Nov19.pdf) | provenance notes for About panels |

---

## 4 · Georeferencing strategies (still no hand-picked control points)

Three automated strategies cover every Tier 1/2 sheet. All of them end the same
way montana does: fit reported as px residuals in the About panel.

**A. GeoTIFF passthrough + neatline crop** — for TopoView quads. The HTMC
GeoTIFFs carry the georeference; the work is (1) reading `ModelTiepoint` /
`ModelPixelScale` TIFF tags, (2) NAD27→WGS84 datum shift (~40–70 m here;
implement Molodensky in `lib/proj.py`, same hand-rolled spirit as the existing
LCC), (3) cropping the collar to the neatline, whose corners are exact
half-degree graticule points, then resampling to the sheet grid. Neatline
detection (the heavy black frame is trivially findable) doubles as an
independent check on the embedded transform — if they disagree beyond a couple
of scan pixels, warn and stop.

**B. Graticule/neatline corner fit** — for the GNP special sheet and any sheet
with a printed graticule but no embedded georeference. Detect the neatline
rectangle and graticule intersections by image processing; their true
coordinates are printed on the collar (entered once as four numbers in the
sheet config — data, not control-point picking). Fit the quad's native
polyconic (or LCC — at 30′ extent the difference is sub-pixel) through the
detected intersections; typically 9–25 automatic GCPs at engraved-line
precision.

**C. Silhouette ICP + graticule anchors** — for statewide sheets (de Lacy,
GLO). Reuse montana's boundary ICP verbatim, but (1) cap the polynomial at
degree 2 — an 1865 draughtsman's boundary should not be chased with a cubic —
and (2) add detected graticule intersections as strongly-weighted anchors, so
the fit is pinned by the map's own coordinate claims and the boundary only
refines it. Report residuals separately for the two evidence classes; for de
Lacy the *residual field itself* becomes a display layer ("where 1865 thought
the mountains were").

**Dependencies:** keep `requirements.txt` at numpy/scipy/pillow/pyshp if
Pillow's libtiff opens the HTMC tiles cleanly; else add `tifffile` (pure
Python) as a pipeline-only dependency. No GDAL, no rasterio — nothing the
one-file build could ever miss. LOC bulk fetches need a browser `User-Agent`
header on `urllib` (their CDN 403s the default one); tile.loc.gov's IIIF Image
API is the reliable machine route, and JP2 derivatives (~9 k px) are usually
enough — fall back to the TIFF master only if JPEG2000 ringing shows in the
engraving.

**QA bar:** each sheet's About panel states source scan, fit method, residuals
(median/RMS px and ground metres), and any honest caveats (the 1920/1943 seam;
Kerr Dam's shoreline; de Lacy's fictions). Acceptance: A/B fits ≤ ~2 px RMS on
the working scan; C reported, not gated.

---

## 5 · Pipeline & asset changes

Per-sheet `pipeline/build.py` shrinks to a config + strategy choice:

```python
SHEET = dict(
    id='glacier', title='Glacier in Contours',
    grid=dict(kind='lcc', sp=(48.3, 48.9), lon0=-113.85, margin=0.002),
    dem=dict(zoom=13, box=(-114.55, -113.15, 48.20, 49.05), clamp=(700, 3400)),
    scan=dict(src='loc', item='2016586564', prefer='jp2'),
    georef=dict(kind='graticule', corners=...),   # or 'geotiff', 'silhouette'
    tex_w=4096, hgt_w=2730,                        # artifact budget
    tex_w_dist=8192,                               # served build, no ceiling
)
```

- **Resolution budgets.** A 300-dpi 1:125,000 scan resolves ~10.6 m/px on the
  ground; `TEX_W` 4096 over the Glacier sheet is ~23 m/px. Keep 4096 for the
  committed assets and the ≤ 8 MB one-file artifact; add an optional hi-res
  encode (`tex_w_dist` 6144–8192, plus `hgt_w` up to 4096) for the served
  `dist/` build, which the README already notes has no ceiling. Committed
  assets stay ~7–8 MB per sheet (montana precedent), so four new sheets add
  roughly 30 MB to the repo — acceptable, same rationale as today.
- **Terrain.** z13 for `glacier/` (~600 tiles), z12 for `flathead/`; the
  12-bit height packing gives ≤ 0.6 m quantisation over these reliefs. Void
  thresholds become the per-sheet `clamp`.
- **Vectors in meta.** Glacier margins and MRDS mines enter `meta.json` as
  simplified `[u,v]` polylines/points in grid space (a few tens of KB),
  drawn by the existing line/label machinery — no new texture channels.
- **Seam handling** (`flathead/`): per-band histogram match of the 1943 sheet
  to the 1920 sheet over a 2 km strip at the join before the mosaic, plus a
  one-texel neutral hairline at 48° so the join is legible, honest, and quiet.

---

## 6 · Reproducing (and quietly enhancing) each sheet's cartography

Principles, in the order they bind:

1. **The scan is the artwork.** Colour-manage it once (neutral paper point,
   gentle de-yellowing; documented in About as "cleaned", never "restored"),
   then leave it alone. No sharpening, no recolouring of linework.
2. **The companion layer speaks the sheet's dialect.** Montana's crossfade
   samples the sheet's own hypsometric legend. The new sheets have no tint
   legends, so each companion render is built from the sheet's *ink palette*:
   engraved-brown contours + cream paper for `glacier/` (synthetic contours at
   the sheet's own 100-ft interval), sepia hachure-toned relief for `gold/`,
   engraved USGS brown/blue/black for `flathead/`. Sampled swatches go in
   `meta.json` exactly like the montana ramp.
3. **Typography by period.** Keep the Plex/Spectral system as the interface
   voice; sheet titling may take one period-appropriate display face per sheet
   (e.g. an engraved-roman for the USGS sheets, a Victorian face for 1865),
   loaded with the same graceful offline fallback.
4. **Modern best practice where the reader benefits**: label de-collision,
   occlusion culling, `prefers-reduced-motion`, keyboard access, perf shedding
   — all inherited; scale bar and cursor lat/lon/elevation stay; attribution
   and rights link stay one click away in every build.
5. **Enhancements must be data, not decoration**: glacier retreat vectors,
   MRDS mines, the de Lacy residual field, the 1920/1943 date seam — each one
   is a checkbox the reader can turn off, sourced in About.

---

## 7 · Gallery & deploy

- New top-level `assemble_all.py` (pure stdlib, like everything else): runs
  each sheet's `src/assemble.py`, collects `montana/dist → dist/montana/`,
  `glacier/dist → dist/glacier/`, …, and writes `dist/index.html` — a landing
  page in the same typographic voice: one card per sheet (still, title, year,
  one-line blurb, source credit), plus links to the one-file artifact builds.
- `vercel.json`: `buildCommand: python3 assemble_all.py`,
  `outputDirectory: dist`. **Note:** montana moves from `/` to `/montana/`;
  add a root redirect only if the gallery shouldn't own `/`. (Decision below.)
- README grows a gallery table mirroring the landing page; each sheet keeps a
  section in the montana format.

---

## 8 · Rights & attribution matrix

| Source | Terms (as stated) | Obligation |
|---|---|---|
| LOC Geography & Map Division | "free to use and reuse"; no advisories on our items | credit line "Library of Congress, Geography and Map Division" |
| LOC Sanborn collection | "in the public domain and … free to use and reuse" | credit |
| USGS (quads, plates, ScienceBase, MRDS) | US Government work — public domain | credit + dataset citations |
| Stanford copy of 1914 GNP sheet | marked public domain | credit |
| David Rumsey Collection | CC BY-NC-SA 3.0 (collection-wide) | credit "David Rumsey Map Collection, David Rumsey Map Center, Stanford Libraries"; non-commercial; share-alike on the derived drape — fine for this repo, but prefer LOC/USGS scans when both exist (we do, for every Tier 1 sheet) |
| Montana History Portal (mtmemory.org) | per-item "Copyright Not Evaluated" labels | rely on the underlying work's status: USGS/GLO/USFS items are US-gov public domain; 1865/1908 commercial items public domain by age; credit the holding institution (MHS or UM Mansfield Library) per item |
| AGSL / UWM (montana sheet; Renshawe, aeroplane, 1948 guide JP2s) | AGSL rights statement; the listed items are US-gov or pre-1930 works | credit AGSL, link their rights page (montana precedent) |
| Internet Archive Rumsey mirrors | scans carry Rumsey's CC BY-NC-SA credit request; underlying pre-1930 works public domain | credit Rumsey when using their scan, even of a PD work |
| GNR 1939 pictorials | copyright "not evaluated" by any holder | gallery/context use only unless cleared |

Tier 1 uses **only public-domain scans** (LOC + USGS + MT Memory/Stanford);
Rumsey's CC BY-NC-SA items enter at Tier 2/3 with their credit line.

---

## 9 · Roadmap

| Phase | Deliverable | Notes |
|---|---|---|
| 0 | this plan; user picks/confirms the Tier 1 lineup and decisions below | ✅ implemented with the recommended defaults, Aug 2026 |
| 1 | `lib/` extraction + `glacier/` end-to-end | ✅ done — georeferencing ended up **correlation against the sibling 30′ quads** (2.7 px RMS ≈ 30 m; the sheet has no internal graticule, so strategy B evolved); glacier margins (LIA + 2015) ride as overlays |
| 2 | `flathead/` (GeoTIFF passthrough, two-quad mosaic + seam, steamboat/Bigfork stories) | ✅ done — the "USGS quads" turned out to be Army **Progressive Military Map** sheets (planimetric, same series both dates), which made the pair stylistic siblings; strategy A validated (~1 scan px vs townsites) |
| 3 | `gold/` (graticule fit, sepia companion, MRDS mines, district labels) | ✅ done — de Lacy draws no internal graticule either; border-tick combs + automatic degree labelling via the red-boundary score (0.98); ~5 px RMS; the sheet's own Washington meridian measured at 77°05′; montana's grid/terrain reused verbatim |
| 4 | `assemble_all.py`, gallery landing, vercel.json, README | ✅ done — gallery at `/`, montana moved to `/montana/` |
| 5 (stretch) | `libby/` gold-district sheet; PP 296 three-way crossfade on `glacier/`; Jaqueth 1908 skin on `flathead/`; flat-art wing (Renshawe, GNR aeroplane views, Sanborn panels, NPS brochure time series); de Lacy states-of-the-map toggle; forest-reserve sheets | ✅ done, Aug 2026 — `libby/` built (B-956 over its 1932 base, MRDS mines); three-layer crossfade shipped on glacier (PP 296), flathead (Jaqueth 1908, 4 px via a two-anchor seed) and gold (the MHS manuscript); the flat wing (`art/`) carries Renshawe, the GNR aeroplane view, NPS guide/brochure maps, Ayres 1899, the USFS Flathead NF map, the 1904 reservation map with plain provenance, and two Sanborns. Deliberately left out: Rumsey-licensed pieces (1872 Colton, 1878 boundary strip, Scheuerle) to keep the wing public-domain, the NPS brochure *time series* (one fold-out shown), and Alden PP 231. |

| 6 (post-plan) | `yellowstone/` — the park and its surrounds, by user request | ✅ done, Aug 2026 — **Geologic Atlas Folio 30** (Hague, 1896): the four park quadrangles' areal-geology plates mosaicked as the drape, their **1911 engraved editions** (HTMC, self-georeferenced) as the middle layer, registered per-quad on a local high-pass **ink mask** (the shared linework is the brown contour plate, invisible to the black+blue mask) — 1.5–2.2 px RMS ≈ 16–23 m, the gallery's tightest; ~70 GNIS geysers/springs as the data layer (♨), 13 GNIS-verified summits, four flights incl. *The Great Caldera*. |

Each phase ends the montana way: pipeline reproducible from
`python3 pipeline/build.py`, residuals printed, one-file build opens from disk,
committed assets ≤ ~8 MB/sheet.

---

## 10 · Decisions wanted from you

1. **Tier 1 lineup** as proposed (`glacier/`, `flathead/`, `gold/`)? Any swap
   with Tier 2 (e.g. Libby sooner for more gold, Simpson 1954 for more
   relief-painting)?
2. **Root URL**: gallery at `/` with montana moving to `/montana/` (my
   recommendation), or montana stays at `/` and the gallery lives at
   `/sheets/`?
3. **Which Glacier edition**: the LOC 1915 administrative scan is the sharpest
   (9,788 px); the 1911 is the earliest state; 1922 adds the roads era. My
   default: fetch 1911 + 1915, keep whichever engraving reads better at
   4096 px, mention the other in About.
4. **Repo weight**: comfortable with ~30 MB of committed assets across four
   new sheets, montana-style, or switch new sheets to fetch-on-build?
5. **Rumsey CC BY-NC-SA** material (Tier 2/3 only): acceptable for the site,
   or keep the whole gallery strictly public-domain?
6. **The 1904 reservation allotment map**: include it as an optional overlay
   with plain-spoken provenance (my lean — it is the region's history and the
   portal publishes it), or leave allotment-era materials out of the gallery
   entirely?
