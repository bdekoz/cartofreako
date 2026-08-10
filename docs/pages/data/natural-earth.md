# Natural Earth 1:10m physical-vector input

Earth, water, Bathymetry Roulette, and Bathymetry Hamonshū generation use the Natural Earth 5.1.1
complete 1:10m physical-vector archive under
`assets.static/natural-earth/10m-physical-vectors/`. A dependent target such
as `make generate-earth-ck`, `make generate-bathymetry-roulette`, or
`make generate-bathymetry-hamonshu` acquires it
when absent.
The directory is a reproducible build input and is intentionally ignored by
Git. Run only the acquisition step with:

```sh
make fetch-natural-earth-10m
```

The fetch script downloads the official archive from:

<https://naciscdn.org/naturalearth/10m/physical/10m_physical.zip>

It verifies this SHA-256 digest before extracting the datasets used by the
Cahill-Keyes earth generator:

```text
a79cc39162f29832b567de5e24e8770f04a0b997eefd8d067ae4c9df40d21d2a
```

The Earth and water SVGs use coastline, land, minor islands, reefs, ocean, rivers
and lake centerlines, lakes and reservoirs, playas, glaciated areas,
Antarctic ice shelves, and all twelve nested bathymetry depths from 0 m to
-10,000 m. Both bathymetry-art passes reuse those polygons and their original
twelve-step blue ramp as projection-safe clips for Izzi curve fields; neither
introduces another geographic input. Natural Earth data is in the public domain. See the
[Natural Earth terms of use](https://www.naturalearthdata.com/about/terms-of-use/)
and the [1:10m physical-vector catalog](https://www.naturalearthdata.com/downloads/10m-physical-vectors/).
