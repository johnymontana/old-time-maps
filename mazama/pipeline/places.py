"""Named places, the guided flights and the 1886 soundings — the Mazama sheet.

Coordinates are from GNIS (DomesticNames_OR) only, never from memory.

Summit figures are the **model's own**: the Terrarium surface at the highest
sample within 600 m of the GNIS point, rounded to ten feet.  This repository
takes the DEM as truth about ground, and on this sheet that choice is load
bearing — the drape underneath carries Mark B. Kerr's 1886 figures, which run
high.  Kerr put the lake surface at 6,239 feet; the model reads a dead-flat
6,175.  Every peak below sits within 45 m of a real local maximum in the
model, so the coordinate is doing its job; where the printed 1886 figure is
worth quoting it is quoted in the range field and in the flights.

The data layer is the lake itself.  Plate I prints 56 depth figures inside
the shoreline — soundings from the 168 casts Major C. E. Dutton's party made
from the boat *Cleetwood* in 1886.  Each was read once off the 300-dpi
rasterisation with a ruler-grid crop, and the inverse of the plate's own
graticule fit puts it on the ground; see SOUNDINGS at the foot of this file.

Tour keys are (lat, lon, distance km, camera bearing, camera elevation angle).
"""
PEAKS = [  # name, lat, lon, feet (model), note — coordinates from GNIS
    ("Mount Scott", 42.922935, -122.016030, 8910, "east of the rim — 'Scott Peak', 1886"),
    ("Applegate Peak", 42.899752, -122.104980, 8110, "south rim — 'Vidae Peak', 8,228 ft on the plate"),
    ("Hillman Peak", 42.951830, -122.169269, 8100, "west rim — 'Glacier Peak', 8,227 ft on the plate"),
    ("Cloudcap", 42.931215, -122.043020, 8060, "east rim — 'Cloud Cap', 8,081 ft on the plate"),
    ("Garfield Peak", 42.903985, -122.123386, 8050, "south rim — unnamed in 1886"),
    ("Llao Rock", 42.972073, -122.133362, 8040, "north rim — the dacite flow"),
    ("The Watchman", 42.942937, -122.172391, 7990, "west rim — 8,125 ft on the plate"),
    ("Union Peak", 42.831117, -122.223304, 7670, "south-west corner of the park"),
    ("Grouse Hill", 42.992480, -122.121298, 7400, "north of the rim"),
    ("Timber Crater", 43.045129, -122.063917, 7400, "north-east corner — 7,642 ft on the plate"),
    ("Red Cone", 42.997887, -122.163266, 7350, "north-west — 7,511 ft on the plate"),
    ("Crater Peak", 42.848181, -122.097790, 7260, "south flank — 7,425 ft on the plate"),
    ("Desert Cone", 43.034262, -122.158731, 6660, "in the Pumice Desert"),
    ("Bald Crater", 43.041787, -122.220296, 6470, "north-west — 6,567 ft on the plate"),
    ("Maklaks Crater", 42.832741, -122.018045, 6410, "south-east corner — unnamed in 1886"),
]
CITIES = [  # the human places: landings, viewpoints, the road head — GNIS coords
    ("Discovery Point", 42.924851, -122.162251, 0),
    ("Victor Rock", 42.910962, -122.142528, 0),
    ("Cleetwood Cove", 42.974405, -122.080188, 1),
    ("Annie Spring", 42.872190, -122.168973, 1),
    ("Eagle Cove", 42.914935, -122.137147, 1),
    ("Munson Valley", 42.865252, -122.145760, 2),
    ("Sun Notch", 42.902630, -122.096971, 2),
    ("Kerr Notch", 42.912352, -122.071693, 2),
    ("Steel Bay", 42.973204, -122.113616, 2),
    ("Grotto Cove", 42.954880, -122.055871, 2),
]
FEATURES = [  # name, lat, lon, kind — GNIS coords
    ("Crater Lake", 42.942012, -122.106390, "water"),
    ("Chaski Bay", 42.909140, -122.103920, "water"),
    ("Danger Bay", 42.917535, -122.074999, "water"),
    ("Llao Bay", 42.964641, -122.139613, "water"),
    ("Boundary Springs", 43.066552, -122.229670, "water"),
    ("Duwee Falls", 42.864615, -122.147246, "water"),
    ("Anderson Spring", 42.913384, -122.048505, "water"),
    ("Cascade Spring", 42.952677, -122.022007, "water"),
    ("Pole Bridge Creek", 42.845408, -122.141138, "water"),
    ("Sphagnum Bog", 42.997296, -122.257289, "water"),
    ("Wizard Island", 42.938739, -122.145584, "region"),
    ("Phantom Ship", 42.910963, -122.092527, "region"),
    ("Devils Backbone", 42.960930, -122.158142, "region"),
    ("Dutton Cliff", 42.904297, -122.085304, "region"),
    ("Redcloud Cliff", 42.936797, -122.050860, "region"),
    ("Skell Head", 42.945685, -122.056693, "region"),
    ("Rugged Crest", 42.980543, -122.075352, "region"),
    ("Pumice Desert", 43.033183, -122.126141, "region"),
    ("The Pinnacles", 42.852910, -122.009191, "region"),
    ("Castle Crest", 42.907301, -122.125977, "region"),
]

