#!/usr/bin/env bash

# Verify that a particulate profile names and pins the supplied GeoJSON.

set -euo pipefail

if [[ $# -ne 2 ]]; then
  echo "usage: $0 PROFILE GEOJSON" >&2
  exit 2
fi

profile=$1
geojson=$2
for path in "$profile" "$geojson"; do
  if [[ ! -f $path ]]; then
  echo "missing Anthropocene particulate input: $path" >&2
    exit 1
  fi
done

mapfile -t declared_names < <(sed -n \
  's/^[[:space:]]*"geojson"[[:space:]]*:[[:space:]]*"\([^"]*\)".*/\1/p' \
  "$profile")
mapfile -t declared_digests < <(sed -n \
  's/^[[:space:]]*"sha256"[[:space:]]*:[[:space:]]*"\([0-9a-fA-F]*\)".*/\1/p' \
  "$profile")
if ((${#declared_names[@]} != 1 || ${#declared_digests[@]} != 1)); then
  echo "profile must contain exactly one data.geojson and data.sha256: $profile" >&2
  exit 1
fi

declared_name=${declared_names[0]}
declared_digest=${declared_digests[0],,}
if [[ ! $declared_digest =~ ^[0-9a-f]{64}$ ]]; then
  echo "profile data.sha256 is not a lowercase 64-digit SHA-256: $profile" >&2
  exit 1
fi
if [[ $(basename -- "$geojson") != "$declared_name" ]]; then
  echo "profile expects $declared_name, not $(basename -- "$geojson")" >&2
  exit 1
fi

read -r actual_digest _ < <(sha256sum -- "$geojson")
if [[ $actual_digest != "$declared_digest" ]]; then
  echo "Anthropocene particulate GeoJSON checksum mismatch: $geojson" >&2
  echo "expected: $declared_digest" >&2
  echo "actual:   $actual_digest" >&2
  exit 1
fi

printf 'Anthropocene particulate data checksum verified: %s\n' "$geojson"
