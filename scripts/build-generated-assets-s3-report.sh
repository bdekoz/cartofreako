#!/usr/bin/env bash

set -Eeuo pipefail

readonly script_dir=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd -P)
readonly repository_root=$(cd -- "$script_dir/.." && pwd -P)
readonly default_data_root=$repository_root/build/s3-release-v12
readonly default_output_dir=$repository_root/reports
readonly template_path=$repository_root/docs/releases/v12-active-archive-report.html.in
readonly report_stem=cartofreako-v12-ucb-active-archive-check-in
readonly report_title='cartofreako v12 checked in to UCB Active Archive Object Storage'
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
completed Cartofreako v12 Active Archive upload. Rendered QA pages are left in
a temporary directory for mandatory visual inspection.

Options:
  --data-root PATH           Override build/s3-release-v12.
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

for command_name in cp find google-chrome grep jq mktemp pdfinfo pdffonts \
  pdftoppm pdftotext sed sha256sum; do
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
   ! grep -Fq '<title>cartofreako v12 checked in to UCB Active Archive Object Storage</title>' \
  "$template_path"; then
  printf 'The report template is not the canonical Active Archive check-in template.\n' >&2
  exit 1
fi
for required_path in SHA256SUMS release.json; do
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

if ! jq -e \
  '.complete == true and
   .release == "v12" and
   .source.tag == "v20260807" and
   .source.commit == "2bd3d760fef540addfcbb4f8002ef7b283d8000f" and
   .destination.bucket == "adekosnik-bucket01" and
   .destination.prefix == "cartofreako/v12" and
   .package.bytes == 927742112 and
   .package.sha256 == "dc1d761def31d77a05a7cc42f9bc0705ee864046f2e235f50c701c9c42fe960a" and
   .inventory.source_tree_bytes == 2322788028 and
   .inventory.manifest_payload_files == 592 and
   .inventory.release_object_count == 594 and
   .inventory.published_svg_gzip_files == 187 and
   .inventory.pdf_files == 187 and
   .inventory.png_files == 187 and
   .inventory.cahill_keyes_thumbnail_files == 28 and
   .integrity.manifest_sha256 == "88302648b9bed3775d708cc1d0e959c6973f01ede09ae9a5c5a4bb4f7c12ce38"' \
  "$data_root/release.json" >/dev/null; then
  printf 'release.json does not match the verified v12 report evidence.\n' >&2
  exit 1
fi
(
  cd -- "$data_root"
  sha256sum --check --quiet --strict SHA256SUMS
)

mkdir -p -- "$output_dir"
output_dir=$(cd -- "$output_dir" && pwd -P)
work_root=$(mktemp -d "${TMPDIR:-/tmp}/cartofreako-v12-report-build.XXXXXX")
qa_dir=$(mktemp -d "${TMPDIR:-/tmp}/cartofreako-v12-report-qa.XXXXXX")
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
  "$html_temp"
if grep -q '@@[A-Z_]*@@' "$html_temp"; then
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
if ! grep -Eq '^Title:[[:space:]]+cartofreako v12 checked in to UCB Active Archive Object Storage$' "$pdfinfo_temp" ||
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
  'CARTOFREAKO · ACTIVE ARCHIVE CHECK-IN · RELEASE V12' '2,039,067,910' \
  '2,322,788,028' 'DecompressionStream("gzip")'; do
  if ! grep -Fq "$required_text" "$normalized_text_temp"; then
    printf 'Required report text is absent after PDF extraction: %s\n' \
      "$required_text" >&2
    exit 1
  fi
done
if ! grep -Fq \
  '88302648b9bed3775d708cc1d0e959c6973f01ede09ae9a5c5a4bb4f7c12ce38' \
  "$compact_text_temp"; then
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
