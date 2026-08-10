# GitHub releases and UCB AAO deposits

[Documentation index](../../index.md) ·
[Generation pipeline](../generation.md) ·
[Prerequisites and hardware](../prerequisites.md) ·
[`v20260810` Stage 14 source release](v20260810.md) ·
[`v20260808.1` corrected release notes](v20260808.1.md) ·
[`v20260808` superseded attempt](v20260808.md) ·
[`v13` S3 publication](s3-v13.md) ·
[`v20260807` release notes](v20260807.md) ·
[`v12` S3 publication](s3-v12.md) ·
[`v20260806` release notes](v20260806.md)

Cartofreako has two deliberately different release concepts:

1. **Releasing on GitHub** publishes a date-named source tag and a GitHub
   release. A generated XZ bundle may be attached as a static GitHub asset,
   but it is not required for a source-only release.
2. **Releasing to UCB Active Archive Object Storage (AAO) via S3** deposits an
   independently versioned generated-assets tree under an immutable Cloudian
   prefix. It publishes the completion marker last and produces a transport
   receipt, verification record, and canonical check-in report.

The first operation never invokes, authorizes, or implies the second. There is
no umbrella `release` Make target. `release-github` has no S3 dependency, and
`release-ucb-aao-s3` is deliberately a separate, top-level, interactive-only
target.

For example, a source-only GitHub release uses:

```sh
git tag v20260810 HEAD
make release-github \
  GITHUB_RELEASE_TAG=v20260810 \
  GITHUB_RELEASE_TITLE='v20260810 — Stage 14 reverse projections' \
  GITHUB_RELEASE_NOTES=docs/releases/v20260810.md
```

An eventual generated-assets deposit is a later, separately authorized human
operation. Cartofreako supplies its reviewed profile, staged tree, and receipt
path; the target delegates credentials, immutable grouped transfer,
marker-last publication, and download verification to the shared
`alpha60-clusterops/bin/load-s3-aao` implementation:

```sh
make release-ucb-aao-s3 \
  UCB_AAO_RELEASE_PROFILE=docs/releases/v14-aao-upload-profile.json \
  UCB_AAO_RELEASE_DATA_ROOT=build/s3-release-v14 \
  UCB_AAO_RELEASE_RECEIPT=reports/cartofreako-v14-aao-upload-receipt.json
```

The AAO target must be the only requested Make goal and must run in an
interactive terminal. The shared engine still requires the exact destination
confirmation. Do not call it from CI, another Make target, a GitHub release
script, or an unattended agent workflow.

Treat GitHub assets and AAO objects as immutable snapshots. Never replace an uploaded file
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

## Shared transport and documentation authority

