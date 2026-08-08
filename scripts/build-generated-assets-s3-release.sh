#!/usr/bin/env bash

set -Eeuo pipefail

readonly script_dir=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd -P)
readonly repository_root=$(cd -- "$script_dir/.." && pwd -P)
readonly default_archive=$repository_root/assets.generated.v13.tar.xz
readonly default_output=$repository_root/build/s3-release-v13
readonly readme_template=$repository_root/docs/releases/v13-s3-README.md.in
readonly viewer_source=$repository_root/docs/releases/v13-s3-viewer.html
readonly default_source_tag=v20260808.1
readonly release_name=v13
readonly package_name=assets.generated.v13.tar.xz
readonly endpoint=https://s3-ewh.ist.berkeley.edu
readonly region=us-east-1
readonly bucket=adekosnik-bucket01
readonly prefix=cartofreako/v13
readonly cache_control='public,max-age=31536000,immutable'
readonly -a projections=(
  cahill-keyes authagraph dymaxion myriahedral star-x voronoi
)
readonly expected_source_tree_files=909
readonly expected_svg_files=211
readonly expected_explicit_svg_gzip_files=84
readonly expected_pdf_files=211
readonly expected_png_files=211
readonly expected_thumbnail_files=192
readonly expected_published_tree_files=825
readonly expected_payload_files=828
readonly expected_release_objects=830

archive=$default_archive
output=$default_output
source_tag=$default_source_tag
source_commit=
source_published_at=

