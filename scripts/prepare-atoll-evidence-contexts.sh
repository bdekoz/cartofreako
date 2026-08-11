#!/usr/bin/env bash

# Freeze compact projection-specific planetary carrier images for the
# exploration-only Majuro atoll-evidence pass.  This maintainer operation
# consumes already-generated authoritative water PNGs and never fetches data.

set -euo pipefail

script_directory=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
repository_root=$(CDPATH= cd -- "$script_directory/.." && pwd)
output_directory=${1:-$repository_root/assets.static/atoll-evidence/context}

for command_name in identify magick sha256sum; do
  command -v "$command_name" >/dev/null 2>&1 || {
    printf 'missing required command: %s\n' "$command_name" >&2
    exit 2
  }
done

sources=(
  'cahill-keyes/png/water-ck-44-22.png'
  'authagraph/png/water-authagraph-44-19.052559.png'
  'dymaxion/png/water-dymaxion-44-20.78461.png'
  'myriahedral/png/water-myriahedral-pacific-44-24.75.png'
  'star-x/png/water-star-x-34-44.png'
  'voronoi/png/water-voronoi-44-22.916667.png'
)
source_hashes=(
  '80f558cce731edfe74dcf41a23c488270c2c319940f8a6e3ae84f88780fcb9b5'
  '8f89f1a28fc85b16d394f3d216c7816d0cb8f34624bf85def887c64096490768'
  'ccc4bb1b8570a066c71cd6aee8e368023b8e8759a3d62cab95a2cd71b6a96ee8'
  'c7a5d360aed56c212854cb4132112f83fdebf4fcb691ecd63e00efb27402c81b'
  '79091bba381fb1faff7bccd0bd692709483648829b45d4b73ba087fdc2c1250b'
  '4aa4d29790ac8689443217053b26c2523e78575306c2df30552a8edac5a28d4e'
)
outputs=(
  'water-cahill-keyes-context.png'
  'water-authagraph-context.png'
  'water-dymaxion-context.png'
  'water-myriahedral-pacific-context.png'
  'water-star-x-context.png'
  'water-voronoi-context.png'
)
expected_dimensions=(
  '1200x600'
  '1200x520'
  '1200x567'
  '1200x675'
  '927x1200'
  '1200x625'
)

work_directory=$(mktemp -d /tmp/cartofreako-atoll-context.XXXXXX)
cleanup()
{
  rm -rf -- "$work_directory"
}
trap cleanup EXIT

mkdir -p -- "$output_directory"
for index in "${!sources[@]}"; do
  source_path=$repository_root/assets.generated/${sources[$index]}
  output_name=${outputs[$index]}
  expected_hash=${source_hashes[$index]}
  expected_dimension=${expected_dimensions[$index]}
  if [[ ! -f $source_path ]]; then
    printf 'missing authoritative water PNG: %s\n' "$source_path" >&2
    printf '%s\n' 'generate the corresponding standard water artifact first' >&2
    exit 1
  fi
  read -r actual_hash _ < <(sha256sum -- "$source_path")
  if [[ $actual_hash != "$expected_hash" ]]; then
    printf 'water parent changed for %s\nexpected %s\nactual   %s\n' \
      "$source_path" "$expected_hash" "$actual_hash" >&2
    exit 1
  fi
  staged=$work_directory/$output_name
  magick "$source_path" -resize '1200x1200>' -depth 8 -strip \
    -define png:exclude-chunks=date,time "$staged"
  actual_dimension=$(identify -format '%wx%h' "$staged")
  if [[ $actual_dimension != "$expected_dimension" ]]; then
    printf 'context dimension mismatch for %s: expected %s, got %s\n' \
      "$output_name" "$expected_dimension" "$actual_dimension" >&2
    exit 1
  fi
  install -m 0644 -- "$staged" "$output_directory/$output_name"
done

(
  cd "$output_directory"
  sha256sum -- "${outputs[@]}" > FULL_PASS_SHA256SUMS
)

printf 'Prepared six checked Majuro planetary contexts in %s\n' \
  "$output_directory"
