"""Refresh only companion legends of a verified, completed optional atlas."""
from copy import deepcopy
from concurrent.futures import ThreadPoolExecutor
import importlib
import json
import os
from pathlib import Path
import shutil

from lxml import etree as E

from dataset import DatasetError, ROOT, atomic_json, context, data_root, digest, output, utcnow
from atlas_bibliography import bibliography, write_bibliography
from atlas_legends import PAPER, update_a3_sources, validate_legend
from atlas_review_sheets import save
from legend_informatics import font_environment
from setouchi_h3_trials import render_svg


def refresh_atlas(base, *, source=None):
    """Regenerate atlas legends from retained key content and bound source profiles."""
    builder = importlib.import_module('build-current-atlas')
    _, manifest = context()
    source = source or base
    old = json.loads((source/'atlas/sources/current-atlas.json').read_text())
    plates = builder.resolve_catalog_sources([p for p in manifest['products']['plates'] if p['default']])
    by_id = {p['id']:p for p in plates}
    citations = {p['id']:bibliography(p) for p in plates}
    records = deepcopy(old['records'])
    for row in records:
        if row['kind'] != 'legend':
            continue
        plate, scope = by_id[row['stem']], row['scope']
        existing = E.parse(str(source/'atlas'/row['svg'])).getroot()
        destination = base/'atlas'/row['svg']
        if existing.get('data-palette-reversed') == 'true':
            if existing.xpath('//*[@id="atlas-legend-model"]'):
                model = json.loads(existing.xpath('//*[@id="atlas-legend-model"]')[0].text)
                model['sources'] = citations[plate['id']]['references']
                tree = builder.legend(**model)
            else:
                tree = update_a3_sources(existing, citations[plate['id']]['references'])
            save(tree, destination)
        elif plate['id'] == 'network-groundstations':
            evidence = json.loads((source/'atlas/sources/current-build/groundstation-capability-evidence.json').read_text())
            _, recipe = builder.settings(builder.STYLE)
            tree = builder.GROUNDSTATIONS.legend(scope, evidence, recipe)
            update_a3_sources(tree, citations[plate['id']]['references'])
            save(tree, destination)
        else:
            builder.standalone_legend(plate, Path(row['source']), destination, manifest, scope,
                                      manifest['sources'], existing=existing)
        validate_legend(E.parse(str(destination)).getroot())
        row.update(svg_sha256=digest(destination), sheet_background=PAPER,
                   legend_presentation='a3-v3')
        print('A3 legend:',scope,row['stem'],flush=True)
    write_bibliography(base/'atlas', list(citations.values()))
    atomic_json(base/'atlas/sources/current-atlas.json', {**old, 'records':records})
    atomic_json(base/'atlas/sources/separate-sheets.json', {'schema':old['schema'],'records':records})
    return len(records)//2


def clone_completed(base, manifest):
    pointer = json.loads((data_root()/'build-current.json').read_text())
    source = Path(pointer.get('storage_output', pointer['output'])).resolve()
    path = source/'validation/full-build.json'
    if digest(path) != pointer['sha256']:
        raise DatasetError('Completed build receipt changed')
    previous = json.loads(path.read_text())
    if previous['status'] != 'passed' or previous['dataset_id'] != manifest['dataset_id']:
        raise DatasetError('Legend refresh requires a completed build of the selected dataset')
    manifest_path, _ = context()
    if previous['manifest_sha256'] != digest(manifest_path):
        raise DatasetError('Legend refresh requires the exact same dataset bytes')
    # A legend refresh can inherit scientific validation only while those
    # producers are byte-identical to the validated parent implementation.
    scientific = ('scripts/ocean_stage_2.py','scripts/ocean_temperature.py',
                  'scripts/ocean-stage-2-kernels.cc','scripts/project-stage-2-points.cc',
                  'scripts/prepare-ocean-climate-baseline.py','scripts/prepare-marine-heatwaves.py',
                  'scripts/prepare-ocean-thermal-seasons.py','scripts/prepare-coastal-compound-heat.py',
                  'scripts/prepare-heat-particulate-coexposure.py')
    for name in scientific:
        expected = previous['implementation']['files'].get(name)
        if expected is None or digest(ROOT/name) != expected:
            raise DatasetError('Legend refresh requires unchanged scientific producers: '+name)
    for i, record in enumerate(previous['files']):
        if digest(source/record['path']) != record['sha256']:
            raise DatasetError('Completed artifact changed: '+record['path'])
        if i%500 == 0:
            print(f'Verified {i}/{len(previous["files"])} retained artifacts',flush=True)
    def copy_file(old, new):
        p = Path(old)
        # Mutable JSON, text, legend exports and frontmatter get independent
        # bytes. Large map/data/native artifacts are shared and never rewritten.
        mutable = (p.suffix in ('.json','.html','.log') or 'legends' in p.parts or
                   p.name.startswith(('frontmatter-', 'contact-')) or '-legend.' in p.name)
        return shutil.copy2(old,new) if mutable else os.link(old,new)
    def ignore(folder, names):
        return [name for name in names if Path(folder)==source/'validation' and name in ('build-state.json','full-build.json')]
    shutil.copytree(source, base, dirs_exist_ok=True, symlinks=True, copy_function=copy_file, ignore=ignore)
    atomic_json(base/'sources/legend-refresh-parent.json', {'pointer':pointer, 'receipt':previous})
    return {'source_build_id':previous['build_id'], 'source_output':str(source),
            'source_receipt_sha256':pointer['sha256'], 'inherited_artifacts':len(previous['files']),
            'source_receipt':'sources/legend-refresh-parent.json'}


