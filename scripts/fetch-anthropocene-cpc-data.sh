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
file_url='https://psl.noaa.gov/thredds/fileServer/Datasets/cpc_global_temp'
user_agent='cartofreako-anthropocene/2.0 (+https://github.com/bkoz/cartofreako)'
gdalinfo_command=${GDALINFO:-gdalinfo}
mkdir -p "$raw_dir"

validate() {
  local path=$1
  local variable=$2
  "$gdalinfo_command" "NETCDF:$path:$variable" >/dev/null 2>&1
}

download_by_ranges() {
  local url=$1
  local output=$2
  local headers total current end expected actual chunk
  headers=$(curl -sS --http1.1 --location --fail --range 0-0 \
    --retry 20 --retry-all-errors --retry-delay 2 \
    --connect-timeout 15 --max-time 120 \
    -A "$user_agent" -D - -o /dev/null "$url")
  total=$(printf '%s\n' "$headers" | tr -d '\r' | awk '
    tolower($1) == "content-range:" {
      split($3, range, "/")
      size = range[2]
    }
    END { print size }
  ')
  if [[ ! $total =~ ^[1-9][0-9]*$ ]]; then
    echo "server did not report a usable byte length: $url" >&2
    return 1
  fi
  current=0
  if [[ -f $output ]]; then
    current=$(stat -c %s "$output")
  fi
  if ((current > total)); then
    echo "discarding oversized partial CPC download: $output" >&2
    rm -f "$output"
    current=0
  fi
  chunk="$output.range"
  while ((current < total)); do
    end=$((current + 2 * 1024 * 1024 - 1))
    if ((end >= total)); then
      end=$((total - 1))
    fi
    expected=$((end - current + 1))
    rm -f "$chunk"
    curl -sS --http1.1 --location --fail \
      --range "$current-$end" \
      --retry 20 --retry-all-errors --retry-delay 2 \
      --connect-timeout 15 --max-time 120 \
      -A "$user_agent" -o "$chunk" "$url"
    actual=$(stat -c %s "$chunk")
    if ((actual != expected)); then
      echo "short CPC byte range $current-$end from $url" >&2
      rm -f "$chunk"
      return 1
    fi
    cat "$chunk" >> "$output"
    current=$((end + 1))
  done
  rm -f "$chunk"
}

for year in $(seq "$start_year" "$end_year"); do
  for variable in tmax tmin; do
    output="$raw_dir/$variable.$year.nc"
    if [[ -s $output ]] && validate "$output" "$variable"; then
      printf 'using existing CPC input %s\n' "$output"
      continue
    fi

    # Keep a deterministic partial file so an interrupted 80--90 MB yearly
    # transfer can resume on the next invocation.  NOAA's THREDDS endpoint is
    # markedly more reliable over HTTP/1.1 than HTTP/2 for these large files.
    temporary="$raw_dir/.${variable}.${year}.nc.part"
    # The ordinary downloads endpoint intermittently returns 504, while
    # open-ended THREDDS responses can be closed by its proxy. Fixed,
    # length-checked ranges make restart behavior unambiguous for both fields.
    url="$file_url/$variable.$year.nc"
    printf 'fetching %s in verified byte ranges\n' "$url"
    download_by_ranges "$url" "$temporary"
    if ! validate "$temporary" "$variable"; then
      echo "download is not a readable CPC $variable NetCDF: $url" >&2
      exit 1
    fi
    mv -f "$temporary" "$output"
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
