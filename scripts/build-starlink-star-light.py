#!/usr/bin/env python3
"""Build the four SLSL v3 plates in World/USA with separate A3 legends."""
import argparse
from pathlib import Path
from starlink_star_light import CONFIG, ROOT, build, verify_delivery
import json


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--config',type=Path,default=CONFIG)
    parser.add_argument('--output',type=Path)
    parser.add_argument('--native',type=Path,help='matching native orbital SVG directory')
    parser.add_argument('--astronomy-source',type=Path,help='explicit newer all-sky SVG; otherwise use the pinned preserved artwork')
    parser.add_argument('--workers',type=int,default=2)
    parser.add_argument('--preview-width',type=int,default=2560)
    parser.add_argument('--skip-exports',action='store_true')
    parser.add_argument('--check',action='store_true',help='verify the existing completed delivery without rebuilding')
    args=parser.parse_args()
    if min(args.workers,args.preview_width)<=0:
        parser.error('Workers and preview width must be positive')
    if args.check:
        verify_delivery(args.output or ROOT/json.loads(args.config.read_text())['output'])
        return
    output,records,_=build(args.config,args.output,args.native,args.astronomy_source,args.workers,args.preview_width,not args.skip_exports)
    print(f'Validated {len(records)} sheets: {output}')


if __name__=='__main__':
    main()
