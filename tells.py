#!/usr/bin/env python3
"""Grep for the mechanically detectable tells in SKILL.md.

Masks fenced code, inline code, link targets and bare URLs before matching, so
prose is checked and code is left alone. Reports two tiers:

  ACT    a tell from SKILL.md sections 1 to 5, the banned words, or a rule
         stated as absolute (dashes, curly quotes). One sighting justifies an edit.
  CHECK  a candidate needing a human judgement, and most are fine. Sections
         marked "weak alone" and the greps SKILL.md itself calls over-matching
         (triads, negations, trailing coordination) land here.

Section 32 is counted rather than listed, because one or two causal "so"s are
fine and the tell is the density.

Usage: tells.py FILE [FILE...]       [--act] to suppress the CHECK tier
"""

import re
import sys

# (tier, section, label, pattern)
PATTERNS = [
    # Banned words, "overrides everything else in this skill"
    ("ACT", "banned", "load-bearing", r"load-bearing"),
    ("ACT", "banned", "fire = trigger", r"\b(fires?|fired|firing)\b"),
    ("ACT", "banned", "anchor (metaphorical)", r"\banchor(s|ed|ing)?\b"),
    ("ACT", "banned", "carry = hold data", r"\bcarr(y|ies|ied|ying)\b"),

    # A. Staging instead of stating
    ("ACT", "1", "not just/only/merely X but Y", r"\bnot (just|only|merely|simply)\b[^.;]{0,60}\bbut\b"),
    ("ACT", "1", "not X but rather Y", r"\bnot\b[^.;]{0,40}\bbut rather\b|\bnot a\b[^.;]{0,30}\bbut a\b"),
    ("ACT", "1", "it's not X, it's Y", r"\b(it|this|that)('s| is) not\b[^.;]{0,50}[,;] (it|this|that)('s| is)\b"),
    ("ACT", "1", "X, not Y", r", not (a |an |the )?\w+"),
    ("ACT", "1", "X, rather than Y", r"\brather than\b"),
    ("ACT", "1", "instead of Y", r"\binstead of\b"),
    ("CHECK", "1", "split contrast", r"\b(does not|doesn't|did not) mean\b[^.]*\.\s*(It|This|That) means\b"),
    ("ACT", "2", "dramatic closer", r"\b(read that again|let that sink in|that is the real win|that distinction matters|that's the real win)\b"),
    ("ACT", "3", "sounds-deep saying", r"\b(the real question is|at its core|what really matters|the deeper issue|the heart of the matter)\b"),
    ("ACT", "3", "the X of Y frame", r"\bthe (language|currency|architecture|grammar) of\b"),
    ("ACT", "4", "staged run-up", r"\b(let's (dive|explore|break this down)|here's what you need to know|without further ado|here's the thing|the thing is,|let's be honest|real talk)\b"),
    ("ACT", "4", "standalone opener", r"(?:^|\. )(Honestly|Look|Basically)[,?:]"),
    ("ACT", "5", "arguing with no one", r"\b(i'm not saying|to be clear,|don't get me wrong|this is not to say|some might say|a tempting approach|one might be tempted|an obvious approach would be|you might think|it would be easy to just)\b"),

    # B. Rhythm by rule
    ("ACT", "8", "em/en dash", r"[—–]"),
    ("ACT", "8", "double hyphen as dash", r"\s--\s"),
    ("ACT", "21", "curly quote", r"[“”‘’]"),
    ("CHECK", "6", "possible triad", r"\b\w+, \w+,? and \w+\b"),
    ("CHECK", "9", "stacked qualifier", r"\b(to be fair|it's also possible|could potentially|might arguably|in some cases it may)\b"),
    ("CHECK", "10", "hyphen pair after noun", r"\b(is|are|was|were|seems|feels) (high-quality|well-known|well-documented|long-term|real-time|client-facing)\b"),

    # C. Inflation and borrowed authority
    ("CHECK", "12", "AI vocabulary", r"\b(additionally|align with|bolstered|crucial|deep dive|delve|enduring|enhance|garner|interplay|intricate|intricacies|landscape|meticulous(ly)?|pivotal|quietly|showcase|tapestry|testament|underscores?|underscored|valuable|vibrant)\b"),
    ("ACT", "13", "inflated significance", r"\b(stands as a testament|a (pivotal|crucial) moment|plays a (key|crucial|vital) role|marking a|underscores its importance|reflects a broader|enduring legacy|lasting legacy|setting the stage for|evolving landscape|indelible mark|future looks bright|exciting times|step in the right direction|despite these challenges)\b"),
    ("CHECK", "14", "vague connection", r"\b(associated with|in association with|in connection with|linked to|tied to)\b"),
    ("CHECK", "15", "shallow -ing rider", r", (highlighting|underscoring|emphasizing|ensuring|reflecting|symbolizing|contributing to|cultivating|fostering|encompassing|showcasing)\b"),
    ## "fostering" is the one rider upstream's de-duplication left uncovered bare:
    ## §12 watched it without a comma before 3.1.0 moved it here. The lookbehind
    ## keeps one instance from being reported twice by the comma form above.
    ("CHECK", "15", "shallow -ing rider", r"(?<!, )\bfostering\b"),
    ("ACT", "16", "sales language", r"\b(nestled|in the heart of|breathtaking|must-visit|renowned|diverse array|groundbreaking|exemplifies|commitment to)\b"),
    ("ACT", "17", "borrowed authority", r"\b(experts (argue|believe|say)|observers have cited|industry reports|some critics|several publications|active social media presence)\b"),
    ("CHECK", "18", "avoiding is/are/has", r"\b(serves|stands|functions|operates) as\b|\brepresents a\b|\bfeatures (a|four|three|two|over)\b"),
    ## "boasts" is sales language whatever rule lists it, so it stays at ACT.
    ("ACT", "18", "avoiding is/are/has", r"\bboasts\b"),

    # D. Formatting by rule
    ("ACT", "19", "bold label list item", r"^\s*[-*+]\s+\*\*[^*]+:?\*\*:?"),
    ("ACT", "20", "emoji/arrow decoration", "[\U0001F300-\U0001FAFF→✅❌⚠]"),

    # E. Leftovers
    ("ACT", "22", "chatbot residue", r"\b(i hope this helps|of course!|certainly!|great question|you're absolutely right|would you like|want me to|should i continue|let me know if)\b"),
    ("ACT", "23", "knowledge-limit disclaimer", r"\b(as of my|up to my last training|while specific details are|based on available information|not publicly available|not widely documented|in the (provided|available) sources|maintains a low profile|it is believed that)\b"),
    ("CHECK", "2", "names what the example showed", r"\b(this shows the importance of|the message was clear|it was a lesson in)\b"),
    # §25 watches text that describes its own sourcing, assembly or layout
    ("CHECK", "25", "text describing itself", r"\b(was added to replace|generated from|compiled from|the table below compares|this section is organi[sz]ed by)\b"),

    # G. Local additions
    ("CHECK", "27", "abstract subject + intentional verb", r"\b(this|that|it|the \w+) (creates|designs|builds|argues|demonstrates|addresses|tackles|constructs)\b"),
    ("ACT", "28", "pseudo-cleft", r"\b(what|where|how|why) [^.;]{0,40}\b(is|are|was|were) (that|to|by|because|a|an|the)\b"),
    ("ACT", "28", "the reason X is that", r"\bthe reason\b[^.;]{0,40}\bis (that|because)\b"),
    ("ACT", "28", "is why / that is why", r"\bis why\b"),
    ("CHECK", "29", "third-person self-reference", r"\bthe (author|applicant|lead investigator|principal investigator)\b"),
    # section 32 is handled by connectives(), which classifies and counts every
    # "so" rather than matching one shape
    ("CHECK", "33", "trailing coordination", r", and (the|what) [^.;:!?]+[.!?]?$"),
    ("CHECK", "34", "and where adversative", r"\b(rises|raises|works|fits|improves|increases) [^.;]{0,40}, and (the|it) \w+ (does not|doesn't|fails)\b"),
    ("CHECK", "31", "negation for effect", r"\b(never|nobody|nothing|no one|none)\b"),
    ("ACT", "37", "X and not-X as a label", r"\b(can|could|will|would|does|do|did|is|are|has|have|should|must) and (cannot|can not|can't|could not|couldn't|will not|won't|would not|wouldn't|does not|doesn't|do not|don't|did not|didn't|is not|isn't|are not|aren't|has not|hasn't|have not|haven't|should not|shouldn't|must not|mustn't)\b"),
    ("ACT", "37", "range with no point in it", r"\b(whether or not|for better or worse|to a greater or lesser extent)\b"),
    # "'s" after a lowercase word, skipping the contractions of "is" and "us"
    ("CHECK", "38", "possessive 's on a thing", r"\b(?!(?:it|that|there|here|what|who|where|how|let|he|she|one|everyone|nobody|someone|this|which)'s\b)[a-z]+'s\b"),
]

