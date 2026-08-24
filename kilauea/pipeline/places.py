"""Named places, the guided flights and the flow list — the Kīlauea sheet.

Coordinates come from GNIS (DomesticNames_HI) and nowhere else; the current
edition is used because it carries the ʻokina and kahakō, and the names on
this block are Hawaiian names.  Summit figures come from the 2021 GNIS
archive, the last edition that still published elevations, and every one of
them was checked against the model: the highest Terrarium sample within
600 m of the GNIS point, dropped if it missed by more than 130 m.  On a
shield volcano that is a real filter — half the named cones on Mauna Loa's
flank sit on ground that keeps climbing past them, and those were dropped
rather than argued with.  `pipeline/verify.py` re-runs the check.

Tour keys are (lat, lon, distance km, camera bearing, camera elevation
angle); the bearing is where the camera stands relative to the subject, so
az 180 puts you south of it looking north.
"""

# GNIS marks a few of these "(historical)"; the label prints the name alone
GNIS_NAME = {
    "ʻŌhaikea": "ʻŌhaikea (historical)",
    "Moaʻula": "Moaʻula (historical)",
    "Na Puu Waenakonu": "Na Puu Waenakonu (historical)",
}

PEAKS = [  # name, lat, lon, feet, where — coordinates and feet from GNIS
    ("Mauna Loa",         19.47539, -155.60579, 13665, "Mokuʻāweoweo"),
    ("1949 Cone",         19.45605, -155.60459, 13412, "caldera floor"),
    ("1940 Cone",         19.46198, -155.60100, 13320, "caldera floor"),
    ("Na Puu Waenakonu",  19.46396, -155.59720, 13123, "caldera floor"),
    ("Pōhakuhanalei",     19.43112, -155.62011, 12772, "Mauna Loa, south rim"),
    ("Pohakuʻohanalei",   19.50338, -155.55483, 12369, "Mauna Loa, northeast"),
    ("Red Cone",          19.38933, -155.62613, 11443, "Southwest Rift"),
    ("Sulphur Cone",      19.38787, -155.63591, 11365, "Southwest Rift"),
    ("ʻĀlika Cone",       19.27291, -155.73198,  7835, "Southwest Rift"),
    ("Puʻuʻokeʻokeʻo",    19.21363, -155.74192,  6863, "Southwest Rift"),
    ("Keau",              19.20417, -155.74150,  6522, "Southwest Rift"),
    ("Puʻukinikini",      19.25921, -155.59892,  6378, "Kahuku"),
    ("Kapoalaala",        19.18889, -155.73722,  6165, "Kahuku"),
    ("Puʻuiki",           19.23567, -155.58261,  5374, "Kahuku"),
    ("Ihuanu",            19.16227, -155.73284,  5295, "Kahuku"),
    ("Makaālia",          19.18738, -155.59901,  4288, "Kaʻū"),
    ("Kīlauea",           19.42094, -155.28742,  4088, "Kīlauea summit"),
    ("Puʻupuaʻi",         19.41208, -155.25324,  3884, "Kīlauea Iki, built 1959"),
    ("Kaiholena",         19.17516, -155.58085,  3802, "Kaʻū"),
    ("Puu Ohale",         19.35087, -155.27654,  3317, "Kaʻū Desert"),
    ("Puʻukoaʻe",         19.35528, -155.32233,  3228, "Kaʻū Desert"),
    ("Maunaiki",          19.34772, -155.35257,  3018, "Southwest Rift, built 1919–20"),
    ("Puʻukuanēnē",       19.32216, -155.41945,  2825, "Kapāpala"),
    ("Kamakaiʻa Uka",     19.31252, -155.35598,  2703, "Kamakaiʻa Hills"),
    ("Puʻukou",           19.28795, -155.39209,  2267, "Kapāpala"),
    ("Puʻukapukapu",      19.27576, -155.25953,  1040, "above the Halapē coast"),
]

