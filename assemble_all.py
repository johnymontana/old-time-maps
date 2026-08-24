#!/usr/bin/env python3
"""Assemble every sheet and the gallery that fronts them.

    python3 assemble_all.py

Runs each sheet's src/assemble.py (pure stdlib, like this file), collects the
served builds under dist/<sheet>/, and writes dist/index.html — the landing
page.  This is what vercel.json runs; any static host works the same way.
"""
import os, shutil, subprocess, sys

ROOT = os.path.dirname(os.path.abspath(__file__))
DIST = os.path.join(ROOT, 'dist')

SHEETS = [  # gallery order: oldest sheet first
    dict(d='gold', title='The Gold Regions', era='W.W. de Lacy · 1865',
         blurb='The first map of Montana Territory, drawn for its First '
               'Legislature — every worked placer gulch hatched in red — '
               'with every gold and silver producer recorded since.',
         credit='Library of Congress'),
    dict(d='missouri', title='The Head of Navigation', era='U.S. Geological Survey · 1886 & 1890',
         blurb='The Great Falls and Fort Benton degree sheets joined — the '
               'five falls, the portage, the Marias junction and the '
               'steamboat levee — with the 1890 Cascade County map one '
               'layer behind and the river’s landmarks as data.',
         credit='USGS · Library of Congress'),
    dict(d='paradise', title='The Livingston Sheet', era='U.S. Geological Survey · Folio 1 · 1894',
         blurb='The first folio of the Geologic Atlas of the United States — '
               'Paradise Valley, Tom Miner Basin, the Boulder and the '
               'Crazies in fever colours, with its 1891 topography one '
               'layer behind and the corridor’s mines riding the terrain.',
         credit='U.S. Geological Survey'),
    dict(d='yellowstone', title='Yellowstone in Folio', era='U.S. Geological Survey · Hague, 1896',
         blurb='The four quadrangle sheets of the first national park — '
               'Hague’s geologic folio in full colour, joined over the '
               'terrain, with its 1911 engraved topography one layer behind '
               'and seventy named geysers riding the plateau.',
         credit='U.S. Geological Survey'),
    dict(d='glacier', title='Glacier in Contours', era='U.S. Geological Survey · surveyed 1900–1912',
         blurb='The engraved sheet of Glacier National Park, registered '
               'against its own survey’s quadrangles, with the glaciers '
               'at their Little-Ice-Age peak and in 2015 riding the terrain.',
         credit='Library of Congress'),
    dict(d='bitterroot', title='The Bitterroot', era='U.S. Geological Survey · 1901 & 1912',
         blurb='The Hamilton and Missoula quadrangles joined — the valley '
               'end to end, mission country to the Hellgate — with '
               'Leiberg’s 1898 forest survey one layer behind and the '
               'strandlines of Glacial Lake Missoula on the hills.',
         credit='U.S. Geological Survey'),
    dict(d='front', title='The Rocky Mountain Front', era='U.S. Geological Survey · 1903–1920',
         blurb='Four quadrangles of the overthrust wall — Sun River to Birch '
               'Creek, the reefs against the plains, half of it the '
               'Blackfeet Nation — with Ayres’ 1899 reserve survey riding '
               'one layer behind.',
         credit='U.S. Geological Survey'),
    dict(d='rails', title='Montana by Rail', era='Rand McNally · Cram · 1884 & 1912',
         blurb='Two railroad maps of the whole state on one slider — the '
               'lone Northern Pacific of 1884 against the four-route web of '
               '1912 — on the montana sheet’s terrain, with the passes, '
               'tunnels and the Gold Creek last spike as data.',
         credit='Internet Archive · Library of Congress'),
    dict(d='flathead', title='The Flathead Country', era='Corps of Engineers, U.S. Army · 1920 & 1943',
         blurb='Flathead Lake and its valley — Somers, Bigfork, Kalispell, '
               'Whitefish — on two Progressive Military Map sheets joined at '
               'the 48th parallel, with the 1908 county map one layer behind.',
         credit='USGS Historical Topographic Map Collection'),
    dict(d='libby', title='The Libby Quadrangle', era='U.S. Geological Survey · Gibson, 1948',
         blurb='The Cabinet Mountains’ silver-lead district in colour — '
               'Gibson’s geologic sheet over its 1932 base, with fifty '
               'recorded mines riding the terrain as data.',
         credit='U.S. Geological Survey'),
    dict(d='montana', title='Montana in Relief', era='Allan Cartography · 1991',
         blurb='The shaded-relief sheet that taught a generation of Montanans '
               'what their state looks like, draped over the elevation model '
               'it was drawn to describe.',
         credit='American Geographical Society Library, UWM'),
    dict(d='tacoma', g='Washington', title='Tacoma: Ice and Iron', era='U.S. Geological Survey · 1897–1900',
         blurb='Bailey Willis reads the ice sheet that dug Puget Sound, on '
               'the folio sheet of the Northern Pacific’s terminus country — '
               'with the 1900 timber-classification plate one layer behind '
               'and the Wilkeson coal district as data.',
         credit='U.S. Geological Survey'),
    dict(d='coeurdalene', g='Idaho', title='The Coeur d’Alene', era='U.S. Geological Survey · Ransome & Calkins, 1908',
         blurb='The richest silver-lead district in America — Professional '
               'Paper 62’s geology over the Survey’s own special map, with '
               'the great lodes riding the terrain and the labor wars and '
               'the Big Burn said plainly.',
         credit='U.S. Geological Survey'),
    dict(d='silverton', g='Colorado', title='The Silverton Folio', era='U.S. Geological Survey · Cross, Howe & Ransome, 1905',
         blurb='Every vein, tunnel and mill of the San Juan caldera country '
               'on the folio’s economic sheet, its areal geology one '
               'crossfade behind — narrow-gauge country, high and deep.',
         credit='U.S. Geological Survey'),
    dict(d='nome', g='Alaska', title='Nome, the Golden Beach', era='U.S. Geological Survey · Bulletin 533 · 1904–13',
         blurb='The only gold rush a steamer ticket could join: the Nome '
               'quadrangle’s 1913 geology over its 1904 topography, fitted '
               'from its own printed graticule, the placer creeks riding '
               'the tundra as data.',
         credit='U.S. Geological Survey'),
    dict(d='mazama', g='The National Parks', title='Mazama: Crater Lake in Professional Paper 3', era='U.S. Geological Survey · Kerr & Diller · 1886–1902',
         blurb='Kerr’s plane-table survey of the caldera, drawn with the '
               'lake’s soundings inked across it, and Diller’s 1902 geology '
               'one crossfade behind — the mountain that fell in, read '
               'before anyone knew what to call it.',
         credit='U.S. Geological Survey'),
    dict(d='luray', g='The National Parks', title='The Hollows of Stony Man', era='U.S. Geological Survey · 1893 & 1933',
         blurb='The Blue Ridge reconnaissance sheet of 1893 — hollows full '
               'of farms, forty years before the park — over the 1933 '
               'survey that mapped the same ridges as the families were '
               'being moved off them.',
         credit='U.S. Geological Survey'),
    dict(d='smoky', g='The National Parks', title='The Smokies in Folio', era='U.S. Geological Survey · Keith, 1895',
         blurb='Arthur Keith’s 1895 folio of the Knoxville sheet — the '
               'Smokies drawn in geology and in contour on the same '
               'engraving, four decades before the park, with eighty gaps '
               'and balds riding the crest.',
         credit='U.S. Geological Survey'),
    dict(d='yosemite', g='The National Parks', title='Yosemite Before the Dam', era='U.S. Geological Survey · 1898–1911 & 1930',
         blurb='Four engraved quadrangles joined over Matthes’ 1930 park '
               'map: Hetch Hetchy is still a valley on the older sheets and '
               'a reservoir on the newer one — the crossfade drowns it in '
               'front of you.',
         credit='U.S. Geological Survey'),
    dict(d='brightangel', g='The National Parks', title='Bright Angel', era='U.S. Geological Survey · Matthes, 1903 & 1907',
         blurb='François Matthes’ plane-table specials at 1:48,000 — the '
               'canyon surveyed by mule and alidade, temple by temple — '
               'joined over the Powell survey’s 1886 reconnaissance of the '
               'same ground.',
         credit='U.S. Geological Survey'),
    dict(d='chisos', g='The National Parks', title='The Big Bend, 1903', era='U.S. Geological Survey · 1903',
         blurb='The Chisos and the river bend as the Survey found them in '
               '1903 — quicksilver camps, ranch tanks and crossings — with '
               'the modern sheets behind and seventy-six springs and '
               'tinajas riding the desert.',
         credit='U.S. Geological Survey'),
    dict(d='mountdesert', g='The National Parks', title='Pemetic: the Island Before Acadia', era='U.S. Geological Survey · 1904 & 1942',
         blurb='Mount Desert Island in 1904 — rusticator hotels, buckboard '
               'roads and the ice-scoured domes — over the 1942 War '
               'Department resurvey, with the harbours and ledges as data.',
         credit='U.S. Geological Survey'),
    dict(d='estes', g='The National Parks', title='The Park Special', era='U.S. Geological Survey · 1915',
         blurb='The only true USGS national-park special sheet in the '
               'archive, printed the year Rocky Mountain opened — its own '
               'georeference, no fitting at all — over the Longs Peak '
               'quadrangle engraved the same spring.',
         credit='U.S. Geological Survey'),
    dict(d='kilauea', g='The National Parks', title='Kīlauea and Mauna Loa', era='U.S. Geological Survey · 1921–1930',
         blurb='The observatory decade on paper: four quadrangles of the '
               'volcano country over the 1930 Kaʻū geology, with the flows '
               'and craters named — a map of ground that keeps moving.',
         credit='U.S. Geological Survey'),
    dict(d='blackhills', g='The National Parks', title='He Sapa in Folio', era='U.S. Geological Survey · Darton & Paige, 1925',
         blurb='The Central Black Hills folio over the 1901 quadrangles it '
               'was printed on — Wind Cave to Black Elk Peak, the granite '
               'core and the artesian rim — on land the 1868 treaty '
               'guaranteed and 1877 took.',
         credit='U.S. Geological Survey'),
    dict(d='art', g='The Flat Wing', title='The Flat Wing', era='Views & panoramas · 1814–1948',
         blurb='Bird’s-eye views, panoramas, system maps and town plans '
               'from five states that cannot honestly be draped — Clark’s '
               '1814 master map, Renshawe’s panorama, the railroads’ own '
               'promotions, Sanborn sheets and more.',
         credit='Various collections — all public domain'),
]