TOURS = [
    dict(id="engulfed", name="Seventeen cubic miles",
         blurb="A mountain is missing, and the rim is the argument: Diller and Dutton reason their way to a collapse.",
         keys=[dict(lat=42.9420, lon=-122.1064, d=11, az=190, el=17,
                    cap="Everything you are looking at is the stump. Diller reckoned the caldera at 'over 27 square miles' inside the crest of the rim and its missing volume at about 17 cubic miles of mountain — and then went looking on the outer slopes for the fragmental rim a blast that size would have thrown down."),
               dict(lat=42.9450, lon=-122.1700, d=5, az=250, el=15,
                    cap="He never found it. 'The surface of the outer slope of the rim exposes everywhere either glaciated rock, glacial moraine or pumice' — and nowhere the fragmental rim a blast would have laid down. So 'we are practically driven to the opinion that Mount Mazama has been engulfed.' The inner wall shows the mechanism: sheet on sheet of andesite lava dipping away from the lake, the flanks of a cone whose middle dropped out."),
               dict(lat=42.9721, lon=-122.1334, d=4.5, az=340, el=14,
                    cap="Llao Rock, lettered D for dacite in Diller's red on Kerr's sheet and painted pale yellow on his own: a stiff flow that filled a glacier-cut notch in the rim not long before the end. Slide to the geology and the dacite runs yellow along the whole north rim, with the moraines in olive out beyond."),
               dict(lat=43.0332, lon=-122.1261, d=7, az=20, el=16,
                    cap="The Pumice Desert, a flat of ash that still will not grow trees — the near end of a fall that laid Mazama ash across the Northwest and into Canada about 7,700 years ago. The Mazamas, the Portland climbing club, gave the vanished mountain its name in 1896 because, as Diller put it, the peak 'had no name.'")]),
    dict(id="cleetwood", name="The Cleetwood, 1886",
         blurb="A boat lowered down the caldera wall, a lead on a wire, and the numbers still printed on the water.",
         keys=[dict(lat=42.9744, lon=-122.0802, d=4, az=30, el=14,
                    cap="Cleetwood Cove, named for the survey boat the 1886 party hauled to the rim and lowered down the inside wall. From here they rowed the lake and let a lead weight down on wire, cast after cast — 168 of them, under Major C. E. Dutton."),
               dict(lat=42.9400, lon=-122.0930, d=6, az=150, el=15,
                    cap="The depth figures floating over the water are those casts, read off Plate I: 56 of them, in feet. The deepest reads 1,996. 'To this should be added a small but unknown correction for the stretching of the wire, which will make the true depth of this cast fully 2,000 feet,' Dutton wrote — 'so far as known to me this is the deepest fresh water in the United States.' Modern sonar puts the floor about fifty feet shallower than his 1,996."),
               dict(lat=42.9387, lon=-122.1456, d=3.5, az=210, el=14,
                    cap="Dutton read the bottom as a nearly flat floor with three prominences standing on it. One broke the surface — this cinder cone, Wizard Island; the plummet found the other two submerged, 'one at a depth of about 450 feet, the other at a depth of about 250.' The shoal readings west of the island — 93, 146, 194 feet — are the shallows around it."),
               dict(lat=42.9149, lon=-122.1371, d=4.5, az=200, el=15,
                    cap="Eagle Cove, where Diller told visitors to start: 'by boat from Eagle Cove along the western and northern shore of the lake to Cleetwood and Rugged Crest, returning by way of the crater capping the cinder cone in Wizard Island. It can be made in a day but may require hard rowing.'")]),
    dict(id="giiwas", name="giiwas",
         blurb="The Klamath name for this place, the treaty that took it, and the names the mapmakers borrowed.",
         keys=[dict(lat=42.9420, lon=-122.1064, d=13, az=140, el=16,
                    cap="This is giiwas — Klamath homeland, and a place of power long before it was a park. Klamath oral tradition holds the mountain's destruction as a battle between Llao of the below world and Skell of the above; people were living in this country when it happened, and sandals buried under Mazama ash at Fort Rock, east of here, are older than the eruption."),
               dict(lat=42.9721, lon=-122.1334, d=5, az=300, el=14,
                    cap="Llao Rock is the one Klamath name already lettered on this 1886 sheet. Skell Head, Chaski Bay and the rest came later, borrowed from Klamath stories by William Gladstone Steel as he campaigned the lake into a park — names taken, like the land, without the asking."),
               dict(lat=42.8722, lon=-122.1690, d=8, az=185, el=15,
                    cap="Twenty miles beyond this southern edge stands Fort Klamath, built 1863, and this red road comes up from it along Annie Creek. By the Treaty of Council Grove of 14 October 1864 the Klamath, Modoc and Yahooskin ceded some twenty million acres — this mountain among them — and were confined to a reservation east of here. Four Modoc leaders, Kintpuash among them, were hanged at that fort in October 1873."),
               dict(lat=42.9124, lon=-122.0717, d=5, az=95, el=14,
                    cap="Kerr Notch, named for the topographer whose survey this drape is. Congress terminated the Klamath Tribes in 1954 and restored them in 1986; the Klamath, Modoc and Yahooskin are here now, and giiwas is still theirs to speak for.")]),
    dict(id="roadhead", name="No hotels at the lake",
         blurb="Twenty miles of wagon road from Fort Klamath, numbered camps, and a park two weeks old when this map was drawn.",
         keys=[dict(lat=42.8653, lon=-122.1458, d=6, az=175, el=14,
                    cap="Munson Valley and the Annie Creek road, the only wheeled way in: 'Crater Lake is only 20 miles distant by way of the Anna Creek road,' Diller wrote of Fort Klamath. From Ashland or Medford it was about eighty miles of mountain road by private conveyance."),
               dict(lat=42.9110, lon=-122.1425, d=3.5, az=200, el=14,
                    cap="Victor Rock, the head of that road on the rim. 'At the end of the road, on the rim of Crater Lake, the camping places are fine, but pasture and water are not so abundant nor so easily obtained. There are as yet no hotels nor permanent accommodations for travel at the lake.' The lodge on this rim was still thirteen years off."),
               dict(lat=42.9026, lon=-122.0970, d=5, az=160, el=15,
                    cap="The dashes around the rim are the sheet's own confession: 'Possible pack-train route, but no trail.' Diller's camps are the small numbers along it. Of the ground below Sun Notch he warns that the canyon of Sun Creek 'is difficult to cross, as its western wall is precipitous.'"),
               dict(lat=42.9040, lon=-122.1234, d=6, az=185, el=16,
                    cap="William Gladstone Steel first saw the lake in 1885 and spent seventeen years arguing it into a park; the act was approved 22 May 1902, and Professional Paper 3 came out the same year. The four lines around this drape are that act — 43°04' north, 42°48' south, 122°00' east, 122°16' west, 'having an area of two hundred and forty-nine square miles.'")]),
    dict(id="survey", name="Fitting the statute",
         blurb="No georeferenced base exists for this country in 1902, so the sheet is registered on its own printed net — and then checked.",
         keys=[dict(lat=42.9330, lon=-122.1330, d=22, az=178, el=18,
                    cap="Every other sheet in this gallery leans on a georeferenced quadrangle. There is none here: the oldest staged Crater Lake quads are 1985. So both plates were fitted from the 25 crossings of their own printed 5-minute net — which is also, exactly, the boundary Congress wrote. Diller's geology lands on that net at 1.0 px, Kerr's topography at 1.1 px, about 13 metres of paper."),
               dict(lat=42.9420, lon=-122.1064, d=9, az=250, el=15,
                    cap="Paper is not ground, so the shoreline settles the question. Lift the lake off this drape and off the 1985 Crater Lake West and East quadrangles and the two outlines agree to a median 170 m — nine tenths of Kerr's shoreline within 360 m — with his water 55.2 km² against the modern 54.7. The best rigid shift that would improve the overlap is 270 m; that is his whole error budget, old datum and plane table and a century of paper together."),
               dict(lat=42.8998, lon=-122.1050, d=4, az=170, el=14,
                    cap="Applegate Peak, which Kerr called Vidae Peak and marked 8,228 feet — one foot above his Glacier Peak across the water, which made it, in Diller's text, 'the highest point in the rim of the lake.' The model reads this summit at 8,110. Kerr's vertical simply ran high: he put the lake surface at 6,239 feet where the model reads a flat 6,175."),
               dict(lat=43.0100, lon=-122.2300, d=8, az=300, el=15,
                    cap="The north-west margin is the sheet's soft edge, and Diller says why: Plate I is a composite. The country between 122°00' and 122°15' and between 42°50' and 43°04' came from the Crater Lake special sheet at an inch to the mile; the strips beyond — this one, and the two minutes along the south — were reduced from the Ashland sheet at an inch to four miles.")]),
]