CITIES = [  # name, lat, lon, tier (0 = major)
    ("Pāhala",                   19.20250, -155.47694, 0),
    ("Nāʻālehu",                 19.06185, -155.58281, 0),
    ("Waiʻōhinu",                19.06776, -155.61203, 1),
    ("Punaluʻu",                 19.13695, -155.50460, 1),
    ("Honuʻapo",                 19.08949, -155.54873, 1),
    ("Nīnole",                   19.13004, -155.51189, 2),
    ("Hīlea",                    19.13546, -155.53340, 2),
    ("Moaʻula",                  19.18333, -155.49944, 2),
    ("Waikapuna",                19.02086, -155.57975, 2),
    ("Punaluʻu Kahawai",         19.24787, -155.60640, 2),
    ("ʻĀinapō",                  19.35587, -155.42258, 2),
    ("ʻŌhaikea",                 19.43333, -155.35000, 2),
    ("Kilauea Military Reserve", 19.43358, -155.27438, 2),
]

FEATURES = [  # name, lat, lon, kind
    ("Halemaʻumaʻu",        19.40664, -155.28353, "park"),
    ("Kaluapele",           19.41206, -155.27587, "park"),
    ("Kīlauea Iki Crater",  19.41370, -155.24727, "park"),
    ("Keanakākoʻi Crater",  19.40016, -155.26392, "park"),
    ("Luamanu Crater",      19.39852, -155.25373, "park"),
    ("Puhimau Crater",      19.39289, -155.24913, "park"),
    ("Mokuʻāweoweo",        19.47019, -155.59223, "park"),
    ("North Pit",           19.49103, -155.58233, "park"),
    ("South Pit",           19.44705, -155.60241, "park"),
    ("Luapoholo",           19.48589, -155.57568, "park"),
    ("Luahohonu",           19.43835, -155.60627, "park"),
    ("Cone Crater",         19.35545, -155.31260, "park"),
    ("Kaʻū Desert",         19.35000, -155.31667, "region"),
    ("Southwest Rift Zone", 19.38873, -155.31042, "region"),
    ("Footprints",          19.35848, -155.36307, "region"),
    ("Kamakaiʻa Hills",     19.30588, -155.36477, "region"),
    ("Hilina Pali",         19.29060, -155.30375, "region"),
    ("Kaʻōiki Pali",        19.38225, -155.36453, "region"),
    ("Uēkahuna",            19.42576, -155.28093, "region"),
    ("Haʻakulamanu",        19.43349, -155.26136, "region"),
    ("Halapē",              19.26962, -155.25819, "region"),
    ("Kapāpala",            19.32306, -155.43833, "region"),
    ("Keauhou",             19.40944, -155.26056, "region"),
    ("Kahuku",              19.20639, -155.71722, "region"),
    ("Wood Valley",         19.26946, -155.47434, "region"),
    ("Wailau Hawaiian Home Land",    19.14461, -155.51711, "region"),
    ("Waiʻōhinu Hawaiian Home Land", 19.07357, -155.62023, "region"),
    ("Punaluʻu Beach",      19.13591, -155.50445, "water"),
    ("Honuʻapo Bay",        19.08007, -155.55051, "water"),
    ("Kāwā Bay",            19.11291, -155.52495, "water"),
    ("Waikapuna Bay",       19.01873, -155.57877, "water"),
    ("Nīnole Springs",      19.12930, -155.51246, "water"),
    ("Hāʻao Springs",       19.08808, -155.62183, "water"),
    ("Keaīwa Reservoir",    19.24872, -155.50032, "water"),
    ("Pāʻauʻau Gulch",      19.18975, -155.46421, "water"),
    ("Kīlauea Gulch",       19.34782, -155.42836, "water"),
]

# years GNIS spells into a flow name; used to rank the data layer
DATED_FLOWS = ('1823', '1851', '1868', '1880', '1887', '1907', '1916', '1919',
               '1920', '1921', '1926', '1949', '1950', '1954', '1959', '1974')

