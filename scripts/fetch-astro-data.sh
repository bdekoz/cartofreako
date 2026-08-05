#!/usr/bin/env bash

set -euo pipefail

if [[ $# -gt 1 ]]; then
  echo "usage: $0 [output-directory]" >&2
  exit 2
fi

output_dir=${1:-assets.static/astronomy}
mkdir -p "$output_dir"
temporary_dir=$(mktemp -d)
trap 'rm -rf "$temporary_dir"' EXIT

gaia_query='SELECT TOP 500 source_id,ra,dec,parallax,pmra,pmdec,radial_velocity,phot_g_mean_mag,bp_rp FROM gaiadr3.gaia_source WHERE phot_g_mean_mag < 5.5 ORDER BY phot_g_mean_mag'
curl -sS --fail --get 'https://gea.esac.esa.int/tap-server/tap/sync' \
  --data-urlencode 'REQUEST=doQuery' \
  --data-urlencode 'LANG=ADQL' \
  --data-urlencode 'FORMAT=csv' \
  --data-urlencode "QUERY=$gaia_query" \
  -o "$temporary_dir/gaia-dr3-bright.csv"

exoplanet_query='SELECT TOP 250 pl_name,hostname,ra,dec,sy_dist,sy_vmag,disc_year,discoverymethod FROM pscomppars WHERE ra IS NOT NULL AND dec IS NOT NULL ORDER BY sy_dist'
curl -sS --fail --get 'https://exoplanetarchive.ipac.caltech.edu/TAP/sync' \
  --data-urlencode "query=$exoplanet_query" \
  --data-urlencode 'format=csv' \
  -o "$temporary_dir/nasa-exoplanet-nearby.csv"

small_body_names=(
  'ceres|1 Ceres'
  'vesta|4 Vesta'
  'eros|433 Eros'
  'apophis|99942 Apophis'
  'halley|1P'
  'encke|2P'
  '67p|67P'
)
for small_body in "${small_body_names[@]}"; do
  file_stem=${small_body%%|*}
  designation=${small_body#*|}
  curl -sS --fail --get 'https://ssd-api.jpl.nasa.gov/sbdb.api' \
    --data-urlencode "sstr=$designation" \
    --data-urlencode 'phys-par=1' \
    -o "$temporary_dir/sbdb-$file_stem.json"
done

test "$(wc -l < "$temporary_dir/gaia-dr3-bright.csv")" -eq 501
test "$(wc -l < "$temporary_dir/nasa-exoplanet-nearby.csv")" -eq 251

install -m 0644 "$temporary_dir/gaia-dr3-bright.csv" \
  "$output_dir/gaia-dr3-bright.csv"
install -m 0644 "$temporary_dir/nasa-exoplanet-nearby.csv" \
  "$output_dir/nasa-exoplanet-nearby.csv"
for small_body in "${small_body_names[@]}"; do
  file_stem=${small_body%%|*}
  install -m 0644 "$temporary_dir/sbdb-$file_stem.json" \
    "$output_dir/sbdb-$file_stem.json"
done

sha256sum \
  "$output_dir/gaia-dr3-bright.csv" \
  "$output_dir/nasa-exoplanet-nearby.csv" \
  "$output_dir"/sbdb-*.json > "$output_dir/SHA256SUMS"

echo "astronomy data refreshed in $output_dir"
