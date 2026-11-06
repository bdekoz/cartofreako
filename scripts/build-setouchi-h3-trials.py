#!/usr/bin/env python3
"""Rebuild dated atmosphere/temperature observations on H3r5 and H3r8 trial plates."""
import argparse
from concurrent.futures import ThreadPoolExecutor
from copy import deepcopy
from datetime import datetime
import json
import os
from pathlib import Path
import subprocess

from legend_informatics import ROOT, digest
from setouchi_futures import write_json

DEFAULT_CONFIG = ROOT / 'config/setouchi-h3-trials-20261106.json'


def pinned(record):
    path = ROOT / record['path']
    if digest(path) != record['sha256']:
        raise ValueError('Pinned trial input changed: ' + record['path'])
    return path


def verify_inputs(config):
    pinned(config['baseline'])
    for subject in ('atmosphere', 'temperature'):
        pinned(config[subject]['profile'])
    path = pinned(config['atmosphere']['fetch_manifest'])
    fetch = json.loads(path.read_text())
    for observation in fetch['observations']:
        for record in observation['files']:
            source = path.parent / record['path']
            if digest(source) != record['sha256']:
                raise ValueError('Atmosphere raster changed: ' + str(source))
    path = pinned(config['temperature']['raw_manifest'])
    subprocess.run(['sha256sum', '--quiet', '-c', path.name], cwd=path.parent, check=True)
    print('Verified all pinned JAXA and CPC raw inputs', flush=True)


