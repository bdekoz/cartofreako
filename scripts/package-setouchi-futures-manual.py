#!/usr/bin/env python3
"""Package the selected Setouchi gallery for a manual WordPress web UI update."""
import argparse
import csv
from datetime import date
from html import escape
import json
from pathlib import Path
import re
import shutil
from urllib.parse import unquote, urlsplit
import zipfile

from bs4 import BeautifulSoup
from PIL import Image

from setouchi_futures import ROOT, PREVIEW_CSS, digest, gallery_blocks, gallery_hamonshu, load_config, write_json
from setouchi_futures_publish import load_prepared, used_keys

TEMPLATE = ROOT / 'scripts/templates/setouchi-futures-manual.html'
SCHEMA = 'cartofreako-setouchi-manual-web-ui-v1'
SOURCES = {
    'media': 'https://wordpress.org/documentation/article/media-library-screen/',
    'image': 'https://wordpress.org/documentation/article/image-block/',
    'columns': 'https://wordpress.org/documentation/article/columns-block/',
    'group': 'https://wordpress.org/documentation/article/group-block/',
    'list_view': 'https://wordpress.org/documentation/article/list-view/',
    'editor': 'https://wordpress.org/documentation/article/wordpress-block-editor/',
    'large_images': 'https://developer.wordpress.org/reference/hooks/big_image_size_threshold/',
    'original_image_control': 'https://developer.wordpress.org/reference/functions/wp_print_media_templates/',
}


def copy_field(label, value, ident):
    return (f'<label for="{ident}">{escape(label)}</label>'
            f'<textarea id="{ident}" readonly rows="3">{escape(value)}</textarea>'
            f'<button type="button" data-copy="{ident}">Copy {escape(label.lower())}</button>')


def ordered_figures(prepared):
    config = prepared['config']
    figures = []
    for scope, title in [('world', 'World'), ('japan', 'Japan / Setouchi')]:
        for item in config['maps']:
            figures.append({'id': scope + '-' + item['stem'], 'section': title, 'title': item['title'],
                            'caption': item[scope + '_caption'], 'alt': item[scope + '_alt'],
                            'background': item.get('background', config['background']),
                            'kind': 'map', 'roles': ['card', 'detail', 'legend']})
    for item in gallery_hamonshu(config):
        figures.append({'id': item['id'], 'section': 'Hamonshū Revisited', 'title': item['title'],
                        'caption': item['caption'], 'alt': item['alt'], 'kind': 'hamonshu',
                        'background': '#f4efe4', 'roles': ['card', 'detail'],
                        'review_url': f'https://situationshipin.space/review/hamonshu-v2-book{item["book"]}/'})
    return figures