Future releases use the declarative
[`alpha60-clusterops` shared AAO interface](https://github.com/alpha60-devops/alpha60-clusterops/blob/main/docs/storage/shared-aao-upload.md),
whose [profile](https://github.com/alpha60-devops/alpha60-clusterops/blob/main/storage/schemas/aao-upload-profile-v1.schema.json)
and [receipt](https://github.com/alpha60-devops/alpha60-clusterops/blob/main/storage/schemas/aao-upload-receipt-v1.schema.json)
schemas define the cross-project transport contract. Shared implementation
commit `cebba0d8144f46f75997f568e7f5b3a36e4161ef` is the first version adopted
by this repository.

| `alpha60-clusterops` is authoritative for | Cartofreako is authoritative for |
| --- | --- |
| Credential prompts, empty rclone configuration, exact-prefix inspection, immutable grouped copies, marker-last publication, remote checks, and transport receipts | Source/tag/package identity, exact counts and pass requirements, the tracked release profile and validator, gallery URLs, report design, recipients, and observed v13 evidence |
| Profile and receipt schemas, baseline report/automatic-delivery policy, and future shared-engine corrections | Versioned S3 prefix, pilot identities declared by the profile, Devastation Pacific report contents, and delivery evidence |

The Cartofreako adapter never opens a desktop mailer. It writes a Gmail outbox
request after report generation; after inspecting every QA page, the
authenticated release orchestrator consumes that request and sends the
canonical PDF automatically, without a second operator confirmation. The
orchestrator records actual delivery separately from upload completion.

The v13 prefix itself was applied and fully read back by uploader 6 before the
shared engine existed. Uploader 7 is the validated migration adapter over the
same sealed 830-object staging tree. Do not republish v13 to exercise it;
Cartofreako v14 is the first intended applied use of the shared interface.

## `v20260808.1` corrective release procedure

Stage 13 uses corrective source tag `v20260808.1`, static asset
`assets.generated.v13.tar.xz`, and the projection-first 909-file artifact
tree. Before packaging, run the native, browser/WebAssembly, and exact artifact
checks recorded in the [corrected release notes](v20260808.1.md). The release
render must contain 211 SVGs, 84 adjacent resource SVG gzip companions, 211
PDFs, 211 full-size PNGs, and 192 thumbnails. Every projection and format must
contain exactly one Cloud-atmosphere and one Fiber Synthesized product.

The immutable `v20260808` attempt contains only the 885-file clean graph. It
was stopped before S3 publication and is marked superseded; do not replace its
GitHub asset or move its tag.

Create the reproducible archive only after the source commit is final. The
archive timestamp is the tagged commit time; ownership and modes are
normalized, and every member remains under `assets.generated/`:

```sh
release_tag=v20260808.1
release_commit=$(git rev-parse "$release_tag^{commit}")
source_date_epoch=$(git show -s --format=%ct "$release_commit")
tar --sort=name \
  --mtime="@$source_date_epoch" \
  --owner=0 --group=0 --numeric-owner \
  --mode='u+rwX,go+rX,go-w' \
  --format=posix \
  --pax-option=delete=atime,delete=ctime \
  --create --file=- assets.generated | \
  xz --threads=4 -9e > assets.generated.v13.tar.xz
```

The Stage 13 package used four XZ worker threads so compression remained
inside the release environment's 64 GiB execution limit. This affects only
compression resources; the normalized archive members and reproducibility
contract are unchanged.

Preflight the sealed package and record its digest and byte counts in
`v20260808.1.md`:

```sh
xz --test assets.generated.v13.tar.xz
test "$(tar --list --file=assets.generated.v13.tar.xz | sed -n '1p')" = \
  'assets.generated/'
test "$(tar --list --file=assets.generated.v13.tar.xz | \
  sed -n '/\/$/!p' | wc -l)" -eq 909
sha256sum assets.generated.v13.tar.xz
```

Push the already-created source tag explicitly. The release notes intentionally
begin with body text; GitHub supplies the one and only announcement title:

```sh
git push origin main
git push origin refs/tags/v20260808.1
gh release create v20260808.1 \
  --repo bdekoz/cartofreako \
  --verify-tag \
  --title 'v20260808.1 — complete generated assets v13 and Stage 13' \
  --notes-file docs/releases/v20260808.1.md \
  'assets.generated.v13.tar.xz#Projection-organized SVG, PDF, PNG, and thumbnail bundle (XZ)'
```

Download the GitHub object into a fresh directory and compare it to the local
package before constructing the S3 release:

```sh
release_verify_dir=$(mktemp -d /tmp/cartofreako-v20260808.1.XXXXXX)
gh release download v20260808.1 \
  --repo bdekoz/cartofreako \
  --pattern 'assets.generated.v13.tar.xz' \
  --dir "$release_verify_dir"
test "$(sha256sum assets.generated.v13.tar.xz | awk '{print $1}')" = \
  "$(sha256sum "$release_verify_dir/assets.generated.v13.tar.xz" | awk '{print $1}')"
xz --test "$release_verify_dir/assets.generated.v13.tar.xz"
```

Historically, v13 built the immutable S3 staging tree and ran its exact local
validation through the release-local adapter:

```sh
scripts/build-generated-assets-s3-release.sh
scripts/upload-generated-assets-s3-release.sh --validate-only
```

The historical applied v13 run used uploader 6 with
`--apply --verify-download`; its observed result is in
[`s3-v13.md`](s3-v13.md). Because `cartofreako/v13/` is complete and
immutable, do not rerun an applied command against it. The release-local
uploader 7 remains migration evidence: it validated the Cartofreako product
and then delegated transport to `alpha60-clusterops/bin/load-s3-aao`.

For v14 and later, keep product validation and post-transfer report generation
in Cartofreako, but do not maintain another S3 transport implementation here.
After building the staged tree, running the version-specific Cartofreako
validator, and reviewing the new profile, the applied transfer is the separate
human-only Make target:

```sh
make release-ucb-aao-s3 \
  UCB_AAO_RELEASE_PROFILE=docs/releases/v14-aao-upload-profile.json \
  UCB_AAO_RELEASE_DATA_ROOT=build/s3-release-v14 \
  UCB_AAO_RELEASE_RECEIPT=reports/cartofreako-v14-aao-upload-receipt.json
```

The Make recipe is only a guarded wrapper over
`alpha60-clusterops/bin/load-s3-aao --apply --verify-download`. The
release-local profile declares the staged tree, immutable destination, groups,
pilots, metadata, and completion marker; the shared engine owns credentials,
dry runs, exact-prefix authorization, upload, and verification. Validation,
dry-run, and applied-upload receipts need separate filenames so a later
preflight cannot overwrite the canonical completion evidence. Copy and
deliberately update the profile's data root, immutable prefix, and pilot names;
never reuse or repair `cartofreako/v13/`.

Do not move `v20260808.1` or replace either public artifact after publication.
A later correction requires a new source tag, generated-assets version, and
S3 prefix.

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
