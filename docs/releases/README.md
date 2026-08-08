# Publishing releases

[Documentation index](../../index.md) ·
[Generation pipeline](../generation.md) ·
[Prerequisites and hardware](../prerequisites.md) ·
[`v20260808` release notes](v20260808.md) ·
[`v13` S3 publication](s3-v13.md) ·
[`v20260807` release notes](v20260807.md) ·
[`v12` S3 publication](s3-v12.md) ·
[`v20260806` release notes](v20260806.md)

Cartofreako releases have two deliberately separate parts:

1. a date-named Git tag supplies the source tree; and
2. large generated outputs are uploaded to that GitHub release as static
   assets rather than committed to Git.

Treat release assets as immutable snapshots. Never replace an uploaded file
with different bytes under the same tag and filename. Publish a new tag and
asset name when either the source or generated payload changes.

The current browser-facing mirror is generated assets v13 at the immutable
Berkeley S3 prefix `cartofreako/v13/`. It exposes the projection-organized
tree for GitHub Pages while retaining the XZ recovery package, manifest, and a
last-written completion marker. Follow the [S3 v13 publication and
implementation notes](s3-v13.md); the GitHub source tag remains unchanged.
Successful applied uploads now finish by generating the Devastation Pacific
Active Archive HTML/PDF report and rendered QA pages. Reports are local delivery
artifacts outside the immutable prefix and Git; their verification and delivery
record belongs in the versioned publication notes.

## `v20260808` release procedure

Stage 13 uses source tag `v20260808`, static asset
`assets.generated.v13.tar.xz`, and the projection-first 885-file artifact
tree. Before packaging, run the native, browser/WebAssembly, and exact artifact
checks recorded in the [release notes](v20260808.md). The release render must
contain 205 SVGs, 84 adjacent resource SVG gzip companions, 205 PDFs, 205
full-size PNGs, and 186 thumbnails.

Create the reproducible archive only after the source commit is final. The
archive timestamp is the tagged commit time; ownership and modes are
normalized, and every member remains under `assets.generated/`:

```sh
release_tag=v20260808
release_commit=$(git rev-parse "$release_tag^{commit}")
source_date_epoch=$(git show -s --format=%ct "$release_commit")
tar --sort=name \
  --mtime="@$source_date_epoch" \
  --owner=0 --group=0 --numeric-owner \
  --mode='u+rwX,go+rX,go-w' \
  --format=posix \
  --pax-option=delete=atime,delete=ctime \
  --create --file=- assets.generated | \
  xz --threads=0 -9e > assets.generated.v13.tar.xz
```

Preflight the sealed package and record its digest and byte counts in
`v20260808.md`:

```sh
xz --test assets.generated.v13.tar.xz
test "$(tar --list --file=assets.generated.v13.tar.xz | sed -n '1p')" = \
  'assets.generated/'
test "$(tar --list --file=assets.generated.v13.tar.xz | \
  sed -n '/\/$/!p' | wc -l)" -eq 885
sha256sum assets.generated.v13.tar.xz
```

Push the already-created source tag explicitly. The release notes intentionally
begin with body text; GitHub supplies the one and only announcement title:

```sh
git push origin main
git push origin refs/tags/v20260808
gh release create v20260808 \
  --repo bdekoz/cartofreako \
  --verify-tag \
  --title 'v20260808 — generated assets v13 and Stage 13' \
  --notes-file docs/releases/v20260808.md \
  'assets.generated.v13.tar.xz#Projection-organized SVG, PDF, PNG, and thumbnail bundle (XZ)'
```

Download the GitHub object into a fresh directory and compare it to the local
package before constructing the S3 release:

```sh
release_verify_dir=$(mktemp -d /tmp/cartofreako-v20260808.XXXXXX)
gh release download v20260808 \
  --repo bdekoz/cartofreako \
  --pattern 'assets.generated.v13.tar.xz' \
  --dir "$release_verify_dir"
test "$(sha256sum assets.generated.v13.tar.xz | awk '{print $1}')" = \
  "$(sha256sum "$release_verify_dir/assets.generated.v13.tar.xz" | awk '{print $1}')"
xz --test "$release_verify_dir/assets.generated.v13.tar.xz"
```

Finally build and publish the immutable S3 prefix. The applied uploader writes
`release.json` last, optionally reads every object back, builds only the
canonical Active Archive check-in report, and performs the report-notification
handoff:

```sh
scripts/build-generated-assets-s3-release.sh
scripts/upload-generated-assets-s3-release.sh --validate-only
scripts/upload-generated-assets-s3-release.sh --apply --verify-download
```

Do not move `v20260808` or replace either public artifact after publication.
A correction requires a new source tag, generated-assets version, and S3
prefix.

## `v20260807` release procedure

The Stage 12 release keeps the date-based source tag and independently
versions the generated static bundle:

```text
tag:       v20260807
commit:    2bd3d760fef540addfcbb4f8002ef7b283d8000f
asset:     assets.generated.v12.tar.xz
sha256:    dc1d761def31d77a05a7cc42f9bc0705ee864046f2e235f50c701c9c42fe960a
```

Run the immutable-object and package preflight from the repository root:

```sh
test "$(git rev-parse \
  2bd3d760fef540addfcbb4f8002ef7b283d8000f^{commit})" = \
  2bd3d760fef540addfcbb4f8002ef7b283d8000f
test -f assets.generated.v12.tar.xz
printf '%s  %s\n' \
  dc1d761def31d77a05a7cc42f9bc0705ee864046f2e235f50c701c9c42fe960a \
  assets.generated.v12.tar.xz | sha256sum --check -
xz --test assets.generated.v12.tar.xz
test "$(tar --list --file=assets.generated.v12.tar.xz | wc -l)" -eq 679
test "$(tar --list --file=assets.generated.v12.tar.xz | sed -n '1p')" = \
  'assets.generated/'
```

Create and push the lightweight tag at the pinned source revision. Fetch only
the branch here: historical local tags may intentionally differ from their
remote counterparts and are outside this release's scope.

```sh
release_commit=2bd3d760fef540addfcbb4f8002ef7b283d8000f
git fetch --no-tags origin main
git tag v20260807 "$release_commit"
git push origin refs/tags/v20260807
test "$(git rev-list -n 1 v20260807)" = "$release_commit"
```

The notes file intentionally begins with body text. The GitHub release name
supplies the single displayed title:

```sh
gh release create v20260807 \
  --repo bdekoz/cartofreako \
  --verify-tag \
  --title 'v20260807 — generated assets v12 and Stage 12' \
  --notes-file docs/releases/v20260807.md \
  'assets.generated.v12.tar.xz#Generated SVG, PDF, PNG, and Cahill-Keyes thumbnail bundle (XZ)'
```

Download the uploaded bytes into a new directory and verify them independently
of the source copy:

```sh
release_verify_dir=$(mktemp -d /tmp/cartofreako-v20260807.XXXXXX)
gh release download v20260807 \
  --repo bdekoz/cartofreako \
  --pattern 'assets.generated.v12.tar.xz' \
  --dir "$release_verify_dir"
printf '%s  %s\n' \
  dc1d761def31d77a05a7cc42f9bc0705ee864046f2e235f50c701c9c42fe960a \
  "$release_verify_dir/assets.generated.v12.tar.xz" | sha256sum --check -
xz --test "$release_verify_dir/assets.generated.v12.tar.xz"
```

Do not move `v20260807` after publication. Later documentation commits may
describe the release, but the tag, announcement, and manifest must continue to
identify `2bd3d760fef540addfcbb4f8002ef7b283d8000f`.

## `v20260806` release procedure

This historical tag follows the existing lightweight, date-based convention.
It must continue to resolve to its pinned source commit even though the
runbook was committed later:

```text
tag:       v20260806
commit:    cfe1f8ff15feadec8f3a0c88a9d66648040e61dd
asset:     assets.generated.v10.tar.xz
sha256:    5256927f2ac7702d35b1450a45d8bca69b47dc2e9e13b2def1160231e5b8705a
```

Run the preflight from the repository root:

```sh
test "$(git rev-parse HEAD)" = \
  cfe1f8ff15feadec8f3a0c88a9d66648040e61dd
test -f assets.generated.v10.tar.xz
printf '%s  %s\n' \
  5256927f2ac7702d35b1450a45d8bca69b47dc2e9e13b2def1160231e5b8705a \
  assets.generated.v10.tar.xz | sha256sum --check -
xz --test assets.generated.v10.tar.xz
test "$(tar --list --file=assets.generated.v10.tar.xz | wc -l)" -eq 433
```

The documentation working tree does not have to be at the release commit to
publish the already-pinned source revision. In that case, replace only the
first preflight assertion with this object check:

```sh
test "$(git rev-parse \
  cfe1f8ff15feadec8f3a0c88a9d66648040e61dd^{commit})" = \
  cfe1f8ff15feadec8f3a0c88a9d66648040e61dd
```

Create and push the lightweight tag explicitly. `--verify-tag` below then
prevents GitHub CLI from silently creating a tag at another revision:

```sh
release_commit=cfe1f8ff15feadec8f3a0c88a9d66648040e61dd
git fetch origin --tags
git tag v20260806 "$release_commit"
git push origin refs/tags/v20260806
test "$(git rev-list -n 1 v20260806)" = "$release_commit"
```

Publish the source tag and static bundle as one GitHub release:

The notes file intentionally begins with body text rather than repeating the
release title as a Markdown heading. GitHub renders the `--title` value above
the notes body.

```sh
gh release create v20260806 \
  --repo bdekoz/cartofreako \
  --verify-tag \
  --title 'v20260806 — generated assets v10 and Stage 10' \
  --notes-file docs/releases/v20260806.md \
  'assets.generated.v10.tar.xz#Generated SVG, PDF, and PNG bundle (XZ)'
```

Finally, download the uploaded bytes into a new directory and verify them
independently of the source copy:

```sh
release_verify_dir=$(mktemp -d /tmp/cartofreako-v20260806.XXXXXX)
gh release download v20260806 \
  --repo bdekoz/cartofreako \
  --pattern 'assets.generated.v10.tar.xz' \
  --dir "$release_verify_dir"
printf '%s  %s\n' \
  5256927f2ac7702d35b1450a45d8bca69b47dc2e9e13b2def1160231e5b8705a \
  "$release_verify_dir/assets.generated.v10.tar.xz" | sha256sum --check -
xz --test "$release_verify_dir/assets.generated.v10.tar.xz"
gh release view v20260806 --repo bdekoz/cartofreako --web
```

Do not move `v20260806` to a documentation commit after publishing. A later
documentation-only commit may describe the release, but the public tag and
the manifest in [`v20260806.md`](v20260806.md) must continue to identify
`cfe1f8ff15feadec8f3a0c88a9d66648040e61dd`.
