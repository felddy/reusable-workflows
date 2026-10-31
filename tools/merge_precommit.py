#!/usr/bin/env python3
"""Merge the central pre-commit base with a repo overlay.

The base (lint-config/pre-commit-base.yaml) carries the hooks and
revisions every repository shares; a repository's optional
.pre-commit-overlay.yaml layers local hooks and overrides on top. The
merged result is the repository's .pre-commit-config.yaml, a generated
file. Overlay semantics:

- Top-level keys other than ``repos`` deep-merge, overlay wins.
- An overlay repo matching a base repo by URL merges into it: hooks
  replace base hooks with the same id, new hooks append, and an
  explicit overlay ``rev`` overrides the base pin (omit it to follow
  the base).
- An overlay repo absent from the base appends after the base repos.
"""

# Standard Python Libraries
import argparse
import difflib
import pathlib
import sys

# Third-Party Libraries
import yaml

HEADER = """\
# GENERATED FILE - DO NOT EDIT.
# Merged from felddy/reusable-workflows lint-config/pre-commit-base.yaml
# and this repository's .pre-commit-overlay.yaml by
# tools/merge_precommit.py.
# yamllint disable rule:line-length
"""


class _IndentedDumper(yaml.SafeDumper):
    """Dump in the house yamllint style.

    Block sequences indent under their key, and scalars that need
    quoting take double quotes (the quoted-strings rule forbids single).
    """

    def increase_indent(self, flow: bool = False, indentless: bool = False):
        """Force indented sequences regardless of context."""
        return super().increase_indent(flow, False)

    def choose_scalar_style(self) -> str:
        """Upgrade single-quoted scalars to double-quoted."""
        style = super().choose_scalar_style()
        return '"' if style == "'" else style


def _deep_merge(base: dict, overlay: dict) -> dict:
    out = dict(base)
    for key, value in overlay.items():
        if isinstance(value, dict) and isinstance(out.get(key), dict):
            out[key] = _deep_merge(out[key], value)
        else:
            out[key] = value
    return out


def merge(base: dict, overlay: dict | None) -> dict:
    """Return the merged configuration mapping."""
    merged = {k: v for k, v in base.items() if k != "repos"}
    repos = [dict(r) for r in base.get("repos", [])]
    if overlay:
        for key, value in overlay.items():
            if key == "repos":
                continue
            if isinstance(value, dict) and isinstance(merged.get(key), dict):
                merged[key] = _deep_merge(merged[key], value)
            else:
                merged[key] = value
        by_url = {r["repo"]: r for r in repos}
        for over_repo in overlay.get("repos", []):
            target = by_url.get(over_repo["repo"])
            if target is None:
                repos.append(over_repo)
                continue
            if "rev" in over_repo:
                target["rev"] = over_repo["rev"]
            hooks = [dict(h) for h in target.get("hooks", [])]
            by_id = {h["id"]: i for i, h in enumerate(hooks)}
            for over_hook in over_repo.get("hooks", []):
                if over_hook["id"] in by_id:
                    hooks[by_id[over_hook["id"]]] = over_hook
                else:
                    hooks.append(over_hook)
            target["hooks"] = hooks
    merged["repos"] = repos
    return merged


def render(config: dict) -> str:
    """Serialize the merged configuration deterministically."""
    body = yaml.dump(  # noqa: DUO109 - _IndentedDumper extends SafeDumper
        config,
        Dumper=_IndentedDumper,
        default_flow_style=False,
        explicit_start=True,
        sort_keys=False,
        width=1000,
    )
    return HEADER + body


def main() -> int:
    """Merge, write, or check the generated configuration."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("base", type=pathlib.Path)
    parser.add_argument(
        "overlay",
        nargs="?",
        type=pathlib.Path,
        help="optional overlay; skipped when the file does not exist",
    )
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--output", type=pathlib.Path)
    group.add_argument(
        "--check",
        type=pathlib.Path,
        help="compare against an existing file; exit 1 on drift",
    )
    args = parser.parse_args()

    base = yaml.safe_load(args.base.read_text())
    overlay = None
    if args.overlay and args.overlay.exists():
        overlay = yaml.safe_load(args.overlay.read_text())
    rendered = render(merge(base, overlay))

    if args.output:
        args.output.write_text(rendered)
        return 0

    committed = args.check.read_text() if args.check.exists() else ""
    if rendered == committed:
        return 0
    sys.stdout.writelines(
        difflib.unified_diff(
            committed.splitlines(keepends=True),
            rendered.splitlines(keepends=True),
            fromfile=str(args.check),
            tofile="merged(base, overlay)",
        )
    )
    print(
        "ERROR: generated pre-commit config is stale; regenerate with "
        "tools/merge_precommit.py --output",
        file=sys.stderr,
    )
    return 1


if __name__ == "__main__":
    sys.exit(main())
