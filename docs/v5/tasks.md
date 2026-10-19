# v5 Modernization — Tasks #

Stage 3 of 3. Decomposes [plan.md](plan.md) into PR-sized tasks.
Conventions:

- One task = one PR unless marked otherwise; IDs follow the plan's
  phases (A–D). References like D1/R1.1 point at plan design sections
  and requirements.
- Order within a phase is dependency order; every merge leaves
  `develop` releasable (the dogfood build must pass on every PR).
- Use conventional-commit titles throughout (release-please depends on
  them from Phase D onward; the habit starts now).

## Phase A — stop the bleeding (v4.3.x) ##

### A1 — Route base images through mirror.gcr.io (D1, R1.1) ###

- [x] Dockerfile: `FROM public.ecr.aws/docker/library/rust:trixie` →
  `FROM rust:trixie` (canonical docker.io reference).
- [x] Daemon-mirror step (writes `registry-mirrors` into
  `/etc/docker/daemon.json` and restarts the daemon) inlined in both
  workflows. A local composite action cannot be used: local `uses:`
  paths resolve against the caller's checkout when a reusable
  workflow runs in another repository.
- [x] `container-build.yml`: daemon mirror before QEMU/buildx setup;
  inline buildkitd config on `setup-buildx-action`:
  `[registry."docker.io"] mirrors = ["mirror.gcr.io"]`.
- [x] `container-test.yml`: daemon mirror before QEMU setup;
  `mirror.gcr.io:443` added to the harden-runner allowlist.
- [ ] Acceptance: dogfood PR green on all 10 platforms; a diagnostic
  step shows the daemon mirror via `docker system info`; no
  `public.ecr.aws` left in the Dockerfile; QEMU/binfmt pull succeeds
  via the daemon mirror.

### A2 — Authenticated fallback and build retry (D1, R1.2, R1.3) ###

- [x] `container-build.yml`: optional `docker-hub-username` /
  `docker-hub-password` secrets; when present, `docker/login-action`
  against `docker.io` so the mirror-miss fallback path is
  authenticated. Additive, non-breaking. (Presence check runs through
  job env — the secrets context is unavailable in step-level `if`.)
- [x] Build retry: first build attempt `continue-on-error`, identical
  second attempt gated on failure, hard-fail step if both fail (GHA
  layer cache makes the retry cheap).
- [ ] Acceptance: dogfood green with secrets absent (login skipped,
  retry skipped); workflow lint passes.

### A3 — Trivy DB resilience (D5, R3.5) ###

- [x] Set `TRIVY_DB_REPOSITORY` and `TRIVY_JAVA_DB_REPOSITORY` on all
  Trivy steps to an ordered fallback list
  (`ghcr.io/aquasecurity/trivy-db:2,mirror.gcr.io/aquasec/trivy-db:2,
  public.ecr.aws/aquasecurity/trivy-db:2`; java-db equivalents).
- [ ] Acceptance: scan steps green; chosen repository visible in scan
  logs.

### A4 — Rulesets as code (D8, R5.6) ###

- [x] Export this repo's live rulesets/branch protections
  (`gh api repos/felddy/reusable-workflows/rulesets`), reconcile with
  foundryvtt-docker's `development.json` shape.
- [x] Add `.github/rulesets/` (development.json, version-tag.json
  locking `refs/tags/v*.*.*`, major-tag.json advance-only for bare
  `refs/tags/v*` excluding `v*.*`), plus the directory README.
- [x] Add a Makefile with only `apply-ruleset`, `export-ruleset`, and
  the gh/jq guard targets (ported from foundryvtt-docker).
- [x] Operator step (Mark, admin): `make apply-ruleset`; then
  `make export-ruleset` round-trips with an empty diff. Verified: all
  three live rulesets match the files byte-for-byte.
- [x] Verified and recorded in the ruleset README: a forward tag move
  (to a descendant commit) evaluates as fast-forward — rule-suite
  result `pass`, no bypass — so the Phase D tag mover needs no bypass
  actor. Backward moves and deletions require bypass.
- [x] Acceptance: files merged; live rulesets match files; semver-tag
  create/update/delete all evaluate as rule violations (rule-suite
  result `bypass` for an admin; non-bypass actors are rejected).
  Consequence for D1: release-please's identity needs a
  `version-tag.json` bypass entry to *create* release tags.

### A5 — Hygiene batch (D9, R5.1, R5.2, R5.4) ###

