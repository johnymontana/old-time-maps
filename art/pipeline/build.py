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
    dict(id='raynolds1860', src='raynolds1860.jp2',
         url='https://tile.loc.gov/storage-services/service/gmd/gmd412/g4127/g4127y/ct000847.jp2',
         title='Map of the Yellowstone and Missouri Rivers and Their Tributaries',
         line='Raynolds Expedition · compiled by F.V. Hayden · 1859–60',
         credit='Library of Congress, Geography & Map Division',
         link='https://www.loc.gov/item/96682479/',
         cap='The army’s reconnaissance of the upper Yellowstone, Jim '
             'Bridger guiding — and the plateau itself left nearly blank, '
             'the last unmapped corner of the territory. Hayden, the '
             'expedition’s naturalist, drew this sheet; a decade later he '
             'came back and filled in the blank. The “before” of every '
             'draped sheet in this gallery.'),
    dict(id='uppergeyser1871', src='uppergeyser1871.jp2',
         url='https://tile.loc.gov/storage-services/service/gmd/gmd426/g4262/g4262y/ye000014.jp2',
         title='Upper Geyser Basin, Fire Hole River, Wyoming Territory',
         line='Hayden Survey · 1871',
         credit='Library of Congress, Geography & Map Division',
         link='https://www.loc.gov/item/97683584/',
         cap='The first map of the Old Faithful basin, sketched the summer '
             'before the park act passed — each geyser a numbered point, '
             'the intervals timed by pocket watch. Congress voted with '
             'this survey’s maps and photographs on its desks.'),
    dict(id='hayden1878', src='hayden1878.jp2',
         url='https://tile.loc.gov/storage-services/service/gmd/gmd426/g4262/g4262y/ye000002.jp2',
         title='Preliminary Geological Map of the Yellowstone National Park',
         line='Hayden Survey · 1878',
         credit='Library of Congress, Geography & Map Division',
         link='https://www.loc.gov/item/97683605/',
         cap='The territorial survey’s colour geology of the young park — '
             'the reading Hague’s folio would redo with better instruments '
             'twenty years on. Hang it beside the draped Folio 30 sheet '
             'and you can watch the science grow up.'),
    dict(id='clark1814', src='clark1814.jp2',
         url='https://tile.loc.gov/storage-services/service/gmd/gmd412/g4126/g4126s/ct000028.jp2',
         title='A Map of Lewis and Clark’s Track Across the Western Portion of North America',
         line='William Clark · engraved by Samuel Lewis · 1814',
         credit='Library of Congress, Geography & Map Division',
         link='https://www.loc.gov/item/79692907/',
         cap='The master map of the expedition, drawn by Clark from his own '
             'field sheets — the Missouri traced bend by bend past the falls '
             'and the Marias, the whole West hung on one river. Every sheet '
             'in this gallery descends from it.'),
    dict(id='nplandgrant', src='nplandgrant.jp2',
         url='https://tile.loc.gov/storage-services/service/gmd/gmd424/g4241/g4241p/ct001237r.jp2',
         title='Land Grant of the Northern Pacific Railroad in Montana and Idaho',
         line='Northern Pacific Railroad Company · c. 1890',
         credit='Library of Congress, Geography & Map Division',
         link='https://www.loc.gov/item/86695638/',
         cap='The checkerboard itself: every odd-numbered section for forty '
             'miles either side of the line, the price Congress paid to get '
             'the road built — an area larger than some states, drawn as '
             'calmly as a timetable.'),
    dict(id='jawbone1899', src='jawbone1899.jp2',
         url='https://tile.loc.gov/storage-services/service/gmd/gmd425/g4251/g4251p/rr004710.jp2',
         title='Map of Central Montana — the Montana Railroad',
         line='“The Jawbone” · September 1, 1899',
         credit='Library of Congress, Geography & Map Division',
         link='https://www.loc.gov/item/98688722/',
         cap='Richard Harlow’s Montana Railroad, promoted here at its '
             'hopeful best — the line they said he financed with his jaw, '
             'wandering up Sixteenmile Canyon toward Lewistown. The '
             'Milwaukee later bought his bluff and made it a main line.'),
    dict(id='missoula_bev', src='missoula_bev.jp2',
         url='https://tile.loc.gov/storage-services/service/gmd/gmd425/g4254/g4254m/pm004600.jp2',
         title='Bird’s Eye View of Missoula, Montana',
         line='Lithograph · 1884',
         credit='Library of Congress, Geography & Map Division',
         link='https://www.loc.gov/item/75694673/',
         cap='Missoula the year after the Northern Pacific arrived — mills '
             'on the Clark Fork, the bridge, Hellgate Canyon behind — the '
             'town the 1912 quadrangle would later leave just off its '
             'eastern edge, drawn here in full.'),
    dict(id='livingston_bev', src='livingston_bev.jp2',
         url='https://tile.loc.gov/storage-services/service/gmd/gmd425/g4254/g4254l/pm004580.jp2',
         title='Bird’s Eye View of Livingston, Montana',
         line='Lithograph · 1883',
         credit='Library of Congress, Geography & Map Division',
         link='https://www.loc.gov/item/75694671/',
         cap='Livingston in its first year: the Northern Pacific’s shops and '
             'roundhouse, the grid staked into the sagebrush, and the Park '
             'Branch curving south toward Paradise Valley — drawn while the '
             'paint was still wet on the depot.'),
]

def p(*a): print(*a, flush=True)

def main():
    meta = []
    for piece in PIECES:
        src = os.path.join(WORK, piece['src'])
        if not os.path.exists(src):
            if 'url' not in piece:
                raise SystemExit('missing %s and no url to fetch it' % piece['src'])
            for attempt in range(4):
                p('· fetching %s…' % piece['id'])
                try:
                    req = urllib.request.Request(piece['url'], headers=UA)
                    with urllib.request.urlopen(req, timeout=600) as r, open(src, 'wb') as f:
                        f.write(r.read())
                    break
                except Exception as e:
                    if os.path.exists(src): os.remove(src)
                    if attempt == 3: raise
                    p('  retry (%s)' % e)
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
