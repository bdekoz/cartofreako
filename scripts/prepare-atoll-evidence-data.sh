#!/usr/bin/env bash

# Derive compact 10 m GeoTIFF canary inputs from the ignored public USGS
# source archives.  The authoritative 1 m TBDEM and scenario archive are not
# modified and are not copied into Git.

set -euo pipefail

if [[ $# -gt 1 ]]; then
  printf 'usage: %s [atoll-evidence-directory]\n' "$0" >&2
  exit 2
fi

script_directory=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
repository_root=$(CDPATH= cd -- "$script_directory/.." && pwd)
data_directory=${1:-$repository_root/assets.static/atoll-evidence}
raw_directory=$data_directory/.raw
prepared_directory=$data_directory/prepared

tbdem_archive=$raw_directory/Majuro_TBDEM_Data.zip
inundation_archive=$raw_directory/Inundation_Exposure_Raster_Layers.zip
for source_path in "$tbdem_archive" "$inundation_archive"; do
  if [[ ! -f $source_path ]]; then
    printf 'missing ignored USGS source package: %s\n' "$source_path" >&2
    printf '%s\n' 'run make fetch-atoll-evidence-data first' >&2
    exit 1
  fi
done

for command_name in gdalinfo gdal_translate md5sum sha256sum unzip; do
  command -v "$command_name" >/dev/null 2>&1 || {
    printf 'missing required command: %s\n' "$command_name" >&2
    exit 2
  }
done

read -r tbdem_md5 _ < <(md5sum -- "$tbdem_archive")
if [[ $tbdem_md5 != 16b35677ba01331845285e178599b4ea ]]; then
  printf 'Majuro TBDEM package failed its published MD5 check\n' >&2
  exit 1
fi
read -r inundation_sha256 _ < <(sha256sum -- "$inundation_archive")
if [[ $inundation_sha256 != 6aea7d5b545825a83a9ab198af8695eeaf4cad507e69538b8dc684764e9f1818 ]]; then
  printf 'Majuro inundation package failed its frozen SHA-256 check\n' >&2
  exit 1
fi

work_directory=$(mktemp -d /tmp/cartofreako-atoll-prepare.XXXXXX)
cleanup()
{
  rm -rf -- "$work_directory"
}
trap cleanup EXIT

unzip -q -j "$tbdem_archive" \
  'Majuro_TBDEM_Data/Majuro_Topobathy_DEM_1m.tif' \
  -d "$work_directory"
unzip -q -j "$inundation_archive" \
  'Inundation_Exposure_Grids_062419/Deterministic/Marine_inundation_30in.tif' \
  'Inundation_Exposure_Grids_062419/Probabilistic/Probability_marine_inundation_30in.tif' \
  -d "$work_directory"

common_creation_options=(
  -co COMPRESS=DEFLATE
  -co TILED=YES
  -co ZLEVEL=9
  -co NUM_THREADS=ALL_CPUS
  -co BIGTIFF=IF_SAFER
)

gdal_translate -q -r average -outsize 4623 2381 -ot Float32 \
  -co PREDICTOR=3 "${common_creation_options[@]}" \
  "$work_directory/Majuro_Topobathy_DEM_1m.tif" \
  "$work_directory/majuro-tbdem-observation-10m.tif"
gdal_translate -q -r nearest -outsize 3973 1272 -ot Byte \
  -co PREDICTOR=2 "${common_creation_options[@]}" \
  "$work_directory/Marine_inundation_30in.tif" \
  "$work_directory/majuro-marine-inundation-30in-deterministic-10m.tif"
gdal_translate -q -r average -outsize 3973 1272 -ot Float32 \
  -co PREDICTOR=3 "${common_creation_options[@]}" \
  "$work_directory/Probability_marine_inundation_30in.tif" \
  "$work_directory/majuro-marine-inundation-30in-probability-10m.tif"

for prepared_name in \
  majuro-tbdem-observation-10m.tif \
  majuro-marine-inundation-30in-deterministic-10m.tif \
  majuro-marine-inundation-30in-probability-10m.tif; do
  gdalinfo "$work_directory/$prepared_name" >/dev/null
done

mkdir -p -- "$prepared_directory"
for prepared_name in \
  majuro-tbdem-observation-10m.tif \
  majuro-marine-inundation-30in-deterministic-10m.tif \
  majuro-marine-inundation-30in-probability-10m.tif; do
  install -m 0644 -- "$work_directory/$prepared_name" \
    "$prepared_directory/$prepared_name"
done

(
  cd "$prepared_directory"
  sha256sum -- \
    majuro-tbdem-observation-10m.tif \
    majuro-marine-inundation-30in-deterministic-10m.tif \
    majuro-marine-inundation-30in-probability-10m.tif \
    > SHA256SUMS
)

printf 'Prepared checked atoll-evidence derivatives in %s\n' "$prepared_directory"
printf '%s\n' 'Source: public USGS 1 m ITRF08 / UTM 59N rasters; derivative: approximately 10 m.'
