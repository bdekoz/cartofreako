#!/usr/bin/env bash

# Fetch mutable raw source files for an explicitly dated Anthropocene refresh.
# Normal map generation never calls this script and uses the checked snapshot.

set -euo pipefail

if [[ $# -gt 2 ]]; then
  echo "usage: $0 [anthropocene-data-directory [profile]]" >&2
  exit 2
fi

data_dir=${1:-assets.static/anthropocene}
profile=${2:-$data_dir/anthropocene-profile.json}
if [[ ! -f $profile ]]; then
  echo "missing authoritative profile: $profile" >&2
  exit 1
fi

year=$(sed -n '/"duration"[[:space:]]*:/,/^[[:space:]]*}/ {
  s/^[[:space:]]*"year"[[:space:]]*:[[:space:]]*\([0-9][0-9]*\).*/\1/p
}' "$profile" | sed -n '1p')
snapshot_date=$(sed -n \
  's/^[[:space:]]*"as_of_utc"[[:space:]]*:[[:space:]]*"\([0-9-]*\)T.*/\1/p' \
  "$profile" | sed -n '1p')
data_through=$(sed -n \
  's/^[[:space:]]*"data_through"[[:space:]]*:[[:space:]]*"\([0-9-]*\)".*/\1/p' \
  "$profile" | sed -n '1p')
if [[ -z $year || -z $snapshot_date ]]; then
  echo "profile does not contain a duration year and snapshot date" >&2
  exit 1
fi
if [[ -n $data_through ]]; then
  snapshot_date=$(date -u -d "$data_through + 1 day" +%F)
fi

raw_dir="$data_dir/.raw/$year"
temporary_dir=$(mktemp -d)
trap 'rm -rf "$temporary_dir"' EXIT
user_agent='cartofreako-anthropocene/1.0 (+https://github.com/bkoz/cartofreako)'

fetch() {
  local output=$1
  local url=$2
  local description=${3:-$url}
  echo "fetching $description"
  curl -sS --fail --remove-on-error -A "$user_agent" \
    -o "$output" "$url"
  if [[ ! -s $output ]]; then
    echo "download is empty: $url" >&2
    exit 1
  fi
}

mkdir -p "$temporary_dir/cwfis" "$temporary_dir/firms"
fetch "$temporary_dir/ghcnd_gsn.tar.gz" \
  'https://www.ncei.noaa.gov/pub/data/ghcn/daily/ghcnd_gsn.tar.gz'
fetch "$temporary_dir/ghcnd-stations.txt" \
  'https://www.ncei.noaa.gov/pub/data/ghcn/daily/ghcnd-stations.txt'
fetch "$temporary_dir/daily_88101_${year}.zip" \
  "https://aqs.epa.gov/aqsweb/airdata/daily_88101_${year}.zip"
fetch "$temporary_dir/hms_smoke${year}.zip" \
  "https://satepsanone.nesdis.noaa.gov/pub/FIRE/web/HMS/Smoke_Polygons/Shapefile/Annual_Bundles/hms_smoke${year}.zip"

tar -tzf "$temporary_dir/ghcnd_gsn.tar.gz" >/dev/null
unzip -tqq "$temporary_dir/daily_88101_${year}.zip"
unzip -tqq "$temporary_dir/hms_smoke${year}.zip"

storm_base='https://www.ncei.noaa.gov/pub/data/swdi/stormevents/csvfiles'
fetch "$temporary_dir/storm-index.html" "$storm_base/"
details_name=$(rg -o \
  "StormEvents_details-ftp_v1\\.0_d${year}_c[0-9]+\\.csv\\.gz" \
  "$temporary_dir/storm-index.html" | sort -u | tail -n 1)
locations_name=$(rg -o \
  "StormEvents_locations-ftp_v1\\.0_d${year}_c[0-9]+\\.csv\\.gz" \
  "$temporary_dir/storm-index.html" | sort -u | tail -n 1)
if [[ -z $details_name || -z $locations_name ]]; then
  echo "NOAA Storm Events index has no details/locations pair for $year" >&2
  exit 1
fi
fetch "$temporary_dir/$details_name" "$storm_base/$details_name"
fetch "$temporary_dir/$locations_name" "$storm_base/$locations_name"
gzip -t "$temporary_dir/$details_name"
gzip -t "$temporary_dir/$locations_name"

first_date="${year}-01-01"
last_date=$(date -u -d "$snapshot_date - 1 day" +%F)
current_date=$first_date
cwfis_files=0
while [[ $current_date < $snapshot_date ]]; do
  compact_date=${current_date//-/}
  output="$temporary_dir/cwfis/$compact_date.csv"
  url="https://cwfis.cfs.nrcan.gc.ca/downloads/hotspots/$compact_date.csv"
  status=$(curl -sS --remove-on-error -A "$user_agent" \
    -o "$output" -w '%{http_code}' "$url")
  case $status in
    200)
      if [[ $(sed -n '1p' "$output") != lat,*lon,*rep_date,* ]]; then
        echo "unexpected CWFIS CSV header: $url" >&2
        exit 1
      fi
      ((cwfis_files += 1))
      ;;
    404)
      rm -f "$output"
      ;;
    *)
      echo "CWFIS returned HTTP $status for $url" >&2
      exit 1
      ;;
  esac
  current_date=$(date -u -d "$current_date + 1 day" +%F)