def main():
    if os.path.isdir(DIST):
        shutil.rmtree(DIST)
    os.makedirs(DIST)
    for s in SHEETS:
        print('== %s' % s['d'], flush=True)
        subprocess.run([sys.executable, os.path.join(ROOT, s['d'], 'src', 'assemble.py')],
                       check=True)
        shutil.copytree(os.path.join(ROOT, s['d'], 'dist'),
                        os.path.join(DIST, s['d']))
        card = os.path.join(ROOT, s['d'], 'assets', 'card.webp')
        if os.path.exists(card):
            shutil.copy(card, os.path.join(DIST, s['d'], 'card.webp'))
    open(os.path.join(DIST, 'index.html'), 'w').write(gallery())
    tot = sum(os.path.getsize(os.path.join(dp, f))
              for dp, _, fs in os.walk(DIST) for f in fs)
    print('gallery   dist/  %.2f MB' % (tot/1e6))

CARD = '''    <a class="card" href="%(d)s/">
      <div class="im"><img src="%(d)s/card.webp" alt="" loading="lazy"></div>
      <div class="tx">
        <h2>%(title)s</h2>
        <div class="era">%(era)s</div>
        <p>%(blurb)s</p>
        <div class="cr">%(credit)s</div>
      </div>
    </a>'''

