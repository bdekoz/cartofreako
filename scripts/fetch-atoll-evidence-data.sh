#!/usr/bin/env bash

# Fetch the two public USGS packages used by the exploration-only Majuro
# atoll-evidence canary.  Raw archives stay local under assets.static/.raw.

set -euo pipefail

if [[ $# -gt 1 ]]; then
  printf 'usage: %s [atoll-evidence-directory]\n' "$0" >&2
  exit 2
fi

data_directory=${1:-assets.static/atoll-evidence}
raw_directory=$data_directory/.raw
user_agent='cartofreako-atoll-evidence-canary/1.0 (+https://github.com/bdekoz/cartofreako)'

for command_name in curl cut jq md5sum sha256sum stat; do
  command -v "$command_name" >/dev/null 2>&1 || {
    printf 'missing required command: %s\n' "$command_name" >&2
    exit 2
  }
done

mkdir -p -- "$raw_directory"

fetch_catalog()
{
  local item_id=$1
  local output=$2
  local temporary=$output.part
  curl --silent --show-error --fail --location \
    --retry 5 --retry-all-errors --connect-timeout 20 --max-time 180 \
    -A "$user_agent" \
    "https://www.sciencebase.gov/catalog/item/$item_id?format=json" \
    --output "$temporary"
  jq -e --arg item_id "$item_id" '.id == $item_id and (.files | type == "array")' \
    "$temporary" >/dev/null
  mv -f -- "$temporary" "$output"
}

digest_for()
{
  local algorithm=$1
  local path=$2
  case $algorithm in
    md5) md5sum -- "$path" | cut -d ' ' -f 1 ;;
    sha256) sha256sum -- "$path" | cut -d ' ' -f 1 ;;
    *) printf 'unsupported digest algorithm: %s\n' "$algorithm" >&2; return 2 ;;
  esac
}

download_file()
{
  local catalog=$1
  local filename=$2
  local expected_size=$3
  local algorithm=$4
  local expected_digest=$5
  local output=$raw_directory/$filename
  local partial=$output.part
  local url actual_size actual_digest

  url=$(jq -er --arg filename "$filename" \
    '.files[] | select(.name == $filename) | .url' "$catalog")

  if [[ -f $output ]]; then
    actual_size=$(stat -c %s -- "$output")
    actual_digest=$(digest_for "$algorithm" "$output")
    if [[ $actual_size == "$expected_size" && $actual_digest == "$expected_digest" ]]; then
      printf 'using verified USGS package %s\n' "$output"
      return
    fi
    if [[ ! -e $partial ]]; then
      mv -- "$output" "$partial"
    else
      printf 'both an invalid output and partial download exist for %s\n' "$filename" >&2
      return 1
    fi
  fi

  printf 'fetching USGS package %s (%s bytes)\n' "$filename" "$expected_size"
  curl --silent --show-error --fail --location --continue-at - \
    --retry 20 --retry-all-errors --retry-delay 2 \
    --connect-timeout 30 --max-time 0 -A "$user_agent" \
    "$url" --output "$partial"

  actual_size=$(stat -c %s -- "$partial")
  if [[ $actual_size != "$expected_size" ]]; then
    printf 'USGS package size mismatch for %s: expected %s, got %s\n' \
      "$filename" "$expected_size" "$actual_size" >&2
    return 1
  fi
  actual_digest=$(digest_for "$algorithm" "$partial")
  if [[ $actual_digest != "$expected_digest" ]]; then
    printf 'USGS package %s mismatch for %s: expected %s, got %s\n' \
      "$algorithm" "$filename" "$expected_digest" "$actual_digest" >&2
    return 1
  fi
  mv -f -- "$partial" "$output"
}

tbdem_catalog=$raw_directory/sciencebase-majuro-tbdem.json
inundation_catalog=$raw_directory/sciencebase-majuro-inundation.json
fetch_catalog 59557881e4b04e08be532c9a "$tbdem_catalog"
fetch_catalog 5ba9511ee4b08583a5ca09fe "$inundation_catalog"

download_file "$tbdem_catalog" Majuro_TBDEM_Data.zip 2355022535 md5 \
  16b35677ba01331845285e178599b4ea
# ScienceBase publishes no checksum for this archive.  The SHA-256 below
# freezes the public 80,927,783-byte package inspected on 2026-08-10.
download_file "$inundation_catalog" Inundation_Exposure_Raster_Layers.zip \
  80927783 sha256 \
  6aea7d5b545825a83a9ab198af8695eeaf4cad507e69538b8dc684764e9f1818
download_file "$tbdem_catalog" majuro_tbdem_metadata.xml 56855 md5 \
  1e42997bdc5665c7d63401b9e17cdd91
download_file "$inundation_catalog" \
  Inundation_Exposure_FGDC_Metadata_Final_Clean.xml 26031 md5 \
  0ef769b294578b81b469300d30c2b102

(
  cd "$raw_directory"
  sha256sum -- \
    Majuro_TBDEM_Data.zip \
    Inundation_Exposure_Raster_Layers.zip \
    majuro_tbdem_metadata.xml \
    Inundation_Exposure_FGDC_Metadata_Final_Clean.xml \
    > SHA256SUMS
)

printf 'USGS Majuro source packages staged under ignored %s\n' "$raw_directory"
printf '%s\n' 'No source archive was added to a standard, optional, release, or upload graph.'
