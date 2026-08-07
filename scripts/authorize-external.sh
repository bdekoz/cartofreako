#!/usr/bin/env bash

# Validate local authorization for optional, externally gated generation passes.

set -euo pipefail

usage()
{
  printf '%s\n' \
    'usage: authorize-external.sh PASS [PASS ...]' \
    'passes: jaxa-ptree nasa-firms network-topology' >&2
  exit 2
}

fail()
{
  printf 'external authorization: %s\n' "$*" >&2
  exit 1
}

for command in curl awk sed stat mktemp; do
  command -v "$command" >/dev/null 2>&1 \
    || fail "missing prerequisite: $command"
done

test $# -gt 0 || usage
temporary_dir=$(mktemp -d /tmp/cartofreako-authorize-external.XXXXXX)
trap 'rm -rf -- "$temporary_dir"' EXIT

authorize_ptree()
{
  local netrc=${PTREE_NETRC:-${HOME:?HOME is required}/.netrc}
  test -f "$netrc" || fail "P-Tree netrc is missing: $netrc"
  local mode
  mode=$(stat -Lc '%a' "$netrc")
  [[ $mode =~ ^[0-7]{3,4}$ ]] || fail "cannot interpret P-Tree netrc mode"
  local permissions=$((8#$mode))
  (( (permissions & 077) == 0 )) \
    || fail "P-Tree netrc must not grant group or other permissions"
  awk '
    tolower($1) == "machine" && $2 == "ftp.ptree.jaxa.jp" { found = 1 }
    END { exit found ? 0 : 1 }
  ' "$netrc" || fail "P-Tree netrc has no ftp.ptree.jaxa.jp machine entry"

  local cacert=${PTREE_CACERT:-}
  if [[ -z $cacert ]]; then
    local data_home=${XDG_DATA_HOME:-${HOME:?HOME is required}/.local/share}
    local installed_cacert=$data_home/cartofreako/certs/secom-tls-rsa-root-ca-2024.pem
    if [[ -r $installed_cacert ]]; then
      cacert=$installed_cacert
    fi
  fi
  local -a ca_arguments=()
  if [[ -n $cacert ]]; then
    [[ $cacert = /* ]] || fail 'PTREE_CACERT must be an absolute path'
    [[ -r $cacert ]] || fail "P-Tree CA certificate is not readable: $cacert"
    ca_arguments=(--cacert "$cacert")
  fi
  curl --fail --silent --show-error --ssl-reqd --netrc-file "$netrc" \
    "${ca_arguments[@]}" --list-only --connect-timeout 20 --max-time 60 \
    'ftps://ftp.ptree.jaxa.jp:990/pub/himawari/L2/CLP/010/' \
    --output "$temporary_dir/ptree-listing"
  test -s "$temporary_dir/ptree-listing" \
    || fail "P-Tree authorization returned an empty listing"
  printf '%s\n' 'external authorization: JAXA P-Tree verified'
}

authorize_firms()
{
  test -n "${FIRMS_MAP_KEY:-}" \
    || fail "FIRMS_MAP_KEY is required for NASA FIRMS"
  local curl_config="$temporary_dir/firms.curl-config"
  umask 077
  printf 'url = "%s"\n' \
    "https://firms.modaps.eosdis.nasa.gov/api/data_availability/csv/${FIRMS_MAP_KEY}/ALL" \
    > "$curl_config"
  curl --fail --silent --show-error --location \
    --connect-timeout 20 --max-time 60 --config "$curl_config" \
    --output "$temporary_dir/firms-availability.csv"
  local heading
  heading=$(sed -n '1p' "$temporary_dir/firms-availability.csv")
  heading=${heading%$'\r'}
  test "$heading" = 'data_id,min_date,max_date' \
    || fail "NASA FIRMS authorization returned an unexpected response"
  printf '%s\n' 'external authorization: NASA FIRMS verified'
}

authorize_topology()
{
  test "${NETWORK_TOPOLOGY_LICENSE_ACCEPTED:-}" = 'CC-BY-NC-SA-3.0' \
    || fail 'set NETWORK_TOPOLOGY_LICENSE_ACCEPTED=CC-BY-NC-SA-3.0 after reviewing the source terms'
  local checker=${NETWORK_INFRASTRUCTURE_SOURCE_CHECKER:-scripts/check-network-infrastructure-sources.sh}
  test -x "$checker" || fail "network source checker is unavailable: $checker"
  "$checker" topology \
    "${NETWORK_INFRASTRUCTURE_CLOUD_SOURCE:?cloud source root is required}" \
    "${SUBMARINE_CABLE_SOURCE:?submarine-cable source root is required}" \
    "${INTERNET_EXCHANGE_SOURCE:?internet-exchange source root is required}"
  printf '%s\n' 'external authorization: network topology license opt-in and sources verified'
}

declare -A requested=()
for pass in "$@"; do
  case "$pass" in
    jaxa-ptree|ptree) requested[jaxa-ptree]=1 ;;
    nasa-firms|firms) requested[nasa-firms]=1 ;;
    network-topology|topology) requested[network-topology]=1 ;;
    *) usage ;;
  esac
done

for pass in jaxa-ptree nasa-firms network-topology; do
  [[ -n ${requested[$pass]:-} ]] || continue
  case "$pass" in
    jaxa-ptree) authorize_ptree ;;
    nasa-firms) authorize_firms ;;
    network-topology) authorize_topology ;;
  esac
done
printf '%s\n' 'external authorization: requested optional passes are ready'
