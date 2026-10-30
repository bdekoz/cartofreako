# Cartofreako / Setouchi Triennale 2028

Open [index.html](index.html) for the visual inventory and all downloads.
See [GIT-CONTENTS.md](GIT-CONTENTS.md) for the versioned review package and local print exports.

The [aggregate exploration PDF](setouchi-tri-explore-v1.pdf) brings together all
38 world/Japan pairs, nine catalogs, the application draft, contact sheets,
petroleum annex, resource colour key, coral prototypes, source notes and pending human reviews. Vector maps remain
zoomable; the PDF is a study volume, separate from the application packet.

- 38 world plates and 38 Japan companions; SVG, PDF and 300 dpi PNG (228 print files).
- Nine four-page catalogs: three exhibitions, three events, three installations.
- Eight-page [application draft](proposal/shared-sea-atlas_application-draft.pdf),
  [proposal/options](proposal/proposal-and-options.md), ten-page contact sheets,
  and four-page petroleum source annex.
- [Offline petroleum explorer](sources/petroleum-explorer.html),
  [source periods and limits](sources/data-quality.md), machine validation and checksums.

Full print size: 44 × 19.052559 inches; PDF 3,168 × 1,371.784248 points;
PNG 13,200 × 5,716 pixels, 300 dpi. Historical layers remain explicitly dated.
No application, payment, outreach or publication has been performed.

Petroleum source assets are in `../../assets.static/petroleum`. OPEC's 14 supplied
workbooks are all retained, with independent EIA, ANP and Statistics Canada data.
The existing global refinery layer uses the repaired official UNSD endpoint.

## Reproduce the delivered files from pinned local inputs

The compiled generators and exact compilation command are in `build/`; the
code revisions are in `sources/repository-state.json`. Keep the current
Cartofreako checkout, sibling izzi headers, Natural Earth files and sibling
cloud_cdn_cache.bkoz and Alpha60 sample/cache dependencies available at their recorded paths. No network refresh is needed
to reproduce the maps from the pinned sources.

The native swarm run requires the extracted cumulative documents in
`build/swarm-runtime/cache`, the sibling Alpha60 executable/data, the recorded
IPinfo database and `build/swarm-runtime/earth-ck-44-22.svg`. Raw participant
cache files and native render intermediates are ignored by Git and excluded
from the delivery inventory. Their hashes and extraction inventory remain in
`sources/swarm-cache-extraction.json` and `sources/swarm-refresh.json`.
`build_swarm.py --compose-only` reuses an existing native render.

```bash
python3 output/setouchi-triennale-2028/build/render_world.py
python3 scripts/prepare-petroleum-data.py
python3 output/setouchi-triennale-2028/build/build_petroleum.py
python3 output/setouchi-triennale-2028/build/build_japan.py
python3 output/setouchi-triennale-2028/build/export_plates.py
python3 output/setouchi-triennale-2028/build/build_catalogs.py
python3 output/setouchi-triennale-2028/build/build_index.py
python3 output/setouchi-triennale-2028/build/build_resource_key.py
PYTHONPATH=/tmp/cartofreako-pdf-deps python3 output/setouchi-triennale-2028/build/build_visual_annex.py
PYTHONPATH=/tmp/cartofreako-pdf-deps python3 output/setouchi-triennale-2028/build/build_aggregate.py
python3 output/setouchi-triennale-2028/build/validate_delivery.py
PYTHONPATH=/tmp/cartofreako-pdf-deps python3 output/setouchi-triennale-2028/build/verify_refinements.py
```

These are repository-root commands. `refresh_resources.py` is the task's raw
download/preparation helper; rerunning it is a new data refresh and requires
checking revised source metadata and observation-year labels before promotion.
The delivery uses the finalized `sources/data/resources` profile, not the
intermediate `resources-current` directory. NOAA historical raw files are
read-only symlinks to the existing local cache.

Human review and next steps are appended to
`../../docs/development/20261029_setouchi_triennale_explore.md`.
