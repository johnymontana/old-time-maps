#!/usr/bin/env python3
"""Typeset the Flat Wing from assets/ — a static page, no WebGL, no build
dependencies beyond the standard library.

    python3 src/assemble.py     # writes dist/index.html + dist/assets/
"""
import html, json, os, shutil

SRC = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(SRC)
BUILD = os.path.join(ROOT, 'assets')
DIST = os.path.join(ROOT, 'dist')

meta = json.load(open(os.path.join(BUILD, 'meta.json')))

FIG = '''    <figure>
      <a href="%(link)s" target="_blank" rel="noopener"><img src="assets/%(id)s.webp" width="%(w)d" height="%(h)d" alt="%(title_a)s" loading="lazy"></a>
      <figcaption>
        <h2>%(title)s</h2>
        <div class="line">%(line)s</div>
        <p>%(cap)s</p>
        <div class="credit"><a href="%(link)s" target="_blank" rel="noopener">%(credit)s</a></div>
      </figcaption>
    </figure>'''

figures = '\n'.join(FIG % dict(f, title_a=html.escape(f['title'], quote=True))
                    for f in meta)

PAGE = '''<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>The Flat Wing — Old Time Maps</title>
<meta name="description" content="Bird's-eye views, panoramas, brochure maps and town plans of the Flathead and Glacier country that cannot be draped — presented as the pictures they are.">
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
header{max-width:980px;margin:0 auto;padding:64px 24px 26px;text-align:center}
h1{margin:0;font-family:Spectral,Georgia,serif;font-weight:300;
   font-size:clamp(26px,5vw,40px);letter-spacing:.34em;text-indent:.34em}
.tag{margin-top:13px;font-size:11.5px;letter-spacing:.2em;text-transform:uppercase;color:var(--dim);line-height:1.8}
.back{margin-top:16px;font-size:11px;letter-spacing:.14em;text-transform:uppercase}
.back a{color:var(--accent);text-decoration:none}
.back a:hover{text-decoration:underline}
.rule{width:64px;height:1px;background:var(--line);margin:24px auto 0}
main{max-width:980px;margin:0 auto;padding:20px 24px 40px}
figure{margin:0 0 46px;background:var(--panel);border:1px solid var(--line);
       border-radius:3px;overflow:hidden}
figure img{display:block;width:100%%;height:auto;border-bottom:1px solid var(--line2)}
figcaption{padding:18px 22px 17px}
h2{margin:0;font-family:Spectral,Georgia,serif;font-weight:400;font-size:21px}
.line{margin-top:5px;font-size:10px;letter-spacing:.14em;text-transform:uppercase;color:var(--warm)}
figcaption p{margin:11px 0 12px;font-size:13px;line-height:1.6;color:var(--muted);max-width:70ch}
.credit{font-size:9.5px;letter-spacing:.1em;text-transform:uppercase}
.credit a{color:var(--dim);text-decoration:none}
.credit a:hover{color:var(--accent)}
footer{max-width:980px;margin:0 auto;padding:0 24px 60px;text-align:center;
       font-size:11px;color:var(--dim);line-height:1.7}
footer a{color:var(--accent);text-decoration:none}
</style>
</head>
<body>
<header>
  <h1>THE FLAT WING</h1>
  <div class="tag">Bird's-eye views, panoramas, brochure maps and town plans<br>
  that cannot honestly be draped — hung here as the pictures they are.</div>
  <div class="back"><a href="../">&larr; back to the gallery</a></div>
  <div class="rule"></div>
</header>
<main>
%s
</main>
<footer>
  Every piece is a public-domain work; scans belong to the credited libraries — click through for the originals.<br>
  <a href="https://github.com/johnymontana/old-time-maps">github.com/johnymontana/old-time-maps</a>
</footer>
</body>
</html>
''' % figures

if os.path.isdir(DIST):
    shutil.rmtree(DIST)
os.makedirs(os.path.join(DIST, 'assets'))
for f in os.listdir(BUILD):
    if f.endswith('.webp'):
        shutil.copy(os.path.join(BUILD, f), os.path.join(DIST, 'assets', f))
open(os.path.join(DIST, 'index.html'), 'w').write(PAGE)
tot = sum(os.path.getsize(os.path.join(dp, f)) for dp, _, fs in os.walk(DIST) for f in fs)
print('dist      %-30s %6.2f MB' % ('dist/', tot/1e6))
