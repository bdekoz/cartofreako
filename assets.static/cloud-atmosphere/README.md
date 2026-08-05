# Cloud-atmosphere source profile

`cloud-atmosphere-profile.json` is the authoritative Stage 4.1a source,
freshness, aggregation, and display configuration.

Normal generation uses a locally prepared snapshot at
`.prepared/cloud-atmosphere-latest.geojson`. Raw COG and NetCDF inputs and the
prepared snapshot are intentionally not checked in because they are large,
mutable refresh products. P-Tree requires a user account; credentials remain
in the operator's `.netrc` and are never copied into this tree. Publication
must retain the JAXA/EORC and applicable upstream credit required by the
current source terms.

The checked fixture under `fixtures/` exercises the schema and renderer. It is
synthetic, is identified as a fixture in its metadata, and must not be
presented as an observation.

For first-time production setup, follow the
[credentialed P-Tree download quick start](../../docs/ptree-production-download.md).
It covers registration, safe `.netrc` configuration, a read-only login test,
the complete refresh sequence, expected outputs, and troubleshooting.

Refresh workflow:

1. Configure a `.netrc` entry for `ftp.ptree.jaxa.jp`.
2. Run `make fetch-cloud-atmosphere-data`.
3. Run `make prepare-cloud-atmosphere-data`; it verifies every staged raster
   digest before aggregation.
4. Review `.prepared/cloud-atmosphere-latest.manifest.json` and the reported
   layer ages and coverage.
5. Run `make generate-cloud-atmosphere`.

The process-start UTC instant controls calculated solar geometry. Each source
observation retains its own interval. A missing cell or property means
unobserved, not clear sky and not zero.
