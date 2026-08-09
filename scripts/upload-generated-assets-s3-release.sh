#!/usr/bin/env bash

set -Eeuo pipefail
set +x

readonly script_name=${0##*/}
readonly uploader_version=7
readonly script_dir=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd -P)
readonly repository_root=$(cd -- "$script_dir/.." && pwd -P)
readonly validator=$script_dir/validate-generated-assets-s3-release.sh
readonly report_builder=$script_dir/build-generated-assets-s3-report.sh
readonly profile=$repository_root/docs/releases/v13-aao-upload-profile.json
readonly default_clusterops_root=/home/bkoz/src/alpha60-clusterops
readonly default_data_root=$repository_root/build/s3-release-v13
readonly default_endpoint=https://s3-ewh.ist.berkeley.edu
readonly default_region=us-east-1
readonly default_bucket=adekosnik-bucket01
readonly default_prefix=cartofreako/v13
readonly default_receipt=$repository_root/reports/cartofreako-v13-aao-upload-receipt.json
readonly default_validation_receipt=$repository_root/reports/cartofreako-v13-aao-validation-receipt.json
readonly default_dry_run_receipt=$repository_root/reports/cartofreako-v13-aao-dry-run-receipt.json
readonly email_request=$repository_root/reports/cartofreako-v13-report-email-request.json

clusterops_root=${AAO_CLUSTEROPS_ROOT:-$default_clusterops_root}
data_root=$default_data_root
endpoint=$default_endpoint
region=$default_region
bucket=$default_bucket
prefix=$default_prefix
receipt=$default_receipt
receipt_was_set=false
apply_upload=false
verify_download=false
validate_only=false
write_email_request=true

usage()
{
  cat <<EOF
Usage: $script_name [OPTIONS]

Validate the exact Cartofreako v13 contract, then publish it through the
shared alpha60-clusterops AAO transport. The default performs an authenticated
dry run. Only --apply writes remote objects.

Options:
  --apply              Upload after dry runs and exact-prefix confirmation.
  --verify-download    Read every remote object back after normal checks.
  --validate-only      Validate locally without network or credentials.
  --skip-report-email  Do not create the post-report Gmail outbox request.
  --clusterops-root P  Override /home/bkoz/src/alpha60-clusterops.
  --data-root PATH     Override build/s3-release-v13.
  --receipt PATH       Override the mode-specific shared-transport receipt.
  --endpoint URL       Override the S3 endpoint.
  --region NAME        Override the S3 signing region.
  --bucket NAME        Override the bucket.
  --prefix PATH        Override the object-key prefix.
  -h, --help           Show this help.

The script never opens a desktop mail composer. After a completed applied run
it writes a credential-free Gmail outbox request beside the canonical report.
The authenticated release orchestrator consumes that request automatically
after visual report review; it does not ask the operator to send or confirm it.
Validation and dry-run receipts use separate filenames and never overwrite the
canonical completed-upload receipt.
EOF
}

die()
{
  printf '%s: %s\n' "$script_name" "$*" >&2
  exit 2
}

