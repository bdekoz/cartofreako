"""Hourly SGP4 calculations with fixed celestial framing and audited exports."""
import argparse
from concurrent.futures import ThreadPoolExecutor
from copy import deepcopy
from datetime import datetime, timedelta, timezone
import hashlib
import importlib
import json
import math
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import threading
from fractions import Fraction
from zoneinfo import ZoneInfo

import numpy as np
from PIL import Image, ImageDraw, ImageFont
from lxml import etree as E

import atlas_world as WORLD
import starlink_star_light as S
from atlas_presentation import settings
from dataset import ROOT, atomic_json, digest
from legend_informatics import FONT_DIR, font_environment, register_fonts

PACIFIC = ZoneInfo('America/Los_Angeles')
STEM = 'orbital-technosphere-observer'
SCHEMA = 'cartofreako-observer-hourly-v1'
COMPOSE_LOCK = threading.Lock()


def require(condition, message):
    if not condition:
        raise ValueError(message)


def report(message):
    print(datetime.now(PACIFIC).strftime('%Y-%m-%d %H:%M:%S %Z') + ': ' + message, flush=True)


def instant(value):
    result = datetime.fromisoformat(value.replace('Z', '+00:00'))
    require(result.utcoffset() is not None, 'Calculation timestamps need an explicit timezone')
    return result.astimezone(timezone.utc)


def timestamp(value):
    return value.astimezone(timezone.utc).isoformat(timespec='seconds').replace('+00:00', 'Z')


def schedule(start, count=24, step_minutes=60):
    require(count > 0 and step_minutes > 0, 'Frame count and time step must be positive')
    start = instant(start) if isinstance(start, str) else start
    return [start + timedelta(minutes=i * step_minutes) for i in range(count)]


def sidereal_degrees(value, longitude):
    """Reproduce this renderer's SGP4 GMST/UTC-Julian-date convention."""
    jd = value.timestamp() / 86400 + 2440587.5
    t = (jd - 2451545) / 36525
    seconds = -6.2e-6*t**3 + .093104*t*t + (876600*3600 + 8640184.812866)*t + 67310.54841
    return (seconds / 240 + longitude) % 360


def derived_profile(profile, directory, value):
    result = deepcopy(profile)
    def resolve(item):
        if isinstance(item, dict):
            for key, child in item.items():
                if key in ('file', 'checksum_file', 'receipt_file') and isinstance(child, str):
                    item[key] = str((directory / child).resolve())
                else:
                    resolve(child)
        elif isinstance(item, list):
            for child in item:
                resolve(child)
    resolve(result)
    result['timestamp'] = timestamp(value)
    return result


def fingerprint(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(',', ':')).encode()).hexdigest()


def file_record(path, output):
    return {'path': path.relative_to(output).as_posix(), 'sha256': digest(path), 'bytes': path.stat().st_size}


def files_match(records, output):
    return all((output/r['path']).is_file() and (output/r['path']).stat().st_size == r['bytes']
               and digest(output/r['path']) == r['sha256'] for r in records)


def copy_file(source, target):
    target.parent.mkdir(parents=True, exist_ok=True)
    if source.resolve() != target.resolve():
        shutil.copy2(source, target)


def snapshot_inputs(profile_path, renderer, output, accepted):
    profile = json.loads(profile_path.read_text())
    checksum_path = profile_path.parent/profile['snapshot']['checksum_file']
    for line in checksum_path.read_text().splitlines():
        if not line.strip():
            continue
        expected, name = line.split(maxsplit=1)
        source = (profile_path.parent/name.lstrip('*')).resolve()
        require(source.is_relative_to(profile_path.parent.resolve()), 'Checksum path escapes catalog directory')
        require(digest(source) == expected, 'Pinned catalog checksum mismatch: '+source.name)
    target = output/'sources/orbital'
    for source in sorted(profile_path.parent.iterdir()):
        if source.is_file():
            copy_file(source, target/source.name)
    copy_file(renderer, output/'sources/renderer/generate-orbiting')
    require(accepted.is_file() or (output/'sources/accepted-frame-zero.svg').is_file(),
            'The accepted World observer plate is required for frame-zero verification')
    if accepted.is_file():
        copy_file(accepted, output/'sources/accepted-frame-zero.svg')
    for source in FONT_DIR.iterdir():
        if source.is_file():
            copy_file(source, output/'assets/fonts'/source.name)
    # Retain the actual Python implementation and its local imports, style
    # configuration, font bytes and native executable used for this delivery.
    modules = {Path(m.__file__).resolve() for m in list(sys.modules.values())
               if getattr(m, '__file__', None) and str(m.__file__).endswith('.py')
               and Path(m.__file__).resolve().is_relative_to(ROOT/'scripts')}
    modules |= {ROOT/'scripts/build-observer-hourly.py', ROOT/'scripts/observer-hourly-viewer.html',
                ROOT/'scripts/observer-hourly-viewer.js', ROOT/'scripts/run-inkscape.sh', ROOT/'generation-style.json'}
    modules |= {ROOT/p for p in (S.STYLE['atlas']['presentation']['recipe_file'],
                                S.STYLE['atlas']['presentation']['groundstation_recipe_file'],
                                S.STYLE['atlas']['presentation']['world_recipe_file'])}
    modules |= {p for p in FONT_DIR.iterdir() if p.is_file()}
    code = {}
    for source in sorted(modules):
        relative = source.relative_to(ROOT)
        code[str(relative)] = digest(source)
        copy_file(source, output/'sources/implementation'/relative)
    inputs = {p.name: digest(p) for p in sorted(target.iterdir()) if p.is_file()}
    return target/profile_path.name, {'catalog_files': inputs, 'implementation_files': code,
                                    'renderer_sha256': digest(output/'sources/renderer/generate-orbiting'),
                                    'accepted_frame_zero_sha256': digest(output/'sources/accepted-frame-zero.svg'),
                                    'original_profile_sha256': digest(profile_path)}