- [x] dependabot.yml: remove the `npm` and `docker-compose` ecosystems
  (and add a 7-day version-update cooldown; security updates bypass
  it).
- [x] Issue #485 (automerge label): the workflow already matches
  labels.yml (`automerge :bell:`); verified and closed, no code
  change.
- [x] Fix the corrupted comment in `container-metadata.yml`
  (`# tag=v7.0.1.2.7.0.1`).
- [x] Sync `version.txt` to the latest release (4.2.1) so the next
  bump is correct.
- [ ] Acceptance: nightly Dependabot run has no failing update jobs;
  #485 closed.

### A6 — Workflow static analysis (D9, R5.3) ###

- [x] Add `actionlint` (shellcheck integration off until the embedded
  scripts are shellcheck-clean — tracked as follow-up) and `zizmor`
  (`--min-severity=medium`) hooks to `.pre-commit-config.yaml`.
- [x] Triage findings: all template-injection fixed by hoisting
  interpolations into `env:` (except dead `container-sign.yml`,
  ignored pending its v5 removal); workflow-level write permissions
  scoped per job; `persist-credentials: false` on all checkouts;
  accepted findings recorded in `.github/zizmor.yml`.
- [x] Consumers inherit the hooks through their own pre-commit
  configs via the skeleton/lineage, not through `common-lint.yml`.
- [x] Acceptance: `pre-commit run --all-files` green; zizmor
  medium-and-above = 0.

### A7 — Release v4.3.0 ###

Known transient (observed 2026-10-19, post-merge run): artifact
downloads can fail with `HTTP 503: Egress is over the account limit`
— GitHub's Actions artifact-egress quota, unrelated to registries.
`gh run rerun --failed` recovers once the quota window moves. If it
recurs, Phase C should reduce artifact round-trips (the per-platform
digest artifacts are the hot path).

- [ ] After one week of green scheduled builds (Phase A exit
  criterion): bump-version minor → 4.3.0, tag, publish release.
- [ ] Operator step: enable Docker Hub immutable tags (semver regex)
  on `felddy/reusable-workflow` mirror repos — low-risk trial before
  consumers adopt it (D4).

## Phase B — attestation modernization (v4.4.x) ##

### B1 — Migrate SBOM attestation to actions/attest (D5, R3.1) ###

- [ ] `container-build.yml`: replace `actions/attest-sbom` with
  `actions/attest` (predicate-type
  `https://spdx.dev/Document/v2.3`, `predicate-path` = Syft output);
  keep `actions/attest-build-provenance` (it is the supported
  provenance generator); confirm all attest steps are on the v4 line.
- [ ] Add `artifact-metadata: write` to the build and publish job
  permission blocks and to `_build.yml`; note it prominently for the
  migration guide (C8).
- [ ] Acceptance: dogfood attestations present for both flavors
  (`oras discover` shows SBOM + provenance + vuln referrers); the
  existing attestation-skip logic still detects them; closes #488.

### B2 — Index-level SBOM subjects + verification gate (D5, R3.2) ###

- [ ] `container-publish-manifest.yml`: download the per-platform SBOM
  artifacts (same `gh run download --name` pattern as digests) and
  attest each against the index digest.
- [ ] Add a post-sign verification gate: `gh attestation verify
  oci://<image>@<index-digest> --repo <repo>` for provenance and SBOM
  predicate types, plus `cosign verify` pinned to this repo's
  certificate identity. Private flavor verifies with registry auth.
- [ ] Acceptance: gate passes for both flavors in dogfood;
  deliberately altering the expected predicate type fails the gate
  (verified once manually via workflow_dispatch on a branch).

### B3 — Rescan workflow + schedule split (D5, R3.3, R1.4) ###

- [ ] New `container-rescan.yml` (workflow_call): inputs `image-name`,
  `tags` (JSON, default `["latest"]`), `scan-severity`, `vex-file`;
  secret `private-package-token`. Per tag: resolve index → platform
  digests (crane), download each platform's SBOM attestation, run
  `trivy sbom` with the fallback DB config (A3), upload SARIF
  (category `rescan-<tag>-<platform>`), refresh the vuln attestation
  via `actions/attest`, fail the run above threshold.
- [ ] New `_rescan.yml` caller in this repo: daily cron, both flavors,
  tags `["latest","edge"]`.
- [ ] `_build.yml`: schedule becomes weekly (Monday 10:00 UTC);
  `edge` strategy unchanged.
