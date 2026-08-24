"""Named places and the guided flights for the Big Bend sheet.

Coordinates and feet come from GNIS — the frozen 2021 archive file, which
still carries elevations — and `build.audit_places` re-reads that file at
encode time and refuses to build if a single figure here has drifted from
it.  Summits are additionally snapped to the model and DEM-verified; any
that missed by more than 130 m of their GNIS feet, or that snapped onto a
taller neighbour more than 700 m away, were dropped rather than guessed —
Casa Grande Peak, Ward Mountain, Burro Mesa and The Solitario all failed
that second test (their GNIS points sit 1.2–1.5 km from the highest ground
within the snap window) and are named only in the flights.

Nothing on the Mexican bank is labelled: GNIS is a United States gazetteer,
and Boquillas del Carmen, Santa Elena and the presidio at San Vicente have
no record in it.  They are named in the flights instead, where the text can
say plainly whose ground they are.

Tour keys are (lat, lon, distance km, camera bearing, camera elevation
angle); the bearing is where the camera stands relative to the subject, so
az 180 puts you south of it, looking north.
"""

# GNIS spells a few of these with a suffix we do not want printed on a map
GNIS_NAME = {
    "Glenn Springs": "Glenn Springs (historical)",
    "La Coyota": "La Coyota (historical)",
    "Ore Terminal": "Ore Terminal Aerial Tramway",
}
# Label points placed on the course the sheets draw inside the neat, because
# the feature's own GNIS point is far outside the block: the Rio Grande is
# 1,900 miles long and its record sits at the Gulf.
LABEL_ONLY = {"Rio Grande"}

