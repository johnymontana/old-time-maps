# Candidate maps: the sixty-three national parks

Research memo, August 2026 — the all-parks survey. Scope requested: every
US National Park, scouted in eight regional batches for old-time
cartography that can carry a sheet in this gallery. Two parks are already
built — **Yellowstone** (`yellowstone/`, the Hague folio plates over their
own 1885 quads) and **Glacier** (`glacier/`) — so 61 parks are graded
below, plus cross-cutting findings on three map series.

**Verification standard.** Nothing in this memo is promised beyond its
flag:

- *probed* — HTMC GeoTIFF opened (full download or a 2 MB header range
  fetch) and corner-checked with `lib/georef.QuadGeoref`; neatline
  coordinates quoted here were read from the files themselves.
- *rendered* — plate PDF downloaded and its title strip rasterised and
  read (the annual-report plate-numbering trap makes this mandatory).
- *listed* — present in the prd-tnm S3 inventory; not yet opened.
- *search-verified* — LOC metadata only. **LOC was Cloudflare/429-blocked
  through nearly the entire survey**; every LOC item below needs a
  file-level check from a cool IP before it is promised anywhere.

Grades: **hero** = verified drapeable primary plus a registration path in
repo terms; **wing** = Flat Wing art only; **thin** = checked honestly,
nothing suitable in era. The field came back **42 hero, 9 wing, 10 thin**.
HTMC filenames below live under
`https://prd-tnm.s3.amazonaws.com/StagedProducts/Maps/HistoricalTopo/GeoTIFF/{ST}/`
(URL-encode the spaces).

---

## The first ring — ten sheets, ranked by build-readiness

Ranked by how little stands between the scout report and a committed
sheet: verified primary, verified base, a recipe the repo has already
shipped, and a story that writes its own flights.

### 1. `estes/` — Rocky Mountain (CO): the one true park special

The only classic USGS park special that exists complete and georeferenced
in HTMC: **Topographic map of Rocky Mountain National Park, 1:125,000,
1915** — downloaded, corner-probed (neat 40°–40°30′ × 105°30′–106°,
content running to 40.59°), title strip read; six 1919-edition scans
(234288–234292, 467174–467175) for variants.

- Primary = base in one file:
  https://prd-tnm.s3.amazonaws.com/StagedProducts/Maps/HistoricalTopo/GeoTIFF/CO/CO_Rocky%20Mountain%20National%20Park_234287_1915_125000_geo.tif
- Alt: `CO_Longs Peak_402456_1915_125000_geo.tif` (probed — the *same*
  0.5° neat) as a same-year crossfade.
- Recipe: montana/front quad-only — the embedded georef does everything;
  no fitting at all.
- Flights: Longs Peak · Estes resort era · Fall River Road 1920 · the
  Arapaho and Ute homeland of the Front Range parklands (say so plainly).
  Wings: Hayden's 1877 Colorado atlas
  (https://archive.org/details/geologicalgeogra00hayd, full JP2 zip) and
  1915–26 circulars at https://npshistory.com/publications/romo/index.htm.

### 2. `blackhills/` — Wind Cave (SD): a folio printed on quads we hold

**GF-219, Central Black Hills (Darton & Paige, 1925)** — areal plate
rendered and read, bounds 43°30′–44°30′ × 103°–104° from `text.pdf` —
printed on the very Hermosa/Harney Peak sheets HTMC stages.

- Primary: https://pubs.usgs.gov/gf/219/quad-1_area.pdf (companions
  `quad-1_topography.pdf` 12.2 MB, `quad-3/4/5_artesian.pdf`; beware
  `quad-2_area.pdf` — a separate Lead-quadrangle sheet).
- Base: `SD_Hermosa_344793_1901_125000_geo.tif` (probed clean; Wind Cave
  at px 496,4963) + Harney Peak 1901 (scan 344786, HEAD-verified) for the
  park's western sliver; 1894 Hermosa (344790) as alt vintage.
- Recipe: yellowstone pattern verbatim — high-pass ink mask, ≤ 6 px RMS
  gate; block spans the Hermosa/Harney Peak seam (~103.2–103.8° ×
  43.4–44.0°).
- Flights: the first cave park (1903) · Darton's artesian waters · He
  Sapa: 1868 Fort Laramie Treaty, 1874 Custer expedition, 1877 seizure of
  the Hills — Lakota sacred land, stated plainly. Wing: 1920–28 brochures
  (https://npshistory.com/publications/wica/brochures/index.htm); the
  Ludlow 1874 and Newton 1879 maps are .sid-trapped at IA — retry LOC.

### 3. `brightangel/` — Grand Canyon (AZ): Matthes' plane-table specials

**Bright Angel 1:48,000 (Matthes, surveyed 1902–03)** — downloaded,
probed 36°–36°15′ × 112°–112°15′, title strip read ("BRIGHT ANGEL, ARIZ.",
Matthes credit, "(Grand Canyon National Park)" edge labels) — joined E–W
with **Vishnu 1907** (probed adjacent).

- Primary pair:
  https://prd-tnm.s3.amazonaws.com/StagedProducts/Maps/HistoricalTopo/GeoTIFF/AZ/AZ_Bright%20Angel_314251_1903_48000_geo.tif
  +
  https://prd-tnm.s3.amazonaws.com/StagedProducts/Maps/HistoricalTopo/GeoTIFF/AZ/AZ_Vishnu_314292_1907_48000_geo.tif
- Base: the same files; recipe = bitterroot/missouri two-quad E–W join,
  same series, ≤ 6 px gate. Alt: `AZ_Kaibab_315511_1886_250000_geo.tif`
  (probed — Powell-survey lineage, village inside).
- Wing: Dutton/Holmes 1882 atlas via the full book scan
  https://archive.org/download/atlasaccompanym00dutt/atlasaccompanym00dutt_jp2.zip
  (Point Sublime panoramas, pages 0065/0069/0073, ~7846 px verified; the
  single-sheet Rumsey `dr_` items are .sid-trapped) and the Pl. IV canyon
  platform map, full 9.1 MB JP2:
  https://archive.org/download/dr_pl-iv-map-of-the-grand-canyon-platform-and-the-surrounding-mesozoic-forma-2147019/2147019.jp2
- Flights: Granite Gorge and the temples · Powell lineage (Kaibab 1886) ·
  Havasupai and Hualapai homelands; Hopi and Diné presence — the Indian
  Garden/Havasupai eviction history belongs in a caption. (The 1923
  `AZ_Grand Canyon No 1` advance sheet was fetched: mostly blank — skip.)

### 4. `smoky/` — Great Smoky Mountains (TN/NC): Keith's 1895 folio

**GF-16, Knoxville (Arthur Keith, 1895)** — areal and topography plates
rendered and read; bounds 35°30′–36° × 83°30′–84° from `text.pdf` — over
the 1895 Knoxville sheet it was printed on.

- Primary: https://pubs.usgs.gov/gf/016/quad-area.pdf (+
  `quad-topography.pdf`, 5.6 MB, verified).
