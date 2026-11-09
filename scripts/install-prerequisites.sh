#!/bin/sh
# Install missing native dependencies, then run the same checks as Make.
set -eu

dry_run=0
case ${1:-} in
  '') ;;
  --dry-run) dry_run=1; shift ;;
  *) echo "usage: $0 [--dry-run]" >&2; exit 2 ;;
esac
[ "$#" -eq 0 ] || { echo "usage: $0 [--dry-run]" >&2; exit 2; }

script_directory=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
repository_root=$(CDPATH= cd -- "$script_directory/.." && pwd)
workspace_root=$(dirname -- "$repository_root")

run()
{
  printf '  +'
  for argument do printf ' %s' "$argument"; done
  printf '\n'
  if [ "$dry_run" -eq 0 ]; then "$@"; fi
}

as_root()
{
  if [ "$(id -u)" -eq 0 ]; then
    run "$@"
  else
    if ! command -v sudo >/dev/null 2>&1; then
      echo 'sudo is required to install system packages; run this script as root or install sudo.' >&2
      exit 1
    fi
    run sudo "$@"
  fi
}

case $(uname -s) in
  Linux)
    # Override permits testing a distribution without changing the host.
    os_release=${PREREQUISITE_OS_RELEASE:-/etc/os-release}
    if [ ! -r "$os_release" ]; then
      echo "Cannot identify the distribution: $os_release is unavailable" >&2
      exit 2
    fi
    ID= ID_LIKE=
    . "$os_release"
    case " $ID $ID_LIKE " in
      *' fedora '*|*' rhel '*|*' centos '*) platform=fedora ;;
      *' debian '*|*' ubuntu '*) platform=debian ;;
      *) echo "Unsupported distribution: $ID; see docs/pages/getting-started/prerequisites.md" >&2; exit 2 ;;
    esac
    ;;
  Darwin) platform=macos ;;
  *) echo 'Use Fedora, Debian/Ubuntu (including WSL), or macOS with Homebrew.' >&2; exit 2 ;;
esac

printf 'Installing missing native prerequisites for %s:\n' "$platform"
case $platform in
  fedora)
    set --
    for package in gcc-c++ make git bash python3 curl jq unzip tar gzip findutils \
        ripgrep coreutils fontconfig gdal gdal-devel geos geos-devel \
        rapidjson-devel h3 h3-devel inkscape doxygen; do
      if ! rpm -q "$package" >/dev/null 2>&1; then set -- "$@" "$package"; fi
    done
    if [ "$#" -gt 0 ]; then as_root dnf install -y "$@"; fi
    ;;
  debian)
    set --
    for package in build-essential git bash python3 curl jq unzip tar gzip \
        findutils ripgrep coreutils fontconfig fonts-atkinson-hyperlegible \
        gdal-bin libgdal-dev libgeos-dev rapidjson-dev libh3-dev inkscape doxygen; do
      status=$(dpkg-query -W -f='${Status}' "$package" 2>/dev/null || :)
      if [ "$status" != 'install ok installed' ]; then set -- "$@" "$package"; fi
    done
    if [ "$#" -gt 0 ]; then
      as_root apt-get update
      as_root apt-get install -y "$@"
    fi
    ;;
  macos)
    if ! command -v brew >/dev/null 2>&1; then
      echo 'Install Homebrew from https://brew.sh, then rerun make install-prerequisites.' >&2
      exit 1
    fi
    if ! xcode-select -p >/dev/null 2>&1; then
      run xcode-select --install
      echo 'Finish the Apple command-line developer tools installer, then rerun make install-prerequisites.' >&2
      exit 1
    fi
    set --
    for package in make gdal h3 rapidjson coreutils git ripgrep jq python doxygen fontconfig; do
      if ! brew list --formula "$package" >/dev/null 2>&1; then set -- "$@" "$package"; fi
    done
    if [ "$#" -gt 0 ]; then run brew install "$@"; fi
    set --
    for package in inkscape font-atkinson-hyperlegible; do
      if ! brew list --cask "$package" >/dev/null 2>&1; then set -- "$@" "$package"; fi
    done
    if [ "$#" -gt 0 ]; then run brew install --cask "$@"; fi
    if [ "$dry_run" -eq 0 ]; then
      PATH="$(brew --prefix coreutils)/libexec/gnubin:$PATH"
      export PATH
    fi
    ;;
