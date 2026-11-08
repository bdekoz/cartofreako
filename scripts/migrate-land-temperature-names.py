#!/usr/bin/env python3
"""Create canonical current land-temperature inputs from retained legacy files."""
import argparse
import json
from pathlib import Path
import shutil

from ocean_temperature import digest, write_json


def migrate(directory):
    for year in (2025,2026):
        legacy=f'anthropocene-temperature-{year}'
        current=f'anthropocene-land-temperature-{year}'
        profile=json.loads((directory/(legacy+'-profile.json')).read_text())
        source=directory/profile['data']['geojson']
        assert digest(source)==profile['data']['sha256']
        target=directory/(current+'.geojson')
        if not target.exists() or digest(target)!=digest(source):shutil.copyfile(source,target)
        profile['name']=profile['name'].replace('temperature','land temperature')
        profile['data']['geojson']=target.name
        write_json(directory/(current+'-profile.json'),profile)
    print('Canonical land-temperature profiles/data prepared; retained legacy sources are unchanged.')


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--directory',type=Path,default=Path('assets.static/anthropocene'))
    migrate(p.parse_args().directory)
