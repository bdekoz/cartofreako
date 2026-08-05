# Network-infrastructure source contract

The generator reads all network-infrastructure data from external source
repositories. No TeleGeography or cloud/CDN source dataset is copied into
cartofreako.

The checked profiles pin the source commits, primary-file SHA-256 digests,
snapshot dates, expected schemas, and exact record counts:

- `network-infrastructure-sites-profile.json` enables only located cloud/CDN
  site records;
- `network-infrastructure-topology-profile.json` explicitly enables the
  TeleGeography cable and Internet-exchange layers.

The default sibling source roots are configurable Make variables:

```text
NETWORK_INFRASTRUCTURE_CLOUD_SOURCE=../cloud_cdn_cache
SUBMARINE_CABLE_SOURCE=../www.submarinecablemap.com
INTERNET_EXCHANGE_SOURCE=../www.internetexchangemap.com
```

The cloud pin deliberately uses the internally consistent audited commit
`7af9b774d191c3c22137682ec697856ef85016a0`. A newer local snapshot observed
during implementation had a seven-record manifest/GeoJSON discrepancy and is
therefore not silently accepted.

The cloud repository says its original dataset is ODC-By 1.0 while provider
snapshots can retain source-specific terms. Both TeleGeography map repositories
state CC BY-NC-SA 3.0 Unported. Accordingly, topology generation is opt-in,
its outputs carry visible attribution and CC metadata, and topology targets are
not dependencies of `make all`.

Validate and generate the ordinary product with:

```sh
make check-network-infrastructure-sources
make generate-network-infrastructure
```

After reviewing the TeleGeography terms, opt in with:

```sh
make check-network-infrastructure-topology-sources
make generate-network-infrastructure-topology
```
