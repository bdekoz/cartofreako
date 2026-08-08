#!/usr/bin/env bash

set -Eeuo pipefail
set +x

readonly uploader_version=6
readonly script_dir=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd -P)
readonly repository_root=$(cd -- "$script_dir/.." && pwd -P)
readonly report_builder=$script_dir/build-generated-assets-s3-report.sh
readonly default_data_root=$repository_root/build/s3-release-v13
readonly default_endpoint=https://s3-ewh.ist.berkeley.edu
readonly default_region=us-east-1
readonly default_bucket=adekosnik-bucket01
readonly default_prefix=cartofreako/v13
readonly cache_control='public,max-age=31536000,immutable'
readonly -a projections=(
  cahill-keyes authagraph dymaxion myriahedral star-x voronoi
)

data_root=$default_data_root
endpoint=$default_endpoint
region=$default_region
bucket=$default_bucket
prefix=$default_prefix
apply_upload=false
verify_download=false
validate_only=false
compose_report_email=true
run_id=$(date -u '+%Y%m%dT%H%M%SZ')

usage() {
  cat <<'EOF'
Usage: scripts/upload-generated-assets-s3-release.sh [options]

Validate, dry-run, and optionally publish the immutable Cartofreako v13 object
release through rclone's ephemeral S3 backend. Credentials are read silently
from /dev/tty, exported only for this process, and never persisted. A completed
applied run also builds the Devastation Pacific Active Archive report.

Options:
  --apply              Upload after the dry run and exact-prefix confirmation.
  --verify-download    Read every remote object back after normal verification.
  --validate-only      Validate local release files without network or credentials.
  --skip-report-email  Do not open the verified report in the desktop mailer.
  --data-root PATH     Override build/s3-release-v13.
  --endpoint URL       Override the S3 endpoint.
  --region NAME        Override the S3 signing region.
  --bucket NAME        Override the bucket.
  --prefix PATH        Override the object-key prefix.
  -h, --help           Show this help.
EOF
}

format_bytes() {
  awk -v bytes="$1" 'BEGIN {
    split("B KiB MiB GiB TiB", units, " ")
    value = bytes + 0
    unit = 1
    while (value >= 1024 && unit < 5) {
      value /= 1024
      unit++
    }
    if (unit == 1) {
      printf "%.0f %s", value, units[unit]
    } else {
      printf "%.2f %s", value, units[unit]
    }
  }'
}