def write_guide(output, prepared, figures, uploads):
    config = prepared['config']
    cards, captions, outline = [], [], []
    for figure in figures:
        number, ident = figure['order'], figure['id']
        files = {role: next(a for a in uploads if a['figure'] == number and a['role'] == role)
                 for role in figure['roles']}
        card = files['card']
        ratio = '44/19.052559' if figure['kind'] == 'map' else '4/3'
        cards.append(f'<article class="asset-card" id="figure-{number:02d}"><h3>{number:02d} · {escape(figure["section"])} · {escape(figure["title"])}</h3>'
                     f'<a href="{files["detail"]["path"]}"><img loading="lazy" src="{card["path"]}" alt="{escape(figure["alt"], quote=True)}" '
                     f'style="aspect-ratio:{ratio};object-fit:contain;background:{figure["background"]}"></a><dl>')
        for role, file in files.items():
            label = {'card': 'Insert this image', 'detail': 'Link the image to this file', 'legend': 'Link “Legend & sources” to this PDF'}[role]
            cards.append(f'<dt>{escape(label)}</dt><dd><a href="{file["path"]}">{escape(Path(file["path"]).name)}</a></dd>')
        cards.append('</dl>')
        caption = figure['title'] + '\n' + figure['caption']
        cards.append(copy_field('Caption', caption, f'caption-{number}'))
        cards.append(copy_field('Alt text', figure['alt'], f'alt-{number}'))
        if figure.get('review_url'):
            cards.append(copy_field('Book review URL', figure['review_url'], f'review-{number}'))
        cards.append('<p class="done"><label><input type="checkbox"> Image, caption, alt text, and links added</label></p></article>')
        captions.extend([f'{number:02d} | {figure["section"]} | {figure["title"]}',
                         'CAPTION:', caption, 'ALT TEXT:', figure['alt']])
        for role, file in files.items():
            captions.append(role.upper() + ' FILE: ' + Path(file['path']).name)
        if figure.get('review_url'):
            captions.append('BOOK REVIEW URL: ' + figure['review_url'])
        captions.append('')
        outline.append(f'<a href="#figure-{number:02d}">{number:02d} · {escape(figure["title"])}</a>')
    guide = TEMPLATE.read_text()
    has_hamonshu = bool(gallery_hamonshu(config))
    for name, include in [('HAMONSHU', has_hamonshu), ('NO_HAMONSHU', not has_hamonshu)]:
        guide = re.sub(r'<!-- IF_' + name + r' -->(.*?)<!-- END_IF_' + name + r' -->',
                       lambda match: match[1] if include else '', guide, flags=re.S)
    replacements = {
        'PAGE_URL': escape(config['page_url'], quote=True),
        'EDIT_URL': escape(config['site_url'] + f'/wp-admin/post.php?post={config["page_id"]}&action=edit', quote=True),
        'UPLOAD_COUNT': str(len(uploads)), 'UPLOAD_MB': f'{sum(a["bytes"] for a in uploads) / 1e6:.1f}',
        'FIGURE_COUNT': str(len(figures)), 'SECTION_COUNT': str(2 + has_hamonshu),
        'LEGEND_COUNT': str(sum(a['role'] == 'legend' for a in uploads)),
        'CARDS': '\n'.join(cards), 'FIGURE_LINKS': '\n'.join(outline),
        'EDITION': config['edition'], 'ANCHOR': escape(config['anchor']),
    }
    for key, value in replacements.items():
        guide = guide.replace('@@' + key + '@@', value)
    if re.search(r'@@[A-Z_]+@@', guide):
        raise ValueError('Unfilled guide field')
    guide = re.sub(r'(?m)^[ \t]+$', '', guide)
    (output / 'START-HERE.html').write_text(guide)
    (output / 'CAPTIONS-AND-ALT-TEXT.txt').write_text('\n'.join(captions))

    fragment = gallery_blocks(prepared)
    for asset in uploads:
        fragment = fragment.replace('{{asset:' + asset['source_key'] + '}}', asset['path'])
    if '{{asset:' in fragment:
        raise ValueError('Missing media in the offline preview')
    (output / 'preview.html').write_text(
        '<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">'
        '<title>Setouchi H3r5 · manual update preview</title><style>' + PREVIEW_CSS + '</style><main>'
        '<h1>Cartofreako × Setouchi</h1><p class="preview-note">Gallery placement reference. '
        'Insert after the three proposal/atlas links and before “Two atlases, one shared table.” '
        'Live typography comes from your WordPress theme. <a href="START-HERE.html">Return to instructions</a>.</p>'
        + fragment + '<hr><h2>Two atlases, one shared table</h2>'
        '<p>The existing page continues here.</p></main></html>')