- [ ] Acceptance: dispatched rescan green for both flavors with zero
  base-image pulls in logs; a seeded old tag with known CVEs
  (e.g. a pre-A1 image) turns the run red at CRITICAL,HIGH.

### B4 — VEX input (D5, R3.4) + release v4.4.0 ###

- [ ] `container-build.yml` and `container-rescan.yml`: optional
  `vex-file` input threaded to Trivy `--vex`.
- [ ] Acceptance: dogfood passes with no VEX file; a sample OpenVEX
  statement suppresses a chosen finding in a branch test.
- [ ] Release v4.4.0 after several green daily rescans.

## Phase C — v5 breaking core (v5.0.0-rc) ##

### C1 — Composite actions extraction (D6, R4.6) — 2 PRs ###

Constraint discovered in Phase A: a reusable workflow cannot reference
its own composite actions by local path — `uses: ./...` resolves
against the *caller's* checkout. The composites must either be
referenced by full `owner/repo/path@ref` (requires a ref-update step
at release time) or the workflow must first check out
felddy/reusable-workflows at `github.workflow_ref` into a subdirectory
and use path-based references into it. Decide at implementation.

- [ ] PR 1: `.github/actions/container-metadata` composite replacing
  `container-metadata.yml` (absorbs `determine-visibility` and the
  `calculate-source-date-epoch` job via its `commit-epoch` output);
  rewire `container-build.yml` and `container-publish-manifest.yml`;
  delete `container-metadata.yml` and `container-sign.yml`.
- [ ] PR 2: `.github/actions/platform-matrix` (shared by build +
  test) and `.github/actions/python-test-deps` (shared by test +
  lint).
- [ ] Acceptance: dogfood green; job count per flavor drops (no
  metadata/epoch/visibility jobs); `grep -r container-sign` and
  `grep -r container-metadata.yml` return nothing.

### C2 — Naming and token unification (D6, R4.1, R4.5) ###

- [ ] `container-mirror.yml` + `dockerhub-description.yml`: all
  inputs/secrets to kebab-case; `container-test.yml`:
  `registry-token` → `private-package-token` (+ `-username`).
- [ ] Update `_build.yml` callers in the same PR (atomic).
- [ ] Acceptance: dogfood green; no snake_case inputs remain
  (`grep -E '^      [a-z]+_' .github/workflows` clean); breaking
  changes logged for the migration guide.

### C3 — Fork-PR handling internalized (D3, R4.2) ###

- [ ] `container-build.yml`: detect fork PRs; build-only mode (no
  push, no digest export, no scan/attest); expose a `pushed` output.
- [ ] `_build.yml`: delete the fork conditionals; test/publish skip
  when `pushed != 'true'`.
- [ ] Acceptance: dogfood green; a fork-simulation branch (condition
  temporarily forced) shows per-platform builds succeed with zero
  registry writes.

### C4 — container-pipeline.yml (D2, R4.3) ###

- [ ] New workflow chaining build → test → publish for one flavor.
  Inputs: image/platform/scan settings plus `private`,
  `pass-build-secrets`, `test-platforms`, `cache-scope` (defaults to
  flavor name), `vex-file`, `force-tag-overwrite`. Secrets forwarded
  conditionally on `private`/`pass-build-secrets`.
- [ ] Acceptance: a branch version of `_build.yml` drives both
  flavors through the pipeline via matrix + `secrets: inherit`; the
  public flavor's build logs show zero secret-file mounts; nesting
  depth ≤ 4 verified by a successful run.

### C5 — project-config.yml and ci-gate.yml (D6, R4.4) ###

- [ ] `project-config.yml`: inputs `version-file`, `image-name`,
  `platforms`, `test-platforms`; outputs those plus `version` and
  `build-args` lines (`CONTAINER_VERSION=`).
- [ ] `ci-gate.yml`: input `needs-json`; passes iff every result is
  `success` or `skipped`.
- [ ] Acceptance: this repo's `_config.yml` is replaced by a
  `project-config.yml` call; gate goes red when any needed job is
  forced to fail on a test branch.

### C6 — Immutability set (D4, R2.2–R2.4) — 3 PRs ###

- [ ] PR 1 — tag-overwrite guard: in publish, resolve each
  immutable-class tag (default pattern `^v?[0-9]+\.[0-9]+\.[0-9]+`)
  with crane before `imagetools create`; same digest → no-op,
  different digest → fail unless `force-tag-overwrite`. Mirror
  gains the matching tolerance (immutable-tag push rejection with
  equal digest → success).