def paths(root, prefix):
    return [(n.get('id'), n.get('d')) for n in root.xpath('//*[starts-with(@id,$p)]', p=prefix)
            if E.QName(n).localname == 'path']


def inventory(root):
    marks = root.xpath('//*[@data-object-kind="locpoint"]')
    result = [{k.removeprefix('data-'): v for k, v in n.attrib.items() if k.startswith('data-')}
              for n in marks]
    ids = [r['norad-id'] for r in result]
    require(len(ids) == len(set(ids)), 'Duplicate plotted NORAD objects')
    require(all(float(r['observer-elevation-deg']) >= -0.000001 for r in result), 'Below-horizon object plotted')
    return result


def science_inventory(records):
    fields = ('norad-id', 'name', 'role', 'element-epoch', 'element-age-days', 'observer-azimuth-deg',
              'observer-elevation-deg', 'topocentric-ra-deg', 'topocentric-dec-deg', 'sunlit')
    return {r['norad-id']: {k: r[k] for k in fields} for r in records}


def validate_geometry(native, plate, reference=None):
    records = inventory(native)
    meta = native.xpath('//*[@id="orbital-technosphere-metadata"]')[0]
    require(len(records) == int(meta.get('data-visible-records')), 'Plotted count differs from native metadata')
    require(int(meta.get('data-failed-propagation')) == 0, 'A native propagation failed')
    require(science_inventory(records) == science_inventory(inventory(plate)), 'Compositor changed scientific values')
    for kind in ('observer-horizon', 'celestial-equator'):
        require(paths(native, kind) and paths(native, kind) == paths(plate, kind), 'Compositor changed '+kind)
    require(float(plate.get('data-image-scale')) == S.FRAMING.SCALE, 'Observer scale changed')
    for n in plate.xpath('//*[@data-role="debris" and @data-marker-shape="x"]'):
        require(S.css(n.attrib)['stroke'] == '#ffffff', 'Debris marker is not white')
    for n in plate.xpath('//*[@id="starlink-name"]/*'):
        require(abs(float(n.get('font-size')) * 72 * S.FRAMING.SCALE - 6) < 1e-8, 'Name type is not 6 pt')
    if reference is not None:
        require(science_inventory(inventory(reference)) == science_inventory(records), 'Frame zero differs from accepted scientific population')
        for kind in ('observer-horizon', 'celestial-equator'):
            require(paths(reference, kind) == paths(plate, kind), 'Frame-zero reference geometry changed')
        before = {n.get('data-norad-id'): dict(n.attrib) for n in reference.xpath('//*[@data-object-kind="locpoint"]')}
        after = {n.get('data-norad-id'): dict(n.attrib) for n in plate.xpath('//*[@data-object-kind="locpoint"]')}
        require(before == after, 'Frame-zero marker styling differs from accepted World plate')
    return records, dict(meta.attrib)


def names_hidden(root):
    result = deepcopy(root)
    for node in result.xpath('//*[@data-object-kind="name" or @data-object-kind="id"]'):
        node.getparent().remove(node)
    return result


def orientation_only(root):
    result = deepcopy(root)
    source = result.xpath('//*[@id="source-cartography"]')[0]
    for child in list(source):
        reference_curves = child.xpath('.//*[starts-with(@id,"observer-horizon") or starts-with(@id,"celestial-equator")]')
        if not reference_curves and E.QName(child).localname != 'metadata':
            source.remove(child)
    require(paths(result, 'observer-horizon') and paths(result, 'celestial-equator'), 'Orientation view lost its reference curves')
    require(not result.xpath('//*[@data-object-kind]'), 'Orientation view retains satellite marks')
    return result


