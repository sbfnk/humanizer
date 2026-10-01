#!/usr/bin/env python3
"""Every upstream pattern is present and unchanged; the fork's own follow at the end.

Run from the repo with a ref for upstream, e.g.  check_upstream.py upstream/main
"""
import re, subprocess, sys

def skill(ref=None):
    if ref is None: return open("SKILL.md").read()
    return subprocess.run(["git","show",f"{ref}:SKILL.md"],capture_output=True,text=True).stdout

def at_ref(ref, path):
    done = subprocess.run(["git", "show", f"{ref}:{path}"], capture_output=True, text=True)
    return done.stdout if done.returncode == 0 else None


# Upstream bodies this fork deliberately extends. A third difference is a slip.
FORK_EDITS = {
    1: "the fork adds the conversation-derived 'X, not Y' material",
    13: "the fork extends the watch list with 'and that is the lesson'",
}


def sections(text):
    """number -> (title, body). Body stops at the next ### OR the next ## group
    heading, so a group intro is never counted as part of the rule above it."""
    out, cur, buf = {}, None, []
    for line in text.split("\n"):
        m = re.match(r"^### ([0-9]+)\. (.*)$", line)
        if m:
            if cur: out[cur[0]] = (cur[1], "\n".join(buf).strip())
            cur, buf = (int(m.group(1)), m.group(2)), []
        elif re.match(r"^## ", line) and cur:
            out[cur[0]] = (cur[1], "\n".join(buf).strip()); cur, buf = None, []
        elif cur: buf.append(line)
    if cur: out[cur[0]] = (cur[1], "\n".join(buf).strip())
    return out

up_ref = sys.argv[1] if len(sys.argv) > 1 else "upstream/main"
up, here = sections(skill(up_ref)), sections(skill())
n_up = max(up)

print(f"upstream {up_ref}: {len(up)} patterns (1-{n_up})   here: {len(here)} patterns (1-{max(here)})")
bad = 0

print("\n== every upstream pattern present, in its own slot, with its own title")
for n in sorted(up):
    if n not in here:
        print(f"  MISSING  §{n} {up[n][0]}"); bad += 1
    elif here[n][0] != up[n][0]:
        print(f"  RETITLED §{n} upstream {up[n][0]!r} -> here {here[n][0]!r}"); bad += 1

print("\n== upstream bodies unchanged, bar the fork's two documented edits")
for n in sorted(up):
    if n in here and here[n][1] != up[n][1]:
        if n in FORK_EDITS:
            print(f"  EDITED   §{n} {up[n][0]} -- {FORK_EDITS[n]}")
        else:
            print(f"  DIFFERS  §{n} {up[n][0]} (not a documented fork edit)")
            bad += 1

print("\n== the fork's own patterns sit after upstream's, contiguous")
mine = sorted(n for n in here if n > n_up)
if mine != list(range(n_up + 1, max(here) + 1)):
    print(f"  NOT CONTIGUOUS: {mine}"); bad += 1
else:
    print(f"  §{mine[0]}-§{mine[-1]} ({len(mine)} local rules) follow upstream's 1-{n_up}")

print("\n== the fork's patterns match what main had, allowing for the shift")
main = sections(skill("main")) if at_ref("main", "SKILL.md") else {}
if not main:
    print("  SKIPPED  no local main branch to compare against")
else:
    by_title = {title: n for n, (title, _body) in main.items()}
    for n in mine:
        title, body = here[n]
        if title not in by_title:
            print(f"  NEW      §{n} {title} (no rule of this name on main)")
            continue
        src = by_title[title]
        if re.sub(r"§\d+", "§", main[src][1]) != re.sub(r"§\d+", "§", body):
            print(f"  CHANGED  §{n} {title} (body differs from main §{src} beyond renumbering)")
            bad += 1

print(f"\n  hard failures: {bad}")
sys.exit(1 if bad else 0)
