#!/usr/bin/env python3
"""Check current pass identities, grouping, selection and mineral data semantics."""
import json
from pathlib import Path
import re

from atlas_catalog import ROOT, catalog, lookup


def main():
    data=catalog();bank=lookup();plates=data['plates']
    ids={p['id'] for p in plates}
    assert len(ids)==len(plates)
    groups={g['id'] for g in data['groups']}
    assert all(p['group'] in groups for p in plates)
    assert all(re.fullmatch('[a-z0-9]+(?:-[a-z0-9]+)*',p['id']) for p in plates)
    assert not any(p['id'].startswith(('ahtropocene','anthropocene-temperature-','petroleum-','resources-fauna-coral')) for p in plates)
    for year in (2025,2026):
        for metric in ('land-temperature','water-temperature','water-temperature-anomaly'):
            assert f'anthropocene-{metric}-{year}' in ids
    assert bank['resources-fauna-coral-reef-threat-2011']['group']=='anthropocene'
    solar=bank['cloud-atmosphere']['selected_presentation']
    assert solar['h3_resolution']==5 and solar['map_background']=='#fcc553'
    assert solar['settings']=='config/setouchi-futures-20261106-h3r5.json'
    for p in plates:
        if p['id'].startswith('bathymetry-'):
            assert p['maturity']=='prototype' and p['lifecycle']=='optional' and not p['default']
        if p['source_stem'].startswith('petroleum-'):
            assert p['group']=='resources-energy' and p['default']
    standard=json.loads((ROOT/'contracts/standard-artifact-manifest-v1.json').read_text())
    assert not any(r['passId'].startswith('bathymetry-') for r in standard['artifacts'])
    assert not any(r['passId'].startswith('anthropocene-temperature-') for r in standard['artifacts'])
    additions=json.loads((ROOT/'config/mineral-additions-20261108.json').read_text())
    assert {m['id'] for m in additions['metrics']}=={'lithium-mine-production','uranium-mine-production'}
    for m in additions['metrics']:
        assert len(m['rows'])==len({r['iso3'] for r in m['rows']})
        assert m['transcribed_country_total']==sum(r['value'] for r in m['rows'])
        assert m['unallocated_difference_to_rounded_total']==m['world_total']-m['transcribed_country_total']
    li,u=additions['metrics']
    assert li['year']==2025 and li['withheld']==['USA'] and not any(r['iso3']=='USA' for r in li['rows'])
    assert u['year']==2024 and next(r for r in u['rows'] if r['iso3']=='DEU')['value']==0
    assert not any(r['iso3']=='RUS' for r in u['rows'])  # never allocate the BGS residual by inference
    styles=json.loads((ROOT/'generation-style.json').read_text())['resources']['mineral_types']
    assert len({r['color'] for r in styles.values()})==3
    assert len({r['shape'] for r in styles.values()})==3
    print(f'Catalog passed: {len(plates)} named plates, {sum(p["default"] for p in plates)} defaults; names, groups, prototypes and mineral semantics consistent.')


if __name__=='__main__':main()
