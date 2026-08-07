#!/usr/bin/env bash
# Refresh the checked Stage 12 resources snapshot from primary sources.

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
iaea_url='https://www-pub.iaea.org/MTCD/publications/PDF/RDS-2-45_web.pdf'
refinery_url='https://data.un.org/Handlers/DownloadHandler.ashx?DataFilter=cmID%3aGR%3btrID%3a086&DataMartId=EDATA&Format=csv'
reef_url='https://wriorg.s3.amazonaws.com/s3fs-public/reefs_at_risk_revisited_present.kmz'

curl "${curl_args[@]}" --output "$work_dir/natural-earth.zip" \
  "$natural_earth_url"
curl "${curl_args[@]}" --output "$work_dir/irena-2026.pdf" "$irena_url"
curl "${curl_args[@]}" --output "$work_dir/usgs-mcs2026.pdf" "$usgs_url"
curl "${curl_args[@]}" --output "$work_dir/iaea-rds-2-45.pdf" "$iaea_url"
curl "${curl_args[@]}" --output "$work_dir/undata-refinery.zip" \
  "$refinery_url"
curl "${curl_args[@]}" --output "$work_dir/reefs-at-risk-present.kmz" \
  "$reef_url"
unzip -q "$work_dir/natural-earth.zip" -d "$work_dir/natural-earth"
refinery_member=$(unzip -Z1 "$work_dir/undata-refinery.zip")
if [[ $refinery_member != UNdata_Export_*.csv ]]; then
  echo "unexpected UNdata refinery archive layout" >&2
  exit 1
fi
unzip -p "$work_dir/undata-refinery.zip" "$refinery_member" \
  > "$work_dir/undata-refinery.csv"

world_bank_codes=(
  AG.PRD.FOOD.XD AG.LND.FRST.ZS ER.FSH.PROD.MT IP.PAT.RESD
  SE.ADT.LITR.ZS SE.SEC.CUAT.UP.ZS SE.TER.CUAT.BA.ZS
  SE.TER.CUAT.MS.ZS SP.POP.0014.TO
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
  --iaea-pdf "$work_dir/iaea-rds-2-45.pdf" \
  --usgs-pdf "$work_dir/usgs-mcs2026.pdf" \
  --refinery-csv "$work_dir/undata-refinery.csv" \
  --reef-kmz "$work_dir/reefs-at-risk-present.kmz" \
  --world-bank-cache "$work_dir" \
  --output-dir "$work_dir/prepared"

mkdir -p "$output_dir"
for prepared in countries-110m.geojson coral-reefs-025deg.geojson \
    resources-profile.json \
    resources-values.json SHA256SUMS; do
  install -m 0644 "$work_dir/prepared/$prepared" "$output_dir/$prepared"
done
