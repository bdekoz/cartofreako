#!/usr/bin/env python3
"""Publish or check all standard plate filenames as separate map and legend sheets."""
import argparse
from pathlib import Path

from legend_informatics import ROOT
from setouchi_delivery import standard_files


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--delivery', type=Path, default=ROOT / 'output/setouchi-triennale-2028-st2')
    parser.add_argument('--check', action='store_true')
    args = parser.parse_args()
    result = standard_files(args.delivery, check=args.check)
    print(f"{'Verified' if args.check else 'Published'} {result['files']} standard files: "
          '76 cartography/data sheets + 76 separate legend/bibliography sheets.')


if __name__ == '__main__':
    main()
