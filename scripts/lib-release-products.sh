#!/usr/bin/env bash
# Shared release-tree product stager.
#
# Sourced by the v14 AAO builder and the top-of-tree preview stager so the
# AAO product layout is emitted by one implementation. It reads an 8-column
# tab-separated case stream on standard input:
#
#   id \t lifecycle \t projection \t svg \t pdf \t png \t screen_png \t screen_webp
#
# Paths are repository-relative. Families are selected by setting these
# variables before calling stage_release_products:
#
#   STAGE_FAMILY_MASTER=1          master/<stem>.svg.gz (gzip unless pre-gzipped)
#   STAGE_FAMILY_PRINT=1           print/<stem>.pdf
#   STAGE_FAMILY_FULL=png|webp|both  full/<stem>.png and/or full/<stem>.webp
#   STAGE_FAMILY_THUMBNAIL=1       thumbnail/<stem>.png (only when it exists)
#   STAGE_FAMILY_SCREEN_PNG=1      screen-1080p/png/<stem>.png
#   STAGE_FAMILY_SCREEN_WEBP=1     screen-1080p/webp/<stem>.webp
#
# For WebP derivation (STAGE_FAMILY_FULL=webp|both):
#   STAGE_WEBP_QUALITY=90          lossy quality 1-100
#   STAGE_WEBP_LOSSLESS=0          set to 1 for lossless
#   STAGE_WEBP_WORKLIST=FILE       append `source|target` pairs here, then run
#                                  convert_staged_webp_worklist
#
# Callers must define `repository_root` before sourcing (or let this file
# derive it), and own everything outside products/: indexes, runtime, viewer,
# README, manifests, hashes, and atomic placement.

if [[ -z ${repository_root:-} ]]; then
  repository_root=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd -P)
fi

release_products_die() {
  printf 'lib-release-products: %s\n' "$*" >&2
  exit 1
}

stage_release_products() {
  local release_root=$1
  local id lifecycle projection svg pdf png screen_png screen_webp
  local product_root stem thumbnail

  while IFS=$'\t' read -r id lifecycle projection svg pdf png screen_png screen_webp; do
    [[ $id && $lifecycle && $projection && $svg && $pdf && $png &&
       $screen_png && $screen_webp ]] ||
      release_products_die "malformed case: ${id:-<empty>}"
    product_root=$release_root/products/$lifecycle/$projection
    stem=$(basename -- "$png" .png)
    mkdir -p -- "$product_root"

    if [[ ${STAGE_FAMILY_MASTER:-0} -eq 1 ]]; then
      mkdir -p -- "$product_root/master"
      [[ -f $repository_root/$svg ]] || release_products_die "missing source SVG: $svg"
      if [[ $svg == *.gz ]]; then
        cp -- "$repository_root/$svg" "$product_root/master/$stem.svg.gz"
      else
        gzip --best --no-name --stdout -- "$repository_root/$svg" \
          > "$product_root/master/$stem.svg.gz"
      fi
    fi

    if [[ ${STAGE_FAMILY_PRINT:-0} -eq 1 ]]; then
      mkdir -p -- "$product_root/print"
      [[ -f $repository_root/$pdf ]] || release_products_die "missing print PDF: $pdf"
      cp -- "$repository_root/$pdf" "$product_root/print/$stem.pdf"
    fi

    case ${STAGE_FAMILY_FULL:-} in
      png)
        mkdir -p -- "$product_root/full"
        [[ -f $repository_root/$png ]] || release_products_die "missing full PNG: $png"
        cp -- "$repository_root/$png" "$product_root/full/$stem.png"
        ;;
      webp)
        mkdir -p -- "$product_root/full"
        [[ -f $repository_root/$png ]] || release_products_die "missing full PNG: $png"
        printf '%s|%s\n' "$repository_root/$png" "$product_root/full/$stem.webp" \
          >> "${STAGE_WEBP_WORKLIST:?STAGE_WEBP_WORKLIST is required for WebP derivation}"
        ;;
      both)
        mkdir -p -- "$product_root/full"
        [[ -f $repository_root/$png ]] || release_products_die "missing full PNG: $png"
        cp -- "$repository_root/$png" "$product_root/full/$stem.png"
        printf '%s|%s\n' "$repository_root/$png" "$product_root/full/$stem.webp" \
          >> "${STAGE_WEBP_WORKLIST:?STAGE_WEBP_WORKLIST is required for WebP derivation}"
        ;;
      "")
        ;;
      *)
        release_products_die "invalid STAGE_FAMILY_FULL: $STAGE_FAMILY_FULL"
        ;;
    esac

    if [[ ${STAGE_FAMILY_THUMBNAIL:-0} -eq 1 ]]; then
      thumbnail=$repository_root/assets.generated/$projection/thumbnail/$stem.png
      if [[ -f $thumbnail ]]; then
        mkdir -p -- "$product_root/thumbnail"
        cp -- "$thumbnail" "$product_root/thumbnail/$stem.png"
      fi
    fi

    if [[ ${STAGE_FAMILY_SCREEN_PNG:-0} -eq 1 ]]; then
      mkdir -p -- "$product_root/screen-1080p/png"
      [[ -f $repository_root/$screen_png ]] ||
        release_products_die "missing screen PNG: $screen_png"
      cp -- "$repository_root/$screen_png" "$product_root/screen-1080p/png/$stem.png"
    fi

    if [[ ${STAGE_FAMILY_SCREEN_WEBP:-0} -eq 1 ]]; then
      mkdir -p -- "$product_root/screen-1080p/webp"
      [[ -f $repository_root/$screen_webp ]] ||
        release_products_die "missing screen WebP: $screen_webp"
      cp -- "$repository_root/$screen_webp" "$product_root/screen-1080p/webp/$stem.webp"
    fi
  done
}

convert_staged_webp_worklist() {
  local worklist=$1
  local jobs=${2:-1}
  local magick_command
  if command -v magick >/dev/null; then
    magick_command=$(command -v magick)
  elif command -v convert >/dev/null; then
    magick_command=$(command -v convert)
  else
    release_products_die 'ImageMagick (magick) is required for full-resolution WebP derivation'
  fi
  [[ -s $worklist ]] || return 0
  export magick_command STAGE_WEBP_QUALITY STAGE_WEBP_LOSSLESS
  < "$worklist" xargs -P "$jobs" -I '{}' bash -c '
    set -e
    line="$1"
    source=${line%|*}
    target=${line#*|}
    if [[ "$STAGE_WEBP_LOSSLESS" == 1 ]]; then
      "$magick_command" "$source" -define webp:lossless=true "$target"
    else
      "$magick_command" "$source" -define webp:quality="$STAGE_WEBP_QUALITY" "$target"
    fi
  ' _ '{}'
}