def refresh_optional(base, jobs):
    """Rebuild only optional legends using already validated product metadata."""
    env = font_environment()
    ocean = importlib.import_module('build-ocean-temperature-plates')
    climate = importlib.import_module('build-ocean-stage-2-plates')
    tasks = []
    manifests = {}
    for group in ('ocean','climate'):
        root = base/'anthropocene-optional'/group
        value = json.loads((root/'preview-manifest.json').read_text())
        manifests[group] = value
        for row in value['records']:
            if row['kind'] != 'legend':
                continue
            if group == 'ocean':
                product = next(p for p in value['products'] if (p['year'],p['period'],p['mode']) == (row['year'],row['period'],row['mode']))
                tree = ocean.make_legend(row['stem'],product['title'],row['mode'],product['metadata'],row['scope'],row['period'],{})
            else:
                product = next(p for p in value['products'] if (p['stem'],p['metric'],p['metadata']['period'],p['metadata'].get('monitor_class')) ==
                               (row['stem'],row['metric'],row['period'],row.get('monitor_class')))
                tree = climate.make_legend(row['stem'],product['title'],row['metric'],product['metadata'],row['scope'])
            validate_legend(tree)
            tasks.append((root,row,tree))
    def render(task):
        root,row,tree = task
        render_optional_legend(root,row,tree,env)
        print('Optional A3 legend:',row['scope'],row['stem'],flush=True)
    with ThreadPoolExecutor(max_workers=jobs) as pool:
        list(pool.map(render,tasks))
    for group,value in manifests.items():
        atomic_json(base/'anthropocene-optional'/group/'preview-manifest.json',value)
        if group=='climate':
            climate.write_index(value['products'],value['records'])
    return len(tasks)


def render_optional_legend(root, row, tree, env):
    """Keep the existing family/period/metric path; stems alone are not unique."""
    svg = root/row['svg']
    save(tree,svg)
    render_svg(svg,root/row['pdf'],env)
    render_svg(svg,root/row['preview'],env,width=2200)
    row.update(sheet_background=PAPER, **{field+'_sha256':digest(root/row[field])
                                         for field in ('svg','pdf','preview')})


def verify_parent(base, parent):
    """Prove sharing unchanged files never modified the accepted previous build."""
    old = json.loads((base/'sources/legend-refresh-parent.json').read_text())['receipt']
    source = Path(parent['source_output'])
    for record in old['files']:
        if digest(source/record['path']) != record['sha256']:
            raise DatasetError('Legend refresh modified its parent: '+record['path'])
    if digest(source/'validation/full-build.json') != parent['source_receipt_sha256']:
        raise DatasetError('Parent receipt changed during legend refresh')
    preserved = [r for r in old['files'] if (base/r['path']).is_file() and digest(base/r['path'])==r['sha256']]
    return {'parent_files_unchanged':len(old['files']), 'reused_unchanged_files':len(preserved),
            'reused_maps':sum('/maps/' in '/'+r['path'] for r in preserved)}
