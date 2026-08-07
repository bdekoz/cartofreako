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
ptree_resolver=$(dirname "$0")/resolve-jaxa-ptree.sh
for path in "$profile" "$resolver" "$ptree_resolver"; do
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

ptree_cacert=${PTREE_CACERT:-}
if [[ -z $ptree_cacert ]]; then
  data_home=${XDG_DATA_HOME:-${HOME:?HOME is required}/.local/share}
  installed_cacert=$data_home/cartofreako/certs/secom-tls-rsa-root-ca-2024.pem
  if [[ -r $installed_cacert ]]; then
    ptree_cacert=$installed_cacert
  fi
fi
if [[ -n $ptree_cacert ]]; then
  [[ $ptree_cacert = /* ]] \
    || { echo 'PTREE_CACERT must be an absolute path' >&2; exit 1; }
  [[ -r $ptree_cacert ]] \
    || { echo "P-Tree CA certificate is not readable: $ptree_cacert" >&2; exit 1; }
fi

if [[ -n ${PTREE_BASE_URL:-} ]]; then
  ptree_product="${PTREE_BASE_URL%/}/pub/himawari/L2/CLP/010"
else
  ptree_product=$(profile_source_field jaxa-ptree-cloud url)
  ptree_product=${ptree_product%/}
fi
PTREE_NETRC="${PTREE_NETRC:-${HOME:?HOME is required}/.netrc}" \
PTREE_CACERT="$ptree_cacert" \
  "$ptree_resolver" "$ptree_product" "$process_start" \
  "$temporary_dir" "$temporary_dir/ptree.json"

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

fetched_at=$(date -u +%Y-%m-%dT%H:%M:%SZ)
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
