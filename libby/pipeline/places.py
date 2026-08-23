"""Named places and the four guided flights for the Libby sheet.  Peak
coordinates from Wikipedia infoboxes; the pipeline snaps each to the nearest
summit in the model and warns when they disagree by over 250 m.  Tour keys
are (lat, lon, distance km, camera bearing, camera elevation angle).
"""
PEAKS = [  # name, lat, lon, feet, range
    ("Snowshoe Peak", 48.2343, -115.6985, 8738, "Cabinet Mountains"),
    ("Elephant Peak", 48.0884, -115.6325, 7938, "Cabinet Mountains"),
]
CITIES = [  # name, lat, lon, tier (0 = major)
    ("Libby", 48.3885, -115.5560, 0),
    ("Troy", 48.4646, -115.8887, 1),
    ("Jennings", 48.3550, -115.3380, 2),
]
FEATURES = [  # name, lat, lon, kind
    ("Kootenai River", 48.4250, -115.7200, "water"),
    ("Kootenai Falls", 48.4545, -115.7680, "water"),
    ("Libby Creek", 48.2400, -115.5600, "water"),
    ("Fisher River", 48.3200, -115.3350, "water"),
    ("Howard Lake", 48.1560, -115.5320, "water"),
    ("Cabinet Mountains", 48.1900, -115.7000, "region"),
    ("Purcell Mountains", 48.5000, -115.9300, "region"),
    ("Vermiculite Mountain", 48.4620, -115.4380, "region"),
]

TOURS = [
    dict(id="snowshoe", name="The Snowshoe",
         blurb="The Cabinets rise seven thousand feet off the Kootenai, and the silver-lead vein under them paid for the town.",
         keys=[dict(lat=48.300, lon=-115.620, d=26, az=200, el=20,
                    cap="The Cabinet front — ice-carved, cirque-bitten, the same Belt rocks Gibson colours across this sheet."),
               dict(lat=48.2343, lon=-115.6985, d=12, az=120, el=16,
                    cap="Snowshoe Peak, 8,738 ft, highest of the Cabinets, over the hanging cirque of Leigh Lake."),
               dict(lat=48.205, lon=-115.600, d=10, az=150, el=14,
                    cap="The Snowshoe vein — silver and lead from 1889; Gibson keyed every working to his printed List of Mines."),
               dict(lat=48.156, lon=-115.532, d=12, az=90, el=15,
                    cap="Howard Lake and the Libby Creek placers, panned since 1867 — the gold was modest; the country was not.")]),
    dict(id="kootenai", name="The Kootenai",
         blurb="Montana's biggest river by volume, and nearly its lowest ground — a rainforest trench through the sheet's north.",
         keys=[dict(lat=48.3885, lon=-115.5560, d=16, az=160, el=15,
                    cap="Libby, on the Kootenai — sawmill town and Great Northern division point from 1892."),
               dict(lat=48.4545, lon=-115.7680, d=10, az=110, el=13,
                    cap="Kootenai Falls, where the river drops through bedrock — a sacred place of the Ktunaxa, never dammed."),
               dict(lat=48.4646, lon=-115.8887, d=14, az=70, el=15,
                    cap="Troy, near the state's lowest elevation — barely 1,800 feet, in the wet cedar country."),
               dict(lat=48.420, lon=-115.600, d=24, az=250, el=18,
                    cap="Upstream, the trench fills with the silts of glacial Lake Kootenai — pale on Gibson's sheet.")]),
    dict(id="colors", name="Reading the Colours",
         blurb="A geologic map is an argument: Belt rocks, granite stocks, and veins exactly where the two meet.",
         keys=[dict(lat=48.250, lon=-115.750, d=30, az=180, el=24,
                    cap="Gibson's palette: Precambrian Belt argillites and quartzites — the same stack that builds Glacier Park."),
               dict(lat=48.280, lon=-115.660, d=14, az=210, el=16,
                    cap="Granite stocks in warm pink — the Dry Creek and Vermilion intrusions that drove hot fluids through the rock."),
               dict(lat=48.210, lon=-115.570, d=12, az=140, el=15,
                    cap="The vein symbols cluster along contacts and faults; each number keys to the mines list printed beside the map."),
               dict(lat=48.060, lon=-115.680, d=22, az=190, el=18,
                    cap="South rim of the sheet — the Vermilion country, prospected hard and rarely rich.")]),
    dict(id="rainy", name="Rainy Creek",
         blurb="Past the sheet's east edge, an alkaline stock carries vermiculite — and Libby's long reckoning.",
         keys=[dict(lat=48.440, lon=-115.500, d=16, az=120, el=16,
                    cap="Northeast of town, Rainy Creek drains an odd alkaline intrusion — mined for vermiculite from the 1920s."),
               dict(lat=48.462, lon=-115.437, d=10, az=100, el=14,
                    cap="Vermiculite Mountain. The ore that insulated America's attics carried tremolite asbestos; Libby's miners and their families are still paying for it."),
               dict(lat=48.410, lon=-115.490, d=14, az=200, el=15,
                    cap="The 1948 sheet records the workings without a word of warning — no one had written that word yet."),
               dict(lat=48.3885, lon=-115.5560, d=18, az=90, el=16,
                    cap="Back down to town: company, courthouse, clinic — and a map that only ever told the geology.")]),
]
