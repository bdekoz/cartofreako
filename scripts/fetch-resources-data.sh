#!/usr/bin/env bash
# Refresh the checked Stage 6b resources snapshot from primary sources.

set -euo pipefail

if [[ $# -gt 1 ]]; then
  echo "usage: $0 [OUTPUT_DIR]" >&2
  exit 2
fi

output_dir=${1:-assets.static/resources}
work_dir=$(mktemp -d /tmp/cartofreako-resources-refresh.XXXXXX)
trap 'rm -rf -- "$work_dir"' EXIT

curl_args=(
  --fail --silent --show-error --location
  --retry 4 --retry-all-errors --connect-timeout 20 --max-time 180
)

natural_earth_url='https://naturalearth.s3.amazonaws.com/110m_cultural/ne_110m_admin_0_countries.zip'
irena_url='https://www.irena.org/-/media/Files/IRENA/Agency/Publication/2026/Mar/IRENA_DAT_RE_capacity_statistics_2026.pdf'
usgs_url='https://pubs.usgs.gov/periodicals/mcs2026/mcs2026.pdf'

curl "${curl_args[@]}" --output "$work_dir/natural-earth.zip" \
  "$natural_earth_url"
curl "${curl_args[@]}" --output "$work_dir/irena-2026.pdf" "$irena_url"
curl "${curl_args[@]}" --output "$work_dir/usgs-mcs2026.pdf" "$usgs_url"
unzip -q "$work_dir/natural-earth.zip" -d "$work_dir/natural-earth"

world_bank_codes=(
  AG.PRD.FOOD.XD AG.LND.FRST.ZS SP.POP.0014.TO
  SP.POP.1519.FE.5Y SP.POP.1519.MA.5Y
  SP.POP.2024.FE.5Y SP.POP.2024.MA.5Y
  SP.POP.2529.FE.5Y SP.POP.2529.MA.5Y
  SP.POP.6064.FE.5Y SP.POP.6064.MA.5Y
  SP.POP.65UP.TO SP.POP.TOTL SP.POP.TOTL.FE.IN SP.POP.TOTL.MA.IN
)
for code in "${world_bank_codes[@]}"; do
  archive="$work_dir/cartofreako-wb-$code.zip"
  if ! curl "${curl_args[@]}" --output "$archive" \
      "https://api.worldbank.org/v2/en/indicator/$code?downloadformat=csv" \
      || ! unzip -tq "$archive" >/dev/null 2>&1; then
    rm -f -- "$archive"
    curl "${curl_args[@]}" \
      --output "$work_dir/cartofreako-wb-$code.json" \
      "https://api.worldbank.org/v2/country/all/indicator/$code?format=json&per_page=20000"
  fi
done

python3 -B scripts/prepare-resources-data.py \
  --natural-earth-shapefile \
    "$work_dir/natural-earth/ne_110m_admin_0_countries.shp" \
  --natural-earth-archive "$work_dir/natural-earth.zip" \
  --irena-pdf "$work_dir/irena-2026.pdf" \
  --usgs-pdf "$work_dir/usgs-mcs2026.pdf" \
  --world-bank-cache "$work_dir" \
  --output-dir "$work_dir/prepared"

mkdir -p "$output_dir"
for prepared in countries-110m.geojson resources-profile.json \
    resources-values.json SHA256SUMS; do
  install -m 0644 "$work_dir/prepared/$prepared" "$output_dir/$prepared"
done
