#!/usr/bin/env bash

set -euo pipefail

script_directory=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
repository_root=$(CDPATH= cd -- "$script_directory/.." && pwd)
output_directory=${1:-$repository_root/output/anthropocene-water-debris-v01}

for command_name in inkscape magick montage install mktemp; do
  command -v "$command_name" >/dev/null 2>&1 || {
    printf 'missing required command: %s\n' "$command_name" >&2
    exit 2
  }
done

work_directory=$(mktemp -d /tmp/cartofreako-water-debris.XXXXXX)
cleanup()
{
  rm -rf -- "$work_directory"
}
trap cleanup EXIT
mkdir -p -- "$work_directory/xdg" "$work_directory/cache" "$output_directory"
export XDG_CONFIG_HOME=$work_directory/xdg
export XDG_CACHE_HOME=$work_directory/cache

projections=(cahill-keyes authagraph dymaxion myriahedral star-x voronoi)
suffixes=(
  ck-44-22
  authagraph-44-19.052559
  dymaxion-44-20.78461
  myriahedral-44-24.75
  star-x-34-44
  voronoi-44-22.916667
)
labels=(Cahill-Keyes AuthaGraph Dymaxion Myriahedral Star-X Voronoi)
panels=()

for year in 2025 2026; do
  for index in "${!projections[@]}"; do
    projection=${projections[$index]}
    suffix=${suffixes[$index]}
    source=$repository_root/assets.generated/$projection/svg/anthropocene-water-debris-$year-$suffix.svg
    test -s "$source" || {
      printf 'missing water-debris SVG: %s\n' "$source" >&2
      exit 1
    }
    raw=$work_directory/raw-$year-$projection.png
    panel=$work_directory/panel-$year-$projection.png
    inkscape --export-type=png --export-width=900 \
      --export-background='#f4f5f5' --export-background-opacity=255 \
      --export-filename="$raw" "$source" >/dev/null
    magick "$raw" -resize '900x620>' -gravity center \
      -background '#f4f5f5' -extent 920x640 -gravity north -splice 0x66 \
      -font DejaVu-Sans -fill '#15252e' -pointsize 30 \
      -annotate +0+17 "$year · ${labels[$index]}" "$panel"
    panels+=("$panel")
  done
done

montage "${panels[@]}" -tile 3x4 -geometry +18+18 \
  -background '#f4f5f5' "$work_directory/grid.png"
magick "$work_directory/grid.png" -gravity north -splice 0x160 \
  -font DejaVu-Sans -fill '#15252e' -pointsize 54 \
  -annotate +0+30 'Anthropocene water debris · 2025 complete / 2026 partial' \
  -pointsize 28 -annotate +0+98 \
  'Exploration only · five observed 2018 depth stations · other source families remain context-only' \
  -set comment 'Cartofreako Stage 15 water-debris experiment; no garbage-patch polygon or invented depth field' \
  -define png:exclude-chunks=date,time "$work_directory/contact-sheet.png"
install -m 0644 -- "$work_directory/contact-sheet.png" \
  "$output_directory/contact-sheet.png"
printf 'Rendered %s\n' "$output_directory/contact-sheet.png"