def validate_package(output, prepared, figures, uploads, files):
    map_count = len(prepared['config']['maps']) * 2
    figure_count = map_count + len(gallery_hamonshu(prepared['config']))
    if len(figures) != figure_count or len(uploads) != figure_count * 2 + map_count:
        raise ValueError('Figure or upload count differs from the selected gallery configuration')
    if {a['source_key'] for a in uploads} != used_keys(prepared):
        raise ValueError('Manual package does not match the gallery media')
    for asset in uploads:
        if digest(output / asset['path']) != asset['sha256']:
            raise ValueError('Copied media differs from the validated source')
        if asset['role'] != 'legend':
            with Image.open(output / asset['path']) as image:
                image.verify()
    for name in ['START-HERE.html', 'preview.html']:
        soup = BeautifulSoup((output / name).read_text(), 'html.parser')
        if len(soup.select('img')) != figure_count or any(not node.get('alt') for node in soup.select('img')):
            raise ValueError('Missing image or alternative text in ' + name)
        ids = [node['id'] for node in soup.select('[id]')]
        if len(ids) != len(set(ids)):
            raise ValueError('Duplicate document IDs in ' + name)
        for button in soup.select('[data-copy]'):
            field = soup.find('textarea', id=button['data-copy'])
            if field is None or not field.has_attr('readonly') or not field.get_text().strip():
                raise ValueError('Broken copy field in ' + name)
        for node in soup.select('[href], [src]'):
            target = node.get('href') or node.get('src')
            if urlsplit(target).scheme:
                continue
            path, _, anchor = unquote(target).partition('#')
            if path and path not in files:
                raise ValueError('Link leaves the package: ' + target)
            if not path and anchor and anchor not in ids:
                raise ValueError('Missing guide anchor: ' + anchor)
    return {'schema': 'cartofreako-setouchi-manual-validation-v1', 'figures': figure_count, 'upload_files': len(uploads),
            'image_files': figure_count * 2, 'legend_pdfs': map_count, 'source_checksums_match': True,
            'local_links_valid': True, 'images_decode': True, 'all_images_have_alt': True,
            'unresolved_asset_tokens': False, 'private_or_print_master_files_included': False}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--bundle', type=Path, default=ROOT / load_config()['output'])
    parser.add_argument('--output', type=Path, default=ROOT / 'output/setouchi-futures-h3r5-manual-20261106')
    args = parser.parse_args()
    bundle, output = args.bundle.resolve(), args.output.resolve()
    prepared = load_prepared(bundle)
    config = prepared['config']
    if config.get('analysis_h3_resolution') != 5:
        raise ValueError('This package requires the selected H3r5 edition')
    validated = json.loads((bundle / 'validation.json').read_text())
    if validated['prepared_sha256'] != digest(bundle / 'prepared.json'):
        raise ValueError('Validate the selected edition before packaging')
    previous_uploads = []
    if output.exists() and any(output.iterdir()):
        existing = output / 'manifest.json'
        if not existing.exists() or json.loads(existing.read_text()).get('schema') != SCHEMA:
            raise ValueError('Output directory is not a previous manual package')
        previous_uploads = json.loads(existing.read_text()).get('uploads', [])
    output.mkdir(parents=True, exist_ok=True)
    (output / 'uploads').mkdir(exist_ok=True)
    assets = {a['key']: a for a in prepared['assets']}
    figures, uploads = ordered_figures(prepared), []
    for number, figure in enumerate(figures, 1):
        figure['order'] = number
        for role in figure['roles']:
            key = figure['id'] + '-' + ('1280' if role == 'card' else role)
            asset = assets[key]
            source = bundle / asset['path']
            path = output / 'uploads' / f'{number:02d}-{figure["id"]}-{role}{source.suffix}'
            shutil.copyfile(source, path)
            uploads.append({'figure': number, 'section': figure['section'], 'role': role,
                            'source_key': key, 'source_path': asset['path'],
                            'path': path.relative_to(output).as_posix(), 'sha256': asset['sha256'],
                            'bytes': asset['bytes'], 'title': asset['title'],
                            'alt': figure['alt'] if role != 'legend' else '',
                            'caption': figure['caption'] if role != 'legend' else ''})
    current_paths = {a['path'] for a in uploads}
    for old in previous_uploads:
        if old['path'] not in current_paths:
            stale = (output / old['path']).resolve()
            if not stale.is_relative_to((output / 'uploads').resolve()):
                raise ValueError('Previous upload path leaves the package')
            if stale.exists():
                if digest(stale) != old['sha256']:
                    raise ValueError('Obsolete packaged upload was modified; preserve it before rebuilding')
                stale.unlink()
    with (output / 'UPLOAD-CHECKLIST.csv').open('w', newline='') as stream:
        writer = csv.writer(stream, lineterminator='\n')
        writer.writerow(['figure', 'section', 'role', 'filename', 'title', 'alt_text', 'caption', 'uploaded_file_url'])
        for asset in uploads:
            writer.writerow([asset['figure'], asset['section'], asset['role'], Path(asset['path']).name,
                             asset['title'], asset['alt'], asset['caption'], ''])
    write_guide(output, prepared, figures, uploads)
    manifest = {'schema': SCHEMA, 'edition': config['edition'], 'h3_resolution': 5,
                'destination': config['page_url'], 'page_id': config['page_id'],
                'source_bundle': bundle.relative_to(ROOT).as_posix(),
                'prepared_sha256': digest(bundle / 'prepared.json'),
                'source_validation_sha256': digest(bundle / 'validation.json'),
                'builder_sha256': digest(Path(__file__)), 'guide_template_sha256': digest(TEMPLATE),
                'documentation_sources': SOURCES, 'figures': figures, 'uploads': uploads,
                'publication_status': 'not-published'}
    write_json(output / 'manifest.json', manifest)
    (output / 'README.md').write_text(
        '# Setouchi H3r5 — manual WordPress update\n\n'
        'Unzip this folder, then open [START-HERE.html](START-HERE.html) in your browser. '
        'Keep it open beside the WordPress page editor. Use your normal WordPress login; '
        'no application password, command line, or plugin installation is required for these steps.\n\n'
        'The guide covers uploading the files, placing the World and Japan grids after the three '
        'proposal/atlas links, and linking larger images and source legends. '
        f'It includes copy-ready captions and alternative text for all {len(figures)} figures.\n\n'
        f'- `uploads/`: the {len(uploads)} web files, numbered in placement order.\n'
        '- [preview.html](preview.html): an offline layout and image reference.\n'
        '- [CAPTIONS-AND-ALT-TEXT.txt](CAPTIONS-AND-ALT-TEXT.txt): plain-text copy sheet.\n'
        '- [UPLOAD-CHECKLIST.csv](UPLOAD-CHECKLIST.csv): filename/role mapping and an optional URL worksheet.\n'
        '- [manifest.json](manifest.json): H3r5 selection, source hashes, and media inventory.\n'
        '- [validation.json](validation.json) and [SHA256SUMS](SHA256SUMS): package checks.\n\n'
        'Only the files in `uploads/` go into the WordPress Media Library. The guide, preview, '
        f'and worksheets are local references. The package contains {len(figures)} gallery cards, {len(figures)} larger '
        'images, and 10 source-legend PDFs. All media bytes match the validated selected edition.\n\n'
        'The much larger 300 dpi print masters remain in the repository’s selected H3r5 print '
        'edition; they are not needed for this website update. The website and its media library '
        'have not been changed by creating this package.\n')
    files = {a['path'] for a in uploads} | {'README.md', 'START-HERE.html', 'preview.html',
              'CAPTIONS-AND-ALT-TEXT.txt', 'UPLOAD-CHECKLIST.csv', 'manifest.json', 'validation.json', 'SHA256SUMS'}
    result = validate_package(output, prepared, figures, uploads, files)
    write_json(output / 'validation.json', result)
    (output / 'SHA256SUMS').write_text(''.join(
        digest(output / name) + '  ' + name + '\n' for name in sorted(files - {'SHA256SUMS'})))
    archive = output.with_suffix('.zip')
    temporary = archive.with_suffix('.zip.tmp')
    day = date.fromisoformat(config['edition'])
    with zipfile.ZipFile(temporary, 'w', compression=zipfile.ZIP_DEFLATED, compresslevel=9) as zip_file:
        for name in sorted(files):
            entry = zipfile.ZipInfo(output.name + '/' + name, (day.year, day.month, day.day, 0, 0, 0))
            entry.create_system = 3
            entry.external_attr = 0o100644 << 16
            entry.compress_type = zipfile.ZIP_DEFLATED
            zip_file.writestr(entry, (output / name).read_bytes(), compresslevel=9)
    with zipfile.ZipFile(temporary) as zip_file:
        if zip_file.testzip() is not None or len(zip_file.namelist()) != len(files):
            raise ValueError('ZIP integrity check failed')
    temporary.replace(archive)
    print(json.dumps({'archive': str(archive), 'bytes': archive.stat().st_size,
                      'files': len(files), 'upload_files': len(uploads), 'figures': len(figures),
                      'sha256': digest(archive), 'status': 'local-only'}))


if __name__ == '__main__':
    main()
