#!/usr/bin/env python3
"""Compare scale and cyclic AuthaGraph registration without changing route geometry."""
import argparse
import copy
import json
import math
import re
import subprocess
from html import escape
from pathlib import Path

from legend_informatics import E, ROOT, XL, WIDTH, HEIGHT, SUFFIX, digest, el, text, save, legend_group, font_environment, register_fonts

VARIANTS = {
    'original-100': {'scale': 1.0, 'shift': 0.0, 'offset': 0.0},
    'centered-95': {'scale': 0.95, 'shift': 0.0, 'offset': 0.0},
    'shifted-95': {'scale': 0.95, 'shift': 0.0, 'offset': 1.1},
    'cyclic-95': {'scale': 0.95, 'shift': 4.4, 'offset': 0.0},
    'cyclic-43p5': {'scale': 43.5 / WIDTH, 'shift': 4.4, 'offset': 0.0},
}


def route_segments(path):
    result = []
    for fragment in path.split('M')[1:]:
        values = [float(s) for s in re.findall(r'[-+]?(?:\d*\.\d+|\d+)(?:[eE][-+]?\d+)?', fragment)]
        if len(values) % 2:
            raise ValueError('Unexpected fiber path coordinates')
        result.append(list(zip(values[::2], values[1::2])))
    return result


def boundary_pairs(root):
    records = []
    for node in root.xpath('//*[@data-fiber-route="true"]'):
        if node.get('data-cable-id') not in ('2africa', 'africa-coast-to-europe-ace', 'west-africa-cable-system-wacs'):
            continue
        ends = [point for segment in route_segments(node.get('d')) for point in (segment[0], segment[-1])]
        left = [p for p in ends if abs(p[0]) < 0.001]
        right = [p for p in ends if abs(p[0] - WIDTH) < 0.001]
        used = set()
        for point in left:
            choices = [(abs(point[1] - candidate[1]), i, candidate) for i, candidate in enumerate(right) if i not in used]
            if not choices:
                continue
            error, index, candidate = min(choices)
            if error > 0.001:
                continue
            used.add(index)
            records.append({'cable': node.get('data-cable-name'), 'feature': node.get('data-source-feature-id'),
                            'left': point, 'right': candidate, 'vertical_error_inches': error})
    return records


def make_plate(source, variant, settings, destination, with_legend=False, consolidate_antarctica=False):
    original = E.parse(str(source), E.XMLParser(huge_tree=True)).getroot()
    antarctic_inset=None;antarctic_receipt=None
    if consolidate_antarctica:
        from antarctica_inset import consolidate
        antarctic_inset,antarctic_receipt=consolidate(original)
    doc = el('svg', width='44in', height=f'{HEIGHT}in', viewBox=f'0 0 {WIDTH} {HEIGHT}', role='img',
             data_framing_variant=variant, data_source_sha256=digest(source))
    el('title', doc).text = source.stem + ' / ' + variant
    # Paint the ocean once, so repeated cyclic copies cannot mask a route or
    # gateway ring that crosses the old rectangular boundary.
    background='#fff'
    for group in original:
        if group.get('id','').endswith('-background') and 'display:none' not in group.get('style','').replace(' ',''):
            rectangle=next((node for node in group if E.QName(node).localname=='rect'),None)
            if rectangle is not None:
                styles=dict(p.strip().split(':',1) for p in rectangle.get('style','').split(';') if ':' in p)
                background=rectangle.get('fill',styles.get('fill',background))
    el('rect', doc, width=WIDTH, height=HEIGHT, fill='#fff')
    defs = el('defs', doc)
    art = el('g', defs, id='source-cartography')
    legends = []
    for child in original:
        identifier = child.get('id', '')
        if E.QName(child).localname in ('title', 'desc', 'metadata', 'namedview'):
            continue
        if legend_group(identifier):
            legends.append(copy.deepcopy(child))
            continue
        if identifier.endswith('-background'):
            continue
        art.append(copy.deepcopy(child))
    scale = settings['scale']
    dx = (WIDTH - WIDTH * scale) / 2 + settings['offset']
    dy = (HEIGHT - HEIGHT * scale) / 2
    frame = el('g', doc, transform=f'translate({dx} {dy}) scale({scale})')
    el('rect', frame, width=WIDTH, height=HEIGHT, fill=background)
    clip = el('clipPath', defs, id='cyclic-frame', clipPathUnits='userSpaceOnUse')
    el('rect', clip, width=WIDTH, height=HEIGHT)
    plot = el('g', frame, clip_path='url(#cyclic-frame)')
    if settings['shift']:
        copies = (settings['shift']-WIDTH, settings['shift'], settings['shift']+WIDTH)
    else:
        copies = (0,)
    for offset in copies:
        use = el('use', plot, transform=f'translate({offset} 0)')
        use.set('{'+XL+'}href', '#source-cartography')
    if antarctic_inset is not None:
        frame.append(antarctic_inset)
    if with_legend:
        editorial = el('g', frame, clip_path='url(#cyclic-frame)')
        for legend in legends:
            editorial.append(legend)
    # The scale study intentionally scales glyphs/strokes with the artwork;
    # the legend revision preserves approved physical strokes separately.
    save(doc, destination)
    return {'variant': variant, **settings, 'translation_inches': [dx, dy],
            'sheet_inches': [WIDTH, HEIGHT], 'image_inches': [WIDTH*scale, HEIGHT*scale],
            'margins_inches': {'left': dx, 'right': WIDTH-WIDTH*scale-dx, 'top': dy, 'bottom': dy},
            'cyclic_move_on_sheet_inches': settings['shift']*scale,
            'all_artwork_scaled_proportionally': True, 'legend_included': with_legend,
            'route_geometry_unchanged': True,'antarctica_adjustment':antarctic_receipt}


