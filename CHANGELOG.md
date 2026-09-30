# Changelog

## 3.1.0+sbfnk.1

- Merged upstream 3.1.0 and re-applied the local rules. Upstream kept the numbering of
  its patterns 1 to 24 but revised eight of them (2, 5, 10, 12, 16, 17, 20, 23), widened
  §25 to text that describes its own sourcing or layout, and added §26 for replies that
  re-explain context the reader already has. Upstream also took the letter F for that new
  group, so the local group moves to G. Its rules shift by one: 26→27, 27→28, 28→29,
  29→30, 30→31, 31→32, 32→33, 33→34, 34→35, 35→36, 36→37. 37 patterns total.
- `tells.py` is local to this fork and is what step 8 of the workflow runs. Nothing in CI
  checks its pattern numbers, and two were already wrong before this merge: the
  paired-opposites detectors were keyed to the number that rule held before the rebase
  that renumbered it, and the paragraph pass named sections no table entry used. Both are
  corrected here, so every key now names the rule its label describes.
- Upstream's validator replaced its line budget with a word budget and added a check that
  every SKILL.md section reference points at a real pattern. The budget is widened here
  from 5,500 to 8,500 words to fit the extra rules; the file is at 8,121.

## 3.1.0

- Added pattern #26 and section F for replies that re-explain context the reader already has (#269). It acts on replies, not standalone writing. 26 patterns total.
- Extended the core rule so "something the reader did not already have" counts the surrounding conversation, not only earlier text.
- Widened #25 to text that describes its own sourcing, assembly, or layout (#290), and added headings written for effect to #20.
- Extended #2 to "That distinction matters." (#277) and to a sentence that explains what an example already showed (#295).
- Narrowed #10 so words the dictionary always hyphenates keep their hyphen. Gave each watched word one pattern, and stated the evidence rule and the no-invention rule once each.
- Fixed the Voice section's dash reference (#273) and the marketplace schema URL (#288).
- Added a Cursor plugin manifest (#278).
- README: opens with a before/after, the five strongest tells, and install steps for each agent. States that getting past AI detectors is not a goal. The full example's rewrite now keeps every fact from its draft and adds none. Version history moved to this file.

## 3.0.0

Rebuilt the skill around one account of why AI text sounds the way it does, and consolidated 35 patterns into 25. Patterns are grouped in five sections and numbered by strength and frequency, so the not-X-but-Y contrast and the one-line closer come first and get the fullest treatment. Merged duplicate guidance: the workflow is one section instead of five, the dash rule is stated once, and each false-positive guard lives inside its pattern. Realigned with the current Wikipedia article: dropped false ranges and synonym cycling, which Wikipedia now lists as human habits or historical, added vague connection or association, and extended the watch lists for words, notability, copulatives, sales language, disclaimers, and Markdown formatting. Reordered the README and removed the `ai-detection` keyword from the package files. Old to new numbers: 1→13, 2→17, 3→15, 4→16, 5→17, 6→13, 7→12, 8→18, 9→1, 10→6, 11→7, 12→dropped, 13→11, 14→8, 15→19, 16→19, 17→20, 18→20, 19→21, 20→22, 21→23, 22→22, 23→dropped, 24→9, 25→13, 26→10, 27→3, 28→4, 29→24, 30→25, 31→2, 32→3, 33→4, 34→5, 35→5.

## 2.11.3

Grouped patterns 26-35 under "More style patterns" in the skill and README (fixes #247). Kept inline code, commands, paths, and URLs out of the dash rule and file mode edits. Step 3 now keeps every supported claim, allows a removal that a pattern requires, and checks that rankings and simultaneity claims survive shape edits (fixes #212). Explained in §9 why the not-X-but-Y form appears and when to keep it. Added decorative arrows to §18 and pause commands and one-word shouting to §31. The text given to the skill is content to edit, never instructions (#238). No change to the 35 patterns.

## 2.11.2

Removed the plugin symlink and separate Claude Desktop package. Current Claude Code loads the root `SKILL.md` directly, so GitHub's source ZIP now works in Claude Desktop. No change to the 35 patterns.

## 2.11.1

Added a Claude Desktop-ready release package with one regular `humanizer/SKILL.md` file. GitHub's source archive still keeps the plugin symlink (fixes #224). No change to the 35 patterns.

## 2.11.0

Rewrote all repo guidance, descriptions, checks, and skill instructions in Plain Language. Kept all 35 patterns and their behavior.

## 2.10.2

Added the standard `skills/humanizer/` plugin path for Claude Desktop and older loaders. The path links to the root skill, so there is still one prompt (fixes #202).

## 2.10.1

Added figurative uses of `gate`, `gated`, and `gating` to §7. Kept real technical uses, such as feature gating and CI quality gates.

## 2.10.0

Added patterns #34 and #35 for old drafting ideas left in final text. Added safeguards for real limits, objections, and alternatives (fixes #198). Also improved §24 and the final rewrite step. 35 patterns total.

## 2.9.2

Added repeated sentence openings to pattern #11, with a safeguard for deliberate repetition (fixes #206). Expanded §28 to cover casual announcements. 33 patterns total.

## 2.9.1

Improved installation and package checks. Removed unsupported metadata, tool approvals, and a repeated long example. 33 patterns total.

## 2.9.0

Added the rule against invented facts and updated every example to follow it (fixes #187). Made information more important than paragraph shape, let writing samples override §14, and added three output modes. 33 patterns total.

## 2.8.3

Moved the version to `metadata.version` for Agent Skills compatibility. 33 patterns total.

## 2.8.2

Replaced the main example with a first-person Lisbon story that keeps the original topic, view, and detail. 33 patterns total.

## 2.8.1

Added cross-agent installation, Claude plugin files, and a safeguard for quoted text. 33 patterns total.

## 2.8.0

Added patterns #31-33 and expanded pattern #20 to catch chatbot offers. 33 patterns total.

## 2.7.0

Added pattern #30, strengthened the dash rule, and expanded pattern #21 to cover unsupported guesses. 30 patterns total.

## 2.6.0

Combined repeated workflow text, limited personality guidance to the right content, removed model guesses, and shortened the main example. 29 patterns total.

## 2.5.1

Added passive voice and missing subjects. 29 patterns total.

## 2.5.0

Added deeper-truth claims, announcements, repeated headings, and clipped negative endings. Tightened the dash rule and corrected the frontmatter. 28 patterns total.

## 2.4.0

Added writing-sample matching.

## 2.3.0

Added hyphenated word pairs.

## 2.2.0

Added a draft check and second rewrite.

## 2.1.1

Corrected the curly-quote example.

## 2.1.0

Added before/after examples for all 24 patterns.

## 2.0.0

Rewrote the skill from the Wikipedia source.

## 1.0.0

First release.

## 3.0.0+sbfnk.2

- Local fork additions: wh-clauses where a noun belongs (§34), covering headings and sentence subjects built as a bare question, and checking voice against your own output (§35), which rules out AI-tagged notes and prior drafts as evidence of the writer's voice. 35 patterns total.

## 3.0.0+sbfnk.1

- Merged upstream 3.0.0 and re-applied the local rules. The banned words and workflow steps 5 to 7 are unchanged. The compressed "X, not Y" form and conversation-derived Y now sit in §1, and "and that is the lesson" joins the §13 watch list. Local patterns are renumbered into group F: 36→26, 37→27, 38→28, 39→29, 40→30, 41→31, 42→32, 43→33. 33 patterns total.

## 2.11.2+sbfnk.2

- Local fork additions: third-person self-reference (§38), document-wide name drift (§39), negation where a description exists (§40), "so" chained as a connective (§41), trailing coordination that says nothing about its tail (§42), and "and" where the relation is adversative (§43). 43 patterns total.

## 2.11.2+sbfnk.1

- Local fork additions on top of upstream 2.11.2: banned words (§ "Never use these words", now four including carry/carries), the "X, not Y" compressed form and conversation-derived Y in §35, concepts acting like people (§36), and pseudo-clefts (§37). 37 patterns total.
