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
end_year=${3:-${CPC_END_YEAR:-$(date -u +%Y)}}
if [[ ! $start_year =~ ^[0-9]{4}$ || ! $end_year =~ ^[0-9]{4}$ \
      || $start_year -gt $end_year ]]; then
  echo "invalid CPC year range: $start_year through $end_year" >&2
  exit 2
fi

raw_dir="$data_dir/.raw/cpc"
file_url=${CPC_BASE_URL:-https://psl.noaa.gov/thredds/fileServer/Datasets/cpc_global_temp}
file_url=${file_url%/}
range_size=${CPC_HTTP_RANGE_SIZE:-2097152}
cache_args=()
case ${CPC_HTTP_DAILY_CACHE:-1} in
  1) cache_args+=(--same-day-cache) ;;
  0) ;;
  *) echo 'CPC_HTTP_DAILY_CACHE must be 0 or 1' >&2; exit 2 ;;
esac
# Legacy direct fetches still reuse readable local files. Every actual transfer
# uses the same paced, identity-checked downloader as current data editions.
revalidate=0
if [[ -n ${DATA_HTTP_CACHE:-} ]]; then
  revalidate=1
fi
project_root=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)
export DATA_HTTP_CACHE=${DATA_HTTP_CACHE:-${DATA_ROOT:-$project_root/.cartofreako/data}/cache}
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
    if ((revalidate == 0)) && [[ -s $output ]] && validate "$output" "$variable"; then
      printf 'using existing CPC input %s\n' "$output"
      continue
    fi
    printf 'revalidating %s in verified byte ranges\n' "$file_url/$variable.$year.nc"
    python3 "$project_root/scripts/data-http-fetch.py" \
      "$file_url/$variable.$year.nc" "$output" --range-size "$range_size" "${cache_args[@]}"
    validate "$output" "$variable" \
      || { echo "CPC download is not a readable $variable NetCDF" >&2; exit 1; }
  done
done

(
  cd "$raw_dir"
  find . -maxdepth 1 -type f \
    \( -name 'tmax.*.nc' -o -name 'tmin.*.nc' \) \
    | LC_ALL=C sort \
    | xargs sha256sum \
    > SHA256SUMS
)

printf 'NOAA CPC inputs staged in %s for %s through %s\n' \
  "$raw_dir" "$start_year" "$end_year"
printf '%s\n' \
  'The local files and SHA256SUMS are the source snapshot; later upstream revisions require an explicit refresh.'
