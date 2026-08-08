#!/usr/bin/env bash

set -Eeuo pipefail

readonly script_name=${0##*/}
readonly script_dir=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd -P)
readonly repository_root=$(cd -- "$script_dir/.." && pwd -P)
readonly default_data_root=$repository_root/build/s3-release-v13
readonly default_endpoint=https://s3-ewh.ist.berkeley.edu
readonly default_region=us-east-1
readonly default_bucket=adekosnik-bucket01
readonly default_prefix=cartofreako/v13
readonly -a projections=(
  cahill-keyes authagraph dymaxion myriahedral star-x voronoi
)

data_root=$default_data_root
endpoint=$default_endpoint
region=$default_region
bucket=$default_bucket
prefix=$default_prefix

usage()
{
  cat <<EOF
Usage: $script_name [OPTIONS]

Validate the exact Cartofreako v13 staged release contract without network
access, credentials, or S3 operations.

Options:
  --data-root PATH  Override build/s3-release-v13.
  --endpoint URL    Destination endpoint expected by release.json.
  --region NAME     Destination signing region expected by release.json.
  --bucket NAME     Destination bucket expected by release.json.
  --prefix PATH     Destination prefix expected by release.json.
  -h, --help        Show this help.
EOF
}

die()
{
  printf '%s: %s\n' "$script_name" "$*" >&2
  exit 1
}

