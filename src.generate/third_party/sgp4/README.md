# Vallado/CelesTrak SGP4

`SGP4.cpp` and `SGP4.h` are the C++ reference implementation distributed
with *Revisiting Spacetrack Report #3*, AIAA 2006-6753, revision
2020-07-13. They were obtained from CelesTrak's official software archive:

<https://celestrak.org/publications/AIAA/2006-6753/>

The upstream [permission FAQ](https://celestrak.org/publications/AIAA/2006-6753/faq.php)
states that the source may be used for any purpose with citation and a link
to its main page. The files are kept unmodified so published
verification vectors remain applicable. Cartofreako compiles this legacy
translation unit separately with its upstream warning profile; all adapter
code continues to use the repository's strict warnings.

Captured-file SHA-256 digests:

```text
source archive  3642043b706c76be87cf012db3f22e04da6b80498d00f515e51879e0ffadc115
SGP4.cpp        2ee7ad0e8f201e8251894083fe21e33a7aace2f43c871bf04357eb44a891b06e
SGP4.h          2a5ec44e059a52b3173d78d9a28bda8142b4f6497c1eb16febc2cea4b5006b0c
```

The adapter initializes SGP4 from CelesTrak OMM fields and uses WGS-72 and
AFSPC operation mode, as recommended for compatibility with the published
reference results.
