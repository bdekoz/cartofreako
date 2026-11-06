# Setouchi futures — local website update

Open [index.html](index.html) to review two five-plate galleries and the
three-image Hamonshū strip. The geographic maps retain the modified Setouchi
AuthaGraph composition. Star-X is the reference for the **website's typography
and spacing**, not the projection.

This is a local insertion preview. It belongs after the existing three lists
and before **Two atlases, one shared table**. The preview uses a temporary
reading style; the native WordPress blocks inherit the installed theme when
published. The current page and Star-X styling were inaccessible to automated
reads, so the preview does not recreate or replace their unseen content.

The images use the approved wine/amber presentation. Both Atmosphere plates
use the lighter amber `#fcc553` (`rgb(252,197,83)`) as their background, including
the thumbnail frames and full-sheet detail images. Land outlines sit in a
separate top layer, using white `#ffffff` at full opacity with their original
line widths. The World layer includes the relocated Antarctica outline.
Nominal outline weights are 0.5 pt for World and 1 pt for Japan (approximately
0.49 pt and 0.99 pt after the Setouchi framing scale on the 44-inch sheets).
Atmospheric data colors, opacity, and geometry are retained. Submarine fiber routes
are amber at full opacity, with matching legend swatches; land routes remain
green. Route geometry and dash classes are retained. Water, atmosphere, and
temperature thumbnails trim the unused part of the Japan print sheet. The
larger links retain the full sheets. Fiber and observer previews retain their
full composition. The observer dates and temperature cutoff are in captions.

The two geographic rows use native two-column blocks; the observer image spans
the content width. Phone layouts stack the figures. The Hamonshū row contains
three complete crops in equal 4:3 frames. No carousel or custom frontend
JavaScript is required.

- [prepared.json](prepared.json) records 49 generated media files, source
  checksums, crop bounds, projection/framing, and credits.
- [gallery-blocks.html](gallery-blocks.html) is the WordPress fragment template.
  Its `{{asset:…}}` tokens are intentionally unresolved until upload. Do not
  paste this template into the live page.
- [Illustrated brief](outreach/brief.pdf) is one A4 page for a possible Narukawa
  conversation. The [message draft](outreach/first-contact.md) is unsent.
- [validation.json](validation.json) records local delivery/browser checks.

## Rebuild and check

Run from the Cartofreako repository root:

```sh
python3 scripts/update-setouchi-futures.py prepare --workers 2
python3 tests/test-setouchi-futures.py
python3 scripts/validate-setouchi-futures.py --browser
```

The build needs the existing `output/atlas/` SVGs and bibliography, the pinned
Atkinson fonts, Python packages Pillow/lxml/Beautiful Soup/ReportLab/requests,
Inkscape, and the verified Hamonshū review crops in the adjacent
`situationshipin.space` checkout. Use `--hamonshu-root PATH` for another checkout
or `--download-sources` to retrieve the three pinned public JPEGs. Chrome is
used only for browser checks. Build intermediates and caches stay under
`build/setouchi-futures/`; no observational data is refreshed.

## Publish later without routine WordPress UI work

The user requested **local preparation first**. No WordPress content or media
was uploaded, and no contact message was sent.

For REST access, provision a dedicated WordPress application password and make
`WP_USERNAME` and `WP_APPLICATION_PASSWORD` available through the local secret
manager/environment. Alternatively, supply `--credentials-file PATH` containing
`username` and `application_password`; the file must be private (`chmod 600`)
and outside the tracked/public delivery. Use the credential option on each
remote command. The account needs permission to edit page 3175 and upload media.
An application password is independently revocable; it does not require
giving the script the normal WordPress login password.

```sh
python3 scripts/update-setouchi-futures.py plan --transport rest
python3 scripts/update-setouchi-futures.py apply \
  --plan output/setouchi-futures-20261106/private/publish-plan.json
python3 scripts/update-setouchi-futures.py verify \
  --receipt output/setouchi-futures-20261106/private/publish-receipt.json --public
```

For SSH/WP-CLI, set `WP_SSH_HOST` and `WP_PATH`, or pass `--ssh-host` and
`--wp-path` to each remote command. Select `plan --transport wp-cli`; the saved
plan records that transport for apply and verify. The script passes JSON on
stdin and quotes the remote command arguments. This route requires WP-CLI on
the WordPress host; no plugin installation is required.

`plan` performs reads only. It verifies the permalink, the unique insertion
heading, and at least three preceding top-level lists. It saves private
before/planned HTML and the base content hash. `--page-file PATH` can instead
use a WordPress `context=edit` JSON export for an entirely offline plan.

`apply` uploads the 36 media assets used in the native blocks. WordPress
generates responsive sizes for the attached gallery images; the local
640-pixel derivatives remain part of the preview package. Content-addressed
media slugs allow reuse, including after an interrupted upload. The page is
updated only after all uploads succeed and a fresh content/metadata check
passes. Status, title, parent, slug, and template are preserved. Later runs
replace the managed Group block, preserving the surrounding page byte for byte.

Both transports check for edits immediately before writing. This is not an
atomic database compare-and-swap: avoid editing the same page during apply.
Readback verifies the saved content and metadata; `verify --public` also checks
the served page and media links. Inspect the actual theme layout before calling
publication visually complete. Live authentication and WordPress integration
remain untested in this local-only delivery.

Backups, media IDs, credentials supplied by the user, and publication receipts
belong outside the public package. The `private/` directory is ignored by Git
and written with restrictive permissions. It must not be copied to public web
hosting. To restore a saved page explicitly:

```sh
python3 scripts/update-setouchi-futures.py restore --backup /path/to/page-backup.json
```

Restore refuses to overwrite subsequent human edits and does not delete media.
An unexpected readback also disables automatic restoration: inspect the saved
content before deciding how to recover.
No automatic publishing or outreach occurs during `prepare`, tests, or local
validation.