PARA_SECTIONS = ("1", "33", "34")

FENCE = re.compile(r"^\s*(```|~~~)")
INLINE_CODE = re.compile(r"`[^`]*`")
LINK_TARGET = re.compile(r"\]\([^)]*\)")
URL = re.compile(r"https?://\S+")
HEADING = re.compile(r"^(#+)\s+(.*)$")

# Uses of "so" that are not the therefore-sense of section 32.
SO_FIXED = re.compile(r"so-called|so\s+far\b|so\s+long\s+as\b|and\s+so\s+on\b", re.IGNORECASE)
# "so large that", "so much as", "so many that": an intensifier, not a connective
SO_INTENSIFIER = re.compile(r"so\s+(?:\w+\s+){0,2}?(?:that|as)\b", re.IGNORECASE)
SO_PURPOSE_INF = re.compile(r"so\s+as\s+to\b", re.IGNORECASE)
# preceded by one of these, "so" is part of a fixed phrase
SO_PRECEDED = re.compile(r"\b(or|if|even|just)\s+so\s*$", re.IGNORECASE)

# "so + clause with a modal" usually reads as purpose even without "that"
SO_MODAL = re.compile(
    r"so\s+(?:the|it|they|this|we|you|a|an)?\s*\w*\s*\b"
    r"(can|cannot|could|will|would|may|might|never)\b",
    re.IGNORECASE,
)

