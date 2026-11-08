#!/usr/bin/env python3
"""Extend a pinned resource profile with audited lithium and uranium tables."""
import argparse
from copy import deepcopy
import json
from pathlib import Path
import shutil

from ocean_temperature import digest, write_json

ROOT=Path(__file__).resolve().parents[1]


def prepare(source, output, additions):
    if source.resolve()==output.resolve():
        raise ValueError('Keep the dated mineral extension separate from its base resource snapshot')
    profile=json.loads((source/'resources-profile.json').read_text())
    values=json.loads((source/profile['values']['path']).read_text())
    assert digest(source/profile['values']['path'])==profile['values']['sha256']
    geometry=json.loads((source/profile['country_geometry']['path']).read_text())
    countries={f['properties']['RESOURCE_A3'] for f in geometry['features']}
    output.mkdir(parents=True,exist_ok=True)
    for name in ('countries-110m.geojson','coral-reefs-025deg.geojson'):
        shutil.copyfile(source/name,output/name)
    family=next(f for f in profile['families'] if f['id']=='resources-mineral')
    added_ids={m['id'] for m in additions['metrics']}
    family['metrics']=[m for m in family['metrics'] if m['id'] not in added_ids|{'lithium','uranium'}]
    values['records']=[r for r in values['records'] if r['metric'] not in added_ids]
    source_ids={s['id'] for s in additions['sources']}
    profile['sources']=[s for s in profile['sources'] if s['id'] not in source_ids]+additions['sources']
    for m in additions['metrics']:
        assert len({r['iso3'] for r in m['rows']})==len(m['rows'])
        assert all(r['iso3'] in countries and r['value']>=0 for r in m['rows'])
        assert not set(m['withheld'])&{r['iso3'] for r in m['rows']}
        total=sum(r['value'] for r in m['rows'])
        assert total == m['transcribed_country_total']
        assert .90<=total/m['world_total']<=1.01
        assert m['world_total']-total == m['unallocated_difference_to_rounded_total']
        coverage=dict(covered_countries=len(m['rows']),mapped_countries=len(countries),
                      country_percent=round(100*len(m['rows'])/len(countries),3),population_percent=None,
                      output_percent=round(min(100,100*total/m['world_total']),3),passes_non_sparse=True)
        family['metrics'].append(dict(id=m['id'],title=m['title'],unit=m['unit'],
            reference_period=str(m['year'])+(' estimate' if m['year']==2025 else ''),
            evidence_class='reported-statistic',source_ids=[m['source_id']],status='released',scale='log1p',
            output_tag=m['id']+'-'+str(m['year']),coverage=coverage,spatial=None,
            notes=m['notes']+' Coverage denominator: '+m['world_total_scope']+'.'))
        values['records'] += [dict(family='resources-mineral',metric=m['id'],year=m['year'],**r) for r in m['rows']]
    values['records'].sort(key=lambda r:(r['family'],r['metric'],r['iso3']))
    profile['snapshot_as_of']=values['snapshot_as_of']='2026-11-08'
    profile['name']+=' / mineral additions 8 November 2026'
    profile['description']+=' Lithium and uranium added; all other source periods and observations are retained from the base snapshot.'
    write_json(output/'resources-values.json',values)
    profile['values']['sha256']=digest(output/'resources-values.json')
    write_json(output/'resources-profile.json',profile)
    write_json(output/'mineral-additions-provenance.json',{'base_profile_sha256':digest(source/'resources-profile.json'),'base_values_sha256':digest(source/'resources-values.json'),'additions':additions})
    (output/'SHA256SUMS').write_text(''.join(digest(output/name)+'  '+name+'\n' for name in ('resources-profile.json','resources-values.json','countries-110m.geojson','coral-reefs-025deg.geojson')))
    print('Prepared lithium (2025, 9 countries; U.S. withheld) and uranium (2024, 16 countries; includes one reported zero).')


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--source',type=Path,default=ROOT/'assets.static/resources')
    p.add_argument('--output',type=Path,default=ROOT/'assets.static/resources/current-20261108')
    a=p.parse_args()
    prepare(a.source,a.output,json.loads((ROOT/'config/mineral-additions-20261108.json').read_text()))
