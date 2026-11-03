#!/usr/bin/env bash
# Capture a new dated snapshot; never replace the historical/default inputs.
set -euo pipefail
if [[ $# -gt 1 ]]; then
  echo "usage: $0 [new-output-directory]" >&2
  exit 2
fi
repository_root=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd -P)
profile=${ORBITING_PROFILE:-$repository_root/assets.static/orbital-technosphere/20261103/orbital-technosphere-profile.json}
output=${1:-$repository_root/build/orbital-technosphere-refresh-$(date -u +%Y%m%dT%H%M%SZ)}
instant=${ORBITING_TIMESTAMP:-$(date -u +%Y-%m-%dT%H:%M:00Z)}
exec python3 "$repository_root/scripts/refresh-orbiting-snapshot.py" \
  --template "$profile" --output "$output" --timestamp "$instant" \
  --cache "$repository_root/build/orbital-technosphere-download-cache" \
  --historical-reference-profile "$repository_root/assets.static/orbital-technosphere/orbital-technosphere-profile.json"
