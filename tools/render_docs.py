#!/usr/bin/env python3
"""Render every *.j2 template from the platform list in _build.yml.

The platform matrix handed to project-config in _build.yml is the
single source of truth for what this repository builds; rendered
documents (the README platforms badge) are generated from it so the
two can never drift apart.
"""

# Standard Python Libraries
import argparse
import difflib
import json
import pathlib
import sys
import urllib.parse

# Third-Party Libraries
import jinja2
import yaml

REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent
BUILD_WORKFLOW = REPO_ROOT / ".github" / "workflows" / "_build.yml"
SKIP_PARTS = {".claude", ".git", "node_modules"}


def platform_context() -> dict:
    """Build the template context from _build.yml's platform matrix."""
    workflow = yaml.safe_load(BUILD_WORKFLOW.read_text())
    platforms = json.loads(workflow["jobs"]["config"]["with"]["platforms"])
    short_names = [p.removeprefix("linux/") for p in platforms]
    badge = urllib.parse.quote(" | ".join(short_names), safe="")
    return {"platforms": platforms, "platforms_badge": badge}


def main() -> int:
    """Render or check every template in the repository."""
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--all", action="store_true", help="write rendered outputs")
    mode.add_argument(
        "--check",
        action="store_true",
        help="diff rendered outputs against committed files",
    )
    args = parser.parse_args()

    # Templates render Markdown, not HTML; autoescaping would corrupt
    # the output and there is no XSS surface. Block tags (e.g. the
    # raw guards around GitHub Actions ${{ }} examples) must not leave
    # blank lines behind, hence the trim/lstrip settings.
    env = jinja2.Environment(  # nosec B701
        autoescape=False,
        keep_trailing_newline=True,
        lstrip_blocks=True,
        trim_blocks=True,
        undefined=jinja2.StrictUndefined,
    )
    context = platform_context()

    stale = False
    for template_path in sorted(REPO_ROOT.rglob("*.j2")):
        # Filter on the path relative to the repo root: the repo itself
        # may live under a filtered directory name (e.g. a worktree in
        # .claude/worktrees), which must not skip everything.
        relative_parts = template_path.relative_to(REPO_ROOT).parts
        if SKIP_PARTS.intersection(relative_parts):
            continue
        output_path = template_path.with_suffix("")
        rendered = env.from_string(template_path.read_text()).render(**context)
        committed = output_path.read_text() if output_path.exists() else ""
        if rendered == committed:
            continue
        if args.all:
            output_path.write_text(rendered)
            print(f"rendered {output_path.relative_to(REPO_ROOT)}")
        else:
            stale = True
            sys.stdout.writelines(
                difflib.unified_diff(
                    committed.splitlines(keepends=True),
                    rendered.splitlines(keepends=True),
                    fromfile=str(output_path.relative_to(REPO_ROOT)),
                    tofile=str(template_path.relative_to(REPO_ROOT)),
                )
            )
    if stale:
        print(
            "ERROR: rendered documents are stale; run ./render-docs-update",
            file=sys.stderr,
        )
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
