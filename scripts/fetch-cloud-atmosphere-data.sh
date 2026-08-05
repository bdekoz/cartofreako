#!/usr/bin/env bash

# Stage immutable latest-not-after JAXA atmosphere inputs for local preparation.

set -euo pipefail

if [[ $# -gt 1 ]]; then
  echo "usage: $0 [cloud-atmosphere-data-directory]" >&2
  exit 2
fi

data_dir=${1:-assets.static/cloud-atmosphere}
profile="$data_dir/cloud-atmosphere-profile.json"
resolver=$(dirname "$0")/resolve-jaxa-stac.py
for path in "$profile" "$resolver"; do
  if [[ ! -f $path ]]; then
    echo "missing cloud-atmosphere input: $path" >&2
    exit 1
  fi
done
for command in curl jq gzip sha256sum date python3; do
  if ! command -v "$command" >/dev/null; then
    echo "missing cloud-atmosphere fetch prerequisite: $command" >&2
    exit 1
  fi
done

profile_source_field()
{
  local source_id=$1
  local field=$2
  jq -er --arg source_id "$source_id" --arg field "$field" '
    .sources
    | map(select(.id == $source_id))
    | if length == 1 then .[0][$field]
      else error("profile must contain exactly one source " + $source_id)
      end
    | select(type == "string" and length > 0)
  ' "$profile"
}

if [[ -n ${SOURCE_DATE_EPOCH:-} ]]; then
  process_start=$(date -u -d "@${SOURCE_DATE_EPOCH}" +%Y-%m-%dT%H:%M:%SZ)
else
  process_start=$(date -u +%Y-%m-%dT%H:%M:%SZ)
fi
stamp=${process_start//[-:]/}
stamp=${stamp/T/}
stamp=${stamp/Z/}
raw_root="$data_dir/.raw"
destination="$raw_root/$stamp"
temporary_dir=$(mktemp -d)
trap 'rm -rf "$temporary_dir"' EXIT

if [[ -n ${PTREE_BASE_URL:-} ]]; then
  ptree_product="${PTREE_BASE_URL%/}/pub/himawari/L2/CLP/010"
else
  ptree_product=$(profile_source_field jaxa-ptree-cloud url)
  ptree_product=${ptree_product%/}
fi
# A P-Tree filename records the start of a ten-minute full-disk observation.
# Require the complete observation interval to end no later than process start,
# matching the interval checks used by the preparer and renderer.
ptree_start_cutoff=$(date -u -d "$process_start - 10 minutes" +%Y%m%d%H%M)
ptree_filename=
ptree_remote_directory=

# Query at most seven hourly directories, then choose the newest 10-minute
# cloud product whose nominal observation time is not in the future.
for hours_back in 0 1 2 3 4 5 6; do
  candidate=$(date -u -d "$process_start - $hours_back hour" +%Y-%m-%dT%H:00:00Z)
  year_month=$(date -u -d "$candidate" +%Y%m)
  day=$(date -u -d "$candidate" +%d)
  hour=$(date -u -d "$candidate" +%H)
  remote_directory="$ptree_product/$year_month/$day/$hour/"
  listing="$temporary_dir/ptree-$year_month$day$hour.txt"
  if curl -sS --fail --netrc --list-only --connect-timeout 30 \
      --max-time 90 "$remote_directory" -o "$listing"; then
    filename=$(sed -n \
      '/NC_H09_[0-9]\{8\}_[0-9]\{4\}_L2CLP010_FLDK\.\(02401_02401\|02801_02401\)\.nc\.gz$/p' \
      "$listing" | sort | while IFS= read -r entry; do
        nominal=$(sed -n \
          's/^NC_H09_\([0-9]\{8\}\)_\([0-9]\{4\}\)_.*/\1\2/p' \
          <<<"$entry")
        if [[ -n $nominal && $nominal -le $ptree_start_cutoff ]]; then
          printf '%s\n' "$entry"
        fi
      done | tail -n 1)
    if [[ -n $filename ]]; then
      ptree_filename=$filename
      ptree_remote_directory=$remote_directory
      break
    fi
  fi
done
if [[ -z $ptree_filename ]]; then
  echo "P-Tree supplied no H09 CLP file not after $process_start within six hours" >&2
  echo "verify that .netrc contains an entry for ftp.ptree.jaxa.jp" >&2
  exit 1
fi
echo "fetching P-Tree $ptree_filename"
curl -sS --fail --netrc --remove-on-error --connect-timeout 30 \
  --max-time 900 -o "$temporary_dir/$ptree_filename" \
  "$ptree_remote_directory$ptree_filename"
gzip -t "$temporary_dir/$ptree_filename"
ptree_nc=${ptree_filename%.gz}
gzip -cd "$temporary_dir/$ptree_filename" > "$temporary_dir/$ptree_nc"
ptree_nominal=$(sed -n \
  's/^NC_H09_\([0-9]\{8\}\)_\([0-9]\{4\}\)_.*/\1\2/p' \
  <<<"$ptree_filename")
ptree_start=$(date -u -d \
  "${ptree_nominal:0:4}-${ptree_nominal:4:2}-${ptree_nominal:6:2} ${ptree_nominal:8:2}:${ptree_nominal:10:2}:00Z" \
  +%Y-%m-%dT%H:%M:%SZ)
ptree_end=$(date -u -d "$ptree_start + 10 minutes" +%Y-%m-%dT%H:%M:%SZ)
fetched_at=$(date -u +%Y-%m-%dT%H:%M:%SZ)
jq -n \
  --arg source jaxa-ptree-cloud \
  --arg collection 'Himawari-9 L2CLP010' \
  --arg start "$ptree_start" --arg end "$ptree_end" \
  --arg fetched "$fetched_at" \
  --arg source_url "$ptree_remote_directory$ptree_filename" \
  --arg coverage 'Himawari full disk; daytime cloud retrieval only' \
  --arg path "$ptree_nc" \
  --arg file_url "$ptree_remote_directory$ptree_filename" \
  --arg sha "$(sha256sum "$temporary_dir/$ptree_nc" | sed 's/[[:space:]].*//')" \
  '{source:$source,collection:$collection,start_utc:$start,end_utc:$end,
    fetched_at_utc:$fetched,source_url:$source_url,coverage:$coverage,
    files:[{path:$path,source_url:$file_url,sha256:$sha,scale:null,
            offset:null,nodata:null,asset_key:"CLP"}]}' \
  > "$temporary_dir/ptree.json"

python3 "$resolver" \
  --root "$(profile_source_field jaxa-gcom-c-aod url)" \
  --collection "$(profile_source_field jaxa-gcom-c-aod collection)" \
  --source jaxa-gcom-c-aod \
  --coverage "$(profile_source_field jaxa-gcom-c-aod coverage)" \
  --cutoff "$process_start" --output-directory "$temporary_dir" \
  --output-json "$temporary_dir/aod.json"
python3 "$resolver" \
  --root "$(profile_source_field jaxa-gsmap-precipitation url)" \
  --collection "$(profile_source_field jaxa-gsmap-precipitation collection)" \
  --source jaxa-gsmap-precipitation \
  --coverage "$(profile_source_field jaxa-gsmap-precipitation coverage)" \
  --cutoff "$process_start" --output-directory "$temporary_dir" \
  --output-json "$temporary_dir/precipitation.json"
python3 "$resolver" \
  --root "$(profile_source_field jaxa-jasmes-swr url)" \
  --collection "$(profile_source_field jaxa-jasmes-swr collection)" \
  --source jaxa-jasmes-swr \
  --coverage "$(profile_source_field jaxa-jasmes-swr coverage)" \
  --cutoff "$process_start" --output-directory "$temporary_dir" \
  --output-json "$temporary_dir/swr.json"

mkdir -p "$destination"
find "$temporary_dir" -maxdepth 1 -type f \
  ! -name '*.json' ! -name 'ptree-*.txt' \
  -exec install -m 0644 -t "$destination" {} +
for document in ptree.json aod.json precipitation.json swr.json; do
  jq --arg prefix "$stamp/" \
    '.files |= map(.path = ($prefix + .path))' \
    "$temporary_dir/$document" > "$destination/$document"
done
jq -n --arg process_start "$process_start" --arg fetched "$fetched_at" \
  --slurpfile ptree "$destination/ptree.json" \
  --slurpfile aod "$destination/aod.json" \
  --slurpfile precipitation "$destination/precipitation.json" \
  --slurpfile swr "$destination/swr.json" \
  '{schema:"cartofreako-cloud-atmosphere-fetch-v1",
    process_start_utc:$process_start,fetched_at_utc:$fetched,
    selection:"latest-not-after",
    observations:[$ptree[0],$aod[0],$precipitation[0],$swr[0]]}' \
  > "$raw_root/cloud-atmosphere-fetch-manifest.json"
find "$destination" -type f ! -name SHA256SUMS -print0 \
  | sort -z | xargs -0 sha256sum > "$destination/SHA256SUMS"
printf 'Cloud-atmosphere raw refresh staged in %s\n' "$destination"
printf 'Manifest: %s\n' "$raw_root/cloud-atmosphere-fetch-manifest.json"
