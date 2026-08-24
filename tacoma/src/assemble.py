#!/usr/bin/env python3
"""Build the explorer from src/ + assets/.

    python3 src/assemble.py

Writes two builds:

    dist/index.html            assets loaded from dist/assets/  (serve it:
                               `python3 -m http.server -d dist`)
    the-flathead.html          one self-contained file, assets inlined as
                               data URIs — this is the artifact build, and
                               it has no <html>/<head>/<body> wrapper
                               because the Artifact publisher adds one.
"""
import base64, os, shutil, sys, urllib.request

SRC   = os.path.dirname(os.path.abspath(__file__))
ROOT  = os.path.dirname(SRC)
BUILD = os.path.join(ROOT, 'assets')
DIST  = os.path.join(ROOT, 'dist')
THREE = os.path.join(ROOT, 'vendor', 'three.min.js')
THREE_URL = 'https://unpkg.com/three@0.155.0/build/three.min.js'

FONTS = ('https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@400;500'
         '&family=IBM+Plex+Sans+Condensed:wght@400;500;600'
         '&family=Spectral:ital,wght@0,300;0,400;0,500;1,400&display=swap')
TITLE = 'Tacoma: Ice and Iron'
BLURB = ("Bailey Willis's 1899 glacial geology of the Tacoma quadrangle — "
         "Puget Sound as an ice-carved trench — over the 1897 standing-timber "
         "survey and modern terrain, with the coal workings as data.")
ONE   = 'tacoma-ice-and-iron.html'

def read(p, mode='r'):
    with open(p, mode) as f: return f.read()

def vendor_three():
    if not os.path.exists(THREE):
        os.makedirs(os.path.dirname(THREE), exist_ok=True)
        print('· fetching three.js r155')
        with urllib.request.urlopen(THREE_URL, timeout=120) as r, open(THREE, 'wb') as f:
            f.write(r.read())
    return read(THREE)

def page(asset_js, standalone):
    # charset first and in head — the artifact build has no head of its own,
    # and it must land in the first 1024 bytes or degree signs go mojibake.
    head = ('<meta charset="utf-8">\n'
            '<title>%s</title>\n'
            '<meta name="description" content="%s">\n'
            '<link rel="preconnect" href="https://fonts.googleapis.com">\n'
            '<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>\n'
            '<link rel="stylesheet" href="%s">\n<style>\n%s</style>'
            % (TITLE, BLURB, FONTS, css))
    scripts = ('<script>%s</script>\n<script>%s</script>\n'
               '<script>%s</script>\n<script>%s</script>' % (three, asset_js, app1, app2))
    if not standalone:
        return head + '\n' + body + '\n' + scripts + '\n'
    return ('<!doctype html>\n<html lang="en">\n<head>\n'
            '<meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover">\n'
            + head + '\n</head>\n<body>\n' + body + '\n' + scripts + '\n</body>\n</html>\n')

if not os.path.exists(os.path.join(BUILD, 'meta.json')):
    raise SystemExit('run pipeline/build.py first — assets/ is empty')

css   = read(os.path.join(SRC, 'style.css'))
body  = read(os.path.join(SRC, 'body.html'))
app1  = read(os.path.join(SRC, 'app1.js'))
app2  = read(os.path.join(SRC, 'app2.js'))
three = vendor_three()
meta  = read(os.path.join(BUILD, 'meta.json'))
for name, blob in (('three.js', three), ('app1', app1), ('app2', app2)):
    assert '</script' not in blob.lower(), name

# self-contained build
durl = lambda p, m: 'data:%s;base64,%s' % (m, base64.b64encode(read(p, 'rb')).decode())
ALT = os.path.join(BUILD, 'alt.webp')
inline = ('window.MT_META=%s;\nwindow.MT_DRAPE="%s";\nwindow.MT_HEIGHT="%s";'
          % (meta, durl(os.path.join(BUILD, 'drape.webp'), 'image/webp'),
                   durl(os.path.join(BUILD, 'height.webp'), 'image/webp')))
if os.path.exists(ALT):
    inline += '\nwindow.MT_ALT="%s";' % durl(ALT, 'image/webp')
one = os.path.join(ROOT, ONE)
open(one, 'w').write(page(inline, standalone=False))
print('artifact  %-30s %6.2f MB' % (ONE, os.path.getsize(one)/1e6))

# served build
os.makedirs(os.path.join(DIST, 'assets'), exist_ok=True)
for f in ('drape.webp', 'height.webp') + (('alt.webp',) if os.path.exists(ALT) else ()):
    shutil.copy(os.path.join(BUILD, f), os.path.join(DIST, 'assets', f))
open(os.path.join(DIST, 'assets', 'meta.json'), 'w').write(meta)
ext = ('window.MT_META=%s;\nwindow.MT_DRAPE="assets/drape.webp";'
       '\nwindow.MT_HEIGHT="assets/height.webp";' % meta)
if os.path.exists(ALT):
    ext += '\nwindow.MT_ALT="assets/alt.webp";' 
open(os.path.join(DIST, 'index.html'), 'w').write(page(ext, standalone=True))
tot = sum(os.path.getsize(os.path.join(dp, f)) for dp, _, fs in os.walk(DIST) for f in fs)
print('dist      %-30s %6.2f MB' % ('dist/', tot/1e6))
