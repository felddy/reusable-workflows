# v5 Modernization — Tasks #

Stage 3 of 3. Decomposes [plan.md](plan.md) into PR-sized tasks.
Conventions:

- One task = one PR unless marked otherwise; IDs follow the plan's
  phases (A–E). References like D1/R1.1 point at plan design sections
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
- Docker Hub immutable-tags trial de-scoped (2026-10-19): GHCR is the
  system of record and Docker Hub publication is maintenance-only.

## Phase B — attestation modernization (v4.4.x) ##

### B1 — Migrate SBOM attestation to actions/attest (D5, R3.1) ###

- [x] `container-build.yml`: replaced `actions/attest-sbom` with
  `actions/attest` (native `sbom-path` input auto-detects SPDX and
  applies the same predicate type); `actions/attest-build-provenance`
  kept (it is the supported provenance generator); all attest steps on
  the v4 line.
- [x] Added `artifact-metadata: write` to every attesting job
  (build, publish, index-SBOM, rescan) and the `_build.yml` caller
  jobs; noted for the migration guide (C8).
- [ ] Acceptance: dogfood attestations present for both flavors
  (`oras discover` shows SBOM + provenance + vuln referrers); the
  existing attestation-skip logic still detects them; closes #488.

### B2 — Index-level SBOM subjects + verification gate (D5, R3.2) ###

- [x] `container-publish-manifest.yml`: a matrixed `attest-index-sbom`
  job attests each platform SBOM against the index digest (artifact
  first; falls back to extracting the platform image's SBOM
  attestation when the build skipped generation). Index attestations
  are now idempotent via the same `oras discover` check the build
  uses.
- [x] Post-sign `verify` job: `gh attestation verify` for provenance
  and SBOM predicate types plus `cosign verify` pinned to this repo's
  certificate identity; registry login covers the private flavor.
- [ ] Acceptance: gate passes for both flavors in dogfood;
  deliberately altering the expected predicate type fails the gate
  (verified once manually via workflow_dispatch on a branch).

### B3 — Rescan workflow + schedule split (D5, R3.3, R1.4) ###

- [x] New `container-rescan.yml` (workflow_call): resolve job maps
  tags → platform digests (crane); matrixed scan job downloads each
  platform's SBOM attestation, runs `trivy sbom` with the fallback DB
  config (A3), uploads SARIF (category
  `rescan-<image>-<tag>-<platform>`), refreshes the vuln attestation
  via `actions/attest`, fails above threshold.
- [x] New `_rescan.yml` caller in this repo: daily cron, both flavors,
  tags `["latest","edge"]`.
- [x] `_build.yml`: schedule is weekly (Monday 10:00 UTC); `edge`
  strategy unchanged.
- [ ] Acceptance: dispatched rescan green for both flavors with zero
  base-image pulls in logs; a seeded old tag with known CVEs
  (e.g. a pre-A1 image) turns the run red at CRITICAL,HIGH.

### B4 — VEX input (D5, R3.4) + release v4.4.0 ###

- [x] `container-build.yml` and `container-rescan.yml`: optional
  `vex-file` input threaded to Trivy via `TRIVY_VEX` (set only when a
  document is supplied).
- [ ] Acceptance: dogfood passes with no VEX file; a sample OpenVEX
  statement suppresses a chosen finding in a branch test.
- [ ] Release v4.4.0 after several green daily rescans.

## Phase C — v5 breaking core (v5.0.0-rc) ##

### C1 — Dedupe internals (D6, R4.6) — folded into C4 ###

