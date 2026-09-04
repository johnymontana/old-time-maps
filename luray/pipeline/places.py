"""Named places and the guided flights for the Stony Man sheet.

Coordinates and feet come from GNIS — the frozen 2021 archive file, which
still carries elevations — and `build.audit_places` re-reads that file at
encode time and refuses to build if a single figure here has drifted from it.
Summits are additionally checked against the elevation model: each must stand
within 130 m of its GNIS feet *and* be the highest ground within 1.5 km, or
`snap_places` would quietly move its label onto a taller neighbour.  This
ridge is crowded, so a dozen real summits — Bushytop, Pollock Knob, Millers
Head, Nakedtop, Little Stony Man, Robertson and Corbin Mountains among them —
failed that second test under Hawksbill and Stony Man and are carried in
FEATURES instead, named but claiming no elevation.

Two label points are not GNIS points and are marked below: the park, whose
GNIS coordinate falls a mile south of this neat, and the South Fork
Shenandoah, whose GNIS point is fifty miles downstream.  Both sit on the
thing the sheets themselves draw inside the block.

Tour keys are (lat, lon, distance km, camera bearing, camera elevation
angle); the bearing is where the camera stands relative to the subject, so
az 180 puts you south of it, looking north.
"""

# Every label below is spelled exactly as GNIS spells it, so this stays empty
GNIS_NAME = {}

PEAKS = [  # name, lat, lon, feet, range — coordinates and feet from GNIS
    ("Hawksbill",           38.55539, -78.39500, 4029, "Blue Ridge"),
    ("Stony Man",           38.59816, -78.37328, 3999, "Blue Ridge"),
    ("Blackrock",           38.52817, -78.44195, 3668, "Blue Ridge"),
    ("Thorofare Mountain",  38.58956, -78.33972, 3369, "Blue Ridge"),
    ("Old Rag Mountain",    38.55172, -78.31603, 3238, "Blue Ridge, east spur"),
    ("Pass Mountain",       38.68286, -78.31430, 3048, "Blue Ridge"),
    ("Knob Mountain",       38.72900, -78.34884, 2861, "Blue Ridge"),
    ("Neighbor Mountain",   38.69579, -78.36068, 2736, "Blue Ridge"),
    ("Kennedy Peak",        38.74203, -78.48766, 2566, "Massanutten Mountain"),
    ("Pignut Mountain",     38.71807, -78.26414, 2536, "Piedmont foothills"),
    ("Oventop Mountain",    38.67233, -78.27583, 2464, "Piedmont foothills"),
    ("Pine Mountain",       38.66084, -78.38412, 1814, "Page Valley"),
    ("Piney Hill",          38.63817, -78.40084, 1604, "Page Valley"),
    ("Browns Mountain",     38.57650, -78.25667, 1575, "Piedmont foothills"),
    ("Hershberger Hill",    38.60100, -78.44461, 1575, "Page Valley"),
    ("Cave Hill",           38.66314, -78.48616, 1063, "Page Valley"),
    ("Oak Hill",            38.74011, -78.41111,  974, "Page Valley"),
    ("Kibler Hill",         38.72401, -78.43842,  965, "Page Valley"),
]
CITIES = [  # name, lat, lon, tier (0 = major)
    ("Luray",        38.66540, -78.45945, 0),
    ("Skyland",      38.59373, -78.38195, 1),
    ("Big Meadows",  38.52651, -78.43973, 1),
    ("Ida",          38.58901, -78.42390, 2),
    ("Marksville",   38.57512, -78.47945, 2),
    ("Mauck",        38.56040, -78.44640, 2),
    ("Valleyburgh",  38.61651, -78.40890, 2),
    ("Pine Grove",   38.53596, -78.48001, 2),
    ("Nethers",      38.57040, -78.27778, 2),
    ("Etlan",        38.52540, -78.26250, 2),
    ("Panorama",     38.65929, -78.32139, 2),
    ("Corbin Cabin", 38.60234, -78.34473, 2),
]
FEATURES = [  # name, lat, lon, kind
    # GNIS puts the park's point a mile south of this neat, so this label sits
    # inside the hatched red boundary the 1933 sheet draws, on Tanners Ridge
    ("Shenandoah National Park", 38.51900, -78.43000, "park"),
    # water — GNIS points, except the river (its point is 50 miles downstream,
    # so the label rides the blue line both sheets draw at the block's edge)
    ("South Fork Shenandoah River", 38.70000, -78.49500, "water"),
    ("Hawksbill Creek",      38.71373, -78.45779, "water"),
    ("East Hawksbill Creek", 38.65623, -78.46140, "water"),
    ("Pass Run",             38.70817, -78.45529, "water"),
    ("Cedar Run",            38.53985, -78.35000, "water"),
    ("Brokenback Run",       38.57373, -78.29417, "water"),
    ("Hannah Run",           38.58846, -78.31361, "water"),
    ("Hogcamp Branch",       38.52568, -78.40695, "water"),
    ("Tims River",           38.55533, -78.35207, "water"),
    ("Dark Hollow Falls",    38.51901, -78.42334, "water"),
    ("Lewis Spring Falls",   38.52040, -78.44945, "water"),
    ("Rose River Falls",     38.53151, -78.40834, "water"),
    # the gaps — the only ways through
    ("Thornton Gap",         38.66123, -78.31973, "region"),
    ("Hawksbill Gap",        38.55679, -78.38639, "region"),
    ("Fishers Gap",          38.53346, -78.42084, "region"),
    ("Milam Gap",            38.50346, -78.44390, "region"),
    ("Hughes River Gap",     38.61207, -78.35723, "region"),
    ("Beahms Gap",           38.69540, -78.31889, "region"),
    ("Elkwallow Gap",        38.73790, -78.30861, "region"),
    # the hollows
    ("Corbin Hollow",        38.56717, -78.32033, "region"),
    ("Nicholson Hollow",     38.57376, -78.29679, "region"),
    # GNIS puts Berry Hollow's point within 20 m of Whiteoak Canyon's and
    # Weakley Hollow's within 120 m of Nicholson Hollow's, so of each pair only
    # one is labelled here; the flights name the others
    ("Whiteoak Canyon",      38.53941, -78.34767, "region"),
    ("Dark Hollow",          38.50952, -78.38894, "region"),
    ("Timber Hollow",        38.57842, -78.41065, "region"),
    ("Jewell Hollow",        38.67268, -78.38298, "region"),
    ("Kettle Canyon",        38.61396, -78.39873, "region"),
    ("Little Devils Stairs", 38.73642, -78.26108, "region"),
    # summits that lost the 1.5 km snap test to a taller neighbour, plus rocks
    ("Marys Rock",           38.65009, -78.31748, "region"),
    ("Little Stony Man",     38.60293, -78.36781, "region"),
    ("Millers Head",         38.59327, -78.39372, "region"),
    ("Bushytop",             38.59141, -78.38678, "region"),
    ("Pollock Knob",         38.58241, -78.38575, "region"),
    ("Nakedtop",             38.55789, -78.40695, "region"),
    ("Bettys Rock",          38.56734, -78.38139, "region"),
    ("Crescent Rock",        38.56123, -78.38362, "region"),
    ("Franklin Cliffs",      38.53707, -78.42028, "region"),
    ("Tanbark Flat",         38.56360, -78.41620, "region"),
    ("Robertson Mountain",   38.57012, -78.34222, "region"),
    ("Corbin Mountain",      38.57949, -78.33357, "region"),
    ("Catlett Mountain",     38.60930, -78.30400, "region"),
    ("Hazel Mountain",       38.62174, -78.28502, "region"),
    ("The Pinnacle",         38.62790, -78.32945, "region"),
    ("Tanners Ridge",        38.51473, -78.47094, "region"),
    ("Tanners Ridge Cemetery", 38.51345, -78.44917, "region"),
]