def prepare_product(config, resolution, subject):
    output = ROOT / config['output'] / 'sources' / f'h3r{resolution}'
    build = ROOT / config['build'] / f'h3r{resolution}' / 'data'
    output.mkdir(parents=True, exist_ok=True)
    build.mkdir(parents=True, exist_ok=True)
    stem = 'cloud-atmosphere' if subject == 'atmosphere' else 'anthropocene-temperature-2026'
    source_profile = pinned(config[subject]['profile'])
    profile = json.loads(source_profile.read_text())
    profile['aggregation']['h3_resolution'] = resolution
    profile['name'] += f' — H3r{resolution} source-center trial'
    profile['description'] += (' Trial: original sample centers indexed at the stated H3 resolution; '
                               'unoccupied cells are unobserved, and source-pixel footprints are not filled.')
    target = build / (stem + '.geojson')
    candidate = build / (stem + '-profile.json')
    helper = ROOT / 'build/setouchi-h3-tools' / ('prepare-' + subject)
    env = os.environ.copy()
    if subject == 'atmosphere':
        manifest = pinned(config[subject]['fetch_manifest'])
        timestamp = json.loads(manifest.read_text())['process_start_utc']
        env['SOURCE_DATE_EPOCH'] = str(int(datetime.fromisoformat(timestamp.replace('Z', '+00:00')).timestamp()))
        profile['data']['prepared_snapshot'] = target.relative_to(ROOT).as_posix()
        args = [str(helper), str(candidate), str(manifest), str(target)]
        source_hash = digest(manifest)
    else:
        manifest = pinned(config[subject]['raw_manifest'])
        profile['aggregation']['cell_domain'] = config[subject]['cell_domain']
        profile['data'] = {'geojson': target.name, 'sha256': ''}
        args = [str(helper), str(manifest.parent), str(candidate), str(target)]
        source_hash = digest(manifest)
    fingerprint = {'profile': deepcopy(profile), 'raw_manifest_sha256': source_hash,
                   'preparer_sha256': digest(helper)}
    receipt = build / (stem + '-receipt.json')
    old = json.loads(receipt.read_text()) if receipt.exists() else None
    if not (old and old['fingerprint'] == fingerprint and target.exists()
            and digest(target) == old['snapshot_sha256']):
        write_json(candidate, profile)
        log = build / (stem + '-prepare.log')
        print(f'Preparing {subject} H3r{resolution}', flush=True)
        with log.open('w') as stream:
            subprocess.run(args, env=env, stdout=stream, stderr=subprocess.STDOUT, check=True)
        old = {'fingerprint': fingerprint, 'snapshot': target.relative_to(ROOT).as_posix(),
               'snapshot_sha256': digest(target), 'bytes': target.stat().st_size}
        write_json(receipt, old)
    if subject == 'temperature':
        profile['data']['sha256'] = old['snapshot_sha256']
    profile_path = output / (stem + '-profile.json')
    write_json(profile_path, profile)
    record = {k: v for k, v in old.items() if k != 'fingerprint'}
    record.update(subject=subject, stem=stem, h3_resolution=resolution,
                  profile=profile_path.relative_to(ROOT).as_posix(), profile_sha256=digest(profile_path),
                  preparer_sha256=digest(helper), raw_manifest_sha256=source_hash,
                  sampling='original source-center sampling; no spatial interpolation')
    write_json(output / (stem + '-product.json'), record)
    print(f'Prepared {subject} H3r{resolution}: {target.stat().st_size / 1e6:.1f} MB', flush=True)
    return record


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--config', type=Path, default=DEFAULT_CONFIG)
    parser.add_argument('--prepare-only', action='store_true')
    parser.add_argument('--render-only', action='store_true', help='Render already prepared, checksum-verified products')
    parser.add_argument('--package-only', action='store_true', help='Optimize completed PDFs and assemble the review')
    parser.add_argument('--resolutions', nargs='+', type=int)
    args = parser.parse_args()
    config = json.loads(args.config.read_text())
    if config['schema'] != 'cartofreako-setouchi-h3-trials-v1':
        raise ValueError('Unsupported trial config')
    if sum([args.prepare_only, args.render_only, args.package_only]) > 1:
        raise ValueError('Choose one preparation/rendering/packaging stage flag')
    if config['data_raster_dpi'] != 300:
        raise ValueError('This trial edition requires 300 dpi data layers')
    resolutions = args.resolutions or config['resolutions']
    if len(resolutions) != len(set(resolutions)) or not set(resolutions) <= {3, 5, 8}:
        raise ValueError('Use distinct resolutions from 3, 5, 8')
    if args.render_only or args.package_only:
        from setouchi_h3_trials import build_plates
        from setouchi_pdf_images import package_delivery
        saved = json.loads((ROOT / config['output'] / 'products.json').read_text())
        if saved['config_sha256'] != digest(args.config):
            raise ValueError('Prepared product configuration changed')
        selected = [p for p in saved['products'] if p['h3_resolution'] in resolutions]
        if {(p['h3_resolution'], p['subject']) for p in selected} != {
                (r, s) for r in resolutions for s in ('atmosphere', 'temperature')}:
            raise ValueError('Missing requested trial products')
        pinned(config['baseline'])
        if not args.package_only: build_plates(config, selected)
        package_delivery(config, selected)
        return
    verify_inputs(config)
    subprocess.run(['make', '-s', '-j2', 'build/setouchi-h3-tools/prepare-atmosphere',
                    'build/setouchi-h3-tools/prepare-temperature'], cwd=ROOT, check=True)
    products = []
    # Only one atmosphere snapshot lives in memory at a time. Temperature's
    # source-center domain is bounded by the 259,200 input grid centers.
    for resolution in resolutions:
        with ThreadPoolExecutor(max_workers=2) as pool:
            jobs = [pool.submit(prepare_product, config, resolution, subject)
                    for subject in ('atmosphere', 'temperature')]
            products.extend(job.result() for job in jobs)
    # A single-resolution resume must not discard the other prepared product
    # records: --package-only needs both for the complete comparison gallery.
    manifest_path = ROOT / config['output'] / 'products.json'
    previous = json.loads(manifest_path.read_text()) if manifest_path.exists() else None
    retained = []
    if previous and previous['config_sha256'] == digest(args.config):
        retained = [p for p in previous['products'] if p['h3_resolution'] not in resolutions]
    all_products = sorted(retained + products, key=lambda p: (p['h3_resolution'], p['subject']))
    write_json(manifest_path, {
        'schema': 'cartofreako-setouchi-h3-trial-products-v1', 'config': config,
        'config_sha256': digest(args.config), 'products': all_products})
    if not args.prepare_only:
        from setouchi_h3_trials import build_plates
        from setouchi_pdf_images import package_delivery
        build_plates(config, products)
        package_delivery(config, products)


if __name__ == '__main__':
    main()
