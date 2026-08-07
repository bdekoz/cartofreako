#!/usr/bin/env bash

# Resolve and download the newest published P-Tree H09 L2 CLP observation not
# after a requested process instant. P-Tree publication can lag observation;
# the selected source interval and age are always recorded and reported.

set -euo pipefail

usage()
{
  printf '%s\n' \
    'usage: resolve-jaxa-ptree.sh PRODUCT-URL CUTOFF-UTC OUTPUT-DIRECTORY OUTPUT-JSON' >&2
  exit 2
}

fail()
{
  printf 'resolve-jaxa-ptree: %s\n' "$*" >&2
  exit 1
}

[[ $# -eq 4 ]] || usage
product_url=${1%/}
cutoff_input=$2
output_directory=$3
output_json=$4

for command in curl date gzip jq sha256sum awk sed sort tail tr mktemp; do
  command -v "$command" >/dev/null 2>&1 \
    || fail "missing prerequisite: $command"
done

cutoff_epoch=$(date -u -d "$cutoff_input" +%s) \
  || fail "invalid cutoff timestamp: $cutoff_input"
cutoff=$(date -u -d "@$cutoff_epoch" +%Y-%m-%dT%H:%M:%SZ)
cutoff_nominal=$(date -u -d "@$((cutoff_epoch - 600))" +%Y%m%d%H%M)
cutoff_month=${cutoff_nominal:0:6}
cutoff_day=${cutoff_nominal:0:8}
cutoff_hour=${cutoff_nominal:0:10}

netrc=${PTREE_NETRC:-${HOME:?HOME is required}/.netrc}
[[ -r $netrc ]] || fail "P-Tree netrc is not readable: $netrc"

cacert=${PTREE_CACERT:-}
ca_arguments=()
if [[ -n $cacert ]]; then
  [[ $cacert = /* ]] || fail 'PTREE_CACERT must be an absolute path'
  [[ -r $cacert ]] || fail "P-Tree CA certificate is not readable: $cacert"
  ca_arguments=(--cacert "$cacert")
fi

temporary_dir=$(mktemp -d)
trap 'rm -rf -- "$temporary_dir"' EXIT
mkdir -p "$output_directory"

list_directory()
{
  local url=$1
  local output=$2
  curl --fail --silent --show-error --ssl-reqd \
    --netrc-file "$netrc" "${ca_arguments[@]}" --list-only \
    --connect-timeout 30 --max-time 90 "${url%/}/" --output "$output"
}

root_listing="$temporary_dir/root.txt"
list_directory "$product_url" "$root_listing" \
  || fail "cannot list P-Tree CLP product root: $product_url/"

selected_filename=
selected_directory=
while IFS= read -r month; do
  ((10#$month <= 10#$cutoff_month)) || continue
  month_url="$product_url/$month"
  month_listing="$temporary_dir/month-$month.txt"
  list_directory "$month_url" "$month_listing" || continue
  while IFS= read -r day; do
    year_month_day=$month$day
    ((10#$year_month_day <= 10#$cutoff_day)) || continue
    day_url="$month_url/$day"
    day_listing="$temporary_dir/day-$year_month_day.txt"
    list_directory "$day_url" "$day_listing" || continue
    while IFS= read -r hour; do
      year_month_day_hour=$year_month_day$hour
      ((10#$year_month_day_hour <= 10#$cutoff_hour)) || continue
      hour_url="$day_url/$hour"
      hour_listing="$temporary_dir/hour-$year_month_day_hour.txt"
      list_directory "$hour_url" "$hour_listing" || continue
      filename=$(sed -n \
        '/^NC_H09_[0-9]\{8\}_[0-9]\{4\}_L2CLP010_FLDK\.\(02401_02401\|02801_02401\)\.nc\(\.gz\)\?$/p' \
        "$hour_listing" | tr -d '\r' | sort | while IFS= read -r entry; do
          nominal=$(sed -n \
            's/^NC_H09_\([0-9]\{8\}\)_\([0-9]\{4\}\)_.*/\1\2/p' \
            <<<"$entry")
          if [[ -n $nominal ]] && ((10#$nominal <= 10#$cutoff_nominal)); then
            printf '%s\n' "$entry"
          fi
        done | tail -n 1)
      if [[ -n $filename ]]; then
        selected_filename=$filename
        selected_directory="${hour_url%/}/"
        break
      fi
    done < <(tr -d '\r' < "$day_listing" \
      | sed -n '/^[0-9]\{2\}$/p' | sort -r)
    [[ -z $selected_filename ]] || break
  done < <(tr -d '\r' < "$month_listing" \
    | sed -n '/^[0-9]\{2\}$/p' | sort -r)
  [[ -z $selected_filename ]] || break
done < <(tr -d '\r' < "$root_listing" \
  | sed -n '/^[0-9]\{6\}$/p' | sort -r)

[[ -n $selected_filename ]] \
  || fail "P-Tree supplied no matching H09 CLP NetCDF not after $cutoff"

nominal=$(sed -n \
  's/^NC_H09_\([0-9]\{8\}\)_\([0-9]\{4\}\)_.*/\1\2/p' \
  <<<"$selected_filename")
[[ ${#nominal} -eq 12 ]] || fail "cannot parse P-Tree filename: $selected_filename"
start_epoch=$(date -u -d \
  "${nominal:0:4}-${nominal:4:2}-${nominal:6:2} ${nominal:8:2}:${nominal:10:2}:00Z" \
  +%s)
end_epoch=$((start_epoch + 600))
((end_epoch <= cutoff_epoch)) \
  || fail "selected P-Tree observation ends after $cutoff"
start_utc=$(date -u -d "@$start_epoch" +%Y-%m-%dT%H:%M:%SZ)
end_utc=$(date -u -d "@$end_epoch" +%Y-%m-%dT%H:%M:%SZ)
age_seconds=$((cutoff_epoch - end_epoch))
age_hours=$(awk -v seconds="$age_seconds" 'BEGIN {printf "%.3f", seconds / 3600}')

source_url=$selected_directory$selected_filename
downloaded="$output_directory/$selected_filename"
curl --fail --silent --show-error --ssl-reqd \
  --netrc-file "$netrc" "${ca_arguments[@]}" --remove-on-error \
  --connect-timeout 30 --max-time 900 --output "$downloaded" "$source_url"
[[ -s $downloaded ]] || fail "P-Tree download is empty: $source_url"

if [[ $selected_filename == *.nc.gz ]]; then
  gzip -t "$downloaded"
  netcdf_name=${selected_filename%.gz}
  gzip -cd "$downloaded" > "$output_directory/$netcdf_name"
else
  netcdf_name=$selected_filename
fi
netcdf="$output_directory/$netcdf_name"
[[ -s $netcdf ]] || fail "resolved P-Tree NetCDF is empty: $netcdf"

fetched_at=$(date -u +%Y-%m-%dT%H:%M:%SZ)
jq -n \
  --arg source jaxa-ptree-cloud \
  --arg collection 'Himawari-9 L2CLP010' \
  --arg start "$start_utc" --arg end "$end_utc" \
  --arg fetched "$fetched_at" --arg source_url "$source_url" \
  --arg coverage 'Himawari full disk; daytime cloud retrieval only' \
  --arg path "$netcdf_name" --arg file_url "$source_url" \
  --arg sha "$(sha256sum "$netcdf" | sed 's/[[:space:]].*//')" \
  --argjson age_hours "$age_hours" \
  '{source:$source,collection:$collection,start_utc:$start,end_utc:$end,
    fetched_at_utc:$fetched,source_url:$source_url,coverage:$coverage,
    selection:"latest-published-not-after",age_hours_at_selection:$age_hours,
    files:[{path:$path,source_url:$file_url,sha256:$sha,scale:null,
            offset:null,nodata:null,asset_key:"CLP"}]}' \
  > "$output_json"

printf 'P-Tree latest available: %s\n' "$selected_filename"
printf 'P-Tree source interval: %s to %s (%s hours old at %s)\n' \
  "$start_utc" "$end_utc" "$age_hours" "$cutoff"
