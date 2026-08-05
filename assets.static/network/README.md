# Cumulative network snapshot

This directory pins the offline input and rendering profile for the
`generate-network` pass. The archive was copied without modification from
`alpha60-results-dragons` commit
`0eafe44b18215e368074ce78d2354ec881298777` (2026-07-28). Both repositories
use GPL-3.0-or-later licensing.

The ZIP contains exactly one 10,714,055-byte GeoJSON member. Its archive and
uncompressed digests are recorded in `network-profile.json`; `SHA256SUMS`
checks the committed archive. The source is a cumulative H3-resolution-5
FeatureCollection for `house-of-the-dragon-301`, covering 2026-06-22 through
2026-07-26. It contains 23,825 Point features.

`properties.downloaders` provides `size`, `mobile`, `satellite`, `tor`,
`tor_exit_nodes`, `vpn`, `relay`, `proxy`, `hosting`, and `service`. The nine
specialized counts can overlap and may sum to more than `size`; they are
therefore rendered as independent overlays, never as a stacked total.

Prepare the bounded archive with:

```sh
make prepare-network-data
```

The preparation script accepts a local `.zip`, `.geojson`, or `.json` through
the Makefile's `NETWORK_SOURCE` override. ZIP input must contain one safe,
flat JSON member, pass its CRC check, and expand to no more than 64 MiB. The
prepared file lives under the ignored `assets.static/network/.prepared/`
directory and can always be reconstructed from the committed archive.
