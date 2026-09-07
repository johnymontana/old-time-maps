# The maps' sources and history

The following text is copied from each map viewer's existing About panel.
It describes the historical sheets and viewer pipelines. The printable models
use the modern terrain only; print scale and sampling are documented separately
in README.md and manifest.json. External links are retained in parentheses.

## The Gold Regions

Source: `gold/src/body.html`

The first map of Montana

Walter W. de Lacy's map of Montana Territory, drawn in the winter of 1864–65 for the First Legislature — every worked placer gulch and quartz district hatched in red — draped over the terrain he was mapping largely from hearsay.

The map

The territory was ten months old and its capital was a mining camp when the legislature hired de Lacy — surveyor, ex-soldier, prospector — to draw the first official map of Montana. Lithographed by Julius Hutawa of St. Louis, 1865; this is the Library of Congress copy, scanned at 8,984 × 6,634 pixels. The red overprint is the whole point: gulch diggings hatched, quartz lodes solid, from Bannack and Alder Gulch to camps that were weeks old when the stone was cut.

Putting it back on the earth

The sheet draws no internal graticule — only degree ticks along its borders: Greenwich longitudes above, Washington longitudes below, latitudes on the sides. The ticks are comb-matched and the degree labelling is chosen automatically as the one that lays the surveyed state boundary along de Lacy's heavy red territory line (it agrees to 98%). Residual across 27 border ticks: about 5 px, roughly 550 m at map scale — far tighter than the map itself, which is the point: east of the divide his boundary tracks the modern survey almost perfectly; in the northwest, where no surveyor had been, the blue truth cuts straight through his imagined ranges. The bottom border even yields the sheet's own prime meridian: de Lacy placed Washington 77°05′ west of Greenwich.

The draft beneath

The layer slider passes through de Lacy's original on its way to the modern relief: the pen-and-pencil manuscript on linen he drew that winter, held by the Montana Historical Society. It is registered to the print by correlation; where the two disagree by miles — and they do — you are watching de Lacy revise Montana between draft and stone.

The mines that came after

The Mines & lodes layer plots gold and silver producers from the USGS Mineral Resources Data System — four hundred of the strongest sites from a century and a half of digging — over the map that started the rush. Butte, in 1865, is a modest placer creek labelled Silver Bow.

The terrain

The grid, elevations and state-line mask are shared verbatim with the Montana in Relief sheet — same conic projection, same Terrarium tiles — because the footprint is the same state. The modern relief layer is toned in the lithograph's own sepia.

Reading it

Grid: 987 × 602 km · 362 m per height sample

Georeference: 27 border ticks · affine · ~5 px RMS

Prime meridian: Washington, 77°05′ W of Greenwich (measured)

Red overprint: diggings worked to January 1st, 1865

Sources

