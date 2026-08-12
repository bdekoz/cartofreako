#!/usr/bin/env bash
set -euo pipefail

script_directory=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
repository_root=$(CDPATH= cd -- "$script_directory/.." && pwd)
output_directory=${1:-$repository_root/fixtures/projections/equal-earth-v1}

for command_name in node proj sed; do
  command -v "$command_name" >/dev/null 2>&1 || {
    printf 'missing required command: %s\n' "$command_name" >&2
    exit 2
  }
done

work_directory=$(mktemp -d /tmp/cartofreako-equal-earth-oracle.XXXXXX)
cleanup()
{
  rm -rf -- "$work_directory"
}
trap cleanup EXIT

printf '%s\n' \
  '0 0' '12.5 41.9' '-73.9857 40.7484' '171.2 7.1' '15 30' \
  '-120 -60' '90 60' '-45 80' '30 -80' '180 0' '-180 0' \
  '0 90' '0 -90' '-168.5 0' '60 -30' \
  > "$work_directory/coordinates.txt"

proj +proj=eqearth +R=1 +lon_0=0 -f %.17f \
  "$work_directory/coordinates.txt" > "$work_directory/canonical.txt"
proj +proj=eqearth +R=1 +lon_0=11.5 -f %.17f \
  "$work_directory/coordinates.txt" > "$work_directory/africa.txt"
proj_version=$(proj </dev/null 2>&1 | sed -n 's/^Rel\. \([^,]*\),.*$/\1/p')
test -n "$proj_version" || {
  printf '%s\n' 'could not identify PROJ version' >&2
  exit 2
}

PROJ_ORACLE_DIRECTORY="$work_directory" PROJ_ORACLE_VERSION="$proj_version" \
  node "$script_directory/generate-equal-earth-fixtures.mjs" "$output_directory"
