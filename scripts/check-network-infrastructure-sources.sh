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

test $# -ge 2 || usage
mode=$1
cloud_root=$2

cloud_commit=80bc389786c7ea6bda563700685d117bbf3d5017
cloud_manifest=data/manifest.20260805.json
cloud_manifest_sha256=514187d06086d3f3e2c276a7d42f6e1c11e13fdf68f14b90972174206c7f3f67

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
    check_repo submarine-cable "$submarine_root" \
      0d684b2aedeae0f7473280270f3f71fa0983f0b3
    check_tracked_clean submarine-cable "$submarine_root" \
      web/public/api/v3/cable web/public/api/v3/landing-point/landing-point-geo.json
    check_digest submarine-cable "$submarine_root" \
      web/public/api/v3/cable/cable-geo.json \
      63134a87d7482cb51b5f22d586384e88fbd9ec4315dba9c6899a5e1ff76637f5
    check_digest submarine-cable "$submarine_root" \
      web/public/api/v3/landing-point/landing-point-geo.json \
      2a350a8be354886949d1a146de6d973d8aa433e085c245b867c130bd0398c69e
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

printf 'network-infrastructure %s sources: pinned and clean\n' "$mode"
