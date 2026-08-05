#!/bin/sh

# Safely stage one local cumulative swarm GeoJSON file for
# generate-network-swarm.

set -eu
set -f

if [ "$#" -ne 2 ]; then
  printf '%s\n' \
    'usage: prepare-network-swarm-data.sh SOURCE DESTINATION.geojson' >&2
  exit 2
fi

source_path=$1
destination=$2
maximum_bytes=67108864

if [ ! -f "$source_path" ] || [ ! -r "$source_path" ]; then
  printf 'network-swarm source is not a readable regular file: %s\n' \
    "$source_path" >&2
  exit 1
fi

destination_directory=$(dirname -- "$destination")
install -d -- "$destination_directory"
temporary_directory=$(mktemp -d \
  "$destination_directory/.network-swarm-prepare.XXXXXX")
temporary_geojson=$temporary_directory/input.geojson
temporary_members=$temporary_directory/members

cleanup()
{
  rm -rf -- "$temporary_directory"
}
trap cleanup 0
trap 'exit 129' HUP
trap 'exit 130' INT
trap 'exit 143' TERM

case "$source_path" in
  *.zip)
    unzip -tqq -- "$source_path"
    unzip -Z1 -- "$source_path" > "$temporary_members"
    member_count=$(wc -l < "$temporary_members")
    if [ "$member_count" -ne 1 ]; then
      printf 'network-swarm ZIP must contain exactly one member; found %s\n' \
        "$member_count" >&2
      exit 1
    fi
    member=$(sed -n '1p' "$temporary_members")
    case "$member" in
      ''|*/*|*\\*|*..*|*[!A-Za-z0-9._-]*)
        printf 'network-swarm ZIP has an unsafe member name: %s\n' \
          "$member" >&2
        exit 1
        ;;
      *.geojson|*.json) ;;
      *)
        printf 'network-swarm ZIP member is not JSON or GeoJSON: %s\n' \
          "$member" >&2
        exit 1
        ;;
    esac
    unzip -p -- "$source_path" "$member" > "$temporary_geojson"
    ;;
  *.geojson|*.json)
    install -m 0644 -- "$source_path" "$temporary_geojson"
    ;;
  *)
    printf 'network-swarm source must end in .zip, .geojson, or .json: %s\n' \
      "$source_path" >&2
    exit 1
    ;;
esac

actual_bytes=$(wc -c < "$temporary_geojson")
if [ "$actual_bytes" -eq 0 ] || [ "$actual_bytes" -gt "$maximum_bytes" ]; then
  printf 'prepared network-swarm GeoJSON size %s is outside 1..%s bytes\n' \
    "$actual_bytes" "$maximum_bytes" >&2
  exit 1
fi

# Preserve the destination timestamp when its bytes are already current.
if [ -f "$destination" ] && cmp -s -- "$temporary_geojson" "$destination"; then
  printf 'network-swarm GeoJSON already prepared: %s (%s bytes)\n' \
    "$destination" "$actual_bytes"
else
  install -m 0644 -- "$temporary_geojson" "$temporary_directory/output"
  mv -f -- "$temporary_directory/output" "$destination"
  printf 'prepared network-swarm GeoJSON: %s (%s bytes)\n' \
    "$destination" "$actual_bytes"
fi