# other ways the same causal step gets spelled
SUBSTITUTES = re.compile(
    r"\b(therefore|thus|hence|consequently|accordingly|as such|which is why|that is why|"
    r"for this reason|as a result)\b|(?<=,)\s+since\s+(?=\w)",
    re.IGNORECASE,
)

# a second full clause hung on the first with ", and" or ", which"; the word
# after "and" must be able to start a clause, which skips most list items
JOIN_AND = re.compile(
    r",\s+and\s+(?:then\s+)?(?:the|a|an|it|its|this|that|these|those|they|we|"
    r"you|he|she|each|every|both|one|[A-Z][\w.]*)\s+\w+"
)
JOIN_WHICH = re.compile(r",\s+which\s+(?!is\s+why\b)\w+", re.IGNORECASE)
SENTENCE_END = re.compile(r"(?<=[.!?;])[ \t]+|(?=\n)|(?<=\n)")

WORD = re.compile(r"[A-Za-z][A-Za-z'-]*")
WORDS_PER_PAGE = 500


def mask(lines):
    """Blank fenced blocks, inline code, link targets and URLs, preserving offsets."""
    out, in_fence = [], False
    for line in lines:
        if FENCE.match(line):
            in_fence = not in_fence
            out.append("")
            continue
        if in_fence:
            out.append("")
            continue
        for pat in (INLINE_CODE, LINK_TARGET, URL):
            line = pat.sub(lambda m: " " * len(m.group(0)), line)
        out.append(line)
    return out


def title_case_heading(text):
    """Two or more capitalised non-initial words that are not acronyms or code."""
    caps = [w for w in text.split()[1:] if re.match(r"^[A-Z][a-z]+$", w)]
    return len(caps) >= 2


def flatten(masked):
    """Join prose into unwrapped text, with a character-to-line-number map.

    Hard wrapping hides any pattern that spans a line break, which SKILL.md
    warns about for section 33 and which also splits "so ... can" clauses.
    """
    chars, lineof = [], []
    for n, line in enumerate(masked, 1):
        stripped = line.strip()
        if not stripped:
            if chars and chars[-1] != "\n":
                chars.append("\n")
                lineof.append(n)
            continue
        if chars and chars[-1] != "\n":
            chars.append(" ")
            lineof.append(n)
        chars.extend(stripped)
        lineof.extend([n] * len(stripped))
    return "".join(chars), lineof


def is_list_tail(sentence, i):
    """True when the ", and" at i closes a list ("a, b, and the c").

    A list has an earlier comma whose item, up to this one, is a few words.
    """
    before = sentence[:i]
    if "," not in before:
        return False
    return len(WORD.findall(before[before.rfind(",") + 1:])) <= 4


