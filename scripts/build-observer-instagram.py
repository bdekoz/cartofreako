#!/usr/bin/env python3
"""Recompose the completed hourly observer study as a portrait Instagram MP4."""
import argparse
from concurrent.futures import ThreadPoolExecutor
from copy import deepcopy
from datetime import datetime
from functools import lru_cache
import hashlib
import json
from pathlib import Path
import re
import struct
import subprocess
from zoneinfo import ZoneInfo

from lxml import etree as E
import numpy as np
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_SOURCE = ROOT / 'output/starlink-star-light-v4-observer-hourly'
PACIFIC = ZoneInfo('America/Los_Angeles')
WIDTH, HEIGHT, FPS, HOLD = 1080, 1920, 30, 2
LEFT, RIGHT, PANEL_WIDTH = 72, 916, 844
BG, AMBER, PAPER, MUTED, EQUATOR = '#240413', '#fcc553', '#fff4df', '#c0a8b0', '#ac959e'
MARKER_SCALE = 2.0
NUMBER = r'[-+]?(?:\d*\.\d+|\d+\.?)(?:[eE][-+]?\d+)?'


def require(condition, message):
    if not condition:
        raise ValueError(message)


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write_json(path, value):
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + '\n')


def run(command):
    return subprocess.check_output([str(v) for v in command], stderr=subprocess.STDOUT)


def report(message):
    print(datetime.now(PACIFIC).strftime('%Y-%m-%d %H:%M:%S %Z') + ': ' + message, flush=True)


def parse(path):
    return E.parse(str(path)).getroot()


def curves(root):
    return [(n.get('id'), n.get('d')) for n in root.xpath(
        '//*[starts-with(@id,"observer-horizon") or starts-with(@id,"celestial-equator")]')]


def marker_center(node):
    """Keep the original location when enlarging only a symbol's silhouette."""
    if E.QName(node).localname == 'circle':
        return float(node.get('cx')), float(node.get('cy'))
    path = node.get('d', '')
    require(not re.sub(NUMBER + r'|[MLZ\s,]', '', path), 'Unsupported marker path')
    values = [float(v) for v in re.findall(NUMBER, path)]
    require(len(values) >= 4 and len(values) % 2 == 0, 'Malformed marker path')
    points = list(zip(values[::2], values[1::2]))
    if node.get('data-marker-shape') == 'triangle':
        require(len(points) == 3, 'Unexpected triangle silhouette')
        return tuple(sum(p[i] for p in points) / 3 for i in (0, 1))
    return tuple((min(p[i] for p in points) + max(p[i] for p in points)) / 2 for i in (0, 1))


def mobile_panel(source, target, expected_count):
    original = parse(source)
    root = deepcopy(original)
    marks = root.xpath('//*[@data-object-kind="locpoint"]')
    require(len(marks) == expected_count, 'Source panel membership differs from its manifest')
    for mark in marks:
        require(not mark.get('transform'), 'Unexpected pre-existing marker transform')
        x, y = marker_center(mark)
        mark.set('transform', f'translate({x:.12g} {y:.12g}) scale({MARKER_SCALE:g}) translate({-x:.12g} {-y:.12g})')
    for node in root.xpath('//*[starts-with(@id,"observer-horizon")]'):
        node.set('style', f'fill:none;stroke:{AMBER};stroke-width:0.12;stroke-opacity:1')
    for node in root.xpath('//*[starts-with(@id,"celestial-equator")]'):
        node.set('style', f'fill:none;stroke:{EQUATOR};stroke-width:0.085;stroke-opacity:0.9')
    require(curves(original) == curves(root), 'Mobile styling changed a reference curve')
    for before, after in zip(original.xpath('//*[@data-object-kind="locpoint"]'), marks):
        require(all(after.get(k) == v for k, v in before.attrib.items()), 'Mobile styling changed scientific or glyph data')
    target.write_bytes(E.tostring(root, xml_declaration=True, encoding='UTF-8'))
    png = target.with_suffix('.png')
    run(['inkscape', target, '--export-area-page', '--export-width=' + str(PANEL_WIDTH * 2), '--export-filename=' + str(png)])
    with Image.open(png) as im:
        expected_height = PANEL_WIDTH * float(root.get('viewBox').split()[3]) / float(root.get('viewBox').split()[2])
        require(abs(im.height / 2 - expected_height) <= 1, 'Panel aspect ratio changed')
        return im.convert('RGB').resize((PANEL_WIDTH, round(expected_height)), Image.Resampling.LANCZOS)


@lru_cache(maxsize=32)
def font(directory, size, bold=False):
    return ImageFont.truetype(str(directory / ('AtkinsonHyperlegible-Bold.ttf' if bold else 'AtkinsonHyperlegible-Regular.ttf')), size)


