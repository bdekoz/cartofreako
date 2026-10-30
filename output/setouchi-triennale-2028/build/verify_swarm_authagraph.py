#!/usr/bin/env python3
"""Compare native circle encodings before/after projection; audit transparent land."""
from pathlib import Path
from collections import Counter
from lxml import etree as E
import json, math, re, xml.sax

OUT = Path(__file__).resolve().parents[1]

class Circles(xml.sax.ContentHandler):
    def __init__(self, native=False):
        self.native = native; self.depth = 0; self.active = not native
        self.counts = Counter(); self.styles = {}; self.style_text = ''; self.in_style = False
        self.transforms = []; self.root = None
    def startElement(self, name, attrs):
        self.depth += 1
        if self.depth == 1: self.root = dict(attrs)
        if self.native and self.depth == 2:
            self.active = attrs.get('id', '').startswith('vector-peer-clouds-')
        if name == 'style': self.in_style = True
        if name == 'g' and 'transform' in attrs: self.transforms.append(attrs['transform'])
        if name == 'circle' and self.active:
            self.counts[(float(attrs['r']), attrs.get('style', attrs.get('class')))] += 1
    def endElement(self, name):
        if name == 'style': self.in_style = False
        if self.native and self.depth == 2: self.active = False
        self.depth -= 1
    def characters(self, text):
        if self.in_style: self.style_text += text
    def normalized(self, radius_scale=1):
        styles = dict(re.findall(r'\.([\w-]+)\{([^}]+)\}', self.style_text))
        result = Counter()
        for (radius, style), count in self.counts.items():
            style = styles.get(style, style).replace(' ', '')
            assert 'fill-opacity:0.05;' in style or style.endswith('fill-opacity:0.05')
            result[(round(radius * radius_scale, 7), style)] += count
        return result

def read(path, native=False):
    result = Circles(native); xml.sax.parse(str(path), result); return result

def main():
    old = json.loads((OUT / 'sources/swarm-cahill-keyes-superseded.json').read_text())
    current = json.loads((OUT / 'sources/swarm-refresh.json').read_text())
    rows = []
    for index, partition in enumerate(current['partitions']):
        before = read(Path(old['panels'][index]['source']), True)
        native = read(Path(partition['source']), True)
        world = read(OUT / partition['output_files']['world'])
        japan = read(OUT / partition['output_files']['japan'])
        expected = before.normalized()
        assert native.normalized() == expected, 'Native circle radii or colours changed'
        assert world.normalized() == expected, 'Composited world circle encodings changed'
        fitted = japan.normalized(partition['japan_geographic_scale'])
        assert all(count <= expected[key] for key, count in fitted.items())
        assert sum(world.counts.values()) == partition['native_circles']
        assert sum(japan.counts.values()) == partition['japan_visible_circles']
        for plate in [world, japan]:
            assert plate.root['data-projection'] == 'authagraph'
            assert plate.root['data-resolution-partition'] == partition['band']
            assert 'scale(0.010416666666666666)' in plate.transforms
        rows.append(dict(band=partition['band'], world_circles=sum(expected.values()),
            japan_circles=sum(fitted.values()), native_radius_colour_opacity_histogram='exact match',
            japan_physical_radius_scale='matches world; geographic enlargement compensated'))
        print('Verified circle conservation:', partition['band'], flush=True)
    atmosphere = []
    for scope in ['world', 'japan']:
        path = next((OUT / f'plates/{scope}/svg').glob('cloud-atmosphere-*.svg'))
        root = E.parse(str(path)); land = root.xpath('//*[@id="terrestrial-land"]')[0]
        paths = land.xpath('.//*[local-name()="path"]'); assert paths
        for path in paths:
            style = dict(part.strip().split(':', 1) for part in path.get('style', '').split(';') if ':' in part)
            assert float(style.get('fill-opacity', path.get('fill-opacity', 1))) == 0
            assert float(style.get('stroke-opacity', path.get('stroke-opacity', 1))) == 0
        coast = root.xpath('//*[@id="terrestrial-coastline"]')[0]
        # These layers share a parent; coastline follows transparent land and fields.
        assert land.getparent() is coast.getparent()
        siblings = list(land.getparent()); assert siblings.index(coast) > siblings.index(land)
        atmosphere.append(dict(scope=scope, land_paths=len(paths), fill_opacity=0,
                               visible_outline='separate foreground coastline'))
    receipt = dict(status='passed', partitions=rows, atmosphere=atmosphere,
        note='Original cumulative cache unchanged; projection and plate layout changed. Circle histogram includes every native radius and member colour.')
    (OUT / 'sources/swarm-authagraph-validation.json').write_text(json.dumps(receipt, indent=2) + '\n')
    print('Verified separate AuthaGraph plates and zero-opacity foreground land', flush=True)

if __name__ == '__main__': main()
