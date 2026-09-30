#!/usr/bin/env python3
"""Every upstream pattern is present and unchanged; the fork's own follow at the end.

Run from the repo with a ref for upstream, e.g.  check_upstream.py upstream/main
"""
import re, subprocess, sys

def skill(ref=None):
    if ref is None: return open("SKILL.md").read()
    return subprocess.run(["git","show",f"{ref}:SKILL.md"],capture_output=True,text=True).stdout

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

print("\n== upstream bodies unchanged (a difference is a deliberate fork edit or a merge slip)")
for n in sorted(up):
    if n in here and here[n][1] != up[n][1]:
        print(f"  DIFFERS  §{n} {up[n][0]}")

print("\n== the fork's own patterns sit after upstream's, contiguous")
mine = sorted(n for n in here if n > n_up)
if mine != list(range(n_up + 1, max(here) + 1)):
    print(f"  NOT CONTIGUOUS: {mine}"); bad += 1
else:
    print(f"  §{mine[0]}-§{mine[-1]} ({len(mine)} local rules) follow upstream's 1-{n_up}")

print("\n== the fork's patterns match what main had, allowing for the shift")
main = sections(skill("main"))
n_up_before = max(n for n in main if n <= 26 and main[n][0] == up.get(n, ("",))[0]) if main else 0
offset = mine[0] - min(n for n in main if n > 25)
for n in mine:
    src = n - offset
    if src not in main:
        print(f"  NEW      §{n} {here[n][0]} (not on main)")
    elif main[src][0] != here[n][0]:
        print(f"  MOVED?   §{n} {here[n][0]!r} vs main §{src} {main[src][0]!r}"); bad += 1
    elif re.sub(r"§\d+","§",main[src][1]) != re.sub(r"§\d+","§",here[n][1]):
        print(f"  CHANGED  §{n} {here[n][0]} (body differs from main §{src} beyond renumbering)")
print(f"\n  hard failures: {bad}")
sys.exit(1 if bad else 0)