def write_report(output, records, pairs):
    """Keep the proof, measurements and comparison pages reproducible together."""
    from PIL import Image
    register_fonts()
    from reportlab.pdfgen.canvas import Canvas
    from reportlab.lib.pagesizes import A3
    from reportlab.lib.utils import ImageReader
    note=('Centering at 95% leaves the horizontal Africa joins separated by 41.8 inches. '
          'The cyclic move rejoins all 14 matched ACE, WACS and 2Africa endpoint pairs. '
          'It moves the seam through the Americas/Antarctica. This does not repair source discontinuities or surveyed routes.')
    html=['<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">',
          '<title>Setouchi Africa framing proof</title><style>body{font:18px/1.5 system-ui;max-width:1500px;margin:2rem auto;padding:0 1rem;color:#292722}img{width:100%;height:auto;border:1px solid #ddd}figure{margin:2rem 0}p{max-width:85ch}a{color:#503b75}table{border-collapse:collapse}td,th{padding:.5rem;border-bottom:1px solid #ddd;text-align:left}.scroll{overflow:auto}</style>',
          '<h1>Africa framing proof</h1><p>'+escape(note)+'</p><p><a href="framing-study.pdf">Framing study PDF</a> · <a href="measurements.json">Measurements and matched joins</a></p>',
          '<div class="scroll"><table><tr><th>Variant</th><th>Image width</th><th>Scale</th><th>Printed horizontal move</th></tr>']
    variants=list(dict.fromkeys(r['variant'] for r in records))
    for variant in variants:
        r=next(r for r in records if r['variant']==variant)
        html.append(f'<tr><td>{variant}</td><td>{r["image_inches"][0]:g}″</td><td>{100*r["scale"]:.6f}%</td><td>{r["cyclic_move_on_sheet_inches"]:g}″</td></tr>')
    html.append('</table></div>')
    if any(r['legend_included'] for r in records):
        html.append('<p>The legend stays at the right within the scaled image. The shifted South America overlaps part of the fiber legend; framing adoption and final legend position remain human review decisions. Print the full-size proof at actual size / 100%.</p>')
    validation=[];pdf_paths=[]
    for r in records:
        title=r['stem']+' / '+r['variant'];links=[]
        for key,label in [('svg','SVG'),('print_pdf','full-size PDF'),('print_png','300 dpi PNG')]:
            if key in r:links.append(f'<a href="{escape(r[key],quote=True)}">{label}</a>')
        if 'png' in r:html.append(f'<figure><h2>{escape(title)}</h2><img src="{r["png"]}" alt="{escape(title)}"><figcaption>'+ ' · '.join(links)+'</figcaption></figure>')
        if 'print_pdf' in r:
            path=output/r['print_pdf'];pdf_paths.append(str(path))
            info=subprocess.check_output(['pdfinfo',str(path)],text=True)
            w,h=map(float,re.search(r'Page size:\s+([\d.]+) x ([\d.]+)',info).groups())
            assert abs(w/72-WIDTH)<.001 and abs(h/72-HEIGHT)<.001
            with Image.open(output/r['print_png']) as image:
                assert image.size==(13200,5716)
                if r['variant']=='cyclic-43p5':
                    for box in [(0,0,74,5716),(13126,0,13200,5716),(0,0,13200,31),(0,5685,13200,5716)]:
                        assert all(extent==(255,255) for extent in image.crop(box).convert('RGB').getextrema())
            validation.append({'stem':r['stem'],'sheet_inches':[w/72,h/72],'pixels':[13200,5716],'margins_verified':r['variant']=='cyclic-43p5'})
    if pdf_paths:
        name='setouchi-43p5-shifted-proof.pdf' if variants==['cyclic-43p5'] else 'full-size-framing-proofs.pdf'
        subprocess.run(['pdfunite',*pdf_paths,str(output/name)],check=True)
        html.insert(5,f'<p><a href="{name}">Combined full-size proof PDF</a></p>')
    (output/'index.html').write_text('\n'.join(html)+'</html>\n')
    (output/'validation.json').write_text(json.dumps(validation,indent=2)+'\n')
    width,height=A3;canvas=Canvas(str(output/'framing-study.pdf'),pagesize=A3)
    canvas.setTitle('Setouchi ST2 — Africa framing study')
    for variant in variants:
        rows=[r for r in records if r['variant']==variant]
        canvas.setFont('Atkinson-Bold',22);canvas.drawString(36,height-42,'Africa framing / '+variant)
        first=rows[0];canvas.setFont('Atkinson-Regular',12)
        canvas.drawString(36,height-68,f"44 × {HEIGHT} in sheet; {first['image_inches'][0]:g} in image width; {100*first['scale']:.6f}%; horizontal move {first['cyclic_move_on_sheet_inches']:g} in.")
        for index,r in enumerate(rows):
            y=height-110-index*390;canvas.setFont('Atkinson-Bold',16);canvas.drawString(36,y,r['stem'])
            if 'png' in r:canvas.drawImage(ImageReader(output/r['png']),36,y-350,width=width-72,height=(width-72)*HEIGHT/WIDTH,mask='auto')
        canvas.setFont('Atkinson-Regular',11)
        lines=['14 matched ACE / WACS / 2Africa boundary pairs; source coordinates unchanged.',
               '95% shrink alone: 41.8-inch gap. Cyclic move: floating-point zero gap (<1.1e-14 inch).',
               'The seam moves through the Americas/Antarctica; disconnected source routes remain disconnected.',
               'With legends: shifted South America overlaps part of the fiber key. Final placement needs review.',
               'This comparison PDF scales images to the page. Use the full-size proof PDF for a 100% print.']
        for index,line in enumerate(lines):canvas.drawString(36,110-index*17,line)
        canvas.showPage()
    canvas.save()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--delivery', type=Path, default=ROOT/'output/setouchi-triennale-2028')
    parser.add_argument('--output', type=Path, default=ROOT/'output/setouchi-triennale-2028-st2/prototypes/africa-framing')
    parser.add_argument('--render', action='store_true')
    parser.add_argument('--variants', nargs='+', choices=VARIANTS, default=list(VARIANTS))
    parser.add_argument('--with-legend', action='store_true')
    parser.add_argument('--export-print', action='store_true', help='Export full-size PDF and 300 dpi PNG in addition to previews')
    args = parser.parse_args()
    env = font_environment()
    args.output.mkdir(parents=True, exist_ok=True)
    records = []
    source = args.delivery/'plates/world/svg'/('network-fiber'+SUFFIX+'.svg')
    pairs = boundary_pairs(E.parse(str(source), E.XMLParser(huge_tree=True)).getroot())
    for stem in ('network-fiber', 'network-groundstations'):
        source = args.delivery/'plates/world/svg'/(stem+SUFFIX+'.svg')
        for variant in args.variants:
            settings = VARIANTS[variant]
            target = args.output/'svg'/(stem+'-'+variant+'.svg')
            record = make_plate(source, variant, settings, target, args.with_legend)
            record.update(stem=stem, source_sha256=digest(source), svg=str(target.relative_to(args.output)))
            if stem == 'network-fiber':
                record['physical_fiber_width_pt'] = .5*settings['scale']
                record['fiber_opacity'] = .75
                record['old_horizontal_seam_pairs'] = len(pairs)
                record['old_seam_visual_gap_inches'] = max((
                    settings['scale'] * math.hypot(
                        ((p['left'][0]+settings['shift']) % WIDTH)-((p['right'][0]+settings['shift']) % WIDTH)
                        if settings['shift'] else p['left'][0]-p['right'][0],
                        p['left'][1]-p['right'][1]) for p in pairs), default=None)
            if args.render or args.export_print:
                png = args.output/'png'/target.with_suffix('.png').name
                png.parent.mkdir(parents=True, exist_ok=True)
                log = args.output/(stem+'-'+variant+'.log')
                with log.open('w') as stream:
                    subprocess.run(['inkscape',str(target),'--export-area-page','--export-width=3840',
                                    '--export-background=white','--export-background-opacity=255',
                                    '--export-filename='+str(png)],env=env,stdout=stream,stderr=subprocess.STDOUT,check=True)
                record['png'] = str(png.relative_to(args.output))
            if args.export_print:
                for extension, options in [('pdf', []), ('png', ['--export-dpi=300'])]:
                    export = args.output/('print-'+extension)/target.with_suffix('.'+extension).name
                    export.parent.mkdir(parents=True, exist_ok=True)
                    with (args.output/(stem+'-'+variant+'-'+extension+'.log')).open('w') as stream:
                        subprocess.run(['inkscape',str(target),'--export-area-page',*options,
                                        '--export-filename='+str(export)],env=env,stdout=stream,stderr=subprocess.STDOUT,check=True)
                    record['print_'+extension] = str(export.relative_to(args.output))
            records.append(record)
            print(stem, variant, flush=True)
    (args.output/'measurements.json').write_text(json.dumps({'variants':records,'matched_boundary_pairs':pairs},indent=2)+'\n')
    if args.render or args.export_print:write_report(args.output,records,pairs)


if __name__ == '__main__':
    main()