while (($#)); do
  case $1 in
    --data-root)
      (($# >= 2)) || die "$1 requires a value"
      data_root=$2
      shift 2
      ;;
    --endpoint)
      (($# >= 2)) || die "$1 requires a value"
      endpoint=$2
      shift 2
      ;;
    --region)
      (($# >= 2)) || die "$1 requires a value"
      region=$2
      shift 2
      ;;
    --bucket)
      (($# >= 2)) || die "$1 requires a value"
      bucket=$2
      shift 2
      ;;
    --prefix)
      (($# >= 2)) || die "$1 requires a value"
      prefix=$2
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

for command_name in awk cmp diff find git grep gzip jq mktemp sha256sum sort \
  wc xargs; do
  command -v "$command_name" >/dev/null || die "missing required command: $command_name"
done
[[ -d $data_root ]] || die "release directory not found: $data_root"
data_root=$(cd -- "$data_root" && pwd -P)
endpoint=${endpoint%/}
prefix=${prefix#/}
prefix=${prefix%/}
[[ $endpoint == https://* && $endpoint != *[$'\r\n']* ]] || \
  die "endpoint must be a single-line HTTPS URL"
[[ $region =~ ^[A-Za-z0-9][A-Za-z0-9._-]*$ ]] || die "invalid region: $region"
[[ $bucket =~ ^[a-z0-9][a-z0-9.-]{1,61}[a-z0-9]$ ]] || die "invalid bucket: $bucket"
[[ -n $prefix && $prefix != *'..'* && $prefix != *'//'* &&
   $prefix != *[$'\r\n']* ]] || die "unsafe or empty prefix: $prefix"

printf 'Validating exact Cartofreako v13 release structure...\n'
for required_path in README.md viewer.html SHA256SUMS release.json \
  package/assets.generated.v13.tar.xz tree; do
  [[ -e $data_root/$required_path ]] || die "missing release artifact: $required_path"
done
for projection in "${projections[@]}"; do
  for format in svg pdf png thumbnail; do
    [[ -d $data_root/tree/$projection/$format ]] || \
      die "missing projection format directory: tree/$projection/$format"
  done
done
if find "$data_root" -type l -print -quit | grep -q .; then
  die "symlinks are not allowed beneath the release directory"
fi
if find "$data_root" -type f -size 0 -print -quit | grep -q .; then
  die "zero-byte files are not allowed beneath the release directory"
fi
if find "$data_root" -type f \( -name '*.tmp' -o -name '*.partial' \) \
  -print -quit | grep -q .; then
  die "temporary files remain beneath the release directory"
fi

work_root=$(mktemp -d "${TMPDIR:-/tmp}/cartofreako-v13-validate.XXXXXX")
local_paths=$work_root/local-paths
manifest_paths=$work_root/manifest-paths
cleanup()
{
  rm -rf -- "$work_root"
}
trap cleanup EXIT HUP INT TERM

LC_ALL=C find "$data_root" -type f ! -name SHA256SUMS ! -name release.json \
  -printf '%P\n' | LC_ALL=C sort > "$local_paths"
awk '{ sub(/^[[:xdigit:]]+[[:space:]][ *]/, ""); print }' \
  "$data_root/SHA256SUMS" | LC_ALL=C sort > "$manifest_paths"
if ! cmp -s -- "$local_paths" "$manifest_paths"; then
  printf 'SHA256SUMS path inventory does not match payload files.\n' >&2
  diff -u -- "$manifest_paths" "$local_paths" | sed -n '1,80p' >&2 || true
  exit 1
fi

printf 'Checking SHA-256 payload hashes...\n'
(
  cd -- "$data_root"
  sha256sum --check --quiet --strict SHA256SUMS
)
printf 'Checking JSON syntax and gzip integrity...\n'
jq empty "$data_root/release.json"
find "$data_root/tree" -type f -path '*/svg/*.svg.gz' -print0 | \
  xargs -0 -r -n 8 -P 4 gzip --test --

tree_file_count=$(find "$data_root/tree" -type f | wc -l)
raw_svg_count=$(find "$data_root/tree" -type f -path '*/svg/*.svg' | wc -l)
svg_gzip_count=$(find "$data_root/tree" -type f -path '*/svg/*.svg.gz' | wc -l)
pdf_count=$(find "$data_root/tree" -type f -path '*/pdf/*.pdf' | wc -l)
png_count=$(find "$data_root/tree" -type f -path '*/png/*.png' | wc -l)
thumbnail_count=$(find "$data_root/tree" -type f -path '*/thumbnail/*.png' | wc -l)
if [[ $tree_file_count -ne 825 || $raw_svg_count -ne 0 ||
      $svg_gzip_count -ne 211 || $pdf_count -ne 211 ||
      $png_count -ne 211 || $thumbnail_count -ne 192 ]]; then
  die "unexpected release inventory: tree=$tree_file_count svg=$raw_svg_count svg.gz=$svg_gzip_count pdf=$pdf_count png=$png_count thumbnails=$thumbnail_count"
fi
for projection in "${projections[@]}"; do
  projection_thumbnail_count=$(find "$data_root/tree/$projection/thumbnail" \
    -maxdepth 1 -type f -name '*.png' | wc -l)
  [[ $projection_thumbnail_count -eq 32 ]] || \
    die "$projection has $projection_thumbnail_count thumbnails; expected 32"
  for required_stem in cloud-atmosphere fiber-synthesized; do
    for format in svg pdf png thumbnail; do
      extension=$format
      [[ $format == svg ]] && extension=svg.gz
      [[ $format == thumbnail ]] && extension=png
      required_count=$(find "$data_root/tree/$projection/$format" -maxdepth 1 \
        -type f -name "$required_stem-*.$extension" | wc -l)
      [[ $required_count -eq 1 ]] || \
        die "$projection/$format has $required_count $required_stem products; expected one"
    done
  done
done

payload_count=$(wc -l < "$local_paths")
release_count=$(find "$data_root" -type f | wc -l)
general_upload_count=$(find "$data_root" -type f \
  ! -path "$data_root/tree/*/svg/*" ! -name release.json | wc -l)
if [[ $payload_count -ne 828 || $release_count -ne 830 ||
      $general_upload_count -ne 618 ]]; then
  die "unexpected publication counts: payload=$payload_count release=$release_count general=$general_upload_count"
fi
manifest_sha256=$(sha256sum "$data_root/SHA256SUMS" | awk '{print $1}')
package_sha256=$(sha256sum "$data_root/package/assets.generated.v13.tar.xz" | awk '{print $1}')
source_tag=$(jq -r '.source.tag' "$data_root/release.json")
source_commit=$(jq -r '.source.commit' "$data_root/release.json")
if [[ ! $source_tag =~ ^v[0-9]{8}(\.[0-9]+)?$ ||
      ! $source_commit =~ ^[0-9a-f]{40}$ ||
      $(git -C "$repository_root" rev-parse "$source_tag^{commit}" 2>/dev/null || true) != "$source_commit" ]]; then
  die "staged source tag and commit do not resolve to the same local commit"
fi

if ! jq -e \
  --arg endpoint "$endpoint" --arg region "$region" --arg bucket "$bucket" \
  --arg prefix "$prefix" --arg manifest_sha256 "$manifest_sha256" \
  --arg package_sha256 "$package_sha256" \
  --arg source_tag "$source_tag" --arg source_commit "$source_commit" \
  --argjson payload_count "$payload_count" \
  --argjson release_count "$release_count" '
    .complete == true and .release == "v13" and .stage == 13 and
    .source.tag == $source_tag and .source.commit == $source_commit and
    .destination.endpoint == $endpoint and .destination.region == $region and
    .destination.bucket == $bucket and .destination.prefix == $prefix and
    .inventory.manifest_payload_files == $payload_count and
    .inventory.release_object_count == $release_count and
    .integrity.manifest_sha256 == $manifest_sha256 and
    .package.sha256 == $package_sha256 and
    .delivery.access == "public-read" and
    .delivery.cache_control == "public,max-age=31536000,immutable" and
    .layout.svg_viewer == "viewer.html" and
    .layout.organization == "projection/format/artifact" and
    .inventory.source_tree_files == 909 and
    .inventory.published_tree_files == 825 and
    .inventory.published_svg_gzip_files == 211 and
    .inventory.pdf_files == 211 and .inventory.png_files == 211 and
    .inventory.thumbnail_files == 192 and
    .inventory.thumbnails_per_projection == 32 and
    .delivery.svg_gzip.content_type == "application/gzip" and
    .delivery.svg_gzip.content_encoding == null and
    .delivery.preview_png.content_type == "image/png"' \
  "$data_root/release.json" >/dev/null; then
  die "release.json does not agree with the exact Cartofreako v13 contract"
fi

release_bytes=$(find "$data_root" -type f -printf '%s\n' | \
  awk '{ total += $1 } END { printf "%.0f", total }')
printf 'Exact Cartofreako validation passed: %s files, %s bytes.\n' \
  "$release_count" "$release_bytes"
