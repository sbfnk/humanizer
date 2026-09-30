#!/usr/bin/env python3
"""Check tells.py against SKILL.md and against the published version.

Nothing else validates tells.py: it is local to this fork, and the package
validator reads only SKILL.md, the README and the manifests. Every defect four
rounds of review found in it was one of the three things checked here.

    python3 scripts/check-tells.py [--against REF]

REF defaults to origin/main, the published state. A REF without tells.py skips
the comparison rather than failing, so the check still works on a fresh fork.
"""

import argparse
import importlib.util
import re
import subprocess
import sys

# Watch-list words this fork has deliberately stopped covering. A drop belongs
# here, with its reason, or the comparison treats it as a regression -- which is
# the point: a deliberate drop is a visible edit and a silent one is a bug.
WAIVED = {
    "data-driven": "upstream 3.1.0 narrowed §10 to six compounds and dropped this",
    "end-to-end": "upstream 3.1.0 narrowed §10 to six compounds and dropped this",
    "cross-functional": "branch §10 exempts dictionary compounds by name",
}

TIER_RANK = {"CHECK": 0, "ACT": 1}


def load_module(source, name):
    """Import a tells.py given as source text."""
    spec = importlib.util.spec_from_loader(name, loader=None)
    module = importlib.util.module_from_spec(spec)
    exec(compile(source, name, "exec"), module.__dict__)
    return module


def at_ref(ref, path):
    done = subprocess.run(
        ["git", "show", f"{ref}:{path}"], capture_output=True, text=True
    )
    return done.stdout if done.returncode == 0 else None


def sections(skill):
    """number -> title, for every rule heading."""
    return {
        int(m.group(1)): m.group(2).strip()
        for m in re.finditer(r"^### ([0-9]+)\. (.*)$", skill, re.M)
    }


def literals(patterns):
    """Concrete strings the table can match, expanding alternation."""
    out = set()
    for _tier, _key, _label, regex in patterns:
        for branchpat in re.split(r"\|(?![^(]*\))", regex):
            bases = [branchpat]
            for group in re.findall(r"\(([^()]*)\)", branchpat):
                bases = [
                    b.replace(f"({group})", alt, 1)
                    for b in bases
                    for alt in group.split("|")
                ]
            for base in bases:
                text = re.sub(r"\\b|\\s\+|\?|\[|\]|sz", "", base)
                text = text.replace("\\", "").strip()
                if text and re.fullmatch(r"[A-Za-z0-9 ,'\-/]+", text):
                    out.add(text)
    return out


def strongest(patterns, text):
    """The strongest tier any pattern fires at on `text`, or None."""
    tiers = [t for t, _k, _l, rx in patterns if re.search(rx, text, re.I)]
    return max(tiers, key=lambda t: TIER_RANK[t]) if tiers else None


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
    covered = sorted((int(k) for k in keys))
    print(f"  {len(covered)} of {len(skill)} rules have a detector; all keys resolve"
          if not failures else "")

    print("\n== every regex compiles")
    for tier, key, label, regex in here.PATTERNS:
        try:
            re.compile(regex)
        except re.error as exc:
            failures.append(f"§{key} {label}: {exc}")
            print(f"  BROKEN   §{key} {label}: {exc}")
    print(f"  {len(here.PATTERNS)} patterns compile")

    print(f"\n== no coverage or tier regression against {args.against}")
    ref_tells = at_ref(args.against, "tells.py")
    ref_skill = at_ref(args.against, "SKILL.md")
    if ref_tells is None or ref_skill is None:
        print(f"  SKIPPED  {args.against} has no tells.py to compare against")
    else:
        there = load_module(ref_tells, "tells_ref")
        # Rules get renumbered when upstream adds a pattern, so map old numbers
        # to new ones by heading text and compare the words, not the numbers.
        old = sections(ref_skill)
        lost, demoted = [], []
        for word in sorted(literals(there.PATTERNS)):
            probe = f"The team {word} the result."
            was = strongest(there.PATTERNS, probe)
            if was is None or any(w in word for w in WAIVED):
                continue
            now = strongest(here.PATTERNS, probe)
            if now is None:
                lost.append(word)
            elif TIER_RANK[now] < TIER_RANK[was]:
                demoted.append((word, was, now))
        for word in lost:
            failures.append(f"{word!r} was covered at {args.against} and now matches nothing")
            print(f"  LOST     {word!r} matched at {args.against}, matches nothing here")
        for word, was, now in demoted:
            failures.append(f"{word!r} dropped from {was} to {now}")
            print(f"  DEMOTED  {word!r} {was} -> {now}, so --act no longer fails on it")
        if not lost and not demoted:
            n = len(literals(there.PATTERNS))
            print(f"  {n} watch words still covered at the same tier or stronger")
        if WAIVED:
            print(f"  {len(WAIVED)} deliberate drops waived:")
            for word, why in sorted(WAIVED.items()):
                print(f"    {word} -- {why}")

    print(f"\n  failures: {len(failures)}")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
