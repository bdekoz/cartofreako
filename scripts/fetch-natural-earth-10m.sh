#!/usr/bin/env bash
# Fetch the pinned Natural Earth input used by generate-earth-ck.

set -euo pipefail

readonly natural_earth_url='https://naciscdn.org/naturalearth/10m/physical/10m_physical.zip'
readonly natural_earth_sha256='a79cc39162f29832b567de5e24e8770f04a0b997eefd8d067ae4c9df40d21d2a'
readonly destination="${1:-assets/natural-earth/10m-physical-vectors}"
readonly archive="${destination}/10m_physical.zip"
readonly stamp="${destination}/.natural-earth-10m-physical-5.1.1"

required_datasets=(
  ne_10m_coastline
  ne_10m_land
  ne_10m_minor_islands
  ne_10m_reefs
  ne_10m_ocean
  ne_10m_rivers_lake_centerlines
  ne_10m_lakes
  ne_10m_playas
  ne_10m_antarctic_ice_shelves_polys
  ne_10m_glaciated_areas
  ne_10m_bathymetry_A_10000
  ne_10m_bathymetry_B_9000
  ne_10m_bathymetry_C_8000
  ne_10m_bathymetry_D_7000
  ne_10m_bathymetry_E_6000
  ne_10m_bathymetry_F_5000
  ne_10m_bathymetry_G_4000
  ne_10m_bathymetry_H_3000
  ne_10m_bathymetry_I_2000
  ne_10m_bathymetry_J_1000
  ne_10m_bathymetry_K_200
  ne_10m_bathymetry_L_0
)

data_complete()
{
  [[ -f "${stamp}" ]] || return 1
  local dataset
  local extension
  for dataset in "${required_datasets[@]}"; do
    for extension in shp shx dbf prj; do
      [[ -f "${destination}/${dataset}.${extension}" ]] || return 1
    done
  done
}

if data_complete; then
  exit 0
fi

mkdir -p "${destination}"
if [[ ! -f "${archive}" ]]; then
  curl -L --fail --show-error \
    --output "${archive}" "${natural_earth_url}"
fi

actual_checksum="$(sha256sum "${archive}")"
actual_checksum="${actual_checksum%% *}"
if [[ "${actual_checksum}" != "${natural_earth_sha256}" ]]; then
  printf 'Natural Earth archive checksum mismatch: expected %s, got %s\n' \
    "${natural_earth_sha256}" "${actual_checksum}" >&2
  exit 1
fi

patterns=()
for dataset in "${required_datasets[@]}"; do
  patterns+=("${dataset}.*")
done
unzip -q -o "${archive}" "${patterns[@]}" -d "${destination}"

# Create the stamp last so an interrupted download or extraction is retried.
touch "${stamp}"
data_complete