while (( $# > 0 )); do
  case $1 in
    --apply)
      apply_upload=true
      ;;
    --verify-download)
      verify_download=true
      ;;
    --validate-only)
      validate_only=true
      ;;
    --skip-report-email)
      compose_report_email=false
      ;;
    --data-root)
      [[ $# -ge 2 ]] || { printf '%s requires a value.\n' "$1" >&2; exit 2; }
      data_root=$2
      shift
      ;;
    --endpoint)
      [[ $# -ge 2 ]] || { printf '%s requires a value.\n' "$1" >&2; exit 2; }
      endpoint=$2
      shift
      ;;
    --region)
      [[ $# -ge 2 ]] || { printf '%s requires a value.\n' "$1" >&2; exit 2; }
      region=$2
      shift
      ;;
    --bucket)
      [[ $# -ge 2 ]] || { printf '%s requires a value.\n' "$1" >&2; exit 2; }
      bucket=$2
      shift
      ;;
    --prefix)
      [[ $# -ge 2 ]] || { printf '%s requires a value.\n' "$1" >&2; exit 2; }
      prefix=$2
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

if (( EUID == 0 )); then
  printf 'Do not run the uploader as root.\n' >&2
  exit 1
fi
for command_name in awk cmp comm curl diff find git grep gzip jq mktemp rclone \
  sed sha256sum sort stat tr wc xargs; do
  if ! command -v "$command_name" >/dev/null; then
    printf 'Missing required command: %s\n' "$command_name" >&2
    exit 1
  fi
done
if [[ ! -d $data_root ]]; then
  printf 'Release directory not found: %s\n' "$data_root" >&2
  printf 'Run scripts/build-generated-assets-s3-release.sh first.\n' >&2
  exit 1
fi
if [[ ! -x $report_builder ]]; then
  printf 'Active Archive report builder is unavailable: %s\n' \
    "$report_builder" >&2
  exit 1
fi
if [[ $apply_upload == true && $compose_report_email == true ]] &&
   ! command -v xdg-email >/dev/null; then
  printf 'xdg-email is required for the post-upload report handoff.\n' >&2
  printf 'Install it or use --skip-report-email for a headless run.\n' >&2
  exit 1
fi
if [[ $endpoint != https://* || $endpoint == *[$'\r\n']* ]]; then
  printf 'The endpoint must be a single-line HTTPS URL.\n' >&2
  exit 2
fi
endpoint=${endpoint%/}
if [[ ! $region =~ ^[A-Za-z0-9][A-Za-z0-9._-]*$ ]]; then
  printf 'Invalid S3 signing region: %s\n' "$region" >&2
  exit 2
fi
if [[ ! $bucket =~ ^[a-z0-9][a-z0-9.-]{1,61}[a-z0-9]$ ]]; then
  printf 'Invalid S3 bucket name: %s\n' "$bucket" >&2
  exit 2
fi
prefix=${prefix#/}
prefix=${prefix%/}
if [[ -z $prefix || $prefix == *'..'* || $prefix == *'//'* ||
      $prefix == *[$'\r\n']* ]]; then
  printf 'Unsafe or empty S3 prefix: %s\n' "$prefix" >&2
  exit 2
fi

readonly destination_label=$bucket/$prefix/
# The trailing slash is deliberate. Rclone otherwise probes the remote root as
# a possible object with HEAD; Berkeley's Cloudian service returns HTTP 500
# instead of 404 when that object is absent on a brand-new prefix.
readonly remote_path=:s3:$bucket/$prefix/
readonly public_base=$endpoint/$bucket/$prefix

printf 'Cartofreako S3 uploader %s (run %s)\n' "$uploader_version" "$run_id"
if [[ $validate_only != true ]]; then
  printf 'Checking HTTPS reachability to %s...\n' "$endpoint"
  if ! curl --connect-timeout 8 --max-time 12 --silent --show-error \
    --output /dev/null "$endpoint/"; then
    printf '[error] The S3 endpoint is not reachable over HTTPS.\n' >&2
    printf 'No credentials were requested and no S3 operation was attempted.\n' >&2
    exit 1
  fi
  printf '[ok] The S3 endpoint responded over HTTPS.\n'
fi

printf 'Validating local release structure...\n'
for required_path in README.md viewer.html SHA256SUMS release.json \
  package/assets.generated.v13.tar.xz tree; do
  if [[ ! -e $data_root/$required_path ]]; then
    printf 'Missing release artifact: %s\n' "$required_path" >&2
    exit 1
  fi
done
for projection in "${projections[@]}"; do
  for format in svg pdf png thumbnail; do
    if [[ ! -d $data_root/tree/$projection/$format ]]; then
      printf 'Missing projection format directory: tree/%s/%s\n' \
        "$projection" "$format" >&2
      exit 1
    fi
  done
done
if find "$data_root" -type l -print -quit | grep -q .; then
  printf 'Symlinks are not allowed beneath the release directory.\n' >&2
  exit 1
fi
if find "$data_root" -type f -size 0 -print -quit | grep -q .; then
  printf 'Zero-byte files are not allowed beneath the release directory.\n' >&2
  exit 1
fi
if find "$data_root" -type f \( -name '*.tmp' -o -name '*.partial' \) \
  -print -quit | grep -q .; then
  printf 'Temporary files remain beneath the release directory.\n' >&2
  exit 1
fi

local_paths=$(mktemp)
manifest_paths=$(mktemp)
release_paths=$(mktemp)
remote_paths=$(mktemp)
unexpected_remote_paths=$(mktemp)
empty_config=$(mktemp)
public_svg_body=$(mktemp)
public_png_body=$(mktemp)
public_headers=$(mktemp)
public_png_headers=$(mktemp)
public_viewer=$(mktemp)
public_viewer_headers=$(mktemp)
public_release=$(mktemp)
log_dir=${TMPDIR:-/tmp}/cartofreako-upload-logs
mkdir -p -- "$log_dir"
chmod 700 -- "$log_dir"
log_file=$log_dir/upload-$run_id.log
chmod 600 -- "$empty_config"

cleanup() {
  unset AWS_ACCESS_KEY_ID AWS_SECRET_ACCESS_KEY AWS_SESSION_TOKEN
  rm -f -- "$local_paths" "$manifest_paths" "$release_paths" \
    "$remote_paths" "$unexpected_remote_paths" "$empty_config" \
    "$public_svg_body" "$public_png_body" "$public_headers" \
    "$public_png_headers" "$public_viewer" "$public_viewer_headers" \
    "$public_release"
}
trap cleanup EXIT HUP INT TERM

LC_ALL=C find "$data_root" -type f ! -name SHA256SUMS ! -name release.json \
  -printf '%P\n' | LC_ALL=C sort > "$local_paths"
LC_ALL=C find "$data_root" -type f -printf '%P\n' | \
  LC_ALL=C sort > "$release_paths"
awk '{ sub(/^[[:xdigit:]]+[[:space:]][ *]/, ""); print }' \
  "$data_root/SHA256SUMS" | LC_ALL=C sort > "$manifest_paths"
if ! cmp -s -- "$local_paths" "$manifest_paths"; then
  printf 'SHA256SUMS path inventory does not match the payload files.\n' >&2
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
thumbnail_count=$(find "$data_root/tree" -type f \
  -path '*/thumbnail/*.png' | wc -l)
if [[ $tree_file_count -ne 825 || $raw_svg_count -ne 0 ||
      $svg_gzip_count -ne 211 || $pdf_count -ne 211 ||
      $png_count -ne 211 || $thumbnail_count -ne 192 ]]; then
  printf 'Unexpected release inventory: tree=%s svg=%s svg.gz=%s pdf=%s png=%s thumbnails=%s\n' \
    "$tree_file_count" "$raw_svg_count" "$svg_gzip_count" \
    "$pdf_count" "$png_count" "$thumbnail_count" >&2
  exit 1
fi
for projection in "${projections[@]}"; do
  projection_thumbnail_count=$(find "$data_root/tree/$projection/thumbnail" \
    -maxdepth 1 -type f -name '*.png' | wc -l)
  if [[ $projection_thumbnail_count -ne 32 ]]; then
    printf 'Unexpected %s thumbnail count: %s; expected 32.\n' \
      "$projection" "$projection_thumbnail_count" >&2
    exit 1
  fi
  for required_stem in cloud-atmosphere fiber-synthesized; do
    for format in svg pdf png thumbnail; do
      extension=$format
      [[ $format == svg ]] && extension=svg.gz
      [[ $format == thumbnail ]] && extension=png
      required_count=$(find "$data_root/tree/$projection/$format" -maxdepth 1 \
        -type f -name "$required_stem-*.$extension" | wc -l)
      if [[ $required_count -ne 1 ]]; then
        printf 'Unexpected %s/%s %s count: %s; expected one.\n' \
          "$projection" "$format" "$required_stem" "$required_count" >&2
        exit 1
      fi
    done
  done
done

payload_count=$(wc -l < "$local_paths")
release_count=$(wc -l < "$release_paths")
release_bytes=$(find "$data_root" -type f -printf '%s\n' | \
  awk '{ total += $1 } END { printf "%.0f", total }')
general_upload_count=$(find "$data_root" -type f \
  ! -path "$data_root/tree/*/svg/*" \
  ! -name release.json | wc -l)
general_upload_bytes=$(find "$data_root" -type f \
  ! -path "$data_root/tree/*/svg/*" \
  ! -name release.json -printf '%s\n' | \
  awk '{ total += $1 } END { printf "%.0f", total }')
svg_gzip_bytes=$(find "$data_root/tree" -type f \
  -path '*/svg/*.svg.gz' -printf '%s\n' | \
  awk '{ total += $1 } END { printf "%.0f", total }')
if [[ $payload_count -ne 828 || $release_count -ne 830 ||
      $general_upload_count -ne 618 ]]; then
  printf 'Unexpected publication counts: payload=%s release=%s general=%s\n' \
    "$payload_count" "$release_count" "$general_upload_count" >&2
  exit 1
fi
manifest_sha256=$(sha256sum "$data_root/SHA256SUMS" | awk '{print $1}')
package_sha256=$(sha256sum "$data_root/package/assets.generated.v13.tar.xz" | \
  awk '{print $1}')
source_tag=$(jq -r '.source.tag' "$data_root/release.json")
source_commit=$(jq -r '.source.commit' "$data_root/release.json")
if [[ ! $source_tag =~ ^v[0-9]{8}(\.[0-9]+)?$ ||
      ! $source_commit =~ ^[0-9a-f]{40}$ ||
      $(git -C "$repository_root" rev-parse "$source_tag^{commit}" 2>/dev/null || true) != "$source_commit" ]]; then
  printf 'The staged source tag and commit do not resolve to the same local commit.\n' >&2
  exit 1
fi

if ! jq -e \
  --arg endpoint "$endpoint" --arg region "$region" --arg bucket "$bucket" \
  --arg prefix "$prefix" --arg manifest_sha256 "$manifest_sha256" \
  --arg package_sha256 "$package_sha256" \
  --arg source_tag "$source_tag" --arg source_commit "$source_commit" \
  --argjson payload_count "$payload_count" \
  --argjson release_count "$release_count" \
  '.complete == true and
   .release == "v13" and .stage == 13 and
   .source.tag == $source_tag and .source.commit == $source_commit and
   .destination.endpoint == $endpoint and
   .destination.region == $region and
   .destination.bucket == $bucket and
   .destination.prefix == $prefix and
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
  printf 'release.json does not agree with the local tree or destination.\n' >&2
  exit 1
fi

printf 'Local validation passed: %s files, %s bytes.\n' \
  "$release_count" "$release_bytes"
printf 'Destination: %s\n' "$destination_label"
printf 'Public base: %s/\n' "$public_base"
printf 'Upload phases:\n'
printf '  package, documents, PDF, and PNG: %s files, %s\n' \
  "$general_upload_count" "$(format_bytes "$general_upload_bytes")"
printf '  explicit SVG gzip:                %s files, %s\n' \
  "$svg_gzip_count" "$(format_bytes "$svg_gzip_bytes")"
printf '  completion marker: release.json (uploaded last)\n'
printf 'Sanitized rclone log: %s\n' "$log_file"

if [[ $validate_only == true ]]; then
  printf 'Local-only validation complete; no network request was made.\n'
  exit 0
fi
if [[ ! -r /dev/tty || ! -w /dev/tty ]]; then
  printf 'An interactive terminal is required for credentials.\n' >&2
  exit 2
fi

printf 'S3 access-key ID: ' >/dev/tty
IFS= read -r -s AWS_ACCESS_KEY_ID </dev/tty
printf '\nS3 secret access key: ' >/dev/tty
IFS= read -r -s AWS_SECRET_ACCESS_KEY </dev/tty
printf '\nOptional session token (Enter for none): ' >/dev/tty
IFS= read -r -s AWS_SESSION_TOKEN </dev/tty
printf '\n' >/dev/tty
if [[ -z $AWS_ACCESS_KEY_ID || -z $AWS_SECRET_ACCESS_KEY ]]; then
  printf 'Both the access-key ID and secret access key are required.\n' >&2
  exit 2
fi
export AWS_ACCESS_KEY_ID AWS_SECRET_ACCESS_KEY
if [[ -n $AWS_SESSION_TOKEN ]]; then
  export AWS_SESSION_TOKEN
else
  unset AWS_SESSION_TOKEN
fi

readonly -a rclone_common=(
  --config "$empty_config"
  --s3-provider Other
  --s3-env-auth
  --s3-endpoint "$endpoint"
  --s3-region "$region"
  --s3-force-path-style
  --s3-no-check-bucket
  --s3-acl public-read
  --transfers 4
  --checkers 8
  --log-file "$log_file"
  --log-level INFO
)
readonly -a rclone_progress=(
  --progress
  --stats 5s
  --stats-one-line-date
  --stats-unit bytes
  --stats-file-name-length 72
)
readonly -a rclone_probe=(
  --contimeout 8s
  --timeout 15s
  --retries 1
  --low-level-retries 1
)
readonly -a copy_safety=(--checksum --immutable --check-first)

printf 'Testing access to the exact bucket and prefix...\n'
if ! rclone lsf "$remote_path" --max-depth 1 \
  "${rclone_common[@]}" "${rclone_probe[@]}" >/dev/null; then
  printf '[error] Quick access check failed for %s\n' "$destination_label" >&2
  printf 'See the sanitized rclone log: %s\n' "$log_file" >&2
  exit 1
fi
printf '[ok] Read access confirmed for %s\n' "$destination_label"

printf 'Reading the complete remote-prefix inventory...\n'
rclone lsf "$remote_path" --recursive --files-only "${rclone_common[@]}" \
  --fast-list | LC_ALL=C sort > "$remote_paths"
remote_existing_count=$(wc -l < "$remote_paths")
printf '[ok] Remote inventory read: %s existing objects at the prefix.\n' \
  "$remote_existing_count"
prefix_complete=false
if grep -Fqx 'release.json' "$remote_paths"; then
  prefix_complete=true
fi
LC_ALL=C comm -13 "$release_paths" "$remote_paths" > "$unexpected_remote_paths"
if [[ -s $unexpected_remote_paths ]]; then
  printf 'The destination contains objects not present in this release.\n' >&2
  printf 'Nothing was deleted. Unexpected remote paths (first 40):\n' >&2
  sed -n '1,40p' "$unexpected_remote_paths" >&2
  exit 1
fi
if [[ $prefix_complete == true &&
      -n $(LC_ALL=C comm -23 "$release_paths" "$remote_paths" | sed -n '1p') ]]; then
  printf 'The completion marker exists, but the prefix is missing release objects.\n' >&2
  printf 'The immutable prefix will not be repaired in place.\n' >&2
  exit 1
fi

printf '[dry run 1/2] Planning package, documents, viewer, PDF, and PNG objects...\n'
rclone copy "$data_root" "$remote_path" \
  "${rclone_common[@]}" "${rclone_progress[@]}" "${copy_safety[@]}" \
  --dry-run --exclude '/tree/*/svg/**' --exclude '/release.json' \
  --header-upload "Cache-Control: $cache_control"
printf '[ok] General-object dry run finished.\n'
printf '[dry run 2/2] Planning explicit SVG gzip objects...\n'
rclone copy "$data_root" "$remote_path" \
  "${rclone_common[@]}" "${rclone_progress[@]}" "${copy_safety[@]}" \
  --dry-run --include '/tree/*/svg/*.svg.gz' \
  --header-upload 'Content-Type: application/gzip' \
  --header-upload "Cache-Control: $cache_control"
printf '[ok] Explicit-gzip dry run finished.\n'

if [[ $apply_upload != true ]]; then
  printf 'Dry run complete; no remote objects were changed.\n'
  printf 'Rerun with --apply to upload.\n'
  exit 0
fi

printf 'Type the full destination to authorize the upload:\n  %s\n> ' \
  "$destination_label" >/dev/tty
IFS= read -r confirmation </dev/tty
if [[ $confirmation != "$destination_label" ]]; then
  printf 'Destination confirmation did not match; upload cancelled.\n' >&2
  exit 2
fi

svg_pilot=tree/cahill-keyes/svg/geometry-ck-44-22.svg.gz
png_pilot=tree/cahill-keyes/thumbnail/geometry-ck-44-22.png
printf '[stage 1/10] Uploading two browser-facing pilot objects...\n'
rclone copy "$data_root" "$remote_path" \
  "${rclone_common[@]}" "${rclone_progress[@]}" "${copy_safety[@]}" \
  --include "/$svg_pilot" \
  --header-upload 'Content-Type: application/gzip' \
  --header-upload "Cache-Control: $cache_control"
rclone copy "$data_root" "$remote_path" \
  "${rclone_common[@]}" "${rclone_progress[@]}" "${copy_safety[@]}" \
  --include "/$png_pilot" \
  --header-upload 'Content-Type: image/png' \
  --header-upload "Cache-Control: $cache_control"

svg_pilot_metadata=$(rclone lsjson "$remote_path$svg_pilot" --stat --metadata \
  "${rclone_common[@]}")
png_pilot_metadata=$(rclone lsjson "$remote_path$png_pilot" --stat --metadata \
  "${rclone_common[@]}")
if ! jq -e \
  '.MimeType == "application/gzip" and
   .Metadata["cache-control"] == "public,max-age=31536000,immutable" and
   ((.Metadata["content-encoding"] // "") == "")' \
  <<<"$svg_pilot_metadata" >/dev/null; then
  if [[ $prefix_complete == true ]]; then
    printf 'A completed release has incorrect SVG pilot metadata; refusing to mutate it.\n' >&2
    exit 1
  fi
  printf '[repair] Refreshing metadata on the incomplete-prefix SVG pilot...\n'
  rclone copy "$data_root" "$remote_path" \
    "${rclone_common[@]}" "${rclone_progress[@]}" --ignore-times \
    --include "/$svg_pilot" \
    --header-upload 'Content-Type: application/gzip' \
    --header-upload "Cache-Control: $cache_control"
  svg_pilot_metadata=$(rclone lsjson "$remote_path$svg_pilot" --stat --metadata \
    "${rclone_common[@]}")
fi

if ! jq -e \
  '.MimeType == "image/png" and
   .Metadata["cache-control"] == "public,max-age=31536000,immutable" and
   ((.Metadata["content-encoding"] // "") == "")' \
  <<<"$png_pilot_metadata" >/dev/null; then
  if [[ $prefix_complete == true ]]; then
    printf 'A completed release has incorrect PNG pilot metadata; refusing to mutate it.\n' >&2
    exit 1
  fi
  printf '[repair] Refreshing metadata on the incomplete-prefix PNG pilot...\n'
  rclone copy "$data_root" "$remote_path" \
    "${rclone_common[@]}" "${rclone_progress[@]}" --ignore-times \
    --include "/$png_pilot" \
    --header-upload 'Content-Type: image/png' \
    --header-upload "Cache-Control: $cache_control"
  png_pilot_metadata=$(rclone lsjson "$remote_path$png_pilot" --stat --metadata \
    "${rclone_common[@]}")
fi

if ! jq -e \
  '.MimeType == "application/gzip" and
   .Metadata["cache-control"] == "public,max-age=31536000,immutable" and
   ((.Metadata["content-encoding"] // "") == "")' \
  <<<"$svg_pilot_metadata" >/dev/null ||
  ! jq -e \
  '.MimeType == "image/png" and
   .Metadata["cache-control"] == "public,max-age=31536000,immutable" and
   ((.Metadata["content-encoding"] // "") == "")' \
  <<<"$png_pilot_metadata" >/dev/null; then
  printf 'Pilot metadata is still incorrect after guarded refresh.\n' >&2
  printf 'SVG metadata: %s\n' \
    "$(jq -c '{MimeType, Metadata}' <<<"$svg_pilot_metadata")" >&2
  printf 'PNG metadata: %s\n' \
    "$(jq -c '{MimeType, Metadata}' <<<"$png_pilot_metadata")" >&2
  exit 1
fi

printf '[stage 2/10] Verifying anonymous browser delivery of both pilots...\n'
if ! curl --connect-timeout 8 --max-time 60 --fail --silent --show-error \
  --location --dump-header "$public_headers" \
  --output "$public_svg_body" "$public_base/$svg_pilot"; then
  printf 'The SVG gzip pilot is not anonymously readable; upload stopped.\n' >&2
  printf 'The bucket must permit the public-read object ACL.\n' >&2
  exit 1
fi
if ! cmp --silent -- "$data_root/$svg_pilot" "$public_svg_body"; then
  printf 'The public SVG gzip pilot bytes differ from the local release.\n' >&2
  exit 1
fi
if tr -d '\r' < "$public_headers" | grep -qi '^content-encoding:'; then
  printf 'The explicit SVG gzip response unexpectedly has Content-Encoding.\n' >&2
  exit 1
fi
if ! tr -d '\r' < "$public_headers" | \
  grep -Eqi '^content-type:[[:space:]]*application/gzip([[:space:]]*;|[[:space:]]*$)'; then
  printf 'The public SVG gzip response lacks Content-Type: application/gzip.\n' >&2
  exit 1
fi
if ! curl --connect-timeout 8 --max-time 60 --fail --silent --show-error \
  --location --dump-header "$public_png_headers" \
  --output "$public_png_body" "$public_base/$png_pilot"; then
  printf 'The PNG pilot is not anonymously readable; upload stopped.\n' >&2
  exit 1
fi
if ! cmp --silent -- "$data_root/$png_pilot" "$public_png_body"; then
  printf 'The public PNG pilot bytes differ from the local release.\n' >&2
  exit 1
fi
if ! tr -d '\r' < "$public_png_headers" | \
  grep -Eqi '^content-type:[[:space:]]*image/png([[:space:]]*;|[[:space:]]*$)'; then
  printf 'The public PNG response lacks Content-Type: image/png.\n' >&2
  exit 1
fi
printf '[ok] Public SVG gzip and PNG delivery passed.\n'

printf '[stage 3/10] Uploading %s package, document, viewer, PDF, and PNG objects (%s)...\n' \
  "$general_upload_count" "$(format_bytes "$general_upload_bytes")"
rclone copy "$data_root" "$remote_path" \
  "${rclone_common[@]}" "${rclone_progress[@]}" "${copy_safety[@]}" \
  --exclude '/tree/*/svg/**' --exclude '/release.json' \
  --header-upload "Cache-Control: $cache_control"
printf '[ok] General-object phase finished.\n'

printf '[stage 4/10] Verifying anonymous same-origin viewer delivery...\n'
if ! curl --connect-timeout 8 --max-time 60 --fail --silent --show-error \
  --location --dump-header "$public_viewer_headers" \
  --output "$public_viewer" "$public_base/viewer.html"; then
  printf 'The SVG viewer is not anonymously readable; upload stopped.\n' >&2
  exit 1
fi
if ! cmp --silent -- "$data_root/viewer.html" "$public_viewer"; then
  printf 'The public SVG viewer bytes differ from the local release.\n' >&2
  exit 1
fi
if ! tr -d '\r' < "$public_viewer_headers" | \
  grep -Eqi '^content-type:[[:space:]]*text/html([[:space:]]*;|[[:space:]]*$)'; then
  printf 'The public SVG viewer lacks Content-Type: text/html.\n' >&2
  exit 1
fi
if ! grep -Fq 'new DecompressionStream("gzip")' "$public_viewer"; then
  printf 'The public viewer lacks the expected streaming decompressor.\n' >&2
  exit 1
fi
printf '[ok] Same-origin SVG viewer delivery passed.\n'

printf '[stage 5/10] Uploading %s explicit SVG gzip objects (%s)...\n' \
  "$svg_gzip_count" "$(format_bytes "$svg_gzip_bytes")"
rclone copy "$data_root" "$remote_path" \
  "${rclone_common[@]}" "${rclone_progress[@]}" "${copy_safety[@]}" \
  --include '/tree/*/svg/*.svg.gz' \
  --header-upload 'Content-Type: application/gzip' \
  --header-upload "Cache-Control: $cache_control"
printf '[ok] Explicit-gzip phase finished.\n'

printf '[stage 6/10] Verifying every payload object before completion...\n'
rclone check "$data_root" "$remote_path" \
  "${rclone_common[@]}" "${rclone_progress[@]}" \
  --one-way --exclude '/release.json'
printf '[ok] Payload verification passed.\n'

printf '[stage 7/10] Publishing release.json last...\n'
rclone copy "$data_root" "$remote_path" \
  "${rclone_common[@]}" "${rclone_progress[@]}" "${copy_safety[@]}" \
  --include '/release.json' \
  --header-upload 'Content-Type: application/json' \
  --header-upload "Cache-Control: $cache_control"

printf '[stage 8/10] Running final release and public-marker verification...\n'
rclone check "$data_root" "$remote_path" \
  "${rclone_common[@]}" "${rclone_progress[@]}" --one-way
if ! curl --connect-timeout 8 --max-time 60 --fail --silent --show-error \
  --location --output "$public_release" "$public_base/release.json"; then
  printf 'The completion marker is not anonymously readable.\n' >&2
  exit 1
fi
if ! cmp --silent -- "$data_root/release.json" "$public_release"; then
  printf 'The public completion marker differs from the local release.\n' >&2
  exit 1
fi
printf '[ok] Final release verification passed.\n'

if [[ $verify_download == true ]]; then
  printf '[extra verification] Reading every remote object back...\n'
  rclone check "$data_root" "$remote_path" \
    "${rclone_common[@]}" "${rclone_progress[@]}" --one-way --download
  printf '[ok] Full download verification passed.\n'
fi

remote_size=$(rclone size "$remote_path" --json "${rclone_common[@]}")
remote_count=$(jq -r '.count' <<<"$remote_size")
remote_bytes=$(jq -r '.bytes' <<<"$remote_size")
if [[ $remote_count -ne $release_count || $remote_bytes -ne $release_bytes ]]; then
  printf 'Remote totals differ: local=%s/%s, remote=%s/%s (files/bytes).\n' \
    "$release_count" "$release_bytes" "$remote_count" "$remote_bytes" >&2
  exit 1
fi

verified_at=$(TZ=America/Los_Angeles date '+%Y-%m-%d %H:%M:%S PT')
# No report-generation subprocess should inherit archive credentials. All S3
# operations and remote verification are complete before this boundary.
unset AWS_ACCESS_KEY_ID AWS_SECRET_ACCESS_KEY AWS_SESSION_TOKEN
report_args=(
  --data-root "$data_root"
  --run-id "$run_id"
  --verified-at "$verified_at"
)
if [[ $verify_download == true ]]; then
  report_args+=(--full-download-verified)
fi
printf '[stage 9/10] Building the Devastation Pacific Active Archive report...\n'
"$report_builder" "${report_args[@]}"
report_pdf=$repository_root/reports/cartofreako-v13-ucb-active-archive-check-in.pdf
printf 'Active Archive delivery PDF: %s\n' \
  "$report_pdf"

if [[ $compose_report_email == true ]]; then
  report_subject='cartofreako v13 checked in to UCB Active Archive Object Storage'
  report_body=$(printf '%s\n\n%s\n%s\n' \
    'The Cartofreako v13 generated assets are complete and verified in UCB Active Archive Object Storage.' \
    "Public release marker: $public_base/release.json" \
    'The canonical Devastation Pacific Active Archive check-in report is attached.')
  printf '[stage 10/10] Opening the canonical report email for both recipients...\n'
  xdg-email --utf8 --subject "$report_subject" --body "$report_body" \
    --attach "$report_pdf" b.dekosnik@gmail.com abigail.dekosnik@gmail.com
  printf 'After the message is sent, type this exact confirmation:\n' >/dev/tty
  printf '  sent cartofreako v13 report\n> ' >/dev/tty
  IFS= read -r report_delivery_confirmation </dev/tty
  if [[ $report_delivery_confirmation != 'sent cartofreako v13 report' ]]; then
    printf 'Report delivery was not confirmed; the archive itself remains complete.\n' >&2
    exit 2
  fi
  printf '[ok] Operator confirmed delivery of the canonical Active Archive report.\n'
else
  printf '[stage 10/10] Report email handoff skipped by explicit option.\n'
fi

printf 'Upload complete and verified: %s files, %s bytes at %s\n' \
  "$remote_count" "$remote_bytes" "$destination_label"
printf 'Public release marker: %s/release.json\n' "$public_base"