def compose(source, output, row):
    index = row['index']
    directory = output / 'panels' / f'{index:02d}'
    directory.mkdir(parents=True, exist_ok=True)
    sky = mobile_panel(source / 'frames' / f'{index:02d}' / 'overview.svg', directory / 'sky.svg', row['plotted'])
    orientation = mobile_panel(source / row['orientation'], directory / 'orientation.svg', 0)
    canvas = Image.new('RGB', (WIDTH, HEIGHT), BG)
    canvas.paste(sky, (LEFT, 599))
    canvas.paste(orientation, (LEFT, 1096))
    draw = ImageDraw.Draw(canvas)
    fonts = source / 'assets/fonts'
    boxes = []

    def text(x, y, value, size, color=PAPER, bold=False, anchor='lt'):
        face = font(fonts, size, bold)
        box = draw.textbbox((x, y), value, font=face, anchor=anchor)
        require(LEFT <= box[0] and box[2] <= RIGHT and 180 <= box[1] and box[3] <= 1590,
                'Label exceeds portrait content bounds: ' + value)
        require(all(box[2] <= b[0] or box[0] >= b[2] or box[3] <= b[1] or box[1] >= b[3] for b in boxes),
                'Portrait labels overlap: ' + value)
        boxes.append(box)
        draw.text((x, y), value, font=face, fill=color, anchor=anchor)

    utc = datetime.fromisoformat(row['timestamp'].replace('Z', '+00:00'))
    local = utc.astimezone(PACIFIC)
    require(local.isoformat() == row['pacific_timestamp'], 'Pacific timestamp disagrees with source')
    text(LEFT, 196, 'STARLINK STAR LIGHT', 28, AMBER, True)
    if index in (0, 23):
        text(RIGHT - 2, 198, 'START / REPLAY' if index == 0 else 'FINAL SNAPSHOT', 24, MUTED, anchor='rt')
    text(LEFT, 244, 'The sky, hour by hour', 67, PAPER, True)
    text(LEFT, 334, 'San Francisco · 24 hourly snapshots', 34, MUTED)
    draw.line((LEFT, 396, RIGHT, 396), fill='#613342', width=2)
    text(LEFT, 424, local.strftime('%a, %b %d, %Y').upper(), 30, MUTED)
    text(LEFT, 466, local.strftime('%I:%M %p %Z').lstrip('0'), 68, AMBER, True)
    text(RIGHT, 424, 'HOUR', 25, MUTED, anchor='rt')
    text(RIGHT, 480, f'{index:02d} / 23', 39, PAPER, True, 'rt')
    text(LEFT, 554, 'ORBITAL OBJECTS ABOVE THE HORIZON', 26, PAPER, True)
    text(RIGHT, 554, f'{row["plotted"]:,} objects', 28, AMBER, True, 'rt')
    text(LEFT, 1002, 'AS EARTH TURNS', 27, PAPER, True)
    draw.line((LEFT, 1056, LEFT + 45, 1056), fill=AMBER, width=4)
    text(LEFT + 58, 1043, 'Horizon moves', 28, AMBER)
    draw.line((435, 1056, 480, 1056), fill=EQUATOR, width=3)
    text(493, 1043, 'Celestial equator stays fixed', 28, MUTED)
    for i in range(24):
        x = LEFT + i * PANEL_WIDTH / 24
        draw.rectangle((round(x), 1502, round(x + PANEL_WIDTH / 24 - 7), 1508), fill=AMBER if i <= index else '#613342')
    text(LEFT, 1530, f'Nov 9 catalog · {row["epoch_exclusions"]} epoch exclusions', 26, MUTED)
    text(LEFT, 1560, 'Hourly samples · Symbols enlarged 2× for mobile', 24, MUTED)
    path = output / 'frames' / f'frame-{index:02d}.png'
    path.parent.mkdir(exist_ok=True)
    canvas.save(path)
    report(f'Portrait hour {index:02d}: {local.strftime("%b %d %I:%M %p %Z")}; {row["plotted"]:,} objects')
    return {'index': index, 'timestamp': row['timestamp'], 'pacific_timestamp': local.isoformat(),
            'timezone_label': local.tzname(), 'plotted': row['plotted'], 'epoch_exclusions': row['epoch_exclusions'],
            'source_geometry_preserved': True, 'path': str(path.relative_to(output)), 'sha256': sha(path)}


