#!/usr/bin/env bash

set -euo pipefail

if [[ $# -gt 1 ]]; then
  echo "usage: $0 [output-directory]" >&2
  exit 2
fi

project_root=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)
# Astronomy queries are small. Bound an unavailable endpoint before trying a
# Gaia partner, while honoring explicit per-source or general retry budgets.
export DATA_HTTP_RETRY_BUDGET=${ASTRO_HTTP_RETRY_BUDGET:-${DATA_HTTP_RETRY_BUDGET:-60}}
exec python3 "$project_root/scripts/fetch-astro-data.py" "${1:-assets.static/astronomy}"