# The 1886 soundings, as printed inside the lake on Plate I:
# (x_px, y_px, depth_ft) on the 300-dpi rasterisation.  Positions were read
# from ruler-grid crops; build.soundings() carries them to the ground through
# the inverse of the plate's own graticule fit.
SOUNDINGS = [
    (1490.5, 1056.5, 1305), (1418.0, 1088.5, 1608), (1175.0, 1101.0, 1100),
    (1347.5, 1097.5, 1700), (1524.5, 1096.5, 995), (1304.5, 1116.5, 1521),
    (1235.5, 1133.5, 1661), (1418.0, 1139.5, 1801), (1178.5, 1147.0, 1787),
    (1364.5, 1147.0, 1521), (1473.0, 1146.0, 1543), (1523.0, 1145.0, 1957),
    (1352.5, 1173.0, 661), (1280.0, 1191.0, 1816), (1215.5, 1204.5, 1804),
    (1338.0, 1210.0, 1676), (1505.5, 1205.5, 1947), (1590.0, 1210.0, 1475),
    (1134.5, 1217.5, 1713), (1047.0, 1236.5, 925), (1458.0, 1235.5, 1947),
    (1309.0, 1253.5, 1859), (1400.0, 1258.0, 1926), (1502.5, 1265.5, 1961),
    (1584.0, 1269.5, 1942), (1476.0, 1295.5, 1996), (1262.0, 1294.0, 1375),
    (1164.5, 1318.5, 470), (1569.5, 1320.0, 1555), (1250.0, 1335.0, 1537),
    (1450.0, 1351.0, 1956), (1221.5, 1387.5, 879), (1448.0, 1379.5, 1915),
    (1552.5, 1379.5, 1744), (1277.0, 1409.5, 1152), (1397.0, 1405.5, 1605),
    (960.0, 1427.5, 194), (1012.0, 1412.0, 146), (1120.5, 1414.0, 462),
    (1216.5, 1430.5, 814), (1465.0, 1419.5, 1818), (1521.5, 1413.5, 1708),
    (1531.0, 1438.0, 1646), (1587.0, 1434.5, 1084), (1078.0, 1450.5, 93),
    (1129.0, 1450.5, 1109), (1418.5, 1461.0, 1754), (1119.5, 1482.5, 1529),
    (1218.5, 1482.5, 1605), (1077.0, 1501.5, 953), (1121.0, 1522.5, 1579),
    (1124.0, 1549.0, 1014), (1228.0, 1549.0, 1203), (1504.0, 1551.0, 1360),
    (1489.0, 1579.0, 1155), (1385.5, 1522.5, 1439),
]
