#!/usr/bin/env bash
set -euo pipefail

script_directory=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
repository_root=$(CDPATH= cd -- "$script_directory/.." && pwd)
output_directory=${1:-$repository_root/output/marshall-islands-speculations-v01}
natural_earth_directory=$repository_root/assets.static/natural-earth/10m-physical-vectors
font_regular=Atkinson-Hyperlegible-Next-Regular
font_bold=Atkinson-Hyperlegible-Next-Bold
background='#f2f2ee'
ink='#151b1f'
marker='#fff45b'

expected_outputs=(
  01-dymaxion-full-water-rmi-locator.png
  02-cahill-keyes-octant-1-five-contexts.png
  03-star-x-vertical-now-four-contexts.png
  04-rmi-regional-ck-dymaxion-preclip.png
  05-majuro-local-azimuthal-equidistant.png
)

for command_name in identify inkscape jq magick montage node ogr2ogr; do
  command -v "$command_name" >/dev/null 2>&1 || {
    printf 'missing required command: %s\n' "$command_name" >&2
    exit 2
  }
done

test -f "$natural_earth_directory/ne_10m_land.shp" || {
  printf '%s\n' 'Natural Earth 10m vectors are missing; run make fetch-natural-earth-10m.' >&2
  exit 2
}
test -f "$repository_root/src.wasm/cartofreako-projections.wasm" || {
  printf '%s\n' 'The all-projection WebAssembly runtime is missing; run make wasm-projections.' >&2
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
    printf 'refusing an output directory containing an unexpected entry: %s\n' "$existing" >&2
    exit 2
  fi
done < <(find "$output_directory" -mindepth 1 -maxdepth 1 -print | sort)

work_directory=$(mktemp -d /tmp/cartofreako-marshall-v01.XXXXXX)
cleanup()
{
  rm -rf -- "$work_directory"
}
trap cleanup EXIT
mkdir -p -- "$work_directory/sources" "$work_directory/xdg" "$work_directory/cache"
export XDG_CONFIG_HOME=$work_directory/xdg
export XDG_CACHE_HOME=$work_directory/cache

resolved_path=
resolve_png()
{
  local projection=$1
  local filename=$2
  local local_path=$repository_root/assets.generated/$projection/png/$filename
  if [[ -f $local_path ]]; then
    resolved_path=$local_path
    return
  fi
  printf 'missing local generated PNG: %s\n' "$local_path" >&2
  printf '%s\n' 'run make render-marshall-islands-speculations-v01; it builds standard sources and fetches the JAXA P-Tree vendor data for the cloud-atmosphere plates first' >&2
  exit 2
}

resolve_svg()
{
  local projection=$1
  local filename=$2
  local local_path=$repository_root/assets.generated/$projection/svg/$filename
  if [[ -f $local_path ]]; then
    resolved_path=$local_path
    return
  fi
  printf 'missing local generated SVG: %s\n' "$local_path" >&2
  printf '%s\n' 'run make render-marshall-islands-speculations-v01; it builds standard sources and fetches the JAXA P-Tree vendor data for the cloud-atmosphere plates first' >&2
  exit 2
}

add_landscape_header()
{
  local input=$1
  local output=$2
  local title=$3
  local subtitle=$4
  magick "$input" -resize '2440x1220>' -gravity center \
    -background "$background" -extent 2560x1260 \
    -gravity north -splice 0x180 \
    -font "$font_bold" -fill "$ink" -pointsize 62 \
    -annotate +0+28 "$title" \
    -font "$font_regular" -pointsize 31 \
    -annotate +0+106 "$subtitle" "$output"
}

add_portrait_header()
{
  local input=$1
  local output=$2
  local title=$3
  local subtitle=$4
  magick "$input" -resize '1340x2260>' -gravity center \
    -background "$background" -extent 1440x2350 \
    -gravity north -splice 0x210 \
    -font "$font_bold" -fill "$ink" -pointsize 58 \
    -annotate +0+30 "$title" \
    -font "$font_regular" -pointsize 28 \
    -annotate +0+114 "$subtitle" "$output"
}

publish_png()
{
  local input=$1
  local filename=$2
  local description=$3
  local staged=$work_directory/published-$filename
  magick "$input" \
    -set comment "$description" \
    -set Software 'Cartofreako Marshall Islands speculations v01' \
    -define png:exclude-chunks=date,time "$staged"
  install -m 0644 -- "$staged" "$output_directory/$filename"
}

projection_source=$natural_earth_directory
ogr2ogr -f GeoJSON "$work_directory/region-land.geojson" \
  "$projection_source/ne_10m_land.shp" -clipsrc 160 4 176 15
ogr2ogr -f GeoJSON "$work_directory/region-islands.geojson" \
  "$projection_source/ne_10m_minor_islands.shp" -clipsrc 160 4 176 15
ogr2ogr -f GeoJSON "$work_directory/region-reefs.geojson" \
  "$projection_source/ne_10m_reefs.shp" -clipsrc 160 4 176 15

local_crs='+proj=aeqd +lat_0=7.0897 +lon_0=171.3803 +datum=WGS84 +units=m +no_defs +type=crs'
ogr2ogr -f GeoJSON "$work_directory/local-land.geojson" \
  "$projection_source/ne_10m_land.shp" -clipsrc 166 2 176 12 -t_srs "$local_crs"
ogr2ogr -f GeoJSON "$work_directory/local-islands.geojson" \
  "$projection_source/ne_10m_minor_islands.shp" -clipsrc 166 2 176 12 -t_srs "$local_crs"
ogr2ogr -f GeoJSON "$work_directory/local-reefs.geojson" \
  "$projection_source/ne_10m_reefs.shp" -clipsrc 166 2 176 12 -t_srs "$local_crs"

node "$script_directory/render-marshall-islands-speculations-v01.mjs" \
  "$work_directory"

dymaxion_x=$(jq -r '.points.dymaxion.x' "$work_directory/coordinates.json")
dymaxion_y=$(jq -r '.points.dymaxion.y' "$work_directory/coordinates.json")
dymaxion_ring_x=$((dymaxion_x + 48))
dymaxion_label_x=$((dymaxion_x + 90))
dymaxion_label_y=$((dymaxion_y - 125))
resolve_png dymaxion water-dymaxion-44-20.78461.png
dymaxion_water=$resolved_path
magick "$dymaxion_water" \
  -stroke "$marker" -strokewidth 14 -fill '#111820' \
  -draw "circle $dymaxion_x,$dymaxion_y $dymaxion_ring_x,$dymaxion_y" \
  -draw "line $dymaxion_x,$dymaxion_y $dymaxion_label_x,$dymaxion_label_y" \
  -font "$font_bold" -pointsize 64 -fill '#111820' -stroke "$marker" \
  -strokewidth 2 -gravity northwest \
  -annotate +$dymaxion_label_x+$dymaxion_label_y 'RMI · 171.2°E, 7.1°N' \
  "$work_directory/iteration-01-marked.png"
add_landscape_header \
  "$work_directory/iteration-01-marked.png" \
  "$work_directory/iteration-01.png" \
  '01 · Planetary ocean relation' \
  'Dymaxion full carrier · released v13 water plate · speculative RMI locator'
publish_png "$work_directory/iteration-01.png" "${expected_outputs[0]}" \
  'Iteration 1: full Dymaxion v13 water plate with a runtime-projected RMI context locator; speculative research framing, not navigation.'

make -C "$repository_root" "$repository_root/src.generate/generate-8-slice" >/dev/null
octant_x=$(jq -r '.points["cahill-keyes"].octant1.export.x' "$work_directory/coordinates.json")
octant_y=$(jq -r '.points["cahill-keyes"].octant1.export.y' "$work_directory/coordinates.json")
octant_ring_x=$((octant_x + 18))
theme_keys=(water reefs atmosphere fiber human)
theme_files=(
  water-ck-44-22.svg
  resources-fauna-coral-reef-threat-2011-ck-44-22.svg
  cloud-atmosphere-ck-44-22.svg
  fiber-synthesized-ck-44-22.svg
  resources-human-population-under-30-2024-ck-44-22.svg
)
theme_labels=('Water' 'Reef threat · 2011' 'P-Tree atmosphere' 'Fiber union' 'Population under 30 · 2024')
octant_panels=()
for index in "${!theme_keys[@]}"; do
  key=${theme_keys[$index]}
  resolve_svg cahill-keyes "${theme_files[$index]}"
  source_svg=$resolved_path
  theme_directory=$work_directory/octant-$key
  mkdir -p -- "$theme_directory"
  "$repository_root/src.generate/generate-8-slice" \
    "$source_svg" "$theme_directory" >/dev/null
  inkscape --export-type=png --export-width=900 \
    --export-background=white --export-background-opacity=255 \
    --export-filename="$theme_directory/raw.png" \
    "$theme_directory/earth-ck-8-slice-1.svg" >/dev/null
  magick "$theme_directory/raw.png" \
    -stroke "$marker" -strokewidth 8 -fill '#111820' \
    -draw "circle $octant_x,$octant_y $octant_ring_x,$octant_y" \
    -resize 455x \
    -gravity north -background "$background" -splice 0x64 \
    -font "$font_bold" -fill "$ink" -stroke none -pointsize 28 \
    -annotate +0+17 "${theme_labels[$index]}" \
    "$theme_directory/panel.png"
  octant_panels+=("$theme_directory/panel.png")
done
montage "${octant_panels[@]}" -tile 5x1 -geometry +14+14 \
  -background "$background" "$work_directory/iteration-02-montage.png"
add_landscape_header \
  "$work_directory/iteration-02-montage.png" \
  "$work_directory/iteration-02.png" \
  '02 · Focused comparative atlas panel' \
  'Cahill–Keyes ck-octant-1 native-cell mask · identical scale · yellow RMI context point'
publish_png "$work_directory/iteration-02.png" "${expected_outputs[1]}" \
  'Iteration 2: five released v13 themes rendered through the exact Cahill-Keyes ck-octant-1 native-cell mask at a shared scale.'

star_x=$(jq -r '.points["star-x"].x' "$work_directory/coordinates.json")
star_y=$(jq -r '.points["star-x"].y' "$work_directory/coordinates.json")
star_ring_x=$((star_x + 42))
star_keys=(atmosphere temperature fiber water)
star_files=(
  cloud-atmosphere-star-x-34-44.png
  anthropocene-temperature-2026-star-x-34-44.png
  fiber-synthesized-star-x-34-44.png
  water-star-x-34-44.png
)
star_labels=('P-Tree atmosphere' 'Temperature · 2026 partial year' 'Fiber union' 'Water')
star_panels=()
for index in "${!star_keys[@]}"; do
  key=${star_keys[$index]}
  resolve_png star-x "${star_files[$index]}"
  source_png=$resolved_path
  panel=$work_directory/star-$key.png
  magick "$source_png" \
    -stroke "$marker" -strokewidth 12 -fill '#111820' \
    -draw "circle $star_x,$star_y $star_ring_x,$star_y" \
    -resize 620x \
    -gravity north -background "$background" -splice 0x76 \
    -font "$font_bold" -fill "$ink" -stroke none -pointsize 30 \
    -annotate +0+20 "${star_labels[$index]}" "$panel"
  star_panels+=("$panel")
done
montage "${star_panels[@]}" -tile 2x2 -geometry +20+20 \
  -background "$background" "$work_directory/iteration-03-montage.png"
add_portrait_header \
  "$work_directory/iteration-03-montage.png" \
  "$work_directory/iteration-03.png" \
  '03 · Vertical “now” comparison' \
  'Star-X full carrier · four contemporaneous relations · yellow RMI context point'
publish_png "$work_directory/iteration-03.png" "${expected_outputs[2]}" \
  'Iteration 3: four full Star-X v13 context plates with a runtime-projected RMI locator; interpretive comparison only.'

regional_panels=()
for projection in cahill-keyes dymaxion; do
  inkscape --export-type=png --export-width=1500 \
    --export-background=white --export-background-opacity=255 \
    --export-filename="$work_directory/regional-$projection.png" \
    "$work_directory/regional-$projection.svg" >/dev/null
  projection_label=$projection
  [[ $projection == cahill-keyes ]] && projection_label='Cahill–Keyes'
  [[ $projection == dymaxion ]] && projection_label='Dymaxion'
  magick "$work_directory/regional-$projection.png" \
    -resize '1160x1000>' -gravity center -background "$background" \
    -extent 1180x1040 -gravity north -splice 0x70 \
    -font "$font_bold" -fill "$ink" -pointsize 32 \
    -annotate +0+18 "$projection_label" \
    "$work_directory/regional-$projection-panel.png"
  regional_panels+=("$work_directory/regional-$projection-panel.png")
done
montage "${regional_panels[@]}" -tile 2x1 -geometry +24+24 \
  -background "$background" "$work_directory/iteration-04-montage.png"
add_landscape_header \
  "$work_directory/iteration-04-montage.png" \
  "$work_directory/iteration-04.png" \
  '04 · RMI regional source preclip' \
  'WGS 84 bounds 160°E–176°E, 4°N–15°N · Natural Earth 1:10m context · same source window'
publish_png "$work_directory/iteration-04.png" "${expected_outputs[3]}" \
  'Iteration 4: one WGS 84 geographic source preclip projected through Cahill-Keyes and Dymaxion; Natural Earth context only.'

inkscape --export-type=png --export-width=2100 \
  --export-background=white --export-background-opacity=255 \
  --export-filename="$work_directory/local-majuro-aeqd.png" \
  "$work_directory/local-majuro-aeqd.svg" >/dev/null
add_landscape_header \
  "$work_directory/local-majuro-aeqd.png" \
  "$work_directory/iteration-05.png" \
  '05 · Local analytical-projection hypothesis' \
  'Majuro-centered WGS 84 azimuthal equidistant · 100/250/500 km rings · Natural Earth 1:10m context only'
publish_png "$work_directory/iteration-05.png" "${expected_outputs[4]}" \
  'Iteration 5: Majuro-centered azimuthal equidistant context with radial distance rings; not hazard, navigation, cadastral, or engineering evidence.'

for filename in "${expected_outputs[@]}"; do
  identify "$output_directory/$filename"
done
printf 'Marshall Islands speculation render complete: %s\n' "$output_directory"
