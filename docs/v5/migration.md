# Migrating from v4 to v5 #

v5 replaces the per-stage caller wiring with a single flavor pipeline and
makes the immutability and verification behavior described in
[plan.md](plan.md) the default. Every breaking change is listed here with
the caller-side fix.

## 1. Call the pipeline, not the stages ##

The build → test → publish-manifest job chains (and their fork-PR
conditionals, which are now handled internally) collapse into one matrixed
call. Before (per flavor, abridged):

```yaml
jobs:
  build:
    if: github.event_name != 'pull_request' || github.event.pull_request.head.repo.full_name == github.repository
    uses: felddy/reusable-workflows/.github/workflows/container-build.yml@v4
    with:
      platforms: ${{ needs.config.outputs.platforms }}
      image-name: felddy/foundryvtt
  test:
    uses: felddy/reusable-workflows/.github/workflows/container-test.yml@v4
    # ...
  publish:
    uses: felddy/reusable-workflows/.github/workflows/container-publish-manifest.yml@v4
    # ...
```

After (both flavors in one job):

```yaml
jobs:
  pipeline:
    name: Pipeline (${{ matrix.flavor }})
    needs: [config, lint, diagnostics]
    strategy:
      fail-fast: false
      matrix:
        include:
          # Give every matrix row explicit values for every field the
          # pipeline call forwards; expression fallbacks (|| defaults)
          # misread intentionally-empty and missing values.
          - flavor: public
            image-name: felddy/foundryvtt
            private: false
            pass-build-secrets: false
            scan-severity: CRITICAL,HIGH
            upload-scan-results: true
            mirror: true
            readme: true
          - flavor: preinstall
            image-name: felddy/foundryvtt-preinstall
            private: true
            pass-build-secrets: true
            scan-severity: ""
            upload-scan-results: false
            mirror: false
            readme: false
    permissions:
      actions: read
      contents: write # release-notes digest recording
      packages: write
      id-token: write
      attestations: write
      artifact-metadata: write
      security-events: write
    uses: felddy/reusable-workflows/.github/workflows/container-pipeline.yml@v5
    with:
      image-name: ${{ matrix.image-name }}
      platforms: ${{ needs.config.outputs.platforms }}
      test-platforms: ${{ needs.config.outputs.test-platforms }}
      private: ${{ matrix.private }}
      pass-build-secrets: ${{ matrix.pass-build-secrets }}
      scan-severity: ${{ matrix.scan-severity }}
      upload-scan-results: ${{ matrix.upload-scan-results }}
      build-args: ${{ needs.config.outputs.build-args }}
      mirror-on-release: ${{ matrix.mirror }}
      publish-readme-on-release: ${{ matrix.readme }}
      build-secret-1-name: foundry_username
      build-secret-2-name: foundry_password
    secrets:
      private-package-token: ${{ secrets.PRIVATE_PACKAGE_TOKEN }}
      docker-hub-username: ${{ secrets.DOCKER_USERNAME }}
      docker-hub-password: ${{ secrets.DOCKER_PASSWORD }}
      build-secret-1: ${{ secrets.FOUNDRY_USERNAME }}
      build-secret-2: ${{ secrets.FOUNDRY_PASSWORD }}
```

The pipeline forwards `private-package-token` only to flavors with
`private: true` and the build secrets only with `pass-build-secrets: true`,
so a single secrets block safely serves every flavor.

## 2. Permissions ##

Pipeline caller jobs need, beyond the v4 set: `artifact-metadata: write`
(actions/attest@v4 storage records) and `contents: write` (digest recording
in release notes). The full block is shown in the snippet above.

## 3. Renamed inputs and secrets ##