TOURS = [
    dict(id="skyland", name="Skyland",
         blurb="A copper company's ridge, George Pollock's summer camp, and one mountain measured four times.",
         keys=[dict(lat=38.59816, lon=-78.37328, d=6, az=285, el=15,
                    cap="Stony Man. The 1893 sheet letters it 4,031 feet; the 1927–29 resurvey set a bench mark here and printed 4,010; GNIS now carries 3,999 and the elevation model under this drape gives 3,996. Four answers to one question over a hundred and thirty years, and the mountain has not moved. Much of what this sheet is about is that argument, drawn twice."),
               dict(lat=38.59373, lon=-78.38195, d=4, az=250, el=14,
                    cap="Skyland. George Freeman Pollock's father held stock in the copper company that owned this stretch of ridge; the copper never paid, so in 1894 the son opened a summer camp on the claim instead and called it Stony Man Camp. By the 1933 sheet it is Skyland — cabins, a road up from the valley, and its own post office, which GNIS now files as (historical). The Old Copper Mine is still lettered just north-east of the buildings."),
               dict(lat=38.60293, lon=-78.36781, d=4, az=300, el=13,
                    cap="Little Stony Man's cliff. The grey-green rock is Catoctin greenstone, lava poured over this basement about 570 million years ago, lying on Old Rag Granite roughly twice that age. The Appalachian Trail runs along the top of it; the 1933 sheet letters the trail, and the 1893 sheet has no trail up here at all."),
               dict(lat=38.55539, lon=-78.39500, d=6, az=200, el=16,
                    cap="Hawksbill, the highest ground in the park. The 1893 sheet gives Hawks Bill, two words, 4,066 feet; the 1933 bench mark reads 4,049; GNIS carries 4,029 and the model 4,030. The county line runs over the summit in both printings — Page west, Madison east — and the hamlet down in the valley that the 1893 sheet calls Blosserville is lettered Stony Man by 1933, having taken the mountain's name once the mountain became a destination.")]),
    dict(id="oldrag", name="Old Rag",
         blurb="A billion-year-old granite outlier, the village at its foot, and the name the 1893 sheet actually printed.",
         keys=[dict(lat=38.55172, lon=-78.31603, d=6, az=120, el=15,
                    cap="Old Rag. The 1893 sheet does not call it that — it letters RAGGED MOUNTAIN, which is what Old Rag is short for. The bare summit is Old Rag Granite, about a billion years old: Grenville basement left standing after the younger lavas and sandstones wore off it, which is why this one mountain stands out east of the crest instead of in it. The 1933 sheet prints 3,297 feet on it."),
               dict(lat=38.55707, lon=-78.33223, d=4, az=250, el=14,
                    cap="Old Rag, the village, at the mountain's west foot. GNIS carries it as a populated place, carries its post office beside it, and appends the same word to both: (historical). Its elevation in GNIS, 1,913 feet, is the bench mark the 1933 sheet prints here — a bench mark set five or six years before the last of the families went. The 1893 sheet, at this spot, draws contours and a road and nobody at all."),
               dict(lat=38.57040, lon=-78.27778, d=5, az=90, el=14,
                    cap="Nethers, at the mouth of Weakley Hollow — the way up Old Rag then and now. Watch what the two sheets do with the hollow behind it. The 1893 reconnaissance gives contours, a stream and a road, and not one building. The 1933 resurvey gives the dwellings one black square at a time, names the hollows, marks the schools and the Hughes River church, and runs the park boundary in red around the lot. Nethers stayed outside that line; the hollow above it did not."),
               dict(lat=38.53941, lon=-78.34767, d=6, az=160, el=15,
                    cap="Whiteoak Canyon and Berry Hollow, whose GNIS points fall within twenty metres of each other at the gorge's mouth. A staircase of waterfalls comes down it, the highest of them 86 feet, to the Robinson River country. The 1893 survey drew this at a hundred-foot contour interval, which is to say it drew a smooth V; the 1927–29 resurvey went to twenty feet and the cliffs appear.")]),
    dict(id="hollows", name="The hollows emptied",
         blurb="Say it plainly: close to five hundred families were condemned off this ridge between 1935 and 1938.",
         keys=[dict(lat=38.56717, lon=-78.32033, d=5, az=110, el=14,
                    cap="Corbin Hollow, and the thing these two sheets say together. The 1893 reconnaissance draws this hollow as contours and a stream and nothing else — no houses, no names, nobody. The 1933 resurvey draws every dwelling as a black square, letters the hollows one by one, and marks the schools and churches. It was made for the Virginia Conservation Commission, which was at that moment assembling the park: the map that finally recorded where these families lived is the map made in order to move them."),
               dict(lat=38.60234, lon=-78.34473, d=4, az=250, el=14,
                    cap="Corbin Cabin, built by George T. Corbin in 1909 in Nicholson Hollow — the hollow the valley called the Free State, after the Nicholsons who ran it. GNIS still lists Aaron Nicholson's house up this hollow at 2,011 feet and marks it (historical). Corbin's cabin is the exception: the Potomac Appalachian Trail Club restored it in the 1950s and rents it to hikers by the night. The other houses on the 1933 sheet came down."),
               dict(lat=38.55000, lon=-78.37000, d=11, az=100, el=16,
                    cap="Now say it plainly. In 1933 Mandel Sherman and Thomas R. Henry published Hollow Folk, a study of five hollows here in which Corbin Hollow, under the pseudonym Colvin, stood for the worst of it; it was read as proof that these people had to be moved for their own good. Virginia's Public Park Condemnation Act of 1928 let the Commonwealth take whole blocks of land in one proceeding. On 26 December 1935 Virginia deeded 176,429 acres to the United States and the park was established that day. Close to five hundred families lived inside that line."),
               dict(lat=38.51345, lon=-78.44917, d=4, az=300, el=13,
                    cap="Tanners Ridge Cemetery, 3,300 feet, inside the park boundary and still in use: the families moved off this ridge kept the right to be buried on it. A mile west GNIS marks Saint Luke Mission (historical) — the church is gone, the graves are not. Most of the removals ran from 1935 to 1938, into seven federal resettlement communities, the nearest at Ida Valley three miles from Luray. Forty-two elderly residents were allowed to stay for life; the last, Annie Lee Bradley Shenk, died in 1979.")]),
    dict(id="drive", name="The Drive and the CCC",
         blurb="Begun as drought relief in July 1931, dedicated by Roosevelt in 1936, and segregated until 1950.",
         keys=[dict(lat=38.55679, lon=-78.38639, d=5, az=280, el=14,
                    cap="Skyline Drive at Hawksbill Gap. Grading began on 18 July 1931 as drought relief for Virginia's mountain counties; the central section over Thornton Gap and Hawksbill was carrying traffic by 1934, and the last of the 105 miles was finished in 1939. On the 1933 sheet it is a solid red line along the crest. Crossfade back and the 1893 crest carries the county line and a few roads that cross it at the gaps, and nothing at all that runs along it."),
               dict(lat=38.52651, lon=-78.43973, d=6, az=100, el=15,
                    cap="Big Meadows — open ground on the crest older than the park, held clear first by fire and grazing and now by mowing; the 1893 sheet already fences it as a clearing. Franklin Roosevelt dedicated Shenandoah National Park from here on 3 July 1936; Civilian Conservation Corps camps had been at work in it since 1933. The park he dedicated was segregated: Lewis Mountain, five miles south of this block, opened in 1939 as the separate area for Black visitors, and the park was not fully desegregated until 1950."),
               dict(lat=38.65929, lon=-78.32139, d=6, az=70, el=14,
                    cap="Thornton Gap, where US 211 crosses the ridge. The 1893 sheet letters the gap 2,279 feet — GNIS now says 2,283 — and draws the old Luray-to-Sperryville turnpike hairpinning down the east side of it. The 1933 sheet adds Panorama at the crossing and the Mary's Rock Tunnel, cut through the ridge in 1932 so the Drive could pass under the rock instead of over it. GNIS carries a Thornton Gap School at 2,155 feet and marks it (historical)."),
               dict(lat=38.66540, lon=-78.45945, d=7, az=300, el=14,
                    cap="Luray. Andrew Campbell, his nephew Quint and Benton Stebbins broke into the caverns west of town on 13 August 1878, and Luray has sold the mountain ever since; US 211 over Thornton Gap is the road that brought the traffic. The 1893 sheet draws the town blocks and the two railroads meeting at them, and on the thousand-foot hill a mile west it prints one word on a lead-line: Cave. Whatever the government did up on the ridge, this town was the market for it.")]),
    dict(id="firstpeople", name="Manahoac and Monacan country",
         blurb="The crest was a treaty line before it was a park boundary — and the people it was drawn against are still here.",
         keys=[dict(lat=38.66123, lon=-78.31973, d=8, az=180, el=16,
                    cap="Start with the line itself. In 1722, at Albany, Virginia and the Haudenosaunee agreed that this crest would be the boundary: the Six Nations were not to come east of the Blue Ridge, the colonists not to go west of it. It held twenty-two years. At Lancaster in June 1744 the Six Nations signed away their claim to the Valley beyond, and the patents followed within the decade."),
               dict(lat=38.62174, lon=-78.28502, d=10, az=90, el=16,
                    cap="East of the crest is Manahoac country — Siouan-speaking towns on the headwaters of the Rappahannock, the river draining every hollow on this side of the sheet. In August 1608 John Smith's shallop met them at that river's falls and fought them; the young man his party took prisoner, Amoroleck, said his people lived at the foot of the mountains and had fought because they had heard the English came to take their world from them. By about 1700 the Manahoac were gone from the Piedmont, and the surveyors who followed wrote the country down as empty."),
               dict(lat=38.66000, lon=-78.47000, d=10, az=60, el=16,
                    cap="West of the crest, the Valley. The path up it — the Great Warriors Path, the Indian Road on the earliest Virginia maps — was a north-south highway long before it was a wagon road, carrying Iroquois war parties to the Catawba country and back. The Valley was a corridor and a hunting ground rather than a country of towns, which is exactly what let eighteenth-century patents treat it as nobody's."),
               dict(lat=38.65009, lon=-78.31748, d=9, az=250, el=16,
                    cap="The Monacan Indian Nation, whose towns were on the upper James south-west of here, is still here. Virginia recognised it in 1989 and the United States on 29 January 2018 — after a century in which the Commonwealth's Racial Integrity Act of 1924 worked to make Virginia Indians disappear from the record. Shenandoah National Park names the Manahoac and the Monacan in its own account of this ground. Neither name appears anywhere on the sheet under this camera.")]),
]
