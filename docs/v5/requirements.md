# v5 Modernization — Requirements #

Stage 1 of 3 (requirements → plans → tasks). This document defines *what*
v5 of the reusable container workflows must do and why. It does not
prescribe implementation; that is stage 2.

Breaking changes are in scope: v5 is a major version bump.

## Evidence base ##

Findings that drive these requirements:

- **CI failures are dominated by ECR Public rate limiting.** Every
  scheduled Build run from 2026-10-14 through 2026-10-18 failed with
  `429 Too Many Requests` / `toomanyrequests: Data limit exceeded`
  resolving `public.ecr.aws/docker/library/rust:trixie` (this repo) and
  `public.ecr.aws/docker/library/node` (foundryvtt-docker) during the
  buildx `FROM` fetch. AWS caps anonymous pulls at 1/sec plus a shared
  500 GB/month unauthenticated data quota; GitHub-hosted runners share
  egress IPs, so anonymous CI pulls are structurally unreliable.
- **GitHub immutable releases are GA** (org/repo opt-in). Once a release
  is published: the tag is permanently locked (never movable, never
  reusable), assets are frozen, and a release attestation is generated
  (`gh release verify`). Title, notes, prerelease flag, and the
  "latest" marker remain editable. Floating major tags (`v4`, `v5`)
  are unaffected because they are plain git tags with no release
  object. Docker Hub now supports per-repo immutable tags (regex
  selectable); GHCR has no tag immutability feature.