- Base: `TN_Knoxville_153455_1895_125000_geo.tif` (probed clean; sibling
  editions 1886/1892/1894/1901 in inventory for an alt).
- Recipe: yellowstone/libby — folio over its own quad, high-pass mask,
  ≤ 6 px RMS.
- Honest limit, for the About: the sheet holds only the park's **western
  half** — Cades Cove and Thunderhead; Clingmans Dome at 83°29.9′W misses
  the neat by a hair. Flights: Cades Cove · the crest · Cherokee homeland,
  with the Qualla Boundary adjoining the quad's NC corner. Wing lead: the
  1928 *Proposed Great Smoky Mountains National Park* map,
  https://www.loc.gov/item/99446123/ (search-verified only — confirm
  free-to-use).

### 5. `mazama/` — Crater Lake (OR): Diller's map of the collapse

**PP 3 Plate I, "Mt. Mazama and Crater Lake National Park" (Kerr
topography surveyed 1886; published 1902)** — rendered at PDF page index
17 of the report (title, scale, corner values read); Diller's colored
geologic map at page index 37 (caption verified) as the crossfade alt.

- Primary: https://pubs.usgs.gov/pp/0003/report.pdf (72.9 MB; render the
  plates out).
- Base: none exists — HTMC's oldest Crater Lake sheets are 1985 24k /
  1989 100k. Recipe = **nome printed-graticule fit**: the plate carries a
  labeled 5′ graticule, 122°00′–122°16′ × 42°48′–43°04′; deg-1 fit, state
  the era-datum caveat; QA against
  `OR_Crater%20Lake%20West_279504_1985_24000_geo.tif`.
- Data layer: the 1886 Cleetwood sounding party's depths are printed in
  the lake — a ready-made data layer, like gold/'s mines.
- Flights: Mazama's collapse told the year the park was born · the
  sounding party · giiwas, sacred to the Klamath and Modoc; 1864 Klamath
  treaty. Wing: PP 3's four-view *Panorama of Crater Lake* (PDF page 29).

### 6. `mountdesert/` — Acadia (ME): the island before the park

**Bar Harbor + Mount Desert 15′ quads, 1904** — both fully downloaded and
corner-probed clean; joined block 44°15′–44°30′ × 68°–68°30′, twelve years
before Sieur de Monts.

- Primary pair (= base, self-draping):
  https://prd-tnm.s3.amazonaws.com/StagedProducts/Maps/HistoricalTopo/GeoTIFF/ME/ME_Bar%20Harbor_460147_1904_62500_geo.tif
  +
  https://prd-tnm.s3.amazonaws.com/StagedProducts/Maps/HistoricalTopo/GeoTIFF/ME/ME_Mount%20Desert_460634_1904_62500_geo.tif
- Recipe: bitterroot/missouri two-quad E–W join; 1942 editions of the same
  cells (S3-listed, e.g. scans 460149/460635) as the park-era alt.
- Risk: the island's far south tips (Bass Harbor Head, 44.216°N) fall just
  below the 44°15′ neat.
- Flights: Bar Harbor and the cottage era · Green (Cadillac) Mountain ·
  Somes Sound · Wabanaki homeland — Pemetic of the Penobscot and
  Passamaquoddy, stated plainly. Wing: the 1921 Lafayette NP booklet,
  http://npshistory.com/publications/acad/brochures/1921.pdf (verified;
  1916 Sieur de Monts item also listed); three Rumsey island maps
  (1885/1890/1894) are .sid-trapped — wing-res only.

### 7. `chisos/` — Big Bend (TX): the 1903 river-country pair

**Chisos Mountains (a non-standard 45′ × 30′ sheet) + Terlingua, both
1903, 1:125,000** — both downloaded and corner-probed; joined at 103°30′
the pair covers Chisos Basin, Boquillas and Santa Elena canyons — nearly
the whole 1944 park, forty years early.

- Primary pair (= base):
  https://prd-tnm.s3.amazonaws.com/StagedProducts/Maps/HistoricalTopo/GeoTIFF/TX/TX_Chisos%20Mountains_108199_1903_125000_geo.tif
  +
  https://prd-tnm.s3.amazonaws.com/StagedProducts/Maps/HistoricalTopo/GeoTIFF/TX/TX_Terlingua_121887_1903_125000_geo.tif
  (1904/1905 sibling scans for variants).
- Recipe: front/missouri E–W join; watch the Chisos sheet's 0.75° width
  when sizing textures.
