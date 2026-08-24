"""Named places and the four guided flights for the Nome sheet.

Coordinates are from GNIS (DomesticNames_AK) only.  Peak elevations are the
plates' own printed spot heights (Gerdine's 1904 survey), read from Plate I
and verified against the Terrarium model within the recipe's ±130 m gate;
summits whose printed figure could not be read (Bonanza Hill, Dexter Peak,
North Newton Peak) are left off rather than guessed — Native Hill keeps its
name in the features layer instead.  Tour keys are (lat, lon, distance km,
camera bearing, camera elevation angle).
"""
PEAKS = [  # name, lat, lon, printed feet (plate I), drainage — GNIS coords
    ("Anvil Mountain", 64.5645944, -165.3732445, 1050, "Anvil Creek"),
    ("Newton Peak", 64.5589135, -165.3186319, 1144, "Nome River"),
    ("King Mountain", 64.5954403, -165.3363667, 1204, "Nome River"),
    ("Mount Brynteson", 64.6354852, -165.4053640, 1741, "Snake River"),
    ("Banner Peak", 64.5702831, -165.4268412, 730, "Glacier Creek"),
    ("Army Peak", 64.5381890, -165.1890431, 612, "Osborn Creek"),
    ("Osborn Dome", 64.6603320, -165.1887804, 1679, "Osborn Creek"),
]
CITIES = [  # name, lat, lon, tier (0 = major) — GNIS coords
    ("Nome", 64.5011111, -165.4063889, 0),
    ("Discovery", 64.5333333, -165.4000000, 1),      # GNIS "Discovery (historical)"
    ("Fort Davis", 64.4833333, -165.3166667, 1),     # GNIS "Fort Davis (historical)"
    ("Summit", 64.5758333, -165.3566667, 2),
    ("Perkinsville", 64.5505556, -165.4150000, 2),
    ("Uinuk", 64.4833333, -165.3000000, 2),          # GNIS "Uinuk (historical)"
    ("Hastings Creek", 64.4666667, -165.1000000, 2), # GNIS "(historical)" camp
]
FEATURES = [  # name, lat, lon, kind — GNIS coords except the sound's label
    ("Snake River", 64.4986111, -165.4130556, "water"),
    ("Nome River", 64.4827778, -165.3050000, "water"),
    ("Anvil Creek", 64.5213889, -165.4713889, "water"),
    ("Glacier Creek", 64.5983333, -165.4594444, "water"),
    ("Dexter Creek", 64.5880556, -165.2775000, "water"),
    ("Osborn Creek", 64.5477778, -165.2208333, "water"),
    ("Moonlight Springs", 64.5547931, -165.4095278, "water"),
    ("Seward Ditch", 64.6194444, -165.3161111, "water"),
    ("Norton Sound", 64.4010999, -165.0178232, "region"),  # GNIS prim, in the apron sea
    ("Cape Nome", 64.4375000, -165.0063889, "region"),
    ("Belmont Point", 64.5041667, -165.4180556, "region"),
    ("Native Hill", 64.5450311, -165.2532945, "region"),
]