- **`actions/attest-sbom` is deprecated** in favor of `actions/attest`
  (v4), which also backs `actions/attest-build-provenance` (tracked
  here as issue #488). Attestations are stored as Sigstore bundles and
  verified with `gh attestation verify`. GHCR still does not implement
  the OCI referrers API (verified 2026-10-19); Docker Hub does.
- **Consumers carry copy-pasted boilerplate** that belongs in the
  reusable layer: a local `_config.yml` + `make github-output` version
  derivation, an aggregate-status `ci-gate` job, fork-PR conditionals
  on every build job, and a SARIF-upload eligibility expression.
  foundryvtt-docker duplicates the entire build → test →
  publish-manifest chain to produce its public and private
  (`-preinstall`) flavors.
- Minor defects: `container-sign.yml` is never called (signing is
  inlined in `container-publish-manifest.yml`); `container-mirror.yml`
  and `dockerhub-description.yml` use `snake_case` inputs while all
  other workflows use `kebab-case`; dependabot.yml configures `npm` and
  `docker-compose` ecosystems with no matching files (fails nightly);
  `version.txt` (4.1.0) has drifted from the latest release (v4.2.1);
  a corrupted version comment exists in `container-metadata.yml`;
  issue #485 reports an automerge-label bug.

## R1 — Registry resilience (fix ECR "too many requests") ##

- **R1.1 (must)** Base-image pulls must not depend on anonymous access
  to rate-limited registries: route them through a mirror whose pulls
  do not count against upstream limits, with automatic fallback to the
  canonical registry (optionally authenticated). Acceptance: a week of
  scheduled builds with zero 429s.
- **R1.2 (must)** `container-build.yml` accepts optional credentials
  for additional registries (ECR Public authenticated pulls raise the
  limit 10×; also covers Docker Hub pulls of `tonistiigi/xx`,
  `moby/buildkit`, binfmt images — issue #428 territory).
- **R1.3 (should)** Transient-failure tolerance: retry with backoff on
  429/5xx during base-image resolution rather than failing the whole
  platform matrix on first error.
- **R1.4 (should)** Reduce scheduled full rebuilds (see R3.3): most
  daily rebuilds exist to catch new CVEs, which an SBOM rescan does
  without pulling base images at all.
- **R1.5 (could)** Support injecting a buildkitd registry-mirror
  configuration for callers running their own mirror.

## R2 — Immutable release support ##

- **R2.1 (must)** All workflows function correctly in repositories with
  release immutability enabled, and that configuration becomes the
  documented default for this repo and its consumers.
- **R2.2 (must)** A published semver container tag is never silently
  overwritten. Because GHCR lacks native tag immutability, the publish
  step must check whether the tag already exists with a different
  digest and fail (with an explicit override input for emergencies).
  Floating tags (`latest`, `release`, `MAJOR`, `MAJOR.MINOR`, `edge`)
  remain intentionally mutable.
- **R2.3 (must)** Rebuilds no longer trigger on `release: edited`.
  Under immutability, edits can only change notes/title/prerelease/
  latest markers, so `edited` may at most re-run tag reconciliation,
  mirroring, or README publication — never a rebuild. The
  latest-marker change path must be handled deliberately.
- **R2.4 (should)** Publish-time traceability: record the final image
  index digest(s) back onto the GitHub release (release notes remain
  editable post-publish; assets do not), so a release page links
  immutably to the exact image.
- **R2.5 (should)** Document (and where possible verify in CI) the
  consumer-side verification story: `gh release verify`,
  `gh attestation verify oci://...`, cosign verify, and digest-pinned
  `FROM`/`uses:` references. Enable Docker Hub immutable tags (regex:
  semver only) for mirrored repositories.
- **R2.6 (could)** Evaluate publishing this repo's own releases as
  immutable (locks `vX.Y.Z`; keeps floating `v5` as a plain git tag)
  and adopting release automation so `version.txt`, the tag, and the
  release can no longer drift.

## R3 — Best-in-class SBOM and vulnerability attestations ##

- **R3.1 (must)** Migrate `actions/attest-sbom` and
  `actions/attest-build-provenance` usage to `actions/attest` v4
  (closes #488), including the new `artifact-metadata: write`
  permission and Sigstore bundle storage.
- **R3.2 (must)** Attest the multi-arch **index digest** (provenance +
  SBOM + vuln) in addition to per-platform digests, and add a
  post-publish verification gate: `gh attestation verify` (and cosign
  verify) must pass against the published tag before the pipeline
  reports success.
- **R3.3 (should)** Add a scheduled **rescan** workflow that
  re-evaluates published images for new CVEs from their attested SBOMs
  (no rebuild, no base-image pulls) and refreshes the vulnerability
  attestation; replace the daily full-rebuild schedule with it.
- **R3.4 (should)** VEX support: accept OpenVEX document(s) as input to
  the scan gate so known-not-exploitable CVEs don't block builds, and
  publish the VEX statements alongside the image.
- **R3.5 (should)** Harden the Trivy path against upstream outages
  (fallback `--db-repository` list; the 2026-10-19 mirror.gcr.io 404
  broke scans for a day).
- **R3.6 (could)** Emit BuildKit-native SBOM/provenance
  (`sbom: true`, `provenance: mode=max`) so registry-native tooling
  (Docker Scout, etc.) sees attestations in the image index, in
  addition to GitHub attestations.
- **R3.7 (could)** Submit image SBOMs to GitHub's dependency
  submission API so container dependencies appear in the dependency
  graph and Dependabot alerts.
- **R3.8 (should)** Document the SLSA v1.0 Build L3 claim (reusable
  workflow + GitHub-hosted runners + artifact attestations) and what
  consumers must check to rely on it.

## R4 — API consolidation (breaking) ##

- **R4.1 (must)** Consistent `kebab-case` input/secret naming across
  every workflow (breaks `container-mirror.yml` and
  `dockerhub-description.yml` callers).
- **R4.2 (must)** Fork-PR handling moves inside `container-build.yml`:
  detect fork PRs and build without pushing instead of requiring every
  caller to gate jobs with repository-equality conditionals.
- **R4.3 (must)** First-class multi-flavor builds: one orchestrator
  call describes N flavors (name suffix, platforms, scan settings,
  secrets, cache scope, visibility), eliminating foundryvtt-docker's
  duplicated job chains. The dogfood pipeline in this repo exercises
  at least two flavors (public + private), as it does today.
- **R4.4 (must)** Absorb consumer boilerplate as reusable pieces:
  version/config derivation (version-file in → image name, version,
  platforms out) and an aggregate-status `ci-gate` suitable for branch
  protection.
- **R4.5 (should)** One token story: a single documented secret name
  for private-package auth across build, test, publish, and mirror
  (today: `private-package-token` in two workflows, `registry-token`
  in another).
- **R4.6 (should)** Remove dead or duplicated internals: delete or
  re-integrate `container-sign.yml`; share the platform→runner matrix
  logic used by both build and test; compute SARIF-upload eligibility
  internally instead of via caller expressions.
- **R4.7 (should)** Re-evaluate the numbered `build-secret-1..5` /
  `test-secret-1..5` interface for ergonomics within `workflow_call`
  constraints; keep proper per-secret redaction.

## R5 — Supporting workflow hygiene ##

- **R5.1 (must)** Fix dependabot.yml (drop or satisfy the `npm` and
  `docker-compose` ecosystems that fail nightly).
- **R5.2 (must)** Fix the automerge label defect (issue #485).
- **R5.3 (should)** Add workflow static analysis (zizmor, actionlint)
  to the lint path for this repo and as part of `common-lint.yml`.
- **R5.4 (should)** Repair small defects: corrupted action-version
  comment in `container-metadata.yml`; reconcile `version.txt` with
  the release process (see R2.6).
- **R5.5 (could)** Review stale-issues/labeler/label-prs for currency;
  they work today and are low priority.
- **R5.6 (must)** Manage branch and tag protection as code: adopt
  foundryvtt-docker's `.github/rulesets/` + Makefile apply/export
  mechanism in this repo, with tag rules aligned to the immutability
  design (semver tags locked; floating major tags advance-only).

## R6 — Quality and migration ##

- **R6.1 (must)** The dogfood pipeline remains the integration test:
  every feature above is exercised by this repo's own build (including
  the tag-overwrite guard and rescan via dry-run/dispatch paths).
- **R6.2 (must)** A v4 → v5 migration guide covering every breaking
  change, with before/after caller snippets for foundryvtt-docker and
  weewx-docker.
- **R6.3 (should)** README pipeline documentation updated to describe
  the v5 composition (flavors, mirror, rescan).

## Non-goals ##

- Migrating talos-rpi5-builder onto these workflows (its
  delete-and-recreate release flow does break under immutable
  releases, but that is a separate downstream effort).
- Fixing weewx-docker's uv-audit dependency failures (downstream).
- Building on the OCI referrers API for attestation discovery on GHCR
  (GHCR does not implement it yet).
- Keyed (non-keyless) signing improvements beyond what exists.

## Open questions ##

1. **Mirror destination and scope (R1.1):** mirror base images to
   `ghcr.io/felddy/mirror/<image>` per-owner? Is any AWS account
   available/desired for authenticated ECR Public pulls instead of or
   in addition to mirroring?
1. **Scheduled builds (R1.4/R3.3):** is the daily 10:00 build's only
   job to refresh `edge` and catch CVEs? Proposal: scheduled SBOM
   rescan daily, full rebuild weekly (refreshing `edge`).
1. **Cosign signing (R3):** keep the separate cosign keyless signature
   alongside GitHub attestations (ecosystem compatibility with
   `cosign verify`), or drop it and rely on Sigstore-bundle
   attestations alone? Recommendation: keep both for v5.
1. **Release automation (R2.6):** adopt release-please (or similar)
   for this repo, or keep the manual bump-version + tag flow with a
   documented checklist?
1. **Flavor API shape (R4.3):** preference for a matrix-style input on
   a single orchestrator vs. keeping per-flavor workflow calls with
   less boilerplate? (Stage 2 will propose a concrete design either
   way.)
