"""Named places and the guided flights for the Rocky Mountain sheet.

Coordinates and feet come from GNIS — the 2021 archive file, which still
carries elevations — and `build.audit_places` re-reads that file at encode
time and refuses to build if a single figure here has drifted from it.
Summits are additionally snapped to the model and DEM-verified; any that
missed by more than 130 m were dropped rather than guessed.  Label points
for features whose GNIS point falls outside the block (the Colorado River,
which is 1,450 miles long) are placed on the course the sheet draws inside
the neat, and are marked below.

Tour keys are (lat, lon, distance km, camera bearing, camera elevation
angle); the bearing is where the camera stands relative to the subject, so
az 180 puts you south of it, looking north.
"""

# GNIS spells a couple of these differently from the label we print
GNIS_NAME = {
    "Lulu City": "Lulu City (historical)",
}

PEAKS = [  # name, lat, lon, feet, range — coordinates and feet from GNIS
    ("Longs Peak",           40.25486, -105.61624, 14262, "Front Range"),
    ("Hagues Peak",          40.48469, -105.64579, 13543, "Mummy Range"),
    ("Chiefs Head Peak",     40.24908, -105.64117, 13540, "Front Range"),
    ("North Arapaho Peak",   40.02660, -105.65066, 13507, "Indian Peaks"),
    ("Fairchild Mountain",   40.46851, -105.66433, 13504, "Mummy Range"),
    ("Apache Peak",          40.05838, -105.65110, 13441, "Indian Peaks"),
    ("Mount Alice",          40.23954, -105.66466, 13313, "Wild Basin"),
    ("Mount Audubon",        40.09900, -105.61630, 13222, "Indian Peaks"),
    ("Copeland Mountain",    40.18194, -105.64636, 13163, "Wild Basin"),
    ("Ogalalla Peak",        40.16999, -105.66689, 13133, "Wild Basin"),
    ("Stones Peak",          40.35431, -105.72042, 12930, "Front Range"),
    ("Mount Richthofen",     40.46947, -105.89432, 12900, "Never Summer Mountains"),
    ("Mount Ida",            40.37180, -105.77936, 12874, "Front Range"),
    ("Howard Mountain",      40.42705, -105.89889, 12805, "Never Summer Mountains"),
    ("Hallett Peak",         40.30284, -105.68583, 12703, "Front Range"),
    ("Specimen Mountain",    40.44457, -105.80850, 12483, "Never Summer Mountains"),
    ("Lulu Mountain",        40.48012, -105.86250, 12218, "Never Summer Mountains"),
    ("Twin Sisters Mountain", 40.28853, -105.51732, 11417, "Estes Valley"),
    ("Deer Mountain",        40.37954, -105.58420, 10016, "Estes Valley"),
]
CITIES = [  # name, lat, lon, tier (0 = major); the ghosts carry no marker of it
    ("Estes Park",   40.37721, -105.52167, 0),
    ("Grand Lake",   40.25221, -105.82307, 1),
    ("Granby",       40.08610, -105.93946, 1),
    ("Allenspark",   40.19443, -105.52555, 2),
    ("Ward",         40.07221, -105.50833, 2),
    ("Meeker Park",  40.23387, -105.53083, 2),
    ("Gaskil",       40.33054, -105.86223, 2),
    ("Lulu City",    40.44554, -105.84807, 2),
    ("Elkdale",      40.04026, -105.88112, 2),
]
FEATURES = [  # name, lat, lon, kind
    ("Rocky Mountain National Park", 40.35547, -105.69731, "park"),
    # water
    # GNIS's point for the Colorado is 1,450 miles downstream, so this label
    # sits on the blue line the sheet itself draws, traced in the Kawuneeche
    ("Colorado River",       40.35500, -105.86450, "water"),
    ("Grand Lake",           40.24357, -105.81465, "water"),
    ("Shadow Mountain Lake", 40.22755, -105.84249, "water"),
    ("Lake Granby",          40.15553, -105.84844, "water"),
    ("Grand Ditch",          40.41943, -105.86390, "water"),
    ("Poudre Lake",          40.42202, -105.80864, "water"),
    ("Bear Lake",            40.31319, -105.64824, "water"),
    ("Chasm Lake",           40.25840, -105.60484, "water"),
    ("Tyndall Glacier",      40.30471, -105.68945, "water"),
    ("Chasm Falls",          40.41676, -105.67262, "water"),
    # regions
    ("Never Summer Mountains", 40.42827, -105.90677, "region"),
    ("Indian Peaks",         40.05360, -105.64667, "region"),
    ("Kawuneeche Valley",    40.25144, -105.86725, "region"),
    ("Forest Canyon",        40.35015, -105.66420, "region"),
    ("Trail Ridge",          40.40825, -105.71053, "region"),
    ("Moraine Park",         40.35332, -105.60278, "region"),
    ("Horseshoe Park",       40.40443, -105.62472, "region"),
    ("Wild Basin",           40.20137, -105.61195, "region"),
    ("Milner Pass",          40.41971, -105.81140, "region"),
    ("Fall River Pass",      40.44054, -105.75473, "region"),
    ("La Poudre Pass",       40.47665, -105.82334, "region"),
    ("Alva B Adams Tunnel",  40.29165, -105.67278, "region"),
]

