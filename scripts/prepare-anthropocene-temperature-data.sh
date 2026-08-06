#!/usr/bin/env bash

# Prepare both year-specific NOAA CPC H3 temperature-field candidates without
# overwriting checked profiles or normalized data.

set -euo pipefail

if [[ $# -gt 1 ]]; then
  echo "usage: $0 [anthropocene-data-directory]" >&2
  exit 2
fi

data_dir=${1:-assets.static/anthropocene}
raw_dir="$data_dir/.raw/cpc"
prepared_dir="$data_dir/.prepared"
profile_2025="$data_dir/anthropocene-temperature-2025-profile.json"
profile_2026="$data_dir/anthropocene-temperature-2026-profile.json"
preparer=${ANTHROPOCENE_TEMPERATURE_PREPARER:-src.generate/prepare-anthropocene-temperature}

for path in \
  "$profile_2025" \
  "$profile_2026" \
  "$raw_dir/SHA256SUMS"; do
  if [[ ! -f $path ]]; then
    echo "missing Anthropocene temperature input: $path" >&2
    exit 1
  fi
done
if [[ ! -x $preparer ]]; then
  echo "missing preparer executable: $preparer (run make $preparer)" >&2
  exit 1
fi
(
  cd "$raw_dir"
  sha256sum -c SHA256SUMS
)

manifest_digest=$(sha256sum "$raw_dir/SHA256SUMS" | cut -d ' ' -f 1)
for profile in "$profile_2025" "$profile_2026"; do
  if ! rg -q "\"manifest_sha256\": \"$manifest_digest\"" "$profile"; then
    echo "profile does not pin the staged CPC manifest: $profile" >&2
    echo "staged manifest SHA-256: $manifest_digest" >&2
    exit 1
  fi
done

mkdir -p "$prepared_dir"
"$preparer" "$raw_dir" \
  "$profile_2025" "$prepared_dir/anthropocene-temperature-2025.geojson" \
  "$profile_2026" "$prepared_dir/anthropocene-temperature-2026.geojson"
sha256sum \
  "$prepared_dir/anthropocene-temperature-2025.geojson" \
  "$prepared_dir/anthropocene-temperature-2026.geojson"
printf '%s\n' \
  'Candidates prepared only. Review coverage, totals, regional audits, profiles, and checksums before promotion.'
