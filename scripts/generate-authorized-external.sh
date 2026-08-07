#!/usr/bin/env bash

# Run the mutating workflows for optional passes after Make has authorized all
# of them. This script is the recipe driver; use the public Make target so the
# read-only authorization prerequisite cannot be skipped accidentally.

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

declare -A requested=()
for pass in "$@"; do
  case "$pass" in
    jaxa-ptree|ptree) requested[jaxa-ptree]=1 ;;
    nasa-firms|firms) requested[nasa-firms]=1 ;;
    network-topology|topology) requested[network-topology]=1 ;;
    *) usage ;;
  esac
done

run_make()
{
  local description=$1
  shift
  printf 'external generation: %s\n' "$description"
  "$make_command" --no-print-directory "$@"
}

for pass in jaxa-ptree nasa-firms network-topology; do
  [[ -n ${requested[$pass]:-} ]] || continue
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
      run_make 'fetching the global Anthropocene refresh with NASA FIRMS' \
        fetch-anthropocene-data
      run_make 'preparing the Anthropocene review candidate' \
        prepare-anthropocene-data
      printf '%s\n' \
        'external generation: NASA FIRMS candidate is ready for maintainer review' \
        'external generation: no Anthropocene release artifact was rendered from the unpromoted candidate'
      ;;
    network-topology)
      run_make 'rendering licensed network-topology SVG, PDF, and PNG artifacts' \
        generate-network-infrastructure-topology-artifacts
      ;;
  esac
done

printf '%s\n' 'external generation: requested optional workflows completed'