def run(command, env=None, log=None):
    result = subprocess.run([str(v) for v in command], env=env, stdout=subprocess.PIPE,
                            stderr=subprocess.STDOUT, text=True)
    if log:
        log.parent.mkdir(parents=True, exist_ok=True)
        with log.open('a') as stream:
            stream.write(result.stdout)
    require(result.returncode == 0, 'Command failed: '+str(command[0])+'\n'+result.stdout[-2500:])
    return result.stdout


def export_svg(svg, pdf, png, width, env, log):
    for target in (pdf, png):
        if target is None:
            continue
        target.parent.mkdir(parents=True, exist_ok=True)
        command = ['bash', ROOT/'scripts/run-inkscape.sh', 'inkscape', svg, '--export-area-page',
                   '--export-filename='+str(target)]
        if target == png:
            command += ['--export-width='+str(width)]
        run(command, env=env, log=log)
    if pdf:
        info = run(['pdfinfo', pdf])
        match = re.search(r'Page size:\s+([\d.]+) x ([\d.]+) pts', info)
        bounds = S.read_svg(svg).get('viewBox').split()
        require(match and all(abs(float(a)-float(b)*72) < .12 for a, b in zip(match.groups(), bounds[2:])),
                'PDF page dimensions do not match the source SVG')


def font(size, bold=False):
    pattern = '*Bold*' if bold else '*Regular*'
    candidates = sorted(FONT_DIR.glob(pattern+'.ttf'))
    require(candidates, 'Bundled Atkinson font unavailable')
    return ImageFont.truetype(str(candidates[0]), size)


def draw_text(draw, xy, value, size, color=S.FG, bold=False, anchor=None):
    selected = font(size, bold)
    bbox = draw.textbbox(xy, value, font=selected, anchor=anchor)
    require(bbox[0] >= 0 and bbox[1] >= 0 and bbox[2] <= draw.im.size[0] and bbox[3] <= draw.im.size[1],
            'Video label exceeds the canvas: '+value)
    draw.text(xy, value, font=selected, fill=color, anchor=anchor)


def compose_video_frame(preview, target, row, width=1920, height=1080):
    require((width, height) == (1920, 1080), 'This reviewed layout requires a 1920 × 1080 canvas')
    canvas = Image.new('RGB', (width, height), S.BG)
    with Image.open(preview) as im:
        require(im.width == width, 'Video plate preview has the wrong width')
        require(abs(im.height - width*S.HEIGHT/S.WIDTH) <= 1, 'Video plate aspect ratio changed')
        y = (height-im.height)//2
        canvas.paste(im.convert('RGB'), (0, y))
    draw = ImageDraw.Draw(canvas)
    local = instant(row['timestamp']).astimezone(PACIFIC)
    draw_text(draw, (36, 17), 'STARLINK STAR LIGHT  /  HOURLY OBSERVER', 24, bold=True)
    draw_text(draw, (36, 59), local.strftime('%b %d, %Y  %I:%M %p %Z'), 36, bold=True)
    draw_text(draw, (850, 65), instant(row['timestamp']).strftime('%Y-%m-%d  %H:%M UTC'), 30)
    limit = f'{row["main_sequence_count"]-1:02d}' if row['index'] < row['main_sequence_count'] else 'ENDPOINT'
    draw_text(draw, (1884, 62), f'HOUR {row["index"]:02d} / {limit}', 32, bold=True, anchor='ra')
    draw_text(draw, (36, 971), 'SAN FRANCISCO  /  37.7749° N, 122.4194° W  /  16 m  /  elevation ≥ 0°', 25)
    draw_text(draw, (1884, 971), f'Model sidereal orientation  {row["sidereal_degrees"]:.3f}°', 25, anchor='ra')
    draw_text(draw, (36, 1007), f'{row["plotted"]:,} plotted  /  {row["epoch_exclusions"]} epoch exclusions  /  '
              f'{row["propagation_failures"]} propagation failures  /  frozen November 9 catalog', 25)
    draw_text(draw, (36, 1043), 'Hourly calculated states; not continuous trajectories. Names retained in SVG/PDF and viewer.', 22)
    draw.line((1430, 1057, 1475, 1057), fill=S.FG, width=3)
    draw_text(draw, (1487, 1043), 'horizon', 22)
    draw.line((1635, 1057, 1680, 1057), fill='#716052', width=2)
    draw_text(draw, (1692, 1043), 'celestial equator', 22)
    target.parent.mkdir(parents=True, exist_ok=True)
    canvas.save(target)