def connectives(path, masked):
    """Section 32: classify and count every causal connective in the prose."""
    text, lineof = flatten(masked)
    words = len(WORD.findall(text))
    pages = max(words / WORDS_PER_PAGE, 1e-9)

    def where(i):
        return lineof[i] if i < len(lineof) else len(lineof)

    def context(i, before=30, after=50):
        return text[max(0, i - before):i + after].replace("\n", " ").strip()

    therefore, purpose = [], []
    for m in re.finditer(r"\bso\b", text, re.IGNORECASE):
        i = m.start()
        tail = text[i:]
        if SO_FIXED.match(tail) or SO_PURPOSE_INF.match(tail):
            continue
        if SO_PRECEDED.search(text[max(0, i - 12):m.end()]):
            continue
        if SO_INTENSIFIER.match(tail):
            continue
        (purpose if SO_MODAL.match(tail) else therefore).append((where(i), context(i)))

    subs = [
        (where(m.start()), m.group(0).strip(), context(m.start(), 30, 40))
        for m in re.finditer(SUBSTITUTES, text)
    ]

    # clause joins, sentence by sentence; a run of joined sentences is the tell
    joined, run, runs = [], [], []
    pos = 0
    therefore_at = {c for _, c in therefore}
    for sentence in SENTENCE_END.split(text):
        start = text.find(sentence, pos)
        pos = start + len(sentence)
        if not sentence.strip():
            # a paragraph break ends any run of chained sentences
            if len(run) >= 2:
                runs.append(run)
            run = []
            continue
        found = [
            m for pat in (JOIN_AND, JOIN_WHICH) for m in pat.finditer(sentence)
            if not is_list_tail(sentence, m.start())
        ]
        so_here = any(c and c in sentence for c in therefore_at)
        for m in found:
            joined.append((where(start + m.start()), context(start + m.start(), 40, 40)))
        if found or so_here:
            run.append(where(start))
        else:
            if len(run) >= 2:
                runs.append(run)
            run = []
    if len(run) >= 2:
        runs.append(run)

    for n, ctx in therefore:
        print(f"{path}:{n}: [ACT §32] so = therefore: ...{ctx}...")
    for r in runs:
        print(
            f"{path}:{r[0]}: [ACT §32] {len(r)} chained sentences in a row "
            f"(lines {r[0]}-{r[-1]}): end the first clause instead of joining"
        )
    for n, ctx in joined:
        print(f"{path}:{n}: [CHECK §32] clause joined with ', and'/', which': ...{ctx}...")
    for n, ctx in purpose:
        print(f"{path}:{n}: [CHECK §32] so + modal, purpose or therefore?: ...{ctx}...")
    for n, word, ctx in subs:
        print(f"{path}:{n}: [CHECK §32] causal connective '{word}': ...{ctx}...")

    allowance = max(1, round(pages))
    print(
        f"{path}: §32 density: {len(therefore)} therefore-sense 'so' in "
        f"{words} words ({round(pages, 1)} pages, allowance ~{allowance}); "
        f"{len(purpose)} ambiguous, {len(subs)} substitute(s), "
        f"{len(joined)} ', and'/', which' join(s)"
    )
    return max(0, len(therefore) - allowance) + len(runs)


def paragraphs(masked):
    paras, start, buf = [], None, []
    for n, line in enumerate(masked, 1):
        if line.strip():
            if start is None:
                start = n
            buf.append(line.strip())
        elif buf:
            paras.append((start, " ".join(buf)))
            start, buf = None, []
    if buf:
        paras.append((start, " ".join(buf)))
    return paras


def check(path, act_only=False):
    with open(path, encoding="utf-8") as fh:
        raw = fh.read().splitlines()
    masked = mask(raw)
    hits = []

    def add(n, tier, sec, label, match):
        entry = (n, tier, sec, label, match)
        if match.strip() and entry not in hits:
            hits.append(entry)

    for n, line in enumerate(masked, 1):
        if not line.strip():
            continue
        for tier, sec, label, pat in PATTERNS:
            if act_only and tier != "ACT":
                continue
            for m in re.finditer(pat, line, re.IGNORECASE):
                add(n, tier, sec, label, m.group(0).strip())

    # headings are structural, so they come from the unmasked text
    if not act_only:
        for n, line in enumerate(raw, 1):
            h = HEADING.match(line)
            if h and title_case_heading(h.group(2)):
                add(n, "CHECK", "20", "title case heading", h.group(2))

    # paragraph-scale patterns, on whitespace-normalised prose
    for start, text in paragraphs(masked):
        for tier, sec, label, pat in PATTERNS:
            if sec not in PARA_SECTIONS or (act_only and tier != "ACT"):
                continue
            for m in re.finditer(pat, text, re.IGNORECASE):
                add(start, tier, sec, label + " (para)", m.group(0).strip())

    hits.sort(key=lambda h: (h[1] != "ACT", h[0]))
    for n, tier, sec, label, match in hits:
        print(f"{path}:{n}: [{tier} §{sec}] {label}: {match}")
    excess = connectives(path, masked)
    return sum(1 for h in hits if h[1] == "ACT") + excess


if __name__ == "__main__":
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    if not args:
        sys.exit(__doc__)
    total = sum(check(p, "--act" in sys.argv) for p in args)
    print(f"\n{total} ACT-tier hit(s)")
    sys.exit(1 if total else 0)
