"""Named places and the guided flights for the Black Hills sheet.

Coordinates are GNIS: summits, towns and natural features from the current
DomesticNames product, park and monument points from the frozen 2021
archive (the current product carries no administrative-area class), mines
from the same 2021 archive at build time.  Summits are snapped to the model
and verified against their GNIS elevations.

One exception, documented because it is one: GNIS has no point for Wind
Cave itself — the gazetteer names the park, the canyon and every ranch
around it, but not the hole.  Its coordinate here was read off the printed
cave symbol on the 1901 Hermosa sheet at scan pixel (527, 4934) and pushed
through that sheet's own polyconic georeference, which is where this whole
build gets its geometry anyway.

Tour keys are (lat, lon, distance km, camera bearing, camera elevation).
"""
PEAKS = [  # name, lat, lon, feet, range — coordinates and feet from GNIS
    ("Black Elk Peak", 43.8660, -103.5312, 7247, "Black Hills"),
    ("Odakota Mountain", 43.9234, -103.7543, 7205, "Limestone plateau"),
    ("Green Mountain", 43.9500, -103.7691, 7172, "Limestone plateau"),
    ("Bear Mountain", 43.8698, -103.7440, 7169, "Limestone plateau"),
    ("Medicine Mountain", 43.9114, -103.7133, 6860, "Limestone plateau"),
    ("Thunderhead Mountain", 43.8369, -103.6241, 6552, "Black Hills"),
    ("Buckhorn Mountain", 43.7911, -103.6060, 6309, "Black Hills"),
    ("Cicero Peak", 43.6794, -103.5613, 6165, "Black Hills"),
    ("Custer Mountain", 43.7522, -103.5363, 6063, "Black Hills"),
    ("Mount Coolidge", 43.7447, -103.4816, 6010, "Custer State Park"),
    ("Mount Rushmore", 43.8801, -103.4592, 5718, "Black Hills"),
    ("Calamity Peak", 43.7784, -103.5473, 5627, "Black Hills"),
    ("Iron Mountain", 43.8586, -103.4335, 5446, "Black Hills"),
    ("Elk Mountain", 43.5602, -103.4912, 4505, "Wind Cave"),
]
CITIES = [  # name, lat, lon, tier (0 = major)
    ("Custer", 43.7667, -103.5988, 0),
    ("Hill City", 43.9325, -103.5752, 1),
    ("Keystone", 43.8955, -103.4183, 1),
    ("Hermosa", 43.8397, -103.1910, 1),
    ("Fairburn", 43.6861, -103.2116, 2),
    ("Pringle", 43.6086, -103.5938, 2),
    ("Rockerville", 43.9580, -103.3585, 2),
    ("Oreville", 43.8675, -103.6230, 2),
    ("Fourmile", 43.7328, -103.6755, 2),
    ("Sanator", 43.6967, -103.6058, 2),
    ("Spokane", 43.8414, -103.3799, 2),
    ("Argyle", 43.5350, -103.6480, 2),
    ("Sheridan", 43.9769, -103.4705, 2),
]
FEATURES = [  # name, lat, lon, kind
    ("Wind Cave National Park", 43.5801, -103.4395, "park"),
    ("Custer State Park", 43.7003, -103.4380, "park"),
    ("Mount Rushmore National Memorial", 43.8804, -103.4525, "park"),
    ("Jewel Cave National Monument", 43.7287, -103.8407, "park"),
    ("Wind Cave", 43.5588, -103.4750, "region"),   # read off the 1901 sheet
    ("The Needles", 43.8369, -103.5494, "region"),
    ("Cathedral Spires", 43.8494, -103.5324, "region"),
    ("Rankin Ridge", 43.6254, -103.4824, "region"),
    ("Red Valley", 43.5604, -103.3861, "region"),
    ("Buffalo Gap", 43.5194, -103.3477, "region"),
    ("Bison Flats", 43.5433, -103.4788, "region"),
    ("Gillette Prairie", 43.9591, -103.7491, "region"),
    ("Sylvan Lake", 43.8460, -103.5634, "water"),
    ("Sheridan Lake", 43.9736, -103.4686, "water"),
    ("Stockade Lake", 43.7683, -103.5169, "water"),
    ("Center Lake", 43.8009, -103.4168, "water"),
    ("Wind Cave Canyon", 43.5473, -103.4036, "water"),
    ("Hell Canyon", 43.5685, -103.9506, "water"),
    ("Highland Creek", 43.5655, -103.3841, "water"),
    ("Grace Coolidge Creek", 43.8269, -103.2202, "water"),
]
FAMOUS_MINES = (  # in order of standing; the ⚒ layer thins by cell, best first
    "Holy Terror", "Etta", "Peerless", "Hugo", "Bullion", "Big Chief",
    "Ingersoll", "Tin Mountain", "Tin Queen", "Clara Belle", "Saint Elmo",
    "Tungsten", "Keystone", "Noble Mica", "Western Feldspar", "Golden Crown",
    "North Star", "Wabash",
)

