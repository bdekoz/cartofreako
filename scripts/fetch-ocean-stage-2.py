#!/usr/bin/env python3
"""Restore the two Stage 2 public inputs using the frozen acquisition receipt."""
import json
import subprocess

from ocean_stage_2 import OUTPUT
from ocean_temperature import digest


def main():
    rows=json.loads((OUTPUT/'data/stage-2-acquisition.json').read_text())['inputs']
    for row in rows:
        path=OUTPUT/row['file']
        if path.exists():
            if digest(path)!=row['sha256']:raise ValueError('Changed pinned source: '+str(path))
            continue
        path.parent.mkdir(parents=True,exist_ok=True);part=path.with_suffix(path.suffix+'.part')
        args=['curl','--http1.1','--location','--fail','--retry','4','--retry-all-errors','--max-time','180']
        if part.exists():args+=['--continue-at','-']
        subprocess.run([*args,row['url'],'--output',str(part)],check=True)
        if digest(part)!=row['sha256']:raise ValueError('Upstream input differs from the November 8 edition: '+row['url'])
        part.replace(path)
    print(f'Verified {len(rows)} pinned Stage 2 public inputs')


if __name__=='__main__':main()
