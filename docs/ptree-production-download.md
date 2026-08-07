# P-Tree production download: quick start

[Documentation index](../index.md) ·
[Generation pipeline](generation.md) ·
[Cloud-atmosphere notes](cloud-atmosphere-implementation-notes.md) ·
[Source profile](../assets.static/cloud-atmosphere/README.md)

This is the short, production-safe path from a new P-Tree account to the six
Cloud-atmosphere maps. The workflow downloads a credentialed Himawari cloud
NetCDF from P-Tree plus public JAXA Earth COGs, prepares one H3 snapshot,
verifies it, and renders it. Run repository commands from the cartofreako
checkout root.

## 1. Request a P-Tree account

1. Read the current
   [P-Tree registration precautions](https://www.eorc.jaxa.jp/ptree/registration_top.html)
   and [terms of use](https://www.eorc.jaxa.jp/ptree/terms.html).
2. Submit the registration form and complete the emailed application.
3. Wait for the completion email containing the FTP account information.

Approval is not immediate; JAXA says it may take a couple of days. This
repository uses the account only for the P-Tree cloud product. The other three
atmosphere sources are public JAXA Earth STAC assets.

## 2. Store the credential safely

The fetcher deliberately reads the standard user-level `~/.netrc`. It does not
accept a password on the command line and does not copy credentials into raw
or prepared manifests.

If `~/.netrc` does not exist, create it with owner-only permissions:

```sh
(umask 077 && touch ~/.netrc)
chmod 600 ~/.netrc
```

Open the file in an editor and add the account supplied by JAXA:

```text
machine ftp.ptree.jaxa.jp
  login YOUR_P_TREE_ACCOUNT
  password YOUR_P_TREE_PASSWORD
```

If the file already contains credentials for other services, append this
machine block; do not replace the existing file. Never put `.netrc`, the
account, or the password inside this repository, a command line, a shell
transcript, or an issue report.

## 3. Install the JAXA certificate root

JAXA P-Tree's current FTPS chain terminates at `SECOM TLS RSA Root CA 2024`,
which may not yet be present in the operating-system CA bundle. Install the
official root in private per-user Cartofreako data:

```sh
make install-jaxa-certificate
```

The installer downloads the PEM certificate only from SECOM's HTTPS root
repository, verifies that its certificate SHA-256 is exactly
`1435f225c5d252d7a21948cc3ce62aecfa88001e3dd72d1cc3555100eb372f93`,
checks that it is a current self-signed trust anchor, and installs it with mode
`600` beneath `${XDG_DATA_HOME:-~/.local/share}/cartofreako/certs/`. It does
not modify the system trust store. `authorize-external` and the production
fetcher discover that location automatically.

Set `PTREE_CACERT` to an absolute path when a different private destination is
required:

```sh
make PTREE_CACERT=/absolute/path/secom-tls-rsa-root-ca-2024.pem \
  install-jaxa-certificate
```

Do not download a similarly named certificate from an unverified mirror and
do not work around certificate failures with `--insecure`.

## 4. Test only the P-Tree login

The repository check uses the same implicit FTPS endpoint, private certificate,
and `.netrc` lookup as the fetcher:

```sh
make EXTERNAL_PASSES=jaxa-ptree authorize-external
```

Success reports that JAXA P-Tree and the requested optional passes are ready.
The
[P-Tree FAQ](https://www.eorc.jaxa.jp/ptree/faq.html) confirms FTPS port 990
and notes that a web browser is not an FTP client.

## 5. Fetch, prepare, verify, and render

First confirm the local compiler, H3, GDAL NetCDF/GeoTIFF drivers, utilities,
font, and rendering tools:

```sh
make check-prerequisite
```

For one internally consistent and reproducible run, capture the current UTC
instant once and let every stage inherit it:

```sh
export SOURCE_DATE_EPOCH="$(date -u +%s)"

make fetch-cloud-atmosphere-data
make prepare-cloud-atmosphere-data
make verify-cloud-atmosphere-data
make generate-cloud-atmosphere

unset SOURCE_DATE_EPOCH
```

The fixed instant is optional but recommended. Without it, fetch and render
sample their own process-start clocks. Do not reuse an old timestamp merely
to bypass freshness checks: P-Tree cloud observations must be no more than
six hours old at the selected process instant.

To export SVG, PDF, and PNG after verification, replace the final generation
command with:

```sh
make generate-cloud-atmosphere-artifacts
```

Or run the same complete credentialed sequence—including the authorization
check—with one target:

```sh
make EXTERNAL_PASSES=jaxa-ptree generate-authorized-external
```

That wrapper runs the fetch, preparation, verification, and full SVG/PDF/PNG
artifact target. It is intentionally separate from `authorize-external`,
which remains read-only.

## 6. Confirm the result

The fetch stage writes ignored operational inputs under:

```text
assets.static/cloud-atmosphere/.raw/cloud-atmosphere-fetch-manifest.json
assets.static/cloud-atmosphere/.raw/YYYYMMDDHHMMSS/
```

Inspect the selected source intervals and number of downloaded tiles:

```sh
jq '{process_start_utc,
     observations: [.observations[] |
       {source, start_utc, end_utc, files: (.files | length)}]}' \
  assets.static/cloud-atmosphere/.raw/cloud-atmosphere-fetch-manifest.json
```

Preparation verifies every raw SHA-256 digest before writing:

```text
assets.static/cloud-atmosphere/.prepared/cloud-atmosphere-latest.geojson
assets.static/cloud-atmosphere/.prepared/cloud-atmosphere-latest.manifest.json
```

The explicit verify command must finish with `Verified cloud-atmosphere
snapshot`. Successful generation then writes six `cloud-atmosphere-*.svg`
files under `assets.generated/svg/`. Missing cells in those maps mean
unobserved, not clear sky and not zero.

Raw rasters and prepared snapshots are intentionally ignored by Git. They can
be large and must not be committed or redistributed merely because they were
downloaded successfully.

## Troubleshooting

| Symptom | What to check |
| --- | --- |
| `curl: (67)` or login denied | Confirm the completion email arrived, the machine name is exactly `ftp.ptree.jaxa.jp`, the login/password block is in the current user's `~/.netrc`, and the file mode is `600`. |
| Timeout or connection refused | Confirm outbound TCP port 990 is allowed. Check the [P-Tree FAQ and site status](https://www.eorc.jaxa.jp/ptree/faq.html) and retry later; JAXA notes that traffic can become busy. |
| `curl: (60)` with `unable to get local issuer certificate` | Run `make install-jaxa-certificate`, confirm its published SHA-256 check passes, and retry. Use `PTREE_CACERT=/absolute/path` only for an intentional alternate private location. Do not add `--insecure`. |
| `P-Tree supplied no H09 CLP file ... within six hours` | Check the machine's UTC clock and `SOURCE_DATE_EPOCH`. A current observation may be delayed; retry with a new current timestamp instead of weakening the six-hour profile limit. |
| A public JAXA collection cannot be resolved | Retry in case the static catalog is temporarily unavailable, then compare the collection IDs in the [source profile](../assets.static/cloud-atmosphere/cloud-atmosphere-profile.json) with the [live JAXA Earth STAC root](https://data.earth.jaxa.jp/stac/cog/v1/catalog.json). |
| Missing GDAL NetCDF or GeoTIFF support | Run `make check-prerequisite` and install the missing GDAL drivers before preparation. |
| Checksum mismatch during preparation or verification | Treat the staged data as incomplete or modified. Rerun fetch/preparation; do not edit the digest or snapshot to force acceptance. |
| Snapshot is stale during generation | Start a new run with a new current `SOURCE_DATE_EPOCH`, or use the same exported timestamp consistently across all four stages if the original observations are still within their configured freshness limits. |

An interrupted fetch is safe to rerun. The workflow stages downloads before
replacing the active raw manifest, and preparation installs the verified
snapshot separately. P-Tree also limits simultaneous connections and session
duration, so avoid launching many fetches in parallel.

## Before publishing output

Review the current P-Tree registration conditions, terms, and
[user guide](https://www.eorc.jaxa.jp/ptree/userguide.html) for the selected
observation date and intended use. They govern account security, use,
redistribution, acknowledgment, and reporting. The generated SVG includes
source credit, but that metadata does not replace the operator's obligations.
