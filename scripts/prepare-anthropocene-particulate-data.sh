#!/usr/bin/env bash

# Prepare a reviewable particulate candidate without overwriting checked data.

set -euo pipefail

if [[ $# -gt 2 ]]; then
  echo "usage: $0 [anthropocene-data-directory particulate-profile]" >&2
  exit 2
fi

data_dir=${1:-assets.static/anthropocene}
profile=${2:-$data_dir/anthropocene-particulate-2026-profile.json}
year=$(sed -n '/"duration"[[:space:]]*:/,/^[[:space:]]*}/ {
  s/^[[:space:]]*"year"[[:space:]]*:[[:space:]]*\([0-9][0-9]*\).*/\1/p
}' "$profile" | sed -n '1p')
if [[ -z $year ]]; then
  echo "profile does not contain duration.year: $profile" >&2
  exit 1
fi

raw_dir="$data_dir/.raw/$year"
prepared_dir="$data_dir/.prepared"
preparer=${ANTHROPOCENE_PARTICULATE_PREPARER:-src.generate/prepare-anthropocene-particulate}
for path in \
  "$profile" \
  "$raw_dir/ghcnd_gsn.tar.gz" \
  "$raw_dir/ghcnd-stations.txt" \
  "$raw_dir/daily_88101_${year}.zip" \
  "$raw_dir/hms_smoke${year}.zip" \
  "$raw_dir/storm-details-${year}.csv.gz" \
  "$raw_dir/storm-locations-${year}.csv.gz" \
  "$raw_dir/SHA256SUMS"; do
  if [[ ! -f $path ]]; then
    echo "missing Anthropocene refresh input: $path" >&2
    exit 1
  fi
done
sha256sum -c "$raw_dir/SHA256SUMS"
if [[ ! -x $preparer ]]; then
  echo "missing preparer executable: $preparer (run make $preparer)" >&2
  exit 1
fi

temporary_dir=$(mktemp -d)
trap 'rm -rf "$temporary_dir"' EXIT
mkdir -p "$temporary_dir/ghcn" "$temporary_dir/epa" \
  "$temporary_dir/hms" "$temporary_dir/storm" "$prepared_dir"
tar -xzf "$raw_dir/ghcnd_gsn.tar.gz" -C "$temporary_dir/ghcn"
unzip -q "$raw_dir/daily_88101_${year}.zip" -d "$temporary_dir/epa"
unzip -q "$raw_dir/hms_smoke${year}.zip" -d "$temporary_dir/hms"
gzip -cd "$raw_dir/storm-details-${year}.csv.gz" \
  > "$temporary_dir/storm/details.csv"
gzip -cd "$raw_dir/storm-locations-${year}.csv.gz" \
  > "$temporary_dir/storm/locations.csv"

epa_csv=$(find "$temporary_dir/epa" -type f -name '*.csv' -print -quit)
hms_shapefile=$(find "$temporary_dir/hms" -type f -name '*.shp' -print -quit)
if [[ -z $epa_csv || -z $hms_shapefile ]]; then
  echo "EPA or HMS archive did not contain its expected member" >&2
  exit 1
fi

ghcn_directory="$temporary_dir/ghcn"
if [[ -z $(find "$ghcn_directory" -maxdepth 1 -type f -name '*.dly' \
    -print -quit) ]]; then
  nested_ghcn="$ghcn_directory/ghcnd_gsn"
  nested_station=$(find "$nested_ghcn" -maxdepth 1 -type f -name '*.dly' \
    -print -quit 2>/dev/null || true)
  if [[ ! -d $nested_ghcn || -z $nested_station ]]; then
    echo "GHCN/GSN archive contained no .dly station files" >&2
    exit 1
  fi
  ghcn_directory=$nested_ghcn
fi

arguments=(
  "$profile"
  "$prepared_dir/anthropocene-particulate-${year}.geojson"
  --ghcn-dir "$ghcn_directory"
  --stations "$raw_dir/ghcnd-stations.txt"
  --epa "$epa_csv"
  --hms "$hms_shapefile"
  --storm-details "$temporary_dir/storm/details.csv"
  --storm-locations "$temporary_dir/storm/locations.csv"
  --cwfis-dir "$raw_dir/cwfis"
)
firms_count=0
if [[ -d $raw_dir/firms ]]; then
  while IFS= read -r -d '' path; do
    arguments+=(--firms "$path")
    ((firms_count += 1))
  done < <(find "$raw_dir/firms" -type f -name '*.csv' -print0 | sort -z)
fi
if ((firms_count == 0)); then
  if [[ ${ANTHROPOCENE_REGIONAL_DEVELOPMENT_ONLY:-0} == 1 ]]; then
    echo "preparing regional-development-only data without FIRMS" >&2
  else
    echo "global Anthropocene preparation requires staged NASA FIRMS CSVs" >&2
    exit 1
  fi
else
  arguments+=(--require-firms)
fi

"$preparer" "${arguments[@]}"
sha256sum "$prepared_dir/anthropocene-particulate-${year}.geojson"
printf '%s\n' \
  'Candidate prepared only. Audit source coverage, metrics, and checksum before replacing the checked GeoJSON/profile digest.'