TOURS = [
    dict(id="windcave", name="The cave that breathes",
         blurb="The seventh national park, and the first anywhere made for a cave — a crack in the limestone that inhales and exhales with the weather.",
         keys=[dict(lat=43.5801, lon=-103.4395, d=9, az=200, el=15,
                    cap="Wind Cave National Park, set apart 9 January 1903 — the seventh national park and the first created to protect a cave. Darton's text puts it flatly: 'Wind Cave, 7 miles northwest of Buffalo Gap and 12 miles northwest of Hot Springs, on the Chicago & Northwestern Railway, is included in a national park.'"),
               dict(lat=43.5473, lon=-103.4036, d=6, az=300, el=14,
                    cap="The cave is dissolved into the Pahasapa limestone — Darton's formation name, taken from Paha Sapa, the Lakota name for these hills. Its passages follow the joints of the rock southeastward and downward to about 250 feet below the entrance; the wind that named it blows out of the crevices, and sometimes in."),
               dict(lat=43.5433, lon=-103.4788, d=7, az=340, el=14,
                    cap="Bison Flats. Fourteen bison arrived by rail from the New York Zoological Park in 1913, for the game preserve Congress had made the year before; elk and pronghorn followed. The prairie under them is drawn here as it was surveyed in 1898–99, when there were none."),
               dict(lat=43.5194, lon=-103.3477, d=8, az=280, el=15,
                    cap="Buffalo Gap — the notch worn through the hogback where the herds came out of the hills, and where the railroad followed them. The park's south boundary runs within a few hundred metres of this sheet's 43°30′ neat line: all but a thin strip of it is on the map, and Hot Springs, twelve miles southeast, is not.")]),
    dict(id="hesapa", name="He Sapa",
         blurb="Treaty land, an army expedition, a gold rush and a seizure — each one readable on the ground it happened on.",
         keys=[dict(lat=43.7667, lon=-103.5988, d=8, az=110, el=14,
                    cap="Custer, on French Creek. In July 1874 Lieutenant Colonel George A. Custer led about a thousand men and 110 wagons into country the 1868 Fort Laramie treaty had set apart for the Lakota's 'absolute and undisturbed use and occupation.' His prospectors found gold in this creek; the telegraphs did the rest."),
               dict(lat=43.7683, lon=-103.5169, d=6, az=250, el=14,
                    cap="Stockade Lake, named for the Gordon party's log stockade of December 1874 — twenty-eight trespassers on treaty land, cleared out by cavalry in the spring. The Army could not hold the line, and did not try for long."),
               dict(lat=43.8660, lon=-103.5312, d=10, az=200, el=17,
                    cap="Black Elk Peak, 7,247 feet — the highest ground for a very long way in any direction. This folio prints it as Harney Peak, 7,242 feet, for the general who commanded the 1855 attack on a Lakota village at Blue Water Creek; in 2016 the U.S. Board on Geographic Names put the name of the Oglala holy man Nicholas Black Elk on it instead."),
               dict(lat=43.8369, lon=-103.6241, d=9, az=90, el=15,
                    cap="Thunderhead Mountain. An act of Congress took the Black Hills on 28 February 1877, nine years after the treaty guaranteed them. In 1980 the Supreme Court held that this was a taking without just compensation; the money has sat uncollected and compounding past a billion dollars, because the claim was never for money. Carving on the Crazy Horse Memorial here began in 1948, at Henry Standing Bear's invitation.")]),
    dict(id="pegmatite", name="The pegmatite belt",
         blurb="Gold at Keystone, then tin, mica, feldspar and spodumene out of the same coarse granite — the ⚒ marks are all one rock.",
         keys=[dict(lat=43.8955, lon=-103.4183, d=6, az=200, el=14,
                    cap="Keystone. The Holy Terror was sunk in 1894 and shut by 1903 — the richest gold mine in the southern hills, and among the deadliest. The ⚒ marks crowded around it are pegmatite workings: Hugo, Peerless, Big Chief, Ingersoll; the plate itself letters ETTA MINE and ETTA MILL just here, where spodumene crystals came out of the rock forty feet long."),
               dict(lat=43.9325, lon=-103.5752, d=8, az=170, el=15,
                    cap="Hill City, headquarters of the tin bubble. English money bought up the Harney Peak tin district in the late 1880s on the strength of cassiterite in the pegmatites; mills were built, the tin never paid, and the claims passed to the mica and feldspar men."),
               dict(lat=43.7469, lon=-103.7210, d=8, az=60, el=15,
                    cap="Tin Mountain, west of Custer. The folio's economic note keeps the whole ledger in one sentence: 'tin and mica in pegmatitic dikes and veins; spodumene and amblygonite (lithia rock) in pegmatitic dikes.' Lithia rock is lithium; the sheet mica went into radios."),
               dict(lat=43.9580, lon=-103.3585, d=7, az=250, el=14,
                    cap="Rockerville, on the dry gravels east of the hills. The placers here had gold and no water, so in 1880 a flume seventeen miles long was built to bring Spring Creek to them. It ran a few seasons; the town is a name on a map now.")]),
    dict(id="needles", name="Norbeck's granite",
         blurb="Sylvan Lake, the Needles and a mountain nobody had carved yet — the country a senator turned into a park.",
         keys=[dict(lat=43.8460, lon=-103.5634, d=5, az=210, el=14,
                    cap="Sylvan Lake — a dam thrown across a granite gorge in 1881. Pull the slider one stop back and the 1901 quadrangle already holds the water and letters SYLVAN LAKE HOTEL beside it; the folio colours the rock around both Harney Peak granite, the coarse pink stuff the whole central hills are made of."),
               dict(lat=43.8369, lon=-103.5494, d=4, az=140, el=13,
                    cap="The Needles: granite spires weathered out along joints in the pegmatite-shot granite. The road that made them famous opened in 1922 — three years before this folio printed — and it is nowhere on the sheet, because the topography under the geology was surveyed in 1897–99."),
               dict(lat=43.8801, lon=-103.4592, d=5, az=200, el=14,
                    cap="Mount Rushmore, 5,718 feet, named in 1885 for a New York lawyer who came out to check mining titles. Gutzon Borglum picked it out in 1925, the year this folio was published; drilling began 4 October 1927 and stopped 31 October 1941. On this sheet the ridge is still only granite."),
               dict(lat=43.8586, lon=-103.4335, d=7, az=210, el=15,
                    cap="Iron Mountain. Custer State Park was a game preserve from 1913 and a state park from 1919 — Peter Norbeck's work; the mountain south of here took President Coolidge's name in 1927, while he spent the summer at the State Game Lodge. Norbeck laid out the road over this ridge on horseback, with pigtail bridges and tunnels aimed at Rushmore.")]),
    dict(id="artesian", name="Darton's water",
         blurb="The Red Valley, the hogback and the three sheets in this folio that map what you cannot see: the water underground.",
         keys=[dict(lat=43.5604, lon=-103.3861, d=8, az=300, el=14,
                    cap="The Red Valley — a ring of soft red Spearfish shale worn all the way around the uplift, between the limestone rim inside and the hogback outside. Lakota tradition knows this circle as the Race Track, where the animals and the two-leggeds ran their great race."),
               dict(lat=43.8397, lon=-103.1910, d=9, az=260, el=15,
                    cap="Hermosa, out on the plains east of the hogback. Three more sheets in this folio map nothing you can look at: the depth to the Dakota and Minnelusa sandstones, and the height to which their water will rise in a well. Darton had already written the Water-Supply Paper on it in 1918."),
               dict(lat=43.6861, lon=-103.2116, d=9, az=290, el=15,
                    cap="Fairburn, where the beds tip east off the dome. The folio's artesian sheets mark out where a well will flow on its own pressure — the valleys of the Cheyenne and of Beaver, French, Battle, Spring and Rapid creeks — water that soaked in on the outcrops behind you and travels east under everything, losing head as it goes."),
               dict(lat=43.6254, lon=-103.4824, d=8, az=160, el=15,
                    cap="Rankin Ridge, the high ground of Wind Cave National Park at about 5,010 feet. Everything in this frame is limestone plateau tipped gently outward: the rain that lands on it runs down the dip, into the sandstones, and east to wells a hundred miles away.")]),
]
