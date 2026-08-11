# Reviewed reports and research records

`reports/` is a curated evidence area, not a general build-output directory.
Files remain ignored unless `.gitignore` explicitly admits a reviewed record.

## Admission policy

A report may enter source control only after an explicit human instruction
identifies it as a record to preserve. The admitted set should be the smallest
package that keeps the work legible and auditable:

- the reviewed PDF as an archival boundary object;
- named reviewer feedback and the planning or decision brief that explains
  the report's lineage; and
- a checked development page that records status, limitations, and QA.

Authored report source, CSS, manifests, metadata, derived HTML, copied
full-resolution plate trees, editor backups, page renders, contact sheets,
temporary QA directories, source-acquisition caches, and delivery receipts
remain ignored unless a later instruction admits a specific record.
Authoritative generated map trees and static release bundles retain their
existing artifact lifecycle outside Git.

Before admission, validate JSON, local links, PDF structure and selectable
text, embedded fonts, intended page geometry, and every rendered page. Record
unavailable accessibility certification rather than inferring it from
structural checks.

## Current admitted Stage 16I set

The reviewed `cartofreako-audit-outcomes-03` record comprises:

- `cartofreako-audit-outcomes-03.pdf`;
- `cartofreako-audit-outcomes-02-feedback.md`; and
- `cartofreako-audit-outcomes-02-next-steps.md`.

The PDF is the portable visual boundary object. Its source package, copied
plate directory, and browser HTML remain reproducible local intermediates
because they point to generated or experimental image trees governed
separately.

Source-control admission is not publication or release authority. Commit,
push, GitHub release, email, UCB AAO/S3 deposit, meeting invitation, and any
other external transfer remain distinct actions.
