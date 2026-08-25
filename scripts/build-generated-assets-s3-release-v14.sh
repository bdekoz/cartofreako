#!/usr/bin/env bash

set -Eeuo pipefail

script_dir=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd -P)
repository_root=$(cd -- "$script_dir/.." && pwd -P)
default_output=$repository_root/build/s3-release-v14
source "$script_dir/lib-release-products.sh"
output=$default_output
replace=false
source_commit=
source_tag=UNAVAILABLE
source_published_at=

usage()
{
  cat <<'EOF'
Usage: scripts/build-generated-assets-s3-release-v14.sh [OPTIONS]

Build the local, offline Cartofreako v14 AAO/S3 release tree from the frozen
217-artifact Stage 14 input cases and the proposed-v14 consumer layout.

Options:
  --output PATH                Override build/s3-release-v14.
  --replace                    Replace an existing output tree.
  --source-commit SHA          Override HEAD.
  --source-tag TAG             Override UNAVAILABLE.
  --source-published-at ISO    Override current UTC timestamp.
  -h, --help                   Show this help.
EOF
}

die()
{
  printf '%s: %s\n' "${0##*/}" "$*" >&2
  exit 1
}

while (($#)); do
  case $1 in
    --output)
      (($# >= 2)) || die "$1 requires a value"
      output=$2
      shift 2
      ;;
    --replace)
      replace=true
      shift
      ;;
    --source-commit)
      (($# >= 2)) || die "$1 requires a value"
      source_commit=$2
      shift 2
      ;;
    --source-tag)
      (($# >= 2)) || die "$1 requires a value"
      source_tag=$2
      shift 2
      ;;
    --source-published-at)
      (($# >= 2)) || die "$1 requires a value"
      source_published_at=$2
      shift 2
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      die "unknown option: $1"
      ;;
  esac
done

for command_name in awk basename cmp cp date dirname find git gzip jq mkdir \
  mktemp mv node rm sed sha256sum sort tar wc; do
  command -v "$command_name" >/dev/null || die "missing command: $command_name"
done

output_parent=$(dirname -- "$output")
mkdir -p -- "$output_parent"
output_parent=$(cd -- "$output_parent" && pwd -P)
output=$output_parent/$(basename -- "$output")
if [[ -e $output ]]; then
  [[ $replace == true ]] || die "output exists: $output; pass --replace"
  rm -rf -- "$output"
fi

if [[ -z $source_commit ]]; then
  source_commit=$(git -C "$repository_root" rev-parse HEAD)
fi
if [[ ! $source_commit =~ ^[0-9a-f]{40}$ ]]; then
  die "source commit must be a full hexadecimal object ID"
fi
if [[ -z $source_published_at ]]; then
  source_published_at=$(date -u '+%Y-%m-%dT%H:%M:%SZ')
fi
if [[ ! $source_published_at =~ ^[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2}Z$ ]]; then
  die "invalid --source-published-at ISO-8601 UTC timestamp"
fi

input_fixture=$repository_root/fixtures/gpu-benchmark/v1/stage-14-inputs.json
consumer_layout=$repository_root/build/consumer-release-layout-v1
viewer_source=$repository_root/docs/releases/v13-s3-viewer.html
for required_path in "$input_fixture" "$viewer_source"; do
  [[ -f $required_path ]] || die "required input not found: $required_path"
done

work_root=$(mktemp -d "$output_parent/.s3-release-v14.XXXXXX")
release_root=$work_root/release
mkdir -p -- "$release_root"
cleanup()
{
  rm -rf -- "$work_root"
}
trap cleanup EXIT HUP INT TERM

printf 'Building proposed-v14 consumer indexes and runtime...\n'
node "$repository_root/scripts/build-consumer-release-layout.mjs" \
  --replace --output "$work_root/consumer-layout"

printf 'Copying indexes and runtime into the v14 release tree...\n'
cp --archive -- "$work_root/consumer-layout/indexes" "$release_root/"
cp --archive -- "$work_root/consumer-layout/runtime" "$release_root/"
cp -- "$viewer_source" "$release_root/viewer.html"

printf 'Copying 217 frozen standard products into proposed-v14 paths...\n'
STAGE_FAMILY_MASTER=1
STAGE_FAMILY_PRINT=1
STAGE_FAMILY_FULL=png
STAGE_FAMILY_THUMBNAIL=1
STAGE_FAMILY_SCREEN_PNG=1
STAGE_FAMILY_SCREEN_WEBP=1
jq -r '.cases[] | [.id, .lifecycle, .projectionId, .parents.svg.path,
  .parents.pdf.path, .parents.fullPng.path, .screen.png.path,
  .screen.webp.path] | @tsv' "$input_fixture" |
stage_release_products "$release_root"

printf 'Writing v14 release README and metadata...\n'
cat > "$release_root/README.md" <<EOF
# Cartofreako v14 generated assets

Source commit: $source_commit
Source tag: $source_tag
Generated release timestamp: $source_published_at

This is the offline-staged v14 object tree for UCB AAO/S3 publication.
Do not treat the presence of this tree as an upload authorization or a
completed remote publication.
EOF

manifest_path=$release_root/SHA256SUMS
release_path=$release_root/release.json
while IFS= read -r -d '' relative_path; do
  (
    cd -- "$release_root"
    sha256sum -- "$relative_path"
  )
done < <(
  LC_ALL=C find "$release_root" -type f \
    ! -path "$manifest_path" ! -path "$release_path" \
    -printf '%P\0' | LC_ALL=C sort -z
) > "$manifest_path"

payload_count=$(wc -l < "$manifest_path")
release_count=$((payload_count + 2))
products_count=$(find "$release_root/products" -type f 2>/dev/null | wc -l)
indexes_count=$(find "$release_root/indexes" -type f 2>/dev/null | wc -l)
runtime_count=$(find "$release_root/runtime" -type f 2>/dev/null | wc -l)
svg_gzip_count=$(find "$release_root/products" -path '*/master/*.svg.gz' -type f | wc -l)
pdf_count=$(find "$release_root/products" -path '*/print/*.pdf' -type f | wc -l)
png_count=$(find "$release_root/products" -path '*/full/*.png' -type f | wc -l)
thumbnail_count=$(find "$release_root/products" -path '*/thumbnail/*.png' -type f | wc -l)
screen_png_count=$(find "$release_root/products" -path '*/screen-1080p/png/*.png' -type f | wc -l)
screen_webp_count=$(find "$release_root/products" -path '*/screen-1080p/webp/*.webp' -type f | wc -l)
manifest_sha256=$(sha256sum -- "$manifest_path" | awk '{print $1}')

jq -n \
  --arg source_commit "$source_commit" \
  --arg source_tag "$source_tag" \
  --arg source_published_at "$source_published_at" \
  --arg manifest_sha256 "$manifest_sha256" \
  --argjson products_count "$products_count" \
  --argjson indexes_count "$indexes_count" \
  --argjson runtime_count "$runtime_count" \
  --argjson svg_gzip_count "$svg_gzip_count" \
  --argjson pdf_count "$pdf_count" \
  --argjson png_count "$png_count" \
  --argjson thumbnail_count "$thumbnail_count" \
  --argjson screen_png_count "$screen_png_count" \
  --argjson screen_webp_count "$screen_webp_count" \
  --argjson payload_count "$payload_count" \
  --argjson release_count "$release_count" \
  '{
    schema_version: 2,
    dataset: "cartofreako-generated-assets",
    release: "v14",
    stage: 14,
    complete: true,
    source: {
      repository: "https://github.com/bdekoz/cartofreako",
      tag: $source_tag,
      commit: $source_commit,
      release_published_at: $source_published_at
    },
    destination: {
      endpoint: "https://s3-ewh.ist.berkeley.edu",
      region: "us-east-1",
      bucket: "adekosnik-bucket01",
      prefix: "cartofreako/v14"
    },
    layout: {
      archive_root: "products/",
      organization: "lifecycle/projection/format/artifact",
      partitions: ["standard", "optional", "exploration"],
      runtime: "runtime/api-3/",
      indexes: "indexes/"
    },
    inventory: {
      products: $products_count,
      indexes: $indexes_count,
      runtime_files: $runtime_count,
      master_svg_gzip_files: $svg_gzip_count,
      print_pdf_files: $pdf_count,
      full_png_files: $png_count,
      thumbnail_files: $thumbnail_count,
      screen_png_files: $screen_png_count,
      screen_webp_files: $screen_webp_count,
      manifest_payload_files: $payload_count,
      release_object_count: $release_count
    },
    integrity: {
      algorithm: "SHA-256",
      manifest: "SHA256SUMS",
      manifest_sha256: $manifest_sha256,
      manifest_excludes: ["SHA256SUMS", "release.json"]
    },
    delivery: {
      access: "public-read",
      cache_control: "public,max-age=31536000,immutable",
      svg_gzip: {
        keys: "products/<lifecycle>/<projection>/master/*.svg.gz",
        stored_form: "gzip",
        content_type: "application/gzip",
        content_encoding: null,
        browser_viewer: "viewer.html"
      }
    }
  }' > "$release_path"

(
  cd -- "$release_root"
  sha256sum --check --quiet --strict SHA256SUMS
)
jq empty "$release_path"

mv -- "$release_root" "$output"
trap - EXIT HUP INT TERM
rm -rf -- "$work_root"

printf 'Built v14 release tree: %s\n' "$output"
printf 'Objects: %s; products: %s; indexes: %s; runtime: %s; svg.gz: %s; pdf: %s; png: %s; thumbnails: %s; screen-png: %s; screen-webp: %s\n' \
  "$release_count" "$products_count" "$indexes_count" "$runtime_count" \
  "$svg_gzip_count" "$pdf_count" "$png_count" "$thumbnail_count" \
  "$screen_png_count" "$screen_webp_count"
