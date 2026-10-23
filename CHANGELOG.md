# Changelog

## [5.1.0](https://github.com/felddy/reusable-workflows/compare/v5.0.1...v5.1.0) (2026-10-23)


### Features

* **build:** warn when VEX statements go stale ([e02e04d](https://github.com/felddy/reusable-workflows/commit/e02e04d5ba571c19472466885acaf6ca2160adbd))
* **build:** warn when VEX statements go stale ([f4d8446](https://github.com/felddy/reusable-workflows/commit/f4d844680b4f72494e65224eb66ab122d80a5ee5))


### Bug Fixes

* **rescan:** scan SBOMs with Grype so OS packages are matched ([1fe8b12](https://github.com/felddy/reusable-workflows/commit/1fe8b12ce3a9b5780aaf5bdf5165b46521589a6e))
* **rescan:** scan SBOMs with Grype so OS packages are matched ([5b512c3](https://github.com/felddy/reusable-workflows/commit/5b512c323d6583b66d185de8813b33c77d20b10f))

## [5.0.1](https://github.com/felddy/reusable-workflows/compare/v5.0.0...v5.0.1) (2026-10-22)


### Bug Fixes

* **deps:** upgrade virtualenv to patched 21.14.12 ([6b69e88](https://github.com/felddy/reusable-workflows/commit/6b69e88af02280a0091cb73ade8cc6c137700f8e))
* **deps:** upgrade virtualenv to patched 21.14.12 ([7c1996b](https://github.com/felddy/reusable-workflows/commit/7c1996bc4da6b787eea734cd47567f31ae3a626e))


### Miscellaneous Chores

* **deps:** bump the github-actions-all group with 4 updates ([dcd49b5](https://github.com/felddy/reusable-workflows/commit/dcd49b56b0a8bb6347f312ecbe58de1961cda39b))
* **release:** surface chores and deps in changelogs and releases ([f7726dc](https://github.com/felddy/reusable-workflows/commit/f7726dcd7759875cb3a30dff93557c5b2d476b91))
* **release:** surface chores and deps in changelogs and releases ([46b92ab](https://github.com/felddy/reusable-workflows/commit/46b92abae579394f5aa8b326485d5c4a70a0b89e))

## [5.0.0](https://github.com/felddy/reusable-workflows/compare/v4.2.1...v5.0.0) (2026-10-21)


### ⚠ BREAKING CHANGES

* branch protection now requires the single aggregate 'CI Gate / Gate' check produced by ci-gate.yml rather than individual test-job checks whose names changed with the pipeline restructure. Apply with 'make apply-ruleset'.
* **publish:** the manifest is pushed under a mutable staging tag and final tags are applied individually. Semver tags (configurable via immutable-tag-pattern) are never repointed to a different digest: identical digests are a no-op so re-runs stay idempotent, and anything else fails unless force-tag-overwrite is set. GHCR has no native tag immutability, so the guard lives here; it complements the version-tag ruleset and immutable releases.
* the primary caller API is now container-pipeline.yml. It computes metadata and platform/runner matrices once per flavor, detects fork pull requests (build-only, no caller conditionals), gates secret forwarding on the private/pass-build-secrets inputs, and chains build, test, publish, and the opt-in DockerHub release jobs.
* container-build.yml takes build-matrix, image-labels, image-annotations, and source-date-epoch inputs instead of computing them (its platforms input and metadata-derived outputs are gone); container-test.yml takes test-matrix instead of platforms; container-publish-manifest.yml takes image-tags and no longer runs its own metadata job (image-tags/tag-names/is-latest outputs removed).
* container-mirror.yml inputs are now image-name, image-tag-names, source-registry, target-registry; dockerhub-description.yml takes image-name, file-path, and docker-hub-username/docker-hub-password (matching container-build's fallback credentials); container-test.yml's registry-token becomes private-package-token with an optional private-package-username, matching build and publish.

### Features

* automate releases with release-please ([12ece42](https://github.com/felddy/reusable-workflows/commit/12ece42242d95367489dbc135132b98018184312))
* automate releases with release-please ([6e573a9](https://github.com/felddy/reusable-workflows/commit/6e573a91774b234bc270959ada1e431454cbcbde))
* build, test, and publish consume shared state as inputs ([16ed24b](https://github.com/felddy/reusable-workflows/commit/16ed24bb4abff6204e27819825849b3361681a54))
* **build:** accept an OpenVEX document for scan suppression ([fb00449](https://github.com/felddy/reusable-workflows/commit/fb00449bda2fc02aa5ae1e36e8285014f149f7b3))
* **build:** retry platform builds once on transient failures ([71b80d6](https://github.com/felddy/reusable-workflows/commit/71b80d691a454cfafac1c04b0c950ab0362873b4))
* **build:** support authenticated Docker Hub fallback pulls ([177994a](https://github.com/felddy/reusable-workflows/commit/177994a349c2d77b1a97e1ad3f035a187403c93f))
* container-pipeline orchestrates one flavor end to end ([972d07b](https://github.com/felddy/reusable-workflows/commit/972d07bbf7988af955fb96438c206a875298a158))
* **deps:** add 7-day cooldown to Dependabot version updates ([47a55b1](https://github.com/felddy/reusable-workflows/commit/47a55b158752aff5fc4125184c7274e4f85e6977))
* kebab-case inputs and one private-token name everywhere ([bf81a03](https://github.com/felddy/reusable-workflows/commit/bf81a03cac2903efbdd6bda26e4590e1391accfa))
* **lint:** add actionlint and zizmor pre-commit hooks ([8203cee](https://github.com/felddy/reusable-workflows/commit/8203cee6aa7c554d99100f92630b493616b6bdcf))
* manage repository rulesets as code ([a4e3e36](https://github.com/felddy/reusable-workflows/commit/a4e3e3602e7a92a2f1720067fc1336701a89bad2))
* **pipeline:** record image digests in release notes ([c62af9e](https://github.com/felddy/reusable-workflows/commit/c62af9e03b7b176d9c790fa35c1855b0f7d95a0f))
* project-config and ci-gate reusable workflows ([813e5e7](https://github.com/felddy/reusable-workflows/commit/813e5e7a6ea4d6c2e22351fc0ae2c26bcde5cb19))
* **publish:** immutable-tag guard via staged manifest tagging ([5c83130](https://github.com/felddy/reusable-workflows/commit/5c8313044caefe96cd622491dab3993f21f48a21))
* **publish:** index-level SBOM attestations and verification gate ([eb7667c](https://github.com/felddy/reusable-workflows/commit/eb7667c64b5012e7a254d7f33c75c5dcb4bee7c8))
* reconcile floating tags on release edits without rebuilding ([ed7c991](https://github.com/felddy/reusable-workflows/commit/ed7c991c7332c80e6108c4ed6f389800c6cf5227))
* require the CI Gate check instead of per-platform tests ([c89bfcb](https://github.com/felddy/reusable-workflows/commit/c89bfcb6f018e6856eec677c36acf0956e34ba32))
* scheduled SBOM rescan replaces daily rebuilds ([08a98e7](https://github.com/felddy/reusable-workflows/commit/08a98e7eb677afda3b0353b2e3f6f7f126a5e146))
* track workflow-pinned tool versions with Renovate ([471f274](https://github.com/felddy/reusable-workflows/commit/471f274a6ebcbac48146907f724028c259060efc))
* track workflow-pinned tool versions with Renovate ([00c96a8](https://github.com/felddy/reusable-workflows/commit/00c96a82300f2b474284b5e040276b680f525658))


### Bug Fixes

* **build:** add Trivy vulnerability DB fallback repositories ([7075f0f](https://github.com/felddy/reusable-workflows/commit/7075f0f8c097ce850e6b7745057a1460ce77bfab))
* **build:** log in to Docker Hub before QEMU and Buildx setup ([695cdb2](https://github.com/felddy/reusable-workflows/commit/695cdb2a2036cf672d41ebe376e3d13a29489cd0))
* **build:** migrate SBOM attestation to actions/attest ([2752a5d](https://github.com/felddy/reusable-workflows/commit/2752a5dba50748b906a90c787dd83a0b8b9a2d3e))
* **build:** route docker.io pulls through mirror.gcr.io ([96b706f](https://github.com/felddy/reusable-workflows/commit/96b706f2f7c64325a606b4110676cf1a7fdddc89))
* **build:** scope write permissions to the jobs that need them ([b77d9b3](https://github.com/felddy/reusable-workflows/commit/b77d9b3459402f64108e58a6f3c616767ecd8481))
* **build:** valid presence check for Docker Hub credentials ([ae2d88a](https://github.com/felddy/reusable-workflows/commit/ae2d88a8d72a1234a77ce278dd125cafe963651e))
* compute the next release from the last stable version ([f89510b](https://github.com/felddy/reusable-workflows/commit/f89510b890d53a49b816f478dc327f0ca90290c5))
* compute the next release from the last stable version ([f2a1d26](https://github.com/felddy/reusable-workflows/commit/f2a1d267213cc259e8460160eedee3e9717d2a4f))
* **deps:** upgrade certifi past the emSign root CA advisory ([3a91b66](https://github.com/felddy/reusable-workflows/commit/3a91b6648614d126ad2ca836dbfa128e1efaac23))
* **deps:** upgrade certifi past the emSign root CA advisory ([73c6245](https://github.com/felddy/reusable-workflows/commit/73c62451da3630eb1fe8d8a8d8853042001649e2))
* extract SBOM statements from Sigstore bundle attestations ([a745419](https://github.com/felddy/reusable-workflows/commit/a745419ba9958ce8d17fce85149b8b63095d9449))
* let admins merge release PRs past the signature rule ([cc2ddb8](https://github.com/felddy/reusable-workflows/commit/cc2ddb8caf3d9e8b9b0e7caf02435c8964e2ad5b))
* let admins merge release PRs past the signature rule ([7dc82e6](https://github.com/felddy/reusable-workflows/commit/7dc82e69fe296dfe1a1f8d3baf2da757a4892f38))
* **lint:** exempt the generated changelog from markdown formatting ([5825e75](https://github.com/felddy/reusable-workflows/commit/5825e75c8240483591237c2008037e81f22a41d3))
* **lint:** exempt the generated changelog from markdown formatting ([9c8c1a1](https://github.com/felddy/reusable-workflows/commit/9c8c1a1fdb0973a2f9d69e7a9f20de4b0d8e1cba))
* map file-path to the action's readme-filepath input ([d122e8d](https://github.com/felddy/reusable-workflows/commit/d122e8dbae6a58db2221d7bd3421a2b778f6f3ab))
* **mirror:** require referrer parity before skipping or tolerating ([10c4f69](https://github.com/felddy/reusable-workflows/commit/10c4f69b13ed024a0bc5d39649564ddd444f12a8))
* **pipeline:** preserve release-note formatting and survive update races ([c2bcbdf](https://github.com/felddy/reusable-workflows/commit/c2bcbdfb1dfd6bfa60e46be3a296814fee60c656))
* **publish:** count SBOM attestations against the platform count ([3e0db1a](https://github.com/felddy/reusable-workflows/commit/3e0db1a001532ce12247fafae8bf1af0720b0916))
* **publish:** fail closed on tag existence lookup errors ([cb32bed](https://github.com/felddy/reusable-workflows/commit/cb32bed907af72a6a8a3c624622728d92b6ec70e))
* **publish:** pin signature verification to the publishing workflow ([595fb9e](https://github.com/felddy/reusable-workflows/commit/595fb9e28b6281c647412cb790c41ac5b7f48da3))
* **publish:** run-unique staging tag; final tags applied from digest ([4f88130](https://github.com/felddy/reusable-workflows/commit/4f8813006a0bade67fd23645ede9fe9c2c7fc7f8))
* **publish:** verify attestations against the reusable-workflow signer ([f6750a7](https://github.com/felddy/reusable-workflows/commit/f6750a7ef87d15f11ecae4c0ef3784daceb83d5d))
* **publish:** verify attestations against the reusable-workflow signer ([9fe3127](https://github.com/felddy/reusable-workflows/commit/9fe3127044052c8e28e8ecf2f3efc59063410429))
* **renovate:** grant the token issues write for the dashboard ([707b2a6](https://github.com/felddy/reusable-workflows/commit/707b2a60934c9f09ce3a5aa59876020479434b25))
* **renovate:** grant the token issues write for the dashboard ([e3bfe47](https://github.com/felddy/reusable-workflows/commit/e3bfe47fd7915f3b52a406f520720b11b2eed688))
* **renovate:** grant the token vulnerability-alerts read ([ef7e54d](https://github.com/felddy/reusable-workflows/commit/ef7e54d924169235b41f61c2482b1d17673b4b72))
* **renovate:** grant the token vulnerability-alerts read ([51228d4](https://github.com/felddy/reusable-workflows/commit/51228d4e9e0f233d8a59aa681d8a6a8b00de46f9))
* **rescan:** always check out the caller's scan-policy files ([d471dac](https://github.com/felddy/reusable-workflows/commit/d471dacdd6deba5a7a7a52b6e0150e8bb54132da))
* **rescan:** always check out the caller's scan-policy files ([1f2a5e1](https://github.com/felddy/reusable-workflows/commit/1f2a5e17089494603884f68b0d967bb94e743e1d))
* **rescan:** fail tag resolution on any manifest fetch error ([3bd066b](https://github.com/felddy/reusable-workflows/commit/3bd066b629343d24a5dc3bfc9d6ba9cc617397d6))
* **rescan:** include the image in SARIF categories ([f274ad7](https://github.com/felddy/reusable-workflows/commit/f274ad73300dac7977121f3c84d9963cae8c9935))
* **retag:** reconcile channels to their rightful owners ([03e9857](https://github.com/felddy/reusable-workflows/commit/03e9857886bc0a5e395e54f4f32d5889bee376d8))
* **workflows:** hoist template expressions out of run scripts ([5981eec](https://github.com/felddy/reusable-workflows/commit/5981eec9c61e4014d4a714b9fbe1b2fb85c6cae1))
* **workflows:** stop persisting checkout credentials ([ec1e408](https://github.com/felddy/reusable-workflows/commit/ec1e408d28cf71f2b5a4d8947739ec9a22d228ec))


### Miscellaneous Chores

* pin the next release version ([f4df5ce](https://github.com/felddy/reusable-workflows/commit/f4df5ce574d77589ccf2cbb6c760499513a311d2))
