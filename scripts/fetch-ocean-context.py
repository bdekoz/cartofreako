#!/usr/bin/env python3
"""Acquire the pinned CRW and JMA inputs for the November 8 review edition."""
import argparse
from datetime import datetime, timezone
import json
from pathlib import Path

import requests

from ocean_temperature import digest, write_json

ROOT=Path(__file__).resolve().parents[1]


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root',type=Path,default=ROOT/'output/ocean-temperature-20261108')
    args=parser.parse_args()
    records=json.loads((ROOT/'config/ocean-context-20261108.json').read_text())['files']
    receipts=[]
    for source in records:
        target=args.root/source['path'];target.parent.mkdir(parents=True,exist_ok=True)
        if not target.exists():
            temporary=target.with_suffix(target.suffix+'.part')
            with requests.get(source['url'],stream=True,timeout=(30,180)) as response:
                response.raise_for_status()
                with temporary.open('wb') as stream:
                    for block in response.iter_content(1024**2):stream.write(block)
            if digest(temporary)!=source['sha256']:
                raise ValueError('Provider content differs from the pinned edition: '+source['url'])
            temporary.replace(target)
        if digest(target)!=source['sha256']:
            raise ValueError('Local input differs from its pinned digest: '+str(target))
        receipts.append({**source,'bytes':target.stat().st_size,
                         'verified_at':datetime.now(timezone.utc).isoformat()})
    write_json(args.root/'data/context-inputs.json',receipts)
    write_json(args.root/'cache/coral/manifest.json',[
        {**r,'path':Path(r['path']).name} for r in receipts if r['path'].startswith('cache/coral/')])
    print(f'Verified {len(receipts)} pinned CRW/JMA inputs')


if __name__=='__main__':main()
