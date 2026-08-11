#!/usr/bin/env bash

# Render the exploration-only Majuro evidence canary from checked compact
# derivatives.  Observation, scenario, and planetary context remain separate.

set -euo pipefail

script_directory=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
repository_root=$(CDPATH= cd -- "$script_directory/.." && pwd)
output_directory=${1:-$repository_root/output/atoll-evidence-canary-v01}
data_directory=$repository_root/assets.static/atoll-evidence
prepared_directory=$data_directory/prepared
coordinate_fixture=$repository_root/fixtures/atoll-evidence/v1/coordinates.json
source_manifest=$repository_root/fixtures/atoll-evidence/v1/manifest.json
context_png=$data_directory/context/water-myriahedral-pacific-700x394.png
output_name=majuro-atoll-evidence-canary.png

for command_name in awk gdaldem identify jq magick sha256sum; do
  command -v "$command_name" >/dev/null 2>&1 || {
    printf 'missing required command: %s\n' "$command_name" >&2
    exit 2
  }
done

for required_path in \
  "$prepared_directory/majuro-tbdem-observation-10m.tif" \
  "$prepared_directory/majuro-marine-inundation-30in-deterministic-10m.tif" \
  "$prepared_directory/majuro-marine-inundation-30in-probability-10m.tif" \
  "$data_directory/topobathy-colors.txt" \
  "$data_directory/inundation-probability-colors.txt" \
  "$data_directory/inundation-deterministic-colors.txt" \
  "$coordinate_fixture" "$source_manifest" "$context_png"; do
  if [[ ! -f $required_path ]]; then
    printf 'missing atoll-canary input: %s\n' "$required_path" >&2
    exit 1
  fi
done

mkdir -p -- "$output_directory"
work_directory=$(mktemp -d /tmp/cartofreako-atoll-render.XXXXXX)
cleanup()
{
  rm -rf -- "$work_directory"
}
trap cleanup EXIT

gdaldem color-relief -q -of PNG -alpha \
  "$prepared_directory/majuro-tbdem-observation-10m.tif" \
  "$data_directory/topobathy-colors.txt" \
  "$work_directory/topobathy.png"
gdaldem color-relief -q -of PNG -alpha \
  "$prepared_directory/majuro-marine-inundation-30in-probability-10m.tif" \
  "$data_directory/inundation-probability-colors.txt" \
  "$work_directory/probability.png"
gdaldem color-relief -q -of PNG -alpha -nearest_color_entry \
  "$prepared_directory/majuro-marine-inundation-30in-deterministic-10m.tif" \
  "$data_directory/inundation-deterministic-colors.txt" \
  "$work_directory/deterministic.png"

# Show the deterministic extent as a boundary over the probabilistic field.
# Filling its complete footprint would wash out the probability evidence.
magick "$work_directory/deterministic.png" -alpha extract \
  -morphology EdgeOut Diamond:8 -threshold 1 \
  "$work_directory/deterministic-edge-mask.png"
magick -size 3973x1272 xc:'#ffffff' \
  "$work_directory/deterministic-edge-mask.png" \
  -alpha off -compose CopyOpacity -composite \
  "$work_directory/deterministic-edge.png"

marker_x=$(jq -er \
  '.projectionTrace.points[] | select(.id == "tbdem-center") | .forward.x' \
  "$coordinate_fixture")
marker_y=$(jq -er \
  '.projectionTrace.points[] | select(.id == "tbdem-center") | .forward.y' \
  "$coordinate_fixture")
context_marker_x=$(awk -v value="$marker_x" 'BEGIN { printf "%.8f", value * 700 / 3840 }')
context_marker_y=$(awk -v value="$marker_y" 'BEGIN { printf "%.8f", value * 394 / 2160 }')
context_marker_ring_x=$(awk -v value="$context_marker_x" 'BEGIN { printf "%.8f", value + 9 }')

magick "$context_png" \
  -fill '#111820' -stroke '#fff45b' -strokewidth 3 \
  -draw "circle $context_marker_x,$context_marker_y $context_marker_ring_x,$context_marker_y" \
  -bordercolor '#35454d' -border 2 \
  "$work_directory/context-panel.png"

magick "$work_directory/topobathy.png" \
  -background '#f4f5f5' -alpha background \
  -resize 820x422! -bordercolor '#35454d' -border 2 \
  "$work_directory/observation-panel.png"

