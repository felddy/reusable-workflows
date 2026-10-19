# Repository rulesets #

This directory holds the repository's GitHub rulesets, managed as code
so that branch and tag protection is reviewable, version-controlled,
and reproducible instead of being hand-edited in the web UI.

## How it works ##

Each `*.json` file in this directory is a single, self-contained
ruleset, identified by its `name` field rather than a numeric ID so
nothing is hardcoded. The Makefile targets operate on every `*.json`
file here, so adding or removing a ruleset is just a matter of adding
or removing a file.

Managing rulesets requires the GitHub CLI (`gh`) and `jq`, with `gh`
authenticated as a repository admin.

## Rulesets in this repository ##

- `development.json` — protections for the default branch and
  `develop-*` branches: PRs required, status checks, code scanning
  gates, and signed commits.
- `version-tag.json` — full semver tags (`v*.*.*`, e.g. `v4.2.1`) are
  locked: no creation, update, or deletion except by bypass actors.
  Release tags are immutable once published.
- `major-tag.json` — floating major tags (`v4`, `v5`) advance to each
  new release, so updates are allowed; deletion and non-fast-forward
  moves are blocked. A floating tag can only move forward.

## Tag-rule semantics ##

GitHub evaluates a tag move to a *descendant* commit as a fast-forward
update: advancing a floating major tag (for example `v4` to a newer
release commit) passes the `non_fast_forward` rule with no bypass.
Moving a tag backward or deleting it violates the rules and requires a
bypass actor, as does any create, update, or delete of a full semver
tag. Automation that must create semver tags (release tooling) needs
its identity added to `version-tag.json`'s `bypass_actors`.

## Applying ##

Push the local rulesets up to GitHub:

```console
make apply-ruleset
```

For each file, `apply-ruleset` resolves the ruleset by its `name`. If
a ruleset with that name already exists it is updated (`PUT`);
otherwise it is created (`POST`). The same body works for both, so
this also bootstraps a repository that has no matching ruleset yet.

## Exporting ##

If a ruleset is edited in the GitHub UI, pull those changes back into
the files so the repository stays the source of truth:

```console
make export-ruleset
```

For each file, `export-ruleset` fetches the live ruleset (located by
its `name`), strips the read-only fields the API rejects on write
(`id`, `_links`, timestamps, and so on), and rewrites the JSON.
Review the diff and commit the result.

## Decoding numeric IDs ##

Rulesets reference GitHub Apps and repository roles by numeric ID
because the API requires the number rather than a slug. These IDs are
stable; look one up with the GitHub CLI, for example:

```console
gh api /apps/github-actions --jq '{slug, id, name}'
```

`actor_id: 5` under `RepositoryRole` is the repository admin role.
