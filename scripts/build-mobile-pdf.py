#!/usr/bin/env python3
"""Flatten a finished atlas into a bounded-resolution, linearized mobile PDF."""

import argparse
from collections import Counter
from datetime import datetime, timezone
from hashlib import sha256
import io
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import zlib

from PIL import Image, __version__ as pillow_version
from reportlab import Version as reportlab_version, rl_config
from reportlab.lib.utils import ImageReader
from reportlab.pdfgen.canvas import Canvas

ROOT = Path(__file__).resolve().parents[1]
try:
    import pikepdf
except ModuleNotFoundError:
    # Reuse the optional PDF dependency from the earlier H3 packaging work.
    sys.path.append(str(ROOT / 'build/setouchi-h3-python'))
    import pikepdf


def digest(path):
    result = sha256()
    with path.open('rb') as source:
        for block in iter(lambda: source.read(1024 * 1024), b''):
            result.update(block)
    return result.hexdigest()


def visible_size(page):
    media = [float(value) for value in page.mediabox]
    crop = [float(value) for value in page.cropbox]
    unit = float(page.get('/UserUnit', 1))
    width = (min(media[2], crop[2]) - max(media[0], crop[0])) * unit
    height = (min(media[3], crop[3]) - max(media[1], crop[1])) * unit
    rotation = int(page.get('/Rotate', 0)) % 360
    if rotation not in (0, 90, 180, 270) or min(width, height) <= 0:
        raise ValueError('Unsupported page rotation or empty visible page box')
    return (height, width) if rotation in (90, 270) else (width, height)