def gallery():
    out, last_g = [], None
    for sh in SHEETS:
        g = sh.get('g', 'Montana')
        if g != last_g:
            out.append('    <h2 class="stateh">%s</h2>' % g)
            last_g = g
        out.append(CARD % sh)
    cards = '\n'.join(out)
    return PAGE % cards

PAGE = '''<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Old Time Maps</title>
<meta name="description" content="Old sheets, put back on the earth — historical maps of Montana and the mountain West, georeferenced and draped over the terrain they describe.">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@400;500&family=IBM+Plex+Sans+Condensed:wght@400;500;600&family=Spectral:ital,wght@0,300;0,400;1,400&display=swap">
<style>
:root{--ink:#0d0c0a;--panel:#151310;--line:#332c24;--line2:#241f1a;--paper:#f1eadc;
      --muted:#9b917f;--dim:#6e675c;--accent:#6fb3cd;--warm:#e0a23c}
*{box-sizing:border-box}
body{margin:0;background:var(--ink);color:var(--paper);
     font-family:"IBM Plex Sans Condensed","Helvetica Neue",sans-serif;
     -webkit-font-smoothing:antialiased}
header{max-width:1060px;margin:0 auto;padding:72px 24px 30px;text-align:center}
h1{margin:0;font-family:Spectral,Georgia,serif;font-weight:300;
   font-size:clamp(30px,6vw,46px);letter-spacing:.38em;text-indent:.38em}
.tag{margin-top:14px;font-size:12px;letter-spacing:.22em;text-transform:uppercase;color:var(--dim)}
.rule{width:64px;height:1px;background:var(--line);margin:26px auto 0}
main{max-width:1060px;margin:0 auto;padding:26px 24px 30px;
     display:grid;grid-template-columns:repeat(auto-fit,minmax(300px,1fr));gap:18px}
.stateh{grid-column:1/-1;margin:26px 0 0;font-family:Spectral,Georgia,serif;
        font-weight:300;font-size:15px;letter-spacing:.34em;text-indent:.34em;
        text-transform:uppercase;color:var(--warm);text-align:center}
.stateh:first-child{margin-top:0}
.card{display:flex;flex-direction:column;text-decoration:none;color:inherit;
      background:var(--panel);border:1px solid var(--line);border-radius:3px;
      overflow:hidden;transition:border-color .18s, transform .18s}
.card:hover{border-color:var(--warm);transform:translateY(-2px)}
.im{height:210px;overflow:hidden;border-bottom:1px solid var(--line2);background:#26221c}
.im img{width:100%%;height:100%%;object-fit:cover;filter:saturate(.96)}
.card:hover .im img{filter:none}
.tx{padding:16px 18px 15px;display:flex;flex-direction:column;flex:1}
h2{margin:0;font-family:Spectral,Georgia,serif;font-weight:400;font-size:21px}
.era{margin-top:5px;font-size:10px;letter-spacing:.14em;text-transform:uppercase;color:var(--warm)}
.tx p{margin:10px 0 14px;font-size:12.5px;line-height:1.55;color:var(--muted);flex:1}
.cr{font-size:9px;letter-spacing:.1em;text-transform:uppercase;color:var(--dim)}
footer{max-width:1060px;margin:0 auto;padding:8px 24px 60px;text-align:center;
       font-size:11px;color:var(--dim);line-height:1.7}
footer a{color:var(--accent);text-decoration:none}
footer a:hover{text-decoration:underline}
</style>
</head>
<body>
<header>
  <h1>OLD TIME MAPS</h1>
  <div class="tag">Old sheets, put back on the earth</div>
  <div class="rule"></div>
</header>
<main>
%s
</main>
<footer>
  Each sheet is georeferenced from its own graticule, silhouette or sibling surveys — no hand-picked control points —<br>
  and draped over open elevation data. Sources and residuals live in each explorer’s <i>About</i> panel.<br>
  <a href="https://github.com/johnymontana/old-time-maps">github.com/johnymontana/old-time-maps</a>
</footer>
</body>
</html>
'''

if __name__ == '__main__':
    main()
