# Guide for agents

This file explains how to change Humanizer without breaking its package or prompt.

## What this repo contains

Humanizer is an agent skill written in Markdown. `SKILL.md` is the prompt that agents read. The repo has no build step.

Keep the skill portable. Do not write instructions that limit it to one or two agent tools.

## Key files

- `SKILL.md` is the source of truth and the repo's only skill file. It contains portable YAML metadata, an account of why AI text sounds the way it does, and numbered patterns grouped in seven sections and ordered by strength and frequency. Group G holds the rules local to this fork.
- `README.md` explains installation, use, and patterns.
- `CHANGELOG.md` holds the release notes, newest first. Old notes keep the pattern numbers their release used.
- `.claude-plugin/plugin.json` describes the Claude plugin and points its skill loader at the root `SKILL.md`.
- `.claude-plugin/marketplace.json` lets users add this repo as a Claude marketplace.
- `.cursor-plugin/plugin.json` describes the Cursor plugin. Omit a `skills` path so Cursor loads the root `SKILL.md`.
- `agents/openai.yaml` holds the display name, short description, and default prompt for OpenAI-compatible agents.
- `scripts/validate-package.py` checks package files and shared values.
- `scripts/check-upstream-merge.py` checks a merge from upstream: every upstream pattern
  present in its own slot with its own title, its body unchanged except for the fork's two
  documented edits to §1 and §13, and the fork's own rules contiguous after upstream's and
  unchanged from before the merge apart from renumbering. Run it as
  `python3 scripts/check-upstream-merge.py upstream/main` before committing a merge.
- `scripts/check-tells.py` checks `tells.py` itself: every pattern key names a SKILL.md rule
  that exists, every regex compiles, and against `origin/main` no detector has been removed or
  demoted from ACT to CHECK and no enumerable watch word has lost coverage. The first gate
  catches a key naming no rule at all; a key pointing at the wrong existing rule still passes,
  which is what a renumber produces, so the renumber checklist below is not optional. Roughly a
  third of the patterns use quantifiers or lookarounds and cannot be expanded into words; those
  are covered by the removal and demotion gate rather than word by word, and the script prints
  how many. A deliberate drop goes in `WAIVED_WORDS` with its reason, which keeps an intended
  change visible and an accidental one failing. `.github/workflows/tells.yml` runs it on pull
  requests and on pushes to `main`, where the comparison is against itself and so vacuous. Pass
  `--against REF` to compare elsewhere.
- `tells.py` is local to this fork. It greps for the mechanically detectable tells and is what
  step 8 of the skill's workflow runs. Its table is keyed on pattern numbers, so a renumber
  means updating it by hand; `check-tells.py` catches a key naming no rule at all, but not one left pointing at the wrong rule.

## Rules for changes

Keep `SKILL.md` and `README.md` in sync.

- **Patterns:** Patterns are numbered from 1 without gaps, strongest and most frequent first. A new tell earns a pattern only when no existing pattern already implies it; prefer folding it into an existing pattern. If you add, remove, or renumber a pattern, update the README tables, the README section title, and every §reference, and `tells.py`'s table keys, then run `python3 scripts/check-tells.py`. The validator derives the count from the headings and checks that README pattern names match them.
- **Version:** Keep the same version in `SKILL.md` under `metadata.version`, the first `CHANGELOG.md` heading, `.claude-plugin/plugin.json`, and `.cursor-plugin/plugin.json`. Do not add a top-level `version` field to the skill.
- **Compatibility:** Keep install and use instructions neutral across agents. Names such as Claude Code, Cursor, OpenCode, and Codex are examples, not limits.
- **Description:** The plugin manifests use the first sentence of the `SKILL.md` description.
- **Length:** Every word of `SKILL.md` is read on each use. The validator caps it at 9,500 words in this fork, widened from upstream's 5,500 to fit the fork's extra 3,266 words, of which group G is 2,692; a change that adds words should earn them.
- **History:** Add a short `CHANGELOG.md` note for any behavior change or non-obvious fix.
- **Checks:** Before publishing, run `python3 scripts/validate-package.py`, `python3 scripts/check-tells.py`, `npx skills add . --list`, and `claude plugin validate .`. After merging upstream, also run `python3 scripts/check-upstream-merge.py upstream/main`. That one stays out of CI deliberately: it compares against a moving `upstream/main`, so the moment upstream releases a pattern this fork has not merged yet, the numbering collides and the check reads red for a fork that is perfectly healthy.

## Writing style

Use Plain Language in code comments, prompts, documentation, descriptions, validation messages, and progress reports.

- Lead with the main point.
- Use common words and active voice.
- Keep sentences and paragraphs short.
- Use one term for the same item.
- Use `must` for requirements.
- Use headings, lists, and tables when they help the reader.
- Remove repeated or unnecessary words.
- Limit acronyms and explain technical terms.
- Avoid double negatives.
- Keep exact identifiers, commands, paths, schema fields, quotations, watched phrases, and behavior-bearing examples.
- Keep the full technical meaning.

## Editing the skill

- Keep the YAML metadata valid.
- Treat the prompt below the metadata as the product.
- Prefer a short, clear instruction over another exception or repeated explanation.
