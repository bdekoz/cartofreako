#!/bin/sh

# Check the installed tools and headers documented in docs/prerequisites.md.
# Required native dependencies make this script fail; optional WebAssembly
# dependencies are reported without changing the exit status.

set -u
set -f

usage()
{
  printf '%s\n' \
    "usage: $0" \
    "   or: $0 MAKE_VERSION CXX CPPFLAGS CXXFLAGS ALPHA60_SRC IZZI_SRC GDAL_CONFIG INKSCAPE DOXYGEN EMXX EMRUN NODE WEB_BROWSER" >&2
}

no_argument_mode=0
case $# in
  0)
    no_argument_mode=1
    script_directory=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
    repository_root=$(CDPATH= cd -- "$script_directory/.." && pwd)
    workspace_root=$(CDPATH= cd -- "$repository_root/.." && pwd)

    make_command=${MAKE:-make}
    make_version=${MAKE_VERSION:-}
    if [ -z "$make_version" ]; then
      make_version=$($make_command --version 2>/dev/null \
        | sed -n '1s/^GNU Make //p')
    fi

    cxx=${CXX:-g++}
    cppflags=${CPPFLAGS:-}
    if [ -z "$cppflags" ]; then
      cppflags="-I$repository_root/src.projections -I$repository_root/src.generate"
    fi
    cxxflags=${CXXFLAGS:-}
    if [ -z "$cxxflags" ]; then
      cxxflags='-std=c++20 -Wall -Wextra -Wpedantic -Werror'
    fi
    alpha60_src=${ALPHA60_SRC:-$workspace_root/alpha60/src}
    izzi_src=${IZZI_SRC:-$workspace_root/izzi/src}
    gdal_config=${GDAL_CONFIG:-gdal-config}
    inkscape=${INKSCAPE:-inkscape}
    doxygen=${DOXYGEN:-doxygen}
    emxx=${EMXX:-$workspace_root/emsdk/upstream/emscripten/em++}
    emrun=${EMRUN:-$workspace_root/emsdk/upstream/emscripten/emrun}
    node=${NODE:-node}
    web_browser=${WEB_BROWSER:-}
    ;;
  13)
    make_version=$1
    cxx=$2
    cppflags=$3
    cxxflags=$4
    alpha60_src=$5
    izzi_src=$6
    gdal_config=$7
    inkscape=$8
    doxygen=$9
    shift 9
    emxx=$1
    emrun=$2
    node=$3
    web_browser=$4
    ;;
  *)
    usage
    exit 2
    ;;
esac

required_failures=0
optional_missing=0

pass()
{
  printf '  ok        %s\n' "$1"
}

fail()
{
  printf '  MISSING   %s\n' "$1"
  required_failures=$((required_failures + 1))
}

optional_fail()
{
  printf '  optional  %s (not found)\n' "$1"
  optional_missing=$((optional_missing + 1))
}

command_available()
{
  [ -n "$1" ] || return 1

  # First preserve an executable path containing spaces. If the value is a
  # command plus arguments (as CXX sometimes is), check its first word.
  command -v "$1" >/dev/null 2>&1 && return 0
  command_name=${1%% *}
  [ "$command_name" != "$1" ] \
    && command -v "$command_name" >/dev/null 2>&1
}

check_required_tool()
{
  if command_available "$2"; then
    pass "$1 ($2)"
  else
    fail "$1 ($2)"
  fi
}

check_optional_tool()
{
  if command_available "$2"; then
    pass "$1 ($2)"
  else
    optional_fail "$1 ($2)"
  fi
}

check_required_file()
{
  if [ -r "$2" ]; then
    pass "$1 ($2)"
  else
    fail "$1 ($2)"
  fi
}

show_log()
{
  if [ -s "$1" ]; then
    sed -n '1,12{s/^/      /;p;}' "$1"
  fi
}

if [ "$no_argument_mode" -eq 1 ]; then
  printf 'Using no-argument configuration rooted at %s\n\n' \
    "$repository_root"
fi

printf '%s\n' 'Checking required native prerequisites:'

if [ -n "$make_version" ]; then
  pass "GNU Make ($make_version)"
else
  fail "GNU Make (MAKE_VERSION is empty)"
fi

check_required_tool "Git" "git"
check_required_tool "Bash" "bash"
check_required_tool "curl" "curl"
check_required_tool "unzip" "unzip"
check_required_tool "sha256sum" "sha256sum"
check_required_tool "Coreutils install" "install"
check_required_tool "Coreutils mktemp" "mktemp"
check_required_tool "Coreutils wc" "wc"
check_required_file "Alpha60 header" "$alpha60_src/a60-io.h"
check_required_file "Izzi header" "$izzi_src/a60-svg.h"
check_required_tool "Inkscape" "$inkscape"
check_required_tool "Doxygen" "$doxygen"

tmp_root=${TMPDIR:-/tmp}
tmp_prefix=${tmp_root%/}/cartofreako-prerequisite.
tmp_dir=$(mktemp -d "${tmp_prefix}XXXXXX")
case "$tmp_dir" in
  "$tmp_prefix"*) ;;
  *) tmp_dir= ;;
esac
if [ -z "$tmp_dir" ] || [ ! -d "$tmp_dir" ]; then
  echo "could not create a temporary directory under $tmp_root" >&2
  exit 2
fi
cleanup()
{
  rm -rf -- "$tmp_dir"
}
trap cleanup 0
trap 'exit 129' HUP
trap 'exit 130' INT
trap 'exit 143' TERM

compiler_available=0
if command_available "$cxx"; then
  compiler_available=1
  cat > "$tmp_dir/cxx20.cc" <<'EOF'
#include <filesystem>
#include <numbers>
#include <variant>

#include <rapidjson/document.h>

