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
source "$script_dir/lib-release-products.sh"

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

case $tier in
  preview)
    STAGE_FAMILY_THUMBNAIL=1
    STAGE_FAMILY_SCREEN_WEBP=1
    ;;
  browse)
    STAGE_FAMILY_THUMBNAIL=1
    STAGE_FAMILY_SCREEN_WEBP=1
    STAGE_FAMILY_FULL=webp
    ;;
  full)
    STAGE_FAMILY_THUMBNAIL=1
    STAGE_FAMILY_SCREEN_WEBP=1
    STAGE_FAMILY_FULL=both
    STAGE_FAMILY_MASTER=1
    STAGE_FAMILY_PRINT=1
    STAGE_FAMILY_SCREEN_PNG=1
    ;;
esac

STAGE_WEBP_QUALITY=$webp_quality
STAGE_WEBP_LOSSLESS=$webp_lossless
webp_worklist=$(mktemp "$work_root/.webp.XXXXXX")
STAGE_WEBP_WORKLIST=$webp_worklist

jq -r '
  .artifacts[]
  | [.id, .pass.lifecycle, .projection.id,
     .parents.svg.path, .parents.pdf.path, .parents.fullPng.path,
     .screen.png.path, .screen.webp.path]
  | @tsv
' "$catalog" | stage_release_products "$release_root"

convert_staged_webp_worklist "$webp_worklist" "$jobs"

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
