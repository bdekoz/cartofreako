"""Keep composition intermediates separate from the public two-sheet delivery."""
import json
import os
from pathlib import Path
import uuid

from legend_informatics import SUFFIX, digest

COMPOSITION = Path('sources/composition')
STANDARD_FILES = Path('sources/standard-plate-files.json')


def migrate_composition(delivery):
    """Preserve the previous combined exports before publishing standard filenames."""
    delivery = Path(delivery)
    internal = delivery / COMPOSITION
    internal.mkdir(parents=True, exist_ok=True)
    if not (delivery / STANDARD_FILES).exists():
        for name in ('plates', 'previews'):
            source, target = delivery / name, internal / name
            if source.exists() and not target.exists():
                source.rename(target)
    for name in ('exports', 'export-manifest.json', 'export-manifest-selected.json',
                 'validation.json', 'validation-map-only.json'):
        source, target = delivery / 'sources' / name, internal / name
        if source.exists() and not target.exists():
            source.rename(target)

    def relocate(value):
        if isinstance(value, list):
            return [relocate(v) for v in value]
        if isinstance(value, dict):
            return {k: (str(COMPOSITION / v) if k == 'path' and isinstance(v, str)
                        and v.startswith(('plates/', 'previews/')) else relocate(v))
                    for k, v in value.items()}
        return value

    receipts = list((internal / 'exports').glob('*.json'))
    receipts += list(internal.glob('export-manifest*.json'))
    for path in receipts:
        previous = json.loads(path.read_text())
        revised = relocate(previous)
        if revised != previous:
            path.write_text(json.dumps(revised, indent=2) + '\n')
    manifest = delivery / 'sources/separate-sheets.json'
    if manifest.exists():
        data = json.loads(manifest.read_text())
        changed = False
        for record in data['records']:
            if record['source'].startswith('plates/'):
                record['source'] = str(COMPOSITION / record['source'])
                changed = True
        if changed:
            manifest.write_text(json.dumps(data, indent=2) + '\n')
    (internal / 'README.md').write_text(
        '# Composition intermediates\n\n'
        'These combined map/legend files are retained only as build inputs and '
        'historical evidence. Final cartography/data and legend/bibliography '
        'sheets are separate. Use the delivery index or the standard files under '
        '`../../plates/` and `../../previews/`.\n')


def expected_files(delivery):
    manifest = json.loads((delivery / 'sources/sheet-export-manifest.json').read_text())
    records = manifest['records']
    keys = {(r['scope'], r['stem'], r['kind']) for r in records}
    if len(records) != 152 or len(keys) != 152:
        raise ValueError('Expected 76 maps and 76 separate legend/bibliography sheets')
    subjects = {r['stem'] for r in records}
    if len(subjects) != 38 or keys != {
            (scope, stem, kind) for scope in ('world', 'japan')
            for stem in subjects for kind in ('map', 'legend')}:
        raise ValueError('Incomplete world/Japan map and legend pairs')
    result = []
    for record in records:
        scope, stem, kind = record['scope'], record['stem'], record['kind']
        name = stem + SUFFIX + ('-japan' if scope == 'japan' else '')
        if kind == 'legend':
            name += '-legend'
        files = {}
        for format in ('svg', 'pdf', 'png', 'preview'):
            if format == 'svg':
                target, checksum = record['svg'], record['fingerprint']['svg_sha256']
            else:
                target = record['outputs'][format]['path']
                checksum = record['outputs'][format]['sha256']
            path = (Path('previews') / scope / (name + '.png') if format == 'preview'
                    else Path('plates') / scope / format / (name + '.' + format))
            files[format] = {'path': str(path), 'target': target, 'sha256': checksum}
        result.append({'scope': scope, 'stem': stem, 'kind': kind, 'files': files})
    return result


def standard_files(delivery, *, check=False):
    """Publish or audit the familiar filenames against the verified separate sheets."""
    delivery = Path(delivery)
    if not check:
        migrate_composition(delivery)
    records = expected_files(delivery)
    # Check every export before changing any public filename.
    for record in records:
        for file in record['files'].values():
            target = delivery / file['target']
            if not target.is_file() or digest(target) != file['sha256']:
                raise ValueError('Separate-sheet export changed: ' + str(target))
            path = delivery / file['path']
            if path.exists() and not path.is_symlink():
                raise ValueError('Unexpected regular file at public plate path: ' + str(path))
    for record in records:
        for file in record['files'].values():
            path, target = delivery / file['path'], delivery / file['target']
            if check:
                if not path.is_symlink() or path.resolve() != target.resolve():
                    raise ValueError('Public filename does not resolve to its separate sheet: ' + str(path))
            elif not path.is_symlink() or path.resolve() != target.resolve():
                path.parent.mkdir(parents=True, exist_ok=True)
                temporary = path.with_name('.' + path.name + '.' + uuid.uuid4().hex)
                temporary.symlink_to(os.path.relpath(target, path.parent))
                temporary.replace(path)
    receipt = {'schema': 'setouchi-standard-plate-files-v1', 'status': 'passed',
               'maps': 76, 'legend_source_sheets': 76, 'files': 608,
               'records': records}
    manifest = delivery / STANDARD_FILES
    if check:
        if json.loads(manifest.read_text()) != receipt:
            raise ValueError('Public filename manifest is out of date')
    else:
        manifest.write_text(json.dumps(receipt, indent=2) + '\n')
    return receipt
