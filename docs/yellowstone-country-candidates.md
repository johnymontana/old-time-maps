# Candidate maps: the Yellowstone country north and east of the park

Research memo, August 2026 — follow-up to the Yellowstone in Folio sheet.
Scope requested: **Tom Miner Basin, Paradise Valley, and the Big Timber /
McLeod country** (the Boulder River and the Crazies), plus anything else
worth having near the park. Every "verified" item below was probed at the
URL given; corner coordinates were read from the actual files.

Geography, from GNIS: Tom Miner Basin 45.185,−110.954 · Yankee Jim Canyon
45.197,−110.901 · Gardiner 45.032,−110.706 · Emigrant 45.370,−110.734 ·
Emigrant Peak 45.263,−110.707 · Chico 45.321,−110.705 · Livingston
45.662,−110.561 · McLeod 45.663,−110.116 · Independence (ghost camp, upper
Boulder) 45.212,−110.246 · Big Timber 45.835,−109.956 · Crazy Peak
46.018,−110.277 · Mount Cowen 45.389,−110.486.

---

## Tier 1 — the hero: `paradise/` — Geologic Folio 1, the Livingston sheet

**One sheet covers nearly the whole request.** The first folio ever
published in the *Geologic Atlas of the United States* — **GF-1,
Livingston, Montana (1894; Iddings & Weed, geology; topography by Frank
Tweedy under Henry Gannett, surveyed 1883–86)** — is the degree sheet
**45°–46° N × 110°–111° W** (stated in the folio text and confirmed from
the GeoTIFF georeference): Gardiner and the park's north boundary along its
bottom edge, Yankee Jim Canyon, **Tom Miner Basin**, all of **Paradise
Valley** with the NPRR Park Branch (1883) drawn down it, Emigrant Peak and
Emigrant Gulch, Chico, Mount Cowen and the Absaroka plateaus, **McLeod and
the Boulder / West Boulder** with the Independence camp at the head, the
Shields, Livingston itself, and the southern **Crazy Mountains** (Crazy
Peak misses the neat by 2 km). The pre-1892 **Crow Reservation boundary**
crosses the east edge — to be stated plainly, as on the flathead sheet.

- Folio plates (verified): https://pubs.usgs.gov/gf/001/ —
  `quad-area.pdf` (areal geology), **`quad-economic.pdf`** (economic
  geology — the mining-district colours: Emigrant Gulch, the upper Boulder,
  the Cokedale and Electric/Horr coal and coke country), `quad-structure.pdf`,
  `quad-topography.pdf`, `text.pdf`, `illustration.pdf`.
- Base scans (verified, HTMC GeoTIFFs with embedded georeference,
  ~20 m/px): `MT_Livingston_268784_1891_250000_geo.tif` plus five 1893
  printings (268785–268789) on the prd-tnm S3 bucket.
- **Recipe = the yellowstone/ pipeline verbatim, one plate instead of
  four**: rasterise the folio's areal (or economic) plate, register to the
  1891 base by correlation **on the local high-pass ink mask** (same
  engraving lineage — expect the same 1.5–2.2 px class of fit), 1891 topo as
  the middle crossfade stop, MRDS mines (already cached repo-wide in
  `gold/work/mrds.json`) as the ⚒ data layer.
- Terrain: z12 Terrarium, block ≈ 78 × 111 km at 45.5°, ~2,000 texels/°;
  relief ~1,300 m (Yellowstone at the north edge) to 3,455 m (Mount Cowen
  region — verify summits against GNIS + DEM as before).
- Flights that write themselves: *Tom Miner and the petrified forest* ·
  *Yankee Jim's toll road and the Park Branch* (Cinnabar, Devil's Slide,
  Electric's coke ovens) · *Emigrant Gulch* (Curry's 1864 diggings, Chico) ·
  *Up the Boulder* (McLeod, Natural Bridge, Independence at the head) ·
  *The Crazies* (island range, Crow fasting site — say so plainly).
- Open choices: primary = areal vs economic plate (areal recommended,
  economic noted in About or swapped in as a variant); which 1893 printing
  scans cleanest.

## Tier 2 — supporting sheets

- **`bigtimber/` — Big Timber 30′ quadrangle, 1891/1893** (verified:
  neat 45°30′–46° × 109°30′–110°, scans
  `MT_Big Timber_268485_1891` + four 1893 printings, 125k). Big Timber
  itself, the Boulder's mouth, Sweet Grass plains, SE Crazies foothills. No
  folio for it — topo-only sheet, so a thinner story than paradise/; worth
  building only if the corridor deserves two sheets. (McLeod is on the
  *Livingston* sheet, not this one. The 1:125,000 "Boulder 1899" in HTMC is
  the Jefferson County Boulder near Butte — not this river.)
