# Network-infrastructure source contract

The generator reads all network-infrastructure data from external source
repositories. No TeleGeography or cloud/CDN source dataset is copied into
cartofreako.

The checked profiles pin source provenance, primary-file and referenced cable
detail SHA-256 digests, snapshot versions, expected schemas, and exact record
counts:

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

The cloud pin uses audited commit
`1be1eb04e73320e0337a74a99686cd532f09ad9b`: 28 canonical layers and
27,378 records. The normal profile deliberately excludes observed cloud
presences, including the new 11,659-record geocoded observation layer, so its
rendered set remains 1,003 provider-declared locations. The observations stay
in the parsed and validated source totals without being presented as declared
infrastructure sites.

The cloud repository says its original dataset is ODC-By 1.0 while provider
snapshots can retain source-specific terms. Both TeleGeography map repositories
state CC BY-NC-SA 3.0 Unported. Accordingly, topology generation is opt-in,
its outputs carry visible attribution and CC metadata, and topology targets are
not dependencies of `make all`.

The submarine-cable profile uses the content snapshot `v3.20260805`: 697
cable systems, 718 route features, and 1,922 landing points. Its exact content
digests are authoritative; the cable source directory does not need to be a
clean Git checkout.

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