int
main()
{
  const std::filesystem::path current{"."};
  const std::variant<int, double> value{42};
  rapidjson::Document document;
  document.Parse("{}");
  return (!current.empty() && std::holds_alternative<int>(value)
          && std::numbers::pi > 3.0 && document.IsObject()) ? 0 : 1;
}
EOF

  # These expansions intentionally match the way Make invokes CXX and its
  # flag variables in the project's build recipes.
  if $cxx $cppflags $cxxflags "$tmp_dir/cxx20.cc" \
      -o "$tmp_dir/cxx20" >"$tmp_dir/cxx20.log" 2>&1 \
      && "$tmp_dir/cxx20" >>"$tmp_dir/cxx20.log" 2>&1; then
    pass "C++20 compiler, standard library, and RapidJSON headers ($cxx)"
  else
    fail "C++20 compiler, standard library, and RapidJSON headers ($cxx)"
    show_log "$tmp_dir/cxx20.log"
  fi
else
  fail "C++20 compiler ($cxx)"
fi

gdal_available=0
if command_available "$gdal_config"; then
  if gdal_version=$("$gdal_config" --version 2>/dev/null); then
    gdal_available=1
    pass "GDAL configuration ($gdal_config $gdal_version)"
  else
    fail "working GDAL configuration ($gdal_config --version failed)"
  fi
else
  fail "GDAL development package ($gdal_config)"
fi

if [ "$gdal_available" -eq 1 ]; then
  ogr_enabled=$("$gdal_config" --ogr-enabled 2>/dev/null)
  case "$ogr_enabled" in
    yes|YES) pass "OGR support in GDAL" ;;
    *) fail "OGR support in GDAL (gdal-config --ogr-enabled did not report yes)" ;;
  esac

  if [ "$compiler_available" -eq 1 ] \
      && gdal_cflags=$("$gdal_config" --cflags 2>/dev/null) \
      && gdal_libs=$("$gdal_config" --libs 2>/dev/null); then
    cat > "$tmp_dir/gdal.cc" <<'EOF'
#include <gdal_priv.h>
#include <ogrsf_frmts.h>

int
main()
{
  GDALAllRegister();
  int status = 0;
  if (!OGRGeometryFactory::haveGEOS())
    status |= 1;
  if (GetGDALDriverManager()->GetDriverByName("ESRI Shapefile") == nullptr)
    status |= 2;
  return status;
}
EOF

    if $cxx $cppflags $cxxflags $gdal_cflags "$tmp_dir/gdal.cc" \
        $gdal_libs -o "$tmp_dir/gdal" >"$tmp_dir/gdal-build.log" 2>&1; then
      pass "GDAL development headers and libraries"
      "$tmp_dir/gdal" >"$tmp_dir/gdal-run.log" 2>&1
      gdal_status=$?
      case "$gdal_status" in
        0)
          pass "GEOS support in GDAL"
          pass "GDAL ESRI Shapefile driver"
          ;;
        1)
          fail "GEOS support in GDAL"
          pass "GDAL ESRI Shapefile driver"
          ;;
        2)
          pass "GEOS support in GDAL"
          fail "GDAL ESRI Shapefile driver"
          ;;
        3)
          fail "GEOS support in GDAL"
          fail "GDAL ESRI Shapefile driver"
          ;;
        *)
          fail "GEOS support in GDAL (runtime probe failed)"
          fail "GDAL ESRI Shapefile driver (runtime probe failed)"
          show_log "$tmp_dir/gdal-run.log"
          ;;
      esac
    else
      fail "GDAL development headers and libraries"
      show_log "$tmp_dir/gdal-build.log"
      fail "GEOS support in GDAL (compile probe unavailable)"
      fail "GDAL ESRI Shapefile driver (compile probe unavailable)"
    fi
  else
    fail "GDAL development headers and libraries (compiler or flags unavailable)"
    fail "GEOS support in GDAL (compile probe unavailable)"
    fail "GDAL ESRI Shapefile driver (compile probe unavailable)"
  fi
else
  fail "OGR support in GDAL (gdal-config unavailable)"
  fail "GDAL development headers and libraries (gdal-config unavailable)"
  fail "GEOS support in GDAL (gdal-config unavailable)"
  fail "GDAL ESRI Shapefile driver (gdal-config unavailable)"
fi

printf '\n%s\n' 'Checking optional WebAssembly prerequisites:'
check_optional_tool "Emscripten C++ compiler" "$emxx"
check_optional_tool "emrun local server" "$emrun"
check_optional_tool "Node.js" "$node"

if [ -n "$web_browser" ]; then
  check_optional_tool "Web browser" "$web_browser"
else
  detected_browser=
  for browser in google-chrome-stable google-chrome chromium \
      chromium-browser firefox microsoft-edge; do
    if command_available "$browser"; then
      detected_browser=$browser
      break
    fi
  done
  if [ -n "$detected_browser" ]; then
    pass "Web browser ($detected_browser)"
  elif [ -d "/Applications/Safari.app" ]; then
    pass "Web browser (Safari)"
  else
    optional_fail "Web browser (set WEB_BROWSER to its executable)"
  fi
fi

printf '\n'
if [ "$required_failures" -ne 0 ]; then
  printf '%s required prerequisite check(s) failed. See docs/prerequisites.md.\n' \
    "$required_failures"
  if [ "$optional_missing" -ne 0 ]; then
    printf '%s optional WebAssembly prerequisite(s) were also not found.\n' \
      "$optional_missing"
  fi
  exit 1
fi

if [ "$optional_missing" -ne 0 ]; then
  printf 'All required prerequisites are installed; %s optional WebAssembly prerequisite(s) were not found.\n' \
    "$optional_missing"
else
  printf '%s\n' 'All documented prerequisites are installed.'
fi
