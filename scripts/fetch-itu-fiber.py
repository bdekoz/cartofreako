#!/usr/bin/env python3
"""Cache and audit ITU's anonymous public terrestrial fibre route layer."""
import argparse
from collections import Counter
import datetime as dt
import hashlib
import json
from pathlib import Path

import requests

PARAMS = dict(service='WFS', version='2.0.0', request='GetFeature',
              typeNames='ITU:trx_public_2', outputFormat='application/json',
              srsName='EPSG:4326', CQL_FILTER="type_inf LIKE 'Fibre%'",
              count=50000, sortBy='id')
URL = requests.Request('GET', 'https://bbmaps.itu.int/geoserver/wfs', params=PARAMS).prepare().url


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, default=Path(__file__).resolve().parents[1] / 'assets.static/fiber-synthesized/itu')
    parser.add_argument('--check', action='store_true', help='Validate the existing cache without network access')
    args = parser.parse_args()
    target = args.output / 'terrestrial-fiber.geojson'
    if args.check:
        body = target.read_bytes()
    else:
        response = requests.get(URL, timeout=(20, 180))
        response.raise_for_status()
        body = response.content
    data = json.loads(body)
    features = data['features']
    assert data['type'] == 'FeatureCollection' and features
    assert len(features) < PARAMS['count'], 'Pagination required: request limit reached'
    assert len({f['id'] for f in features}) == len(features)
    assert all(f['properties']['type_inf'].startswith('Fibre') for f in features)
    assert all(f['geometry']['type'] in ['LineString', 'MultiLineString'] for f in features)
    for f in features:
        lines = f['geometry']['coordinates']
        if f['geometry']['type'] == 'LineString':
            lines = [lines]
        assert all(len(line) >= 2 for line in lines)
        assert all(-180 <= p[0] <= 180 and -90 <= p[1] <= 90 for line in lines for p in line)
    digest = hashlib.sha256(body).hexdigest()
    if args.check:
        assert digest == json.loads((args.output / 'provenance.json').read_text())['sha256']
    else:
        args.output.mkdir(parents=True, exist_ok=True)
        target.write_bytes(body)
        receipt = dict(url=URL, retrieved_at_utc=dt.datetime.now(dt.timezone.utc).isoformat(),
                       feature_count=len(features), sha256=digest,
                       status_counts=dict(Counter(f['properties']['type_inf'] for f in features)),
                       source_page='https://bbmaps.itu.int/bbmaps/',
                       scope='Published anonymous terrestrial fibre routes; microwave and restricted layers excluded',
                       line_width_pt=0.5, opacity=0.75, color_name='Kelly green', color_hex='#4CBB17')
        (args.output / 'provenance.json').write_text(json.dumps(receipt, indent=2) + '\n')
    print(f'ITU cache verified: {len(features):,} fibre features; SHA256 {digest}')


if __name__ == '__main__':
    main()
