#!/usr/bin/env python3
"""Check tells.py against SKILL.md and against the published version.

Nothing else validates tells.py: it is local to this fork, and the package
validator reads only SKILL.md, the README and the manifests.

    python3 scripts/check-tells.py [--against REF]

REF defaults to origin/main, the published state.
"""

import argparse
import importlib.util
import re
import subprocess
import sys

# Watch words this fork has deliberately stopped covering, each with its reason.
# A deliberate drop belongs here; an accidental one fails the check.
# Detectors deliberately rewritten since the reference, keyed on the exact row
# they replace so a waiver covers that one row and nothing else. Each entry is
# (tier, key, label, regex) -> why. Fill this in when a rewrite is intended; an
# unintended one fails.
WAIVED_DETECTORS = {
    # upstream 3.1.0 rewrote §2's watch list; the replacement adds the example-closer phrases
    ('ACT', '2', 'dramatic closer',
     "\\b(read that again|let that sink in|that is the real win|that's the real win)\\b"): "upstream 3.1.0 rewrote §2's watch list; the replacement adds the example-closer phrases",
    # upstream 3.1.0 narrowed §10 to six compounds, dropping data-driven and end-to-end
    ('CHECK', '10', 'hyphen pair after noun',
     '\\b(is|are|was|were|seems|feels) (cross-functional|high-quality|data-driven|client-facing|real-time|long-term|end-to-end|well-known)\\b'): 'upstream 3.1.0 narrowed §10 to six compounds, dropping data-driven and end-to-end',
    # upstream 3.1.0 moved fostering to §15 and dropped it here
    ('CHECK', '12', 'AI vocabulary',
     '\\b(additionally|align with|bolstered|crucial|deep dive|delve|enduring|enhance|fostering|garner|interplay|intricate|intricacies|landscape|meticulous(ly)?|pivotal|quietly|showcase|tapestry|testament|underscores?|underscored|valuable|vibrant)\\b'): 'upstream 3.1.0 moved fostering to §15 and dropped it here',
    # upstream 3.1.0 moved boasts to §18 and dropped it here
    ('ACT', '16', 'sales language',
     '\\b(boasts|nestled|in the heart of|breathtaking|must-visit|renowned|diverse array|groundbreaking|exemplifies|commitment to)\\b'): 'upstream 3.1.0 moved boasts to §18 and dropped it here',
}

# Phrases that must stay covered at the stated tier, whatever the table looks
# like. The gate below compares against a reference, so it cannot protect a
# detector added since that reference, and a waived rewrite is only a human
# assertion that coverage moved. These assert it directly. Add a row whenever a
# fix restores coverage, so the fix cannot be undone quietly.
FIXTURES = [
    ("The gallery boasts three thousand square feet.", "ACT", "boasts"),
    ("A plan fostering closer ties.", "CHECK", "fostering"),
    ("Gallery 825 serves as the exhibition space.", "CHECK", "serves as"),
    ("What matters is the result of the run.", "ACT", "pseudo-cleft"),
    ("The reason it fails is that N is wrong.", "ACT", "the reason X is that"),
    ("It is not only slow but wrong.", "ACT", "not just/only/merely X but Y"),
    ("The team is data-driven and cross-functional.", None, "§10 dropped these upstream"),
    ("The vaccine's effectiveness was high.", "CHECK", "possessive 's on a thing"),
]

TIER_RANK = {"CHECK": 0, "ACT": 1}


def load_module(source, name):
    spec = importlib.util.spec_from_loader(name, loader=None)
    module = importlib.util.module_from_spec(spec)
    exec(compile(source, name, "exec"), module.__dict__)
    return module


def at_ref(ref, path):
    done = subprocess.run(
        ["git", "show", f"{ref}:{path}"], capture_output=True, text=True
    )
    return done.stdout if done.returncode == 0 else None


def ref_exists(ref):
    return subprocess.run(
        ["git", "rev-parse", "--verify", "--quiet", ref], capture_output=True
    ).returncode == 0


