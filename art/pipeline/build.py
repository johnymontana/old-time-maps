#!/usr/bin/env python3
"""The Flat Wing — asset pipeline.

Bird's-eye views, panoramas, brochure maps and town plans that cannot be
draped honestly — oblique perspectives and block-level plats — presented as
what they are: pictures. This pipeline fetches each public-domain original,
downsizes it to a web-friendly WebP, and writes the piece list the page is
typeset from.

    python3 pipeline/build.py
"""
import json, os, sys, urllib.request

from PIL import Image

Image.MAX_IMAGE_PIXELS = None
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
WORK = os.environ.get('AR_WORK', os.path.join(ROOT, 'work'))
BUILD = os.path.join(ROOT, 'assets')
os.makedirs(WORK, exist_ok=True); os.makedirs(BUILD, exist_ok=True)

UA = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) '
                    'AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0 Safari/537.36'}

PIECES = [
    dict(id='renshawe', src='renshawe.jp2',
         url='https://collections.lib.uwm.edu/digital/api/collection/agdm/id/20/download',
         title='Panoramic View of the Glacier National Park',
         line='John H. Renshawe · U.S. Geological Survey · 1914',
         credit='American Geographical Society Library, UW-Milwaukee',
         link='https://collections.lib.uwm.edu/digital/collection/agdm/id/20',
         cap='The Survey’s own painter of parks: Renshawe rendered the '
             'topographers’ sheets as a single soft-lit panorama, relief '
             'without a single contour. It is an oblique view — no honest '
             'way to drape it — so it hangs here as the painting it is.'),
    dict(id='aeroplane', src='aeroplane1914.jp2',
         url='https://archive.org/download/dr_aeroplane-view-of-glacier-national-park-see-america-first-great-norther-8707003/8707003.jp2',
         title='Aeroplane View of Glacier National Park',
         line='Great Northern Railway · McGill-Warner Co. · 1914',
         credit='Internet Archive · scan via the David Rumsey Map Collection',
         link='https://archive.org/details/dr_aeroplane-view-of-glacier-national-park-see-america-first-great-norther-8707003',
         cap='“See America First” from an imaginary altitude: the railway’s '
             'promotional bird’s-eye, with every hotel and chalet of its '
             'park empire drawn in. The perspective is a salesman’s, not a '
             'surveyor’s.'),
    dict(id='guide1948', src='guide1948.jp2',
         url='https://collections.lib.uwm.edu/digital/api/collection/agdm/id/27960/download',
         title='Guide Map, Waterton-Glacier International Peace Park',
         line='National Park Service · revised 1948',
         credit='American Geographical Society Library, UW-Milwaukee',
         link='https://collections.lib.uwm.edu/digital/collection/agdm/id/27962',
         cap='The mid-century park at a glance — roads, trails, chalets and '
             'the Peace Park border — closing the era the 1915 sheet opened.'),
    dict(id='brochure1938', src='brochure1938.jpg',
         title='Map of Waterton-Glacier International Peace Park',
         line='National Park Service brochure fold-out · revised 1937',
         credit='NPS History eLibrary',
         link='http://npshistory.com/publications/glac/brochures/index.htm',
         cap='The fold-out every 1930s visitor carried: Going-to-the-Sun '
             'finally complete, printed by the Geological Survey for the '
             'glovebox rather than the drafting table.'),
    dict(id='ayres1899', src='ayres1899.jpg',
         title='Lewis and Clark Forest Reserve — Classification of Lands',
         line='H.B. Ayres · USGS 21st Annual Report, plate III · 1899',
         credit='U.S. Geological Survey, Publications Warehouse',
         link='https://pubs.usgs.gov/ar/21-5/plate-003.pdf',
         cap='Before the parks and the forests had their names, Ayres rode '
             'the reserves classifying every township by timber and burn — '
             'the Bien-lithographed plates are the region’s first land-use '
             'cartography.'),
    dict(id='usfs_fnf', src='usfs_fnf.jpg',
         title='Flathead National Forest',
         line='U.S. Forest Service · c. 1912–1920',
         credit='Montana History Portal · University of Montana',
         link='https://www.mtmemory.org/nodes/view/87874',
         cap='The half-inch-to-the-mile forest map of the Swan and Mission '
             'country — hachured relief and the township grid, filling the '
             'gap between the Glacier sheets and the valley quads.'),
    dict(id='resv1904', src='resv1904.jpg',
         title='Sectionized Map of the Flathead Indian Reservation',
         line='General Land Office · 1904',
         credit='Montana History Portal · Montana Historical Society',
         link='https://www.mtmemory.org/nodes/view/45365',
         cap='The section grid drawn to administer allotment and the 1910 '
             'opening of Séliš, Ql̓ispé and Ksanka lands to homesteaders. '
             'Cartographically precise; historically, the paperwork of a '
             'dispossession. It hangs here so that can be said plainly.'),
    dict(id='sanborn_kalispell', src='sanborn_kalispell.jp2',
         title='Kalispell, Montana — Sanborn sheet 1',
         line='Sanborn Map Company · August 1910',
         credit='Library of Congress, Geography & Map Division',
         link='https://www.loc.gov/item/sanborn05032_005/',
         cap='Fire-insurance cartography at one inch to fifty feet: every '
             'building in the young county seat, colour-coded by material. '
             'Thirty sheets cover the town; this is the index.'),
    dict(id='sanborn_bigfork', src='sanborn_bigfork.jp2',
         title='Big Fork, Montana — the whole town on one sheet',
         line='Sanborn Map Company · September 1916',
         credit='Library of Congress, Geography & Map Division',
         link='https://www.loc.gov/item/sanborn04936_001/',
         cap='Bigfork in 1916 fit on a single Sanborn sheet — mill, dam, '
             'hotel and the few dozen buildings above the Swan’s mouth.'),
]

def p(*a): print(*a, flush=True)

def main():
    meta = []
    for piece in PIECES:
        src = os.path.join(WORK, piece['src'])
        if not os.path.exists(src):
            if 'url' not in piece:
                raise SystemExit('missing %s and no url to fetch it' % piece['src'])
            p('· fetching %s…' % piece['id'])
            req = urllib.request.Request(piece['url'], headers=UA)
            with urllib.request.urlopen(req, timeout=600) as r, open(src, 'wb') as f:
                f.write(r.read())
        out = os.path.join(BUILD, piece['id'] + '.webp')
        if not os.path.exists(out):
            p('· encoding %s…' % piece['id'])
            im = Image.open(src).convert('RGB')
            im.thumbnail((2200, 2200), Image.LANCZOS)
            im.save(out, quality=84, method=6)
        im = Image.open(out)
        meta.append(dict(id=piece['id'], w=im.width, h=im.height,
                         title=piece['title'], line=piece['line'],
                         credit=piece['credit'], link=piece['link'],
                         cap=piece['cap']))
        p('  %-18s %d×%d  %5.0f KB' % (piece['id'], im.width, im.height,
                                       os.path.getsize(out)/1024))
    json.dump(meta, open(os.path.join(BUILD, 'meta.json'), 'w'))
    card = Image.open(os.path.join(BUILD, 'renshawe.webp'))
    card = card.resize((640, int(card.height*640/card.width)), Image.LANCZOS)
    card.save(os.path.join(BUILD, 'card.webp'), quality=82, method=6)
    p('· card + meta written')

if __name__ == '__main__':
    main()
