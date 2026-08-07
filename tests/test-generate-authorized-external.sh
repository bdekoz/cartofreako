#!/usr/bin/env bash

set -euo pipefail

repository_root=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd -P)
driver="$repository_root/scripts/generate-authorized-external.sh"
temporary_dir=$(mktemp -d /tmp/cartofreako-generate-external-test.XXXXXX)
trap 'rm -rf -- "$temporary_dir"' EXIT

fake_make="$temporary_dir/fake-make"
apply_log="$temporary_dir/apply.log"
cat > "$fake_make" <<'FAKE_MAKE'
#!/usr/bin/env bash
printf '%s\n' "$*" >> "${EXTERNAL_GENERATION_TEST_LOG:?}"
FAKE_MAKE
chmod 700 "$fake_make"

EXTERNAL_GENERATION_TEST_LOG="$apply_log" \
MAKE_COMMAND="$fake_make" \
  "$driver" ptree jaxa-ptree firms nasa-firms topology network-topology \
  > "$temporary_dir/output"

cat > "$temporary_dir/expected" <<'EXPECTED'
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

if EXTERNAL_GENERATION_TEST_LOG="$temporary_dir/invalid.log" \
     MAKE_COMMAND="$fake_make" "$driver" unknown \
     > "$temporary_dir/invalid-output" 2>&1; then
  echo 'unknown external pass unexpectedly succeeded' >&2
  exit 1
fi
test ! -e "$temporary_dir/invalid.log"

printf '%s\n' 'authorized external generation driver tests passed'
