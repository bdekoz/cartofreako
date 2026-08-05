#!/usr/bin/env bash

set -euo pipefail

if [[ $# -gt 1 ]]; then
  echo "usage: $0 [cloud-atmosphere-data-directory]" >&2
  exit 2
fi

data_dir=${1:-assets.static/cloud-atmosphere}
prepared_dir="$data_dir/.prepared"
manifest="$prepared_dir/cloud-atmosphere-latest.manifest.json"
if [[ ! -f $manifest ]]; then
  echo "missing prepared cloud-atmosphere manifest: $manifest" >&2
  exit 1
fi
snapshot=$(jq -er '.snapshot' "$manifest")
expected=$(jq -er '.sha256' "$manifest")
path="$prepared_dir/$snapshot"
if [[ ! -f $path ]]; then
  echo "missing prepared cloud-atmosphere snapshot: $path" >&2
  exit 1
fi
actual=$(sha256sum "$path" | sed 's/[[:space:]].*//')
if [[ $actual != "$expected" ]]; then
  echo "cloud-atmosphere prepared checksum mismatch" >&2
  exit 1
fi
jq -e '
  .type == "FeatureCollection" and
  .metadata.schema == "cartofreako-cloud-atmosphere-snapshot-v1" and
  .metadata.fixture == false and
  .metadata.missing_semantics == "unobserved-not-zero" and
  (.metadata.observations | length == 4) and
  (.features | length > 0)
' "$path" >/dev/null
printf 'Verified cloud-atmosphere snapshot: %s\n' "$path"
