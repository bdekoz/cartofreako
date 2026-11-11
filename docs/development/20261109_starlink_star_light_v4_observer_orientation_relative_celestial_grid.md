# Starlink Star Light v4: observer orientation relative to the celestial grid

Implementation and delivery record, 11 November 2026, America/Los_Angeles.

The study advances the San Francisco observer plate by one hour
per frame for a day, using the accepted November 9 catalog and unchanged
AuthaGraph display framing. A manual stepper and a **1920 × 1080 MKV**, with
**two seconds per hourly plate**, make the moving horizon and satellite
population easier to understand.

The complete delivery contains 24 hourly map/legend pairs and a separate
+24-hour proof. Open the [local stepper](../../output/starlink-star-light-v4-observer-hourly/index.html),
[48-second MKV](../../output/starlink-star-light-v4-observer-hourly/observer-hourly-24-plates-48s.mkv),
[Instagram portrait MP4](../../output/starlink-star-light-v4-observer-hourly/instagram/observer-hourly-instagram-1080x1920-48s.mp4),
[A2 contact sheet](../../output/starlink-star-light-v4-observer-hourly/observer-hourly-contact-sheet.pdf),
or [source and validation manifest](../../output/starlink-star-light-v4-observer-hourly/manifest.json).
The separate
[annotated November 3 / November 9 comparison PDF](../../output/orbital-observer-nov3-nov9-comparison/orbital-observer-nov3-vs-nov9-annotated.pdf)
explains the underlying coordinate behavior.

## What moves, and what stays fixed

The published November 3 plate and the current November 9 plate already
have **identical cyclic framing**: a 44-inch native rectangle, scaled to a
43.5-inch image, moved right by 4.4 native inches / 4.35 printed inches,
with content wrapping across its sides. The shared celestial-equator paths
are exactly equal. The page framing does not rotate by 126 degrees.

The observer's orientation relative to the celestial grid changes with
Earth's rotation. The two calculation times, 2026-11-03 17:10 UTC and
2026-11-09 01:12 UTC, differ by **5 days, 8 hours and 2 minutes**. Their model
local sidereal orientations are **178.055°** and **303.813°**, a residual
change of **125.758°** after complete turns are removed. In San Francisco,
the clock times are November 3 at 09:10 PST and November 8 at 17:12 PST.
The eight-hour clock-time difference is the main reason this is a large
orientation change. At the same clock time six days later, the residual
would be about **5.9°**.

An hourly calculation advances the model sidereal orientation by about
**15.041° per hour**. The local zero-elevation horizon therefore moves in
right ascension against the fixed celestial grid. AuthaGraph projects this
rotation into changing curved and sometimes split shapes. Cyclic framing
is applied afterward and remains constant throughout the sequence.

The satellites also move along their propagated orbits. The renderer keeps
only objects at local elevation **≥ 0°**, so objects enter and leave the
plate. Illumination can change symbol opacity. The result is a calculated
sky selection, not a simulation of naked-eye visibility or a time-averaged
exposure. Empty regions include directions below the local horizon.