| Workflow | v4 | v5 |
| --- | --- | --- |
| container-mirror.yml | `image_name` | `image-name` |
| container-mirror.yml | `image_tag_names` | `image-tag-names` |
| container-mirror.yml | `source_registry` / `target_registry` | `source-registry` / `target-registry` |
| dockerhub-description.yml | `image_name` / `filepath` | `image-name` / `file-path` |
| dockerhub-description.yml | `docker_username` / `docker_password` | `docker-hub-username` / `docker-hub-password` |
| container-test.yml | `registry-token` | `private-package-token` (+ optional `private-package-username`) |

## 4. Removed ##

- `container-metadata.yml` — absorbed into the pipeline's metadata job.
- `container-sign.yml` — was never wired in; signing lives in
  container-publish-manifest.yml.
- `container-build.yml`'s `platforms` input and its metadata-derived
  outputs (`image-tags`, `image-tag-names`, `image-version`); the stage now
  takes `build-matrix`, `image-labels`, `image-annotations`, and
  `source-date-epoch` inputs from the pipeline. `container-test.yml` takes
  `test-matrix` instead of `platforms`;
  `container-publish-manifest.yml` takes `image-tags` and no longer emits
  tag outputs. Callers using the pipeline are unaffected.

## 5. Release events ##

- Trigger builds on `release: [published]` only. `edited` events are
  handled by a retag caller — add an `_retag.yml` to your repository:

```yaml
on:
  release:
    types: [edited]
jobs:
  retag:
    permissions:
      contents: read
      packages: write
    uses: felddy/reusable-workflows/.github/workflows/container-retag.yml@v5
    with:
      image-name: felddy/foundryvtt
      release-tag: ${{ github.event.release.tag_name }}
```

- Semver tags are immutable at publish: re-running a release workflow is a
  no-op when digests match, and repointing an existing semver tag fails
  without `force-tag-overwrite: true`.
- Enable repository release immutability (Settings → Releases) and apply
  the tag rulesets from `.github/rulesets/` so git-level protections match.

## 6. Scheduling: weekly builds, daily rescans ##

Change the build cron to weekly and add a daily `_rescan.yml`:

```yaml
on:
  schedule:
    - cron: 0 10 * * *
jobs:
  rescan:
    permissions:
      contents: read
      packages: write
      id-token: write
      attestations: write
      artifact-metadata: write
      security-events: write
    uses: felddy/reusable-workflows/.github/workflows/container-rescan.yml@v5
    with:
      image-name: felddy/foundryvtt
      tags: '["latest","edge"]'
```

## 7. Adopt project-config and ci-gate ##

Replace the local `_config.yml` + `make github-output` plumbing with
`project-config.yml` (inputs: `version-file`, `image-name`, `platforms`,
`test-platforms`), and the copy-pasted aggregate-status job with:

```yaml
  ci-gate:
    name: CI Gate
    needs: [diagnostics, config, lint, pipeline]
    if: always()
    permissions: {}
    uses: felddy/reusable-workflows/.github/workflows/ci-gate.yml@v5
    with:
      needs-json: ${{ toJSON(needs) }}
```

Point the branch-protection required check at `CI Gate / Gate`.

## Consumer checklists ##

### foundryvtt-docker ###

1. Bump the pin to v5; replace the six build/test/publish jobs with the
   matrixed pipeline call (section 1 snippet is foundry-shaped).
1. `FROM public.ecr.aws/docker/library/node:…` →
   `FROM node:…` (docker.io reference; CI routes it through
   mirror.gcr.io).
1. Keep the local Foundry version derivation step; feed its outputs into
   the pipeline's `build-args`. Adopt `project-config.yml` for the rest.
1. Delete fork-PR conditionals and the local ci-gate job; update the
   required check to `CI Gate / Gate` in the rulesets.
1. Switch the build cron to weekly; add `_rescan.yml` (both flavors) and
   `_retag.yml`; drop `release: edited` from the build triggers.
1. Operator: enable release immutability; `make apply-ruleset`.

### weewx-docker ###

Same as above with a single flavor and no build secrets; remove the
vestigial `image-tag` dispatch input or keep it (the pipeline's dispatch
strategy still honors it).
