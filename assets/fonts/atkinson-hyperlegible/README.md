# Atkinson Hyperlegible

The Setouchi legend reference specifies Atkinson Hyperlegible. These four
TrueType files make that typography reproducible without installing fonts
into a user's home directory. Regular, bold, italic and bold italic are
included; requests for weight 600 resolve to the available bold weight 700.

Source: [Google Fonts, Atkinson Hyperlegible](https://github.com/google/fonts/tree/95f4904fc8bcf26d3420fe315560c96417c6dec7/ofl/atkinsonhyperlegible),
revision `95f4904fc8bcf26d3420fe315560c96417c6dec7`.
The [SIL Open Font License](OFL.txt) permits redistribution. Exact download
URLs and SHA-256 hashes are recorded in `provenance.json`.

`scripts/legend_informatics.py` creates a repository-local Fontconfig
configuration and checks the resolved font before exporting SVGs. On the
development host, an unconfigured request previously substituted Montserrat
Bold; the revision uses the font declared in the supplied reference.
