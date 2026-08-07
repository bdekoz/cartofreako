# Publishing releases

[Documentation index](../../index.md) ·
[Generation pipeline](../generation.md) ·
[Prerequisites and hardware](../prerequisites.md) ·
[`v20260806` release notes](v20260806.md)

Cartofreako releases have two deliberately separate parts:

1. a date-named Git tag supplies the source tree; and
2. large generated outputs are uploaded to that GitHub release as static
   assets rather than committed to Git.

Treat release assets as immutable snapshots. Never replace an uploaded file
with different bytes under the same tag and filename. Publish a new tag and
asset name when either the source or generated payload changes.

## `v20260806` release procedure

The next tag follows the existing lightweight, date-based tag convention. It
must resolve to the requested source commit, even if this runbook is committed
later:

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
