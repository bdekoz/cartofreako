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
parser.add_argument('--retain-cache', action='store_true', help='retain verified completed-period bytes across runs and dates')
parser.add_argument('--allow-missing', action='store_true', help='exit 3 for HTTP 404 without publishing a file')
args = parser.parse_args()
try:
    record = fetch(args.url, args.output, os.environ["DATA_HTTP_CACHE"],
                   minimum_interval=args.minimum_interval, range_size=args.range_size, same_day_cache=args.same_day_cache,
                   retain_cache=args.retain_cache, allow_missing=args.allow_missing)
    if record is None:
        sys.exit(3)
except (DatasetError, KeyError) as error:
    print(f"fetch-data-http: {error}", file=sys.stderr)
    sys.exit(1)
