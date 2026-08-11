#!/usr/bin/env bash

set -euo pipefail

script_directory=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
repository_root=$(CDPATH= cd -- "$script_directory/.." && pwd)

expected=(
  generate-gpu-controls
  build-consumer-release-layout
  generate-atoll-evidence-canary
  render-marshall-islands-speculations-v01
  generate-majuro-atoll-evidence
  generate-anthropocene-purpleair-experiments
  generate-anthropocene-water-debris-experiments
)
mapfile -t actual < <(make --no-print-directory -s -C "$repository_root" \
  list-experiments)

if [[ ${actual[*]} != "${expected[*]}" ]]; then
  printf '%s\n' 'all-experiments registry differs from its checked contract:' >&2
  printf '  expected: %s\n' "${expected[*]}" >&2
  printf '  actual:   %s\n' "${actual[*]}" >&2
  exit 1
fi

for target in "${actual[@]}"; do
  case $target in
    release-*|*upload*|fetch-*|authorize-*|refresh-*)
      printf 'non-release experiment registry contains a state-changing target: %s\n' \
        "$target" >&2
      exit 1
      ;;
  esac
done

printf 'Non-release experiment aggregate passed: %s local builders.\n' \
  "${#actual[@]}"