- Flights: Santa Elena · Boquillas · the Comanche Trail crossings ·
  Terlingua quicksilver · Hill's 1899 canyon traverse. Wing: Emory's 1857
  boundary-survey report, verified at IA
  (https://archive.org/details/reportonunitedst11unit); the exact Hill
  1899 map scan still needs pinning.

### 8. `kilauea/` — Hawaiʻi Volcanoes (HI): the observatory decade

**Kilauea 15′, 1921** — corner-probed (caldera and Kaʻū Desert rim
inside) — in a 2×2 with Mauna Loa 1928, Pahala 1923, Kalapana 1924
(all S3-verified), summit to sea.

- Primary:
  https://prd-tnm.s3.amazonaws.com/StagedProducts/Maps/HistoricalTopo/GeoTIFF/HI/HI_Kilauea_349872_1921_62500_geo.tif
  with
  https://prd-tnm.s3.amazonaws.com/StagedProducts/Maps/HistoricalTopo/GeoTIFF/HI/HI_Mauna%20Loa_349891_1928_62500_geo.tif
  and mates `HI_Pahala_349895_1923_62500`, `HI_Kalapana_349862_1924_62500`.
- Recipe: front 2×2, self-georeferenced. Alt: the **same-quad 1921 vs 1924
  Kilauea editions** (scans 349874/467968) straddle the May 1924
  Halemaʻumaʻu explosions — a built-in crossfade story.
- Flights: Jaggar's HVO, founded 1912 · Halemaʻumaʻu's lava lake and the
  1924 explosions · Mauna Loa's 1926 flow against the 1928 sheet · Pele;
  Kaʻū and Puna districts, Native Hawaiian land. About must carry the old
  Hawaiian-datum note even though HTMC re-tags NAD27.

### 9. `luray/` — Shenandoah (VA): the Blue Ridge, 1893

**Luray 30′ quad, 1893** — fully downloaded, corner-probed (39°–38°30′ ×
78°–78°30′); Front Royal, Thornton Gap, Skyland/Stony Man, Old Rag,
Hawksbill and Big Meadows all on one self-georeferenced sheet, 42 years
pre-park.

- Primary (= base):
  https://prd-tnm.s3.amazonaws.com/StagedProducts/Maps/HistoricalTopo/GeoTIFF/VA/VA_Luray_189048_1893_125000_geo.tif
  ; alt = the 1905 edition of the same sheet (scan 189049).
- Recipe: montana quad-only, single sheet. The South District would need
  `VA_Harrisonburg_188999_1892_125000_geo.tif` (range-verified only), but
  the two 30′ cells touch **only at a corner** — the honest block is
  Luray alone. Park-era 15′ layers if wanted: `VA_Elkton_188077_1937`,
  `VA_Waynesboro_188711_1934`.
- Flights: Stony Man and Pollock's Skyland · Old Rag · the ~500 mountain
  families displaced by condemnation, 1934–38 · Manahoac and Monacan
  homeland along the ridge. Wing: the 1934 leaflet,
  http://npshistory.com/publications/shen/brochures/1934.pdf (verified).
  The tempting 1935 Skyline Drive map at IA
  (dr_map-of-the-stony-man-region…-11795000) **fails PD-by-age — excluded**.

### 10. `yosemite/` — Yosemite (CA): the 30′ ladder and Hetch Hetchy

No park special exists in HTMC (TNM-confirmed; earliest is the 1897
125k), so build front-style on the 30′ quads: **2×2 of Dardanelles 1898 +
Bridgeport 1911 over Yosemite 1909 + Mt Lyell 1901**, with the
**1897-vs-1909 Yosemite editions** as the alt crossfade — undammed Hetch
Hetchy, pre/post the 1905–06 boundary shrink.

- Primary (probed; corners invert to 37°30′–38° × 119°30′–120°):
  https://prd-tnm.s3.amazonaws.com/StagedProducts/Maps/HistoricalTopo/GeoTIFF/CA/CA_Yosemite_299699_1909_125000_geo.tif
  ; editions 1897/1900/1903 in S3 (1903 scan 299698 also probed).
- Companions (S3-listed): `CA_Mt Lyell_299480_1901`,
  `CA_Dardanelles_299315_1898`, `CA_Bridgeport_299235_1911`.
- Recipe: front 2×2, self-georeferenced; later upgrade: Matthes' PP 160
  valley plates registered libby-style over the drape
  (https://pubs.usgs.gov/pp/0160/plate-2.pdf, 22.5 MB, plus plate-29 and
  plate-7).
- Flights: Hetch Hetchy before the 1923 dam · the Valley · Tuolumne ·
  Ahwahneechee / Southern Sierra Miwok homeland and the 1851 Mariposa
  Battalion, stated plainly. Wing: the 1874 Whitney pocket-guide valley
  map (https://archive.org/details/dr_map-of-the-yosemite-valley-prepared-to-accompany-the-pocket-edition-of-the-5902005);
  the 1868 Gardiner/King item
  (dr_…-commissio-5949035) is a **.sid trap** — 493 KB jpg only.

---

## Series findings (cross-cutting)

### The USGS park specials are mostly a myth in HTMC

~35 park-named prefixes probed across 24 states via the S3 list API: only
**two** parks have sheets literally titled "… National Park" — Rocky
Mountain (the real 1915/1919 special, hero above) and Yellowstone (modern
1982–83 metric 100k only, e.g.
`WY_Yellowstone%20National%20Park%20North_342385_1983_100000_geo.tif` —
skippable). The famous Yellowstone, Glacier, Mount Rainier, Crater Lake,
Yosemite Valley (1907), Zion, Bryce, Mesa Verde and Great Smoky specials
are **absent** from the HTMC GeoTIFF staging under every prefix tried.
What does exist, by HTMC evidence: Rocky Mountain's complete special;
Grand Canyon's numbered NPS-cooperative 48k series (only
`AZ_Grand%20Canyon%20No%201_314273_1923_48000_geo.tif` staged — title
strip read "NATIONAL PARK SERVICE, Stephen T. Mather, Director / Advance
sheet", but the scan is mostly blank — while the Matthes Bright
Angel/Vishnu specials are the real prize); and Hawaii's Kilauea 1921/24.
The illustrative trap:
`WA_Mt%20Rainier_242668_1924_96000_geo.tif` corner-probes to a park-shaped
footprint (47.031/−122.089 to 46.420/−121.414) yet its title strip reads
MT. RAINIER QUADRANGLE — an advance sheet, not the park special. **Hunt
park heroes by quad name, not park name.**

### NPS brochure folded maps (npshistory.com) — a Flat Wing seam

Pattern verified end-to-end:
`http://npshistory.com/publications/{parkcode}/brochures/{year}.pdf`,
discovered from `/brochures/brochures-{a-f,g-m,n-s,t-z}.htm`; fetches need
a browser User-Agent **plus an npshistory.com Referer**. Four PDFs
downloaded and opened with pypdfium2: mora 1915 (38 pp with an 11.5×9.2 in
map spread, 14.9 MB), yell 1920 (114 pp, 40.4 MB), acad 1921, shen 1934.
Runs are deep — acad from 1916, yell from 1912, mora from 1912/1915, glac
from 1916 (National Parks Portfolio). NPS-authored, so public domain.
Quality is ~150–200 dpi book pages: excellent Flat Wing and About-panel
material, **not** drape-grade cartography.

### Folio coverage over parks

The gallery's folio-over-its-own-quad pattern generalises: five folios
were verified plate-by-plate this survey — **GF-15 Lassen Peak 1895**
(https://pubs.usgs.gov/gf/015/quad-area.pdf), **GF-16 Knoxville 1895**
(gf/016/), **GF-77 Raleigh 1902** (gf/077/ — the "gf 72?" lead is
disproven: GF-72's text reads *Charleston*), **GF-215 Hot Springs 1923**
(gf/215/ — an off-grid 15′ district, so nome-fit), and **GF-219 Central
Black Hills 1925** (gf/219/). All follow the `pubs.usgs.gov/gf/{NNN}/`
layout with `text.pdf` p. 1 stating the bounds.

### Traps confirmed this survey

- **LOC 429.** Cloudflare rate-limiting blocked nearly every LOC query in
  every batch. Search-verified-only items riding on this: Mesa Verde 1915
  (loc.gov/item/2012586900/), Mammoth Cave 1930 (2012588163), proposed
  Smoky 1928 (99446123), Teton/Yellowstone boundaries 1929 (97683583),
  Hot Springs 1890 (2001622065). The survey's one 200: the Dune Park
  photo series (2018649091). **Re-scout LOC from a cool IP before any
  build that leans on it.**
- **The .sid trap.** IA Rumsey `dr_` items repeatedly carry only an
  unreadable MrSID beside a ~250–700 KB JPG (Wheeler sheets, Wilkes
  charts, Dutton singles, Ludlow 1874, the 1838 Florida *Seat of War*,
  Compton & Dry). Workaround where it exists: full book-scan `_jp2.zip`
  items (Dutton atlas, Hayden Colorado atlas, Griggs 1922).
- **Annual-report plate numbering.** File numbers never match plate
  numerals: ar/18-2 `plate-19/20` are Davis' Connecticut Triassic, not
  Russell's Rainier glaciers; ar/20-5 `plate-48` is the Colorado White
  River Plateau; ar/21-5's directory *skips* files 091–114 (Plummer's
  Rainier reserve plates simply absent); ar/21-2 `plate-43` is Brooks'
  Pyramid Harbor–Eagle route; ar/20-7 stages 25 `plate-map_*` files with
  the same trap. Rasterise the title strip, always.
- **Plates inside report.pdf.** Some primaries live only inside big
  reports (Reid's Glacier Bay at 16-1 p. 523 — works; Ball's Bulletin 308
  — 24.8 MB, no split plates), and PP 20's big folded route maps are
  **not in the scan at all** (verified page by page).
- **Alaska HTMC is Transverse Mercator** — QuadGeoref rejects it; every
  Alaska hero rides the nome printed-graticule path instead, and the
  1946–56 AK 250k sheets serve only as TM-caveat alts.

### Additions for the two sheets already built

Yellowstone: the yell brochure run reaches back to 1912
(http://npshistory.com/publications/yell/brochures/1912.pdf listed; the
1920 booklet verified at 40.4 MB / 114 pp) — About/Flat Wing material.
Glacier: glac brochures from 1916 onward (index verified, PDFs not
downloaded); confirmed **no** `MT_Glacier National Park` special exists in
HTMC under any probed prefix — nothing new for the drape.

---

## The rest of the field, region by region

Every park not in the first ring, thin ones included — absence honestly
recorded. HTMC candidates are given as exact filenames under the S3
prefix stated in the intro.

### Sierra & California

| Park | Tier | Best verified candidate | Note |
|---|---|---|---|
| Sequoia | hero | `CA_Kaweah_299400_1904_125000_geo.tif` + `CA_Mt Whitney_299505_1907_125000_geo.tif` (probed) | front 2×2 with Tehipite 1905 + Olancha 1907 (scan 299527, listed); Giant Forest sits 4 km north of the Kaweah/Tehipite seam — keep the join clean; natural combined SEKI block; Buffalo Soldier roads 1903, Western Mono homeland. |
| Kings Canyon | hero | `CA_Tehipite_302085_1905_125000_geo.tif` (probed) | General Grant Grove and Cedar Grove on one 1905 sheet; `CA_Mt Goddard_299469_1912_125000_geo.tif` (probed) joins bitterroot-style for the Palisades; ships with Sequoia or alone. |
| Lassen Volcanic | hero | GF-15 plates https://pubs.usgs.gov/gf/015/quad-area.pdf (HEAD-verified) over `CA_Lassen Peak_299801_1894_250000_geo.tif` (probed) | libby one-plate-over-one-base, same-lineage ink; the map predates the 1914–15 eruptions and the 1916 park — that is the story; crop ≈ 40.3–40.7° × 121.2–121.8°; Atsugewi / Yana-Yahi homeland. |
| Pinnacles | hero | `CA_Metz_298176_1921_62500_geo.tif` + `CA_San Benito_298856_1919_62500_geo.tif` (probed) | bitterroot N–S join at 36°30′, seam safely north of the High Peaks; 15′ detail over the 1908 monument; Chalon / Mutsun Ohlone homeland; modest story. |
| Redwood | hero | `CA_Crescent City_299307_1929_125000_geo.tif` (probed) | single-sheet libby-simple; the 1929 sheet covers only the park's north half (Jed Smith, Del Norte Coast, Klamath mouth — Yurok homeland); south coverage starts at `CA_Orick_298418_1945_62500_geo.tif` — scope the block or say so. |
| Channel Islands | hero | `CA_Santa Cruz Island B_300256_1943_24000_geo.tif` (probed; A–D tile + Santa Rosa / San Miguel 1943 sets listed) | 1943 war-survey quads — the youngest "old-time" claim in the survey; Chumash Limuw villages; 1854 Anacapa engraving wing-only: https://archive.org/download/mma_us_coast_surveysketch_of_anapaca_island_in_santa_barbara_channel_372964/372964.jpg (1.1 MB). |
| Joshua Tree | thin | — nothing pre-1930 (HTMC prefixes + TNM bbox checked; earliest are war-era 15′: Edom 1941, Pinkham Well 1943, Pinyon Well 1944, Amboy 1942 250k) | the war quads postdate the 1936 monument and carry no early story; LOC blocked, npshistory links unresolved. |
| Death Valley | hero | `CA_Furnace Creek_299777_1910_250000_geo.tif` + `CA_Ballarat_299736_1913_250000_geo.tif` (probed; 1908 editions 299776/299735 as alts) | missouri E–W join at 117°: borax roads, Skidoo, the Panamint camps on Timbisha Shoshone homeland; the park's northern third (Ubehebe, Scotty's) is off-sheet — state it; Ball 1907 recon is a report-embedded-plate chore (https://pubs.usgs.gov/bul/0308/report.pdf). |

### Pacific Northwest & Pacific

| Park | Tier | Best verified candidate | Note |
|---|---|---|---|
| Mount Rainier | hero | `WA_Mt Rainier_242668_1924_96000_geo.tif` (probed) | park-shaped footprint but titled MT. RAINIER QUADRANGLE (see series section); drapes on its own georef, libby pattern; alt `WA_Mt Rainier_242669_1928_125000_geo.tif`; Matthes' 1915 62.5k special is NOT in HTMC; Russell 1898 plates unlocated inside a 282 MB report. |
| Olympic | hero | Dodwell & Rixon 1900 reserve plates, https://pubs.usgs.gov/ar/21-5/plate-051.pdf (title-verified; run 051/053/056/059/061/063) over `WA_Mount Olympus_242513_1935_62500_geo.tif` (probed) + 1940s 15′ lattice (listed) | rails-style correlation of drainage/coast on the high-pass mask; reconnaissance grade — expect an Ayres-1899-class plateau, bend, and print the number; S'Klallam, Quinault, Quileute, Hoh, Skokomish and Makah homelands. |
| North Cascades | hero | `WA_Mt Baker_242611_1909_192000_geo.tif` (probed; 1915 "Dist" ed. 242737 probed) + `WA_Stehekin_244020_1902_125000_geo.tif` (listed) | bitterroot/front join of 1899–1915 reconnaissance sheets (Glacier Peak 1899, Chelan 1901 listed); check a possible Ross Lake NE gap (Methow unprobed); Upper Skagit, Nlaka'pamux, Chelan, Sauk-Suiattle, Methow homelands. |
| Great Basin | wing | Wheeler Atlas Sheet 49, https://archive.org/download/dr_parts-of-eastern-nevada-and-western-utah-atlas-sheet-no-49-the-graphic-c-00034034/00034034.jpg (.sid trap, ~1536 px) | no early base exists (oldest is Wheeler Peak 1948/50); Western Shoshone and Goshute homeland; flat art at small size unless a full-res PD scan surfaces. |
| Haleakalā | wing | 1906 Hawaii Territory Survey Maui, https://archive.org/download/dr_maui-hawaiian-islands-primary-triangulation-by-wd-alexander-and-se-bi-3705006/3705006.jpg (.sid trap, 1536×1288) | HTMC has no early Maui sheet at all (full HI inventory grepped: 1954+); wing at small size or nothing. |
| American Samoa | wing | Wilkes 1839 charts — Pago Pago https://archive.org/download/dr_harbour-of-pago-pago-island-of-tutuila-by-the-usexex-1839-6994000/6994000.jpg and Manuʻa https://archive.org/download/dr_islands-of-manua-manua-ofoo-ofu--oloosinga-olosega-samoan-group-6974000/6974000.jpg (both .sid-trapped, ~1536 px) | HTMC AS starts 1963; faʻasāmoa communal land (the park leases); two small flat pieces with expedition provenance are the honest ceiling. |

### Alaska (all heroes ride the nome graticule path — AK HTMC is TM)

| Park | Tier | Best verified candidate | Note |
|---|---|---|---|
| Denali | hero | PP 70 Pl. III, Brooks/Reaburn reconnaissance 1902–06 (pub. 1911), https://pubs.usgs.gov/pp/0070/plate-03.pdf (rendered, 7164 px) | drawn 1° grid, ~52 m/texel at 1:625k — size TEX_W to it; geology plate-09 and glacier plate-15 as companions; Koyukon Deenaalee; Kantishna stampede 1905; `AK_Mount McKinley_361197_1952_250000_geo.tif` as TM-caveat alt. |
| Glacier Bay | hero | Reid's 1890/92 survey map, 16th AR Pt I Pl. LXXXVI at PDF p. 523 of https://pubs.usgs.gov/ar/16-1/report.pdf (rendered 3565×4243, crisp litho) | drawn 20′ grid; the registration itself tells the retreat — ice drawn where the DEM holds open water; state the deliberate disagreement plus the era-datum caveat; Huna Tlingit homeland; geologic sketch (p. 541) and ice-front photo plates in the same report. |
| Katmai | hero | NGS 1917–19 monument map in Griggs 1922 (IA jp2, ~35 m/px at map scale): https://archive.org/download/valleyoftenthous00grig/valleyoftenthous00grig_jp2.zip/valleyoftenthous00grig_jp2%2Fvalleyoftenthous00grig_0389.jp2 | PD by age (1922); credit NGS plainly; 20′ grid; the 115-dpi scan is the plateau (higher-res rescan verified a dead end); Savonoski and Katmai — Sugpiaq/Alutiiq villages abandoned in 1912 — are on the map; 1951 63.36k lattice (54 files) as TM alt. |
| Kenai Fjords | wing | Bul 526 Pl. II, 1913 Kenai coast, https://pubs.usgs.gov/bul/0526/plate-2.pdf (rendered; companion plate-1) | genuinely the park's earliest cartography, but ~167 m/px at 1:500k — too coarse to drape honestly; the drawn coast wrapped around a blank Harding Icefield is the flat story. |
| Wrangell–St. Elias | hero | Bul 448 Pl. II, Nizina district 1911, https://pubs.usgs.gov/bul/0448/plate-2.pdf (rendered, 7117 px, drawn 5′ grid) | the Kennecott/McCarthy heart at district scale — the right-sized block for a 13-million-acre park; geologic plate-3 companion; Ahtna homeland (Nizina, Chitina, Tana names throughout); ar/20-7's 25 plate-map files for 1898 routes (numbering trap). |
| Lake Clark | hero | Bul 655 Pl. I, P.S. Smith's 1914 reconnaissance (pub. 1917), https://pubs.usgs.gov/bul/0655/plate-1.pdf (rendered, 11093 px) | crop the SE quadrant — the lake, Kijik/Qizhjeh (Denaʼina, now an NHL) and Telaquana with real contours; the surveyor's inked daily route dates are a built-in tour; Cook Inlet volcano coast off-sheet east; `AK_Lake Clark_361086_1946_250000_geo.tif` as TM alt. |
| Kobuk Valley | hero | Bul 815 Pl. 1, Smith & Mertie 1930, https://pubs.usgs.gov/bul/0815/plate-1.pdf (rendered, 15981 px, 1° grid) | slightly past the usual decade but PD-federal and the only drapeable early sheet; park block hugs the south edge — verify the dunes clear the neat; Iñupiat Kobuk, Onion Portage; Stoney/Cantwell 1880s river charts unverified (LOC 429). |
| Gates of the Arctic | hero | same Bul 815 Pl. 1 (SE quadrant read: Endicotts, Anaktuvuk Pass, Chandler Lake, upper Koyukuk) | covers the western/central park; the literal Gates (~150.7°W) sit at or past the east neat — verify before promising that tour; PP 20's folded route maps absent from the pubs scan; Nunamiut homeland; Marshall's 1930s maps skipped on copyright grounds. |

### Colorado Plateau + Saguaro

| Park | Tier | Best verified candidate | Note |
|---|---|---|---|
| Zion | hero | `UT_St George_252053_1885_250000_geo.tif` (probed; West Temple, Springdale, the Narrows, Kolob Arch all inside) | Powell-era 250k, no Zion-named HTMC sheet exists; canyon sits 300–500 px from the east neat — pair E–W with Kanab 1886; PP 220 pl. 2 (1950, https://pubs.usgs.gov/pp/0220/plate-2.pdf) as redrawn-lineage alt; Holmes' *Temples and Towers of the Virgen* (Dutton atlas p. 0021, 7855 px — caption carries the Paiute name Mukuntuweap); Southern Paiute (Parrusits) homeland. |
| Bryce Canyon | hero | `UT_Kanab_250081_1886_250000_geo.tif` (probed, title strip read) | the same sheet as east Zion — a combined Powell-survey southern-Utah build is natural; at 250k the amphitheater is a small patch of rim (the sheet's story is the Paunsaugunt — Southern Paiute homeland, say so); PP 226 plates 1/4 (1951) as alt/wing. |
| Arches | thin | — no Arches-named sheets in HTMC; first real topo is Moab 7.5′ 1952 / 15′ 1959 (listing verified) | `UT_La Sal_250204_1885_250000_geo.tif` (probed) covers the area if folded into a canyon-country sheet; LOC 429 blocked the panoramic/commercial check; Ute homeland, Wolfe Ranch rock art. |
| Canyonlands | hero | `UT_La Sal_250204_1885_250000_geo.tif` (probed; Green–Colorado confluence, Grand View Point, the Needles landmark-probed inside) | libby template, base doubles as primary; the Maze falls on San Rafael 1885 (listed); 1953 Needles 15′ as alt; Powell 1875 report river maps exist as a 165 MB IA jp2 zip (https://archive.org/download/explorationofcol00smit/explorationofcol00smit_jp2.zip) — plates not yet located inside, one fetch before promising. |
| Capitol Reef | hero | `UT_Fish Lake_249281_1885_250000_geo.tif` + `UT_Escalante_249177_1886_250000_geo.tif` (both probed) | missouri N–S join down the Waterpocket Fold; `UT_Fruita_249438_1954_62500_geo.tif` (probed) as anchor-seeded alt for the park core; Fremont-culture petroglyphs and Fruita orchards; the 1885–86 sheets predate the park name entirely — say so. |
| Petrified Forest | hero | `AZ_Petrified Forest_314893_1912_62500_geo.tif` (probed, title strip read) | the 1912 15′ special, six years after the monument; alt `AZ_St Johns_315591_1886_250000_geo.tif` (probed — Adamana, Agate Bridge, Blue Mesa, Rainbow Forest inside; Holbrook 1886's east edge just misses the park); Puerco Pueblo, Diné/Hopi/Zuni homeland; "Chalcedony Park" commercial art unverified (LOC 429). |
| Saguaro | hero | `AZ_Tucson_315407_1904_125000_geo.tif` + `AZ_Tucson Mountains_464970_1934_125000_geo.tif` (both probed) | two districts, two sheets overlapping at 111°: E–W join per front/missouri, or a single-district sheet on the pre-statehood 1904 quad; Tohono O'odham homeland and Hohokam petroglyphs, stated plainly. |

### Southern Rockies & Southwest

| Park | Tier | Best verified candidate | Note |
|---|---|---|---|
| Mesa Verde | hero | LOC 1915 park special, https://www.loc.gov/item/2012586900/ (search-verified; files 429-blocked; 1928 ed. https://www.loc.gov/item/2012586820/) over `CO_Soda Canyon_234458_1912_62500_geo.tif` (probed — Cliff Palace, Spruce Tree House, Balcony House inside; "Mesa Verde National Park" read in the margin) | libby recipe if the LOC scan delivers; the probed quad alone is the fallback primary; park carved from Weeminuche Ute reservation land (1911 exchange) — say so plainly; Holmes/Jackson 1876–79 ruins maps need one more IA volume hunt. |
| Black Canyon of the Gunnison | thin | — CO_Montrose 1909 125k probed: neat top edge exactly 38.5°, the NP gorge runs 38.55–38.59° — off-sheet; nothing pre-1950 north of it | 1965 USGS Bulletin 1191 (https://npshistory.com/publications/geology/bul/1191.pdf) is the PD flat fallback; Gunnison Tunnel and Ute homeland stories wait on a real primary. |
| Great Sand Dunes | wing | Hayden 1877 Colorado atlas, San Luis Valley sheets — https://archive.org/details/geologicalgeogra00hayd (full-res JP2 zip verified, 1.9 GB) | the dune field was first quad-mapped 1965–67 (Mosca/Medano/Liberty etc. all modern — verified); a Hayden graticule fit would plateau at kilometres — not a hero to promise; 1967 monument sheet: https://store.usgs.gov/assets/MOD/StoreFiles/PDF/48288_CO_Great_Sand_Dunes_Nat'l_Monument_1967.pdf; Ute and Jicarilla Apache homeland. |
| Grand Teton | hero | `WY_Grand Teton_342470_1899_125000_geo.tif` (probed, title strip read) | the whole 1929 park fits one 30′ quad (survey 1897–98) — quad-only hero; scan 342470 carries red reprint overprints, so pick the cleanest of five siblings (342466/342467/342468/342471, 1901); `WY_Gros Ventre_342472_1907_125000_geo.tif` (probed) only if 1950 boundaries wanted; Hayden 1877 Teton division (https://archive.org/details/eleventhannualre00hayd, JP2 zip verified) as wing; Tukudika (Sheep Eater) Shoshone homeland. |
| Carlsbad Caverns | hero | `NM_Carlsbad Caverns East_190018_1945_62500_geo.tif` + `NM_Carlsbad Caverns West_190023_1940_62500_geo.tif` (both probed; cavern entrance verified inside East) | park-named missouri E–W pair; 1940/45 is honestly the earliest topo that exists — say so; the famous 1925 NGS cave map is **copyrighted, do not use** — cave art from the 1939 NPS pamphlet https://npshistory.com/publications/cave/history-geology-1939.pdf; Jim White's guano era; Mescalero Apache homeland. |
| White Sands | thin | — NM_Tularosa 1916 125k probed: south neat exactly 33°, the dunefield (32.7–32.97°) wholly off-sheet; earliest dune mapping `NM_White Sands_193576_1955_24000_geo.tif` (listed) | verified gap, nothing in era; early Rules & Regulations brochures not located before LOC/time ran out; Mescalero Apache homeland. |
| Guadalupe Mountains | hero | `TX_Guadalupe Peak_128422_1933_48000_geo.tif` (probed; Guadalupe Peak and El Capitan inside) | the unusual 1:48,000 advance sheet (62.5k siblings also 1933) — single-quad build, zero registration work; Butterfield's Pinery station 1858–59 at the pass; Mescalero Apache stronghold and the 1869–80 campaigns; McKittrick Canyon mouth sits at the east neat. |

### Plains & Great Lakes

| Park | Tier | Best verified candidate | Note |
|---|---|---|---|
| Cuyahoga Valley | hero | `OH_Cleveland_224476_1903_62500_geo.tif` + `OH_Akron_224708_1903_62500_geo.tif` (both probed; joined 41°–41°30′ × 81°30′–81°45′) | first in line behind the ring: bitterroot N–S join drawing the Ohio & Erie Canal and Valley Railway twenty years before the parkway; park's NE fringe within a hair of the 81°30′ neat — check after fetch; 1953/1963 24k scans listed for the alt; Lenape and Wyandot country, 1805 Fort Industry cession; canal-era strip maps still unverified (LOC 429). |
| Badlands | wing | Darton PP 32 plates 35 + 69 (1905), https://pubs.usgs.gov/pp/0032/plate-35.pdf and https://pubs.usgs.gov/pp/0032/plate-69.pdf (both rendered) | 1:2.5M — context art, not park-scale; early 125k coverage stops at 103°W (verified), so the White River Badlands were never early-mapped; the missing hero is an 1890s Pine Ridge military/GLO map at LOC (429); the Stronghold and 1890 Ghost Dance ground demand ground-rule-4 provenance. |
| Theodore Roosevelt | thin | — HTMC over the park is 1970+ (verified); earliest brochure https://npshistory.com/publications/thro/brochures/1949.pdf (index-verified) | IA searches empty; leads for a later pass: LOC Dept. of Dakota military maps, GLO plats at glorecords.blm.gov; Mandan/Hidatsa/Arikara and Lakota country. |
| Voyageurs | hero | `MN_International Falls_804713_1919_62500_geo.tif` (probed) | modest libby/missouri single-quad: Rainy Lake, Black Bay and the boundary channel — the west end only (Kabetogama/Namakan/Crane first mapped 1963–69, verified) and the About must say so; the dream primary is the IBC 1909-treaty border-lakes atlas (~1931) — not on IA, LOC blocked; Bois Forte / Rainy Lake Ojibwe homeland. |
| Isle Royale | wing | Foster & Whitney 1850 copper-lands report, https://archive.org/details/reportongeology00fost (foldout plates at book-scan res); Lane 1898, https://archive.org/details/geologicalrepor00lanegoog | HTMC has zero Isle Royale GeoTIFFs (S3 KeyCount 0 — verified); a Lake Survey chart hero via nome-style graticule is plausible but unverified — LOC 429'd, NOAA search JS-only; first to re-scout when LOC cools; 1842 La Pointe / 1844 cession, Grand Portage and Lake Superior Ojibwe; 1941 brochure https://npshistory.com/publications/isro/brochures/1941.pdf. |
| Indiana Dunes | wing | LOC Dune Park photo series, http://www.loc.gov/item/2018649091/ (the survey's one LOC 200) + `IN_Dune Acres_156425_1953_24000_geo.tif` (listed; Chesterton/Gary 1953 too) | earliest quads are 1953 — the last map of the Central Dunes before Bethlehem Steel leveled them (1962–64); a 1953-vintage sheet is a maintainer judgment call, flagged not claimed; the 1917 Mather "Sand Dunes National Park" report is the lead; Potawatomi homeland, 1833 Chicago Treaty. |
| Gateway Arch | wing | Compton & Dry 1876 *Pictorial St. Louis* riverfront plates — IA set verified but .sid-trapped (~200 KB JPEGs), e.g. https://archive.org/details/dr_pictorial-st-louis-plate-29-plate-30-by-cn-dry-1876-00884105 — source from LOC when unblocked | wing-only by instruction and evidence: 91 urban acres, no terrain story, `MO_Saint Louis` is 1949 250k only; 1944 memorial brochure https://npshistory.com/publications/jeff/brochures/1944.pdf; Osage and Illinois Confederacy homelands, Cahokia across the river. |

### Southeast & islands

| Park | Tier | Best verified candidate | Note |
|---|---|---|---|
| Mammoth Cave | hero | LOC 1930 park-survey topo, https://www.loc.gov/item/2012588163/ (search-verified; files 429-blocked) over `KY_Mammoth Cave_803745_1922_62500_geo.tif` (probed, in hand) | libby recipe, both USGS lineage; if the LOC scan disappoints, the probed 1922 quad carries the sheet alone; the sinkhole plain drapes surprisingly well; cave-interior maps (Lee 1835, Hovey) belong in the Flat Wing but none verified this survey. |
| Hot Springs | hero | GF-215 plates (Purdue & Miser 1923), https://pubs.usgs.gov/gf/215/quad-area.pdf + quad-topography/quad-structure (all rendered; corners 34°37′57″ / 92°55′47″ printed on the neat) | the district sheet is **offset from the standard grid** — nome-style printed-graticule fit off the drawn 5′ crossings; `AR_Hot Springs_260499_1894_125000_geo.tif` (probed) as independent QA overlay; the 1832 reservation is the oldest federal-protection claim in the gallery; novaculite quarries — Caddo and Quapaw homeland; 1890 bird's-eye lead https://www.loc.gov/item/2001622065/ (search-verified only). |
| Congaree | thin | — SC_Columbia 1904 125k probed: the park lies off-sheet to the SE (its box maps to y≈7100–8450 on a 5958-px scan); covering quads begin 1943–53 | LOC throttled both attempts; floodplain relief is minimal anyway; Congaree, Santee, Wateree country. |
| Everglades | thin | — the 1838 *Map of the Seat of War in Florida* exists at IA only as .sid + 248 KB jpg (item dr_map-of-the-seat-of-war-in-florida-compiled-by-order-of-the-hon-joel-r-po-00194046) | HTMC FL_Everglades is 1973–74 only; every LOC query 429'd; ~2 m of relief makes a drape pointless — Flat Wing at best, re-scout LOC from a cool IP; Seminole and Miccosukee homeland, never ceded — say so. |
| Biscayne | thin | — HTMC FL_Miami starts 1950; FL_Key West 1921 62.5k exists but far southwest of the park | Coast Survey Biscayne Bay charts (1870s–) are a real future Flat Wing lead; NOAA endpoints guessed this session 404'd, LOC 429'd; Tequesta homeland. |
| Dry Tortugas | thin | — HTMC FL_Dry Tortugas starts 1971; 1850s+ Tortugas Harbor charts surely at LOC/NOAA, unverified (429; IA returned .sid-trapped items and a text record) | sea-level terrain: Flat Wing material only (Fort Jefferson charts). |
| Virgin Islands | thin | `VI_Eastern St John_462200_1958_24000_geo.tif` (probed — QuadGeoref accepts; **Puerto Rico datum, not NAD27** — lib/proj's Molodensky shift does not apply) + `VI_Western St John_462219_1958_24000_geo.tif` (HEAD 200) | graded thin because no pre-1930 primary was verified — the 1917 purchase-era USC&GS/Danish charts all 429'd; the probed St John base pair is banked, and Bordeaux Mtn's 1,277 ft would drape well — **first park to re-scout when LOC cools**; Taíno presence, 1733 St. John rebellion. |
| New River Gorge | hero | GF-77 Raleigh coal plate (Campbell 1902), https://pubs.usgs.gov/gf/077/quad-economic.pdf (+ quad-topography.pdf; both rendered) over `WV_Raleigh_254008_1902_125000_geo.tif` (probed) | yellowstone/libby pattern for the Thurmond–Prince–Quinnimont heart, plus a second self-draping block: `WV_Fayetteville_253221_1908_48000_geo.tif` (probed — holds Fayetteville and the bridge reach; the blocks nearly meet at Thurmond); "gf 72?" disproven — GF-72 is Charleston; a 2020 park wearing 1902 coal cartography is the story; C&O flat art .sid-trapped at IA, LOC unqueried. |

### Northeast

Both Northeast parks — **Acadia** and **Shenandoah** — made the first
ring; nothing remains to tabulate.

---

## Recommendation

Build the ring from the top. **`estes/` is nearly a one-day sheet** — the
only literal park special in HTMC, registration-free — and it anchors the
atlas's frame story, the USGS park-special program itself (see series
findings). **`blackhills/`** and **`smoky/`** are the proven
folio-over-its-own-quad pipeline verbatim (GF-219/1925, GF-16/1895), and
**`brightangel/`** is a two-quad Matthes join whose Dutton/Holmes atlas
wing is the finest flat material in the survey. **`mazama/`** extends the
nome pattern to a lower-48 classic — and rehearses the recipe the seven
Alaska heroes all need, of which **Glacier Bay (Reid 1892)** should go
first: there the registration itself is the story, ice drawn where the
DEM holds open water. Behind the ring, probe-verified and waiting:
`cuyahoga/`, Hot Springs, New River Gorge, Death Valley, and a combined
SEKI block; open composition calls are Zion+Bryce as one Powell-survey
sheet and SEKI as one block or two. The single highest-value follow-up is
not a build at all: **re-run the LOC checks from a cool IP** — Mesa Verde
and Mammoth Cave's primaries, Isle Royale's Lake Survey charts, the
Virgin Islands' purchase-era charts, the Everglades' Seat-of-War map and
every bird's-eye in the field sit behind the same 429. And per ground
rule 4: every sheet above stands on named homeland — the scouts carried
the specifics; keep them in the captions.