usage() {
  cat <<'EOF'
Usage: scripts/build-generated-assets-s3-release.sh [options]

Build and locally validate the immutable, projection-organized Cartofreako
v13 S3 object tree. The output directory must not already exist.

Options:
  --archive PATH                Override assets.generated.v13.tar.xz.
  --output PATH                 Override build/s3-release-v13.
  --source-tag TAG              Override v20260808.1.
  --source-commit SHA           Override the commit resolved from the tag.
  --source-published-at ISO8601 Record the GitHub release publication time.
  -h, --help                    Show this help.
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
    --source-tag)
      [[ $# -ge 2 ]] || { printf '%s requires a value.\n' "$1" >&2; exit 2; }
      source_tag=$2
      shift
      ;;
    --source-commit)
      [[ $# -ge 2 ]] || { printf '%s requires a value.\n' "$1" >&2; exit 2; }
      source_commit=$2
      shift
      ;;
    --source-published-at)
      [[ $# -ge 2 ]] || { printf '%s requires a value.\n' "$1" >&2; exit 2; }
      source_published_at=$2
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

for command_name in awk basename cmp cp date diff dirname find git grep gzip \
  jq ln mkdir mktemp mv rm sed sha256sum sort stat tar wc xz; do
  if ! command -v "$command_name" >/dev/null; then
    printf 'Missing required command: %s\n' "$command_name" >&2
    exit 1
  fi
done
if [[ ! $source_tag =~ ^v[0-9]{8}(\.[0-9]+)?$ ]]; then
  printf 'Source tag must use vYYYYMMDD or vYYYYMMDD.N: %s\n' \
    "$source_tag" >&2
  exit 2
fi
resolved_commit=$(git -C "$repository_root" rev-parse "$source_tag^{commit}" 2>/dev/null) || {
  printf 'Source tag does not resolve locally: %s\n' "$source_tag" >&2
  exit 1
}
if [[ -z $source_commit ]]; then
  source_commit=$resolved_commit
elif [[ $source_commit != "$resolved_commit" ]]; then
  printf 'Source commit does not match %s: %s != %s\n' \
    "$source_tag" "$source_commit" "$resolved_commit" >&2
  exit 1
fi
if [[ ! $source_commit =~ ^[0-9a-f]{40}$ ]]; then
  printf 'Source commit must be a full hexadecimal object ID.\n' >&2
  exit 2
fi
if [[ -z $source_published_at ]]; then
  source_published_at=$(date -u '+%Y-%m-%dT%H:%M:%SZ')
fi
if [[ ! $source_published_at =~ ^[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2}Z$ ]]; then
  printf 'Invalid --source-published-at ISO-8601 UTC timestamp.\n' >&2
  exit 2
fi
for required_path in "$archive" "$readme_template" "$viewer_source"; do
  if [[ ! -f $required_path ]]; then
    printf 'Required release input not found: %s\n' "$required_path" >&2
    exit 1
  fi
done
if [[ -e $output ]]; then
  printf 'Output already exists: %s\n' "$output" >&2
  printf 'Move it aside or select another --output; nothing was replaced.\n' >&2
  exit 1
fi

archive=$(cd -- "$(dirname -- "$archive")" && pwd -P)/$(basename -- "$archive")
output_parent=$(dirname -- "$output")
mkdir -p -- "$output_parent"
output_parent=$(cd -- "$output_parent" && pwd -P)
output=$output_parent/$(basename -- "$output")
work_root=$(mktemp -d "$output_parent/.s3-release-v13.XXXXXX")
extract_root=$work_root/extracted
release_root=$work_root/release
listing_path=$work_root/archive-paths.txt
actual_projection_paths=$work_root/projection-paths.txt
expected_projection_paths=$work_root/expected-projection-paths.txt

cleanup() {
  rm -rf -- "$work_root"
}
trap cleanup EXIT HUP INT TERM

archive_sha256=$(sha256sum -- "$archive" | awk '{print $1}')
archive_bytes=$(stat -c '%s' -- "$archive")
printf 'Verifying v13 archive %s (%s bytes)...\n' \
  "$archive_sha256" "$archive_bytes"
xz --test -- "$archive"
tar --list --file="$archive" > "$listing_path"
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

mkdir -p -- "$extract_root" "$release_root/tree" "$release_root/package"
tar --extract --xz --file="$archive" --directory="$extract_root" \
  --no-same-owner --no-same-permissions
source_tree=$extract_root/assets.generated
if [[ ! -d $source_tree ]]; then
  printf 'Archive lacks its required assets.generated/ root.\n' >&2
  exit 1
fi
if find "$source_tree" -type l -print -quit | grep -q .; then
  printf 'Symlinks are not allowed in the generated-assets tree.\n' >&2
  exit 1
fi
if find "$source_tree" -type f -size 0 -print -quit | grep -q .; then
  printf 'Zero-byte files are not allowed in the generated-assets tree.\n' >&2
  exit 1
fi
printf '%s\n' "${projections[@]}" | LC_ALL=C sort > "$expected_projection_paths"
find "$source_tree" -mindepth 1 -maxdepth 1 -type d -printf '%f\n' | \
  LC_ALL=C sort > "$actual_projection_paths"
if ! cmp -s -- "$expected_projection_paths" "$actual_projection_paths"; then
  printf 'Projection directories do not match the v13 contract.\n' >&2
  diff -u "$expected_projection_paths" "$actual_projection_paths" >&2 || true
  exit 1
fi
if find "$source_tree" -mindepth 1 -maxdepth 1 ! -type d -print -quit | grep -q .; then
  printf 'The assets.generated root may contain only projection directories.\n' >&2
  exit 1
fi
for projection in "${projections[@]}"; do
  for format in svg pdf png thumbnail; do
    if [[ ! -d $source_tree/$projection/$format ]]; then
      printf 'Missing projection format directory: %s/%s\n' \
        "$projection" "$format" >&2
      exit 1
    fi
  done
  thumbnail_count=$(find "$source_tree/$projection/thumbnail" -maxdepth 1 \
    -type f -name '*.png' | wc -l)
  if [[ $thumbnail_count -ne 32 ]]; then
    printf '%s has %s thumbnails; expected 32.\n' \
      "$projection" "$thumbnail_count" >&2
    exit 1
  fi
  for required_stem in cloud-atmosphere fiber-synthesized; do
    for format in svg pdf png thumbnail; do
      extension=$format
      [[ $format == thumbnail ]] && extension=png
      required_count=$(find "$source_tree/$projection/$format" -maxdepth 1 \
        -type f -name "$required_stem-*.$extension" | wc -l)
      if [[ $required_count -ne 1 ]]; then
        printf '%s/%s has %s %s products; expected exactly one.\n' \
          "$projection" "$format" "$required_count" "$required_stem" >&2
        exit 1
      fi
    done
  done
done

tree_files=$(find "$source_tree" -type f | wc -l)
tree_bytes=$(find "$source_tree" -type f -printf '%s\n' | \
  awk '{ total += $1 } END { printf "%.0f", total }')
svg_files=$(find "$source_tree" -path '*/svg/*.svg' -type f | wc -l)
svg_gzip_files=$(find "$source_tree" -path '*/svg/*.svg.gz' -type f | wc -l)
pdf_files=$(find "$source_tree" -path '*/pdf/*.pdf' -type f | wc -l)
png_files=$(find "$source_tree" -path '*/png/*.png' -type f | wc -l)
thumbnail_files=$(find "$source_tree" -path '*/thumbnail/*.png' -type f | wc -l)
if [[ $tree_files -ne $expected_source_tree_files ||
      $svg_files -ne $expected_svg_files ||
      $svg_gzip_files -ne $expected_explicit_svg_gzip_files ||
      $pdf_files -ne $expected_pdf_files ||
      $png_files -ne $expected_png_files ||
      $thumbnail_files -ne $expected_thumbnail_files ]]; then
  printf 'Unexpected archive inventory: files=%s svg=%s svg.gz=%s pdf=%s png=%s thumbnails=%s\n' \
    "$tree_files" "$svg_files" "$svg_gzip_files" "$pdf_files" \
    "$png_files" "$thumbnail_files" >&2
  exit 1
fi

printf 'Checking explicit resource SVG gzip members...\n'
while IFS= read -r -d '' gzip_path; do
  gzip --test -- "$gzip_path"
  gzip --decompress --stdout -- "$gzip_path" | \
    cmp --silent -- - "${gzip_path%.gz}"
done < <(find "$source_tree" -path '*/svg/*.svg.gz' -type f -print0 | \
  LC_ALL=C sort -z)

printf 'Constructing the browser tree with explicit SVG gzip objects...\n'
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
done < <(find "$release_root/tree" -path '*/svg/*.svg' -type f -print0 | \
  LC_ALL=C sort -z)

while IFS= read -r -d '' gzip_path; do
  relative_path=${gzip_path#"$release_root/tree/"}
  source_path=$source_tree/${relative_path%.gz}
  gzip --test -- "$gzip_path"
  gzip --decompress --stdout -- "$gzip_path" | \
    cmp --silent -- - "$source_path"
done < <(find "$release_root/tree" -path '*/svg/*.svg.gz' -type f -print0 | \
  LC_ALL=C sort -z)

published_tree_files=$(find "$release_root/tree" -type f | wc -l)
published_svg_files=$(find "$release_root/tree" -path '*/svg/*.svg' \
  -type f | wc -l)
published_svg_gzip_files=$(find "$release_root/tree" -path '*/svg/*.svg.gz' \
  -type f | wc -l)
if [[ $published_tree_files -ne $expected_published_tree_files ||
      $published_svg_files -ne 0 ||
      $published_svg_gzip_files -ne $expected_svg_files ]]; then
  printf 'Unexpected published tree: files=%s raw-svg=%s svg.gz=%s\n' \
    "$published_tree_files" "$published_svg_files" \
    "$published_svg_gzip_files" >&2
  exit 1
fi

package_path=$release_root/package/$package_name
if ! ln -- "$archive" "$package_path" 2>/dev/null; then
  cp --archive --reflink=auto -- "$archive" "$package_path"
fi
cp -- "$viewer_source" "$release_root/viewer.html"

payload_file_count=$expected_payload_files
release_object_count=$expected_release_objects
sed \
  -e "s|@@SOURCE_TAG@@|$source_tag|g" \
  -e "s|@@SOURCE_COMMIT@@|$source_commit|g" \
  -e "s|@@SOURCE_TREE_FILES@@|$tree_files|g" \
  -e "s|@@RELEASE_OBJECTS@@|$release_object_count|g" \
  -e "s|@@PAYLOAD_FILES@@|$payload_file_count|g" \
  -e "s|@@ARCHIVE_SHA256@@|$archive_sha256|g" \
  "$readme_template" > "$release_root/README.md"
if grep -Eq '@@[A-Z0-9_]+@@' "$release_root/README.md"; then
  printf 'Unresolved placeholder remains in the v13 S3 README.\n' >&2
  exit 1
fi

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
release_object_count=$((payload_file_count + 2))
if [[ $payload_file_count -ne $expected_payload_files ||
      $release_object_count -ne $expected_release_objects ]]; then
  printf 'Unexpected release counts: payload=%s objects=%s\n' \
    "$payload_file_count" "$release_object_count" >&2
  exit 1
fi
payload_byte_count=$(find "$release_root" -type f ! -path "$manifest_path" \
  ! -path "$release_path" -printf '%s\n' | \
  awk '{ total += $1 } END { printf "%.0f", total }')
published_tree_bytes=$(find "$release_root/tree" -type f -printf '%s\n' | \
  awk '{ total += $1 } END { printf "%.0f", total }')
published_svg_gzip_bytes=$(find "$release_root/tree" \
  -path '*/svg/*.svg.gz' -type f -printf '%s\n' | \
  awk '{ total += $1 } END { printf "%.0f", total }')
manifest_sha256=$(sha256sum -- "$manifest_path" | awk '{print $1}')

jq -n \
  --arg source_tag "$source_tag" \
  --arg source_commit "$source_commit" \
  --arg source_published_at "$source_published_at" \
  --arg archive_sha256 "$archive_sha256" \
  --arg manifest_sha256 "$manifest_sha256" \
  --arg cache_control "$cache_control" \
  --argjson archive_bytes "$archive_bytes" \
  --argjson source_tree_files "$tree_files" \
  --argjson source_tree_bytes "$tree_bytes" \
  --argjson published_tree_files "$published_tree_files" \
  --argjson published_tree_bytes "$published_tree_bytes" \
  --argjson published_svg_gzip_bytes "$published_svg_gzip_bytes" \
  --argjson payload_file_count "$payload_file_count" \
  --argjson payload_byte_count "$payload_byte_count" \
  --argjson release_object_count "$release_object_count" \
  '{
    schema_version: 2,
    dataset: "cartofreako-generated-assets",
    release: "v13",
    stage: 13,
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
      prefix: "cartofreako/v13"
    },
    layout: {
      archive_root: "assets.generated/",
      organization: "projection/format/artifact",
      projections: ["cahill-keyes", "authagraph", "dymaxion", "myriahedral", "star-x", "voronoi"],
      formats: ["svg", "pdf", "png", "thumbnail"],
      published_tree_root: "tree/",
      recovery_package: "package/assets.generated.v13.tar.xz",
      svg_viewer: "viewer.html"
    },
    package: {bytes: $archive_bytes, sha256: $archive_sha256},
    inventory: {
      source_tree_files: $source_tree_files,
      source_tree_bytes: $source_tree_bytes,
      source_svg_files: 211,
      source_explicit_svg_gzip_files: 84,
      published_tree_files: $published_tree_files,
      published_tree_bytes: $published_tree_bytes,
      published_svg_gzip_files: 211,
      published_svg_gzip_bytes: $published_svg_gzip_bytes,
      derived_svg_gzip_files: 127,
      pdf_files: 211,
      png_files: 211,
      thumbnail_files: 192,
      thumbnails_per_projection: 32,
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
        keys: "tree/<projection>/svg/*.svg.gz",
        stored_form: "gzip",
        content_type: "application/gzip",
        content_encoding: null,
        browser_viewer: "viewer.html",
        browser_decompression: "DecompressionStream(\"gzip\")"
      },
      preview_png: {
        keys: "tree/<projection>/thumbnail/*.png",
        content_type: "image/png",
        width: 480,
        click_target: "viewer.html?asset=<projection>/svg/<name>.svg.gz"
      }
    }
  }' > "$release_path"

(
  cd -- "$release_root"
  sha256sum --check --quiet --strict SHA256SUMS
)
if ! jq -e \
  --arg tag "$source_tag" --arg commit "$source_commit" \
  --arg archive_sha256 "$archive_sha256" \
  --arg manifest_sha256 "$manifest_sha256" \
  '.complete == true and .release == "v13" and .stage == 13 and
   .source.tag == $tag and .source.commit == $commit and
   .destination.prefix == "cartofreako/v13" and
   .layout.organization == "projection/format/artifact" and
   .package.sha256 == $archive_sha256 and
   .inventory.source_tree_files == 909 and
   .inventory.published_tree_files == 825 and
   .inventory.thumbnail_files == 192 and
   .inventory.thumbnails_per_projection == 32 and
   .inventory.manifest_payload_files == 828 and
   .inventory.release_object_count == 830 and
   .integrity.manifest_sha256 == $manifest_sha256 and
   .delivery.svg_gzip.content_type == "application/gzip" and
   .delivery.svg_gzip.content_encoding == null and
   .delivery.preview_png.content_type == "image/png"' \
  "$release_path" >/dev/null; then
  printf 'Generated release.json failed its consistency check.\n' >&2
  exit 1
fi

mv -- "$release_root" "$output"
trap - EXIT HUP INT TERM
rm -rf -- "$work_root"

printf 'Built immutable S3 release tree: %s\n' "$output"
printf 'Objects: %s; source files: %s; projection thumbnails: %s\n' \
  "$release_object_count" "$tree_files" "$thumbnail_files"
printf 'Destination encoded in release.json: %s/%s/\n' "$bucket" "$prefix"