TOURS = [
    dict(id="kaluapele", name="Kaluapele",
         blurb="The caldera of Kīlauea, home of Pelehonuamea — a lava lake on the 1921 sheet, and what May 1924 did to it.",
         keys=[dict(lat=19.40664, lon=-155.28353, d=4.5, az=205, el=15,
                    cap="Halemaʻumaʻu, the home of Pelehonuamea. This is a living Hawaiian temple, not a viewpoint: hoʻokupu are still brought to this rim. When the sheet was surveyed a lava lake stood in the pit."),
               dict(lat=19.40900, lon=-155.28000, d=6.0, az=250, el=16,
                    cap="In February 1924 the lava lake drained out of sight. By May groundwater had reached the hot conduit, and a fortnight of steam explosions threw blocks onto the rim, roughly doubled the crater's drawn width and dropped its floor hundreds of feet. One man, Truman Taylor, was killed on 18 May. The 1921 sheet is the crater as it stood three years before."),
               dict(lat=19.42576, lon=-155.28093, d=3.2, az=160, el=15,
                    cap="Uēkahuna, the bluff on the northwest rim — the sheet letters a Museum and BM 4090 here. Thomas Jaggar founded the Hawaiian Volcano Observatory in 1912 and kept his seismograph vault across the caldera by the Volcano House; both buildings are lettered on this sheet, along with a Prison Camp on the road west."),
               dict(lat=19.41370, lon=-155.24727, d=3.4, az=250, el=16,
                    cap="Kīlauea Iki, drawn here with a flat floor, at the block's very east edge. In November 1959 a fountain on its south wall reached some 1,900 feet, filled the pit with a lava lake and piled the cinder cone Puʻupuaʻi — none of which the sheet can show.")]),

    dict(id="mokuaweoweo", name="Mokuʻāweoweo",
         blurb="Mauna Loa's summit caldera on the 1928 sheet, three miles of pit and pit-crater at thirteen thousand feet.",
         keys=[dict(lat=19.47019, lon=-155.59223, d=7.5, az=200, el=16,
                    cap="Mokuʻāweoweo. The 1928 sheet carries bench marks of 13,653 and 13,648 feet on its west rim and pencils the caldera's outline in 50-foot contours, the same interval used at sea level forty miles south."),
               dict(lat=19.48800, lon=-155.58000, d=5.0, az=170, el=16,
                    cap="North Pit and Lua Poholo at the caldera's north end. The 1928 sheet contours Lua Poholo as a clean shaft off the northeast lip, with a waterhole and BM 13018 lettered beside it — this is a mountain the surveyors had to carry their own water up."),
               dict(lat=19.45900, lon=-155.60200, d=4.2, az=215, el=15,
                    cap="The 1940 and 1949 cones stand on the caldera floor and are named for eruptions that happened after every sheet in this block was printed. The map's floor is flat where they now are — the ground here is younger than its cartography."),
               dict(lat=19.39381, lon=-155.45000, d=10.0, az=125, el=15,
                    cap="ʻĀinapō, the old Hawaiian route to the summit up the southeast flank — the way parties climbed Mauna Loa before any road existed. The 1928 sheet letters TRAIL across the high contours and dots waterholes along them.")]),

    dict(id="kau-desert", name="The Kaʻū Desert",
         blurb="Ash, cracks and cones on the Southwest Rift — the driest ground on a wet island, and a place of memory.",
         keys=[dict(lat=19.35848, lon=-155.36307, d=4.5, az=300, el=15,
                    cap="The ash bed here holds footprints. Hawaiian accounts record that in 1790 an explosive eruption of Kīlauea caught part of Keōua Kuahuʻula's army crossing this desert and killed many of them, in the war that ended with Kamehameha's rule over the island. The ground is a place of memory."),
               dict(lat=19.34772, lon=-155.35257, d=4.0, az=210, el=15,
                    cap="Maunaiki, 3,018 feet, was not here when the century began: a Southwest Rift eruption built it between December 1919 and August 1920. The 1921 sheet is new enough to draw it — one of the few places where this cartography is younger than its ground."),
               dict(lat=19.22275, lon=-155.42157, d=9.0, az=60, el=15,
                    cap="The Great Crack, miles of open ground fissure down the rift. Lava came out of it in 1823 — the Keaīwa flow, fast pāhoehoe that ran to the sea; William Ellis's party walked across Kaʻū that same year and described ground still steaming."),
               dict(lat=19.30588, lon=-155.36477, d=5.5, az=250, el=15,
                    cap="The Kamakaiʻa Hills, cones strung along the rift. Pull the slider back one stop: Stearns' 1930 map colours the flows around them by age, pink for the youngest, and marks each fissure the lava came out of.")]),

    dict(id="pali", name="Down to the sea",
         blurb="Kīlauea's south flank, sliding seaward — three fault scarps between the desert and the surf.",
         keys=[dict(lat=19.29060, lon=-155.30375, d=6.5, az=200, el=14,
                    cap="Hilina Pali — 1,302 feet at the lip. The whole south flank of Kīlauea is creeping seaward, and these palis are where it breaks; the sheets draw them as walls of hachures, three of them stepping down to the water."),
               dict(lat=19.26962, lon=-155.25819, d=3.6, az=320, el=13,
                    cap="Halapē, a coconut grove on the shore. In November 1975 a magnitude 7.7 earthquake dropped this coast about ten feet and the sea came in behind it; two campers were killed. The 1921 sheet shows the beach as it stood before."),
               dict(lat=19.27576, lon=-155.25953, d=4.5, az=280, el=14,
                    cap="Puʻukapukapu, 1,040 feet, above that coast — the pali country the old coastal trail crossed between Kaʻū and Puna, with a night's walk between water sources."),
               dict(lat=19.26010, lon=-155.29853, d=5.0, az=20, el=13,
                    cap="Kaʻaha and the Kaʻū shore westward. Below the palis the block runs out to blank paper on the sheets and dead-flat zero in the model: the sea floor drops thousands of metres within a few miles of this beach, and none of it is drawn.")]),

    dict(id="kau-sugar", name="Kaʻū sugar",
         blurb="Cane, landings and a homestead act — the Kaʻū coast between Pāhala and Nāʻālehu.",
         keys=[dict(lat=19.20250, lon=-155.47694, d=6.5, az=200, el=15,
                    cap="Pāhala, the mill town — the black block beside BM 834 is the mill itself. The sheet letters PIPE LINE down from the Wood Valley uplands and names the plantation camps around it: Whitney, Meyer, Moaʻula, Makanau. Cane was ground here from the 1870s until the last Kaʻū harvest in 1996."),
               dict(lat=19.13695, lon=-155.50460, d=4.0, az=300, el=14,
                    cap="Punaluʻu, the landing where Kaʻū sugar went aboard: HAWAIIAN AGRICULTURAL CO. is lettered down the ticked railroad line that comes to it from Pāhala, and the wharf is drawn at the head of the bay. The beach is Keoneʻeleʻele, black sand made of lava quenched at the shore, and fresh water still rises through it."),
               dict(lat=19.26946, lon=-155.47434, d=6.5, az=180, el=15,
                    cap="Wood Valley. On 2 April 1868 a magnitude 7.9 earthquake shook Kaʻū; a mudflow came down out of this valley and killed thirty-one people, and a tsunami the same day destroyed the villages along the coast below. The surveyors of these sheets worked among people who remembered it."),
               dict(lat=19.14461, lon=-155.51711, d=6.0, az=250, el=15,
                    cap="Wailau. The Hawaiian Homes Commission Act passed in 1921 — the year the Kilauea sheet was surveyed — setting aside tracts for Kanaka ʻŌiwi homesteading; Wailau and Waiʻōhinu are two of them, and both are on this block.")]),
]
