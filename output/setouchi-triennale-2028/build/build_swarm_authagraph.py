#!/usr/bin/env python3
"""Separate AuthaGraph plates using Alpha60's native cumulative swarm renderer."""
from plate_tools import *
import argparse, collections, fcntl, hashlib, json, os, re, xml.sax
from xml.sax.saxutils import XMLGenerator

RUNTIME = OUT / 'build/swarm-runtime'
NATIVE = RUNTIME / 'tmp/authagraph'
BINARY = OUT / 'build/render-swarm-authagraph'
BANDS = {'ge-1080p': ('1080p / 4K', 2804935), 'lt-1080p': ('720p / SD', 876541)}

def digest(path):
    with path.open('rb') as f: return hashlib.file_digest(f, 'sha256').hexdigest()

def source_for(band):
    paths = list(NATIVE.glob('*-downloader-cumulative-' + band + '-render*.svg'))
    assert len(paths) == 1, (band, paths)
    return paths[0]

def native_render():
    NATIVE.mkdir(parents=True, exist_ok=True)
    with (RUNTIME / 'authagraph-render.lock').open('w') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)
        if all(len(list(NATIVE.glob('*-downloader-cumulative-' + b + '-render*.svg'))) == 1 for b in BANDS): return
        subprocess.run(['python3', str(OUT / 'build/compile_swarm_authagraph.py')], check=True)
        env = dict(os.environ, a60_PREFIX_DIR='/home/bkoz/src/alpha60', a60_DATA_DIR='/home/bkoz/src/alpha60-data', a60_GEOLOCATION_DB='/home/bkoz/src/geoip-databases/ipinfo/standard_location.mmdb')
        with (OUT / 'logs/swarm-native-authagraph.log').open('w') as log:
            subprocess.run([str(BINARY), str(RUNTIME / 'cache'), 'dan-da-dan-210', str(NATIVE)], cwd=RUNTIME, env=env, stdout=log, stderr=subprocess.STDOUT, check=True)

class Native(xml.sax.ContentHandler):
    """Stream native circles to world and a fitted Japan viewport."""
    def __init__(self, world, japan, band, scale, visible_box):
        self.world = XMLGenerator(world, encoding='utf-8'); self.japan = XMLGenerator(japan, encoding='utf-8')
        self.band, self.scale, self.box = band, scale, visible_box
        self.depth = 0; self.active = False; self.emitted = []; self.styles = {}; self.ids = collections.Counter()
        self.count = self.japan_count = 0
    def startElement(self, name, attributes):
        self.depth += 1; a = dict(attributes)
        if self.depth == 2:
            ident = a.get('id', '')
            self.active = ident.startswith('vector-peer-clouds-') or ident == 'text-geolocation-text'
        if not self.active: return
        assert name != 'image'
        assert name != 'g' or 'transform' not in a, 'Native cloud transforms require explicit registration'
        if 'id' in a:
            old = a['id']; self.ids[old] += 1
            a['id'] = self.band + '-' + old.replace('/', '-') + '-' + str(self.ids[old])
        ja = dict(a); keep = True
        if name == 'circle':
            self.count += 1; style = a.pop('style')
            assert 'fill-opacity:0.05' in style.replace(' ', '')
            a['class'] = self.styles.setdefault(style, 'native-c' + str(len(self.styles)))
            ja = dict(a)
            # Fitted detail changes centre coordinates, as Alpha60's country
            # renderer does. Physical circle area stays comparable to the world.
            ja['r'] = format(float(a['r']) / self.scale, '.12g')
            x, y, radius = float(a['cx']) / 96, float(a['cy']) / 96, float(ja['r']) / 96
            left, top, right, bottom = self.box
            keep = x + radius >= left and x - radius <= right and y + radius >= top and y - radius <= bottom
            self.japan_count += keep
        elif name == 'text' and 'font-size' in ja:
            size = re.fullmatch(r'([0-9.]+)([a-z]*)', ja['font-size'])
            assert size, ja['font-size']
            ja['font-size'] = format(float(size[1]) / self.scale, '.12g') + size[2]
        self.world.startElement(name, a)
        if keep: self.japan.startElement(name, ja)
        self.emitted.append(keep)
    def endElement(self, name):
        if self.active:
            self.world.endElement(name)
            if self.emitted.pop(): self.japan.endElement(name)
        if self.depth == 2: self.active = False
        self.depth -= 1
    def characters(self, data):
        if self.active:
            self.world.characters(data)
            if not self.emitted or self.emitted[-1]: self.japan.characters(data)