PEAKS = [  # name, lat, lon, feet, range — coordinates and feet from GNIS
    ("Emory Peak",         29.24607, -103.30528, 7798, "Chisos Mountains"),
    ("Lost Mine Peak",     29.27556, -103.25839, 7523, "Chisos Mountains"),
    ("Pulliam Peak",       29.29326, -103.29482, 6847, "Chisos Mountains"),
    ("Panther Peak",       29.29818, -103.23905, 6411, "Chisos Mountains"),
    ("Sierra Quemada",     29.18908, -103.30962, 6040, "south of the Chisos"),
    ("Sue Peaks",          29.42056, -102.98016, 5860, "Sierra del Carmen"),
    ("Paisano Peak",       29.45411, -103.45945, 5456, "Christmas Mountains"),
    ("Elephant Tusk",      29.15736, -103.26767, 5249, "south of the Chisos"),
    ("Stuarts Peak",       29.49486, -103.01981, 5092, "Sierra del Carmen"),
    ("Fresno Peak",        29.42714, -103.83714, 5066, "the Solitario"),
    ("Hen Egg Mountain",   29.47408, -103.59130, 4984, "Terlingua country"),
    ("Panther Mountain",   29.42130, -103.98297, 4924, "Sauceda country"),
    ("Punta de la Sierra", 29.10603, -103.31767, 4875, "south of the Chisos"),
    ("Nugent Mountain",    29.26219, -103.17186, 4787, "Tornillo country"),
    ("Croton Peak",        29.37232, -103.34808, 4600, "Burro Mesa country"),
    ("Goat Mountain",      29.18758, -103.40628, 4600, "Castolon country"),
    ("Chilicotal Mountain", 29.20429, -103.15377, 4104, "Tornillo country"),
    ("Mariscal Mountain",  29.02523, -103.14975, 3937, "the bend"),
    ("Mesa de Anguila",    29.21103, -103.68851, 3888, "Santa Elena country"),
    ("Mule Ear Peaks",     29.14354, -103.40230, 3875, "Castolon country"),
    ("Talley Mountain",    29.13576, -103.16655, 3707, "the bend"),
    ("Cerro Castellan",    29.14464, -103.49739, 3274, "Castolon country"),
]
CITIES = [  # name, lat, lon, tier (1 = the larger places, 2 = ranches,
            #                     crossings, camps and mines)
    ("Terlingua",            29.32159, -103.61602, 1),
    ("Study Butte",          29.31825, -103.53074, 1),
    ("Lajitas",              29.26159, -103.77658, 1),
    ("Castolon",             29.13326, -103.51435, 1),
    ("Panther Junction",     29.32853, -103.20517, 1),
    ("Rio Grande Village",   29.18326, -102.96211, 1),
    ("Terlingua Abaja",      29.19353, -103.60741, 2),
    ("La Coyota",            29.15215, -103.54824, 2),
    ("Santa Elena Crossing", 29.12159, -103.52407, 2),
    ("Buenos Aires",         29.08520, -103.46907, 2),
    ("San Vicente Crossing", 29.13021, -103.01489, 2),
    ("Solis",                29.06132, -103.09961, 2),
    ("Woodsons",             29.00632, -103.29490, 2),
    ("Johnson Ranch",        29.02521, -103.37156, 2),
    ("Glenn Springs",        29.16104, -103.14739, 2),
    ("Hot Springs",          29.18215, -102.99211, 2),
    ("Boquillas Crossing",   29.18882, -102.94544, 2),
    ("Ore Terminal",         29.21882, -102.94350, 2),
    ("Stillwell Crossing",   29.39881, -102.81877, 2),
    ("McKinney Springs",     29.38798, -103.07628, 2),
    ("Sauceda Ranch",        29.46991, -103.95797, 2),
    ("Mariscal Mine",        29.09544, -103.18775, 2),
    ("Mariposa Mine",        29.31825, -103.69463, 2),
    ("Lone Star Mine",       29.31797, -103.71824, 2),
]
FEATURES = [  # name, lat, lon, kind
    ("Rio Grande",                29.14300, -103.56800, "water"),   # label point
    ("Santa Elena Canyon",        29.16547, -103.61212, "water"),
    ("Mariscal Canyon",           29.01591, -103.10453, "water"),
    ("Boquillas Canyon",          29.21107, -102.88612, "water"),
    ("Terlingua Creek",           29.16492, -103.60991, "water"),
    ("Tornillo Creek",            29.17743, -102.99711, "water"),
    ("Fresno Canyon",             29.28227, -103.85501, "water"),
    ("Comanche Creek",            29.24798, -103.77519, "water"),
    ("Boot Canyon",               29.25138, -103.26818, "water"),
    ("Pine Canyon",               29.25479, -103.21695, "water"),
    ("Chisos Mountains",          29.20073, -103.34231, "region"),
    ("Sierra del Carmen",         29.39863, -102.99571, "region"),
    ("Sierra del Caballo Muerto", 29.29417, -102.92736, "region"),
    ("Christmas Mountains",       29.44064, -103.44155, "region"),
    ("Blue Range",                29.43658, -103.76547, "region"),
    ("The Basin",                 29.27520, -103.30462, "region"),
    ("Laguna Meadow",             29.24409, -103.31157, "region"),
    ("Tornillo Flat",             29.43103, -103.13767, "region"),
    ("Reed Plateau",              29.31048, -103.63185, "region"),
    ("Green Gulch",               29.36537, -103.20020, "region"),
    ("Backbone Ridge",            29.14314, -103.27319, "region"),
    ("Ernst Valley",              29.19489, -102.92314, "region"),
]