- **`absaroka/` — GF-52, Absaroka folio (1899)**: Crandall + Ishawooa
  quadrangles, the park's **east** wall — upper Clarks Fork, Sunlight
  Basin, the approaches to Cooke City. Verified: plates at
  https://pubs.usgs.gov/gf/052/ (`quad-1_historical.pdf` etc.), bases
  `WY_Crandall_342425_1899_125000_geo.tif` (corners confirmed
  44°30′–45° × 109°30′–110°) and `WY_Ishawooa_342479/…` on S3. Same
  folio-over-own-base recipe; extends the park block eastward as its own
  sheet.
- **GF-24, Three Forks folio (1896, Peale)** — the adjoining degree sheet
  west of Livingston (Bozeman, Gallatin Valley, Bridgers). Verified at
  https://pubs.usgs.gov/gf/024/ (same four-plate layout). "Around
  Yellowstone" in the broad sense; third priority.
- **Gardiner + Emigrant 15′ quads, 1955** (verified in HTMC at 1:62,500) —
  a mid-century fine-scale pair for the upper corridor, mirroring the
  flathead sheet's two-quad mosaic. Newer-era styling; only if a 1950s
  sheet is wanted.

## Tier 3 — the Flat Wing (all Library of Congress, verified items)

- **Bird's eye view of Livingston, Mont., 1883** — the year the NPRR
  arrived and the town was born. Panoramic Maps collection,
  https://www.loc.gov/item/75694671/.
- **Raynolds, *Map of the Yellowstone and Missouri rivers…*, 1859–60** —
  https://www.loc.gov/item/96682479/ — the pre-park reconnaissance (Jim
  Bridger guiding); the upper Yellowstone left nearly blank. The "before"
  of every sheet in the gallery.
- **Hayden, *Preliminary geological map of the Yellowstone National Park*,
  1878** — https://www.loc.gov/item/97683605/ — the survey geology Hague's
  folio replaced; a perfect foil for the yellowstone/ sheet.
- **Hayden party, *Upper Geyser Basin, Fire Hole River*, 1871** —
  https://www.loc.gov/item/97683584/ — the first map of the Old Faithful
  basin, drawn the summer before the park act.
- **Yellowstone National Park, 1871** — https://www.loc.gov/item/97683567/
  (search-verified; item fetch was rate-limited).
- **Sanborn runs** (pre-1930 printings are public domain): Livingston —
  eight editions 1884→1929 (`sanborn05041_001…008`); Big Timber — six
  editions 1891→1938 (`sanborn04938_001…006`). The 1884 Livingston, one
  year into the town's existence, is the pick.

## Leads not yet verified (check before promising)

- **NPRR / "Wonderland" promotional maps** of the Park Branch
  (Livingston→Cinnabar→Gardiner): nothing found in LOC's railroad-maps
  collection under obvious queries; try LOC general search, the Montana
  History Portal, and NPRR annual reports. Likely exists; source unknown.
- **Forest-reserve atlas sheets** around the park: AR 19-5 plates were
  spot-checked and are *not* obviously the Yellowstone reserve (plate 74 is
  Washington State); the Absaroka reserve (1902) postdates the atlas era.
  Needs plate-by-plate identification in AR 19/20/21 before counting on it.
- **Mining-district literature** for Emigrant Gulch and Independence:
  USGS Pubs Warehouse has nothing obvious; the likely sources are MBMG
  (state, not federal-PD — check terms) and the folio's own economic plate,
  which may honestly be the best period mining map of the corridor anyway.

## Built (August 2026)

`paradise/` shipped as **The Livingston Sheet** (GF-1 areal plate over the
1891 base, 1.9 px RMS ≈ 40 m, 44 MRDS mines, five flights), and the Flat
Wing gained the Raynolds 1859–60, the 1871 Upper Geyser Basin, the 1878
Hayden geology and the 1883 Livingston bird's-eye. Still on the shelf:
`bigtimber/`, `absaroka/` (GF-52), GF-24 Three Forks, the 1955 15′ pair,
the Sanborn runs, and the unverified NPRR / forest-reserve leads.

## Recommendation

Build **`paradise/` from GF-1** — it answers Tom Miner, Paradise Valley,
and McLeod in a single folio-over-its-own-base sheet with the proven
pipeline, and it is *Folio No. 1*, which the gallery's story practically
demands. Add the **Livingston 1883 bird's-eye + Raynolds 1860 + Hayden
1878/1871** to the Flat Wing in the same stroke. Hold `bigtimber/` and
`absaroka/` as the next ring outward.