def geography(scale):
    earth = E.parse(str(OUT / 'plates/world/svg' / ('earth' + SUFFIX + '.svg')), PARSER)
    land = copy.deepcopy(earth.xpath('//*[@id="land"]')[0])
    for p in land.xpath('.//*[local-name()="path"]'):
        p.attrib.pop('style', None); p.set('fill', 'white'); p.set('stroke', 'none')
    atmo = E.parse(str(OUT / 'plates/world/svg' / ('cloud-atmosphere' + SUFFIX + '.svg')), PARSER)
    coast = copy.deepcopy(atmo.xpath('//*[@id="terrestrial-coastline"]')[0])
    for p in coast.xpath('.//*[local-name()="path"]'):
        p.attrib.pop('style', None); p.set('fill', 'none'); p.set('stroke', '#555555'); p.set('stroke-opacity', '.75')
        p.set('stroke-width', format((1 if scale != 1 else .5) / 72 / scale, '.12g'))
    return E.tostring(land, encoding='unicode'), E.tostring(coast, encoding='unicode')

def compose(band):
    title, expected = BANDS[band]; source = source_for(band); stem = 'network-swarm-' + band
    paths = {scope: OUT / f'plates/{scope}/svg' / (stem + SUFFIX + ('-japan' if scope == 'japan' else '') + '.svg') for scope in ['world', 'japan']}
    view = json.loads((OUT / 'sources/japan-view.json').read_text()); bx, by, bw, bh = view['world_viewbox']
    scale = min(28 / bw, 15 / bh)
    dx, dy = .7 + (28 - bw * scale) / 2 - bx * scale, 2 + (15 - bh * scale) / 2 - by * scale
    visible_box = ((.7 - dx) / scale, (2 - dy) / scale, (28.7 - dx) / scale, (17 - dy) / scale)
    land, world_coast = geography(1); _, japan_coast = geography(scale)
    with paths['world'].open('w') as world, paths['japan'].open('w') as japan:
        for scope, stream in [('world', world), ('japan', japan)]:
            doc = el('svg', width='44in', height='19.052559in', viewBox='0 0 44 19.052559', role='img', data_projection='authagraph', data_resolution_partition=band)
            el('title', doc).text = f'{scope.title()} / Dan Da Dan / {title} / AuthaGraph'
            el('desc', doc).text = 'Alpha60 native cumulative cache, member colours, 5% opacity and weighted circles. Coordinates use the atlas AuthaGraph projection.'
            el('rect', doc, width=44, height=19.052559, fill='white')
            if scope == 'japan':
                txt(doc, .7, .8, 'JAPAN / NETWORK SWARM / DAN DA DAN / ' + title, .47, font_weight='bold')
                txt(doc, .7, 1.35, 'SETOUCHI TRIENNALE 2028 / AuthaGraph / 4 September 2025–4 March 2026', .23)
                defs = el('defs', doc); clip = el('clipPath', defs, id='japan-viewport'); el('rect', clip, x='.7', y='2', width='28', height='15')
            stream.write(E.tostring(doc, encoding='unicode')[:-6])
            if scope == 'japan': stream.write(f'<g clip-path="url(#japan-viewport)"><g transform="translate({dx} {dy}) scale({scale})">')
            stream.write('<rect width="44" height="19.052559" fill="#f2f2f2"/>' + land)
            stream.write('<g transform="scale(0.010416666666666666)">')
        handler = Native(world, japan, band, scale, visible_box); xml.sax.parse(str(source), handler)
        assert handler.count == expected, (band, handler.count, expected)
        for scope, stream in [('world', world), ('japan', japan)]:
            stream.write('</g>' + (world_coast if scope == 'world' else japan_coast))
            if scope == 'japan': stream.write('</g></g>')
            notes = el('g', id='legend-and-provenance')
            if scope == 'world':
                el('rect', notes, x='28.5', y='16.25', width='15.2', height='2.5', fill='white', fill_opacity='.94')
                txt(notes, 29, 16.8, 'NETWORK SWARM / DAN DA DAN', .4, font_weight='bold'); txt(notes, 29, 17.25, title + ' / AuthaGraph', .32, font_weight='bold')
                y = 17.64
                lines = ['Cumulative downloader observations · 4 Sep 2025–4 Mar 2026', 'Native circle area follows weight; 5% opacity; per-member colours.', '2160p: yellow; 1080p: pink/purple.' if band == 'ge-1080p' else '720p: blue; SD: green.', 'Observations across torrents are not unique people or traffic volume.']
                for line in lines: txt(notes, 29, y, line, .19); y += .26
            else:
                import textwrap
                y = 2.35
                for heading, body in [
                    ('READ THIS PLATE', 'Japan detail in the atlas AuthaGraph projection. Circle centres follow the geographic enlargement; circle area uses the same physical weight scale as the world plate. Coastlines are 1 pt.'),
                    ('RESOLUTION AND COLOUR', title + ('. 2160p is yellow; 1080p pink/purple.' if band == 'ge-1080p' else '. 720p is blue; SD green.') + ' Colours within each band distinguish media members. Circle fill opacity is 5%.'),
                    ('SOURCE AND LIMIT', 'Dan Da Dan 210 cache, episodes 210 / 211 / 212. Cumulative observations from 4 September 2025 to 4 March 2026. Repeated participants across torrents are not unique people. This geographic viewport includes neighbouring countries; it is not a Japan-only total.')]:
                    txt(notes, 30, y, heading, .27, font_weight='bold'); y += .55
                    for line in textwrap.wrap(body, 72): txt(notes, 30, y, line, .23); y += .36
                    y += .65
                txt(notes, .7, 18.35, '44 × 19.052559 in / AuthaGraph / Native Alpha60 circles / sources/swarm-refresh.json', .22)
            stream.write(E.tostring(notes, encoding='unicode'))
            stream.write('<style>' + ''.join('.' + cls + '{' + style + '}' for style, cls in handler.styles.items()) + '</style></svg>')
    receipt = dict(band=band, title=title, source=str(source), source_sha256=digest(source), native_circles=handler.count, japan_visible_circles=handler.japan_count, projection='AuthaGraph', fill_opacity=.05, native_units_per_inch=96, japan_geographic_scale=scale, japan_circle_radius_compensation=1 / scale, japan_viewport_world_coordinates=visible_box, output_files={scope: str(p.relative_to(OUT)) for scope, p in paths.items()})
    (OUT / 'sources' / (stem + '.json')).write_text(json.dumps(receipt, indent=2) + '\n')
    print(f'Composed {title}: {handler.count:,} world circles; {handler.japan_count:,} intersect Japan viewport', flush=True)