while (($#)); do
  case $1 in
    --apply)
      apply_upload=true
      shift
      ;;
    --verify-download)
      verify_download=true
      shift
      ;;
    --validate-only)
      validate_only=true
      shift
      ;;
    --skip-report-email)
      write_email_request=false
      shift
      ;;
    --clusterops-root)
      (($# >= 2)) || die "$1 requires a value"
      clusterops_root=$2
      shift 2
      ;;
    --data-root)
      (($# >= 2)) || die "$1 requires a value"
      data_root=$2
      shift 2
      ;;
    --receipt)
      (($# >= 2)) || die "$1 requires a value"
      receipt=$2
      receipt_was_set=true
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

if [[ $validate_only == true &&
      ($apply_upload == true || $verify_download == true) ]]; then
  die "--validate-only cannot be combined with --apply or --verify-download"
fi
if [[ $verify_download == true && $apply_upload != true ]]; then
  die "--verify-download requires --apply"
fi
if [[ $receipt_was_set != true ]]; then
  if [[ $validate_only == true ]]; then
    receipt=$default_validation_receipt
  elif [[ $apply_upload != true ]]; then
    receipt=$default_dry_run_receipt
  fi
fi

readonly loader=$clusterops_root/bin/load-s3-aao
[[ -x $loader ]] || die "shared AAO launcher is unavailable: $loader"
[[ -x $validator ]] || die "Cartofreako release validator is unavailable: $validator"
[[ -x $report_builder ]] || die "Active Archive report builder is unavailable: $report_builder"
[[ -f $profile ]] || die "Cartofreako AAO profile is unavailable: $profile"

printf 'Cartofreako S3 release adapter %s\n' "$uploader_version"
printf 'Running the exact product-specific validator before shared transport...\n'
"$validator" --data-root "$data_root" --endpoint "$endpoint" \
  --region "$region" --bucket "$bucket" --prefix "$prefix"

transport_args=(
  --release-root "$repository_root"
  --profile "$profile"
  --data-root "$data_root"
  --receipt "$receipt"
  --endpoint "$endpoint"
  --region "$region"
  --bucket "$bucket"
  --prefix "$prefix"
)
if [[ $validate_only == true ]]; then transport_args+=(--validate-only); fi
if [[ $apply_upload == true ]]; then transport_args+=(--apply); fi
if [[ $verify_download == true ]]; then transport_args+=(--verify-download); fi

"$loader" "${transport_args[@]}"

if [[ $validate_only == true || $apply_upload != true ]]; then
  exit 0
fi

if ! jq -e '
  .schema == "aao-upload-receipt-v1" and .status == "complete" and
  .release == "cartofreako-v13" and
  .destination.bucket == "adekosnik-bucket01" and
  .destination.prefix == "cartofreako/v13" and
  .inventory.objects == 830 and .inventory.stored_bytes == 2800589791 and
  .verification.standard == true' "$receipt" >/dev/null; then
  die "shared transport did not produce the exact completed v13 receipt"
fi

run_id=$(jq -r '.run_id' "$receipt")
completed_at=$(jq -r '.completed_at' "$receipt")
verified_at=$(TZ=America/Los_Angeles date -d "$completed_at" '+%Y-%m-%d %H:%M:%S PT')
report_args=(
  --data-root "$data_root"
  --run-id "$run_id"
  --verified-at "$verified_at"
)
if [[ $(jq -r '.verification.full_download' "$receipt") == true ]]; then
  report_args+=(--full-download-verified)
fi

printf 'Building the canonical Devastation Pacific Active Archive report...\n'
"$report_builder" "${report_args[@]}"
report_pdf=$repository_root/reports/cartofreako-v13-ucb-active-archive-check-in.pdf
report_sha256=$(sha256sum "$report_pdf" | awk '{print $1}')
printf 'Active Archive delivery PDF: %s\n' "$report_pdf"

if [[ $write_email_request == true ]]; then
  report_subject='cartofreako v13 checked in to UCB Active Archive Object Storage'
  report_body=$(printf '%s\n\n%s\n%s\n\n%s\n' \
    'The Cartofreako v13 generated assets are complete and verified in UCB Active Archive Object Storage.' \
    'Public release marker: https://s3-ewh.ist.berkeley.edu/adekosnik-bucket01/cartofreako/v13/release.json' \
    'GitHub release: https://github.com/bdekoz/cartofreako/releases/tag/v20260808.1' \
    'The attached PDF is the canonical Devastation Pacific Active Archive check-in report.')
  mkdir -p -- "$(dirname -- "$email_request")"
  jq -n \
    --arg schema cartofreako-report-email-request-v1 \
    --arg status ready-for-automatic-delivery \
    --argjson to '["b.dekosnik@gmail.com", "abigail.dekosnik@gmail.com"]' \
    --arg subject "$report_subject" --arg body "$report_body" \
    --arg attachment "$report_pdf" \
    --arg attachment_sha256 "$report_sha256" \
    --arg transport_receipt "$receipt" \
    '{schema: $schema, status: $status, to: $to, subject: $subject,
      body: $body, attachment: {path: $attachment, sha256: $attachment_sha256},
      transport_receipt: $transport_receipt,
      requirements: {visual_report_review: true,
        authenticated_provider_send: true, desktop_composer: false}}' \
    > "$email_request.tmp"
  mv -- "$email_request.tmp" "$email_request"
  printf 'Automatic Gmail outbox request: %s\n' "$email_request"
  printf 'The authenticated release orchestrator consumes it after report QA and writes delivery evidence; no desktop composer or extra operator confirmation is used.\n'
else
  printf 'Report-email request skipped by explicit option.\n'
fi

printf 'Cartofreako v13 archive transport and report generation complete.\n'
