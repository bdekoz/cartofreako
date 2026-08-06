#!/usr/bin/env bash

# Fetch immutable local copies of the NOAA CPC Global Unified Temperature
# yearly NetCDF files used by the non-sparse Anthropocene temperature pass.

set -euo pipefail

if [[ $# -lt 1 || $# -gt 3 ]]; then
  echo "usage: $0 anthropocene-data-directory [start-year [end-year]]" >&2
  exit 2
fi

data_dir=$1
start_year=${2:-1979}
end_year=${3:-$(date -u +%Y)}
if [[ ! $start_year =~ ^[0-9]{4}$ || ! $end_year =~ ^[0-9]{4}$ \
      || $start_year -gt $end_year ]]; then
  echo "invalid CPC year range: $start_year through $end_year" >&2
  exit 2
fi

raw_dir="$data_dir/.raw/cpc"
base_url='https://downloads.psl.noaa.gov/Datasets/cpc_global_temp'
user_agent='cartofreako-anthropocene/2.0 (+https://github.com/bkoz/cartofreako)'
gdalinfo_command=${GDALINFO:-gdalinfo}
mkdir -p "$raw_dir"

validate() {
  local path=$1
  local variable=$2
  "$gdalinfo_command" "NETCDF:$path:$variable" >/dev/null 2>&1
}

for year in $(seq "$start_year" "$end_year"); do
  for variable in tmax tmin; do
    output="$raw_dir/$variable.$year.nc"
    if [[ -s $output ]] && validate "$output" "$variable"; then
      printf 'using existing CPC input %s\n' "$output"
      continue
    fi

    temporary=$(mktemp "$raw_dir/.${variable}.${year}.XXXXXX.nc")
    trap 'rm -f "$temporary"' EXIT
    url="$base_url/$variable.$year.nc"
    printf 'fetching %s\n' "$url"
    curl -sS --fail --remove-on-error -A "$user_agent" \
      -o "$temporary" "$url"
    if ! validate "$temporary" "$variable"; then
      echo "download is not a readable CPC $variable NetCDF: $url" >&2
      exit 1
    fi
    mv -f "$temporary" "$output"
    trap - EXIT
  done
done

(
  cd "$raw_dir"
  find . -maxdepth 1 -type f -name 'tmax.*.nc' -o \
    -type f -name 'tmin.*.nc' \
    | LC_ALL=C sort \
    | xargs sha256sum \
    > SHA256SUMS
)

printf 'NOAA CPC inputs staged in %s for %s through %s\n' \
  "$raw_dir" "$start_year" "$end_year"
printf '%s\n' \
  'The local files and SHA256SUMS are the source snapshot; later upstream revisions require an explicit refresh.'