The sidereal definition and longitude relation are described by the
[U.S. Naval Observatory](https://aa.usno.navy.mil/faq/GAST). The values above
reproduce this renderer's existing SGP4 GMST calculation using its UTC
Julian-date input; they do not claim a higher-precision apparent-sidereal
or UT1 treatment.

## Delivered time window

Anchor frame zero to the **current accepted plate**, preserving its exact
01:12 UTC calculation rather than rounding it to an hour. Use one-hour
increments from that instant.

| Frame | Elapsed time | UTC calculation | San Francisco / PST |
| --- | ---: | --- | --- |
| 00 | 0 h | 2026-11-09 01:12 | 2026-11-08 17:12 |
| 06 | 6 h | 2026-11-09 07:12 | 2026-11-08 23:12 |
| 12 | 12 h | 2026-11-09 13:12 | 2026-11-09 05:12 |
| 18 | 18 h | 2026-11-09 19:12 | 2026-11-09 11:12 |
| 23 | 23 h | 2026-11-10 00:12 | 2026-11-09 16:12 |
| 24 / optional endpoint | 24 h | 2026-11-10 01:12 | 2026-11-09 17:12 |

The principal video has **24 snapshots**, indices 00–23, for **48 seconds**.
The sample instants span 23 elapsed hours. Including the exact +24-hour
endpoint produces **25 snapshots and a 50-second comparison version**.
Neither version averages an hour of observations into a plate.

For a calendar-day variant, use 00:00–23:00 in an explicitly selected
timezone; do not silently mix UTC dates and San Francisco dates. The
anchored sequence above is the recommended first edition because its
first frame can be checked directly against the accepted current plate.

## Native calculation checks

The existing native binary accepts a profile timestamp and computes the
observer product independently. It needs no new remote acquisition and no
global land rendering for this sequence.

Three calculations from the **same pinned November 9 input catalog** were
run in isolated directories:

| Offset | Propagated records | Above-horizon records | Epoch exclusions | Propagation failures |
| ---: | ---: | ---: | ---: | ---: |
| 0 h | 17,956 | 972 | 46 | 0 |
| +12 h | 17,952 | 1,008 | 50 | 0 |
| +24 h | 17,947 | 964 | 55 | 0 |

Each native canary completed in about **1.3 seconds**, with three canaries
running concurrently on this machine. This measures native calculation
and SVG generation only. It does not establish the runtime of all 24/25
frames, typography, preview/PDF rendering, viewer packaging or encoding.
The local [canary receipt](../../build/observer-v4-feasibility/results.json)
retains exact metadata and timings.

The completed sequence reproduces all three canaries. Across its 24 main
frames, the above-horizon count ranges from **962 to 1,190**, with **46 to
54 epoch exclusions** and **zero propagation failures**. The retained
+24-hour proof has 964 plotted objects and 55 exclusions. Frame zero also
matches the accepted World plate's scientific attributes, marker styling,
horizon paths and celestial-equator paths.

The **seven-day maximum element age** and **six-hour future-epoch tolerance**
remain active. A frozen catalog does not guarantee a constant eligible
population: at +24 hours, nine more records are excluded by these rules
than at the start. Preserve and display those exclusions. Do not loosen
the rules to make the totals match or conceal their contribution to count
changes. Freeze catalog membership and input bytes; recalculate eligibility,
satellite positions, horizon, illumination and visible membership each hour.

## Calculation and rendering design

1. Pin the existing
   [November 9 orbital profile](../../assets.static/orbital-technosphere/20261109/orbital-technosphere-profile.json),
   its catalog/checksum files and renderer binary hash. Retain San Francisco
   at 37.7749° N, 122.4194° W, 16 m, the 0° elevation threshold, celestial
   handedness and central right ascension of 12 hours.
2. Derive 24 profiles by changing only their calculation timestamps. Put
   each profile and output in its own frame directory. Resolve relative
   catalog and NASA-reference paths against the original profile directory
   before writing the derived profiles. Keep acquisition times separate
   from calculation times; do not rewrite the acquisition receipt.
3. Run `generate-orbiting authagraph observer PROFILE` for every timestamp.
   Each frame is a real propagation and topocentric-coordinate calculation.
   Reusing the first PNG and rolling it horizontally would not produce the
   requested hourly sky.
4. Style every result through the shared
   [World compositor](../../scripts/atlas_world.py) and accepted
   [World recipe](../../config/starlink-star-light-world-20261110.json).
   Preserve the wine field, categorical fleet colors, white debris x marks,
   1.5× Starlink sunbursts, 6 pt source names and fixed cyclic framing. Use
   separate A3 light legends without symbol backing boxes. Counts and time
   labels must come from each frame's metadata.
5. Render a complete frame to SVG/PDF and a preview. Cache by source hashes,
   timestamp, derived profile, compositor, style and font hashes. A changed
   frame must invalidate its own outputs and the assembled video.
6. Write a sequence manifest and validate the ordered sequence before
   building the viewer or encoding the MKV. Keep all outputs separate from
   the accepted single-time World delivery and default atlas.

Output root: `output/starlink-star-light-v4-observer-hourly/`.
Entry point: `scripts/build-observer-hourly.py`, with
`--profile`, `--start`, `--hours 24`, `--step-minutes 60`, `--include-endpoint`,
`--video-width 1920`, `--video-height 1080` and `--seconds-per-plate 2`.
The reviewed edition uses 24 one-hour steps and the original profile's
calculation timestamp. A full rebuild and an independent delivery check are:

```sh
python3 scripts/build-observer-hourly.py --jobs 2
python3 scripts/build-observer-hourly.py --check
```

`--proofs-only` prepares hours 0, 12 and 24 before the full run. Frame caches
require matching catalog, profile, renderer, implementation, font and export
hashes. `--reference` selects the accepted World SVG for frame-zero checks.
The delivery retains the exact catalog and acquisition receipt under
`sources/orbital/`, the renderer under `sources/renderer/`, and the Python,
style and font sources under `sources/implementation/`. This keeps the
hourly study separate from a concurrently running default atlas build.

## Viewer that makes the orientation understandable

Provide a local stepper with **Previous hour**, **Next hour**, a numbered
slider, **Play/Pause**, and **Reset to the accepted plate**. Default to
manual stepping, with automatic playback at one plate every two seconds.
Support arrow-key stepping and preload the next preview so that image
loading does not change the dwell time. The viewer can use the pinned local
previews and manifest without a server-side calculation service.

Every view should show the UTC and PST timestamps, elapsed hour, local
sidereal orientation, above-horizon total and epoch-exclusion count. Keep
the camera, scale, projection, cyclic shift and symbol sizes fixed.

Use layers that distinguish the causes of apparent movement:

- **Full plate:** the actual satellite population and current horizon.
- **Orientation only:** the current horizon and a fixed celestial equator,
  with satellite marks hidden. This isolates the rotating local horizon.
- **Previous-hour horizon:** an optional dashed outline from the preceding
  calculation, clearly identified as an older boundary. It is not a
  satellite trajectory. Keep the equator visually distinct and stationary.
- **Names:** a display toggle; retain all source name data in the editable
  plate. Optional NORAD selection can follow a single object's changing
  coordinates without treating a straight screen-space connector as its
  physical orbital path.

The legend should explain that “above the horizon” is an elevation test,
not necessarily a higher position on the printed page. A near-geostationary
example such as **AMAZONAS 3 / NORAD 39078**, if eligible in each sampled
frame, is useful: its local azimuth and elevation change little while its
right ascension and position on this celestial-grid plate move markedly.

## 1080p horizontal MKV

Use a **1920 × 1080, square-pixel, 30 fps** canvas. The source plate has a
44:19.052559 aspect ratio. A proportional full-width fit is about
**1920 × 832 px**, leaving about **124 px above and below** for labels.
Preserve the complete plate and its aspect ratio. Use the wine background
throughout those bands.

The top band should carry a readable **UTC timestamp**, **San Francisco
timestamp**, and **hour 00/23** indicator. Use roughly 28–36 px type for the
main time labels. The bottom band should identify the observer, 0°
elevation selection, frozen catalog date, plotted count, exclusion count,
and horizon/equator key in roughly 22–26 px type. Final fit needs a rendered
preview; these are starting sizes, not verified layout dimensions.

At full-width 1080p, a 6 pt name from the 44-inch plate becomes only about
**3.6 px high**, before font-specific glyph proportions. It will not be
readable. Retain the accepted names in the SVG/PDF edition and offer a
**video overview with names hidden** so the moving point field and horizon
remain clear. Keep names available in the interactive viewer at zoom.
Preserve source marker sizes in the baseline video; a separate enhancement
of subpixel outlines would need to be identified as a video presentation
choice. In particular, white debris x strokes can be thinner than one
pixel at this reduction.

Encode with **H.264/libx264 inside Matroska**, `yuv420p`, no audio, and CRF 18
as the first review setting. Hold each hourly plate for **60 identical
output frames**, giving two seconds at 30 fps. Use clean cuts. Dissolving or
interpolating unrelated satellite positions would suggest trajectories
that were never calculated.

Hourly sampling is appropriate for comparing orientation and occupancy.
Fast satellite motion is undersampled at this cadence: the movie shows
discrete calculated states and should not be read as a continuous orbital
trajectory. A smoother scientific animation would require additional
propagated times between the hourly plates, rather than interpolating
their screen positions.

The builder assembles 24 **1920 × 1080** PNG frames and uses this encoding
pattern, with an additional metadata input for the 24 hourly chapters:

```sh
ffmpeg -framerate 1/2 -start_number 0 \
  -i frames-1080p/frame-%02d.png \
  -an -vf setsar=1 -c:v libx264 -preset medium -crf 18 \
  -pix_fmt yuv420p -r 30 -fps_mode cfr -frames:v 1440 \
  observer-hourly-24-plates-48s.mkv
```

For the 25-frame version, use 1,500 output frames and a filename identifying
its **50-second** duration. Check the actual encoded duration and frame
count; do not rely solely on filenames. A higher-quality archival option
is FFV1 in Matroska, with a larger file and a clearly stated pixel format.

Local FFmpeg **8.1.3** exposes both `libx264` and `ffv1`. A two-image
**encoder-only probe**, using two copies of the current plate, passed with
H.264, `yuv420p`, 1920 × 1080, 30 fps, **120 frames and exactly 4.000 s**.
This checks encoding mechanics; it is not an hourly scientific sequence or
the requested final movie. The probe is under
`build/observer-v4-feasibility/encoder-smoke/`.
Image-sequence timing is documented in the
[FFmpeg image2 demuxer documentation](https://ffmpeg.org/ffmpeg-formats.html#image2-1),
and was also checked against this installation's
`ffmpeg -h demuxer=image2` output.

Optional MKV chapters can identify each hour at video times 00:00, 00:02,
00:04, …, 00:46. Put the astronomical calculation timestamp in each chapter
title; the video playback time and observation time are different clocks.

## Instagram portrait edition

The companion [Instagram MP4](../../output/starlink-star-light-v4-observer-hourly/instagram/observer-hourly-instagram-1080x1920-48s.mp4)
recomposes the same 24 states for a **1080 × 1920, 9:16** screen. It retains
the **48-second** runtime and two-second holds, using H.264 High 4.1,
30 fps, `yuv420p`, BT.709, square pixels and a fast-start MP4 container,
with no audio. A [cover image](../../output/starlink-star-light-v4-observer-hourly/instagram/observer-hourly-instagram-cover.jpg)
and [posting caption](../../output/starlink-star-light-v4-observer-hourly/instagram/caption.txt)
accompany the export.

The upper panel shows the complete orbital-object plate; the lower panel
isolates its horizon and fixed celestial equator. Both retain the original
aspect ratio, projection, cyclic framing and curve geometry. The mobile
presentation enlarges each marker silhouette **2× about its original
center** and strengthens the reference curves. Scientific coordinates,
object membership, categorical colors and illumination opacities remain
unchanged. The video labels the symbol enlargement explicitly.

Larger timestamps use `America/Los_Angeles` to select PST or PDT for the
calculated instant. These November 8–9 states use **PST**. The title,
timestamps, panels and progress strip leave space above, below and to the
right for app controls. This is a presentation margin, not a guarantee
about every Instagram interface. `START / REPLAY` and `FINAL SNAPSHOT`
labels distinguish the final-to-first reset from another calculated hour.

Build from the completed study without reacquiring data or recalculating
the orbits:

```sh
python3 scripts/build-observer-instagram.py --proofs-only
python3 scripts/build-observer-instagram.py
```

The builder verifies the original delivery hashes before reading its SVGs,
checks membership and geometry while preparing the mobile panels, and
checks all 1,440 decoded video frames against their scheduled hourly state.
It records source, builder and output hashes in a separate
[Instagram manifest](../../output/starlink-star-light-v4-observer-hourly/instagram/manifest.json).
The original horizontal study and its manifest remain unchanged.

## Ending and looping

Default to **stop at the final frame**, with replay as an explicit control.
After 24 solar hours, the horizon's residual shift is about **0.986°**;
the satellite states do not return to their initial values. A sidereal-day
endpoint, about **23 h 56 min 4 s**, nearly restores the horizon orientation
but still does not restore satellite positions.

The 23 h → 0 h cut in a looping 24-frame video is therefore not the next
physical hour. If a loop is requested, identify the reset visibly, for
example with a brief “Replay from starting instant” card, and account for
that card in the video duration. Do not claim a seamless physical loop.

## Validation and acceptance

- Frame zero reproduces the accepted November 9 calculation: 972 plotted
  objects, 46 epoch exclusions, no propagation failures, same observer and
  timestamp. A video-only hidden-name option must not alter scientific
  coordinates or source inventories.
- There are exactly 24 ordered hourly profiles, or 25 with the endpoint.
  UTC steps are exactly 3,600 seconds. PST labels agree with the actual
  timezone conversion. No repeated timestamp or missing hour is accepted.
- Catalog, checksum and style hashes stay pinned across the sequence.
  Per-frame epoch exclusions and failures are explicit. Plotted totals
  equal the number of unique above-horizon NORAD objects in that frame;
  constant visible or eligible totals are not an acceptance condition.
- The scale, cyclic shift, source clipping window and celestial-equator
  geometry remain identical in every frame. Horizon changes are calculated
  at the new instant. Frame-zero source geometry is not repeatedly rolled
  to imitate this change.
- All objects and labels fit their delivery pages; white debris keys,
  unboxed legend symbols and physical type are checked on rendered proofs.
  Video timestamps remain legible at 1920 × 1080.
- FFprobe confirms H.264, 1920 × 1080, square pixels, `yuv420p`, 30 fps,
  no audio, and 1,440 frames / 48 s, or 1,500 frames / 50 s. Validate each
  plate's two-second hold, including the first and last plate, against the
  sequence manifest.
- Inspect the start, an intermediate horizon-seam crossing and the end
  visually. The stepper, PDF/contact sheet and MKV must refer to the same
  reviewed timestamps and populations.

## Implementation order and deliverables

The profile schedule, per-frame native calculations and sequence manifest
are implemented. Hours 0, 12 and 24 were exported and visually checked
before the remaining frames were assembled. The 48-second movie is the
delivered main edition; a 50-second endpoint movie remains an explicitly
selected comparison option.

Delivered: an `index.html` stepper; 24 SVG/PDF plate/legend pairs and
preview images; a 24-frame contact sheet; the 48-second MKV; and a manifest
containing timestamps, local sidereal values, source/profile/style hashes,
plotted counts, exclusion/failure counts, page geometry and export hashes.
The contact sheet should use simplified time labels large enough to read;
it is an overview, while individual PDFs carry the editable fine detail.
The optional +24-hour proof is retained even if it is omitted from the main
video.

The study is a separate sequence edition. Promoting it into atlas
navigation can follow review of the hourly proofs; a time series should not
silently replace the atlas's single-time observer plate.

The native and export checks cover every frame, including unique NORAD
membership, elevation eligibility, unchanged scientific coordinates after
styling, fixed equator and framing, white debris marks, physical name type,
PDF page sizes and unclipped A3 legend contents. The video check decodes all
**1,440 frames**, matches every decoded frame to its scheduled source plate,
and verifies **60 frames per hourly hold**, 48.000 seconds, H.264, `yuv420p`,
1920 × 1080, square pixels, 30 fps, 24 chapters and no audio. H.264 is lossy;
the timing check compares decoded imagery with the scheduled source images
rather than claiming byte-identical decoded pixels.

The local viewer is tested in Chromium for manual navigation, slider and
keyboard stepping, two-second playback, pause, reset, zoom, name visibility,
orientation-only geometry, the actual previous-hour horizon, per-frame
downloads, loaded typography and stop-at-end behavior. SVG is parsed as XML
before insertion so namespaced `use` references remain visible in the
browser. Desktop/mobile proofs and the final 1080p frame are visually
checked as well as the scientific geometry.
