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
WAIVED_WORDS = {
    "data-driven": "upstream 3.1.0 narrowed §10 to six compounds and dropped this",
    "end-to-end": "upstream 3.1.0 narrowed §10 to six compounds and dropped this",
    "cross-functional": "§10 exempts dictionary compounds by name",
}

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


def expand(regex):
    """Concrete strings `regex` can match, or None where it cannot be enumerated.

    None matters as much as the strings: a pattern that cannot be enumerated is a
    blind spot in the word-level comparison, and the caller reports how many there
    are rather than letting them pass unnoticed.
    """
    if re.search(r"\\[sdwSDW]|[+*.]|\(\?[=!<]", regex):
        return None  # quantifiers, classes and lookarounds are not enumerable here
    out = [""]
    i = 0
    while i < len(regex):
        ch = regex[i]
        if regex.startswith(r"\b", i):
            i += 2
            continue
        if ch == "(":
            depth, j = 1, i + 1
            while j < len(regex) and depth:
                depth += (regex[j] == "(") - (regex[j] == ")")
                j += 1
            inner = regex[i + 1 : j - 1]
            if inner.startswith("?:"):
                inner = inner[2:]
            alts = []
            for alt in split_top(inner):
                sub = expand(alt)
                if sub is None:
                    return None
                alts.extend(sub)
            optional = j < len(regex) and regex[j] == "?"
            if optional:
                alts.append("")
                j += 1
            out = [a + b for a in out for b in alts]
            i = j
            continue
        if ch == "[":
            j = regex.index("]", i)
            chars = list(regex[i + 1 : j])
            j += 1
            if j < len(regex) and regex[j] == "?":
                chars.append("")
                j += 1
            out = [a + c for a in out for c in chars]
            i = j
            continue
        if ch == "\\":
            nxt = regex[i + 1] if i + 1 < len(regex) else ""
            out = [a + nxt for a in out]
            i += 2
            continue
        if i + 1 < len(regex) and regex[i + 1] == "?":
            out = [a + ch for a in out] + out
            i += 2
            continue
        out = [a + ch for a in out]
        i += 1
    return out


def split_top(regex):
    """Split on | at depth zero."""
    parts, depth, cur = [], 0, ""
    for ch in regex:
        depth += (ch == "(") - (ch == ")")
        if ch == "|" and not depth:
            parts.append(cur)
            cur = ""
        else:
            cur += ch
    parts.append(cur)
    return parts


def words_of(patterns):
    """(word -> strongest tier matching it, number of unenumerable patterns)."""
    cover, blind = {}, 0
    for tier, _key, _label, regex in patterns:
        strings = expand(regex)
        if strings is None:
            blind += 1
            continue
        for s in strings:
            s = s.strip()
            # Keep only strings the regex really matches, so a flawed expansion
            # cannot invent a word and report it lost later.
            if s and re.search(regex, s, re.I):
                if TIER_RANK[tier] > TIER_RANK.get(cover.get(s, "CHECK"), -1) or s not in cover:
                    cover[s] = tier
    return cover, blind


def strongest_match(patterns, text):
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
    print(f"  {len(keys)} of {len(skill)} rules have a detector")

    print("\n== every regex compiles")
    for _tier, key, label, regex in here.PATTERNS:
        try:
            re.compile(regex)
        except re.error as exc:
            failures.append(f"§{key} {label}: {exc}")
            print(f"  BROKEN   §{key} {label}: {exc}")
    print(f"  {len(here.PATTERNS)} patterns compile")

    print(f"\n== no detector removed or demoted since {args.against}")
    if not ref_exists(args.against):
        print(f"  FAILED   {args.against} does not resolve, so nothing was compared")
        failures.append(f"{args.against} does not resolve")
    else:
        ref_tells = at_ref(args.against, "tells.py")
        ref_skill = at_ref(args.against, "SKILL.md")
        if ref_tells is None:
            print(f"  SKIPPED  {args.against} has no tells.py yet")
        else:
            there = load_module(ref_tells, "tells_ref")
            # Rules are renumbered whenever upstream adds a pattern, so match them
            # by heading text. A regex compared by key alone would look removed.
            old_titles = sections(ref_skill) if ref_skill else {}
            here_by_title = {t: n for n, t in skill.items()}
            rules_here = {k for _t, k, _l, _r in here.PATTERNS}
            same = {(t, rx) for t, _k, _l, rx in here.PATTERNS}
            rewritten = set()
            for tier, key, label, regex in there.PATTERNS:
                title = old_titles.get(int(key)) if key.isdigit() else None
                now_key = str(here_by_title.get(title, key)) if title else key
                if (tier, regex) in same:
                    continue
                stronger = any(
                    rx == regex and TIER_RANK[t] > TIER_RANK[tier]
                    for t, _k, _l, rx in here.PATTERNS
                )
                if stronger:
                    continue
                demoted = any(rx == regex for _t, _k, _l, rx in here.PATTERNS)
                if demoted:
                    failures.append(f"§{now_key} {label} dropped below {tier}")
                    print(f"  DEMOTED  §{now_key} {label}: was {tier}, so --act changes verdict")
                elif now_key not in rules_here:
                    failures.append(f"§{now_key} {label} has no detector at all any more")
                    print(f"  REMOVED  §{now_key} {label}: the rule has no detector left")
                else:
                    rewritten.add((now_key, label))
            if rewritten:
                print(f"  {len(rewritten)} detector(s) rewritten; checking their words:")
            was, blind_was = words_of(there.PATTERNS)
            now, _blind_now = words_of(here.PATTERNS)
            lost, demoted_words = [], []
            for word, tier in sorted(was.items()):
                if any(w in word for w in WAIVED_WORDS):
                    continue
                got = strongest_match(here.PATTERNS, word)
                if got is None:
                    lost.append(word)
                elif TIER_RANK[got] < TIER_RANK[tier]:
                    demoted_words.append((word, tier, got))
            for word in lost:
                failures.append(f"{word!r} was covered and now matches nothing")
                print(f"  LOST     {word!r} matched at {args.against}, matches nothing here")
            for word, old, new in demoted_words:
                failures.append(f"{word!r} dropped from {old} to {new}")
                print(f"  DEMOTED  {word!r} {old} -> {new}")
            print(f"  {len(was)} watch words compared, {len(WAIVED_WORDS)} drops waived")
            print(f"  {blind_was} of {len(there.PATTERNS)} patterns are not word-enumerable;")
            print(f"    those are covered by the removal and demotion check above, not by word.")

    print(f"\n  failures: {len(failures)}")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
