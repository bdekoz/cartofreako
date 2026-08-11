#!/usr/bin/env bash

# Select locally configured optional passes, install the pinned JAXA trust
# anchor when needed, authorize the complete selection, and only then run the
# mutating source and artifact workflows.

set -euo pipefail

usage()
{
  printf '%s\n' \
    'usage: generate-authorized-external.sh PASS [PASS ...]' \
    'passes: jaxa-ptree nasa-firms network-topology' >&2
  exit 2
}

fail()
{
  printf 'external generation: %s\n' "$*" >&2
  exit 1
}

test $# -gt 0 || usage

selection_mode=${EXTERNAL_SELECTION_MODE:-strict}
case "$selection_mode" in
  auto|strict) ;;
  *) fail 'EXTERNAL_SELECTION_MODE must be auto or strict' ;;
esac

make_command=${MAKE_COMMAND:-make}
[[ $make_command != *[[:space:]]* ]] \
  || fail 'MAKE_COMMAND must name one executable without shell arguments'
if [[ $make_command == */* ]]; then
  [[ -x $make_command ]] || fail "Make executable is unavailable: $make_command"
else
  command -v "$make_command" >/dev/null 2>&1 \
    || fail "Make executable is unavailable: $make_command"
fi

repository_root=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd -P)
cd "$repository_root"

external_authorizer=${EXTERNAL_AUTHORIZER:-scripts/authorize-external.sh}
[[ -x $external_authorizer ]] \
  || fail "external authorizer is unavailable: $external_authorizer"

declare -A requested=()
for pass in "$@"; do
  case "$pass" in
    jaxa-ptree|ptree) requested[jaxa-ptree]=1 ;;
    nasa-firms|firms) requested[nasa-firms]=1 ;;
    network-topology|topology) requested[network-topology]=1 ;;
    *) usage ;;
  esac
done

declare -A selected=()
if [[ $selection_mode == strict ]]; then
  for pass in jaxa-ptree nasa-firms network-topology; do
    [[ -n ${requested[$pass]:-} ]] && selected[$pass]=1
  done
else
  netrc=${PTREE_NETRC:-${HOME:?HOME is required}/.netrc}
  if [[ -n ${requested[jaxa-ptree]:-} ]]; then
    if [[ -f $netrc ]] && awk '
      tolower($1) == "machine" && $2 == "ftp.ptree.jaxa.jp" { found = 1 }
      END { exit found ? 0 : 1 }
    ' "$netrc"; then
      selected[jaxa-ptree]=1
    else
      printf '%s\n' \
        'external generation: skipping jaxa-ptree (no P-Tree netrc entry)'
    fi
  fi
  if [[ -n ${requested[nasa-firms]:-} ]]; then
    if [[ -n ${FIRMS_MAP_KEY:-} ]]; then
      selected[nasa-firms]=1
    else
      printf '%s\n' \
        'external generation: skipping nasa-firms (FIRMS_MAP_KEY is unset)'
    fi
  fi
  if [[ -n ${requested[network-topology]:-} ]]; then
    if [[ ${NETWORK_TOPOLOGY_LICENSE_ACCEPTED:-} == CC-BY-NC-SA-3.0 ]]; then
      selected[network-topology]=1
    else
      printf '%s\n' \
        'external generation: skipping network-topology (license acknowledgement is unset)'
    fi
  fi
fi

selected_passes=()
for pass in jaxa-ptree nasa-firms network-topology; do
  [[ -n ${selected[$pass]:-} ]] && selected_passes+=("$pass")
done
((${#selected_passes[@]} > 0)) \
  || fail 'no optional external workflows are locally configured'

run_make()
{
  local description=$1
  shift
  printf 'external generation: %s\n' "$description"
  "$make_command" --no-print-directory "$@"
}

if [[ -n ${selected[jaxa-ptree]:-} ]]; then
  cacert=${PTREE_CACERT:-}
  if [[ -z $cacert ]]; then
    data_home=${XDG_DATA_HOME:-${HOME:?HOME is required}/.local/share}
    cacert=$data_home/cartofreako/certs/secom-tls-rsa-root-ca-2024.pem
  fi
  if [[ ! -r $cacert ]]; then
    certificate_installer=${JAXA_CERTIFICATE_INSTALLER:-scripts/install-jaxa-certificate.sh}
    [[ -x $certificate_installer ]] \
      || fail "JAXA certificate installer is unavailable: $certificate_installer"
    printf '%s\n' \
      'external generation: installing the verified JAXA P-Tree trust anchor'
    "$certificate_installer"
    [[ -r $cacert ]] \
      || fail "certificate installer did not create a readable file: $cacert"
  fi
fi

printf 'external generation: authorizing'
printf ' %s' "${selected_passes[@]}"
printf '\n'
"$external_authorizer" "${selected_passes[@]}"

for pass in jaxa-ptree nasa-firms network-topology; do
  [[ -n ${selected[$pass]:-} ]] || continue
  case "$pass" in
    jaxa-ptree)
      run_make 'fetching the JAXA P-Tree snapshot' \
        fetch-cloud-atmosphere-data
      run_make 'preparing the cloud-atmosphere snapshot' \
        prepare-cloud-atmosphere-data
      run_make 'verifying the cloud-atmosphere snapshot' \
        verify-cloud-atmosphere-data
      run_make 'rendering cloud-atmosphere SVG, PDF, and PNG artifacts' \
        generate-cloud-atmosphere-artifacts
      ;;
    nasa-firms)
      run_make 'fetching the 2025/2026 particulate refresh with NASA FIRMS' \
        fetch-anthropocene-particulate-data
      run_make 'preparing the 2025/2026 particulate review candidates' \
        prepare-anthropocene-particulate-data
      printf '%s\n' \
        'external generation: NASA FIRMS candidates are ready for maintainer review' \
        'external generation: no particulate release artifact was rendered from an unpromoted candidate'
      ;;
    network-topology)
      run_make 'rendering licensed network-topology SVG, PDF, and PNG artifacts' \
        generate-network-infrastructure-topology-artifacts
      ;;
  esac
done

authorization_state=${EXTERNAL_AUTHORIZATION_STATE:-.cartofreako/authorized-external-passes}
[[ $authorization_state = /* ]] \
  || authorization_state=$repository_root/$authorization_state
state_directory=$(dirname "$authorization_state")
mkdir -p "$state_directory"
state_temporary=$(mktemp "$state_directory/.authorized-external-passes.XXXXXX")
trap 'rm -f -- "$state_temporary"' EXIT
{
  if [[ -r $authorization_state ]]; then
    sed -n \
      '/^jaxa-ptree$/p;/^nasa-firms$/p;/^network-topology$/p' \
      "$authorization_state"
  fi
  printf '%s\n' "${selected_passes[@]}"
} | sort -u > "$state_temporary"
chmod 600 "$state_temporary"
mv -f "$state_temporary" "$authorization_state"
trap - EXIT

printf '%s\n' \
  'external generation: requested optional workflows completed' \
  "external generation: enabled passes recorded in $authorization_state"
