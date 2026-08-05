#!/usr/bin/env bash

set -euo pipefail

if [[ $# -gt 1 ]]; then
  echo "usage: $0 [output-directory]" >&2
  exit 2
fi

output_dir=${1:-assets.static/orbital-technosphere}
profile="$output_dir/orbital-technosphere-profile.json"
if [[ ! -f $profile ]]; then
  echo "missing authoritative profile: $profile" >&2
  exit 1
fi

temporary_dir=$(mktemp -d)
trap 'rm -rf "$temporary_dir"' EXIT
user_agent='cartofreako-orbital-technosphere/1.0 (+https://github.com/bkoz/cartofreako)'

fetch() {
  local output=$1
  shift
  # CelesTrak's usage policy says to stop and report any HTTP error,
  # especially 403/404, rather than retrying and extending a temporary block.
  curl -sS --fail -A "$user_agent" "$@" -o "$output"
}

groups=(
  'active|active'
  'starlink|starlink'
  'oneweb|oneweb'
  'kuiper|kuiper'
  'qianfan|qianfan'
  'hulianwang|hulianwang'
  'gnss|gnss'
  'iridium-next|iridium-NEXT'
  'globalstar|globalstar'
  'orbcomm|orbcomm'
  'resource|resource'
  'science|science'
  'stations|stations'
  'fengyun-1c-debris|fengyun-1c-debris'
  'iridium-33-debris|iridium-33-debris'
  'cosmos-2251-debris|cosmos-2251-debris'
)

complete_snapshot=true
for entry in "${groups[@]}"; do
  file_stem=${entry%%|*}
  if [[ ! -s $output_dir/celestrak-$file_stem.csv ]]; then
    complete_snapshot=false
  fi
done
if [[ ! -s $output_dir/nasa-ssc-reference.json ]]; then
  complete_snapshot=false
fi

# CelesTrak checks for new GP data only once every two hours and restricts the
# large active and Starlink groups to one download per update. Treat the
# checked-in set as the cache and avoid a network request inside that window.
if [[ $complete_snapshot == true && ${ORBITING_FORCE_REFRESH:-0} != 1 ]]; then
  if modified=$(stat -c %Y "$output_dir/celestrak-active.csv" 2>/dev/null); then
    :
  else
    modified=$(stat -f %m "$output_dir/celestrak-active.csv")
  fi
  current=$(date +%s)
  if (( current - modified < 7200 )); then
    echo "Orbital Technosphere snapshot is less than two hours old; reusing it"
    exit 0
  fi
fi

for entry in "${groups[@]}"; do
  file_stem=${entry%%|*}
  group=${entry#*|}
  echo "fetching CelesTrak group $group"
  fetch "$temporary_dir/celestrak-$file_stem.csv" --get \
    'https://celestrak.org/NORAD/elements/gp.php' \
    --data-urlencode "GROUP=$group" \
    --data-urlencode 'FORMAT=csv'
  header=$(sed -n '1p' "$temporary_dir/celestrak-$file_stem.csv")
  if [[ $header != OBJECT_NAME,OBJECT_ID,EPOCH,* ]]; then
    echo "unexpected CelesTrak OMM header for group $group" >&2
    exit 1
  fi
done

if [[ $(wc -l < "$temporary_dir/celestrak-active.csv") -lt 10001 ]]; then
  echo "CelesTrak active snapshot is unexpectedly small" >&2
  exit 1
fi

nasa_url=$(sed -n \
  's/^[[:space:]]*"query_url": "\([^"]*\)",*$/\1/p' "$profile")
if [[ -z $nasa_url ]]; then
  echo "profile is missing catalogs.nasa_ssc_reference.query_url" >&2
  exit 1
fi
echo "fetching NASA SSCWeb reference"
fetch "$temporary_dir/nasa-ssc-reference.json" \
  -H 'Accept: application/json' "$nasa_url"
if ! rg -q 'SUCCESS' "$temporary_dir/nasa-ssc-reference.json"; then
  echo "NASA SSCWeb response did not report SUCCESS" >&2
  exit 1
fi

mkdir -p "$output_dir"
for entry in "${groups[@]}"; do
  file_stem=${entry%%|*}
  install -m 0644 "$temporary_dir/celestrak-$file_stem.csv" \
    "$output_dir/celestrak-$file_stem.csv"
done
install -m 0644 "$temporary_dir/nasa-ssc-reference.json" \
  "$output_dir/nasa-ssc-reference.json"

sha256sum "$output_dir"/celestrak-*.csv \
  "$output_dir/nasa-ssc-reference.json" > "$output_dir/SHA256SUMS"

echo "Orbital Technosphere data refreshed in $output_dir"