esac

# Use the original font family, rather than silently substituting "Next".
label_font=${LABEL_FONT:-${CARTOFREAKO_LABEL_FONT:-atkinson_hyperlegible}}
case $label_font in
  atkinson_hyperlegible|'Atkinson Hyperlegible') label_font_family='Atkinson Hyperlegible' ;;
  *) label_font_family=$label_font ;;
esac
matched_font=
if command -v fc-match >/dev/null 2>&1; then
  matched_font=$(fc-match -f '%{family}' "$label_font_family")
fi
if [ "${matched_font%%,*}" != "$label_font_family" ]; then
  if [ "$label_font_family" != 'Atkinson Hyperlegible' ]; then
    echo "Install the configured font '$label_font_family', or rerun with LABEL_FONT=atkinson_hyperlegible." >&2
    exit 1
  fi
  if [ "$platform" = macos ]; then
    font_directory="$HOME/Library/Fonts/AtkinsonHyperlegible"
  else
    font_directory="${XDG_DATA_HOME:-$HOME/.local/share}/fonts/AtkinsonHyperlegible"
  fi
  printf 'Installing original Atkinson Hyperlegible fonts into %s\n' "$font_directory"
  if [ "$dry_run" -eq 0 ]; then
    font_stage=$(mktemp -d)
    trap 'rm -rf -- "$font_stage"' 0
    trap 'exit 129' HUP
    trap 'exit 130' INT
    trap 'exit 143' TERM
    font_base=https://raw.githubusercontent.com/google/fonts/main/ofl/atkinsonhyperlegible
    for face in Regular Italic Bold BoldItalic; do
      filename="AtkinsonHyperlegible-$face.ttf"
      curl --fail --location --silent --show-error --output "$font_stage/$filename" "$font_base/$filename"
      family=$(fc-scan --format '%{family}' "$font_stage/$filename")
      if [ "${family%%,*}" != 'Atkinson Hyperlegible' ]; then
        echo "Downloaded font has an unexpected family: $filename" >&2
        exit 1
      fi
    done
    curl --fail --location --silent --show-error --output "$font_stage/OFL.txt" "$font_base/OFL.txt"
    mkdir -p "$font_directory"
    install -m 0644 "$font_stage/"* "$font_directory/"
    fc-cache -f "$font_directory"
    rm -rf -- "$font_stage"
    trap - 0 HUP INT TERM
  fi
fi

# Populate missing documented sibling repositories. Existing trees are never
# pulled, reset or checked out; their contents are verified by the checker.
clone_missing()
{
  destination=$1
  url=$2
  revision=${3:-}
  if [ -e "$destination" ]; then return; fi
  run mkdir -p "$(dirname -- "$destination")"
  run git clone "$url" "$destination"
  if [ -n "$revision" ]; then run git -C "$destination" checkout "$revision"; fi
}

alpha60_src=${ALPHA60_SRC:-$workspace_root/alpha60/src}
izzi_src=${IZZI_SRC:-$workspace_root/izzi/src}
clone_missing "$(dirname -- "$alpha60_src")" https://github.com/bdekoz/alpha60.git
clone_missing "$(dirname -- "$izzi_src")" https://github.com/bdekoz/izzi.git
clone_missing "${NETWORK_INFRASTRUCTURE_CLOUD_SOURCE:-$workspace_root/cloud_cdn_cache}" \
  https://github.com/bdekoz/cloud_cdn_cache.git 1be1eb04e73320e0337a74a99686cd532f09ad9b
clone_missing "${SUBMARINE_CABLE_SOURCE:-$workspace_root/www.submarinecablemap.com}" \
  https://github.com/telegeography/www.submarinecablemap.com.git

if [ "$dry_run" -eq 1 ]; then
  echo 'Dry run complete; no packages, fonts or repositories were changed.'
  exit 0
fi
exec "$script_directory/check-prerequisites.sh"
