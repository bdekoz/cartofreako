#!/usr/bin/env python3
"""Refresh bounded astronomy catalogs with retries, cache receipts and Gaia failover."""
import argparse
import csv
import json
import math
import os
from pathlib import Path
import sys
import tempfile
from urllib.parse import urlencode

from data_http import fetch
from dataset import DatasetError, ROOT, digest

GAIA_COLUMNS = 'source_id,ra,dec,parallax,pmra,pmdec,radial_velocity,phot_g_mean_mag,bp_rp'
GAIA_QUERY = ('SELECT TOP 500 ' + GAIA_COLUMNS +
              ' FROM gaiadr3.gaia_source WHERE phot_g_mean_mag < 5.5 ORDER BY phot_g_mean_mag')
GAIA_TAPS = ('https://gea.esac.esa.int/tap-server/tap/sync',
             'https://gaia.ari.uni-heidelberg.de/tap/sync')
PLANET_COLUMNS = 'pl_name,hostname,ra,dec,sy_dist,sy_vmag,disc_year,discoverymethod'
PLANET_QUERY = ('SELECT TOP 250 ' + PLANET_COLUMNS +
                ' FROM pscomppars WHERE ra IS NOT NULL AND dec IS NOT NULL ORDER BY sy_dist')
PLANET_TAP = 'https://exoplanetarchive.ipac.caltech.edu/TAP/sync'
SBDB_API = 'https://ssd-api.jpl.nasa.gov/sbdb.api'
SMALL_BODIES = (('ceres', '1 Ceres', '1'), ('vesta', '4 Vesta', '4'),
                ('eros', '433 Eros', '433'), ('apophis', '99942 Apophis', '99942'),
                ('halley', '1P', '1P'), ('encke', '2P', '2P'), ('67p', '67P', '67P'))


def validate_catalog(path, columns, count, identity):
    with path.open(encoding='utf-8-sig', newline='') as stream:
        reader = csv.DictReader(stream)
        if not set(columns.split(',')).issubset(reader.fieldnames or []):
            raise DatasetError(f'{path.name}: missing required CSV columns')
        rows = list(reader)
    if len(rows) != count:
        raise DatasetError(f'{path.name}: expected {count} rows, received {len(rows)}')
    identities = [row[identity] for row in rows]
    if any(not value for value in identities) or len(set(identities)) != count:
        raise DatasetError(f'{path.name}: missing or duplicate catalog identities')
    for row in rows:
        ra, dec = float(row['ra']), float(row['dec'])
        if not (math.isfinite(ra) and math.isfinite(dec) and 0 <= ra < 360 and -90 <= dec <= 90):
            raise DatasetError(f'{path.name}: invalid celestial coordinates')
        if identity == 'source_id' and not float(row['phot_g_mean_mag']) < 5.5:
            raise DatasetError(f'{path.name}: star outside the configured magnitude selection')


def validate_small_body(path, designation):
    record = json.loads(path.read_text())
    if record['object']['des'] != designation:
        raise DatasetError(f'{path.name}: unexpected JPL object identity')
    if not record['object']['fullname'] or not record['object']['kind']:
        raise DatasetError(f'{path.name}: incomplete JPL object metadata')
    orbit = record['orbit']
    values = [float(orbit['epoch'])]
    elements = {item['name']: item['value'] for item in orbit['elements']}
    values += [float(elements[name]) for name in ('e', 'a', 'i', 'om', 'w', 'ma', 'n')]
    if not all(map(math.isfinite, values)):
        raise DatasetError(f'{path.name}: invalid JPL orbital elements')


def refresh(output, cache, *, gaia_taps=GAIA_TAPS, planet_tap=PLANET_TAP,
            sbdb_api=SBDB_API, fetcher=None):
    output, cache = Path(output), Path(cache)
    fetcher = fetcher or fetch
    output.mkdir(parents=True, exist_ok=True)
    names = []
    with tempfile.TemporaryDirectory(prefix='.astro-fetch-', dir=output.parent) as folder:
        staging = Path(folder)

        def acquire(name, url, validator):
            print(f'astronomy: fetching {name} from {url}', flush=True)
            path = staging / name
            try:
                fetcher(url, path, cache, same_day_cache=True)
                validator(path)
            except (DatasetError, OSError, ValueError, KeyError, TypeError, csv.Error) as error:
                raise DatasetError(f'{name}: {error}') from None

        failures = []
        gaia_name = 'gaia-dr3-bright.csv'
        for endpoint in gaia_taps:
            url = endpoint + '?' + urlencode({'REQUEST': 'doQuery', 'LANG': 'ADQL',
                                              'FORMAT': 'csv', 'QUERY': GAIA_QUERY})
            try:
                acquire(gaia_name, url, lambda p: validate_catalog(p, GAIA_COLUMNS, 500, 'source_id'))
            except (DatasetError, OSError, ValueError, KeyError, TypeError, csv.Error) as error:
                failures.append(f'{endpoint}: {error}')
                print(f'astronomy: Gaia service failed: {failures[-1]}', file=sys.stderr, flush=True)
            else:
                names.append(gaia_name)
                break
        else:
            raise DatasetError('Gaia DR3 unavailable from all configured TAP services; ' + '; '.join(failures))

        planet_name = 'nasa-exoplanet-nearby.csv'
        acquire(planet_name, planet_tap + '?' +
                urlencode({'query': PLANET_QUERY, 'format': 'csv'}),
                lambda p: validate_catalog(p, PLANET_COLUMNS, 250, 'pl_name'))
        names.append(planet_name)
        for stem, search, designation in SMALL_BODIES:
            name = f'sbdb-{stem}.json'
            acquire(name, sbdb_api + '?' +
                    urlencode({'sstr': search, 'phys-par': '1'}),
                    lambda p: validate_small_body(p, designation))
            names.append(name)

        # Validate the entire staged bundle before replacing any previous
        # output. Successful individual requests remain in the shared cache
        # even when a later provider fails.
        (staging / 'SHA256SUMS').write_text(''.join(digest(staging / name) + '  ' + name + '\n'
                                                   for name in names))
        for name in [*names, *[name + '.receipt.json' for name in names], 'SHA256SUMS']:
            source = staging / name
            source.chmod(0o644)
            source.replace(output / name)
    print(f'astronomy data refreshed in {output}', flush=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('output', nargs='?', type=Path, default=Path('assets.static/astronomy'))
    args = parser.parse_args()
    os.environ['DATA_HTTP_RETRY_BUDGET'] = os.environ.get('ASTRO_HTTP_RETRY_BUDGET',
                                        os.environ.get('DATA_HTTP_RETRY_BUDGET', '60'))
    cache = Path(os.environ.get('DATA_HTTP_CACHE',
                 str(Path(os.environ.get('DATA_ROOT', ROOT / '.cartofreako/data')) / 'cache')))
    try:
        refresh(args.output, cache)
    except (DatasetError, OSError, ValueError, KeyError, TypeError, csv.Error) as error:
        print(f'fetch-astro-data: {error}; previous astronomy files retained; '
              'successful downloads remain cached. Retry with make data-update '
              '(or make fetch-astro-data for a standalone refresh).', file=sys.stderr)
        return 1
    return 0


if __name__ == '__main__':
    sys.exit(main())