def build_frame(index, value, profile, profile_path, output, common, env, preview_width, video_count):
    base = output/'frames'/f'{index:02d}'
    base.mkdir(parents=True, exist_ok=True)
    derived = derived_profile(profile, profile_path.parent, value)
    key = fingerprint({'common': common, 'profile': derived, 'preview_width': preview_width})
    receipt = base/'frame.json'
    if receipt.is_file():
        old = json.loads(receipt.read_text())
        if old.get('fingerprint') == key and files_match(old['files'], output):
            report(f'Frame {index:02d}: verified cached exports')
            return old
    atomic_json(base/'profile.json', derived)
    native_dir = base/'native'
    native_dir.mkdir(exist_ok=True)
    log = base/'render.log'
    result = subprocess.run([str(output/'sources/renderer/generate-orbiting'), 'authagraph', 'observer',
                             str(base/'profile.json')], cwd=native_dir, env=env,
                            stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
    log.write_text(result.stdout)
    require(result.returncode == 0, f'Native frame {index:02d} failed: '+result.stdout[-2000:])
    native = S.read_svg(native_dir/(STEM+S.SUFFIX+'.svg'))
    _, recipe = settings(S.STYLE)
    with COMPOSE_LOCK:
        plate, legend, layout = WORLD.compose(STEM, native, base, recipe, orbital_profile=base/'profile.json')
    reference = output/'sources/accepted-frame-zero.svg'
    accepted = S.read_svg(reference) if index == 0 and value == instant(profile['timestamp']) and reference.is_file() else None
    records, metadata = validate_geometry(native, plate, accepted)
    require(metadata['data-timestamp'] == timestamp(value), 'Native timestamp differs from scheduled hour')
    row = {'index': index, 'main_sequence_count': video_count,
           'elapsed_minutes': index*common['step_minutes'], 'timestamp': timestamp(value),
           'pacific_timestamp': value.astimezone(PACIFIC).isoformat(),
           'pacific_label': value.astimezone(PACIFIC).strftime('%b %d, %Y %I:%M %p %Z'),
           'sidereal_degrees': sidereal_degrees(value, profile['reference_point']['longitude_deg_east']),
           'plotted': len(records), 'propagated': int(metadata['data-propagated-records']),
           'epoch_exclusions': int(metadata['data-skipped-stale']),
           'propagation_failures': int(metadata['data-failed-propagation']),
           'layout': layout, 'equator_sha256': fingerprint(paths(native, 'celestial-equator')),
           'horizon_sha256': fingerprint(paths(native, 'observer-horizon')), 'fingerprint': key,
           'accepted_frame_zero_verified': accepted is not None}
    for tree in (plate, legend):
        tree.set('data-hourly-index', str(index))
        tree.set('data-hourly-calculation', row['timestamp'])
        tree.set('data-hourly-sidereal-degrees', str(row['sidereal_degrees']))
    plate.xpath('./*[local-name()="title"]')[0].text = 'Hourly observer / '+row['pacific_label']+' / '+row['timestamp']
    for node in legend.xpath('//*[local-name()="text"]'):
        if node.text and node.text.startswith('World  |'):
            node.text = f'World  |  Hour {index:02d}  |  '+row['pacific_label']+'  /  '+row['timestamp']
        if node.text and node.text.startswith('STARLINK STAR LIGHT / v3'):
            node.text = f'STARLINK STAR LIGHT / v4 HOURLY / HOUR {index:02d} / WORLD / A3 landscape / 420 x 297 mm'
    S.save(plate, base/'map.svg')
    S.save(legend, base/'legend.svg')
    S.save(names_hidden(plate), base/'overview.svg')
    S.save(orientation_only(plate), base/'orientation.svg')
    atomic_json(base/'objects.json', records)
    atomic_json(base/'native-metadata.json', metadata)
    export_svg(base/'map.svg', base/'map.pdf', base/'preview.png', preview_width, env, log)
    export_svg(base/'legend.svg', base/'legend.pdf', base/'legend.png', 1800, env, log)
    export_svg(base/'overview.svg', None, base/'overview.png', 1920, env, log)
    boxes = S.query_boxes(base/'legend.svg', env)
    page_w, page_h = (float(v)*96 for v in legend.get('viewBox').split()[2:])
    for ident in (legend.get('id'), 'observer-notes'):
        require(ident in boxes, 'Legend bounding box is missing')
        x,y,w,h = boxes[ident]
        require(min(x,y) >= -.1 and x+w <= page_w+.1 and y+h <= page_h+.1,
                f'Legend artwork exceeds the page in frame {index:02d}')
    compose_video_frame(base/'overview.png', base/'video.png', row)
    row['files'] = [file_record(p, output) for p in sorted(base.rglob('*'))
                    if p.is_file() and p.name not in ('frame.json', 'render.log')]
    row['map'] = (base/'map.svg').relative_to(output).as_posix()
    row['map_pdf'] = (base/'map.pdf').relative_to(output).as_posix()
    row['legend_pdf'] = (base/'legend.pdf').relative_to(output).as_posix()
    row['preview'] = (base/'preview.png').relative_to(output).as_posix()
    row['video_frame'] = (base/'video.png').relative_to(output).as_posix()
    row['orientation'] = (base/'orientation.svg').relative_to(output).as_posix()
    atomic_json(receipt, row)
    report(f'Frame {index:02d}: {row["plotted"]} plotted, {row["epoch_exclusions"]} epoch exclusions; SVG/PDF/PNG passed')
    return row


def validate_sequence(rows, profile, step_minutes, main_count):
    require(len(rows) >= main_count and [r['index'] for r in rows] == list(range(len(rows))), 'Hourly sequence is incomplete or out of order')
    times = [instant(r['timestamp']) for r in rows]
    require(all((b-a).total_seconds() == step_minutes*60 for a,b in zip(times,times[1:])), 'Missing or repeated calculation hour')
    require(len({r['equator_sha256'] for r in rows}) == 1, 'Celestial equator moved between frames')
    require(len({fingerprint(r['layout']) for r in rows}) == 1, 'Camera, scale or cyclic framing changed')
    require(len({r['horizon_sha256'] for r in rows}) == len(rows), 'An hourly horizon was reused')
    for row in rows:
        require(row['pacific_timestamp'] == instant(row['timestamp']).astimezone(PACIFIC).isoformat(), 'Pacific timestamp is wrong')
        require(row['propagation_failures'] == 0, 'Propagation failure in hourly sequence')
    if times[0] == instant('2026-11-09T01:12:00Z') and step_minutes == 60:
        for index, expected in ((0,(972,46,17956)), (12,(1008,50,17952)), (24,(964,55,17947))):
            if index < len(rows):
                r = rows[index]
                require((r['plotted'],r['epoch_exclusions'],r['propagated']) == expected, 'Previously checked native calculation changed at hour '+str(index))
    return {'status': 'passed', 'ordered_timestamps': True, 'fixed_equator_and_framing': True,
            'independent_hourly_propagation': True, 'native_canaries_reproduced': True,
            'frame_count': main_count, 'retained_endpoint_proof': len(rows) > main_count}


def viewer_svg(svg, previous):
    root = S.read_svg(svg)
    if previous:
        bank = S.el('g', root.xpath('//*[@id="source-cartography"]')[0], id='previous-hour-horizon')
        for index, (_, d) in enumerate(paths(S.read_svg(previous), 'observer-horizon')):
            S.el('path', bank, id=f'previous-hour-horizon-{index}', d=d, fill='none', stroke='#39d4e0',
                 stroke_width='.035', stroke_dasharray='.15 .10', stroke_opacity='.9')
    return E.tostring(root, encoding='unicode')


def write_viewer(output, rows, manifest):
    frames = []
    for index,row in enumerate(rows):
        previous = output/rows[index-1]['map'] if index else None
        frames.append({**{k:row[k] for k in ('index','timestamp','pacific_label','sidereal_degrees','plotted','epoch_exclusions',
                                           'propagation_failures','preview','map','map_pdf','legend_pdf')},
                       'full_svg': viewer_svg(output/row['map'], previous),
                       'orientation_svg': viewer_svg(output/row['orientation'], previous)})
    value = {'frames': frames, 'seconds_per_plate': manifest['seconds_per_plate'], 'video': manifest['video_filename']}
    (output/'frames.js').write_text('window.OBSERVER_SEQUENCE = '+json.dumps(value, separators=(',', ':')).replace('<', '\\u003c')+';\n')
    copy_file(ROOT/'scripts/observer-hourly-viewer.html', output/'index.html')
    copy_file(ROOT/'scripts/observer-hourly-viewer.js', output/'viewer.js')


def contact_sheet(output, rows):
    from reportlab.pdfgen import canvas
    from reportlab.lib.colors import HexColor
    from reportlab.lib.utils import ImageReader
    register_fonts()
    width,height = 594/25.4*72, 420/25.4*72
    target = output/'observer-hourly-contact-sheet.pdf'
    pdf = canvas.Canvas(str(target), pagesize=(width,height), pageCompression=1)
    pdf.setTitle('Starlink Star Light v4 / 24 hourly observer states')
    pdf.setFillColor(HexColor('#fff9eb')); pdf.rect(0,0,width,height,fill=1,stroke=0)
    pdf.setFillColor(HexColor(S.BG)); pdf.setFont('Atkinson-Bold',27)
    pdf.drawString(36,height-43,'STARLINK STAR LIGHT / HOURLY OBSERVER')
    pdf.setFont('Atkinson-Regular',14)
    pdf.drawString(36,height-66,'Frozen November 9 catalog / San Francisco / one calculated state each hour / Pacific Standard Time')
    columns = 4; row_count = math.ceil(len(rows)/columns)
    cw=(width-72)/columns; ch=(height-112)/row_count
    for index,row in enumerate(rows):
        x=36+(index%columns)*cw; top=height-85-(index//columns)*ch
        pdf.setFont('Atkinson-Bold',14)
        pdf.drawString(x+8,top-15,f'{index:02d}  '+instant(row['timestamp']).astimezone(PACIFIC).strftime('%b %d  %I:%M %p PST'))
        iw=min(cw-16,(ch-45)*S.WIDTH/S.HEIGHT); ih=iw*S.HEIGHT/S.WIDTH
        pdf.drawImage(ImageReader(output/'frames'/f'{index:02d}'/'overview.png'),x+(cw-iw)/2,top-24-ih,iw,ih)
        pdf.setFont('Atkinson-Regular',11)
        pdf.drawString(x+8,top-ch+9,f'{row["plotted"]:,} plotted / {row["epoch_exclusions"]} excluded / LST {row["sidereal_degrees"]:.2f}°')
    pdf.setFont('Atkinson-Regular',12)
    pdf.drawString(36,20,'Fixed projection, camera and celestial equator. Hourly states are not continuous trajectories. Names are available in individual SVG/PDF plates.')
    pdf.save()
    run(['pdftoppm','-singlefile','-scale-to','2200','-png',target,output/'observer-hourly-contact-sheet'])


def encode_video(output, rows, seconds):
    frames=output/'frames-1080p';frames.mkdir(exist_ok=True)
    for index,row in enumerate(rows):
        copy_file(output/row['video_frame'], frames/f'frame-{index:02d}.png')
    chapters=[';FFMETADATA1','title=Starlink Star Light v4 / hourly observer','comment=Frozen November 9 catalog; discrete hourly SGP4 states; no interpolation']
    for index,row in enumerate(rows):
        chapters += ['[CHAPTER]','TIMEBASE=1/1000',f'START={round(index*seconds*1000)}',
                     f'END={round((index+1)*seconds*1000)}',f'title=Hour {index:02d} / {row["timestamp"]} / {row["pacific_label"]}']
    (output/'chapters.ffmetadata').write_text('\n'.join(chapters)+'\n')
    name=f'observer-hourly-{len(rows)}-plates-{len(rows)*seconds:g}s.mkv'
    duration = Fraction(str(seconds))
    command=['ffmpeg','-y','-v','error','-threads','2','-framerate',f'{duration.denominator}/{duration.numerator}','-start_number','0',
             '-i',str(frames/'frame-%02d.png'),'-f','ffmetadata','-i',str(output/'chapters.ffmetadata'),
             '-map','0:v:0','-map_metadata','1','-map_chapters','1','-an','-vf','setsar=1',
             '-c:v','libx264','-threads','2','-preset','medium','-crf','18','-pix_fmt','yuv420p',
             '-r','30','-fps_mode','cfr','-frames:v',str(round(len(rows)*seconds*30)),str(output/name)]
    run(command,log=output/'video-encoding.log')
    return name


def validate_video(path, output, rows, seconds):
    probe=json.loads(run(['ffprobe','-v','error','-count_frames','-show_streams','-show_format','-show_chapters','-of','json',path]))
    streams=probe['streams'];require(len(streams)==1 and streams[0]['codec_type']=='video','Video must have no audio or extra streams')
    stream=streams[0]
    expected=len(rows)*seconds
    require((stream['codec_name'],stream['width'],stream['height'],stream['pix_fmt'],stream['r_frame_rate'],stream['sample_aspect_ratio'])
            ==('h264',1920,1080,'yuv420p','30/1','1:1'),'Encoded video format differs from the specification')
    require(int(stream['nb_read_frames']) == round(expected*30) and abs(float(probe['format']['duration'])-expected)<.001,
            'Video frame count or duration differs from the schedule')
    require(len(probe['chapters'])==len(rows),'Missing hourly video chapters')
    for index,chapter in enumerate(probe['chapters']):
        require(abs(float(chapter['start_time'])-index*seconds)<.001 and abs(float(chapter['end_time'])-(index+1)*seconds)<.001,
                'Video chapter timing differs from its hourly hold')
    # Decode every output frame. Classify it against every scheduled source
    # image; lossy H.264 pixels may differ, but none may cross an hour boundary.
    filter_value='scale=256:144:flags=area,format=gray'
    reference=subprocess.check_output(['ffmpeg','-v','error','-threads','2','-framerate','1','-i',str(output/'frames-1080p/frame-%02d.png'),
                                       '-frames:v',str(len(rows)),'-vf',filter_value,'-threads','2','-f','rawvideo','-pix_fmt','gray','pipe:1'])
    reference=np.frombuffer(reference,dtype=np.uint8).reshape(len(rows),144,256).astype(np.int16)
    process=subprocess.Popen(['ffmpeg','-v','error','-threads','2','-i',str(path),'-vf',filter_value,'-threads','2',
                              '-f','rawvideo','-pix_fmt','gray','pipe:1'],stdout=subprocess.PIPE)
    counts=[0]*len(rows); maximum=0.0; n=0; size=144*256
    try:
        while True:
            frame=process.stdout.read(size)
            if not frame:break
            require(len(frame)==size,'Truncated decoded frame')
            image=np.frombuffer(frame,dtype=np.uint8).reshape(144,256).astype(np.int16)
            delta=(reference-image).astype(np.float32)
            error=np.mean(delta*delta,axis=(1,2))
            selected=int(np.argmin(error));expected_index=int(n//round(seconds*30))
            require(selected==expected_index,'Decoded video frame does not match its scheduled hourly plate: '+str(n))
            maximum=max(maximum,float(error[selected]));counts[selected]+=1;n+=1
    finally:
        process.stdout.close()
        code=process.wait()
    require(code==0 and counts==[round(seconds*30)]*len(rows),'Incorrect first, intermediate or final plate hold')
    result={'status':'passed','codec':'h264','pixel_format':'yuv420p','size':[1920,1080], 'fps':30,
            'duration_seconds':float(probe['format']['duration']),'decoded_frames':n,'hourly_frame_counts':counts,
            'all_decoded_frames_match_scheduled_plate':True,'maximum_reduced_frame_mse':maximum,'audio_streams':0,
            'chapters':len(probe['chapters'])}
    atomic_json(output/'validation/video.json',result)
    return result


def verify(output, video=True):
    manifest=json.loads((output/'manifest.json').read_text())
    require(manifest.get('status')=='complete' and manifest.get('schema')==SCHEMA,'Delivery is incomplete')
    require(files_match(manifest['files'],output),'A delivery artifact changed or is missing')
    rows=manifest['frames'];profile=json.loads((output/'sources/orbital'/manifest['profile_filename']).read_text())
    validate_sequence(rows+manifest['endpoint_proofs'],profile,manifest['step_minutes'],len(rows))
    if video:validate_video(output/manifest['video_filename'],output,rows,manifest['seconds_per_plate'])
    report(f'Verified {len(rows)} hourly plates, source and export hashes, fixed framing, and complete video timing')
    return manifest


def main(argv=None):
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--profile',type=Path,default=ROOT/'assets.static/orbital-technosphere/20261109/orbital-technosphere-profile.json')
    parser.add_argument('--renderer',type=Path,default=ROOT/'src.generate/generate-orbiting')
    parser.add_argument('--reference',type=Path,default=ROOT/'output/starlink-star-light-world-20261110/maps/world/svg/slsl2-orbital-technosphere-observer.svg',
                        help='accepted World observer SVG used for frame-zero comparison')
    parser.add_argument('--output',type=Path,default=ROOT/'output/starlink-star-light-v4-observer-hourly')
    parser.add_argument('--start')
    parser.add_argument('--hours',type=int,default=24)
    parser.add_argument('--step-minutes',type=int,default=60)
    parser.add_argument('--include-endpoint',action='store_true')
    parser.add_argument('--seconds-per-plate',type=float,default=2)
    parser.add_argument('--video-width',type=int,default=1920)
    parser.add_argument('--video-height',type=int,default=1080)
    parser.add_argument('--preview-width',type=int,default=2560)
    parser.add_argument('--jobs',type=int,choices=range(1,5),default=2)
    parser.add_argument('--proofs-only',action='store_true')
    parser.add_argument('--check',action='store_true')
    args=parser.parse_args(argv)
    try:
        output=args.output.resolve()
        if args.check:
            verify(output);return 0
        require((args.video_width,args.video_height)==(1920,1080),'The reviewed video layout is 1920 × 1080')
        require(args.hours==24 and args.step_minutes==60,'This reviewed edition requires 24 hourly states; an endpoint may be included separately')
        require(args.seconds_per_plate>0 and args.seconds_per_plate*30==int(args.seconds_per_plate*30),'Plate duration must be a positive whole number of video frames')
        output.mkdir(parents=True,exist_ok=True)
        # A failed rebuild must not leave a stale completed-delivery claim.
        if (output/'manifest.json').is_file():
            previous=json.loads((output/'manifest.json').read_text())
            previous['status']='rebuilding'
            atomic_json(output/'manifest.json',previous)
        profile_path,provenance=snapshot_inputs(args.profile.resolve(),args.renderer.resolve(),output,args.reference.resolve())
        profile=json.loads(profile_path.read_text());start=instant(args.start or profile['timestamp'])
        require(profile['propagation']['maximum_element_age_days']==7 and profile['propagation']['maximum_future_epoch_hours']==6,
                'The accepted epoch eligibility limits must be preserved')
        require(profile['visibility']['minimum_elevation_deg']==0,'The accepted horizon threshold must be preserved')
        count=args.hours+int(args.include_endpoint)
        values=schedule(start,max(count,args.hours+1),args.step_minutes)
        tools={'ffmpeg':run(['ffmpeg','-version']).splitlines()[0],
               'inkscape':run(['inkscape','--version']).strip(), 'python':sys.version.split()[0]}
        common={**provenance,'step_minutes':args.step_minutes,'export_tools':tools,'main_sequence_count':count}
        register_fonts();env=font_environment();env['CARTOFREAKO_LABEL_FONT']='atkinson_hyperlegible'
        indices=sorted({0,args.hours//2,args.hours}) if args.proofs_only else list(range(len(values)))
        report(f'Building {len(indices)} independent calculations from the frozen November 9 catalog')
        with ThreadPoolExecutor(max_workers=args.jobs) as pool:
            futures=[pool.submit(build_frame,i,values[i],profile,profile_path,output,common,env,args.preview_width,count) for i in indices]
            rows=[f.result() for f in futures]
        if args.proofs_only:
            atomic_json(output/'validation/proofs.json',{'status':'passed','frames':rows,'provenance':provenance})
            report('Hours 0, 12 and 24 exported for visual proof inspection');return 0
        validation=validate_sequence(rows,profile,args.step_minutes,count)
        atomic_json(output/'validation/proofs.json',
                    {'status':'passed','kind':'completed-sequence-canaries',
                     'frames':[r for r in rows if r['index'] in (0,12,24)],'provenance':provenance})
        main_rows=rows[:count]
        manifest={'schema':SCHEMA,'status':'assembling','profile_filename':profile_path.name,
                  'start':timestamp(start),'observer':profile['reference_point'],'propagation':profile['propagation'],
                  'orientation':profile['orientation'],'provenance':provenance,'export_tools':tools,'step_minutes':args.step_minutes,
                  'seconds_per_plate':args.seconds_per_plate,'frames':main_rows,'endpoint_proofs':rows[count:],
                  'sequence_validation':validation,'video_filename':f'observer-hourly-{count}-plates-{count*args.seconds_per_plate:g}s.mkv'}
        atomic_json(output/'sequence.json',manifest)
        report('Ordered sequence passed scientific and fixed-framing checks; assembling viewer and video')
        write_viewer(output,main_rows,manifest)
        contact_sheet(output,main_rows)
        manifest['video_filename']=encode_video(output,main_rows,args.seconds_per_plate)
        manifest['video_validation']=validate_video(output/manifest['video_filename'],output,main_rows,args.seconds_per_plate)
        for name,expected in provenance['implementation_files'].items():
            require(digest(ROOT/name)==expected,'Implementation changed during the build: '+name)
            require(digest(output/'sources/implementation'/name)==expected,'Archived implementation changed: '+name)
        for name,expected in provenance['catalog_files'].items():
            require(digest(output/'sources/orbital'/name)==expected,'Pinned catalog changed during the build: '+name)
        require(digest(output/'sources/renderer/generate-orbiting')==provenance['renderer_sha256'],'Pinned renderer changed')
        require(files_match([r for row in rows for r in row['files']],output),'A frame export changed during assembly')
        manifest['status']='complete'
        manifest['files']=[file_record(p,output) for p in sorted(output.rglob('*')) if p.is_file()
                           and p.name not in ('manifest.json',) and p.suffix not in ('.log',) and '.tmp' not in p.name]
        atomic_json(output/'manifest.json',manifest)
        report(f'Complete: {count} hourly plates; {count*args.seconds_per_plate:g}-second MKV; '+str(output/'index.html'))
        return 0
    except Exception as error:
        report('Observer hourly build failed: '+str(error))
        return 1
