# GitHub repository and the directory of branch/tag rulesets managed as code.
# Ruleset IDs are resolved at run time by name, so they are not hardcoded.
# See .github/rulesets/README.md for what the JSON contains (and a decoder
# for the GitHub App IDs it references).
REPO := felddy/reusable-workflows
RULESET_DIR := .github/rulesets

.PHONY: help guard-gh guard-jq apply-ruleset export-ruleset

## help: list the available targets.
help:
	@grep -E '^## ' Makefile | sed 's/^## //'

## guard-gh: fail loudly if the GitHub CLI is unavailable.
guard-gh:
	@command -v gh >/dev/null 2>&1 || { echo "ERROR: gh (GitHub CLI) is required" >&2; exit 1; }

## guard-jq: fail loudly if jq is unavailable.
guard-jq:
	@command -v jq >/dev/null 2>&1 || { echo "ERROR: jq is required" >&2; exit 1; }

## apply-ruleset: create or update every ruleset in RULESET_DIR (IDs resolved by name).
apply-ruleset: guard-gh guard-jq
	@test -n "$$(ls $(RULESET_DIR)/*.json 2>/dev/null)" || { echo "ERROR: no ruleset files in $(RULESET_DIR)" >&2; exit 1; }
	@set -e; \
	for f in $(RULESET_DIR)/*.json; do \
	  name=$$(jq -r '.name' "$$f"); \
	  id=$$(gh api "repos/$(REPO)/rulesets" --jq "[.[] | select(.name == \"$$name\") | .id][0] // empty"); \
	  if [ -n "$$id" ]; then \
	    echo "Updating ruleset '$$name' (id $$id) in $(REPO)"; \
	    gh api --method PUT "repos/$(REPO)/rulesets/$$id" --input "$$f" >/dev/null; \
	  else \
	    echo "Creating ruleset '$$name' in $(REPO)"; \
	    gh api --method POST "repos/$(REPO)/rulesets" --input "$$f" >/dev/null; \
	  fi; \
	done; \
	echo "Done."

## export-ruleset: overwrite each file in RULESET_DIR from its live ruleset.
export-ruleset: guard-gh guard-jq
	@test -n "$$(ls $(RULESET_DIR)/*.json 2>/dev/null)" || { echo "ERROR: no ruleset files in $(RULESET_DIR)" >&2; exit 1; }
	@set -e; \
	for f in $(RULESET_DIR)/*.json; do \
	  name=$$(jq -r '.name' "$$f"); \
	  id=$$(gh api "repos/$(REPO)/rulesets" --jq "[.[] | select(.name == \"$$name\") | .id][0] // empty"); \
	  if [ -z "$$id" ]; then echo "ERROR: no ruleset named '$$name' in $(REPO)" >&2; exit 1; fi; \
	  raw=$$(gh api "repos/$(REPO)/rulesets/$$id"); \
	  printf '%s\n' "$$raw" | jq -S '{name, target, enforcement, conditions, bypass_actors, rules}' > "$$f.tmp"; \
	  mv "$$f.tmp" "$$f"; \
	  echo "Wrote $$f from ruleset '$$name' (id $$id)"; \
	done
