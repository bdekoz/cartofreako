#!/usr/bin/env bash

set -euo pipefail

repository_root=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd -P)
driver="$repository_root/scripts/generate-authorized-external.sh"
temporary_dir=$(mktemp -d /tmp/cartofreako-generate-external-test.XXXXXX)
trap 'rm -rf -- "$temporary_dir"' EXIT

fake_make="$temporary_dir/fake-make"
fake_authorizer="$temporary_dir/fake-authorizer"
fake_installer="$temporary_dir/fake-installer"
apply_log="$temporary_dir/apply.log"
cat > "$fake_make" <<'FAKE_MAKE'
#!/usr/bin/env bash
printf '%s\n' "$*" >> "${EXTERNAL_GENERATION_TEST_LOG:?}"
FAKE_MAKE
cat > "$fake_authorizer" <<'FAKE_AUTHORIZER'
#!/usr/bin/env bash
printf 'authorize %s\n' "$*" >> "${EXTERNAL_GENERATION_TEST_LOG:?}"
FAKE_AUTHORIZER
cat > "$fake_installer" <<'FAKE_INSTALLER'
#!/usr/bin/env bash
printf '%s\n' 'install-jaxa-certificate' >> "${EXTERNAL_GENERATION_TEST_LOG:?}"
mkdir -p "$(dirname "${PTREE_CACERT:?}")"
printf '%s\n' 'test certificate' > "$PTREE_CACERT"
FAKE_INSTALLER
chmod 700 "$fake_make" "$fake_authorizer" "$fake_installer"

EXTERNAL_GENERATION_TEST_LOG="$apply_log" \
EXTERNAL_AUTHORIZER="$fake_authorizer" \
JAXA_CERTIFICATE_INSTALLER="$fake_installer" \
EXTERNAL_SELECTION_MODE=strict \
PTREE_CACERT="$temporary_dir/strict/certificate.pem" \
MAKE_COMMAND="$fake_make" \
  "$driver" ptree jaxa-ptree firms nasa-firms topology network-topology \
  > "$temporary_dir/output"

cat > "$temporary_dir/expected" <<'EXPECTED'
install-jaxa-certificate
authorize jaxa-ptree nasa-firms network-topology
--no-print-directory fetch-cloud-atmosphere-data
--no-print-directory prepare-cloud-atmosphere-data
--no-print-directory verify-cloud-atmosphere-data
--no-print-directory generate-cloud-atmosphere-artifacts
--no-print-directory fetch-anthropocene-data
--no-print-directory prepare-anthropocene-data
--no-print-directory generate-network-infrastructure-topology-artifacts
EXPECTED
diff -u "$temporary_dir/expected" "$apply_log"

grep -Fq \
  'no Anthropocene release artifact was rendered from the unpromoted candidate' \
  "$temporary_dir/output"

auto_log="$temporary_dir/auto.log"
cat > "$temporary_dir/netrc" <<'NETRC'
machine ftp.ptree.jaxa.jp
  login test-user
  password test-password
NETRC
chmod 600 "$temporary_dir/netrc"
EXTERNAL_GENERATION_TEST_LOG="$auto_log" \
EXTERNAL_AUTHORIZER="$fake_authorizer" \
JAXA_CERTIFICATE_INSTALLER="$fake_installer" \
EXTERNAL_SELECTION_MODE=auto \
PTREE_NETRC="$temporary_dir/netrc" \
PTREE_CACERT="$temporary_dir/auto/certificate.pem" \
FIRMS_MAP_KEY='' \
NETWORK_TOPOLOGY_LICENSE_ACCEPTED='' \
MAKE_COMMAND="$fake_make" \
  "$driver" jaxa-ptree nasa-firms network-topology \
  > "$temporary_dir/auto-output"
cat > "$temporary_dir/auto-expected" <<'AUTO_EXPECTED'
install-jaxa-certificate
authorize jaxa-ptree
--no-print-directory fetch-cloud-atmosphere-data
--no-print-directory prepare-cloud-atmosphere-data
--no-print-directory verify-cloud-atmosphere-data
--no-print-directory generate-cloud-atmosphere-artifacts
AUTO_EXPECTED
diff -u "$temporary_dir/auto-expected" "$auto_log"
grep -Fq 'skipping nasa-firms (FIRMS_MAP_KEY is unset)' \
  "$temporary_dir/auto-output"
grep -Fq 'skipping network-topology (license acknowledgement is unset)' \
  "$temporary_dir/auto-output"

if EXTERNAL_GENERATION_TEST_LOG="$temporary_dir/invalid.log" \
     EXTERNAL_AUTHORIZER="$fake_authorizer" \
     MAKE_COMMAND="$fake_make" "$driver" unknown \
     > "$temporary_dir/invalid-output" 2>&1; then
  echo 'unknown external pass unexpectedly succeeded' >&2
  exit 1
fi
test ! -e "$temporary_dir/invalid.log"

printf '%s\n' 'authorized external generation driver tests passed'