TOURS = [
    dict(id="anvil", name="Anvil Creek, 1899",
         blurb="Three lucky Swedes on a tundra creek — the claim that called twenty thousand people to the edge of the map.",
         keys=[dict(lat=64.5333, lon=-165.4000, d=6, az=40, el=15,
                    cap="Discovery claim, Anvil Creek. In September 1898 Jafet Lindeberg, Erik Lindblom and John Brynteson — the 'Three Lucky Swedes,' one of them Norwegian — panned coarse gold here and organized the Cape Nome mining district that October."),
               dict(lat=64.5646, lon=-165.3732, d=7, az=200, el=16,
                    cap="Anvil Mountain, 1,050 feet on Gerdine's survey, named for the anvil-shaped tor on its crest. The creek below out-produced every stream on Seward Peninsula — so in 1900 a bought judge, Arthur Noyes, simply handed the claims to a receiver; the Ninth Circuit jailed the ring, and Rex Beach wrote it up as The Spoilers."),
               dict(lat=64.5970, lon=-165.4075, d=5, az=180, el=15,
                    cap="Snow Gulch, off Glacier Creek — gulch ground rich from the grass roots down. The MIOCENE DITCH lettered along the hillside brought Nome River water around dozens of miles of tundra bench to sluice ground like this."),
               dict(lat=64.6355, lon=-165.4054, d=8, az=160, el=16,
                    cap="The map remembers the discoverers: Mount Brynteson for the Swedish coal miner, Lindblom Creek below it for the tailor who had jumped ship. Their Pioneer Mining Company held Anvil against every jumper who argued that immigrants' claims were no claims at all.")]),
    dict(id="beach", name="The Golden Beach, 1900",
         blurb="Gold in the surf sand, free to any shovel — the only rush a steamer ticket could join.",
         keys=[dict(lat=64.5011, lon=-165.4064, d=5, az=70, el=14,
                    cap="July 1899: prospector John Hummel, too sick for the creeks, tried the beach itself — and the tide line was pay dirt. Two thousand people with rockers washed roughly a million dollars out of this sand before freeze-up."),
               dict(lat=64.5042, lon=-165.4181, d=4, az=110, el=14,
                    cap="Below the high-tide line there were no claims to stake and no title to fight over: free ground under mining law. By late June 1900 the steamers had landed some twenty thousand more people onto a canvas city miles long — hotels, thieves, typhoid and all."),
               dict(lat=64.4833, lon=-165.3167, d=6, az=250, el=14,
                    cap="Fort Davis, the Army post at the Nome River mouth, pitched in the summer of 1900 to police a gold camp with hardly any government — soldiers walked the beach, evicted jumpers, and hauled wreckage out of the surf after every blow."),
               dict(lat=64.5150, lon=-165.3300, d=7, az=200, el=15,
                    cap="Behind town the tundra hides older beaches — buried strandlines of higher seas, gold-bearing like the first. The geologic sheet colours the whole plain Qcp, 'creek, bench, and coastal plain deposits': the entire map, read as one placer.")]),
    dict(id="roadstead", name="The Roadstead",
         blurb="No harbor at all: ships anchor a mile out, and everything — coal, pianos, passengers — comes ashore through the surf.",
         keys=[dict(lat=64.4700, lon=-165.4400, d=8, az=45, el=14,
                    cap="Nome's 'port' is an open roadstead. Steamers from Seattle anchored well offshore while lighters and barges ferried every ton through the breakers; in the June rush of 1900 fifty-odd ships lay off this beach at once."),
               dict(lat=64.4986, lon=-165.4131, d=4, az=30, el=15,
                    cap="The Snake River mouth, the only shelter on the sheet — a sandspit lagoon for launches and lighters, with the pumping plant on the spit feeding the beach sluices. Jetties came later; in 1900 even the barges broached in the swash."),
               dict(lat=64.4850, lon=-165.3800, d=7, az=310, el=15,
                    cap="The sea takes back: the storm of 12–13 September 1900 flattened the beachfront and scattered ships and lumber for miles, and another in October 1913 — the year this map was printed — carried off a third of the town."),
               dict(lat=64.4500, lon=-165.3000, d=10, az=300, el=15,
                    cap="From October to June the roadstead is ice: no ship and, before the wire, no word. Mail came a thousand miles by dog team — the trail that carried diphtheria serum behind Togo and Balto in 1925, and that the Iditarod remembers; Balto Creek is on this sheet.")]),
    dict(id="wires", name="Wires and Rails",
         blurb="A three-foot railroad to the diggings, a wireless leap across the Sound — and the Inupiaq homeland all of it stands on.",
         keys=[dict(lat=64.5011, lon=-165.4064, d=5, az=20, el=15,
                    cap="The Wild Goose Railroad, 1900: Charles Lane's three-foot gauge from the beach up to the Anvil Creek claims — ore down, miners up, a dollar a ride. The plate owns up in its corner: 'Railroad unsurveyed; position approximate.'"),
               dict(lat=64.5758, lon=-165.3567, d=5, az=330, el=15,
                    cap="Dexter, Summit and the divide roadhouses at the top of the grade. By 1906 the little line had grown into the Seward Peninsula Railroad, pushing more than eighty miles north toward the Kougarok diggings."),
               dict(lat=64.4970, lon=-165.3900, d=4, az=90, el=14,
                    cap="'WIRELESS STATION,' the sheet notes east of town: from 1903 the Army's WAMCATS system leapt Norton Sound — a 107-mile wireless hop toward St. Michael, then landline and cable to Washington. News that had taken a winter now took a day."),
               dict(lat=64.4833, lon=-165.3000, d=7, az=260, el=15,
                    cap="Uinuk, at the Nome River mouth, was an Inupiaq place long before Fort Davis was pitched beside it. This is Sitŋasuaq — Inupiaq homeland; King Islanders wintered on Nome's beach into the 1960s. They mined, freighted and clothed the camp, and, barred from citizenship until 1924, could not legally hold the claims this map records.")]),
]
