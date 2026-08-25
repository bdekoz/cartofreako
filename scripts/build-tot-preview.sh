#!/usr/bin/env bash
# Build the repo-local top-of-tree (TOT) preview snapshot.
#
# Reads assets.generated/catalog/artifacts-v1.json and mirrors the AAO
# products layout under a repo-local root so the GitHub Pages site can switch
# image backends without a per-backend path grammar. This is a mutable local
# preview, not an AAO publication.
set -Eeuo pipefail

readonly script_dir=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd -P)
readonly repository_root=$(cd -- "$script_dir/.." && pwd -P)
readonly catalog=$repository_root/assets.generated/catalog/artifacts-v1.json
readonly default_output=$repository_root/assets.tot

tier=browse
output=$default_output
webp_quality=90
webp_lossless=0
allow_oversize=0
jobs=$(nproc 2>/dev/null || printf '4')

usage() {
  cat <<'EOF'
Usage: scripts/build-tot-preview.sh [options]

Build the TOT preview tree from the current generated catalog using the AAO
product layout. Tiers:

  preview  thumbnails + screen-1080p WebP
  browse   preview + full-resolution WebP (default; deployable ceiling)
  full     everything, including master SVG, print PDF, and full PNG
           (local only; requires --allow-oversize)

Options:
  --tier TIER            preview|browse|full (default: browse)
  --output PATH          Override the default assets.tot directory.
  --webp-quality N       Full-resolution WebP quality 1-100 (default: 90).
  --webp-lossless        Derive lossless full-resolution WebP instead.
  --jobs N               Parallel conversion workers (default: CPU count).
  --allow-oversize       Permit the full tier.
  -h, --help             Show this help.
EOF
}

die() {
  printf 'build-tot-preview: %s\n' "$*" >&2
  exit 1
}

while (( $# > 0 )); do
  case $1 in
    --tier)
      [[ $# -ge 2 ]] || die '--tier requires a value'
      tier=$2
      shift
      ;;
    --output)
      [[ $# -ge 2 ]] || die '--output requires a value'
      output=$2
      shift
      ;;
    --webp-quality)
      [[ $# -ge 2 ]] || die '--webp-quality requires a value'
      webp_quality=$2
      shift
      ;;
    --webp-lossless)
      webp_lossless=1
      ;;
    --jobs)
      [[ $# -ge 2 ]] || die '--jobs requires a value'
      jobs=$2
      shift
      ;;
    --allow-oversize)
      allow_oversize=1
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      die "unknown option: $1"
      ;;
  esac
  shift
done

case $tier in
  preview|browse|full) ;;
  *) die "invalid tier: $tier (expected preview|browse|full)" ;;
esac
[[ $webp_quality =~ ^[0-9]+$ ]] && (( webp_quality >= 1 && webp_quality <= 100 )) ||
  die "invalid --webp-quality: $webp_quality"
[[ $jobs =~ ^[0-9]+$ ]] && (( jobs >= 1 )) || die "invalid --jobs: $jobs"
if [[ $tier == full && $allow_oversize -eq 0 ]]; then
  die 'the full tier exceeds commit and Pages limits; pass --allow-oversize to confirm'
fi

[[ -f $catalog ]] || die "missing catalog: $catalog"
command -v jq >/dev/null || die 'jq is required'
if command -v magick >/dev/null; then
  magick_command=$(command -v magick)
elif command -v convert >/dev/null; then
  magick_command=$(command -v convert)
else
  die 'ImageMagick (magick) is required for the full-resolution WebP family'
fi

output=${output%/}
case $output in
  ""|"/"|"$repository_root"|".") die "refusing output path: $output" ;;
esac
output_parent=$(dirname -- "$output")
output_name=$(basename -- "$output")
mkdir -p -- "$output_parent"

work_root=$(mktemp -d "$output_parent/.tot-preview.XXXXXX")
release_root=$work_root/$output_name
mkdir -p -- "$release_root"
cleanup() {
  rm -rf -- "$work_root"
}
trap cleanup EXIT HUP INT TERM

source_revision=$(jq -c '.sourceRevision' "$catalog")

emit_thumbnail=0
emit_screen_webp=0
emit_full_webp=0
emit_master=0
emit_print=0
emit_full_png=0
emit_screen_png=0
case $tier in
  preview)
    emit_thumbnail=1
    emit_screen_webp=1
    ;;
  browse)
    emit_thumbnail=1
    emit_screen_webp=1
    emit_full_webp=1
    ;;
  full)
    emit_thumbnail=1
    emit_screen_webp=1
    emit_full_webp=1
    emit_master=1
    emit_print=1
    emit_full_png=1
    emit_screen_png=1
    ;;
esac

webp_worklist=$(mktemp "$work_root/.webp.XXXXXX")