def check_output(path, sizes, records, max_edge):
    with pikepdf.open(path) as pdf:
        problems = pdf.check_pdf_syntax()
        if problems:
            raise ValueError('\n'.join(problems))
        if not pdf.is_linearized or not pdf.check_linearization():
            raise ValueError('Mobile PDF must pass the linearization check')
        if len(pdf.pages) != len(sizes):
            raise ValueError('Page count changed')
        for page, size, record in zip(pdf.pages, sizes, records, strict=True):
            if any(abs(a - b) > 0.001 for a, b in zip(visible_size(page), size)):
                raise ValueError('Visible page dimensions changed')
            resources = page.Resources
            images = list(resources.XObject.values())
            if len(images) != 1 or images[0].Subtype != pikepdf.Name.Image:
                raise ValueError('Each page must contain exactly one image')
            image = images[0]
            dimensions = [int(image.Width), int(image.Height)]
            if dimensions != record['pixels'] or max(dimensions) > max_edge:
                raise ValueError('Page image dimensions differ from the render')
            if image.ColorSpace != pikepdf.Name.DeviceRGB or int(image.BitsPerComponent) != 8:
                raise ValueError('Page image must be opaque RGB8')
            if '/SMask' in image or '/Mask' in image or '/Annots' in page:
                raise ValueError('Mobile pages must be fully flattened')
            if '/Font' in resources:
                raise ValueError('Unexpected font resource')
            operators = [str(item.operator) for item in pikepdf.parse_content_stream(page)]
            if operators.count('Do') != 1 or set(operators) - {'q', 'Q', 'cm', 'Do'}:
                raise ValueError('Unexpected vector or text content')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('source', type=Path)
    parser.add_argument('destination', type=Path)
    parser.add_argument('--max-edge', type=int, default=2400,
                        help='Maximum pixels on either page edge (default: 2400)')
    parser.add_argument('--jpeg-quality', type=int, default=85,
                        help='JPEG quality, used only when smaller than lossless (default: 85)')
    parser.add_argument('--receipt', type=Path,
                        help='JSON receipt path (default: destination with .json suffix)')
    args = parser.parse_args()
    source, destination = args.source.resolve(), args.destination.resolve()
    receipt = (args.receipt or destination.with_suffix('.json')).resolve()
    if not source.is_file():
        parser.error(f'Source does not exist: {source}')
    if len({source, destination, receipt}) != 3:
        parser.error('Source, destination and receipt must have different paths')
    if destination.exists() or receipt.exists():
        parser.error('Destination or receipt already exists; choose a new output name')
    if not 256 <= args.max_edge <= 8192 or not 1 <= args.jpeg_quality <= 95:
        parser.error('Use --max-edge 256..8192 and --jpeg-quality 1..95')

    source_hash = digest(source)
    with pikepdf.open(source) as original:
        sizes = [visible_size(page) for page in original.pages]
    if not sizes:
        parser.error('Source PDF has no pages')
    version = subprocess.run(['pdftoppm', '-v'], capture_output=True, text=True, check=True)
    renderer = (version.stdout + version.stderr).splitlines()[0]
    work_root = ROOT / 'tmp/pdfs'
    work_root.mkdir(parents=True, exist_ok=True)
    records = []
    with tempfile.TemporaryDirectory(prefix='mobile-', dir=work_root) as directory:
        work = Path(directory)
        print(f'Rendering {len(sizes)} pages at at most {args.max_edge} pixels per edge', flush=True)
        subprocess.run(['pdftoppm', '-cropbox', '-scale-to', str(args.max_edge),
                        '-aa', 'yes', '-aaVector', 'yes', '-png', '-progress',
                        str(source), str(work / 'page')], check=True)
        renders = sorted(work.glob('page-*.png'), key=lambda p: int(p.stem.split('-')[-1]))
        if len(renders) != len(sizes):
            raise ValueError('Rendered page count differs from the source PDF')

        rl_config.useA85 = False  # Store binary streams without ASCII85 expansion.
        assembled = work / 'assembled.pdf'
        canvas = Canvas(str(assembled), pagesize=sizes[0], pageCompression=1,
                        invariant=1, pdfVersion=(1, 4))
        canvas.setTitle(destination.stem)
        canvas.setCreator('Cartofreako / scripts/build-mobile-pdf.py')
        canvas.setSubject(f'Mobile raster edition; {args.max_edge}px maximum edge; source SHA-256 {source_hash}')
        for number, (render, size) in enumerate(zip(renders, sizes, strict=True), 1):
            with Image.open(render) as png:
                rgb = png.convert('RGB')
            pixels = list(rgb.size)
            if max(pixels) > args.max_edge:
                raise ValueError('Renderer exceeded the pixel limit')
            # ReportLab encodes RGB ImageReader data with zlib's default level.
            lossless_bytes = len(zlib.compress(rgb.tobytes()))
            jpeg = io.BytesIO()
            rgb.save(jpeg, format='JPEG', quality=args.jpeg_quality,
                     subsampling=0, optimize=True, progressive=False)
            jpeg_bytes = jpeg.getbuffer().nbytes
            use_jpeg = jpeg_bytes < lossless_bytes
            jpeg.seek(0)
            image = ImageReader(jpeg if use_jpeg else rgb)
            canvas.setPageSize(size)
            canvas.drawImage(image, 0, 0, width=size[0], height=size[1], mask=None)
            canvas.showPage()
            records.append({'page': number, 'size_points': list(size), 'pixels': pixels,
                            'encoding': 'JPEG' if use_jpeg else 'Flate',
                            'jpeg_candidate_bytes': jpeg_bytes,
                            'lossless_candidate_bytes': lossless_bytes})
            print(f'Packed page {number}/{len(sizes)}: {pixels[0]}x{pixels[1]} '
                  f'{records[-1]["encoding"]}', flush=True)
        canvas.save()

        ready = work / 'linearized.pdf'
        with pikepdf.open(assembled) as pdf:
            for page in pdf.pages:
                # Strip ReportLab's unused initial font setup, keeping only image placement.
                instructions = []
                for item in pikepdf.parse_content_stream(page):
                    if str(item.operator) in {'BT', 'ET', 'Tf', 'TL'}:
                        continue
                    instructions.append(item)
                page.Contents = pdf.make_stream(pikepdf.unparse_content_stream(instructions))
                if '/Font' in page.Resources:
                    del page.Resources['/Font']
            pdf.save(ready, linearize=True, compress_streams=True,
                     object_stream_mode=pikepdf.ObjectStreamMode.disable,
                     force_version='1.4', deterministic_id=True)
        check_output(ready, sizes, records, args.max_edge)
        if digest(source) != source_hash:
            raise ValueError('Source PDF changed during conversion')
        source_bytes, output_bytes = source.stat().st_size, ready.stat().st_size
        result = {
            'schema': 'cartofreako-mobile-pdf-v1',
            'created_at': datetime.now(timezone.utc).isoformat(),
            'source': {'path': str(source), 'sha256': source_hash, 'bytes': source_bytes},
            'output': {'path': str(destination), 'sha256': digest(ready), 'bytes': output_bytes},
            'settings': {'max_edge_pixels': args.max_edge, 'jpeg_quality': args.jpeg_quality,
                         'jpeg_subsampling': '4:4:4', 'encoding': 'smaller of JPEG and lossless RGB Flate',
                         'pdf_version': '1.4', 'linearized': True},
            'tools': {'renderer': renderer, 'Pillow': pillow_version,
                      'ReportLab': reportlab_version, 'pikepdf': pikepdf.__version__},
            'builder_sha256': digest(Path(__file__)),
            'checks': {'source_unchanged': True, 'page_count_and_dimensions': True,
                       'one_opaque_rgb_image_per_page': True, 'no_text_or_vector_drawing': True,
                       'syntax': True, 'linearization': True},
            'encoding_counts': dict(Counter(record['encoding'] for record in records)),
            'pages': records,
        }
        destination.parent.mkdir(parents=True, exist_ok=True)
        receipt.parent.mkdir(parents=True, exist_ok=True)
        # Exclusive creation prevents accidental replacement of an existing edition.
        with destination.open('xb') as output, ready.open('rb') as data:
            for block in iter(lambda: data.read(1024 * 1024), b''):
                output.write(block)
        with receipt.open('x') as output:
            json.dump(result, output, indent=2)
            output.write('\n')
        print(f'{destination}: {output_bytes / 1024**2:.2f} MiB '
              f'({100 * (1 - output_bytes / source_bytes):.2f}% smaller)', flush=True)
        print(f'Receipt: {receipt}', flush=True)


if __name__ == '__main__':
    main()
