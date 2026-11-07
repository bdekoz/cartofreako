# Setouchi futures — selected H3r5 edition

Open the [website gallery](index.html) or the [four print plates](print/index.html).
Atmosphere and Temperature records · 2026 now use **H3r5** in both World and
Japan. The two galleries also retain Water, Fiber, and the orbital observer.
The Hamonshū image section was removed on 7 November; the ten map figures now
lead directly to “Two atlases, one shared table.” This is the current edition selected after the
[r3/r5/r8 comparison](../setouchi-h3-trials-20261106/index.html).

For a manual WordPress update, download the
[web UI package](../setouchi-futures-h3r5-manual-20261106.zip) (about 8.9 MB),
unzip it, and open `START-HERE.html`. The
[browser guide](../setouchi-futures-h3r5-manual-20261106/START-HERE.html) includes
the upload order, block layout, captions, alt text, and detail/legend links.
It uses the normal WordPress page editor and login.

- [World maps and legends](print/world.pdf), four 44 × 19.052559-inch pages.
- [Japan maps and legends](print/japan.pdf), four pages of the same size.
- [Saved settings](../../config/setouchi-futures-20261106-h3r5.json).
- [Provenance and artifact hashes](prepared.json).
- [Validation receipt](validation.json).
- [Development record](../../docs/development/20261106_setouchi_triennale_futures.md#selected-h3r5-edition--6-november-2026).

The selected print index also links each map's PDF, SVG, and 300 dpi PNG,
and its separate legend/source PDF. SVGs retain reference vectors and named
data layers linked to adjacent `layers/` PNGs; keep that directory with the
SVG. PDFs embed those raster layers. Map geometry and imagery are identical
to the validated r5 trial; legends now identify the selected edition.

## Settings and interpretation

Atmosphere keeps light amber `#fcc553`, topmost white nominal 0.66 pt land
outlines, and 100 radiation-opacity levels on the shared 0–400 W/m² scale.
The 1,448,374 radiation cells occupy all 100 levels. Temperature keeps the
wine background, warm record-high classes, and blue record-low outlines.
World and Japan use the same data products and saved modified AuthaGraph
framing, including the horizontal adjustment.

Observation dates and sampled source centers are unchanged. Atmosphere uses
the archived October JAXA rasters with the original 720-samples-per-axis cap.
Temperature uses the original 0.5° CPC centers, with 62,035 covered H3r5 cells
through 28 October 2026. Daily spatial means precede strict comparisons with
1979–2025, requiring at least 30 valid history years.

Finer cells do not add observations. Cells without a sampled center are
unobserved; they do not necessarily indicate missing source pixels. Source
pixel footprints are not filled. R5 improves legibility relative to r8 at
this sheet size while retaining the original physical stroke widths.

The website package includes 640/1280-pixel cards, 3840-pixel details, and
separate legend PDFs. Japan's Water, Atmosphere, and Temperature cards keep
the saved crop; full sheets remain available. Fiber and Observer retain the
complete composition. Native WordPress blocks provide the two-column grids,
and full-width observer rows, stacked on phones. The selected manifests set
`include_hamonshu_gallery: false`; retained Hamonshū source assets still support
the original archived edition and unsent outreach brief.

## Rebuild and check

From the repository root:

```sh
python3 scripts/update-setouchi-futures.py prepare --workers 2
python3 tests/test-setouchi-futures.py
python3 tests/test-setouchi-radiation.py
python3 scripts/validate-setouchi-futures.py --browser
```

The active manifest selects this output. To reproduce the edition explicitly,
add `--manifest config/setouchi-futures-20261106-h3r5.json` to `prepare`.
The entry point verifies the selected trial manifest and every source artifact
before copying the validated print layers, rebuilding the legends, and
generating responsive images and print booklets. It rejects a mismatched H3
resolution, product hash, or changed style. It does not reapply already baked
outline and radiation styling.

The verified r5 trial plates are the production inputs; intermediate GeoJSON
files under `build/` are not required for this rebuild. To reaggregate the
original observations, use [the trial builder](../setouchi-h3-trials-20261106/README.md#rebuild).
That requires the pinned raw files and preserves the r5/r8 comparison edition.

Dependencies remain Inkscape, Poppler, the pinned Atkinson fonts,
Pillow/lxml/Beautiful Soup/ReportLab/requests, and the verified Hamonshū crops
in the adjacent `situationshipin.space` checkout. Use `--hamonshu-root PATH`
for another checkout or `--download-sources` for the three pinned public JPEGs.
Chrome is used for browser validation. Build caches stay under `build/`.

## Publication and recovery

The selected gallery was published on 6 November 2026 to
[the Setouchi page](https://benjamin.dekosnik.com/futures/setouchi-2028/)
through the WordPress REST API and revised on 7 November to remove the
Hamonshū image section. Page 3175 contains ten map figures with
their captions, alternative text, detail links, legends, and attributions.
The publisher preserved the surrounding raw editor content and page metadata.
The initial 36 public media files were verified against their local source hashes.
The current page references 30 of those assets, with the ten map figures unchanged.
Public readback confirms the image section was removed. SiteDistrict blocks automated
Chrome access, so live visual inspection remains unverified; the local desktop
and phone gallery checks passed before publication.

The manual handoff is self-contained: 30 web uploads, an offline gallery
reference, and instructions for building the two grids in
the visual editor. It also identifies the twelve files needed if an existing
gallery only needs its four Atmosphere/Temperature figures changed to r5.
Rebuild the handoff from the validated edition with
`python3 scripts/package-setouchi-futures-manual.py`.

The initial publisher uploaded 36 media assets; the removal reused existing
map attachments and left the original uploads available. Print
masters remain repository deliverables. Its default bundle follows the active
manifest, so future plans select H3r5. The current page uses a bold-paragraph
section title and a single list of three atlas links. The publisher recognizes
that boundary while preserving unrelated legacy markup. Original-image URLs
retain the supplied detail resolution when WordPress creates scaled copies.

```sh
python3 scripts/update-setouchi-futures.py plan --transport rest
python3 scripts/update-setouchi-futures.py apply \
  --plan output/setouchi-futures-h3r5-20261106/private/publish-plan.json
python3 scripts/update-setouchi-futures.py verify \
  --receipt output/setouchi-futures-h3r5-20261106/private/publish-receipt.json --public
```

Authentication, WP-CLI, conflict detection, and recovery retain the
[documented workflow](../setouchi-futures-20261106/README.md#publish-later-without-routine-wordpress-ui-work).
Use the current bundle paths above. Keep credentials, backups, and receipts
private; they are ignored by Git. Preparation, tests, and validation perform
no publishing or outreach. The illustrated brief and contact draft remain unsent.

The backup immediately before the Hamonshū removal is
`private/page-backup-50ddd17718a7372b.json`, with the current publication receipt at
`private/publish-receipt.json`. To restore that saved content with authenticated
access, run:

```sh
python3 scripts/update-setouchi-futures.py restore \
  --backup output/setouchi-futures-h3r5-20261106/private/page-backup-50ddd17718a7372b.json
```

Restoration checks the published content hash first and refuses to overwrite
subsequent edits. Media uploads remain available after a content restoration.

The [saved H3r3 gallery](../setouchi-futures-20261106/index.html), original atlas
masters, and [resolution comparison](../setouchi-h3-trials-20261106/index.html)
remain available for reference.