Decision (follows from the Phase A finding): composites are not used.
A reusable workflow cannot reference its own composite actions by
local path (`uses: ./...` resolves against the *caller's* checkout),
and checking this repository out into the consumer workspace would
pollute docker build contexts. Instead, `container-pipeline.yml`
computes metadata and the platform/runner matrices **once** as inline
jobs and passes the results to build/test/publish as inputs. This
removes the duplicated metadata computation (previously run in both
build and publish), the `calculate-source-date-epoch` and
`determine-visibility` jobs, and both `generate-matrix` copies. The
uv/pip detection block stays duplicated between test and lint (30
lines; acceptable until a better mechanism exists).

- [x] Delete `container-metadata.yml` (logic moves into the pipeline's
  inline metadata job) and dead `container-sign.yml`.
- [ ] Acceptance: dogfood green; job count per flavor drops;
  `grep -r container-sign` and `grep -r container-metadata.yml`
  return nothing.

### C2 — Naming and token unification (D6, R4.1, R4.5) ###

- [x] `container-mirror.yml` + `dockerhub-description.yml`: all
  inputs/secrets to kebab-case; `container-test.yml`:
  `registry-token` → `private-package-token` (+ `-username`).
- [x] Update `_build.yml` callers in the same commit (atomic).
- [ ] Acceptance: dogfood green; no snake_case inputs remain
  (`grep -E '^      [a-z]+_' .github/workflows` clean); breaking
  changes logged for the migration guide.

### C3 — Fork-PR handling internalized (D3, R4.2) ###

- [x] Fork detection lives in the pipeline's metadata job (single
  place): fork PRs downgrade to build-only (no push, no digest export,
  no scan/attest); the pipeline exposes a `pushed` output.
- [x] `_build.yml`: fork conditionals deleted; test/publish skip
  when the effective push is false.
- [ ] Acceptance: dogfood green; a fork-simulation branch (condition
  temporarily forced) shows per-platform builds succeed with zero
  registry writes.

### C4 — container-pipeline.yml (D2, R4.3) ###

- [x] New workflow for one flavor: inline `metadata` job (absorbed
  from container-metadata.yml, plus fork-PR detection and visibility
  from the `private` input) and inline `generate-matrix` job feed
  build → test → publish called as sibling reusable workflows with
  metadata/matrix passed as inputs. Optional release-event post-jobs:
  DockerHub mirror and README publication (flavor opts in — avoids
  the matrix-job output-collision problem for downstream jobs).
  Inputs: image/platform/scan settings plus `private`,
  `pass-build-secrets`, `test-platforms`, `cache-scope` (defaults to
  flavor name), `vex-file`, `force-tag-overwrite`. Secrets forwarded
  conditionally on `private`/`pass-build-secrets`.
- [ ] Acceptance: a branch version of `_build.yml` drives both
  flavors through the pipeline via matrix + `secrets: inherit`; the
  public flavor's build logs show zero secret-file mounts; nesting
  depth ≤ 4 verified by a successful run.

### C5 — project-config.yml and ci-gate.yml (D6, R4.4) ###

- [x] `project-config.yml`: inputs `version-file`, `image-name`,
  `platforms`, `test-platforms`; outputs those plus `version` and
  `build-args` lines (`CONTAINER_VERSION=`).
- [x] `ci-gate.yml`: input `needs-json`; passes iff every result is
  `success` or `skipped`.
- [ ] Acceptance: this repo's `_config.yml` is replaced by a
  `project-config.yml` call; gate goes red when any needed job is
  forced to fail on a test branch.

### C6 — Immutability set (D4, R2.2–R2.4) — 3 PRs ###

- [x] Tag-overwrite guard: the manifest is pushed under a mutable
  staging tag and final tags are applied individually; in detail:
  immutable-class tag (default pattern `^v?[0-9]+\.[0-9]+\.[0-9]+`)
  with crane before `imagetools create`; same digest → no-op,
  different digest → fail unless `force-tag-overwrite`. Mirror
  gains the matching tolerance (immutable-tag push rejection with
  equal digest → success).
- [x] `container-retag.yml`: recomputes floating tags from release
  state (API) and `crane tag`s existing digests; no build. `_retag.yml`
  runs it on `release: edited` + dispatch; `edited` removed from
  `_build.yml`. (Mirror/readme chaining dropped — DockerHub is
  maintenance-only.)
- [x] Digest-on-release: the pipeline writes an idempotent,
  marker-delimited section (digest + verify command) into the release
  notes, serialized per release across flavors; `contents: write` on
  the pipeline caller job (migration-guide entry).
- [ ] Acceptance: re-publishing an existing semver tag with different
  content fails the guard on a test branch; editing a release
  re-points `latest` without any build jobs; release notes show
  both flavors' digests after a release event.

### C7 — Rewrite `_build.yml` on the v5 pattern (D2) ###

