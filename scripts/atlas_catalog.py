"""Canonical current atlas identities; historical filenames are explicit aliases."""
from copy import deepcopy
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PATH = ROOT/'config/atlas-plates.json'


def catalog():
    return json.loads(PATH.read_text())


def lookup():
    result = {}
    for plate in catalog()['plates']:
        for key in [plate['id'], plate['source_stem'], *plate['aliases']]:
            if key in result and result[key]['id'] != plate['id']:
                raise ValueError('Ambiguous plate alias: '+key)
            result[key] = plate
    return result


def canonical(stem):
    return lookup()[stem]['id']


def default_entries(entries):
    bank = lookup()
    result = []
    for old in entries:
        plate = bank[old['stem']]
        if not plate['default']:
            continue
        row = deepcopy(old)
        row.update(stem=plate['id'],title=plate['title'],group=plate['group'],
                   source_stem=plate['source_stem'],lifecycle=plate['lifecycle'],maturity=plate['maturity'])
        result.append(row)
    order = {g['id']:i for i,g in enumerate(catalog()['groups'])}
    result.sort(key=lambda r:order[r['group']])
    for i, row in enumerate(result,1):
        row['ordinal']=i
    return result