def sections(skill):
    return {
        int(m.group(1)): m.group(2).strip()
        for m in re.finditer(r"^### ([0-9]+)\. (.*)$", skill, re.M)
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--against", default="origin/main", metavar="REF")
    args = ap.parse_args()

    here = load_module(open("tells.py").read(), "tells_here")
    skill = sections(open("SKILL.md").read())
    failures = []

    print("== every pattern key names a real SKILL.md section")
    keys = {k for _t, k, _l, _r in here.PATTERNS if k.isdigit()}
    keys |= {k for k in here.PARA_SECTIONS if k.isdigit()}
    for key in sorted(keys, key=int):
        if int(key) not in skill:
            failures.append(f"§{key} is keyed in tells.py but SKILL.md has no such rule")
            print(f"  MISSING  §{key} keyed in tells.py, absent from SKILL.md")
    print(f"  {len(keys)} of {len(skill)} rules have a detector")

    print("\n== phrases that must stay covered, whatever the table looks like")
    for text, want, what in FIXTURES:
        tiers = [t for t, _k, _l, rx in here.PATTERNS if re.search(rx, text, re.I)]
        got = max(tiers, key=lambda t: TIER_RANK[t]) if tiers else None
        if want is None:
            print(f"  {'not covered' if got is None else 'COVERED ' + got:14} {what}"
                  + ("" if got is None else "  <- expected no coverage"))
        elif got is None or TIER_RANK[got] < TIER_RANK[want]:
            failures.append(f"{what!r} should be covered at {want}, got {got}")
            print(f"  FAILED   {what}: expected {want}, got {got or 'nothing'}")
        else:
            print(f"  {got:<8} {what}")

    print("\n== every regex compiles")
    for _tier, key, label, regex in here.PATTERNS:
        try:
            re.compile(regex)
        except re.error as exc:
            failures.append(f"§{key} {label}: {exc}")
            print(f"  BROKEN   §{key} {label}: {exc}")
    print(f"  {len(here.PATTERNS)} patterns compile")

    print(f"\n== every detector still present since {args.against}")
    if not ref_exists(args.against):
        print(f"  FAILED   {args.against} does not resolve, so nothing was compared")
        failures.append(f"{args.against} does not resolve")
    else:
        ref_tells = at_ref(args.against, "tells.py")
        ref_skill = at_ref(args.against, "SKILL.md")
        if ref_tells is None or ref_skill is None:
            print(f"  FAILED   {args.against} lacks tells.py or SKILL.md, so nothing was compared")
            failures.append(f"{args.against} lacks the files needed for comparison")
        else:
            there = load_module(ref_tells, "tells_ref")
            old_titles = sections(ref_skill)
            here_by_title = {t: n for n, t in skill.items()}
            # Compare detector by detector, by exact regex text. No attempt to
            # work out what a regex matches: two earlier versions of this script
            # tried, and both passed while coverage was being deleted. A rewrite
            # of a watch list is a deliberate act, so it goes in WAIVED_DETECTORS
            # with its reason rather than being inferred.
            present = {(t, rx) for t, _k, _l, rx in here.PATTERNS}
            weaker = {rx for t, _k, _l, rx in here.PATTERNS if t == "CHECK"}
            for tier, key, label, regex in there.PATTERNS:
                if (tier, regex) in present:
                    continue
                title = old_titles.get(int(key)) if key.isdigit() else None
                now = str(here_by_title.get(title, key)) if title else key
                if regex in weaker and tier == "ACT":
                    failures.append(f"§{now} {label} dropped from ACT to CHECK")
                    print(f"  DEMOTED  §{now} {label}: ACT -> CHECK, so --act changes verdict")
                elif (tier, key, label, regex) in WAIVED_DETECTORS:
                    print(f"  WAIVED   §{now} {label}: {WAIVED_DETECTORS[(tier, key, label, regex)]}")
                else:
                    failures.append(f"§{now} {label}: this detector is gone or rewritten")
                    print(f"  GONE     §{now} {label}: detector removed or rewritten, unwaived")
                    print(f"             was: {regex[:88]}")
            kept = sum(1 for t, _k, _l, rx in there.PATTERNS if (t, rx) in present)
            print(f"  {kept} of {len(there.PATTERNS)} detectors carried over byte-for-byte")
            print(f"  {len(WAIVED_DETECTORS)} deliberate rewrite(s) waived")

    print(f"\n  failures: {len(failures)}")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
