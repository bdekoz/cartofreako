# Publishing releases

[Documentation index](../../index.md) ·
[Generation pipeline](../generation.md) ·
[Prerequisites and hardware](../prerequisites.md) ·
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

The browser-facing mirror of generated assets v12 is separately published at
the immutable Berkeley S3 prefix `cartofreako/v12/`. It exposes the extracted
tree for GitHub Pages while retaining the XZ recovery package, manifest, and a
last-written completion marker. Follow the [S3 v12 publication and
implementation notes](s3-v12.md); the GitHub source tag remains unchanged.
Successful applied uploads now finish by generating the Devastation Pacific
Active Archive HTML/PDF report and rendered QA pages. Reports are local delivery
artifacts outside the immutable prefix and Git; their verification and delivery
record belongs in the versioned publication notes.

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