- [x] Final form: project-config → matrix pipeline (2 flavors,
  mirror/readme opt-in inside the pipeline) → ci-gate; retag path from
  C6.
- [x] `development.json` required check updated to `CI Gate / Gate`;
  operator applies via `make apply-ruleset` at merge.
- [ ] Acceptance: full dogfood green across PR, push, dispatch
  events; branch protection shows the single gate check.

### C8 — Documentation (D5, R6.2, R6.3, R3.8) ###

- [x] README: v5 composition, mermaid update, SLSA Build L3 posture,
  verification commands (`gh attestation verify`, `cosign verify`,
  `gh release verify`).
- [x] `docs/v5/migration.md`: every breaking change with before/after
  caller snippets (foundryvtt-docker and weewx-docker shaped),
  permission-block diffs (`artifact-metadata: write`,
  `contents: write`), secret renames, consumer checklists for D4/D5.
- [x] Acceptance: migration guide written against the actual diff of
  this repo's own `_build.yml` v4 → v5.

### C9 — Release v5.0.0-rc1 ###

- [x] Bump to 5.0.0-rc1, tag, publish as prerelease.
- [ ] Acceptance: this repo runs wholly on the rc; rc announcement
  notes link the migration guide.

## Phase D — release & migrate (v5.0.0) ##

### D1 — release-please + floating tag mover (D7, R2.6) ###

- [x] release-please workflow (manifest mode, `simple` release type
  owning `version.txt` + CHANGELOG.md; publishes complete releases on
  release-PR merge). Publishes via the RELEASE_PLEASE_TOKEN secret —
  GITHUB_TOKEN fallback keeps the release PR working but a release
  published that way does not trigger the Build pipeline.
- [x] Post-release step advances the floating major tag via the git
  refs API with GITHUB_TOKEN — no bypass needed (A4 verified forward
  moves are fast-forward). No `version-tag.json` bypass entry needed
  either: the PAT acts as the repository admin, whose bypass already
  covers semver tag creation.
- [x] README documents the release flow; bump-version remains only as
  a skeleton-provided script and is no longer part of this repo's
  release process.
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
- [ ] Operator: enable release immutability; apply ported rulesets
  change for the gate check. (Docker Hub immutable tags de-scoped —
  GHCR is the system of record.)
- [ ] Acceptance: full pipeline green for both flavors including a
  prerelease cut end-to-end; preinstall package remains private and
  unlinked.

### D5 — Migrate weewx-docker ###