TOURS = [
    dict(id="canyons", name="Three canyons",
         blurb="Santa Elena, Mariscal, Boquillas — the river saws through three limestone blocks in eighty miles, and in 1899 a Geological Survey party rowed all three.",
         keys=[dict(lat=29.16547, lon=-103.61212, d=7, az=40, el=14,
                    cap="Santa Elena Canyon: fifteen hundred feet of Cretaceous limestone with a channel at the bottom narrow enough to touch both walls. Texas on the right hand, Chihuahua on the left — and the 1903 Terlingua sheet draws the Texas rim in hundred-foot contours and leaves Mexico as blank paper."),
               dict(lat=29.01591, lon=-103.10453, d=8, az=340, el=14,
                    cap="Mariscal Canyon, the turn of the bend and the southernmost water on the sheet — the printed neat line runs along 29°00′, barely a mile below this cut. Mariscal Mountain above it is a plunging anticline of the same limestone, sawn through the middle."),
               dict(lat=29.21107, lon=-102.88612, d=8, az=250, el=14,
                    cap="Boquillas Canyon, where the river leaves the block eastward between the Sierra del Carmen and the Dead Horse Mountains. The village on the Coahuila bank is Boquillas del Carmen; the 1903 sheet letters it simply Boquillas and carries its contours across the boundary into Mexico."),
               dict(lat=29.18215, lon=-102.99211, d=6, az=140, el=15,
                    cap="In October 1899 Robert T. Hill and five men rowed three flat-bottomed boats from Presidio to Langtry — some 350 miles of river almost no outsider had seen — and published the first full description of these canyons. The topographers came in the next seasons; these two sheets are what they found.")]),
    dict(id="chisos", name="The Chisos",
         blurb="A sky island in the Chihuahuan Desert: seven thousand eight hundred feet of mountain with pine, oak and maple on top.",
         keys=[dict(lat=29.24607, lon=-103.30528, d=6, az=200, el=16,
                    cap="Emory Peak, 7,798 feet by GNIS — the roof of the sheet and of the park. It carries the name of William H. Emory, who ran the United States side of the boundary survey that made this river a border after the treaty of 1848."),
               dict(lat=29.27520, lon=-103.30462, d=5, az=100, el=14,
                    cap="The Basin, the bowl inside the range, with Casa Grande and Pulliam Peak on its rim. In 1903 the surveyors show a trail in and a spring or two; the road, the lodge and the campground are Civilian Conservation Corps work of 1934–42, and they show on the 1985 sheet in red."),
               dict(lat=29.25138, lon=-103.26818, d=5, az=150, el=15,
                    cap="Boot Canyon: Arizona cypress, Mexican drooping juniper and bigtooth maple, a woodland stranded up here when the ice age ended and the desert closed in below. The Colima warbler nests in this canyon and nowhere else in the United States."),
               dict(lat=29.27556, lon=-103.25839, d=5, az=70, el=16,
                    cap="Lost Mine Peak, named for a Spanish mine of legend that no one has found. The range itself carries the name of the Chisos people, who lived in this desert when the Spanish came and were killed, enslaved or absorbed by the mid-1700s; the Mescalero Apache held these heights after them, into the 1880s.")]),
    dict(id="quicksilver", name="Terlingua quicksilver",
         blurb="Cinnabar on the Terlingua flats: a company town, three camps, and mercury that mattered in two world wars.",
         keys=[dict(lat=29.32159, lon=-103.61602, d=5, az=210, el=14,
                    cap="Terlingua. Howard E. Perry organised the Chisos Mining Company here in 1903 — the year the surveyors were on this ground — and built a company town around his shafts. The quadrangle was surveyed in 1902–03 in cooperation with the University of Texas Mineral Survey, which is why a desert 30-minute sheet exists this early at all."),
               dict(lat=29.31825, lon=-103.69463, d=5, az=160, el=14,
                    cap="The Mariposa and the Lone Star, west of town: cinnabar roasted in retorts, mercury run off into iron flasks of seventy-six pounds. For two decades the Terlingua district was one of the country's chief sources of quicksilver, and the ore ran out about when Perry's company failed in 1942."),
               dict(lat=29.31825, lon=-103.53074, d=5, az=250, el=14,
                    cap="Study Butte, the second camp — named for Will Study, who ran the Big Bend Cinnabar mine here from 1902. The 1903 sheet letters California Hill and Fossil Knobs beside it, and the wagon roads that hauled the flasks eighty miles north to the railroad at Alpine."),
               dict(lat=29.09544, lon=-103.18775, d=5, az=20, el=14,
                    cap="The Mariscal Mine, thirty miles southeast of Terlingua on the bend itself, worked in bursts from 1900 to 1943. Its condensers and adobe walls are the best-preserved quicksilver works in Texas; mercury poisoning was part of the wage, and the ruins are a park historic district now.")]),
    dict(id="crossings", name="The crossings",
         blurb="A river that was a road: the Comanche war trail, the vados, the farm villages on the floodplain, and one night in May 1916.",
         keys=[dict(lat=29.26159, lon=-103.77658, d=8, az=110, el=15,
                    cap="Lajitas, the flat ford at the west edge of the sheet. For a century the Comanche War Trail came down to the river here — the raiding road into Chihuahua and Coahuila, ridden hardest in the 1840s and 1850s under the September moon. The 1903 sheet still letters Comanche Spring and Comanche Creek along its line."),
               dict(lat=29.13021, lon=-103.01489, d=6, az=330, el=14,
                    cap="San Vicente. Spain raised a presidio on the Coahuila bank in 1774, one of a line of forts meant to stop exactly those raids, and abandoned it within a decade. The crossing outlived the fort by two hundred years; the village of San Vicente is still over there, unlabelled here because GNIS is a United States gazetteer."),
               dict(lat=29.14187, lon=-103.52518, d=6, az=200, el=14,
                    cap="Castolon, La Coyota, Terlingua Abaja, Santa Elena Crossing — Mexican-American farming villages working the floodplain in cotton, corn and alfalfa. The Army built adobe barracks at Castolon in 1919–20 for a border garrison that hardly came; the La Harmonia store moved in in 1921 and traded with both banks until the park bought it out."),
               dict(lat=29.16104, lon=-103.14739, d=6, az=90, el=14,
                    cap="Glenn Springs, 5 May 1916: raiders out of Mexico attacked the candelilla wax works and the nine cavalrymen guarding it, killing three soldiers and a seven-year-old boy. The same night a second party looted the store at Boquillas and carried off two Americans. Punitive columns rode into Coahuila, and the border stayed militarised for years.")]),
    dict(id="park", name="Eighty-two years",
         blurb="Pull the layer slider: the same desert in 1903 plane-table contours and in the 1984–85 metric sheets, with a national park in between.",
         keys=[dict(lat=29.32853, lon=-103.20517, d=6, az=200, el=14,
                    cap="Panther Junction, the park headquarters. On the 1903 sheet there is nothing here at all — Lone Mountain, Green Gulch and a wagon track. Big Bend was authorised by Congress in 1935 and established on 12 June 1944, after the State of Texas bought the land and deeded it to the United States."),
               dict(lat=29.36537, lon=-103.20020, d=6, az=180, el=15,
                    cap="Green Gulch, the way up into the Basin: a trail in 1903, a paved switchback road in red on the 1985 sheet. Civilian Conservation Corps crews cut the first road up it in the late 1930s, largely by hand, from a camp in the Basin."),
               dict(lat=29.18326, lon=-102.96211, d=6, az=300, el=14,
                    cap="Rio Grande Village — farms and a store when the sheet was drawn, a campground now. Just upstream J. O. Langford filed on the hot springs in 1909 and ran a bathhouse and store until 1942; the 105° water still fills his foundation at the mouth of Tornillo Creek. The ore tramway from the Puerto Rico mine in Coahuila crossed the river below here after 1909, six miles of cable buckets to a terminal on the Texas side."),
               dict(lat=29.08000, lon=-103.55000, d=9, az=20, el=15,
                    cap="Look south of the river on the west half of the sheet: blank paper. The 1903 Terlingua sheet stopped at the boundary line, while the Chisos sheet carried its contours miles into Coahuila. Eighty-two years later the 1985 metric sheet letters INTERNATIONAL DATA NOT AVAILABLE across the same ground — a border drawn by what the map declines to say.")]),
]