while IFS=$'\t' read -r id lifecycle projection svg pdf png screen_png screen_webp; do
  [[ $id && $lifecycle && $projection && $svg && $pdf && $png &&
     $screen_png && $screen_webp ]] ||
    die "malformed catalog case: ${id:-<empty>}"
  product_root=$release_root/products/$lifecycle/$projection
  stem=$(basename -- "$png" .png)
  mkdir -p -- "$product_root/screen-1080p/webp"

  if [[ $emit_thumbnail -eq 1 ]]; then
    thumbnail=$repository_root/assets.generated/$projection/thumbnail/$stem.png
    if [[ -f $thumbnail ]]; then
      mkdir -p -- "$product_root/thumbnail"
      cp -- "$thumbnail" "$product_root/thumbnail/$stem.png"
    fi
  fi

  if [[ $emit_screen_webp -eq 1 ]]; then
    [[ -f $repository_root/$screen_webp ]] || die "missing screen WebP: $screen_webp"
    cp -- "$repository_root/$screen_webp" "$product_root/screen-1080p/webp/$stem.webp"
  fi

  if [[ $emit_full_webp -eq 1 ]]; then
    [[ -f $repository_root/$png ]] || die "missing full PNG: $png"
    mkdir -p -- "$product_root/full"
    printf '%s|%s\n' "$repository_root/$png" "$product_root/full/$stem.webp" \
      >> "$webp_worklist"
  fi

  if [[ $emit_full_png -eq 1 ]]; then
    [[ -f $repository_root/$png ]] || die "missing full PNG: $png"
    cp -- "$repository_root/$png" "$product_root/full/$stem.png"
  fi

  if [[ $emit_master -eq 1 ]]; then
    [[ -f $repository_root/$svg ]] || die "missing master SVG: $svg"
    mkdir -p -- "$product_root/master"
    if [[ $svg == *.gz ]]; then
      cp -- "$repository_root/$svg" "$product_root/master/$stem.svg.gz"
    else
      gzip --best --no-name --stdout -- "$repository_root/$svg" \
        > "$product_root/master/$stem.svg.gz"
    fi
  fi

  if [[ $emit_print -eq 1 ]]; then
    [[ -f $repository_root/$pdf ]] || die "missing print PDF: $pdf"
    mkdir -p -- "$product_root/print"
    cp -- "$repository_root/$pdf" "$product_root/print/$stem.pdf"
  fi

  if [[ $emit_screen_png -eq 1 ]]; then
    [[ -f $repository_root/$screen_png ]] || die "missing screen PNG: $screen_png"
    mkdir -p -- "$product_root/screen-1080p/png"
    cp -- "$repository_root/$screen_png" "$product_root/screen-1080p/png/$stem.png"
  fi
done < <(jq -r '
  .artifacts[]
  | [.id, .pass.lifecycle, .projection.id,
     .parents.svg.path, .parents.pdf.path, .parents.fullPng.path,
     .screen.png.path, .screen.webp.path]
  | @tsv
' "$catalog")

if [[ -s $webp_worklist ]]; then
  export magick_command webp_quality webp_lossless
  < "$webp_worklist" xargs -P "$jobs" -I '{}' bash -c '
    set -e
    line="$1"
    source=${line%|*}
    target=${line#*|}
    if [[ "$webp_lossless" == 1 ]]; then
      "$magick_command" "$source" -define webp:lossless=true "$target"
    else
      "$magick_command" "$source" -define webp:quality="$webp_quality" "$target"
    fi
  ' _ '{}'
fi

generated_at=$(date --iso-8601=seconds --utc)
artifact_count=$(jq '.artifacts | length' "$catalog")
projection_count=$(jq '.artifacts | map(.projection.id) | unique | length' "$catalog")
stored_bytes=$(find "$release_root/products" -type f -printf '%s\n' |
  awk '{ total += $1 } END { print total + 0 }')

case $tier in
  preview) families=(thumbnail screen-1080p/webp) ;;
  browse) families=(thumbnail screen-1080p/webp full) ;;
  full) families=(master print full thumbnail screen-1080p/png screen-1080p/webp) ;;
esac
families_json=$(printf '%s\n' "${families[@]}" | jq -R . | jq -s .)

if [[ $webp_lossless -eq 1 ]]; then
  full_webp_mode=lossless
  full_webp_quality=null
else
  full_webp_mode=lossy
  full_webp_quality=$webp_quality
fi

manifest=$(jq -n \
  --arg schema "cartofreako-tot-preview-manifest-v1" \
  --arg tier "$tier" \
  --argjson sourceRevision "$source_revision" \
  --arg generatedAt "$generated_at" \
  --argjson artifactCount "$artifact_count" \
  --argjson projectionCount "$projection_count" \
  --argjson families "$families_json" \
  --argjson storedBytes "$stored_bytes" \
  --arg fullWebpMode "$full_webp_mode" \
  --argjson fullWebpQuality "$full_webp_quality" \
  '{
     schema: $schema,
     tier: $tier,
     stagedFrom: "assets.generated/catalog/artifacts-v1.json",
     sourceRevision: $sourceRevision,
     generatedAt: $generatedAt,
     artifactCount: $artifactCount,
     projectionCount: $projectionCount,
     families: $families,
     storedBytes: $storedBytes,
     fullWebp: { mode: $fullWebpMode, quality: $fullWebpQuality },
     mutability: "mutable local preview; not an AAO publication"
   }')
printf '%s\n' "$manifest" > "$release_root/manifest.json"

cat > "$release_root/README.md" <<EOF
# Cartofreako top-of-tree preview snapshot

Tier: $tier
Source revision: $(jq -r '.sourceRevision.gitCommit' "$catalog")
Generated: $generated_at

This is a mutable local snapshot of the current generated assets, staged into
the AAO product layout for offline GitHub Pages previews. It is not an AAO
publication and does not alter any release record. Restage it with:

\`\`\`sh
scripts/build-tot-preview.sh --tier $tier
\`\`\`
EOF

if [[ -e $output ]]; then
  rm -rf -- "$output"
fi
mv -- "$release_root" "$output"

printf 'Built TOT preview: %s (tier %s, %s artifacts, %s bytes)\n' \
  "$output" "$tier" "$artifact_count" "$stored_bytes"