- [x] Migrated (felddy/weewx-docker#508, on v5.0.0-rc2): single
  flavor, full project-config.yml adoption (local _config.yml
  deleted), daily rescan + retag, `image-tag` dispatch input kept and
  now honored. Required three preparatory fixes (felddy/weewx-docker
  #507): stale transitive lock pins, Debian security updates in the
  image build (foundry's archive-state pattern), and documented
  .trivyignore exceptions for pip-vendored packages that no pip
  release fixes yet.
- [ ] Acceptance: pipeline green at merge ✓; daily rescans stay red
  until fresh images publish (the v4-era latest/edge genuinely carry
  since-fixed CVEs) and until the rescan checkout fix reaches the
  consumer pin; release flow verified on the next weewx release.

### D6 — Close out ###

- [ ] One week of green daily rescans + weekly builds across all
  three repos; file issues for the deferred "could" items
  (BuildKit-native SBOM emission, dependency submission API,
  own-namespace sync contingency).
- [ ] Update `docs/v5/` stage docs' status headers to "delivered";
  v4 goes to maintenance (security backports only).

## Phase E — housekeeping consolidation (v5.x) ##

Design in plan.md D10. Non-breaking post-GA minors; each rw task is
one `feat:` PR cut as a release so consumers (on `@v5`) pick it up
without a pin change.

### E1 — dependency-review.yml callable (D10) ###

- [x] Promote `_dependency-review.yml` to dual-trigger
  `dependency-review.yml` (`workflow_call` + `pull_request`). The job
  id stays `dependency-review` — it is the status-check context the
  development rulesets require, here and in consumers.
- [x] Acceptance: this repo's own PR check runs the dual-trigger file
  (#596); a branch call from foundryvtt-docker passed
  (felddy/foundryvtt-docker#1595). Consumer check contexts gain the
  caller-job prefix (`dependency-review` →
  `dependency-review / dependency-review`) — ruleset updates folded
  into E10.

### E2 — stale-issues.yml callable (D10) ###

- [x] Dual-trigger (`workflow_call` + schedule); inputs for the
  stale/close day counts with current values as defaults. The stale
  message interpolates the day counts, and schedule/dispatch runs fall
  back to the same values the call defaults advertise.

### E3 — sync-labels.yml callable + central label definitions (D10) ###

- [x] Central labels file in this repo; the callable checks it out
  explicitly (`repository:` input at `central-ref`, default `v5`, so
  consumers ride the same floating tag they call; `job_workflow_sha`
  is an OIDC claim only, not a `github` context property), merges an
  optional caller overlay at `.github/labels.yml` (last writer wins by
  name), applies with ghaction-github-labeler.
  Apply only on the caller's default branch; other refs dry-run. The
  `autorelease: pending/tagged` labels joined the central set — the
  labeler deletes unlisted labels, and losing release-please's state
  labels mid-release was a latent defect in the per-repo copies.
- [ ] Consumer stubs: weekly schedule + `workflow_dispatch` + push on
  their overlay path.
- [ ] Acceptance: a dispatch run converges one consumer's labels; a
  consumer-only overlay label survives the sync.

### E4 — label-prs.yml + label-automerge.yml callable (D10) ###

- [x] Both files gain `workflow_call` alongside their native triggers
  (this repo's copies were already SHA-pinned; foundry's tag-pinned
  `actions/labeler@v7` / `action-job-preamble@v1` disappear with its
  E10 stub conversion). `label-automerge` keeps `pull_request_target`
  — safe since no PR code is checked out or executed. The caller's own
  `.github/labeler.yml` path rules stay per-repo.

### E5 — codeql-analysis.yml callable (D10) ###

- [x] `languages` input (JSON-array string into the matrix via
  fromJSON; default `["actions"]`, which is also this repo's own set);
  SARIF upload runs in the caller's context (proven pattern). The
  required "CodeQL" ruleset context is the code-scanning tool check
  (integration 57789), not an Actions job name, so the call prefix on
  "Analyze (…)" job names is cosmetic.

### E6 — renovate.yml callable (D10) ###

- [x] App id via `vars`, private key via `secrets: inherit`; the five
  permission-* token inputs baked in (delivers the standing "tighten
  foundry's renovate token" TODO at its E10 conversion);
  `renovate.json` stays per-repo. dry-run/log-level mirrored as
  workflow_call inputs. Stub gotcha recorded: workflow-level
  concurrency is ignored when called — consumer stubs declare their
  own group (and their own offset cron).

### E7 — render-docs.yml callable (D10) ###

- [x] Generalize `_render-release-docs.yml` into dual-trigger
  `render-docs.yml`: `render-command` input (default
  `sh render-docs-update`, the consumers' actual invocation, routed
  through env to satisfy the template-injection audit); uv toolchain;
  PAT push via a declared optional `RELEASE_PLEASE_TOKEN` secret so
  re-rendered commits re-run checks; `raw.githubusercontent.com` in
  the egress allowlist (setup-uv needs it). Commit message stays
  version-aware by probing `src/version.txt`.
- [x] Dogfood: this repo's README platforms badge renders from
  `_build.yml`'s platform matrix (`README.md.j2` +
  `tools/render_docs.py` + `render-docs-update`/`-check`, `docs`
  dependency group, render-docs-check pre-commit hook); the workflow
  runs directly on this repo's release branch.

### E8 — scorecards.yml callable (D10) ###

- [x] Callable file in the approved shape (see D10, restated in the
  file's header so future edits stay inside it);
  `fail_on_publish_error: true` so an enforcement change fails runs
  loudly — including this repo's own, which dogfoods the same file.
- [x] Pilot on weewx-docker only. Acceptance met 2026-10-29: fresh
  results published by the stub's own run (score intact), verified via
  the scorecard REST API. The pilot paid for itself: a global
  `permissions: read-all` in the called file failed stub callers at
  startup (a called workflow may not request more than the caller's
  job grants) — now workflow-level none, like the rest of the set.
- [x] Convert the remaining repos only after the pilot publishes:
  folded into the E10 conversions.

### E9 — felddy/.github defaults (operator + content) ###

- [x] `felddy/.github` already existed (2023 skeleton era); glowed up
  instead of created (felddy/.github#12): issue forms replace markdown
  templates, SUPPORT.md replaces the cisagov QUESTIONS catalog,
  SECURITY.md adds private vulnerability reporting, FUNDING.yml goes
  account-wide, skeleton machinery (lineage, broken 2023 pre-commit
  stack, build workflow) retired, default branch renamed to develop,
  and a sync-labels stub keeps form-assigned labels present.
- [x] Remove now-redundant generic copies from consumers that don't
  customize: FUNDING.yml dropped from weewx (#539) and foundry (in its
  E10 PR). foundry keeps its bespoke issue forms (all-or-nothing
  folder fallback).

### E10 — consumer conversions + close out ###

- [x] weewx converted (felddy/weewx-docker#537, merged): seven `@v5`
  stubs, local labels.yml deleted (first sync delivered the full
  central set), render-docs proven live on the release branch
  (render + PAT push + clean-tree early exit), ruleset context updated.
  Gotcha recorded: weewx's ruleset FILE lagged its live ruleset
  (`CI Gate` vs `CI Gate / Gate`) and applying the file regressed it —
  audit file-vs-live before every ruleset apply.
- [ ] foundry conversion open (felddy/foundryvtt-docker#1599): nine
  stubs, FUNDING.yml + labels.yml deleted, ruleset context updated
  (file-vs-live audited clean up front). felddy/.github re-pin to
  `@v5` open (felddy/.github#14).
- [ ] Update consumer rulesets alongside: reusable-call check contexts
  gain the caller-job prefix (`dependency-review` →
  `dependency-review / dependency-review`, verified in
  felddy/foundryvtt-docker#1595); apply from the PR branch per the
  migration-guide gotcha.
- [ ] Acceptance: one full action-bump cycle (Dependabot PR here →
  release → `v5` advance) reaches consumers with zero consumer PRs;
  consumers' remaining third-party pins are reduced to checkout in
  `_config.yml`.
- [ ] File an issue for the deferred labels fan-out dispatch.

### E11 — lint-config consolidation (D10) ###

Independent of E1–E6 and E8–E10; shares the render engine with E7.

- [x] Base in `lint-config/pre-commit-base.yaml` (the 49 hook entries
  byte-identical between this repo and foundry, plus actionlint,
  zizmor, and the terraform hooks, which no-op where no matching files
  exist); per-repo `.pre-commit-overlay.yaml` for local hooks and
  overrides. This repo's own config is now generated (ansible-lint,
  the mypy stubs dep, and render-docs-check live in its overlay); the
  dead pre-commit.ci `ci:` block is gone. Dotfiles (.yamllint,
  .flake8, …) deferred: all differ materially between repos today —
  phase 2 after configs converge.
- [x] `tools/merge_precommit.py` merges base + overlay
  deterministically in the house yamllint style (indented sequences,
  double quotes); a `lint-config-check` hook in this repo's overlay
  fails commits when the generated file is stale.
- [x] Reusable `config-sync.yml`: regenerates the caller's config from
  the central base at `central-ref` (default `v5`) plus the caller's
  overlay, and opens an auto-merging squash PR on drift (PAT push so
  checks run).
- [x] Renovate `pre-commit` manager enabled, scoped to the base file
  only; a `postUpgradeTasks` regenerates this repo's own config in the
  bump commit so the lint-config-check hook stays green.
- [x] `common-lint.yml` drift check: when a caller has an overlay, the
  generated config is re-derived from the base at `lint-config-ref`
  and a mismatch fails lint (skipped for this repo, whose unreleased
  base would false-fail; its local hook covers it).
- [ ] Converge consumers: overlay + generated config + config-sync
  stub per consumer (closes weewx's rev drift and finally delivers
  actionlint + zizmor); retire `.github/lineage.yml` where the sync
  replaces it. Needs a release carrying this task first.
- [ ] Acceptance: a hook bump merged here reaches both consumers as
  auto-merged sync PRs; a hand edit to a consumer's rendered config
  fails that repo's lint run.