Map of the territory of Montana… 1865 (https://www.loc.gov/item/2006629609/) — Library of Congress, Geography and Map Division, free to use and reuse. Mines: USGS MRDS (https://mrdata.usgs.gov/mrds/), public domain. Elevation tiles are open data (https://registry.opendata.aws/terrain-tiles/). The rush this map advertises ran across the unceded homelands of the Séliš, Ql̓ispé, Ksanka, Niitsítapi, Apsáalooke and other nations; de Lacy's blank northwest was not empty country.

## The Head of Navigation

Source: `missouri/src/body.html`

The river that ran the territory

The Missouri where it earned its keep: the GREAT FALLS (surveyed 1884–85, edition of 1886) and FORT BENTON (1890) degree sheets joined at 111°W — the five falls, the portage plain, the Marias junction, and the levee at the head of steamboat navigation — with Mortson’s 1890 Official Map of Cascade County one slider-stop behind and the river’s own landmarks riding the terrain under an anchor.

The sheets

Two of the earliest degree sheets the Survey drew in Montana, engraved with 200-ft contours while the steamboats still ran: Fort Benton’s ferry and adobes, the falls that stopped every boat, the stage roads to Fort Shaw, and the Shonkin Sag’s dry glacial channel through the Highwoods. The county map behind them colours the Belt Mountains’ coal and silver workings and the township grid that was about to swallow the open range.

Registration, honestly

The degree sheets carry their own polyconic georeference. The county map is a township-plat compilation seeded from the printed symbols of Great Falls and Neihart and correlated against the degree sheets on shared river-and-grid ink — the residual is printed below; where its townships stretch, they stretch in plain sight.

The river as data

The anchor layer (⚓) marks the five falls by name, Giant Springs, the Fort Benton levee, Decision Point at the Marias mouth — where the expedition bet the journey on the clear fork and won — and Coal Banks Landing where the White Cliffs begin. Four flights run the river from the falls to the edge of the Breaks; the Head of Navigation flight says plainly what the levee’s ledger carried, whiskey trade and all.

Reading it

Grid: 166 × 126 km · 74 m per height sample

Relief: the river trench to Highwood Baldy at 7,625 ft

Georeference: sheets self-georeferenced · county map ≈ 1 km by correlation

Contours: the sheets’ 200 ft — key C

Sources

Degree sheets from the USGS Historical Topographic Map Collection (https://ngmdb.usgs.gov/topoview/) (scans 268740, 268718); county map from the Library of Congress (https://www.loc.gov/item/2002626670/); names from GNIS. Public domain throughout. Elevation tiles are open data (https://registry.opendata.aws/terrain-tiles/). This reach of the river is the treaty country of the Blackfeet, A’aninin and River Crow peoples; the trade the levee lived on ran through their lands, and the sheets’ empty-looking bench country was never empty.

## The Livingston Sheet

Source: `paradise/src/body.html`

Folio Number One

The first folio of the Geologic Atlas of the United States (Livingston, Montana, 1894; geology by Joseph Iddings and Walter Weed) — Paradise Valley, Tom Miner Basin, the Boulder and the southern Crazy Mountains, one full degree of country between the Northern Pacific main line and the Yellowstone Park boundary — with the 1891 engraved topography one slider-stop behind.

The folio

When the Survey set out to map the nation's geology folio by folio, it started here: the Livingston degree sheet, triangulated in 1883–86 under Henry Gannett with topography by Frank Tweedy, geology worked by Iddings and Weed out of the same campaigns that produced the Yellowstone Park folio two years later. The plate reads like a fever map — hot-pink Archean gneiss in the Absaroka front, brown volcanic breccias southward toward the park, olive Cretaceous belts through the Livingston coal country, and the Crazy Mountains' radial dike swarm bursting off the sheet's north edge like a firework. The east margin still carries the boundary of the Crow Reservation as it stood in 1891, the year before the tribe was pressed into ceding this strip; that line, and what it meant, are part of what the sheet records.

Three layers

The slider passes from modern relief through the 1891 topographic edition (USGS Historical Topographic Map Collection, carrying its own georeference, 200-ft contours) to the 1894 folio geology. The folio plate is registered to the 1891 base by correlation on a local high-pass ink mask — the same engraving beneath both printings — at 1.9 px RMS ≈ 40 m on 119 control points.

The mines as data

The Summits & mines layer plots forty-four recorded gold, silver, lead and copper producers from the USGS MRDS database — Emigrant Gulch's placers and lodes, Jardine's gold-and-arsenic veins above Gardiner, the snowbound Independence camp at the head of the Boulder — over the geology the folio's own economic plate first keyed to them.

The terrain

Elevations are open Terrarium tiles at zoom 12 on a local conic grid — about 27 m per drape texel over the 93 × 127 km block, from the Yellowstone's exit near 3,980 ft to Mount Cowen at 11,206, with Electric Peak shared across the park line from the Yellowstone folio sheet. The bottom edge of the block is the park's northern boundary, engraved across the sheet exactly where the terrain still changes hands today.

Reading it

Grid: 93 × 127 km · 55 m per height sample

Relief: 1,214 m (Yellowstone River) to 3,416 m (Mount Cowen)

Georeference: folio plate vs 1891 base · correlation · 1.9 px ≈ 40 m

Contours: the sheet's 200 ft — key C

Sources

USGS Geologic Atlas, Folio 1 (https://pubs.usgs.gov/publication/gf1) (Iddings & Weed, 1894); base sheet from the Historical Topographic Map Collection (https://ngmdb.usgs.gov/topoview/) (scan 268784, edition of December 1891); mines from MRDS (https://mrdata.usgs.gov/mrds/); names from GNIS. All U.S. government works, public domain. Elevation tiles are open data (https://registry.opendata.aws/terrain-tiles/). The Crazy Mountains are Awaxaawippíia, a fasting and vision place of the Apsáalooke, and this whole sheet is their treaty country.

## Yellowstone in Folio

Source: `yellowstone/src/body.html`

The first park, surveyed

Arnold Hague's geologic folio of Yellowstone National Park (Geologic Atlas of the United States, Folio 30, 1896) — four quadrangle sheets of orange rhyolite, purple Absaroka breccia and white geyser sinter — joined into one drape, with the 1911 engraved topography of the same four quadrangles one slider-stop behind.

The folio

Congress made Yellowstone the world's first national park in 1872, largely on the strength of maps and testimony from the federal surveys; the Geological Survey then spent the 1880s and 90s giving the park a scientific footing. The four 30-minute quadrangles — Gallatin, Canyon, Shoshone and Lake — were triangulated and drawn in 1883–85 by J. H. Renshawe, Frank Tweedy and colleagues under chief geographer Henry Gannett; Arnold Hague's parties (with Iddings, Weed and Wright) worked the geology through 1893, and Folio 30 printed the areal sheets in April 1896 under Director Charles D. Walcott. Half the block is one immense rhyolite field; no one could yet see the 640,000-year-old caldera it fills, and the folio is the honest record of what could be known before that reading.

Three layers

The slider passes from modern relief through the 1911 topographic editions — the same four quadrangles at their engraved best, from the USGS Historical Topographic Map Collection, each carrying its own georeference — to the 1896 folio geology. Each folio plate is registered to its own base quad by correlation on shared linework; same survey, same engraving lineage, so the fits are tight (the residuals are printed below). The four printings are tone-matched at their paper whites and meet at their neatlines.

The geysers as data

The Summits & geysers layer plots about seventy named geysers and hot springs from the U.S. Board on Geographic Names (GNIS) over the geology that drives them — Old Faithful to Steamboat, Grand Prismatic to the Mud Volcano — famous names first, thinned so the basins stay readable. Every white patch on Hague's sheets is hot ground.

The terrain

Elevations are open Terrarium tiles at zoom 12 on a local conic grid — about 27 m per drape texel over the 95 × 126 km block, from the Falls River corner near 5,100 ft to Table Mountain at 11,063, with Electric Peak standing just over the sheet edge on the Montana side. The north edge of the block is the 45th parallel: the Montana boundary line, engraved across the top of both northern sheets.

Reading it

Grid: 95 × 126 km · 55 m per height sample

Relief: 1,569 m (Falls River) to 3,364 m (Table Mountain)

Georeference: four plates vs their 1911 bases · correlation · 1.5–2.2 px ≈ 16–23 m

Contours: the sheets' 100 ft — key C

Sources

USGS Geologic Atlas, Folio 30 (https://pubs.usgs.gov/publication/gf30) (Hague, 1896); base quadrangles from the Historical Topographic Map Collection (https://ngmdb.usgs.gov/topoview/) (scans 342460, 342404, 342550, 342496, editions of 1911); names from GNIS (https://www.usgs.gov/us-board-on-geographic-names). All U.S. government works, public domain. Elevation tiles are open data (https://registry.opendata.aws/terrain-tiles/). The park is the homeland of the Tukudika Shoshone and the treaty country of many nations; the Nez Perce crossed every sheet of this block in their 1877 flight.

## Glacier in Contours

Source: `glacier/src/body.html`

The park, as first surveyed

The USGS-engraved sheet of Glacier National Park — 100-foot contours and hand-laid relief over the Lewis and Livingston ranges, drawn from the surveys of 1900–1912 — draped on the terrain it describes, with the park's vanishing glaciers carried along as data.

The sheet

Surveyed under R.B. Marshall in 1900–1904 and 1907–1912, engraved and printed by the U.S. Geological Survey; this is the Interior Department's administrative printing of 1915, scanned by the Library of Congress at 9,788 × 8,492 pixels. Going-to-the-Sun Road does not exist on it — the road opened in 1933; in 1915 you crossed Logan Pass on a saddle horse behind a guide.

Putting it back on the earth

The scan carries no coordinates, so it was registered against the survey's own 30-minute quadrangles — Chief Mountain (1904), Kintla Lakes (1906), Nyack (1914) and Marias Pass (1913), which the USGS distributes already georeferenced. The 49th-parallel boundary line seeds the alignment; shared linework (black culture, blue drainage) is then matched by image correlation, giving 38 control points across the sheet. Residual: 2.2 px median, 2.7 px RMS — about 30 metres on the ground, tighter than the 1912 triangulation itself.

The geology between

The layer slider now passes through a third sheet on its way to the modern relief: Clyde Ross's reconnaissance geologic map of the park (USGS Professional Paper 296, plate 1, 1959) — the Lewis Overthrust story in colour, Precambrian Belt rocks in reds riding over Cretaceous plains in green. It is registered to the 1915 sheet by the same correlation method; the two agree to roughly half a kilometre, which is about the drafting precision of a reconnaissance geology at this scale.

The ice, then and now

Two vector layers ride the terrain beside the engraving: the named glaciers at their Little-Ice-Age maxima (~1850, mapped by the USGS from moraines) and the same glaciers in 2015. The surveyors drew the ice a lifetime past its peak; the century since has taken most of what they saw. Data: USGS Northern Rocky Mountain Science Center, ScienceBase.

The terrain

Elevations are open Terrarium tiles (SRTM/NED lineage) at zoom 12 on the same conic grid — about 31 m per drape texel over a 112 × 99 km plate. The modern relief layer's tints are drawn from the sheet's own inks: cream lowland, woodland green, engraved brown, and the blue-white of ice.

Reading it

Grid: 112 × 99 km · 41 m per height sample

Relief: 881 m (Flathead River) to 3,179 m (Mt Cleveland)

Georeference: 38 correlation points vs sibling quads · 2.7 px RMS

Contours: the sheet's own interval, 100 ft — key C

Sources

Administrative map of Glacier National Park, 1915 (https://www.loc.gov/item/2016586564/) — Library of Congress, Geography and Map Division, free to use and reuse. Registration quads from the USGS Historical Topographic Map Collection (https://ngmdb.usgs.gov/topoview/). Glacier margins: USGS glacier margin time series (https://www.sciencebase.gov/catalog/item/58af7022e4b01ccd54f9f542) and Little-Ice-Age maxima. Elevation tiles are open data (https://registry.opendata.aws/terrain-tiles/). The park's east front lies within the Blackfeet Nation's treaty lands, sold under duress in 1895 — Nínaiistáko, Chief Mountain, remains sacred ground.

## The Bitterroot

Source: `bitterroot/src/body.html`

The valley and the wall

Two engraved quadrangles joined at 46°30′ — HAMILTON (edition of 1901) and MISSOULA (edition of 1912) — the Bitterroot Valley end to end, from the Como moraines to the Hellgate, with J.B. Leiberg's 1898 Bitterroot Forest Reserve survey one slider-stop behind.

The sheets

The Survey mapped the valley at the turn of the century: the Hamilton quadrangle surveyed 1899–1900, the Missoula quadrangle behind it, both with 100-ft contours and the township grid ruled across the irrigated floor. The 1912 sheet ends at Missoula's doorstep — the city's street grid touches the neat line — and the pair together hold the whole story: mission and treaty valley, railroad and orchard boom, and forty miles of granite canyons on the west wall.

Three layers

The slider passes from modern relief through Leiberg's 1898 land-classification map of the Bitterroot Forest Reserve (USGS 20th Annual Report) to the quadrangles. Leiberg's plate is a sketch-contour compilation, not the quad engraving — it is seeded from the printed symbols of Stevensville and Hamilton and refined by correlation where the valley's grid and drainage hold, to about 7 px ≈ 150 m. The reserve ended at the Lolo divide, so the layer fades to paper in the sheet's north; its greens are board-feet of standing timber, its hatching the burns the 1910 fires would redouble.

The mines as data

Seventeen recorded producers from MRDS ride the terrain — the Curlew at Victor, placers on Hughes Creek, prospects in the Sapphires — a modest layer, honestly: this valley's fortunes were water, timber and soil.

The terrain

Elevations are open Terrarium tiles at zoom 12 on a local conic grid — about 28 m per drape texel over the 53 × 126 km strip, from the Clark Fork near 3,100 ft to Saint Joseph Peak at 9,587. Look at Sentinel and Jumbo above Missoula: the horizontal benches are the strandlines of Glacial Lake Missoula.

Reading it

Grid: 53 × 126 km · 42 m per height sample

Relief: 875 m (Clark Fork) to 2,930 m (St. Joseph Peak)

Georeference: quads self-georeferenced · Leiberg vs quads · 7.4 px ≈ 150 m

Contours: the sheets' 100 ft — key C

Sources

Quadrangles from the USGS Historical Topographic Map Collection (https://ngmdb.usgs.gov/topoview/) (scans 268555, 268581); Leiberg's plate from the 20th Annual Report, part V (https://pubs.usgs.gov/ar/20-5/); mines from MRDS (https://mrdata.usgs.gov/mrds/); names from GNIS. All U.S. government works, public domain. Elevation tiles are open data (https://registry.opendata.aws/terrain-tiles/). This valley is the homeland of the Bitterroot Salish, promised to them by the 1855 Hellgate Treaty and taken from them in 1891; the St. Mary's Mission flight says so plainly.

## The Rocky Mountain Front

Source: `front/src/body.html`

Where the mountains meet the plains

Four engraved quadrangles tiled into one degree of the Rocky Mountain Front — SAYPO (1903), CHOTEAU (1920), HEART BUTTE (1918) and DUPUYER (1920) — the overthrust wall the Blackfeet call Miistákis, the Backbone of the World, with H.B. Ayres' 1899 forest-reserve survey one slider-stop behind.

The sheets

The block reads as two worlds because it is one: on the west half, reef after reef of thrust-faulted limestone drawn in hundred-foot contours, with the young Lewis and Clarke Forest Reserve lettered across it; on the east, the ruled township grid of the wheat and sheep bench, surveyed after the homestead boom. The north half is the Blackfeet Nation — the sheets carry the reservation lettering, and the 1896 cession line along Birch Creek is part of what they record. Augusta sits just off the south edge, Choteau anchors the east, and every canyon — Sun, Teton, Deep, Birch, Two Medicine — is a water gap sawed through the reefs.

Three layers

The slider passes from modern relief through Ayres' 1899 land-classification map of the Lewis and Clark Forest Reserve (USGS 21st Annual Report — "GREAT PLAINS (TREELESS)" sweeping its east half) to the quadrangles. Ayres drew with sketch contours at reconnaissance scale; seeded from the printed symbols of Choteau and Dupuyer and refined by correlation, his plate sits about a mile from the surveyed quads in places (39 px RMS at the plate's ~41 m/px). That disagreement is the distance between reconnaissance and survey — the greens are where the timber stood, even where the streams wander.

The terrain

Elevations are open Terrarium tiles at zoom 12 on a local conic grid — about 27 m per drape texel over the 90 × 126 km block, from the Teton's exit near 3,600 ft to Rocky Mountain at 9,392. The modern terrain holds Gibson Reservoir in the Sun River Canyon; the 1903 sheet shows only the river — the dam came in 1929, and the mismatch is left in plain sight.

Reading it

Grid: 90 × 126 km · 53 m per height sample

Relief: 1,050 m (Teton River) to 2,849 m (Rocky Mountain)

Georeference: quads self-georeferenced · Ayres vs quads · 39 px ≈ 1.6 km

Contours: the sheets' 100 ft — key C

Sources

Quadrangles from the USGS Historical Topographic Map Collection (https://ngmdb.usgs.gov/topoview/) (scans 268609, 472643, 268562, 472677); Ayres' plate from the 21st Annual Report, part V (https://pubs.usgs.gov/ar/21-5/); names from GNIS. All U.S. government works, public domain. Elevation tiles are open data (https://registry.opendata.aws/terrain-tiles/). The northern half of this sheet is the Blackfeet Nation; the Old North Trail along the mountain foot, the Starvation Winter on Badger Creek, and the star-story mountain names are theirs, and the Old North Trail flight says so plainly.

## Montana by Rail

Source: `rails/src/body.html`

Twenty-eight years of iron

Two railroad maps of Montana on one slider: Rand McNally’s New Commercial Atlas map of 1912 — four transcontinental routes, the branch web, electric lines already in the legend — and Geo. F. Cram’s Railroad and County Map of Montana Ty. of 1884, when the Northern Pacific was one year old and almost alone. Pull the slider back and the web vanishes.

The maps

Cram’s 1884 pocket map shows a territory with two railroads: the just-completed Northern Pacific along the Yellowstone and the Clark Fork, and the Utah & Northern narrow gauge reaching Butte from the south. By Rand McNally’s 1912 sheet the Great Northern runs the Hi-Line, the Milwaukee’s Puget Sound extension threads between its rivals, the Burlington slips in from the southeast, and the index lists a dozen roads down to the White Sulphur Springs & Yellowstone Park. Both maps hang on the montana sheet’s own terrain and grid.

Registration, honestly

Neither map carries a trustworthy projection. Each is seeded from two printed townsites and correlated against the already-georeferenced 1991 relief sheet on shared drainage ink. The 1912 atlas spread is fitted as two pages and rejoined at its binding fold (a cubic per page, ≈1.8 km — about the drafting accuracy of a commercial atlas). Cram’s 1884 compilation disagrees with the modern grid by up to five miles: territorial mapping, bent as far as a cubic will follow and left honest beyond that.

Passes & tunnels as data

The data layer (∩) marks where the rails beat the mountains: Mullan and Bozeman Pass tunnels, Stevens’ Marias Pass, the Milwaukee’s Pipestone crossing, Monida, Lookout — and Gold Creek, where Ulysses S. Grant drove the Northern Pacific’s last spike on September 8, 1883. Five flights run from the last spike to the electrics.

Reading it

Grid: the montana sheet’s, reused — 1,030 × 500 km

Terrain: the montana sheet’s height field, re-encoded

Georeference: 1912: two cubic fits ≈1.8 km · 1884: ≈8 km, period-honest

Layers: 1912 network · 1884 territory · modern relief

Sources

Rand McNally 1912 map from the Internet Archive (https://archive.org/details/dr_montana-2790233), scan via the David Rumsey Map Collection (the work itself is public domain by age); Cram 1884 from the Library of Congress (https://www.loc.gov/item/99441786/), Geography & Map Division. Pass and townsite coordinates from GNIS. Elevation tiles are open data (https://registry.opendata.aws/terrain-tiles/). Both maps draw the reservations of 1884 and 1912 as the railroads’ era bounded them; the land the grants and the lines crossed was, and is, treaty land.

## The Flathead Country

Source: `flathead/src/body.html`

The Army's map of the valley

Flathead Lake and its valley — Somers, Bigfork, Kalispell, Whitefish — on two sheets of the U.S. Army's Progressive Military Map, joined at the 48th parallel and draped over the terrain they describe.

The sheets

South of 48°: the Flathead Lake quadrangle, an advance sheet (146-N-E/2) printed by the Engineer Reproduction Plant in 1920 on warm tan paper. North of 48°: the Kalispell quadrangle (1669:30/31), compiled in 1919 under Col. Chas. L. Potter and reprinted by the Army Map Service in 1943. Both are planimetric compilations — General Land Office township plats, USGS and Forest Atlas sheets, county maps — drawn at 1:125,000 with no contours. A pencilled note on the 1920 sheet reads "not mapped by USGS."

The join

The two printings meet at 48°00′ — the hairline drawn across the map is that join, left visible on purpose. The 1943 sheet has been tone-matched to the 1920 paper, but the lake keeps two textures: dark stipple below the line, pale wash above. One more honesty: Kerr Dam raised the lake about ten feet in 1938, so the 1920 sheet shows the natural shore and the model beneath it carries today's.

The county map between

The layer slider passes through a third sheet: Jaqueth & Walters' 1908 Map of Flathead County and the Flathead Indian Reservation (Montana Historical Society) — the whole lake on one sheet, with steamboat routes, forest reserves and the proposed Glacier National Park drawn in. It is registered to the Army sheets by correlation, seeded from the townsites of Somers and Polson; agreement is about 4 px, roughly 200 m.

Putting them back on the earth

Both scans carry their georeference — a polyconic projection on the 1927 North American Datum, at 10.58 m per pixel. The grid here is a local Lambert conformal conic (standard parallels 47°42′ and 48°18′); each texel is datum-shifted to NAD27 and looked up in the sheets directly. Checked against a dozen townsites, the chain lands within roughly one scan pixel — under 100 m on the ground. Beyond the neatlines the sheets end and the modern model continues, dimmed.

The terrain

Elevations are open Terrarium tiles (SRTM/NED lineage) at zoom 12, resampled onto the same conic grid — about 26 m per drape texel and 32 m per height sample over a 54 × 128 km plate.

Reading it

Grid: 54 × 128 km · 32 m per height sample

Relief: 771 m (Flathead River) to 2,743 m (Swan crest)

Georeference: embedded polyconic · NAD27 → WGS84 · ≲ 100 m

Shadows: ray-marched against the height field, per pixel

Sources

Scans: USGS Historical Topographic Map Collection (https://ngmdb.usgs.gov/topoview/) (scans 472710 and 472788), public domain as U.S. government works. Elevation tiles are open data (https://registry.opendata.aws/terrain-tiles/). The south half of the lake lies within the Flathead Reservation of the Séliš, Ql̓ispé and Ksanka people; the township grid engraved on these sheets is the survey that opened those lands to homesteading in 1910.

## The Libby Quadrangle

Source: `libby/src/body.html`

The ore beneath the Cabinets

Russell Gibson's geologic map of the Libby quadrangle (USGS Bulletin 956, 1948) — Belt rocks, granite stocks, and the silver-lead veins that paid for the town — draped over the Cabinet Mountains with its 1932 topographic base one slider-stop behind it.

The sheet

Gibson mapped the quadrangle for the Survey through the 1930s; the bulletin's plate colours the Precambrian Belt series — the same stack of argillites and quartzites that builds Glacier Park — cut by granite stocks whose margins carry the veins. A printed List of Mines, Prospects and Placers keys every numbered working on the map. Gold was panned on Libby Creek in 1867; the Snowshoe silver-lead vein carried the district from 1889.

Three layers

The slider passes from the modern relief through the 1932 topographic base (USGS Historical Topographic Map Collection, already georeferenced) to the 1948 geology printed over that very base. The plate is registered to the base by correlation — about 46 px, some 370 m, the drafting difference between the bulletin's re-engraved base and the original quad.

The mines as data

The Summits & mines layer plots fifty recorded gold, silver, lead, copper and zinc producers from the USGS MRDS database over the geology that explains them. Northeast of town, past the sheet's edge, Rainy Creek's vermiculite mine is part of the story too — the Rainy Creek flight says plainly what the 1948 map could not yet know about asbestos, and what Libby has carried since.

The terrain

Elevations are open Terrarium tiles at zoom 12 on a local conic grid — about 26 m per drape texel over a 52 × 71 km plate, from the Kootenai's cedar bottoms near 1,800 ft to Snowshoe Peak at 8,738.

Reading it

Grid: 52 × 71 km · 38 m per height sample

Relief: 556 m (Kootenai River) to 2,644 m (Snowshoe Peak)

Georeference: plate vs 1932 base · correlation · ~370 m

Contours: the base map's 100 ft — key C

Sources

USGS Bulletin 956 (https://pubs.usgs.gov/publication/b956), plate 1 (1948); base quad from the Historical Topographic Map Collection (https://ngmdb.usgs.gov/topoview/) (scan 268577); mines from MRDS (https://mrdata.usgs.gov/mrds/). All U.S. government works, public domain. Elevation tiles are open data (https://registry.opendata.aws/terrain-tiles/). Kootenai Falls remains a sacred site of the Ktunaxa Nation.

## Montana in Relief

Source: `montana/src/body.html`

A 1991 sheet, lifted off the paper

Allan Cartography's Montana — the shaded-relief sheet that taught a generation of Montanans what their state looks like — draped over the elevation model it was drawn to describe.

The map

Prepared by Allan Cartography of Medford, Oregon, from the U.S. Geological Survey's 1:500,000 state base series and published at 1:600,000, revised 1991. Relief is shown by gradient tints, hand-tuned shading and spot heights; the original is a single colour sheet, 104 × 164 cm. Scanned at 15,000 × 9,521 pixels by the American Geographical Society Library at the University of Wisconsin–Milwaukee.

Putting it back on the earth

The scan carries no coordinates, so it was georeferenced here from the ground up: the printed map body was isolated by colour, its silhouette matched against the surveyed state boundary, and a Lambert conformal conic projection — standard parallels 45° and 49°, central meridian 109°30′ W, the USGS state-base convention — fitted through it, with a cubic correction absorbing the paper's own distortion and the seam where the two sheets were joined. Residual against 8,700 boundary points: 1.4 pixels median, roughly 190 m on the ground.

The terrain

Elevations come from the open Terrarium tiles (SRTM and NED lineage), resampled onto the same conic grid as the map so that ridge for ridge, the 1991 engraving and the modern model line up. The hypsometric tints on the modern relief layer are not invented: they are sampled from the elevation legend printed at the bottom of the sheet, so the crossfade moves between two renderings of one palette.

Reading it

Grid: 987 × 602 km · 362 m per height sample

Relief: 549 m (Kootenai River) to 3,904 m (Granite Peak)

Shadows: ray-marched against the height field, per pixel

Elevations: cursor values sampled from the model; summit figures as published

Source

American Geographical Society Library Digital Map Collection, item 17590 (https://collections.lib.uwm.edu/digital/collection/agdm/id/17590/rec/20) · University of Wisconsin–Milwaukee Libraries. Please consult the library's rights statement before reuse of the scan.

## Nome, the Golden Beach

Source: `nome/src/body.html`

The golden beach

The Nome quadrangle of USGS Bulletin 533 — Moffit's 1913 geologic map of the Cape Nome placers over Gerdine's 1904 topography of the same half-degree — the one gold rush a steamer ticket could join, draped on modern terrain with the district's placer creeks as data.

The sheets

Gerdine's parties surveyed the quadrangle in 1904, five seasons after the "Three Lucky Swedes" staked Anvil Creek and four after twenty thousand stampeders rocked gold out of the very beach; Moffit, Hess and Smith mapped the geology over it in 1905–06, and Congress printed both as House Document 1428 in 1913. Everything the rush needed is engraved here: the roadstead town at the sand's edge, WIRELESS STATION and FORT DAVIS, the ditches contouring the benches, the schist uplands (sc) that shed the gold and the coastal plain (Qcp) that caught it — and one engraved confession under the border: "Railroad unsurveyed; position approximate."

Three layers

The slider passes from modern relief through the 1904 topographic plate to the 1913 geologic plate. There is no georeferenced base to check these against — the Survey's Alaska scans use a projection this pipeline's quad reader refuses — so both plates are fitted from their own printed graticule: all 28 drawn 5-minute crossings per plate were measured once from ruler-grid crops and a degree-1 fit lands on the net at about 2 px ≈ 11 m (a warped top-left corner trimmed from each). That is the internal fit only, with no correlation cross-check; the printed graticule is taken at face value, so whatever offset the 1904 Coast and Geodetic control carries against modern datums — likely a couple hundred metres hereabouts — rides along in both plates equally.

The placers as data

The Summits & placers layer plots forty ⚒ names from GNIS — Anvil, Snow Gulch, Glacier, Dexter, Specimen and the rest of the creeks and gulches Bulletin 533 describes working by working, plus the Seward Ditch that watered them. The current GNIS Alaska file carries no Mine class at all, so the named placer ground itself stands for the workings; the beach placers, which belonged to no one and everyone, have no coordinates to plot.

The terrain

Elevations are open Terrarium tiles at zoom 12 on a local conic grid — about 13 m per drape texel over the 33 × 37 km block, from Norton Sound held at zero to the schist domes above Osborn Creek. The relief is real but modest: Anvil Mountain's printed 1,050 feet is the skyline of the whole rush.

Reading it

Grid: 33 × 37 km · 19 m per height sample

Relief: 0 m (Norton Sound) to 634 m (Osborn divide)

Georeference: printed graticule, 27 crossings kept per plate · deg-1 · 2.0 px ≈ 11 m · no cross-check

Contours: the plates' 25 ft — key C

Sources

USGS Bulletin 533 (https://pubs.usgs.gov/publication/b533) (Moffit, 1913), Plate III (https://pubs.usgs.gov/bul/0533/plate-3.pdf) and Plate I (https://pubs.usgs.gov/bul/0533/plate-1.pdf); names and coordinates from GNIS (https://www.usgs.gov/tools/geographic-names-information-system-gnis). All U.S. government works, public domain. Elevation tiles are open data (https://registry.opendata.aws/terrain-tiles/). Nome stands in Sitŋasuaq — Inupiaq homeland, King Islanders wintering on its beach into the 1960s — whose people mined, freighted and clothed the camp and, barred from citizenship until 1924, could not hold the claims these sheets record; the Wires and Rails flight says so plainly.

## Bright Angel

Source: `brightangel/src/body.html`

A mile of rock, drawn in fifty-foot lines

François E. Matthes' two 1:48,000 specials of the Grand Canyon — BRIGHT ANGEL and VISHNU, surveyed with plane table and mule in 1902–03 — joined at 112°W over modern terrain, with the Powell-era reconnaissance of 1886 one slider stop behind, and the canyon's named rapids, springs and falls riding the ground as data.

The two sheets

The Survey sent a party to the canyon in 1902 to do something nobody had done: map it properly. The credit line is short — E. M. Douglas, geographer in charge; topography by François E. Matthes (and, on the east sheet, Richard T. Evans); triangulation by H. L. Baldwin, Jr. and J. T. Stewart; surveyed in 1902–1903 — and the result was a fifteen-minute quadrangle pair at four thousand feet to the inch with a fifty-foot contour interval, fine enough that in the Redwall the lines merge into a solid band. The east sheet was engraved in June 1906 and printed as the edition of September 1907; the west sheet carries the note that "a map of Grand Canyon National Park … is published in two sheets (east and west)," which is what you are standing on. The Survey did not replace them until the 1960s: the next Bright Angel and Vishnu editions in the collection are 1962.

Two honest notes about the paper. The west sheet is dated 1903 and its contours are Matthes' 1902–03 work, but the scan is a mid-century reissue and the culture on it kept accruing: El Tovar (1905), the Powell Memorial (1918), the Kaibab Trail and its 1928 suspension bridge, Grand Canyon Lodge (1928) are all lettered on a 1903 sheet. The east sheet is the plain 1907 first edition, printed before there was a park at all — so the drape crosses from a built rim to an empty one at 112°W, and that is a real difference, not a seam artefact.

Three layers, none of them fitted

All four scans are USGS Historical Topographic Map Collection GeoTIFFs, and every one of them carries its own polyconic projection on NAD27 in its geokeys. So there is no registration on this sheet: no control points, no correlation, no polynomial. Each plate is placed by the transform it was scanned with, clipped to its own printed neatline, and the four corners of every neat were probed against the raster before anything was resampled. The two printings in each pair are tone-matched at both ends of their histogram — paper white and deepest ink — so the 1903 and 1907 presses meet at 112°W without a colour step.

What that leaves is a disagreement worth measuring. The middle stop is the 1886 reconnaissance: the ARIZONA Kaibab and Echo Cliffs sheets at 1:250,000, drawn with 250-foot contours and signed J. W. Powell, Director — the man who ran the river in 1869. Sample the blue line on each layer and the river Powell's men drew lies a median 570 m from the river Matthes drew, a quarter of it more than 1.4 km away. That is the distance between reconnaissance and survey, and it is left in plain sight. The temples show it too: slide back to 1886 and forty miles of rim carries almost no names — Point Sublime and Shivas Temple, and little else.

One more number. Both specials predate the 1927 datum, and the west sheet says so: "To place on 1927 North American datum move projection lines 420 feet south and 350 feet west." We drape the georeference as staged rather than nudging it, and the drawn Colorado duly runs a median 113 m south of the modern channel through the west half — 420 feet is 128 m, so what you see is the printed correction, measured.

The water as data

The Summits & waters layer plots thirty named waters from the U.S. Board on Geographic Names: every rapid the Colorado runs through this block, the springs that keep both rims and the inner canyon alive, and the two waterfalls. Read together they explain the place. Each rapid sits at a side-canyon mouth — Hance below Red Canyon, Granite below Monument Creek, Crystal below Crystal Creek — because rapids in this canyon are boulder piles delivered by flash floods, not river work. The springs are the other half: Redwall and Muav water leaking back out at Roaring Springs, Santa Maria, Dripping and Cliff, which is why every trail on the sheet goes where it goes.

The terrain

Elevations are open Terrarium tiles at zoom 12 on a local conic grid — about 20 m per drape texel over a 51 × 34 km grid holding a 45 × 28 km block. The relief inside the neat runs 705 m to 2,642 m: 6,355 feet of it, in a place where you can stand at the top and the bottom on the same afternoon. The north edge cuts the Kaibab Plateau just short of Point Imperial, so the block's high ground sits on the neat line itself; the low point is the Colorado leaving the sheet at Crystal, 2,314 feet.

Reading it

Grid: 51 × 34 km · 30 m per height sample

Relief: 705 m (2,314 ft, the Colorado at the west neat) to 2,642 m (8,669 ft, the Kaibab Plateau on the north neat)

Georeference: four HTMC GeoTIFFs on their own polyconic/NAD27 keys · no fitted control points · 1886 vs 1903–07 river ≈ 570 m median

Contours: key C draws the sheets' 250 ft index line — the printed interval is 50 ft, finer than a 30 m model can honestly carry

Sources

All four plates from the USGS Historical Topographic Map Collection (https://ngmdb.usgs.gov/topoview/) — Bright Angel 1903 (scan 314253) and Vishnu 1907 (scan 464981) at 1:48,000, Kaibab and Echo Cliffs 1886 (scans 315511, 315475) at 1:250,000; names, coordinates and summit elevations from GNIS (https://www.usgs.gov/us-board-on-geographic-names). All U.S. government works, public domain. Elevation tiles are open data (https://registry.opendata.aws/terrain-tiles/). This canyon is Havasupai and Hualapai homeland, and Hopi, Diné, Southern Paiute and Zuni country: the Havasu 'Baaja farmed the spring bench the west sheet letters "Indian Garden" until an 1882 executive order cut their land to 518 acres and the Park Service forced the last family out in 1928; 185,000 acres were returned by act of Congress in 1975, and the U.S. Board on Geographic Names restored the name Havasupai Gardens in 2022. Sipapuni, the Hopi place of emergence, lies in the Little Colorado gorge at the sheet's east edge. The Bright Angel and the garden flight says all of this on the ground it happened.

## Yosemite Before the Dam

Source: `yosemite/src/body.html`

Hetch Hetchy, still a valley

Four engraved quadrangles at 1:125,000 — YOSEMITE (1909), MT. LYELL (1901), DARDANELLES (1898) and BRIDGEPORT (1911) — tiled into one block of the Sierra Nevada and draped over modern elevations. Every one of them was printed before the Raker Act of December 1913, so on this drape Hetch Hetchy is still a valley with a river in it. Pull the slider one stop and François Matthes' 1930 park map puts the reservoir there instead.

The sheets

These are the 30-minute quadrangles the Survey ran up the Sierra while the park was being argued over: Yosemite (surveyed 1893–94, engraved June 1896, this edition of April 1909), Mt. Lyell (1898–99, edition of May 1901), Dardanelles (1891–96, edition of May 1898) and Bridgeport (1905–09, edition of December 1911). R. B. Marshall drew the topography on the first three and signs the fourth as chief geographer; H. E. C. Feusier ran the triangulation for all three of the early ones. Contour interval 100 feet throughout. The Yosemite sheet carries a confession in its bottom margin — “The elevations on this map were later found to be 85 feet too high” — and the park's changing shape is written across the set: the 1898 Dardanelles sheet still rules YOSEMITE NATIONAL PARK BOUNDARY LINE straight east–west across itself, while the 1909 Yosemite sheet, printed after the 1905 reduction, letters STANISLAUS and SIERRA NATIONAL FOREST over the western and southern ground the park had lost. Matthes' 1930 plate draws a third line again, in green, and it agrees with neither.

Three layers

The slider passes from modern relief through Matthes' 1930 topographic map of Yosemite National Park — USGS Professional Paper 160, plate 2, “from Geological Survey maps surveyed between 1893 and 1909, roads and trails added 1928 by National Park Service” — to the quadrangles themselves. The plate is drawn on the block's exact sheet lines, so it covers the drape corner to corner, title block and all; the engraver set that cartouche inside the neat line over the Bodie Hills and it is left where he put it. Matthes' collar admits its projection sits 690 feet south and 300 feet west of the North American datum; the registration absorbs that automatically. Fitted by correlation on shared engraved ink against all four quads at once — 265 control points, 4.8 px RMS at the plate's 10.5 m/px, about 50 m on the ground. Same survey, same engraving house, so the disagreement is thin: reduction, revision and a 1930 press.

The falls as data

The Summits & falls layer plots 39 named falls and cascades from the U.S. Board on Geographic Names, from Yosemite Falls and Bridalveil to Waterwheel and Le Conte in the Grand Canyon of the Tuolumne, and Wapama and Tueeulala on the wall of Hetch Hetchy — the two that now drop into a reservoir. They sit where the granite breaks; turn the sun low and the cliffs that make them come out.

The terrain

Elevations are open Terrarium tiles at zoom 12 on a local conic grid — about 32 m per drape texel over the 103 × 99 km block, from the Merced canyon at 1,069 ft on the western edge to Mount Ritter at 13,051 ft in the model. The modern terrain holds Hetch Hetchy Reservoir and Lake Eleanor behind their dams; the 1898–1911 sheets show meadow, river and a shallow natural lake, and the mismatch is left in plain sight — it is the whole point of this sheet.

Reading it

Block: 37°30′–38°15′ N × 119°–120° W · 103 × 99 km · 49 m per height sample

Relief: 326 m (the Merced at the west edge) to 3,978 m (Mount Ritter)

Georeference: quads self-georeferenced · 1930 plate vs quads · 4.8 px ≈ 50 m · 265 points

Contours: the sheets' 100 ft — key C

Sources

Quadrangles from the USGS Historical Topographic Map Collection (https://ngmdb.usgs.gov/topoview/) (scans 299699, 299480, 299315, 299235); the park map from Professional Paper 160 (https://pubs.usgs.gov/pp/0160/), plate 2 (Matthes, 1930); names, summit elevations and the falls from GNIS (https://www.usgs.gov/us-board-on-geographic-names) (the frozen 2021 archive of the domestic names file, which still carries elevations). All U.S. government works, public domain. Elevation tiles are open data (https://registry.opendata.aws/terrain-tiles/). This block is the homeland of the Ahwahneechee and the Southern Sierra Miwok on the west slope and the Kutzadika'a Paiute at Mono Lake, who traded across these passes for as long as anyone can measure; in March 1851 the state-funded Mariposa Battalion rode into Yosemite Valley, burned the villages and the acorn stores, and drove Chief Tenaya's people to the Fresno River reservation — the Valley flight says so where it happened.

## The Silverton Folio

Source: `silverton/src/body.html`

The silver quadrangle

The Economic Geology sheet of the Silverton folio (Geologic Atlas of the United States, Folio 120, 1905) — every named lode, tunnel and mill of the San Juan silver country, drawn in red over the engraved topography — draped over modern terrain, with the folio's Areal Geology sheet, the caldera volcanics in colour, one slider-stop behind.

The folio

The Survey came to the San Juans a generation behind the miners. Prospectors struck the Little Giant lode in Arrastra Gulch in 1870, while the land was still Ute by treaty; the Brunot Agreement took the mountains in 1873, and by the time Whitman Cross, Ernest Howe and Frederick Ransome worked the quadrangle at the turn of the century, Silverton was thirty years into its boom. Ransome tramped the workings for Bulletin 182 (1901); Cross and Howe, with A. C. Spencer, read the volcanic stack; Folio 120 printed both sheets in 1905 on the Survey's 1901 topographic base — the areal sheet colouring the San Juan tuff and the Silverton and Potosi volcanic series, the economic sheet lacing the same country with red vein lines. No one yet knew the quadrangle sat in a caldera; that reading came with Burbank's ring-fault zone in 1933 and Lipman's remapping in the 1970s, and the folio is the honest record of what could be known before it.

Three layers

The slider passes from modern relief through the areal geology to the economic geology. Both folio plates are registered by correlation on shared engraved linework against the USGS's georeferenced scan of the 1901 base quadrangle — the base is a registration target only, and the folio sheets are the layers. The lithographs disagree with the engraving at sub-kilometre scale, so each plate is fitted down a pyramid of ever-smaller patches; the residuals settle near 4 px ≈ 20 m on the ground (the exact numbers are printed below), tight enough that the red veins hang on the ridges that carry their mines.

The mines as data

The Summits & mines layer plots about eighty named mines from the U.S. Board on Geographic Names (GNIS) — the live gazetteer dropped man-made features in 2021, so these come from its frozen 2021 archive — famous producers first: the Sunnyside above Eureka, the Gold King above Gladstone, Stoiber's Silver Lake in Arrastra Gulch, the Shenandoah and the Dives in Cunningham. Four hundred and six named workings fall inside this one quarter-degree; the thinning keeps the gulches readable.

The terrain

Elevations are open Terrarium tiles at zoom 12 on a local conic grid — about 15 m per drape texel over the 37 × 43 km block, from the Animas canyon at 8,344 ft where the river leaves the sheet to Handies Peak at 14,048, the one fourteener inside the neat. Silverton itself sits at 9,308 ft in Bakers Park, and everything the folio cares about happens in the two vertical miles between town and the summits.

Reading it

Grid: 37 × 43 km · 22 m per height sample

Relief: 2,543 m (Animas at the south edge) to 4,271 m (Handies Peak)

Georeference: two plates vs the 1901 base · correlation · 4.1–4.2 px ≈ 20 m · 899 points

Contours: the sheets' 100 ft — key C

Sources

USGS Geologic Atlas, Folio 120 (https://pubs.usgs.gov/publication/gf120) (Cross, Howe & Ransome, 1905); base quadrangle from the Historical Topographic Map Collection (https://ngmdb.usgs.gov/topoview/) (scan 234428, edition of 1901); names and mines from GNIS (https://www.usgs.gov/us-board-on-geographic-names) and its 2021 archive. All U.S. government works, public domain. Elevation tiles are open data (https://registry.opendata.aws/terrain-tiles/). These mountains are Nuchu — Ute — homeland, taken by the 1873 Brunot Agreement within living memory of everyone named on this sheet; the High and Deep flight says so plainly.

## The Park Special

Source: `estes/src/body.html`

One survey, printed twice

The one classic USGS park special that survives complete and georeferenced: Topographic Map of Rocky Mountain National Park, Colorado, 1:125,000, surveyed 1912–15 — with the Longs Peak quadrangle of the same survey, engraved February 1915, one slider-stop behind it. One field party, one half degree of the Front Range, and thirty-six years of history printed in between.

The two sheets

Both cover exactly the same block: 40°00′–40°30′ north by 105°30′–106°00′ west, the graticule box printed on each. Both credit R. B. Marshall as chief geographer, Sledge Tatum as geographer in charge, and the topography to B. A. Jenkins and C. A. Ecklund — with Cornelius Schurr added on the park sheet. The quadrangle says Surveyed in 1912–1913, carries a 50-foot contour interval, and is the edition of May 1915. The park sheet says Surveyed in 1912–1915, generalises to 100 feet, and is the edition of 1915 reprinted in 1951 — with a line in its margin admitting that roads and trails were added 1940 by National Park Service. Every red road and dashed trail on the drape is that 1940 addition; the red hatched ribbon is the park limit, already swollen west by the Never Summer extension of 1930. The park sheet's map body runs north past the shared neat to about 40°33′, over Comanche Peak and Mummy Pass, but this block is cut to the thirty-minute graticule both sheets print, so the crossfade holds edge to edge.

Three layers

The slider passes from modern relief through the 1915 Longs Peak quadrangle to the park sheet. Nothing here was fitted and no control point was picked. Both files are Historical Topographic Map Collection GeoTIFFs carrying their own polyconic transform on NAD27, and each layer is resampled straight through its own geokeys. To check that the two transforms agree, 169 patches of the park sheet's engraving were correlated into the Longs Peak scan at the positions the Longs Peak geokeys predict on their own: the two land 3.3 px apart at the median, 3.4 px RMS, on scans of 10.58 m per pixel — about 34 m on the ground, roughly a pen width at this scale. That number was measured, not applied; neither sheet was moved.

What the thirty-six years did

Pull the slider between the two printings and the changes are the history of the place. The park boundary is a thin line in 1915 and a hatched red band on the park sheet, swollen west across the Never Summer Mountains by the addition of 1930. Fall River Road does not exist on the quadrangle — the wagon road ends at Horseshoe Falls and goes on as a dashed trail — and on the park sheet it switchbacks to Fall River Pass with Trail Ridge Road beside it. At Grand Lake, one lake becomes three: Shadow Mountain Lake and Granby Reservoir are stencilled straight over the 1915 survey, so Soda Creek still meanders across the middle of Lake Granby and Stillwater still stands in it. Even a name moves — the glacier under Hagues Peak is lettered Hallett Glacier in 1915 and Rowe Glacier on the park sheet.

Summits, and no mine layer

This sheet ships without a data layer, and the reason is worth stating. The frozen 2021 GNIS archive — the last edition that still carries the Mine feature class — puts 65 mine and tunnel records inside this neat, but 28 of them share one identical coordinate at Ward, in the block's far south-east corner: the Boulder County tungsten camps, off the park and off this sheet's story. The Colorado headwaters, where the mining that matters here happened, hold none at all: Lulu City is a Locale, not a mine. A layer that stacks twenty-eight glyphs on one point would be worse than no layer, so the Summits chip carries the nineteen peaks alone — each one checked against the model within 25 m of its printed feet.

The terrain

Elevations are open Terrarium tiles at zoom 12 on a local conic grid — about 23 m per drape texel over the 58 × 71 km grid, of which the printed block is 42 × 56 km. On the sheet itself the ground runs from 2,277 m, where the Big Thompson leaves the block at 105°30′ below Estes Park, to 4,342 m on Longs Peak; the grid keeps going down to 2,035 m out in the St. Vrain foothills beyond the neat. That summit is worth a moment: the bench mark engraved on the sheet reads 14,255 feet, GNIS now carries 14,262, and the elevation model gives 14,245. Three answers to one question, a century apart, and none of them wrong by much.

Reading it

Grid: 58 × 71 km · 34 m per height sample

Relief: on the sheet, 2,277 m (Big Thompson at the east neat) to 4,342 m (Longs Peak); the grid floor is 2,035 m beyond it

Georeference: both sheets self-georeferenced · nothing fitted · they agree to 3.3 px ≈ 34 m over 169 points

Contours: the park sheet's 100 ft — the quadrangle's are 50 ft — key C

Sources

Both sheets from the USGS Historical Topographic Map Collection (https://ngmdb.usgs.gov/topoview/) — Rocky Mountain National Park 1:125,000, scan 234287 (edition of 1915, reprinted 1951) and Longs Peak 1:125,000, scan 402456 (edition of May 1915); names, coordinates and elevations from GNIS (https://www.usgs.gov/us-board-on-geographic-names), with the frozen 2021 archive file used for the summit elevations, and every figure re-checked against that file at build time. All U.S. government works, public domain. Elevation tiles are open data (https://registry.opendata.aws/terrain-tiles/). This half degree is Núuchi-u (Ute) and Hinono'eino' (Arapaho) homeland: the Ute Trail lettered across Trail Ridge on both sheets is theirs, and the Arapaho names now official on it — Kawuneeche, Ni-chebe-chii — were written down in July 1914 from Gun Griswold and Sherman Sage, brought back from the Wind River Reservation because they had been removed from this country in 1878. The Ute and Arapaho Country flight says it at length.

## Kīlauea and Mauna Loa

Source: `kilauea/src/body.html`

The observatory decade

Four engraved fifteen-minute quadrangles of the island of Hawaiʻi tiled into one half-degree block — MAUNA LOA (1928), KILAUEA (1921), HONUAPO (1924) and PAHALA (1923), all 1:62,500 with a fifty-foot contour interval — draped from the Kaʻū surf to Mokuʻāweoweo at 13,665 feet, with Harold Stearns' 1930 geologic map of the Kaʻū district one slider-stop behind. This is Kanaka ʻŌiwi land in the moku of Kaʻū and Puna, and the caldera on the east edge is Kaluapele, the home of Pelehonuamea.

The sheets

These are the Territory-era topography of Hawaiʻi: surveyed between 1912 and 1922 by the Geological Survey with the Territory of Hawaii — the Mauna Loa sheet's collar credits the Commissioner of Public Lands — and drawn at fifty-foot contours from the surf to thirteen thousand six hundred feet. HAWAII NATIONAL PARK is lettered in open capitals across Mauna Loa's summit and again around Kīlauea: the two pieces Congress protected on 1 August 1916, three weeks before the National Park Service itself existed. (Haleakalā on Maui was the third piece, and stayed in the same park until 1961.) Everything else on the block is Kaʻū — the ahupuaʻa lettered mountain-to-sea, the Hawaiian Agricultural Company's cane land and its railroad down to Punaluʻu, the landings at Punaluʻu and Honuʻapo, the ʻĀinapō trail with its waterholes, and, on the caldera rim, a Volcano House, a Park Hotel, a Summer Camp, a Prison Camp and a Museum. Look out to sea off the Kaʻū coast and you will find, twice, a pair of small ruled boxes captioned Boundary of lava flow and Cracks: the Honuapo and Pahala engravers put the sheets' own symbol key inside the neatline, in the only empty water they had. It is left where they put it.

Three layers

The slider passes from modern relief through Harold T. Stearns' geologic map of the Kaʻū district — Water-Supply Paper 616, Plate 1: geology 1924, published 1930, 43 inches of paper at the same 1:62,500 — to the quadrangles themselves. Stearns drew on these very sheets, and his margin says so: "Base from U. S. Geological Survey maps of Puna, Kilauea, Mauna Loa, Pahala, Honuapo, and Kalae quadrangles, surveyed in 1912–1922." Same lineage, so the fit is tight. Rasterised at 300 dpi the plate lands on the quads' own 5.29 m per pixel, and 573 automatically matched control points fit to 3.5 px RMS — about 19 m on the ground (median 3.0 px, worst 6.7). Nothing was picked by hand: the plate's position was seeded from the projection it shares with the quads, then correlated on a local high-pass ink mask. Slide between the two over the caldera and the benchmarks, the Stone Corral and the word Halemaumau stay put while the colour arrives.

Two-thirds of the block carries Stearns' colour; the rest goes to bare paper, honestly. He mapped the Kaʻū district and stopped, so Mauna Loa above roughly 8,000 feet is white on his plate — Mokuʻāweoweo is on the quadrangle only — and the two panels he printed inside his own neatline, the EXPLANATION and four cross-sections drawn out in the Pacific, are masked out rather than draped onto ground they do not describe.

The flows as data

The ≈ layer plots every named lava flow and kīpuka the U.S. Board on Geographic Names carries inside the block — 52 of them, fifteen named for the year they ran: 1823, 1851, 1868, 1880, 1887, 1907, 1916, 1919, 1920, 1921, 1926, 1949, 1950, 1959, 1974. Four of those are younger than every sheet here, which is rather the point: on this block the ground is regularly newer than its cartography. Maunaiki, 3,018 feet in the Kaʻū Desert, did not exist when the century began — and the 1921 sheet is new enough to draw it. The rest of the layer is kīpuka: islands of older ground that the flows went round, still forested, and named.

Which datum?

The Historical Topographic Map Collection stages every Hawaii sheet with a NAD27 datum key, and it is wrong. The graticule printed on these quadrangles is the Old Hawaiian Datum, and on this island the two are 575 m apart — a third of a mile, twenty-seven drape texels. This build uses the island-of-Hawaiʻi three-parameter shift instead, and does not ask to be taken on faith: the pipeline's datum stage draws the model's own shoreline over the 1924 Honuapo sheet under each candidate and keeps the three panels side by side. Under the Old Hawaiian shift the line lies along the printed surf at Honuʻapo, Hanakaula and Papine; under NAD27 it lies a quarter of a mile out in the blue.

The terrain

Elevations are open Terrarium tiles at zoom 13 on a local conic grid — about 21 m per drape texel and 32 m per height sample across the 60 × 63 km grid, from a flat Pacific to 4,165 m at Mokuʻāweoweo (13,665 feet, which is exactly the figure GNIS gives for Mauna Loa). A quarter of the block is ocean. The tiles carry bathymetry there and none of it is drawn: the sea is held dead flat at zero, because a sea floor that drops thousands of metres within a few miles of the beach would swallow the whole hypsometric ramp. The caldera sits hard against the east neatline — Kīlauea Iki's centre is three metres inside it, and the Chain of Craters below Puhimau is off the sheet.

Reading it

Grid: 60 × 63 km · 32 m per height sample

Relief: 0 m (the Pacific) to 4,165 m (Mauna Loa)

Georeference: four sheets self-georeferenced, Old Hawaiian datum · Stearns 1930 vs the sheets · 3.5 px ≈ 19 m, 573 points

Contours: the sheets' 50 ft — key C

Sources

Quadrangles from the USGS Historical Topographic Map Collection (https://ngmdb.usgs.gov/topoview/) (scans 349891, 349872, 349835, 349895); the geology from Water-Supply Paper 616 (https://pubs.usgs.gov/wsp/0616/), Plate 1 (Stearns, 1930); names from GNIS (https://www.usgs.gov/us-board-on-geographic-names) — the current file for the names, because it carries the ʻokina and kahakō, and the 2021 archive for the summit feet, which the live product no longer publishes. All U.S. government works, public domain. Elevation tiles are open data (https://registry.opendata.aws/terrain-tiles/).

This block is Kanaka ʻŌiwi land in the moku of Kaʻū and Puna. Kīlauea is Kaluapele; hoʻokupu are still carried to the rim of Halemaʻumaʻu, which is a temple and not a viewpoint. The park was made in 1916 out of ahupuaʻa land — Keauhou and Kapāpala among them — part of it Crown and Government land of the Kingdom of Hawaiʻi that passed to the United States at the 1898 annexation, five years after the Kingdom was overthrown, and part of it bought from the Bishop Estate. The Kaʻū Desert flight says plainly what the ash bed at the Footprints records of 1790; the Kaʻū sugar flight ends on Wailau, one of two Hawaiian Home Lands tracts on this block set aside under the Act of 1921 — the same year the Kilauea sheet was surveyed.

## The Coeur d’Alene

Source: `coeurdalene/src/body.html`

The lodes of the Coeur d'Alene

Ransome and Calkins' geologic map of the Coeur d'Alene mining district (USGS Professional Paper 62, Plate II, 1908) — the great silver-lead lodes of the South Fork and Canyon Creek drawn across the Belt rocks that carry them — draped over the district's terrain with the 1906 special base it was engraved on one slider-stop behind.

The sheet

Gold placers on Prichard Creek brought the rush of 1883–84; the galena of Canyon Creek and the Bunker Hill discovery of 1885 made the district, and the dynamitings of 1892 and 1899 made it notorious. The Survey answered with its full apparatus: R. U. Goode's topographers (C. F. Urquhart on triangulation, Van H. Manning on topography) drew this 30′ × 15′ special sheet in 1900–01 at 1:62,500 with 50-foot contours, and F. L. Ransome and F. C. Calkins worked the geology over it in 1903–04. Professional Paper 62 (1908) is the district's founding document — the Prichard, Burke, Revett, St. Regis, Wallace and Striped Peak formations it named are the working language of the Belt Supergroup still, and its reading of the lodes along the Osburn fault system guided a century of mining that made this the largest silver district in the United States.

Three layers

The slider passes from modern relief through the 1906 edition of the special base (USGS Historical Topographic Map Collection, already georeferenced) to the 1908 geology printed on that very engraving. The plate is seeded from its printed neat corners and registered to the base by correlation on shared linework — 3.1 px RMS at the plate's 3.5 m/px, about 11 m on the ground: one engraving family in near-perfect agreement.

The mines as data

The Summits & mines layer plots some fifty named workings from the U.S. Board on Geographic Names — famous lodes first: Bunker Hill, Sunshine, Morning, Hecla, Tiger-Poorman, Hercules, Standard Mammoth, Granite — over the geology that explains their alignment along the Osburn fault. (GNIS retired its Mine records in 2021; these come from the archived file, coordinates unchanged.)

The terrain

Elevations are open Terrarium tiles at zoom 12 on a local conic grid — about 21 m per drape texel over the 53 × 43 km block, from the South Fork below Kellogg near 2,160 ft to Stevens Peak at 6,827. The relief is all dissection: no summit flat, no valley wide, which is why the towns, the mills and the railroads all stand in the same few feet of creek bottom.

Reading it

Grid: 53 × 43 km · 31 m per height sample

Relief: 657 m (South Fork Coeur d'Alene River) to 2,076 m (Stevens Peak)

Georeference: plate vs 1906 base · correlation · 3.1 px ≈ 11 m

Contours: the sheet's 50 ft — key C

Sources

USGS Professional Paper 62 (https://pubs.usgs.gov/publication/pp62), Plate II (Ransome & Calkins, 1908); base sheet from the Historical Topographic Map Collection (https://ngmdb.usgs.gov/topoview/) (scan 238988, edition of 1906); names and mines from GNIS (https://www.usgs.gov/us-board-on-geographic-names). All U.S. government works, public domain. Elevation tiles are open data (https://registry.opendata.aws/terrain-tiles/). This district is the homeland of the Schitsu'umsh — the Coeur d'Alene people — whose reservation was cut away to the southwest by the agreements of 1887–89, five years before the first location notice on Canyon Creek was a decade old; the Labor Wars and 1910 flights tell the district's other hard histories plainly.

## Pemetic: the Island Before Acadia

Source: `mountdesert/src/body.html`

The island when the park was called Lafayette

Two 15-minute quadrangles — BAR HARBOR and MOUNT DESERT, surveyed 1902–03 and published in 1904 — joined at 68°15′ into one island, in the state their plates were reprinted in during the 1920s: LAFAYETTE NATIONAL PARK lettered across the mountains, and every summit wearing the new name it was given in 1918. One slider-stop behind lies the 1942 edition of the same two cells: a wholly new survey, drawn under a War Department imprint, with the park renamed Acadia.

The sheets

Both cells were mapped by the U.S. Coast and Geodetic Survey with W. H. Lovell, in cooperation with the State of Maine, under H. M. Wilson as geographer in charge — Bar Harbor surveyed in 1902 and printed April 1904, Mount Desert printed May 1904. Then the plates were reissued, and each reissue is a snapshot of what the island was called that year. The Bar Harbor sheet here is the 1920 reprint; the Mount Desert sheet is the 1928 reprint, its Survey file stamp dated SEP 6 – 1928. Both carry a park that did not exist when the topography was drawn: Woodrow Wilson proclaimed Sieur de Monts National Monument on 8 July 1916, Congress made it Lafayette National Park on 26 February 1919 — the first national park east of the Mississippi — and on 19 January 1929 it became Acadia. Earlier printings of these same plates carry the monument boundary in red, and the earliest carry no park at all and the old names: Green, Dry and Newport Mountain, Robinson, Browns, Jordan and Dog.

Three layers

The slider passes from modern relief through the 1942 editions — surveyed 1934-35 and 1939-40 by A. J. Ogle's parties, printed with ACADIA NATIONAL PARK hatched in red, Schoodic Peninsula inside it, the motor road up Cadillac and Rockefeller's carriage roads drawn for the first time — to the 1904 plates. All four scans are HTMC GeoTIFFs carrying their own polyconic georeference, so nothing here is fitted: every layer drapes by passthrough, and the two cells of each edition meet at their own neat lines, tone-matched at the paper white (no channel had to move by more than 2.1%).

What was measured instead is how far apart the two surveys actually are. The 1904 ink was correlated against the 1942 ink on a lattice over the island — 131 matched patches — and compared against each sheet's own georeference: 6.2 px on Mount Desert and 8.5 px on Bar Harbor, about 33 and 45 m on the ground, median 25–27 m, with a plain shift and rotation accounting for most of it (24–26 m residual after a degree-1 fit). That is the honest distance between a 1902 reconnaissance on the old North American datum and a 1930s plane-table survey on NAD 1927, and it is left in the sheet rather than fitted away. Watch it on the shoreline when you cross the slider.

The archipelago

The data layer under the anchor glyph is the islands: 69 of them, from Bartlett and Ironbound down to Junk of Pork and Old Soaker, keyed by GNIS feature_id because four separate islands inside this one block are called Bar Island. On a sheet that is a third open water, they are the structure. Baker Island and the Bass Harbor Head light fall a kilometre and more below the 44°15′ neat line, and are simply not on the paper.

The terrain

Elevations are open Terrarium tiles at zoom 12 on a local conic grid — about 12 m per drape texel over the 47 × 35 km block. The Gulf of Maine's real bathymetry is carried through the mosaic and then flattened at zero, so the sea in the model is exactly flat and every depth curve you can see belongs to the 1942 sheet, not to the terrain. Land runs from that sea surface to 464 m on Cadillac Mountain, which the 1942 plate marks 1,530 feet — the model reads 1,521. Nineteen summits are labelled, each with the elevation printed beside its triangulation mark on the 1942 sheet; every one was checked against the model and none is more than 25 m out.

Reading it

Grid: 47 × 35 km · 23 m per height sample

Relief: sea level to 464 m (Cadillac Mountain, printed 1,530 ft)

Georeference: all four scans self-georeferenced · 1904 vs 1942 measured at 131 points · 6.2–8.5 px ≈ 33–45 m

Contours: the sheets' 20 ft — key C

Sources

All four quadrangle scans from the USGS Historical Topographic Map Collection (https://ngmdb.usgs.gov/topoview/) — Bar Harbor 807360 (1904, reprinted 1920) and Mount Desert 807575 (1904, reprinted 1928); Bar Harbor 460150 and Mount Desert 460635 (edition of 1942). Names and island coordinates from GNIS (https://www.usgs.gov/us-board-on-geographic-names). All U.S. government works, public domain. Elevation tiles are open data (https://registry.opendata.aws/terrain-tiles/). The Bar Harbor sheet is a Survey file copy and looks it: a rubber stamp reading FILE COPY — MAPS & DRAFTING sits out in the Atlantic in the southeast corner, and the symbol table printed on the back of the paper shows faintly through the ocean. Both are left where they are.

This island is Pemetic, the sloping land — Wabanaki homeland, the country of the Penobscot and Passamaquoddy with their Maliseet and Mi'kmaq relations, lived in for some five thousand years by the record of the shell heaps along these shores. Champlain struck a ledge off the east side on 5 September 1604 and wrote down another name. Through the whole resort era drawn on the 1904 sheets, Penobscot and Passamaquoddy families camped each summer on the Bar Harbor waterfront selling ash baskets and canoes, and were moved on and finally moved off; no edition of this quadrangle marks the encampment. Maine took Wabanaki land without a ratified federal treaty, and the claims over that failure ran until the Maine Indian Claims Settlement Act of 1980. The Pemetic flight says so on the ground it happened.

## Mazama: Crater Lake in Professional Paper 3

Source: `mazama/src/body.html`

The pit where a mountain stood

Mark B. Kerr's plane-table survey of 1886, printed as Plate I of Professional Paper 3 and cut to the four lines Congress had just made the boundary of Crater Lake National Park — draped on modern elevations, with J. S. Diller's coloured geology one slider-stop behind and the soundings of the boat Cleetwood floating over the water they were taken from. This is giiwas, Klamath homeland.

The plates

Professional Paper 3, The Geology and Petrography of Crater Lake National Park (Joseph Silas Diller and Horace Bushnell Patton, 1902), carries both layers. Plate I is Kerr's topography — Henry Gannett chief geographer, A. H. Thompson geographer in charge, "Surveyed in 1886" — everything red on it is Diller's: the numbers where he collected the specimens the paper describes, and the single letters that class the rock (A hypersthene-andesite, B basalt, D dacite, D′ tuffaceous dacite, G glacial moraine and dacite tuff). It also carries a dashed "possible pack-train route, but no trail" around the rim, with his camps numbered along it. Plate VI paints those same five classes on the identical base — pink andesite for the body of the old cone and the ridges radiating off it, pale yellow dacite along the north rim at Llao Rock, orange tuffaceous dacite at Round Top and the Wineglass, blue-grey basalt for the outlying cones (Timber Crater, Bald Crater, Desert Cone, Crater Peak), olive moraine and dacite tuff over the low ground north and west — and adds little arrows for the glacial striae. Both were rasterised at 300 dpi straight out of the report's own scan; both were lithographed by Julius Bien & Co. of New York.

Diller says how Plate I was assembled, and it shows at the edges: the country between 122°00′ and 122°15′ and between 42°50′ and 43°04′ came from the Crater Lake special sheet at an inch to the mile, while the strips outside it — one minute of longitude along the west, two minutes of latitude along the south — were reduced from the Ashland sheet at an inch to four miles. The west and south margins of this drape are softer than the rest because they were drawn from farther off.

Three layers

There is no early georeferenced base for this country. The oldest Crater Lake quadrangles the USGS has staged are 1985, and they are Lambert conformal rather than the polyconic this pipeline reads, so there is nothing whatever to correlate a 1902 plate against. Both plates were therefore fitted from their own printed graticule, the way the Nome sheet was: the 25 crossings of the five-minute net on each were located by ruler-grid crops and a darkness-centroid profile, and a degree-2 polynomial in the sheet's own conic plane carried them to the earth. Plate I lands on its net at 1.11 px RMS (worst 2.20), Plate VI at 1.02 px (worst 1.53) — about 12 metres at the plates' 11.9 m per pixel. A degree-1 fit leaves Plate I at 3.06 px, because that sheet's paper carries a keystone of roughly 0.7 per cent; the second-degree term is exactly that much paper.

Paper is not ground, so the lake was made to answer for the survey. Lifted off this drape and off the 1985 Crater Lake West and Crater Lake East quadrangles, the two shorelines agree to a median 171 m, nine tenths of Kerr's outline within 363 m, his water 55.2 km² against the modern 54.7; the best rigid shift that would improve the overlap is 268 m. That number — old datum, plane table and a century of paper together — is what an 1886 triangulation taken at face value is worth here. His heights ran high the same way: the plate letters "Lake surface 6239 feet above sea level" where the model reads a dead-flat 6,175.

The soundings

The data layer is the lake floor. In 1886 the survey party hauled the boat Cleetwood to the rim and lowered her down the inside wall, and "to determine the configuration of the bottom of Crater Lake a large number (168) of soundings were made under the direction of Major Dutton" — lead and wire, cast after cast. Plate I prints 56 of those depths inside the shoreline, and all 56 are here, read once off the 300-dpi scan and carried to the ground by the inverse of the plate's own graticule fit. The deepest reads 1,996 feet; Dutton added "a small but unknown correction for the stretching of the wire, which will make the true depth of this cast fully 2,000 feet," and called it the deepest fresh water in the United States. Modern sonar puts the floor about fifty feet shallower than his figure. The terrain under the labels is flat because the elevation model is a surface model: it stops at the water, and these numbers are the only depth on the sheet.

The terrain

Elevations are open Terrarium tiles on a local conic grid — zoom 13 rather than the gallery's usual 12, because this is the smallest block in the collection and at zoom 12 a post is 28 m here, enough to round the Devils Backbone and Llao Rock off the rim. That gives about 11 m per drape texel over a 28 × 36 km grid. The park itself measures 21.7 × 29.6 km — 249 square miles, exactly the figure in the act.

Reading it

Grid: 28.1 × 36.0 km · 11.0 m per drape texel · 16.5 m per height sample

Relief: 1,177 m at the south-west corner to 2,715 m on Mount Scott; the lake surface sits at 1,882 m

Georeference: printed 5′ graticule, 25 crossings per plate, degree 2 · Pl. I 1.11 px, Pl. VI 1.02 px ≈ 12 m · shoreline vs the 1985 quads: median 171 m

Contours: the plate's 100 ft, index every 500 — key C

Data layer: 56 printed soundings, in feet below the 1886 lake surface — key toggles with the summits

Sources

Both plates from USGS Professional Paper 3 (https://pubs.usgs.gov/pp/0003/report.pdf) (1902), pages 18 and 38 of the scan; the modern quadrangles used only as a check are Crater Lake West (scan 279504) and Crater Lake East (279501), 1985, from the USGS Historical Topographic Map Collection (https://ngmdb.usgs.gov/topoview/); names and coordinates from GNIS (https://www.usgs.gov/tools/geographic-names-information-system-gnis); elevation tiles are open data (https://registry.opendata.aws/terrain-tiles/). All U.S. government works, public domain. The place this sheet draws is giiwas — Klamath homeland, and a place of power in Klamath tradition, which holds the mountain's destruction as a battle between Llao of the below world and Skell of the above. By the Treaty of Council Grove of 14 October 1864 the Klamath, Modoc and Yahooskin ceded some twenty million acres, this mountain among them; Fort Klamath, from which this map's only wagon road climbs, is where four Modoc leaders were hanged in October 1873. The Klamath Tribes were terminated by Congress in 1954 and restored in 1986. The rim's Klamath names were put on the map by others, in the 1880s and '90s, out of stories that were not theirs to take — Llao Rock is the one already lettered on this 1886 sheet, and the giiwas flight says so plainly.

## He Sapa in Folio

Source: `blackhills/src/body.html`

The southern hills, in colour

N. H. Darton and Sidney Paige's Central Black Hills folio (Geologic Atlas of the United States, Folio 219, 1925) — pink Harney Peak granite in the middle, grey Pahasapa limestone around it, the red ring of the Spearfish shale outside that — draped over the country it maps, with the 1901 engraved topography of the HARNEY PEAK and HERMOSA quadrangles one slider-stop behind. Wind Cave National Park is at the bottom of the sheet. Mount Rushmore is an uncarved granite ridge at the top.

The folio

Folio 219 covers a full degree — 43°30′ to 44°30′, 103° to 104° — over the Deadwood, Rapid, Harney Peak and Hermosa quadrangles, "thus embracing about 3,441 square miles." This sheet is its southern half, the two quadrangles that hold the granite core, the cave and the whole southern mining district. The areal plate is the Edition of Nov. 1921 and still names Albert B. Fall as Secretary of the Interior; by the time the folio was bound and issued in 1925 the cover read Hubert Work. Under the map: "Topography from U.S. Geological Survey maps of Deadwood, Harney Peak, Hermosa, and Rapid quadrangles. Surveyed in 1891-1899. Partially revised in 1913-1915." The geology of the Cambrian and later rocks is chiefly Darton's, the pre-Cambrian is Paige's, surveyed 1900–1915; contour interval 100 feet; engraved and printed by the Survey itself.

Three layers

The slider passes from modern relief through the 1901 quadrangles — Harney Peak, edition of June 1901, surveyed 1897–98; Hermosa, edition of March 1901 reprinted June 1913, surveyed 1898–99; both under E. M. Douglas with topography by A. F. Dunnington — to the 1925 geology. Each quad carries its own polyconic georeference and drapes straight from it; the two printings are tone-matched at their paper whites and meet at their neatlines on 103°30′. The folio plate is rasterised at 300 dpi (10.5 m per pixel, the scale the quads were scanned at), seeded from two of its own printed neat corners, then registered by correlation against both quads at once on a local high-pass ink mask. The folio's topography is literally these sheets, so the fit is folio-tight: 220 control points, none trimmed, 1.48 px RMS — about 16 m on the ground, worst residual 3.3 px.

The mines as data

The Summits & mines layer plots 69 named mines and quarries from the U.S. Board on Geographic Names — the frozen 2021 gazetteer, because the live product retired the Mine feature class that year. They trace one thing: the Harney Peak pegmatite field, gold at Keystone at its top and industrial minerals everywhere under it. Darton and Paige printed their own ledger in the plate's corner: "tin and mica in pegmatitic dikes and veins; spodumene and amblygonite (lithia rock) in pegmatitic dikes… limestone for lime, flux, and cement manufacture in Minnekahta, Whitewood, Pahasapa, Englewood, and Niobrara limestones." Wind Cave itself has no point in the gazetteer at all — GNIS names the park, the canyon and every ranch around it, but not the hole; its label here was read off the cave symbol printed on the 1901 Hermosa sheet.

The terrain

Elevations are open Terrarium tiles at zoom 12 on a local conic grid — about 37 m per drape texel over the 96 × 71 km grid, from 816 m (2,676 ft) out on the plains east of the hogback to 2,191 m (7,188 ft) on the crest. The model reads Black Elk Peak at 7,171 ft against its surveyed 7,247: a 30-metre elevation grid rounds a sharp granite summit off, and the broad limestone top of Odakota Mountain — grey on the folio where Black Elk is pink — comes out highest instead. Nothing in this terrain shows the reason the park at the bottom of the sheet exists: the cave is more than 150 miles of mapped passage under a surface that reads as grass.

Reading it

Grid: 96 × 71 km · 56 m per height sample

Relief: 816 m (plains, east edge) to 2,191 m (Odakota Mountain)

Georeference: quads self-georeferenced · folio plate vs both quads · 1.48 px ≈ 16 m, 220 points

Contours: the sheets' 100 ft — key C

Sources

USGS Geologic Atlas, Folio 219 (https://pubs.usgs.gov/publication/gf219) (Darton & Paige, 1925; plates and text (https://pubs.usgs.gov/gf/219/)); base quadrangles from the Historical Topographic Map Collection (https://ngmdb.usgs.gov/topoview/) (scans 344786 and 344793, editions of 1901); names and mines from GNIS (https://www.usgs.gov/us-board-on-geographic-names) and its 2021 archive. All U.S. government works, public domain. Elevation tiles are open data (https://registry.opendata.aws/terrain-tiles/). This is He Sapa, the Black Hills — Lakota land, and Cheyenne, Arapaho, Kiowa and Crow country before and beside them. The 1868 Fort Laramie treaty set these hills apart for the Lakota's "absolute and undisturbed use and occupation"; Custer's expedition found gold on French Creek in 1874, and an act of Congress took the hills on 28 February 1877. In United States v. Sioux Nation of Indians (1980) the Supreme Court held that taking unlawful and awarded compensation; it has never been accepted, because the claim was never for money. Darton borrowed the same name for his limestone: Pahasapa.

## The Smokies in Folio

Source: `smoky/src/body.html`

The sheet before the park

Arthur Keith's geologic folio of the Knoxville quadrangle (Geologic Atlas of the United States, Folio 16, edition of January 1895) — the folded reds of the Great Valley of East Tennessee, and the single grey mass of the Great Smoky Mountains lying on top of them — draped over modern elevations, with the folio's own engraved topography sheet one slider-stop behind. Thirty-nine years before there was a park.

The folio

The Knoxville sheet runs between the parallels 36° and 35°30′ and the meridians 84° and 83°30′ and holds, in Keith's count, a thousand square miles of Knox, Sevier and Blount counties in Tennessee and Swain County in North Carolina. Henry Gannett was chief topographer and Gilbert Thompson chief geographer; S. S. Gannett ran the triangulation; F. M. Pearson and C. G. Van Hook drew the topography, surveyed in 1884, 1885 and 1890. Keith mapped the geology in 1889–91 under Bailey Willis, with G. K. Gilbert as chief geologist, and signed his description in May 1895. The plates still name J. W. Powell as Director, though he had resigned the year before they printed. Folio 16 went out as a set of sheets — description, topography, areal geology, economic geology, structure sections — engraved and printed by the Survey itself, Bailey Willis editing the geologic maps and S. J. Kubel cutting the plates.

Four windows

Northwest of Chilhowee Mountain the sheet is Great Valley country: Cambrian and Ordovician limestones and shales folded, faulted and planed off, so that every ridge, every creek and every farm road runs northeast in the same comb. Southeast of that one long ridge the map changes character completely — a single wash of grey and brown over the whole mountain quarter, the Ocoee series, marked age unknown on Keith's own legend, shoved northwest over the younger valley rocks. Inside the grey lie four pale islands: Cades Cove, Tuckaleechee, Wear and Millers coves, limestone floors showing through where erosion has worn holes clean through the thrust sheet. Keith read them correctly in 1895 — the coves “were produced by erosion of the Wilhite slate and Knox dolomite, while the harder rocks around them were not reduced” — and he named formations off this very block that are still in use: the Cades, Thunderhead and Clingman conglomerates, the Wilhite and Pigeon slates.

Three layers

The slider passes from modern relief through the folio's topography sheet — the identical engraved base, hundred-foot contours in brown, drainage in blue — to the areal geology printed on it, so the colour blooms onto lines that do not move. Both plates are rasterised at 300 dpi from the USGS PDFs and registered by correlation on shared linework against the 1895 scan of the same quadrangle in the Historical Topographic Map Collection, which carries the Survey's own polyconic georeference on NAD27. Same survey, same engraving, so the fits are tight: 1.33 px RMS on 100 automatically detected control points for the geology and 1.27 px on 100 for the topography — about 14 metres on the ground either way, roughly the width of the line the engraver drew. No control point was placed by hand.

The gaps as data

The Summits & gaps layer plots eighty named gaps from the U.S. Board on Geographic Names, thinned so the crest stays readable. A gap is the only way through a ridge, and this sheet is nothing but ridges: Chilhowee Gap, where Little River saws through the wall; Ekaneetlee Gap, from the Cherokee Egwanulti, ‘by the river’ — the trace over the crest from Cades Cove to the Oconaluftee; Indian Grave Gap, Big Medicine Gap, Tali Gap, Schoolhouse Gap. Coordinates and summit heights are GNIS's own, taken from the 2021 archive file — the last release that still carried elevations. Every summit label was hunted against the elevation model within 600 m of its GNIS point and agrees with its published feet to within 20 m; anything that missed by more than 130 m was dropped rather than guessed at.

What came after

Keith's last paragraph, May 1895: “the mountain timber has been touched only in the most accessible places, and is for the most part virgin forest.” The Little River Lumber Company was chartered six years later, in 1901, ran its railroad up the gorge he had just mapped, built some 150 miles of track and sawed about 560 million board feet before the mill closed in 1938. Congress authorised Great Smoky Mountains National Park in 1926; it was assembled from roughly 1,200 separate landholdings with state money and five million dollars from the Rockefellers, and fully established on 15 June 1934. The people of Cades Cove, Tremont and the Sugarlands were bought out or condemned out; a few stayed on lifetime leases. The folio drew the country while all of that was still ahead of it.

The terrain

Elevations are open Terrarium tiles at zoom 12 on a local conic grid — about 24 m per drape texel over a 60 × 71 km frame that carries the 45 × 55 km sheet with room around it. The high ground on the sheet, 2,013 m, is the west shoulder of Clingmans Dome; the summit itself, 6,644 ft, stands roughly 120 m east of the neat line, and Keith — who named the Clingman conglomerate for it — sends his reader to the Mount Guyot sheet. The highest named summit inside the line is Mount Buckley, 6,555 ft. The low point is not the river: the Tennessee stands at 248 m behind Fort Loudoun Dam, while a quarry cut in the South Knoxville marble belt reaches 193. Two sheets of water on the modern terrain postdate the folio entirely — Fort Loudoun's pool on the Tennessee, backed up by TVA in 1943, and Chilhowee Lake in the southwest corner, closed by Alcoa in 1957, where the 1895 sheet still draws a running river.

Reading it

Grid: 60 × 71 km · 44 m per height sample

Sheet: 45 × 55 km · 1:125,000 · edition of Jan. 1895

Relief: 193 m (a South Knoxville quarry) to 2,013 m (Clingmans Dome's west shoulder)

Georeference: two folio plates vs the 1895 base · correlation · 1.3 px ≈ 14 m · 200 points

Contours: the sheet's 100 ft — key C

Sources

USGS Geologic Atlas, Folio 16 (https://pubs.usgs.gov/gf/016/) (Keith, 1895) — the areal geology and topography plates; base quadrangle from the Historical Topographic Map Collection (https://ngmdb.usgs.gov/topoview/) (scan 153456, edition of 1895); names, coordinates and heights from GNIS (https://www.usgs.gov/us-board-on-geographic-names). All U.S. government works, public domain. Elevation tiles are open data (https://registry.opendata.aws/terrain-tiles/). This block is Cherokee homeland: the Overhill towns — Chilhowee, Tallassee, Chota — stood on the Little Tennessee just off the sheet's southwest corner; the Treaty of the Holston was signed at James White's fort, now downtown Knoxville, on 2 July 1791; and in 1838–39 the Cherokee were held in stockades and marched west, those who evaded removal in these mountains becoming the Eastern Band, whose Qualla Boundary adjoins the park beyond the sheet's southeast corner. The Cherokee ground flight says so on the ground itself.

## The Big Bend, 1903

Source: `chisos/src/body.html`

The bend, forty years before the park

Two Geological Survey quadrangles of 1903 — TERLINGUA and CHISOS MOUNTAINS, 1:125,000, joined at 103°30′ — draped over modern elevations, with the 1984–85 metric sheets of the same ground one slider-stop behind. Between them the two old sheets hold nearly all of Big Bend National Park, which would not exist until 12 June 1944.

The sheets

Arthur Stiles ran the triangulation and drew both, assisted by J. E. Blackburn and (on the Chisos sheet) S. T. Penick, under E. M. Douglas as geographer in charge. Terlingua was surveyed in 1902–03 in cooperation with the University of Texas Mineral Survey — quicksilver had been found on the Terlingua flats and somebody wanted a map of it — which is much of why these sheets exist this early at all, while the country immediately north of them waited for the Bone Spring sheet of 1918. Chisos Mountains is not a standard quadrangle at all but 45′ of longitude by 30′ of latitude, cut to hold the mountains and the bend. Both print 100-foot contours, both carry the era's printed datum note — to place on 1927 North American datum move projection lines 225 feet south and 100 feet west — and both stop where the country stops being American: Terlingua leaves Mexico as blank paper, while the Chisos sheet carries its contours miles into Coahuila and letters Boquillas and San Vicente on the far bank.

Three layers

All four scans carry their own georeference, so nothing here is fitted: the 1903 pair is polyconic on NAD 27, the 1984–85 pair transverse Mercator on NAD 27, each read from its own GeoTIFF geokeys and resampled straight onto the conic grid. What the pipeline does instead is measure. Correlating the 1903 engraving into the 1985 sheet at the positions the 1985 georeference predicts on its own gives 73 shared points and a disagreement of 31 px median, 44 px rms at 8.47 m per pixel — about 265 m, 370 m rms, worst 780 m. That is not a registration error; it is the distance between a plane-table survey carried on a sparse triangulation net in 1903 and a photogrammetric compilation from 1:24,000 sheets of 1970–71 — four times the sheets' own printed datum note. Nothing was adjusted to hide it, and the modern terrain arbitrates: the 1985 river lies in the model's canyon, the 1903 river a few hundred metres beside it.

Water as data

The Summits & springs layer plots the named springs and tinajas GNIS records inside the block — 76 of them, thinned one to a cell so the basins stay readable: Comanche, Glenn, Neville, Dripping, Ernst Tinaja, Tinaja Blanca, McGuirks Tanks. In the Chihuahuan Desert the map of water is the map of everything: the ranches, the wax camps, the crossings and the raiding trails all sit where water sits, and the 1903 topographers lettered spring after spring in brown because that is what a survey party in this country had to know.

The terrain

Elevations are open Terrarium tiles at zoom 12 on a local conic grid — about 33 m per drape texel over the 137 × 71 km grid, of which the two sheets fill 70 per cent and the rest is table. The block runs from the Rio Grande leaving the east neat at 1,672 ft to Emory Peak, which the model puts at 7,726 ft where GNIS says 7,798 — a 22 m disagreement on a summit, and the model is the one that has been right before. Emory Peak stands 1,775 m above the river at Mariscal Canyon, thirty-two kilometres south of it.

Reading it

Grid: 137 × 71 km · 53 m per height sample

Relief: on the block, 510 m (Rio Grande at Heath Canyon) to 2,355 m (Emory Peak)

Georeference: all four sheets self-georeferenced · 1903 vs 1985 measured at 31 px ≈ 265 m

Contours: the 1903 sheets' 100 ft — key C (the metric sheets' own interval is 20 m)

Sources

All four quadrangles from the USGS Historical Topographic Map Collection (https://ngmdb.usgs.gov/topoview/) — scans 121887 (Terlingua, 1903) and 108199 (Chisos Mountains, 1903) for the drape, 122109 (Chisos Mountains, 1985) and 121986 (Boquillas, 1984) for the middle layer, the latter pair compiled from 1:24,000 sheets of 1970–71 with the Mexican portion taken from a 1983 DGG 1:50,000 map, San Vicente H13D46; names, elevations and springs from GNIS (https://www.usgs.gov/us-board-on-geographic-names), the frozen 2021 archive that still carries elevations. All U.S. government works, public domain. Elevation tiles are open data (https://registry.opendata.aws/terrain-tiles/). This is Chisos, Mescalero Apache and Comanche country: the range carries the name of the Chisos people, who lived in this desert when the Spanish came and were killed, enslaved or absorbed by the mid-1700s; the Mescalero held the high country into the 1880s; and for a century the Comanche War Trail forded the river at Lajitas and below San Vicente on its way into Chihuahua and Coahuila — the 1903 sheets still letter Comanche Spring and Comanche Creek along its line. The villages on the Mexican bank that these sheets name — Boquillas del Carmen, San Vicente, Santa Elena — are ejidos, communal grants of the Mexican agrarian reform, and their people crossed to trade at Boquillas until that port of entry was closed in 2002; it reopened in 2013. On the Texas bank the farm villages the sheets draw — Castolon, La Coyota, Terlingua Abaja, Santa Elena Crossing — were bought out or left as the park came in.

## The Hollows of Stony Man

Source: `luray/src/body.html`

One ridge, surveyed twice, emptied in between

Fifteen minutes of the Blue Ridge — 38°30′ to 38°45′ north, 78°15′ to 78°30′ west — drawn first by a reconnaissance party in 1884–86 and again by a plane-table crew in 1927–29. Between the two printings the Commonwealth of Virginia condemned the mountain out from under the people living on it and gave it to the United States as Shenandoah National Park. The face of this drape is the older sheet — a Blue Ridge of contours, streams and a county line, with a mountain called Ragged where Old Rag is now, and no people on it anywhere. One slider-stop behind it is the survey that put them all on the map, made while the park was being assembled around them.

The two sheets

The drape is the USGS LURAY SHEET, Virginia, 1:125,000 — Henry Gannett, Chief Geographer; Gilbert Thompson, Geographer in charge; Triangulation and Topography by W. T. Griswold; Surveyed in 1884–6, edition of May 1893 reprinted October 1898, with J. W. Powell still named as Director in the top margin. Contour interval 100 feet. The block here is its south-west quarter. What kind of survey it was, the sheet itself eventually admitted: the next edition of the same map, October 1905, is headed RECONNAISSANCE MAP, and the 1938 reprint of that edition says it outright in the bottom margin — Surveyed by reconnaissance methods. Nothing on the 1893 printing warns you.

The middle layer is STONY MAN, VA., 1:62,500, fifteen-minute series — Topography by Hersey Munroe, Fred Graff Jr., K. W. Trimble, W. K. McKinley, H. B. Smith and F. W. Cook. Surveyed in 1927–1929, made in cooperation with the State of Virginia represented by the Conservation Commission, Geological Survey; edition of 1933, reprinted 1944. Contours at 20 and 50 feet. Its neat is exactly this block, which is why the block is this block: it is the only park-era survey covering this ground at map scale. Skyline Drive runs the crest in red, the Shenandoah National Park boundary is the hatched red band, and the 1944 printing adds a red road-classification legend dated 1944.

Three layers, and nothing fitted

The slider passes from modern relief through the 1933 resurvey to the 1893 sheet. No control point was picked and nothing was warped. Both files are Historical Topographic Map Collection GeoTIFFs carrying their own polyconic transform on NAD27, and each layer is resampled straight through its own geokeys; the 1:62,500 sheet, which is 2.7 times finer than this grid, is low-passed by half a texel before the downsample so its twenty-foot contours do not alias into speckle.

What the build does instead is measure the two against each other. Patches of the 1933 engraving were correlated into the 1893 scan at the positions the 1893 geokeys predict on their own; the correlation returned sixty-two control points and fifty-four survived an outlier trim, and they say the old sheet puts the country 240 m from the resurvey at the median, 303 m RMS — twenty-three pixels on a scan of 10.58 m per pixel, about two millimetres at 1:125,000. Split it and it is mostly one thing: 185 m of straight shift (62 m east, 174 m north) and about 90 m of local wander around it. Both scans corner-probe cleanly onto the same printed graticule, so this is not a difference between the sheets' frames; it is the difference between what two surveys forty years apart put inside them. It was measured and printed, never applied.

The practical consequence is visible and worth knowing: the 1893 ink lands roughly 185 m north-north-east of the ground it describes, so its contour bullseye for Hawksbill sits a little uphill of the summit the elevation model actually carries. Crossfade to 1933 and the two agree. The labels on this sheet come from GNIS and the model, not from either printing, so they stay on the mountain while the drape drifts.

Which sheet saw the people

The obvious guess is wrong, and it is the most useful thing on this page. Crossfade to 1893 over any hollow — Corbin, Nicholson, Weakley, Dark Hollow — and there is nothing there: contours, a stream, sometimes a road, no buildings, no hollow names, nobody. A reconnaissance survey mapped the ground, not the households. Crossfade forward to 1933 and every dwelling is a black square, every hollow is lettered, the schools and the churches are marked, the bench marks are set, and the park boundary runs around the whole of it in hatched red. That sheet was made in cooperation with Virginia's Conservation Commission — the state body that was at that moment buying and condemning this land for Shenandoah National Park. The survey that finally recorded where these families lived is the survey made in order to move them.

The ⌂ layer: what is no longer there

GNIS keeps a record after the thing itself is gone and appends one word to the name: (historical). Every such place inside this neat carries a ⌂ here — thirty-six of them. Twenty are schools, five are churches, three are Shenandoah River ferries, two are stores, two are trail shelters; one is the post office at Skyland, one is Aaron Nicholson's house at 2,011 feet in the hollow his family gave its name to, and one is the hamlet of Old Rag, whose GNIS elevation of 1,913 feet is the bench mark the 1933 sheet prints on it. There is no editorial selection here — the filter is the parenthesis. Some of these closed when Page County consolidated its schools and some when a bridge replaced a ferry. The ones up on the ridge — Community School at 3,186 feet, Dark Hollow Church, Thorofare Mountain School, Saint Luke Mission — closed because the people were condemned out from under them between 1935 and 1938.

One name on the middle layer should be said out loud rather than scrolled past. The stream coming off Thorofare Mountain, between Whiteoak Canyon and Robertson Mountain, is lettered on the 1944 printing with a racial slur — as hundreds of features on federal maps were. The U.S. Board on Geographic Names ordered that word replaced throughout in 1963, and GNIS carries no such name anywhere in this block today. It is left where it is because this layer is the printing, not a redrawing of it.

The terrain

Elevations are open Terrarium tiles at zoom 13 on a local conic grid — about 14.5 m per drape texel over the 37 × 43 km grid, of which the printed block is 21.7 × 27.7 km. On the sheet the ground runs from 181 m at the east edge, where the Piedmont streams leave the block below Etlan, to 1,228 m on Hawksbill; the grid keeps falling to 129 m out in the Piedmont beyond the neat. Hawksbill is the sheet's own argument in miniature: the 1893 engraving letters Hawks Bill 4066, the 1933 bench mark reads 4,049, GNIS carries 4,029 and the model gives 4,030. Eighteen summits are named here, and every one of them stands within 14 m of its GNIS elevation in the model. Twelve more real summits — Bushytop, Pollock Knob, Millers Head, Nakedtop, Little Stony Man, Bettys Rock, Tanbark Flat, Marys Rock, Robertson, Corbin, Catlett and Hazel Mountains — sit inside 1.5 km of a taller neighbour, which is close enough that the label-snapping would have climbed them onto it; they are carried as plain names instead, claiming no elevation at all.

Reading it

Grid: 37 × 43 km · 22 m per height sample

Relief: on the sheet, 181 m (the east edge, below Etlan) to 1,228 m (Hawksbill); the grid floor is 129 m beyond the neat

Georeference: both sheets self-georeferenced · nothing fitted · they disagree by 240 m median over 54 points, of which 185 m is one shift

Contours: the drape's 100 ft — the 1933 sheet's are 20 and 50 ft — key C

⌂: 36 places GNIS marks (historical)

Sources

Both sheets from the USGS Historical Topographic Map Collection (https://ngmdb.usgs.gov/topoview/) — Luray 1:125,000, scan 189048 (edition of May 1893, reprinted October 1898) and Stony Man 1:62,500, scan 188599 (edition of 1933, reprinted 1944). The reconnaissance admission quoted above was read off two later printings of the Luray sheet in the same collection, scans 189049 and 189053. Names, coordinates and elevations from GNIS (https://www.usgs.gov/us-board-on-geographic-names), using the frozen 2021 archive file, which still carries elevations; every figure in places.py is re-read from that file at build time and the build stops if one has drifted. All U.S. government works, public domain. Elevation tiles are open data (https://registry.opendata.aws/terrain-tiles/). East of this crest is Manahoac country — Siouan-speaking towns on the Rappahannock headwaters, met and fought by John Smith's party at that river's falls in August 1608 and gone from the Piedmont by about 1700 under Iroquois raiding and epidemic disease; west of it, the Valley was the Great Warriors Path. The crest itself was made a treaty line at Albany in 1722 and the Six Nations' claim beyond it was signed away at Lancaster in June 1744. The Monacan Indian Nation, recognised by Virginia in 1989 and by the United States on 29 January 2018, is still here, and Shenandoah National Park names both peoples in its own account of this ground. Neither name appears anywhere on the 1893 sheet. The Manahoac and Monacan country and The hollows emptied flights say all of this at length.

## Tacoma: Ice and Iron

Source: `tacoma/src/body.html`

The ice sheet's work, the railroad's harbour

Bailey Willis and George Otis Smith's Historical Geology sheet of the Tacoma quadrangle (Geologic Atlas of the United States, Folio 54, 1899) — Vashon drift, outwash prairies, the drowned trench of Puget Sound and the coal measures up the Carbon — with Rankine and Plummer's 1897 standing-timber classification of the very same engraving one slider-stop behind.

The folio

Willis knew this ground before the Survey did: he first came to the Carbon River in the early 1880s as a Northern Pacific man, hunting coal. The quadrangle was triangulated and drawn in 1894–95 by W. T. Griswold, G. E. Hyde and R. H. McKee under chief geographer Henry Gannett; Willis and Smith surveyed the geology in 1895–96, and Folio 54 printed in 1899 under Director Charles D. Walcott. The historical sheet is a reading of the ice age: Vashon drift over an older Admiralty till — both names coined here, on Willis's 1898 evidence, and still in every textbook — with the Steilacoom gravels spread as prairie and the Sound itself left as the trench the ice cut. One unit is an honest mistake: the white Osceola till of the Buckley plateau is the Osceola Mudflow, a collapse of Mount Rainier's summit about 5,700 years ago, recognised for what it is only in the 1950s.

Three layers

The slider passes from modern relief through plate CXXIX of the 21st Annual Report — J. W. Rankine and G. H. Plummer's 1897 land classification, greens for standing timber, red hatching for cutover, yellow for the naturally treeless prairies — to the folio geology. Both plates were printed on the 1897 engraved base the USGS distributes georeferenced (HTMC scan 244174), and each is registered to it by correlation on shared linework. The folio fits to 1.0 px RMS — about 11 m on the ground, from 141 control points; the timber plate, its linework under heavier tints and its paper creased by book folds, still fits to 2.6 px (about 28 m, 141 points). The tints carry less ink, but the section lines and the drainage carry enough.

The mines as data

The Hills & mines layer plots the Survey's own mapped mine workings from USMIN — the adits, shafts, coal mines, prospects and quarries its topographers drew on later editions of these quadrangles. They cluster where the folio's Eocene coal measures crop out: the Wilkeson–Carbonado–Burnett–Fairfax district up the Carbon, and the Renton and Cedar Mountain seams in the northeast corner. The folio itself prints coal-mine symbols at the same bends of the same creeks.

The terrain

Elevations are open Terrarium tiles at zoom 12 on a local conic grid — about 21 m per drape texel over the 53 × 71 km block, from tidewater to 2,440 ft on Cowling Ridge. Puget Sound is held at sea level: the tiles' patchy soundings below zero are voided to the sea surface, so the drape lies on flat water, not on the glacial trench beneath it. Two anachronisms are left in plain sight — Lake Tapps is the 1911 power reservoir, four kettle ponds in the sheets' day; and the modern terrain carries the White River into the Puyallup, a course the river only took in the flood of 1906, after these plates were engraved with it flowing north to the Duwamish.

Reading it

Grid: 53 × 71 km · 31 m per height sample

Relief: 0 m (Puget Sound) to 744 m (Cowling Ridge)

Georeference: two plates vs the 1897 base · correlation · 1.0 / 2.6 px RMS ≈ 11 / 28 m

Contours: the sheets' 50 ft — key C

Sources

USGS Geologic Atlas, Folio 54 (https://pubs.usgs.gov/publication/gf54) (Willis & Smith, 1899); timber plate from the 21st Annual Report, part V (https://pubs.usgs.gov/publication/ar21_5) (Gannett, 1900); base quadrangle from the Historical Topographic Map Collection (https://ngmdb.usgs.gov/topoview/) (scan 244174, edition of 1897); names from GNIS (https://www.usgs.gov/us-board-on-geographic-names); mine features from USMIN (https://mrdata.usgs.gov/usmin/). All U.S. government works, public domain. Elevation tiles are open data (https://registry.opendata.aws/terrain-tiles/). The estuary at the centre of this sheet is Puyallup homeland and the prairies south of it Nisqually country, with the Muckleshoot on the White River bench; the Medicine Creek Treaty was signed in December 1854 six miles off the sheet's southwest corner, the reservations it left are lettered on both plates, and the Terminus flight says so plainly.
