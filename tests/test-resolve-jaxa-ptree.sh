#!/usr/bin/env bash

set -euo pipefail

repository_root=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd -P)
resolver="$repository_root/scripts/resolve-jaxa-ptree.sh"
temporary_dir=$(mktemp -d)
trap 'rm -rf -- "$temporary_dir"' EXIT

netrc="$temporary_dir/netrc"
umask 077
: > "$netrc"

product="$temporary_dir/server/pub/himawari/L2/CLP/010"
mkdir -p "$product/202607/31/23" "$product/202608/08/00"
printf '%s\n' old \
  > "$product/202607/31/23/NC_H09_20260731_2340_L2CLP010_FLDK.02401_02401.nc"
printf '%s\n' latest \
  > "$product/202607/31/23/NC_H09_20260731_2350_L2CLP010_FLDK.02401_02401.nc"
printf '%s\n' future \
  > "$product/202608/08/00/NC_H09_20260808_0000_L2CLP010_FLDK.02401_02401.nc"

output_directory="$temporary_dir/output"
output_json="$temporary_dir/ptree.json"
selection=$(PTREE_NETRC="$netrc" "$resolver" \
  "file://$product" '2026-08-07T22:42:17Z' \
  "$output_directory" "$output_json")

grep -Fq 'P-Tree latest available: NC_H09_20260731_2350' <<<"$selection"
grep -Fq 'P-Tree source interval: 2026-07-31T23:50:00Z to 2026-08-01T00:00:00Z' \
  <<<"$selection"
jq -e '
  .selection == "latest-published-not-after"
  and .start_utc == "2026-07-31T23:50:00Z"
  and .end_utc == "2026-08-01T00:00:00Z"
  and .age_hours_at_selection > 166
  and .age_hours_at_selection < 167
  and .files[0].path
    == "NC_H09_20260731_2350_L2CLP010_FLDK.02401_02401.nc"
' "$output_json" >/dev/null
test "$(<"$output_directory/NC_H09_20260731_2350_L2CLP010_FLDK.02401_02401.nc")" \
  = latest

gzip_product="$temporary_dir/gzip-server/pub/himawari/L2/CLP/010"
mkdir -p "$gzip_product/202606/30/23"
gzip_netcdf="$gzip_product/202606/30/23/NC_H09_20260630_2350_L2CLP010_FLDK.02801_02401.nc"
printf '%s\n' compressed > "$gzip_netcdf"
gzip -n "$gzip_netcdf"
gzip_output="$temporary_dir/gzip-output"
gzip_json="$temporary_dir/gzip-ptree.json"
PTREE_NETRC="$netrc" "$resolver" \
  "file://$gzip_product" '2026-07-01T00:05:00Z' \
  "$gzip_output" "$gzip_json" >/dev/null
jq -e '
  .files[0].path
    == "NC_H09_20260630_2350_L2CLP010_FLDK.02801_02401.nc"
  and (.source_url | endswith(".nc.gz"))
' "$gzip_json" >/dev/null
test "$(<"$gzip_output/NC_H09_20260630_2350_L2CLP010_FLDK.02801_02401.nc")" \
  = compressed

printf '%s\n' 'P-Tree latest-available resolver tests passed'