done
if ((cwfis_files == 0)); then
  echo "CWFIS supplied no daily hotspot files for $first_date through $last_date" >&2
  exit 1
fi

# A global release requires NASA FIRMS. The explicit regional-development
# override exists for pipeline debugging and must never promote a checked
# global snapshot.
if [[ -n ${FIRMS_MAP_KEY:-} ]]; then
  availability="$temporary_dir/firms-data-availability.csv"
  fetch "$availability" \
    "https://firms.modaps.eosdis.nasa.gov/api/data_availability/csv/${FIRMS_MAP_KEY}/ALL" \
    'NASA FIRMS source-availability table'
  if [[ $(sed -n '1p' "$availability" | tr -d '\r') \
        != data_id,min_date,max_date ]]; then
    echo "unexpected NASA FIRMS availability response" >&2
    exit 1
  fi

  # S-NPP is the canonical global VIIRS series. Standard processing and NRT
  # are queried only over the ranges advertised by FIRMS, so the NRT tail
  # begins where the approximately five-month-lagged standard series ends.
  # Maintainers may add NOAA-20/21 sources explicitly for a multi-sensor union.
  read -r -a firms_sources <<< \
    "${ANTHROPOCENE_FIRMS_SOURCES:-VIIRS_SNPP_SP VIIRS_SNPP_NRT}"
  if ((${#firms_sources[@]} == 0)); then
    echo "ANTHROPOCENE_FIRMS_SOURCES must name at least one FIRMS source" >&2
    exit 1
  fi
  firms_delay=${ANTHROPOCENE_FIRMS_DELAY_SECONDS:-25}
  if [[ ! $firms_delay =~ ^[0-9]+([.][0-9]+)?$ ]]; then
    echo "ANTHROPOCENE_FIRMS_DELAY_SECONDS must be a nonnegative number" >&2
    exit 1
  fi
  for firms_source in "${firms_sources[@]}"; do
    if ! available_range=$(awk -F, -v wanted="$firms_source" '
      NR == 1 {
        for (column = 1; column <= NF; ++column) {
          gsub(/\r|"/, "", $column)
          if ($column == "data_id") source_column = column
          if ($column == "min_date") minimum_column = column
          if ($column == "max_date") maximum_column = column
        }
        next
      }
      {
        gsub(/\r|"/, "", $source_column)
        if ($source_column == wanted) {
          gsub(/\r|"/, "", $minimum_column)
          gsub(/\r|"/, "", $maximum_column)
          print $minimum_column, $maximum_column
          found = 1
          exit
        }
      }
      END { if (!found) exit 1 }
    ' "$availability"); then
      echo "NASA FIRMS does not advertise requested source: $firms_source" >&2
      exit 1
    fi
    read -r available_minimum available_maximum <<< "$available_range"
    if [[ ! $available_minimum =~ ^[0-9]{4}-[0-9]{2}-[0-9]{2}$ \
          || ! $available_maximum =~ ^[0-9]{4}-[0-9]{2}-[0-9]{2}$ ]]; then
      echo "NASA FIRMS returned invalid availability dates for $firms_source" >&2
      exit 1
    fi
    current_date=$first_date
    if [[ $available_minimum > $current_date ]]; then
      current_date=$available_minimum
    fi
    source_end=$(date -u -d "$available_maximum + 1 day" +%F)
    if [[ $snapshot_date < $source_end ]]; then
      source_end=$snapshot_date
    fi
    if [[ ! $current_date < $source_end ]]; then
      echo "skipping $firms_source: no advertised data in the profile period"
      continue
    fi
    chunk_index=0
    while [[ $current_date < $source_end ]]; do
      remaining=$((
        ($(date -u -d "$source_end" +%s)
         - $(date -u -d "$current_date" +%s)) / 86400
      ))
      day_range=$remaining
      if ((day_range > 5)); then
        day_range=5
      fi
      output=$(printf '%s/firms/%03d-%s-%s.csv' \
        "$temporary_dir" "$chunk_index" "$firms_source")
      url="https://firms.modaps.eosdis.nasa.gov/api/area/csv/${FIRMS_MAP_KEY}/${firms_source}/world/${day_range}/${current_date}"
      fetch "$output" "$url" \
        "NASA FIRMS $firms_source world/$day_range from $current_date"
      if [[ $(sed -n '1p' "$output") != latitude,longitude,* ]]; then
        echo "unexpected NASA FIRMS CSV response for $firms_source on $current_date" >&2
        exit 1
      fi
      current_date=$(date -u -d "$current_date + $day_range days" +%F)
      ((chunk_index += 1))
      if [[ $current_date < $source_end && $firms_delay != 0 ]]; then
        sleep "$firms_delay"
      fi
    done
  done
else
  if [[ ${ANTHROPOCENE_REGIONAL_DEVELOPMENT_ONLY:-0} == 1 ]]; then
    echo "FIRMS_MAP_KEY is unset; staging regional-development-only data" >&2
  else
    echo "FIRMS_MAP_KEY is required for a global Anthropocene refresh" >&2
    echo "set ANTHROPOCENE_REGIONAL_DEVELOPMENT_ONLY=1 only for local pipeline debugging" >&2
    exit 1
  fi
fi

mkdir -p "$raw_dir/cwfis" "$raw_dir/firms"
install -m 0644 "$temporary_dir/ghcnd_gsn.tar.gz" "$raw_dir/"
install -m 0644 "$temporary_dir/ghcnd-stations.txt" "$raw_dir/"
install -m 0644 "$temporary_dir/daily_88101_${year}.zip" "$raw_dir/"
install -m 0644 "$temporary_dir/hms_smoke${year}.zip" "$raw_dir/"
install -m 0644 "$temporary_dir/$details_name" \
  "$raw_dir/storm-details-${year}.csv.gz"
install -m 0644 "$temporary_dir/$locations_name" \
  "$raw_dir/storm-locations-${year}.csv.gz"
find "$temporary_dir/cwfis" -maxdepth 1 -type f -name '*.csv' \
  -exec install -m 0644 -t "$raw_dir/cwfis" {} +
firms_file=$(find "$temporary_dir/firms" -maxdepth 1 -type f -name '*.csv' \
  -print -quit)
if [[ -n $firms_file ]]; then
  install -m 0644 "$availability" "$raw_dir/"
  find "$temporary_dir/firms" -maxdepth 1 -type f -name '*.csv' \
    -exec install -m 0644 -t "$raw_dir/firms" {} +
fi

find "$raw_dir" -type f ! -name SHA256SUMS -print0 \
  | sort -z | xargs -0 sha256sum > "$raw_dir/SHA256SUMS"
printf 'Anthropocene raw refresh staged in %s (%s CWFIS files)\n' \
  "$raw_dir" "$cwfis_files"
printf '%s\n' \
  'Raw feeds are mutable. Review coverage and regenerate the normalized snapshot before changing the checked checksum.'
