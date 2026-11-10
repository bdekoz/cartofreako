#!/usr/bin/env python3
"""Download one object into an isolated source workspace with revalidation."""
import argparse
import os
import sys

from data_http import fetch
from dataset import DatasetError

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument("url")
parser.add_argument("output")
parser.add_argument("--minimum-interval", type=int, default=0)
parser.add_argument("--range-size", type=int, help="download in bounded byte ranges of this size")
parser.add_argument("--same-day-cache", action="store_true", help="reuse validated objects checked on this UTC day")
args = parser.parse_args()
try:
    fetch(args.url, args.output, os.environ["DATA_HTTP_CACHE"],
          minimum_interval=args.minimum_interval, range_size=args.range_size, same_day_cache=args.same_day_cache)
except (DatasetError, KeyError) as error:
    print(f"fetch-data-http: {error}", file=sys.stderr)
    sys.exit(1)