- [ ] PR 2 — `container-retag.yml`: recompute floating tags from
  release state via the metadata composite; `crane tag` existing
  digests; no build. New `_retag.yml` caller on `release: edited` +
  dispatch; remove `edited` from `_build.yml` triggers; chain
  mirror/readme after retag on non-prerelease.
- [ ] PR 3 — digest-on-release: publish writes an idempotent,
  marker-delimited "Container images" section (tag → index digest →
  verify commands) into the release notes; `contents: write` on the
  publish job (migration-guide entry).
- [ ] Acceptance: re-publishing an existing semver tag with different
  content fails the guard on a test branch; editing a release
  re-points `latest` without any build jobs; release notes show
  both flavors' digests after a release event.

### C7 — Rewrite `_build.yml` on the v5 pattern (D2) ###

- [ ] Final form: project-config → matrix pipeline (2 flavors) →
  ci-gate → mirror/readme on release; retag path from C6.
- [ ] Update `development.json` required check to the gate job;
  operator applies via `make apply-ruleset`.
- [ ] Acceptance: full dogfood green across PR, push, dispatch
  events; branch protection shows the single gate check.

### C8 — Documentation (D5, R6.2, R6.3, R3.8) ###

- [ ] README: v5 composition, mermaid update, SLSA Build L3 posture,
  verification commands (`gh attestation verify`, `cosign verify`,
  `gh release verify`).
- [ ] `docs/v5/migration.md`: every breaking change with before/after
  caller snippets (foundryvtt-docker and weewx-docker shaped),
  permission-block diffs (`artifact-metadata: write`,
  `contents: write`), secret renames, consumer checklists for D4/D5.
- [ ] Acceptance: migration guide reviewed against the actual diff of
  this repo's own `_build.yml` v4 → v5.

### C9 — Release v5.0.0-rc1 ###

- [ ] Bump to 5.0.0-rc1, tag, publish as prerelease.
- [ ] Acceptance: this repo runs wholly on the rc; rc announcement
  notes link the migration guide.

## Phase D — release & migrate (v5.0.0) ##

### D1 — release-please + floating tag mover (D7, R2.6) ###

- [ ] release-please workflow (manifest config; `version.txt` as
  extra-file; publishes complete releases on release-PR merge).
- [ ] Post-release job moves the floating `v5` tag — no bypass needed
  (A4 verified forward moves are fast-forward). Add a
  `version-tag.json` bypass entry for the identity release-please
  runs as (semver tag creation is restricted).
- [ ] Note in CONTRIBUTING: bump-version retired for this repo;
  release-please is canonical.
- [ ] Acceptance: a dry-run release PR shows correct version + notes.

### D2 — Enable release immutability (operator) ###

- [ ] Repo settings: enable release immutability; confirm rulesets
  live (A4/C7).
- [ ] Acceptance: next release shows the "immutable" badge and
  `gh release verify <tag>` passes.

### D3 — Release v5.0.0 ###

- [ ] Merge the release-please PR → v5.0.0 published immutable;
  floating `v5` tag created; `gh release verify v5.0.0` green.

### D4 — Migrate foundryvtt-docker ###

- [ ] Single PR per the C8 checklist: pin bump to v5; flavor matrix
  (public + preinstall) via `container-pipeline`; delete local
  `_config.yml`, ci-gate job, fork conditionals; `FROM node` →
  docker.io reference; add `_rescan.yml` (daily) + `_retag.yml`;
  weekly build cron; secret names per migration guide.
- [ ] Operator: Docker Hub immutable tags (semver regex) on
  `felddy/foundryvtt`; enable release immutability; apply ported
  rulesets change for the gate check.
- [ ] Acceptance: full pipeline green for both flavors including a
  prerelease cut end-to-end; preinstall package remains private and
  unlinked.

### D5 — Migrate weewx-docker ###

- [ ] Same checklist, single flavor; remove the vestigial
  `image-tag` dispatch input (or wire it through
  `project-config.yml` if still wanted).
- [ ] Acceptance: pipeline + rescan green; release flow verified on
  the next weewx release.

### D6 — Close out ###

- [ ] One week of green daily rescans + weekly builds across all
  three repos; file issues for the deferred "could" items
  (BuildKit-native SBOM emission, dependency submission API,
  own-namespace sync contingency).
- [ ] Update `docs/v5/` stage docs' status headers to "delivered";
  v4 goes to maintenance (security backports only).