TOURS = [
    dict(id="peak", name="The Peak",
         blurb="Longs Peak from every side — the east face, the Boulder Field, and the bench mark that reads 14,255.",
         keys=[dict(lat=40.25486, lon=-105.61624, d=10, az=155, el=16,
                    cap="Longs Peak and Mount Meeker, the pair the Arapaho called Neníisótoyóú'u, the Two Guides — visible from a hundred miles out on the plains. Major Stephen Long saw them in 1820 and never came closer; the name stuck anyway."),
               dict(lat=40.25840, lon=-105.60484, d=5, az=100, el=14,
                    cap="Chasm Lake under the east face — two thousand four hundred feet of it, from the water to the summit. The sheer upper wall, the Diamond, went unclimbed until David Rearick and Bob Kamps went up it in August 1960. The sheet draws cliff hachures here and says nothing more."),
               dict(lat=40.26082, lon=-105.62111, d=6, az=30, el=15,
                    cap="The Boulder Field, lettered on the sheet, and the Keyhole notch above it at about 13,150 feet. John Wesley Powell's party made the first recorded ascent on 23 August 1868, William Byers of the Rocky Mountain News among them; in January 1925 Agnes Vaille died of exposure just below here after the first winter climb of the east face, and the stone shelter at the Keyhole is her memorial."),
               dict(lat=40.25486, lon=-105.61624, d=4, az=250, el=15,
                    cap="The summit bench mark on this sheet reads 14,255 feet. GNIS now carries 14,262 and the modern survey 14,259 — three answers, a century apart, to the same question about the same rock.")]),
    dict(id="resort", name="The Resort Era",
         blurb="Joel Estes' cattle valley, an Irish earl's private hunting park, F. O. Stanley's hotel — and the park act of 26 January 1915.",
         keys=[dict(lat=40.37721, lon=-105.52167, d=8, az=95, el=14,
                    cap="Estes Park. Joel Estes drove cattle into this valley in 1860 and sold out in 1866 — too cold to winter. By 1874 the Earl of Dunraven had assembled some 15,000 acres of it through hired homestead claimants, and ran the whole valley as a private hunting park; his Estes Park Hotel opened in 1877 on a site Albert Bierstadt picked for him."),
               dict(lat=40.37200, lon=-105.51500, d=6, az=250, el=14,
                    cap="F. O. Stanley came in 1903 for tuberculosis, recovered, and stayed. His Stanley Hotel opened in 1909, lit by his own hydro plant, with Stanley Steamer mountain wagons hauling guests up from the railhead at Lyons — the machine that made this valley a resort instead of a ranch."),
               dict(lat=40.40443, lon=-105.62472, d=7, az=100, el=14,
                    cap="Horseshoe Park, where the park was dedicated on 4 September 1915 — eight months after Woodrow Wilson signed the act on 26 January. Enos Mills, innkeeper and Longs Peak guide, had argued for it since 1909 and is fairly called its father."),
               dict(lat=40.35332, lon=-105.60278, d=8, az=110, el=15,
                    cap="Moraine Park: a glacial trough floored with meadow between two lateral moraines, drawn here with a village of cottages, a lodge and a ranger station along its north side, and the park boundary threaded around the private tracts. The Park Service bought the inholdings out over the decades that followed and took the buildings down; the sheet is the record of what stood.")]),
    dict(id="fallriver", name="Fall River Road, 1920",
         blurb="The first road across the range — convict crews, sixteen switchbacks, and the highway that replaced it twelve years later.",
         keys=[dict(lat=40.40900, lon=-105.63500, d=6, az=95, el=14,
                    cap="Horseshoe Park and the foot of Fall River Road. Work began in 1913 with convict labour from the state penitentiary at Cañon City, and the road opened in 1920 — the first way over the range by automobile. The red road net on this drape is the National Park Service's 1940 addition, printed over the 1915 survey."),
               dict(lat=40.41676, lon=-105.67262, d=4, az=75, el=14,
                    cap="Chasm Falls and the switchbacks — sixteen of them, gravel, no guard rails, grades to sixteen per cent, and a rule against stopping. Once Trail Ridge Road took the traffic this one was made one-way uphill, and one-way uphill it stays."),
               dict(lat=40.44054, lon=-105.75473, d=7, az=115, el=15,
                    cap="Fall River Pass, 11,762 feet, where the old road tops out on the tundra. Crossfade to the 1915 quadrangle and the road is simply not there: the survey of 1912–13 ends the wagon track at Horseshoe Falls and lets a dashed trail go on, because in 1915 that is where it ended."),
               dict(lat=40.40825, lon=-105.71053, d=12, az=185, el=16,
                    cap="Trail Ridge, and the road that took the traffic: begun 1929, over the top in 1932, through to Grand Lake in 1933 — four miles of it above 12,000 feet. It follows the Ute Trail, which is lettered on both of these sheets and is older than either.")]),
    dict(id="twoguides", name="Ute and Arapaho Country",
         blurb="Say it plainly: this is Núuchi-u and Hinono'eino' homeland, and the names on the sheet were collected in 1914 from two men who had been made to leave.",
         keys=[dict(lat=40.39000, lon=-105.70000, d=10, az=205, el=16,
                    cap="Trail Ridge, with the Ute Trail lettered along it in brown on both sheets. This is the Núuchi-u — Ute — high road between the mountain parks, and the Arapaho used it too; the stone game-drive walls near Timberline Pass are thousands of years old."),
               dict(lat=40.42827, lon=-105.90677, d=12, az=105, el=16,
                    cap="The Never Summer Mountains. In July 1914 the Colorado Mountain Club brought two elderly Arapaho men from the Wind River Reservation — Gun Griswold and Sherman Sage, with Tom Crispin interpreting — to ride this country and say what it had been called. Oliver Toll wrote it down; Ni-chebe-chii, 'never no summer,' is the range's name in that notebook, and it is the range's name on the map today."),
               dict(lat=40.25144, lon=-105.86725, d=12, az=100, el=16,
                    cap="Kawuneeche — an Arapaho word for 'coyote valley', from the same list of names, and now the official one for the Colorado's headwater trench. The men who gave it were speaking about a country they had been made to leave: the Northern Arapaho were settled on the Wind River Reservation in 1878, and Toll's notebook is dated 1914."),
               dict(lat=40.24357, lon=-105.81465, d=9, az=75, el=15,
                    cap="Grand Lake, and the plain accounting. The 1851 Fort Laramie treaty recognised Arapaho and Cheyenne country along this Front Range; the 1861 Treaty of Fort Wise shrank it to a strip on the Arkansas, and the Sand Creek massacre of November 1864 settled the argument by force. West of the Divide it was the Utes: Middle Park was signed away in the treaty of 1868, and the last bands were marched out of Colorado to Utah in 1881. The park was laid over both, in 1915.")]),
    dict(id="headwaters", name="The Headwaters",
         blurb="Lulu City's silver, the Grand Ditch, and the year the Colorado River was plumbed under the Continental Divide.",
         keys=[dict(lat=40.44554, lon=-105.84807, d=5, az=175, el=14,
                    cap="Lulu City, platted in 1879 on the infant Colorado — then still called the Grand. Benjamin Burnett named it for his daughter; it held a post office from 1880 to 1883, and the ore assayed too poor to pay the haul. By 1884 it was gone. Only the names stayed — Lulu Creek, Lulu Mountain, and a cemetery."),
               dict(lat=40.41943, lon=-105.86390, d=7, az=85, el=15,
                    cap="The Grand Ditch, begun 1890 and extended by hand crews until 1936 — fourteen miles of contour ditch scratched across the Never Summers' east face to carry snowmelt over La Poudre Pass to the plains. It is drawn here as a contour that carries water, and it takes that water out of the Colorado before the Colorado has properly begun."),
               dict(lat=40.24000, lon=-105.83000, d=11, az=35, el=15,
                    cap="Grand Lake, Shadow Mountain Lake and Lake Granby. Now crossfade to the 1915 quadrangle: the two lower lakes vanish and the valley floor comes back — Stillwater, Sleepy Hollow School, the Ranger Station, a river meandering through hay meadow. Shadow Mountain filled in 1946, Granby by 1950."),
               dict(lat=40.29165, lon=-105.67278, d=13, az=280, el=17,
                    cap="Under this ridge runs the Alva B. Adams Tunnel — 13.1 miles bored through the Continental Divide between 1940 and 1944, delivering its first water east in 1947. The park's headwaters have been an eastern-slope water supply ever since, and the 1951 printing shows the reservoirs stencilled over contours that still map the meadows they drowned.")]),
]
