#!/usr/bin/env bash
set -euo pipefail

script_directory=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
repository_root=$(CDPATH= cd -- "$script_directory/.." && pwd)
output_directory=${1:-$repository_root/output/equal-earth-positioning-speculations-v01}
source_countries=$repository_root/assets.static/resources/countries-110m.geojson

expected_outputs=(
  01-mercator-equal-earth-full-world.png
  02-equal-earth-centering-and-tissot.png
  03-africa-europe-source-window.png
  04-cartofreako-full-carrier-alternatives.png
  05-projection-and-slice-strategies.png
)

for command_name in identify inkscape magick node ogr2ogr; do
  command -v "$command_name" >/dev/null 2>&1 || {
    printf 'missing required command: %s\n' "$command_name" >&2
    exit 2
  }
done
test -f "$repository_root/src.wasm/cartofreako-projections.wasm" || {
  printf '%s\n' 'projection WebAssembly is missing; run make wasm-projections' >&2
  exit 2
}
test -f "$source_countries" || {
  printf 'missing checked country geometry: %s\n' "$source_countries" >&2
  exit 2
}

mkdir -p -- "$output_directory"
while IFS= read -r existing; do
  existing_name=${existing##*/}
  allowed=false
  for expected in "${expected_outputs[@]}"; do
    if [[ $existing_name == "$expected" ]]; then
      allowed=true
      break
    fi
  done
  if [[ $allowed == false ]]; then
    printf 'refusing an output directory containing an unexpected entry: %s\n' \
      "$existing" >&2
    exit 2
  fi
done < <(find "$output_directory" -mindepth 1 -maxdepth 1 -print | sort)

work_directory=$(mktemp -d /tmp/cartofreako-equal-earth-render.XXXXXX)
cleanup()
{
  rm -rf -- "$work_directory"
}
trap cleanup EXIT
mkdir -p -- "$work_directory/xdg" "$work_directory/cache"
export XDG_CONFIG_HOME=$work_directory/xdg
export XDG_CACHE_HOME=$work_directory/cache

ogr2ogr -f GeoJSON "$work_directory/africa-europe.geojson" \
  "$source_countries" -clipsrc -25 -40 60 75
node "$script_directory/render-equal-earth-positioning-v01.mjs" \
  "$repository_root" "$work_directory"

for expected in "${expected_outputs[@]}"; do
  stem=${expected%.png}
  source_svg=$work_directory/$stem.svg
  raw_png=$work_directory/$stem.raw.png
  staged_png=$work_directory/$expected
  test -f "$source_svg" || {
    printf 'renderer omitted expected SVG: %s\n' "$source_svg" >&2
    exit 2
  }
  inkscape --export-type=png --export-width=2560 --export-height=1440 \
    --export-background='#f2f2ee' --export-background-opacity=255 \
    --export-filename="$raw_png" "$source_svg" >/dev/null
  magick "$raw_png" \
    -set comment 'Cartofreako Stage 16J Equal Earth positioning speculation; exploration only' \
    -set Software 'Cartofreako Stage 16J renderer' \
    -define png:exclude-chunks=date,time "$staged_png"
  dimensions=$(identify -format '%wx%h' "$staged_png")
  test "$dimensions" = 2560x1440 || {
    printf 'unexpected output dimensions for %s: %s\n' "$expected" "$dimensions" >&2
    exit 2
  }
  install -m 0644 -- "$staged_png" "$output_directory/$expected"
done

printf 'Rendered Stage 16J exploration: %s PNGs at %s\n' \
  "${#expected_outputs[@]}" "$output_directory"
