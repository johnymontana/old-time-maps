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
    dict(d='art', title='The Flat Wing', era='Views & panoramas · 1899–1948',
         blurb='Bird’s-eye views, brochure maps and town plans that cannot '
               'honestly be draped — Renshawe’s painted panorama, the Great '
               'Northern’s aeroplane view, Sanborn sheets and more.',
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

def gallery():
    cards = '\n'.join('''    <a class="card" href="%(d)s/">
      <div class="im"><img src="%(d)s/card.webp" alt="" loading="lazy"></div>
      <div class="tx">
        <h2>%(title)s</h2>
        <div class="era">%(era)s</div>
        <p>%(blurb)s</p>
        <div class="cr">%(credit)s</div>
      </div>
    </a>''' % s for s in SHEETS)
    return '''<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Old Time Maps</title>
<meta name="description" content="Old sheets, put back on the earth — historical maps of Montana, georeferenced and draped over the terrain they describe.">
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
''' % cards

if __name__ == '__main__':
    main()
