# Cartofreako — restart here

Status date: 2026-08-15 (late). This file is the cold-restart entry point: it
records where the repository and the surrounding hosts stand, what is done,
and the exact next steps, so a fresh session can resume without archaeology.

## Where things live

| Host | Role | Address | Notes |
| --- | --- | --- | --- |
| `rizal` | primary agent host (this repo) | local | all git pushes originate here |
| `eureka` | gate/release build host | 172.31.200.55 (`/etc/hosts`) | 125 GiB RAM; full gate ran green here |
| `ord` | idle | 172.31.200.57 | sshd keepalive fix only |

Eureka's checkout is `/home/bkoz/src/cartofreako`. Its login shell is `tcsh`,
so remote commands should be wrapped as `bash -lc '...'` over SSH, and multi-line
shell pastes break — prefer one-line commands.

## Repository state

- Remote: `git@github.com:bdekoz/cartofreako.git` (branch `main`).
- `origin/main` is at `52b8e82` (development-docs restructure); local `HEAD`
  equals `origin/main` and the working tree is clean.
- This file is tracked at `docs/development/20260815_explore_restart.md`.
- Development records moved from `docs/pages/development/` to
  `docs/development/`; navigation and repository-local links were updated, and
  `make check-docs` passed on 129 files / 1304 local links.
- The project-local snapshot-dyad ledger is frozen at
  `docs/profile-markers/snapshot-dyad-marker-ledger.json`; its canonical
  continuation is the ignored house-style asset
  `devastation-pacific-house-style/assets.rizal.bkoz/per-project/cartofreako/ledger.json`.
  Markers remain local-only until an explicit ledger check-in instruction.

## What is done (verified green on eureka)

1. **Alpha60-styled network passes** (`8eaae48`):
   - Network Fiber (renamed from Fiber Synthesized; alpha60 green/black fiber style)
   - Network CDN (renamed from network infrastructure sites; alpha60 black CDN style)
   - Network Groundstations (new pass; vendored alpha60 Starlink gateway data,
     red-triangle style)
   - Network swarm restyled to the izzi/alpha60-unique blue palette
2. **Corpus is now 217 artifacts / 33 passes** (was 211/32). Baseline bumps
   applied across scripts, schemas, fixtures, and S3 release tooling (`74b3504`).
3. **Gate fixes**:
   - atoll/cloud fetch→prepare ordering (`96d89a8`)
   - orbital-snapshot fallback on CelesTrak/NASA failure (`3ad7077`)
   - per-invocation D-Bus isolation for Inkscape (`fc78d80`)
   - wasm-projections prerequisite ordering for wasm consumers (`af16ccf`)
   - Majuro exporter Inkscape fallback — no browser needed anywhere (`27daadf`)
   - Network Groundstations path densification for high-cell projections (`bd0e6ff`)
4. **Stage 15A freeze** re-advanced to eureka's corpus at `c3263c1`
   (217 cases, `e006b3e`). The freeze is **machine-bound**: the raster parents
   differ across Inkscape/font versions, so the baseline must be re-advanced on
   the host that builds the release.
5. **Full gate green on eureka** (`all-experiments-resilient` phases):
   clean+fetch, resilient build (217), and all eight experiments (GPU controls
   434, consumer layout 217/45, atoll canary, Marshall Islands, equal-earth,
   Majuro, PurpleAir, water-debris). No make errors.
6. **SSH keepalive remediation** on rizal/eureka/ord: sshd drop-in
   `ClientAliveInterval 120` / `ClientAliveCountMax 3` + client
   `ServerAliveInterval 120`. Scoped sudoers file
   `/etc/sudoers.d/cartofreako-ssh` (bkoz NOPASSWD for
   `systemctl restart sshd` + `tee`) — safe to remove once this work is done.
7. GitHub Pages builds from `main`; docs are current (a Cahill-Keyes gallery
   card was added in `5484a74`).
8. **Eureka GitHub auth fixed**: dedicated passphrase-less deploy key
   `~/.ssh/id_ed25519_gh` on eureka, added to the `bdekoz` GitHub account as
   "eureka cartofreako", with `~/.ssh/config` routing `github.com` through it
   (`IdentitiesOnly yes`). Verified (`Hi bdekoz! ...`); eureka's branch is
   synced with `origin/main` (merge `cb482cb`). No ssh-agent needed.
9. **Development docs restructured** (`52b8e82`): moved
   `docs/pages/development/` to `docs/development/`, updated navigation and all
   repository-local links, rewrote `documentation-layout.md`, and passed the
   documentation link gate.

## Open items / decision queue

1. **Asset verification**: user is reviewing all generated + experiment
   assets. Confirmed complete on eureka (217 corpus, screens, 434 controls,
   layout 217/45, all five `output/` evidence dirs).
2. **v14 AAO upload decision**: user is leaning yes (immutable S3 v14 deposit
   so docs fixes are easier). Upload is a separate, human-gated operation
   (`release-ucb-aao-s3` or `scripts/upload-generated-assets-s3-release.sh` +
   `scripts/build-generated-assets-s3-release.sh`); the S3 tooling counts are
   prepped for 217 (tree 849, payload 852, objects 854).
3. **v20260815 source release** after AAO decision: tag `v20260815`, draft
   `docs/pages/releases/v20260815.md` release notes (user previously declined,
   may revisit), run `make release-github`.
4. **Docs fixes**: the development-docs restructure is complete; remaining
   release-facing documentation fixes still wait on the v14 upload decision.

## Resume commands

To bring eureka's commits to rizal (fallback if eureka ever cannot reach
GitHub again):

```sh
ssh eureka "bash -lc 'cd /home/bkoz/src/cartofreako && git format-patch -1 <hash> -o /tmp/eureka-final'"
scp eureka:/tmp/eureka-final/*.patch /tmp/
git am /tmp/*.patch      # use git apply --reject + manual fix if context diverges
```

Verify the gate log on eureka:

```sh
ssh eureka "bash -lc 'tail -20 /tmp/gate-experiments.log'"
```

## Key learnings

- The Stage 15A freeze is raster-machine-bound; advancing it must happen on
  the release host after its own build (bump `frozenCommit` in
  `scripts/freeze-stage-15-inputs.mjs` to the host HEAD, regenerate the catalog
  at a clean tree, `make refresh-stage-15-inputs`).
- No Chrome/Chromium exists on eureka; the Majuro exporter now falls back to
  Inkscape, so the gate has no browser dependency.
- Long gate runs should be under `tmux` on the remote and watched via
  `tail`/log files; keepalives are configured so idle SSH sessions survive.
