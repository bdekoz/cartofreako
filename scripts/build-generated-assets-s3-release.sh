#!/usr/bin/env bash

set -Eeuo pipefail

readonly script_dir=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd -P)
readonly repository_root=$(cd -- "$script_dir/.." && pwd -P)
readonly default_archive=$repository_root/assets.generated.v12.tar.xz
readonly default_output=$repository_root/build/s3-release-v12
readonly readme_source=$repository_root/docs/releases/v12-s3-README.md
readonly viewer_source=$repository_root/docs/releases/v12-s3-viewer.html
readonly expected_archive_sha256=dc1d761def31d77a05a7cc42f9bc0705ee864046f2e235f50c701c9c42fe960a
readonly expected_archive_bytes=927742112
readonly expected_archive_entries=679
readonly expected_tree_files=673
readonly expected_tree_bytes=2322788028
readonly expected_svg_files=187
readonly expected_svg_gzip_files=84
readonly expected_pdf_files=187
readonly expected_png_files=187
readonly expected_thumbnail_files=28
readonly expected_published_tree_files=589
readonly expected_published_svg_gzip_files=187
readonly expected_derived_svg_gzip_files=103
readonly expected_payload_files=592
readonly expected_release_objects=594
readonly cache_control='public,max-age=31536000,immutable'

archive=$default_archive
output=$default_output

usage() {
  cat <<'EOF'
Usage: scripts/build-generated-assets-s3-release.sh [options]

Build the locally validated object tree for the immutable Cartofreako v12 S3
release. The output directory must not already exist.

Options:
  --archive PATH  Override assets.generated.v12.tar.xz.
  --output PATH   Override build/s3-release-v12.
  -h, --help      Show this help.
EOF
}