def encode(output):
    video = output / 'observer-hourly-instagram-1080x1920-48s.mp4'
    run(['ffmpeg', '-y', '-v', 'error', '-threads', '2', '-filter_threads', '2', '-framerate', '1/2',
         '-start_number', '0', '-i', output / 'frames/frame-%02d.png', '-an',
         '-vf', 'scale=out_color_matrix=bt709:out_range=tv,format=yuv420p,setsar=1',
         '-c:v', 'libx264', '-threads', '2', '-preset', 'medium', '-crf', '17', '-profile:v', 'high', '-level:v', '4.1',
         '-pix_fmt', 'yuv420p', '-r', '30', '-fps_mode', 'cfr', '-frames:v', '1440', '-g', '60',
         '-color_primaries', 'bt709', '-color_trc', 'bt709', '-colorspace', 'bt709', '-color_range', 'tv',
         '-movflags', '+faststart', '-metadata', 'title=Starlink Star Light / hourly observer / San Francisco',
         '-metadata', 'comment=24 discrete hourly states from the frozen November 9 catalog. Each state holds for 2 seconds.', video])
    return video


def validate(video, output):
    probe = json.loads(run(['ffprobe', '-v', 'error', '-count_frames', '-show_streams', '-show_format', '-of', 'json', video]))
    require(len(probe['streams']) == 1, 'Unexpected audio or extra video streams')
    s = probe['streams'][0]
    require((s['codec_name'], s['width'], s['height'], s['pix_fmt'], s['r_frame_rate'], s['sample_aspect_ratio']) ==
            ('h264', WIDTH, HEIGHT, 'yuv420p', '30/1', '1:1'), 'Incorrect video format')
    require(int(s['nb_read_frames']) == 1440 and abs(float(probe['format']['duration']) - 48) < .001, 'Incorrect duration')
    atoms = []
    with video.open('rb') as stream:
        while header := stream.read(8):
            size, kind = struct.unpack('>I4s', header)
            header_size = 8
            if size == 1:
                size = struct.unpack('>Q', stream.read(8))[0]
                header_size = 16
            atoms.append(kind.decode('ascii'))
            if size == 0:
                break
            require(size >= header_size, 'Invalid MP4 atom')
            stream.seek(size - header_size, 1)
    require(atoms.index('moov') < atoms.index('mdat'), 'MP4 is not optimized for streaming')
    # Match every decoded frame, including both sides of each hourly cut.
    filter_value = 'scale=144:256:flags=area,format=gray'
    reference = run(['ffmpeg', '-v', 'error', '-threads', '2', '-filter_threads', '2', '-framerate', '1', '-i',
                     output / 'frames/frame-%02d.png', '-frames:v', '24', '-vf', filter_value, '-threads', '2',
                     '-f', 'rawvideo', '-pix_fmt', 'gray', 'pipe:1'])
    reference = np.frombuffer(reference, dtype=np.uint8).reshape(24, 256, 144).astype(np.float32)
    decoded = run(['ffmpeg', '-v', 'error', '-threads', '2', '-filter_threads', '2', '-i', video, '-vf', filter_value,
                   '-threads', '2', '-f', 'rawvideo', '-pix_fmt', 'gray', 'pipe:1'])
    require(len(decoded) == 1440 * 256 * 144, 'Decoded video has missing frames')
    counts, maximum = [0] * 24, 0.0
    for i, frame in enumerate(np.frombuffer(decoded, dtype=np.uint8).reshape(1440, 256, 144)):
        errors = np.mean((reference - frame) ** 2, axis=(1, 2))
        selected = int(np.argmin(errors))
        require(selected == i // 60, f'Wrong hourly state at decoded video frame {i}')
        counts[selected] += 1
        maximum = max(maximum, float(errors[selected]))
    require(counts == [60] * 24, 'An hourly state has an incorrect hold')
    return {'status': 'passed', 'size': [WIDTH, HEIGHT], 'fps': FPS, 'codec': 'h264', 'pixel_format': 'yuv420p',
            'duration_seconds': 48, 'decoded_frames': 1440, 'hourly_frame_counts': counts, 'audio_streams': 0,
            'faststart': True, 'all_frames_match_scheduled_hour': True, 'maximum_reduced_frame_mse': maximum}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source', type=Path, default=DEFAULT_SOURCE)
    parser.add_argument('--output', type=Path)
    parser.add_argument('--proofs-only', action='store_true')
    args = parser.parse_args()
    source = args.source.resolve()
    output = args.output.resolve() if args.output else source / 'instagram'
    require(output != source, 'Portrait delivery must have its own output directory')
    manifest_path = source / 'manifest.json'
    manifest = json.loads(manifest_path.read_text())
    require(manifest['status'] == 'complete' and len(manifest['frames']) == 24, 'A completed 24-state study is required')
    require(manifest['step_minutes'] == 60, 'The source is not hourly')
    rows = manifest['frames']
    require([r['index'] for r in rows] == list(range(24)), 'Source hours are out of order')
    require(all(r['propagation_failures'] == 0 for r in rows), 'Source has propagation failures')
    # The original manifest pins every source panel, metadata file and font.
    for record in manifest['files']:
        path = source / record['path']
        require(path.is_file() and path.stat().st_size == record['bytes'] and sha(path) == record['sha256'],
                'Original delivery changed: ' + record['path'])
    source_sha = sha(manifest_path)
    output.mkdir(parents=True, exist_ok=True)
    write_json(output / 'manifest.json', {'status': 'building', 'source_manifest_sha256': source_sha})
    selected = [rows[i] for i in (0, 12, 23)] if args.proofs_only else rows
    with ThreadPoolExecutor(max_workers=2) as pool:
        frames = list(pool.map(lambda row: compose(source, output, row), selected))
    with Image.open(output / 'frames/frame-00.png') as im:
        im.save(output / 'observer-hourly-instagram-cover.jpg', quality=96, subsampling=0)
        im.resize((360, 640), Image.Resampling.LANCZOS).save(output / 'phone-preview.png')
    if args.proofs_only:
        report('Portrait proofs ready for hours 00, 12 and 23')
        return
    report('Encoding 48-second portrait MP4')
    video = encode(output)
    report('Checking format, all 1,440 decoded frames and every two-second hold')
    validation = validate(video, output)
    require(sha(manifest_path) == source_sha, 'Source manifest changed while exporting')
    times = [datetime.fromisoformat(r['timestamp'].replace('Z', '+00:00')).astimezone(PACIFIC) for r in (rows[0], rows[-1])]
    labels = [value.strftime('%B %d, %Y at %I:%M %p %Z') for value in times]
    (output / 'caption.txt').write_text(
        'The sky, hour by hour.\n\n24 calculated snapshots above San Francisco, using the frozen November 9, 2026 catalog. '
        'The gold curve marks the local horizon; the muted curve is the fixed celestial equator. '
        'Watch how the horizon shifts and the orbital population changes as Earth turns.\n\n'
        + labels[0] + ' through ' + labels[1] + '. One hourly state every two seconds; '
        '24 samples span 23 elapsed hours. Symbols are enlarged for mobile. '
        'These are calculated above-horizon positions, not a recording of naked-eye visibility or continuous flight paths.\n')
    (output / 'README.md').write_text(
        '# Hourly observer / Instagram edition\n\n'
        '[48-second portrait MP4](observer-hourly-instagram-1080x1920-48s.mp4) · '
        '[Cover](observer-hourly-instagram-cover.jpg) · [Caption](caption.txt)\n\n'
        '1080 × 1920, 9:16, H.264 High 4.1, 30 fps, yuv420p, BT.709, square pixels, '
        'fast-start MP4, no audio. The 24 calculated states each hold for 60 frames. '
        'The first frame says START / REPLAY and the last says FINAL SNAPSHOT to distinguish a replay from the next physical hour.\n\n'
        'Both panels preserve the complete source projection. The upper panel shows satellites and the lower panel '
        'isolates the same horizon and equator. Marker silhouettes are enlarged 2× about their original centers; '
        'curve strokes are strengthened for phone viewing. Scientific coordinates, populations, curve paths, '
        'categorical colors and illumination opacities are unchanged. Source names remain available in the original study.\n\n'
        'Pacific labels are converted with America/Los_Angeles, selecting PST or PDT for each calculation instant. '
        'This November 8–9 edition uses PST. Text and panel content sit inside x=72–916 and y=196–1590 '
        'to leave room for playback controls. This is a layout choice, not a guarantee for every app interface.\n\n'
        'Rebuild from the repository root: `python3 scripts/build-observer-instagram.py`. '
        'Use `--proofs-only` for hours 00, 12 and 23. The source study is read-only. '
        'The delivery manifest records its hash, this builder hash, output hashes and the decoded-frame checks.\n')
    files = [{'path': str(p.relative_to(output)), 'sha256': sha(p), 'bytes': p.stat().st_size}
             for p in sorted(output.rglob('*')) if p.is_file() and p.name != 'manifest.json']
    write_json(output / 'manifest.json', {'status': 'complete', 'schema': 'cartofreako-observer-instagram-v1',
               'source_manifest_sha256': source_sha, 'builder_sha256': sha(Path(__file__)),
               'marker_linear_scale': MARKER_SCALE, 'seconds_per_plate': HOLD, 'frames': frames,
               'video': video.name, 'video_validation': validation, 'files': files})
    report('Complete: ' + str(video))


if __name__ == '__main__':
    main()
