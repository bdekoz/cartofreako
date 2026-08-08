#!/usr/bin/env bash

set -Eeuo pipefail

readonly script_dir=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd -P)
readonly repository_root=$(cd -- "$script_dir/.." && pwd -P)
readonly default_data_root=$repository_root/build/s3-release-v13
readonly default_output_dir=$repository_root/reports
readonly template_path=$repository_root/docs/releases/v13-active-archive-report.html.in
readonly report_stem=cartofreako-v13-ucb-active-archive-check-in
readonly report_title='cartofreako v13 checked in to UCB Active Archive Object Storage'
readonly report_style='Devastation Pacific Summer 2026 v1.1 canonical Active Archive check-in'

data_root=$default_data_root
output_dir=$default_output_dir
run_id=
verified_at=
full_download_verified=false

usage() {
  cat <<'EOF'
Usage: scripts/build-generated-assets-s3-report.sh [options]

Generate the Devastation Pacific house-style HTML and tagged PDF report for a
completed Cartofreako v13 Active Archive upload. Rendered QA pages are left in
a temporary directory for mandatory visual inspection.

Options:
  --data-root PATH           Override build/s3-release-v13.
  --output-dir PATH          Override reports/.
  --run-id ID                Uploader run ID, YYYYMMDDTHHMMSSZ (required).
  --verified-at TIMESTAMP    Pacific verification time ending in PT (required).
  --full-download-verified   Record successful remote download verification.
  -h, --help                 Show this help.
EOF
}