while (( $# > 0 )); do
  case $1 in
    --archive)
      [[ $# -ge 2 ]] || { printf '%s requires a value.\n' "$1" >&2; exit 2; }
      archive=$2
      shift
      ;;
    --output)
      [[ $# -ge 2 ]] || { printf '%s requires a value.\n' "$1" >&2; exit 2; }
      output=$2
      shift
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      printf 'Unknown option: %s\n' "$1" >&2
      usage >&2
      exit 2
      ;;
  esac
  shift
done

for command_name in cmp cp find gzip jq mktemp sha256sum stat tar xz; do
  if ! command -v "$command_name" >/dev/null; then
    printf 'Missing required command: %s\n' "$command_name" >&2
    exit 1
  fi
done

if [[ ! -f $archive ]]; then
  printf 'Release archive not found: %s\n' "$archive" >&2
  exit 1
fi
if [[ ! -f $readme_source ]]; then
  printf 'S3 release README not found: %s\n' "$readme_source" >&2
  exit 1
fi
if [[ ! -f $viewer_source ]]; then
  printf 'S3 SVG viewer not found: %s\n' "$viewer_source" >&2
  exit 1
fi
if [[ -e $output ]]; then
  printf 'Output already exists: %s\n' "$output" >&2
  printf 'Move it aside or choose another --output path; nothing was replaced.\n' >&2
  exit 1
fi

archive=$(cd -- "$(dirname -- "$archive")" && pwd -P)/$(basename -- "$archive")
output_parent=$(dirname -- "$output")
mkdir -p -- "$output_parent"
output_parent=$(cd -- "$output_parent" && pwd -P)
output=$output_parent/$(basename -- "$output")

work_root=$(mktemp -d "$output_parent/.s3-release-v12.XXXXXX")
extract_root=$work_root/extracted
release_root=$work_root/release
listing_path=$work_root/archive-paths.txt

cleanup() {
  rm -rf -- "$work_root"
}
trap cleanup EXIT HUP INT TERM

printf 'Verifying v12 archive identity and XZ stream...\n'
actual_archive_sha256=$(sha256sum -- "$archive" | awk '{print $1}')
actual_archive_bytes=$(stat -c '%s' -- "$archive")
if [[ $actual_archive_sha256 != "$expected_archive_sha256" ||
      $actual_archive_bytes -ne $expected_archive_bytes ]]; then
  printf 'Archive identity mismatch: sha256=%s bytes=%s\n' \
    "$actual_archive_sha256" "$actual_archive_bytes" >&2
  exit 1
fi
xz --test -- "$archive"

tar --list --file="$archive" > "$listing_path"
archive_entries=$(wc -l < "$listing_path")
if [[ $archive_entries -ne $expected_archive_entries ]]; then
  printf 'Unexpected archive entry count: %s (expected %s).\n' \
    "$archive_entries" "$expected_archive_entries" >&2
  exit 1
fi
while IFS= read -r member_path; do
  if [[ $member_path != assets.generated/ &&
        $member_path != assets.generated/* ]]; then
    printf 'Archive member escapes assets.generated/: %s\n' "$member_path" >&2
    exit 1
  fi
  if [[ $member_path == /* || $member_path == *'/../'* ||
        $member_path == ../* || $member_path == *'/..' ]]; then
    printf 'Unsafe archive member path: %s\n' "$member_path" >&2
    exit 1
  fi
done < "$listing_path"

printf 'Extracting the authoritative archive into the temporary build area...\n'
mkdir -p -- "$extract_root" "$release_root/tree" "$release_root/package"
tar --extract --xz --file="$archive" --directory="$extract_root" \
  --no-same-owner --no-same-permissions
source_tree=$extract_root/assets.generated

if find "$source_tree" -type l -print -quit | grep -q .; then
  printf 'Symlinks are not allowed in the generated-assets tree.\n' >&2
  exit 1
fi
if find "$source_tree" -type f -size 0 -print -quit | grep -q .; then
  printf 'Zero-byte files are not allowed in the generated-assets tree.\n' >&2
  exit 1
fi

tree_files=$(find "$source_tree" -type f | wc -l)
tree_bytes=$(find "$source_tree" -type f -printf '%s\n' | \
  awk '{ total += $1 } END { printf "%.0f", total }')
svg_files=$(find "$source_tree/svg" -maxdepth 1 -type f -name '*.svg' | wc -l)
svg_gzip_files=$(find "$source_tree/svg" -maxdepth 1 -type f -name '*.svg.gz' | wc -l)
pdf_files=$(find "$source_tree/pdf" -maxdepth 1 -type f -name '*.pdf' | wc -l)
png_files=$(find "$source_tree/png" -maxdepth 1 -type f -name '*.png' | wc -l)
thumbnail_files=$(find "$source_tree/thumbnail/cahill-keyes" -maxdepth 1 \
  -type f -name '*.png' | wc -l)
if [[ $tree_files -ne $expected_tree_files ||
      $tree_bytes -ne $expected_tree_bytes ||
      $svg_files -ne $expected_svg_files ||
      $svg_gzip_files -ne $expected_svg_gzip_files ||
      $pdf_files -ne $expected_pdf_files ||
      $png_files -ne $expected_png_files ||
      $thumbnail_files -ne $expected_thumbnail_files ]]; then
  printf 'Unexpected archive inventory: files=%s bytes=%s svg=%s svg.gz=%s pdf=%s png=%s thumbnails=%s\n' \
    "$tree_files" "$tree_bytes" "$svg_files" "$svg_gzip_files" \
    "$pdf_files" "$png_files" "$thumbnail_files" >&2
  exit 1
fi

printf 'Checking the 84 explicit SVG gzip members...\n'
while IFS= read -r -d '' gzip_path; do
  gzip --test -- "$gzip_path"
  gzip --decompress --stdout -- "$gzip_path" | cmp --silent -- - "${gzip_path%.gz}"
done < <(find "$source_tree/svg" -maxdepth 1 -type f -name '*.svg.gz' \
  -print0 | LC_ALL=C sort -z)

printf 'Constructing tree/ with every SVG stored as an explicit .svg.gz object...\n'
cp --archive --link -- "$source_tree"/. "$release_root/tree"/
while IFS= read -r -d '' svg_path; do
  gzip_path=$svg_path.gz
  if [[ -f $gzip_path ]]; then
    gzip --test -- "$gzip_path"
    gzip --decompress --stdout -- "$gzip_path" | \
      cmp --silent -- - "$svg_path"
  else
    gzip_temp=$gzip_path.partial
    gzip --best --no-name --stdout -- "$svg_path" > "$gzip_temp"
    mv -- "$gzip_temp" "$gzip_path"
  fi
  rm -- "$svg_path"
done < <(find "$release_root/tree/svg" -maxdepth 1 -type f -name '*.svg' \
  -print0 | LC_ALL=C sort -z)

while IFS= read -r -d '' gzip_path; do
  gzip --test -- "$gzip_path"
  source_path=$source_tree/svg/$(basename -- "${gzip_path%.gz}")
  gzip --decompress --stdout -- "$gzip_path" | \
    cmp --silent -- - "$source_path"
done < <(find "$release_root/tree/svg" -maxdepth 1 -type f -name '*.svg.gz' \
  -print0 | LC_ALL=C sort -z)

published_tree_files=$(find "$release_root/tree" -type f | wc -l)
published_svg_files=$(find "$release_root/tree/svg" -maxdepth 1 -type f \
  -name '*.svg' | wc -l)
published_svg_gzip_files=$(find "$release_root/tree/svg" -maxdepth 1 \
  -type f -name '*.svg.gz' | wc -l)
if [[ $published_tree_files -ne $expected_published_tree_files ||
      $published_svg_files -ne 0 ||
      $published_svg_gzip_files -ne $expected_published_svg_gzip_files ]]; then
  printf 'Unexpected published inventory: tree=%s svg=%s svg.gz=%s\n' \
    "$published_tree_files" "$published_svg_files" \
    "$published_svg_gzip_files" >&2
  exit 1
fi

package_path=$release_root/package/assets.generated.v12.tar.xz
if ! ln -- "$archive" "$package_path" 2>/dev/null; then
  cp --archive --reflink=auto -- "$archive" "$package_path"
fi
cp -- "$readme_source" "$release_root/README.md"
cp -- "$viewer_source" "$release_root/viewer.html"

manifest_path=$release_root/SHA256SUMS
release_path=$release_root/release.json
printf 'Calculating the sorted SHA-256 object manifest...\n'
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

payload_file_count=$(wc -l < "$manifest_path")
payload_byte_count=$(find "$release_root" -type f ! -path "$manifest_path" \
  ! -path "$release_path" -printf '%s\n' | \
  awk '{ total += $1 } END { printf "%.0f", total }')
published_tree_bytes=$(find "$release_root/tree" -type f -printf '%s\n' | \
  awk '{ total += $1 } END { printf "%.0f", total }')
published_svg_gzip_bytes=$(find "$release_root/tree/svg" -maxdepth 1 -type f \
  -name '*.svg.gz' -printf '%s\n' | \
  awk '{ total += $1 } END { printf "%.0f", total }')
manifest_sha256=$(sha256sum -- "$manifest_path" | awk '{print $1}')
release_object_count=$((payload_file_count + 2))
if [[ $payload_file_count -ne $expected_payload_files ||
      $release_object_count -ne $expected_release_objects ]]; then
  printf 'Unexpected release counts: payload=%s objects=%s\n' \
    "$payload_file_count" "$release_object_count" >&2
  exit 1
fi

jq -n \
  --arg manifest_sha256 "$manifest_sha256" \
  --arg archive_sha256 "$expected_archive_sha256" \
  --arg cache_control "$cache_control" \
  --argjson archive_bytes "$expected_archive_bytes" \
  --argjson source_tree_files "$expected_tree_files" \
  --argjson source_tree_bytes "$expected_tree_bytes" \
  --argjson published_tree_files "$expected_published_tree_files" \
  --argjson published_tree_bytes "$published_tree_bytes" \
  --argjson svg_files "$expected_svg_files" \
  --argjson source_svg_gzip_files "$expected_svg_gzip_files" \
  --argjson derived_svg_gzip_files "$expected_derived_svg_gzip_files" \
  --argjson published_svg_gzip_files "$expected_published_svg_gzip_files" \
  --argjson published_svg_gzip_bytes "$published_svg_gzip_bytes" \
  --argjson pdf_files "$expected_pdf_files" \
  --argjson png_files "$expected_png_files" \
  --argjson thumbnail_files "$expected_thumbnail_files" \
  --argjson payload_file_count "$payload_file_count" \
  --argjson payload_byte_count "$payload_byte_count" \
  --argjson release_object_count "$release_object_count" \
  '{
    schema_version: 1,
    dataset: "cartofreako-generated-assets",
    release: "v12",
    complete: true,
    source: {
      repository: "https://github.com/bdekoz/cartofreako",
      tag: "v20260807",
      commit: "2bd3d760fef540addfcbb4f8002ef7b283d8000f",
      release_published_at: "2026-08-07T03:04:22Z"
    },
    destination: {
      endpoint: "https://s3-ewh.ist.berkeley.edu",
      region: "us-east-1",
      bucket: "adekosnik-bucket01",
      prefix: "cartofreako/v12"
    },
    layout: {
      archive_root: "assets.generated/",
      published_tree_root: "tree/",
      recovery_package: "package/assets.generated.v12.tar.xz",
      svg_viewer: "viewer.html"
    },
    package: {
      bytes: $archive_bytes,
      sha256: $archive_sha256
    },
    inventory: {
      source_tree_files: $source_tree_files,
      source_tree_bytes: $source_tree_bytes,
      source_svg_files: $svg_files,
      source_explicit_svg_gzip_files: $source_svg_gzip_files,
      published_tree_files: $published_tree_files,
      published_tree_bytes: $published_tree_bytes,
      published_svg_gzip_files: $published_svg_gzip_files,
      published_svg_gzip_bytes: $published_svg_gzip_bytes,
      derived_svg_gzip_files: $derived_svg_gzip_files,
      pdf_files: $pdf_files,
      png_files: $png_files,
      cahill_keyes_thumbnail_files: $thumbnail_files,
      manifest_payload_files: $payload_file_count,
      manifest_payload_bytes: $payload_byte_count,
      release_object_count: $release_object_count
    },
    integrity: {
      algorithm: "SHA-256",
      manifest: "SHA256SUMS",
      manifest_sha256: $manifest_sha256,
      manifest_excludes: ["SHA256SUMS", "release.json"]
    },
    delivery: {
      access: "public-read",
      cache_control: $cache_control,
      svg_gzip: {
        keys: "tree/svg/*.svg.gz",
        stored_form: "gzip",
        content_type: "application/gzip",
        content_encoding: null,
        browser_viewer: "viewer.html",
        browser_decompression: "DecompressionStream(\"gzip\")"
      },
      cahill_keyes_preview_png: {
        keys: "tree/thumbnail/cahill-keyes/*.png",
        content_type: "image/png",
        width: 480,
        height: 240,
        click_target: "viewer.html?asset=<name>.svg.gz"
      }
    }
  }' > "$release_path"

(
  cd -- "$release_root"
  sha256sum --check --quiet --strict SHA256SUMS
)
if ! jq -e \
  --argjson payload_file_count "$payload_file_count" \
  --argjson release_object_count "$release_object_count" \
  --arg manifest_sha256 "$manifest_sha256" \
  '.complete == true and
   .destination.prefix == "cartofreako/v12" and
   .inventory.manifest_payload_files == $payload_file_count and
   .inventory.release_object_count == $release_object_count and
   .integrity.manifest_sha256 == $manifest_sha256 and
   .delivery.access == "public-read" and
   .layout.svg_viewer == "viewer.html" and
   .delivery.svg_gzip.content_type == "application/gzip" and
   .delivery.svg_gzip.content_encoding == null and
   .delivery.cahill_keyes_preview_png.content_type == "image/png"' \
  "$release_path" >/dev/null; then
  printf 'Generated release.json failed its consistency check.\n' >&2
  exit 1
fi

mv -- "$release_root" "$output"
trap - EXIT HUP INT TERM
rm -rf -- "$work_root"

printf 'Built immutable S3 release tree: %s\n' "$output"
printf 'Objects: %s; stored bytes: %s; manifest payload objects: %s\n' \
  "$release_object_count" \
  "$(find "$output" -type f -printf '%s\n' | awk '{ total += $1 } END { printf "%.0f", total }')" \
  "$payload_file_count"
printf 'Destination encoded in release.json: adekosnik-bucket01/cartofreako/v12/\n'
