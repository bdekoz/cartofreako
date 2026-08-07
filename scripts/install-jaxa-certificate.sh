#!/usr/bin/env bash

# Install the official SECOM root used by JAXA P-Tree into private user data.

set -Eeuo pipefail

readonly certificate_url=https://repo1.secomtrust.net/root/tlsrsa/tlsrsarootca2024-pem.cer
readonly certificate_filename=secom-tls-rsa-root-ca-2024.pem
readonly expected_sha256=1435f225c5d252d7a21948cc3ce62aecfa88001e3dd72d1cc3555100eb372f93

fail()
{
  printf 'JAXA certificate installation failed: %s\n' "$*" >&2
  exit 1
}

if [[ $# -gt 0 ]]; then
  printf '%s\n' \
    'usage: install-jaxa-certificate.sh' \
    '' \
    'Downloads and verifies the official SECOM TLS RSA Root CA 2024 used by' \
    'JAXA P-Tree, then installs it in private per-user data. Set PTREE_CACERT' \
    'to override the destination path.' >&2
  exit 2
fi

for command_name in curl dirname install mktemp openssl sha256sum; do
  command -v "$command_name" >/dev/null 2>&1 \
    || fail "missing prerequisite: $command_name"
done

data_home=${XDG_DATA_HOME:-${HOME:?HOME is required}/.local/share}
destination=${PTREE_CACERT:-$data_home/cartofreako/certs/$certificate_filename}
destination_directory=$(dirname -- "$destination")
[[ $destination = /* ]] || fail 'PTREE_CACERT must be an absolute path'
if [[ -L $destination || ( -e $destination && ! -f $destination ) ]]; then
  fail "destination is not a regular file: $destination"
fi

temporary_directory=$(mktemp -d "${TMPDIR:-/tmp}/cartofreako-jaxa-certificate.XXXXXX")
downloaded_certificate=$temporary_directory/$certificate_filename
cleanup()
{
  rm -rf -- "$temporary_directory"
}
trap cleanup EXIT HUP INT TERM

printf 'Downloading the official JAXA P-Tree trust anchor...\n'
curl --fail --silent --show-error --location \
  --proto '=https' --tlsv1.2 \
  --output "$downloaded_certificate" "$certificate_url"

openssl x509 -in "$downloaded_certificate" -noout -checkend 0 >/dev/null \
  || fail 'downloaded certificate is invalid or expired'
actual_sha256=$(openssl x509 -in "$downloaded_certificate" -outform DER | \
  sha256sum)
actual_sha256=${actual_sha256%% *}
if [[ $actual_sha256 != "$expected_sha256" ]]; then
  fail "certificate SHA-256 mismatch: expected $expected_sha256, got $actual_sha256"
fi
openssl verify -CAfile "$downloaded_certificate" \
  "$downloaded_certificate" >/dev/null \
  || fail 'downloaded certificate is not a valid self-signed trust anchor'

install -d -m 700 -- "$destination_directory"
install -m 600 -- "$downloaded_certificate" "$destination"

printf '%s\n' \
  '[ok] Installed and verified SECOM TLS RSA Root CA 2024.' \
  "Path: $destination" \
  "Certificate SHA-256: $actual_sha256" \
  'Cartofreako P-Tree authorization and fetching will use it automatically.'