while (( $# > 0 )); do
  case $1 in
    --data-root)
      [[ $# -ge 2 ]] || { printf '%s requires a value.\n' "$1" >&2; exit 2; }
      data_root=$2
      shift
      ;;
    --output-dir)
      [[ $# -ge 2 ]] || { printf '%s requires a value.\n' "$1" >&2; exit 2; }
      output_dir=$2
      shift
      ;;
    --run-id)
      [[ $# -ge 2 ]] || { printf '%s requires a value.\n' "$1" >&2; exit 2; }
      run_id=$2
      shift
      ;;
    --verified-at)
      [[ $# -ge 2 ]] || { printf '%s requires a value.\n' "$1" >&2; exit 2; }
      verified_at=$2
      shift
      ;;
    --full-download-verified)
      full_download_verified=true
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

if [[ ! $run_id =~ ^[0-9]{8}T[0-9]{6}Z$ ]]; then
  printf 'A valid --run-id in YYYYMMDDTHHMMSSZ form is required.\n' >&2
  exit 2
fi
if [[ ! $verified_at =~ ^[0-9]{4}-[0-9]{2}-[0-9]{2}[[:space:]][0-9]{2}:[0-9]{2}:[0-9]{2}[[:space:]]PT$ ]]; then
  printf 'A valid --verified-at timestamp in YYYY-MM-DD HH:MM:SS PT form is required.\n' >&2
  exit 2
fi

for command_name in awk cp find google-chrome grep jq mktemp pdfinfo pdffonts \
  pdftoppm pdftotext sed sha256sum stat tr wc; do
  if ! command -v "$command_name" >/dev/null; then
    printf 'Missing required report command: %s\n' "$command_name" >&2
    exit 1
  fi
done
if [[ ! -f $template_path ]]; then
  printf 'Report template not found: %s\n' "$template_path" >&2
  exit 1
fi
if ! grep -Fq \
  '<meta name="devastation-pacific-house-style" content="Summer 2026 v1.1 canonical">' \
  "$template_path" ||
   ! grep -Fq \
  '<meta name="document-kind" content="active-archive-check-in">' \
  "$template_path" ||
   ! grep -Fq '<title>cartofreako v13 checked in to UCB Active Archive Object Storage</title>' \
  "$template_path"; then
  printf 'The report template is not the canonical Active Archive check-in template.\n' >&2
  exit 1
fi
for required_path in README.md viewer.html SHA256SUMS release.json \
  package/assets.generated.v13.tar.xz; do
  if [[ ! -f $data_root/$required_path ]]; then
    printf 'Validated release artifact not found: %s\n' "$data_root/$required_path" >&2
    exit 1
  fi
done
for font_path in \
  /home/bkoz/.fonts/atkinson_hyperlegible.2026/AtkinsonHyperlegibleNext-Regular.otf \
  /home/bkoz/.fonts/atkinson_hyperlegible.2026/AtkinsonHyperlegibleNext-SemiBold.otf \
  /home/bkoz/.fonts/atkinson_hyperlegible.2026/AtkinsonHyperlegibleNext-Bold.otf \
  /home/bkoz/.fonts/atkinson_hyperlegible.2026/AtkinsonHyperlegibleMono-Regular.otf \
  /home/bkoz/.fonts/atkinson_hyperlegible.2026/AtkinsonHyperlegibleMono-Bold.otf; do
  if [[ ! -r $font_path ]]; then
    printf 'Required Atkinson font is not readable: %s\n' "$font_path" >&2
    exit 1
  fi
done

(
  cd -- "$data_root"
  sha256sum --check --quiet --strict SHA256SUMS
)
manifest_sha256=$(sha256sum -- "$data_root/SHA256SUMS" | awk '{print $1}')
package_path=$data_root/package/assets.generated.v13.tar.xz
package_sha256=$(sha256sum -- "$package_path" | awk '{print $1}')
if ! jq -e \
  --arg manifest_sha256 "$manifest_sha256" \
  --arg package_sha256 "$package_sha256" \
  '.schema_version == 2 and
   .complete == true and
   .release == "v13" and .stage == 13 and
   (.source.tag | test("^v[0-9]{8}([.][0-9]+)?$")) and
   (.source.commit | test("^[0-9a-f]{40}$")) and
   .destination.endpoint == "https://s3-ewh.ist.berkeley.edu" and
   .destination.region == "us-east-1" and
   .destination.bucket == "adekosnik-bucket01" and
   .destination.prefix == "cartofreako/v13" and
   .layout.organization == "projection/format/artifact" and
   .package.sha256 == $package_sha256 and
   .inventory.source_tree_files == 909 and
   .inventory.manifest_payload_files == 828 and
   .inventory.release_object_count == 830 and
   .inventory.published_tree_files == 825 and
   .inventory.published_svg_gzip_files == 211 and
   .inventory.pdf_files == 211 and
   .inventory.png_files == 211 and
   .inventory.thumbnail_files == 192 and
   .inventory.thumbnails_per_projection == 32 and
   .integrity.manifest_sha256 == $manifest_sha256' \
  "$data_root/release.json" >/dev/null; then
  printf 'release.json does not match the verified v13 report contract.\n' >&2
  exit 1
fi

format_integer() {
  local value=$1
  local grouped=
  while (( ${#value} > 3 )); do
    grouped=,${value: -3}$grouped
    value=${value:0:${#value}-3}
  done
  printf '%s%s' "$value" "$grouped"
}

sum_matching_files() {
  find "$data_root/tree" -type f -path "$1" -printf '%s\n' | \
    awk '{ total += $1 } END { printf "%.0f", total }'
}

source_tag=$(jq -r '.source.tag' "$data_root/release.json")
source_commit=$(jq -r '.source.commit' "$data_root/release.json")
source_tree_files=$(jq -r '.inventory.source_tree_files' "$data_root/release.json")
source_tree_bytes_raw=$(jq -r '.inventory.source_tree_bytes' "$data_root/release.json")
payload_files=$(jq -r '.inventory.manifest_payload_files' "$data_root/release.json")
release_objects=$(jq -r '.inventory.release_object_count' "$data_root/release.json")
svg_count=$(jq -r '.inventory.published_svg_gzip_files' "$data_root/release.json")
pdf_count=$(jq -r '.inventory.pdf_files' "$data_root/release.json")
png_count=$(jq -r '.inventory.png_files' "$data_root/release.json")
thumbnail_count=$(jq -r '.inventory.thumbnail_files' "$data_root/release.json")
thumbnails_per_projection=$(jq -r '.inventory.thumbnails_per_projection' "$data_root/release.json")
package_bytes_raw=$(jq -r '.package.bytes' "$data_root/release.json")
release_bytes_raw=$(find "$data_root" -type f -printf '%s\n' | \
  awk '{ total += $1 } END { printf "%.0f", total }')
svg_bytes_raw=$(sum_matching_files '*/svg/*.svg.gz')
pdf_bytes_raw=$(sum_matching_files '*/pdf/*.pdf')
png_bytes_raw=$(sum_matching_files '*/png/*.png')
thumbnail_bytes_raw=$(sum_matching_files '*/thumbnail/*.png')
readme_bytes_raw=$(stat -c '%s' -- "$data_root/README.md")
viewer_bytes_raw=$(stat -c '%s' -- "$data_root/viewer.html")
manifest_bytes_raw=$(stat -c '%s' -- "$data_root/SHA256SUMS")
marker_bytes_raw=$(stat -c '%s' -- "$data_root/release.json")
actual_release_objects=$(find "$data_root" -type f | wc -l)
actual_svg_count=$(find "$data_root/tree" -type f -path '*/svg/*.svg.gz' | wc -l)
actual_pdf_count=$(find "$data_root/tree" -type f -path '*/pdf/*.pdf' | wc -l)
actual_png_count=$(find "$data_root/tree" -type f -path '*/png/*.png' | wc -l)
actual_thumbnail_count=$(find "$data_root/tree" -type f \
  -path '*/thumbnail/*.png' | wc -l)
actual_package_bytes=$(stat -c '%s' -- "$package_path")
if [[ $actual_release_objects -ne $release_objects ||
      $actual_svg_count -ne $svg_count || $actual_pdf_count -ne $pdf_count ||
      $actual_png_count -ne $png_count ||
      $actual_thumbnail_count -ne $thumbnail_count ||
      $actual_package_bytes -ne $package_bytes_raw ]]; then
  printf 'Local report inventory differs from release.json.\n' >&2
  exit 1
fi

release_bytes=$(format_integer "$release_bytes_raw")
source_tree_bytes=$(format_integer "$source_tree_bytes_raw")
svg_bytes=$(format_integer "$svg_bytes_raw")
pdf_bytes=$(format_integer "$pdf_bytes_raw")
png_bytes=$(format_integer "$png_bytes_raw")
thumbnail_bytes=$(format_integer "$thumbnail_bytes_raw")
package_bytes=$(format_integer "$package_bytes_raw")
readme_bytes=$(format_integer "$readme_bytes_raw")
viewer_bytes=$(format_integer "$viewer_bytes_raw")
manifest_bytes=$(format_integer "$manifest_bytes_raw")
marker_bytes=$(format_integer "$marker_bytes_raw")
release_gib=$(awk -v bytes="$release_bytes_raw" 'BEGIN { printf "%.2f", bytes / 1073741824 }')
source_tree_gib=$(awk -v bytes="$source_tree_bytes_raw" 'BEGIN { printf "%.2f", bytes / 1073741824 }')
all_png_count=$((png_count + thumbnail_count))

mkdir -p -- "$output_dir"
output_dir=$(cd -- "$output_dir" && pwd -P)
work_root=$(mktemp -d "${TMPDIR:-/tmp}/cartofreako-v13-report-build.XXXXXX")
qa_dir=$(mktemp -d "${TMPDIR:-/tmp}/cartofreako-v13-report-qa.XXXXXX")
html_temp=$work_root/$report_stem.html
pdf_temp=$work_root/$report_stem.pdf
text_temp=$work_root/$report_stem.txt
normalized_text_temp=$work_root/$report_stem-normalized.txt
compact_text_temp=$work_root/$report_stem-compact.txt
pdfinfo_temp=$work_root/pdfinfo.txt
pdffonts_temp=$work_root/pdffonts.txt
chrome_log=$work_root/chrome.log

cleanup() {
  rm -rf -- "$work_root"
}
trap cleanup EXIT HUP INT TERM

if [[ $full_download_verified == true ]]; then
  download_sentence='A full remote read-back and re-hash of every object also passed.'
  download_step='The optional rclone check --download completed without reported differences.'
  download_label='Observed'
  download_boundary='The optional full download verification was selected and completed; this report claims a post-upload read-back and re-hash of every remote object.'
else
  download_sentence='The optional full remote read-back was not selected for this run.'
  download_step='The optional full remote download verification was not selected.'
  download_label='Not performed'
  download_boundary='The optional full download verification was not selected; this report does not claim a post-upload read-back and re-hash of every remote object.'
fi

cp -- "$template_path" "$html_temp"
sed -i \
  -e "s|@@VERIFIED_AT@@|$verified_at|g" \
  -e "s|@@RUN_ID@@|$run_id|g" \
  -e "s|@@DOWNLOAD_SENTENCE@@|$download_sentence|g" \
  -e "s|@@DOWNLOAD_STEP@@|$download_step|g" \
  -e "s|@@DOWNLOAD_LABEL@@|$download_label|g" \
  -e "s|@@DOWNLOAD_BOUNDARY@@|$download_boundary|g" \
  -e "s|@@RELEASE_OBJECTS@@|$release_objects|g" \
  -e "s|@@RELEASE_BYTES@@|$release_bytes|g" \
  -e "s|@@RELEASE_GIB@@|$release_gib|g" \
  -e "s|@@SOURCE_TREE_FILES@@|$source_tree_files|g" \
  -e "s|@@SOURCE_TREE_BYTES@@|$source_tree_bytes|g" \
  -e "s|@@SOURCE_TREE_GIB@@|$source_tree_gib|g" \
  -e "s|@@SVG_COUNT@@|$svg_count|g" \
  -e "s|@@SVG_BYTES@@|$svg_bytes|g" \
  -e "s|@@PDF_COUNT@@|$pdf_count|g" \
  -e "s|@@PDF_BYTES@@|$pdf_bytes|g" \
  -e "s|@@PNG_COUNT@@|$png_count|g" \
  -e "s|@@PNG_BYTES@@|$png_bytes|g" \
  -e "s|@@THUMBNAIL_COUNT@@|$thumbnail_count|g" \
  -e "s|@@THUMBNAILS_PER_PROJECTION@@|$thumbnails_per_projection|g" \
  -e "s|@@THUMBNAIL_BYTES@@|$thumbnail_bytes|g" \
  -e "s|@@ALL_PNG_COUNT@@|$all_png_count|g" \
  -e "s|@@PACKAGE_BYTES@@|$package_bytes|g" \
  -e "s|@@PACKAGE_SHA256@@|$package_sha256|g" \
  -e "s|@@README_BYTES@@|$readme_bytes|g" \
  -e "s|@@VIEWER_BYTES@@|$viewer_bytes|g" \
  -e "s|@@MANIFEST_BYTES@@|$manifest_bytes|g" \
  -e "s|@@MARKER_BYTES@@|$marker_bytes|g" \
  -e "s|@@PAYLOAD_FILES@@|$payload_files|g" \
  -e "s|@@MANIFEST_SHA256@@|$manifest_sha256|g" \
  -e "s|@@SOURCE_TAG@@|$source_tag|g" \
  -e "s|@@SOURCE_COMMIT@@|$source_commit|g" \
  "$html_temp"
if grep -Eq '@@[A-Z0-9_]+@@' "$html_temp"; then
  printf 'Unresolved placeholder remains in the report HTML.\n' >&2
  exit 1
fi

mkdir -p -- "$work_root/chrome-profile"
google-chrome \
  --headless=new \
  --disable-gpu \
  --disable-dev-shm-usage \
  --no-sandbox \
  --allow-file-access-from-files \
  --export-tagged-pdf \
  --generate-pdf-document-outline \
  --no-pdf-header-footer \
  --run-all-compositor-stages-before-draw \
  --user-data-dir="$work_root/chrome-profile" \
  --print-to-pdf="$pdf_temp" \
  "file://$html_temp" > /dev/null 2> "$chrome_log"
if [[ ! -s $pdf_temp ]]; then
  printf 'Chrome did not create the report PDF.\n' >&2
  sed -n '1,80p' "$chrome_log" >&2
  exit 1
fi

pdfinfo "$pdf_temp" > "$pdfinfo_temp"
pdffonts "$pdf_temp" > "$pdffonts_temp"
pdftotext -layout "$pdf_temp" "$text_temp"
tr '\n' ' ' < "$text_temp" | \
  sed 's/[[:space:]][[:space:]]*/ /g' > "$normalized_text_temp"
tr -d '[:space:]' < "$text_temp" > "$compact_text_temp"
if ! grep -Eq '^Title:[[:space:]]+cartofreako v13 checked in to UCB Active Archive Object Storage$' "$pdfinfo_temp" ||
   ! grep -Eq '^Tagged:[[:space:]]+yes$' "$pdfinfo_temp" ||
   ! grep -Eq '^Pages:[[:space:]]+3$' "$pdfinfo_temp" ||
   ! grep -Eq '^Page size:[[:space:]]+612 x 792 pts \(letter\)$' "$pdfinfo_temp"; then
  printf 'PDF metadata, tagging, page count, or page size is incorrect.\n' >&2
  sed -n '1,40p' "$pdfinfo_temp" >&2
  exit 1
fi
for font_name in AtkinsonHyperlegibleNext-Bold \
  AtkinsonHyperlegibleNext-Regular AtkinsonHyperlegibleMono-Bold \
  AtkinsonHyperlegibleMono-Regular; do
  if ! grep -Fq "$font_name" "$pdffonts_temp"; then
    printf 'Expected embedded font is absent: %s\n' "$font_name" >&2
    exit 1
  fi
done
if grep -Eq 'LiberationSans|DejaVuSans' "$pdffonts_temp"; then
  printf 'Generic deposit-report fonts were found in the Active Archive PDF.\n' >&2
  cat "$pdffonts_temp" >&2
  exit 1
fi
if awk 'NR > 2 && $0 !~ /yes[[:space:]]+yes[[:space:]]+yes/ { exit 1 }' \
  "$pdffonts_temp"; then
  :
else
  printf 'One or more PDF fonts lack embedded, subset, or Unicode status.\n' >&2
  cat "$pdffonts_temp" >&2
  exit 1
fi
for required_text in "$report_title" \
  'CARTOFREAKO · ACTIVE ARCHIVE CHECK-IN · RELEASE V13' "$release_bytes" \
  "$source_tree_bytes" 'DecompressionStream("gzip")'; do
  if ! grep -Fq "$required_text" "$normalized_text_temp"; then
    printf 'Required report text is absent after PDF extraction: %s\n' \
      "$required_text" >&2
    exit 1
  fi
done
if ! grep -Fq "$manifest_sha256" "$compact_text_temp"; then
  printf 'The manifest digest is absent after PDF extraction.\n' >&2
  exit 1
fi

pdftoppm -png -r 180 "$pdf_temp" "$qa_dir/page" >/dev/null 2>&1
if [[ $(find "$qa_dir" -maxdepth 1 -type f -name 'page-*.png' | wc -l) -ne 3 ]]; then
  printf 'Expected three rendered QA pages.\n' >&2
  exit 1
fi

html_path=$output_dir/$report_stem.html
pdf_path=$output_dir/$report_stem.pdf
mv -- "$html_temp" "$html_path"
mv -- "$pdf_temp" "$pdf_path"

printf 'Built Devastation Pacific Active Archive report:\n'
printf '  Style: %s\n' "$report_style"
printf '  HTML: %s\n' "$html_path"
printf '  PDF:  %s\n' "$pdf_path"
printf '  QA:   %s\n' "$qa_dir"
printf '  SHA-256: '
sha256sum -- "$pdf_path" | awk '{print $1}'
printf 'Structural checks passed; inspect all three rendered QA pages before delivery.\n'
