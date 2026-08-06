#!/usr/bin/env bash

set -euo pipefail

usage()
{
  printf '%s\n' \
    'usage: check-network-infrastructure-sources.sh sites CLOUD_ROOT' \
    '       check-network-infrastructure-sources.sh topology CLOUD_ROOT SUBMARINE_ROOT EXCHANGE_ROOT' >&2
  exit 2
}

fail()
{
  printf 'network-infrastructure source check: %s\n' "$*" >&2
  exit 1
}

check_repo()
{
  local label=$1
  local root=$2
  local expected_commit=$3
  test -d "$root" || fail "$label root does not exist: $root"
  test "$(git -C "$root" rev-parse --is-inside-work-tree 2>/dev/null)" = true \
    || fail "$label root is not a Git checkout: $root"
  local actual_commit
  actual_commit=$(git -C "$root" rev-parse --verify HEAD)
  test "$actual_commit" = "$expected_commit" \
    || fail "$label checkout is $actual_commit; expected $expected_commit"
}

check_tracked_clean()
{
  local label=$1
  local root=$2
  shift 2
  git -C "$root" diff --quiet -- "$@" \
    || fail "$label source paths have modified tracked files"
  git -C "$root" diff --cached --quiet -- "$@" \
    || fail "$label source paths have staged tracked changes"
}

check_digest()
{
  local label=$1
  local root=$2
  local relative=$3
  local expected=$4
  test -f "$root/$relative" || fail "$label file is missing: $root/$relative"
  local actual
  actual=$(sha256sum "$root/$relative")
  actual=${actual%% *}
  test "$actual" = "$expected" \
    || fail "$label digest is $actual; expected $expected"
}

check_cable_details_digest()
{
  local label=$1
  local root=$2
  local routes_relative=$3
  local details_relative=$4
  local expected=$5
  local routes_path=$root/$routes_relative
  local details_path=$root/$details_relative
  test -d "$details_path" \
    || fail "$label detail directory is missing: $details_path"
  local cable_ids
  cable_ids=$(jq -er '[.features[].properties.id] | unique[]' "$routes_path") \
    || fail "$label route index does not contain readable cable ids"
  test -n "$cable_ids" || fail "$label route index contains no cable ids"
  local actual
  actual=$(
    while IFS= read -r cable_id; do
      [[ $cable_id =~ ^[a-z0-9-]+$ ]] \
        || fail "$label route index contains unsafe cable id: $cable_id"
      local detail=$details_path/$cable_id.json
      test -f "$detail" || fail "$label detail file is missing: $detail"
      local digest
      digest=$(sha256sum "$detail")
      digest=${digest%% *}
      printf '%s  %s.json\n' "$digest" "$cable_id"
    done <<< "$cable_ids" | sha256sum
  )
  actual=${actual%% *}
  test "$actual" = "$expected" \
    || fail "$label detail digest is $actual; expected $expected"
}

test $# -ge 2 || usage
mode=$1
cloud_root=$2

cloud_commit=1be1eb04e73320e0337a74a99686cd532f09ad9b
cloud_manifest=data/manifest.20260805.json
cloud_manifest_sha256=35d6d0edd250e4aa7528dfa5b0bff68714dc45c4c2637ea568cadb960b912679

check_repo cloud_cdn_cache "$cloud_root" "$cloud_commit"
check_tracked_clean cloud_cdn_cache "$cloud_root" data schema
check_digest cloud_cdn_cache "$cloud_root" "$cloud_manifest" \
  "$cloud_manifest_sha256"

case "$mode" in
  sites)
    test $# -eq 2 || usage
    ;;
  topology)
    test $# -eq 4 || usage
    submarine_root=$3
    exchange_root=$4
    check_digest submarine-cable "$submarine_root" \
      web/public/api/v3/cable/cable-geo.json \
      d41a3dfb3e4107740a895a7f178dfee43c874f432c59120679e0dad94803f874
    check_digest submarine-cable "$submarine_root" \
      web/public/api/v3/landing-point/landing-point-geo.json \
      d4f3ecac61f34bbc7910c04f74917ac3fae0fb7b40d09e7cc12711c98c7307a0
    check_cable_details_digest submarine-cable "$submarine_root" \
      web/public/api/v3/cable/cable-geo.json \
      web/public/api/v3/cable \
      bd97f641df1a6d62b1f901090751bc626834833056c0e1679f98bc4b3542f757
    check_repo internet-exchange "$exchange_root" \
      2b9c36ad7fad083c0b4db998c4dedadc1ba89027
    check_tracked_clean internet-exchange "$exchange_root" \
      public/api/v2/buildings.geojson
    check_digest internet-exchange "$exchange_root" \
      public/api/v2/buildings.geojson \
      6fdad528d4e0383ed71a0f5495cef4c0576ef3b0e8488fe8affc7978cf97253c
    ;;
  *) usage ;;
esac

printf 'network-infrastructure %s sources: pinned and validated\n' "$mode"