magick -size 3973x1272 xc:'#e7ecee' \
  "$work_directory/probability.png" -compose over -composite \
  "$work_directory/deterministic-edge.png" -compose over -composite \
  -resize 820x263! -bordercolor '#35454d' -border 2 \
  "$work_directory/scenario-panel.png"

font_regular=Atkinson-Hyperlegible-Next-Regular
font_bold=Atkinson-Hyperlegible-Next-Bold
background='#f4f5f5'
ink='#151b1f'
muted='#526169'

magick -size 2560x1440 xc:"$background" \
  -font "$font_bold" -fill "$ink" -pointsize 68 \
  -gravity northwest -annotate +70+42 'Majuro Atoll — Stage 15 evidence canary' \
  -font "$font_regular" -fill "$muted" -pointsize 30 \
  -annotate +72+126 'Exploration only · source-governed observation + separately labeled scenario · not navigation or engineering' \
  "$work_directory/context-panel.png" -geometry +70+270 -composite \
  "$work_directory/observation-panel.png" -geometry +820+270 -composite \
  "$work_directory/scenario-panel.png" -geometry +1690+270 -composite \
  -font "$font_bold" -fill '#155b78' -pointsize 25 \
  -annotate +70+220 'PLANETARY CONTEXT' \
  -fill '#236346' -annotate +820+220 'OBSERVATION / DERIVED SURFACE' \
  -fill '#713b88' -annotate +1690+220 'SCENARIO / NOT OBSERVATION' \
  -font "$font_bold" -fill "$ink" -pointsize 32 \
  -annotate +70+690 'Myriahedral Pacific carrier' \
  -annotate +820+730 'USGS 1 m Majuro TBDEM' \
  -annotate +1690+590 'USGS marine inundation · 30 in' \
  -font "$font_regular" -fill "$muted" -pointsize 25 \
  -annotate +70+742 'Yellow ring: TBDEM metadata-envelope center\nForward + face-qualified reverse: native cell 1738\nCarrier is context; it is not the analytical grid.' \
  -annotate +820+782 '1944–2016 multi-source composite · LMSL heights\nITRF2008 / UTM zone 59N · checked 10 m derivative\nLand RMSE 0.197 m; bathymetry RMSE varies by source.\nThe 1 m source remains authoritative and local-only.' \
  -annotate +1690+642 '0.762 m above Mean Higher High Water\nColor: Monte Carlo inundation probability, 0–1\nWhite outline: deterministic static-water extent\nCumulative vertical RMSE 0.192 m; 30 in supports 95% confidence.\nScenario source surface: 2016 · analysis: 2018 · release: 2019.' \
  -fill '#e3e7e8' -stroke '#aeb8bc' -strokewidth 2 \
  -draw 'roundrectangle 70,1040 2490,1355 18,18' \
  -stroke none -font "$font_bold" -fill '#762d36' -pointsize 28 \
  -annotate +100+1070 'UNAVAILABLE / NOT ASSERTED' \
  -font "$font_regular" -fill "$ink" -pointsize 24 \
  -annotate +100+1120 'Freshwater spatial field · authoritative infrastructure · current independent shoreline · reviewed benthic reef geometry' \
  -annotate +100+1162 'Ocean heat is not rendered · Marshall Islands community/regional review is not established · no promotion decision exists' \
  -font "$font_bold" -fill '#713b88' -pointsize 25 \
  -annotate +100+1220 'LIFECYCLE: EXPLORATION ONLY' \
  -font "$font_regular" -fill "$muted" -pointsize 23 \
  -annotate +100+1262 'The observation and scenario are intentionally separate. This PNG does not enter make all, ordinary make check, GitHub release, or UCB AAO/S3 publication.' \
  -set comment 'Cartofreako Stage 15 Majuro atoll evidence canary: public USGS TBDEM observation-derived surface and separately labeled 30-inch modeled inundation scenario; exploration only.' \
  -set Software 'Cartofreako atoll evidence canary v01' \
  -depth 8 \
  -define png:exclude-chunks=date,time \
  "$work_directory/$output_name"

install -m 0644 -- "$work_directory/$output_name" \
  "$output_directory/$output_name"
identify "$output_directory/$output_name"
sha256sum "$output_directory/$output_name"
