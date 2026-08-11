#!/usr/bin/env bash

set -euo pipefail

contract=${1:-contracts/print-products-v1.json}
root=$(cd "$(dirname "$0")/.." && pwd)
tolerance=$(jq -r '.pageTolerancePoints' "$contract")

jq -r '.projections[] | [.id, .representativeStem, (.width * 72), (.height * 72)] | @tsv' \
  "$contract" |
while IFS=$'\t' read -r projection stem expected_width expected_height; do
  pdf="$root/assets.generated/$projection/pdf/$stem.pdf"
  test -s "$pdf"
  info=$(pdfinfo "$pdf")
  pages=$(printf '%s\n' "$info" | sed -n 's/^Pages:[[:space:]]*//p')
  dimensions=$(printf '%s\n' "$info" |
    sed -n 's/^Page size:[[:space:]]*\([0-9.]*\)[[:space:]]*x[[:space:]]*\([0-9.]*\)[[:space:]]*pts.*$/\1 \2/p')
  test "$pages" = 1
  test -n "$dimensions"
  actual_width=${dimensions%% *}
  actual_height=${dimensions##* }
  awk -v actual="$actual_width" -v expected="$expected_width" \
    -v tolerance="$tolerance" \
    'BEGIN { difference = actual - expected; if (difference < 0) difference = -difference; exit !(difference <= tolerance) }'
  awk -v actual="$actual_height" -v expected="$expected_height" \
    -v tolerance="$tolerance" \
    'BEGIN { difference = actual - expected; if (difference < 0) difference = -difference; exit !(difference <= tolerance) }'
done

printf '%s\n' 'print contract: six one-page PDF MediaBoxes match their exact-ratio SVG products'