def main():
    parser = argparse.ArgumentParser(description=__doc__); parser.add_argument('--band', choices=list(BANDS)); parser.add_argument('--compose-only', action='store_true'); args = parser.parse_args()
    if not args.compose_only: native_render()
    for band in [args.band] if args.band else BANDS: compose(band)
    if all((OUT / 'sources' / ('network-swarm-' + b + '.json')).exists() for b in BANDS):
        prior = json.loads((OUT / 'sources/swarm-cahill-keyes-superseded.json').read_text())
        audit = dict(renderer=str(BINARY), renderer_sha256=digest(BINARY), native_source='/home/bkoz/src/alpha60/src/a60-carto-geo.cc', source_revision=prior['source_revision'], cache_archive=prior['cache_archive'], geolocation_database=prior['geolocation_database'], input_mode='sample-cache-cumulative', projection='AuthaGraph', layout_frame_inches=[44, 19.052559], circle_encoding='Original Alpha60 member colours and native weighted radii, 5% opacity; no rescaling of source counts or sampling.', japan_layout='AuthaGraph geographic viewport; physical circle areas match the world scale; neighbouring countries can appear.', partitions=[json.loads((OUT / 'sources' / ('network-swarm-' + b + '.json')).read_text()) for b in BANDS])
        (OUT / 'sources/swarm-refresh.json').write_text(json.dumps(audit, indent=2) + '\n')

if __name__ == '__main__': main()
