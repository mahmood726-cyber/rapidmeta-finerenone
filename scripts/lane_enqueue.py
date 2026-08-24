"""Generate the standing queue: many small independent lanes, not a few large ones.

ONE LANE PER MODULE, not one lane for a directory. A lane asked to sweep `ssot/` spends its
budget deciding where to look; a lane handed one module answers about that module. Four
Codex passes tonight produced no verdict at all while exploring, and the fifth answered in
7,791 tokens because the file was pasted into the prompt. Every lane here is built that way
where the subject fits: EVIDENCE INLINE, question narrow, answer bounded.

PACKET COMPLETENESS IS ASSERTED IN EVERY PROMPT. Six confident accusations of fabrication
tonight all traced to facts that were on the object and missing from the packet I built. So
each prompt states what it contains, states that nothing is withheld, and instructs the
reviewer to answer COULD NOT DETERMINE rather than call anything fabricated.
"""
from __future__ import annotations

import glob
import io
import json
import os
import sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LANES = os.path.join(REPO, "outputs", "lanes")
QUEUE = os.path.join(LANES, "queue")
PROMPTS = os.path.join(LANES, "prompts")

# RAW, because this string now quotes a regex. Written non-raw it produced an invalid
# escape `\.` -- which works by accident today and becomes a SyntaxError -- and
# lint_escape_hazards refused the commit for it, correctly.
RECURRING = r"""The defect shapes PROVEN to recur in this repository. Hunt these by name:

  - a check that CANNOT FAIL: no reachable non-zero exit, or a predicate that matches
    nothing in this corpus, so its zero means "the marker cannot fire" not "nothing is wrong"
  - a probe keyed to the STRING A FIX REMOVES, so success makes the control vacuous
  - an idempotency guard satisfied by its OWN comment or marker rather than by the work
  - an instrument reading a DIFFERENT COPY than the one being changed: worktree vs HEAD vs
    origin/main vs served; the module vs the call site; a name vs its binding
  - a SELECTOR KEYED TO A FORM THE CORPUS DOES NOT USE -- a regex, key name or field path
    that looks right and matches far less than intended
  - values compared AS TEXT where line endings differ (CRLF vs LF), so equal content reads
    as changed or changed content reads as equal
  - merged-cell and OFF-BY-ONE errors in any tabulation or count
  - ZERO CONFLATED WITH ABSENT: `or {}`, `or 0`, truthiness tests that drop a real 0.0
  - a NEGATION DROPPED: a pattern matching "not randomised" as "randomised", or a count
    read out of a sentence that denies it
  - a STATUS CODE REPORTING THE WRAPPER rather than the work: $? through a pipe, a
    subprocess return ignored, a gate that prints PASS without asserting anything
  - a VERIFIER THAT PRODUCES FALSE NEGATIVES -- a checker whose pattern cannot represent
    the thing it checks, so it REFUTES a true finding. `sys.exit(main())` matched against
    `sys\.exit\(([^)]*)\)` captures "main(" because the class stops at the first
    close-paren, and the check reports "not as claimed" against a claim that is correct.
    THIS IS THE WORST OF THE SHAPES HERE and it is the one nobody looks for: a false
    POSITIVE gets investigated and dies, a false NEGATIVE buries a real finding in silence.
    Same asymmetry as a wrapper reporting success. Look hardest at any pattern with nested
    delimiters, any regex over code, and any check whose CLEAN result nobody re-derived.
  - a CHECK THAT MATCHES THE TRIGGER IT IS TESTING -- circular, and it reports PASS on
    everything it fires on. A rule flagged pages carrying `chip-robme` but no RoB-ME
    IMPLEMENTATION; the check written to test it searched for `robme` case-insensitively,
    which matches `chip-robme` itself. Every flagged page looked like a false positive and
    the rule was one edit from being suppressed across 301 pages. Ask of any verifier: could
    this pattern match the very thing that CAUSED the flag?
  - a CHECK THAT ACCUSES CORRECT WORK. Not "can this check fail" -- whether it fails on
    work that is RIGHT. A rule required `const tau2 = (k>=2) ? ...` with parentheses the
    corpus never writes, so it accused 301 pages of a statistical-engine violation they did
    not have. AN AUDIT THAT CRIES WOLF AT 301 PAGES GETS SWITCHED OFF, AND IS THEN WORTH
    NOTHING ON THE DAY IT IS RIGHT. For any rule, find work that satisfies the PROPERTY and
    check the rule stays quiet.
"""

HEAD = """You are hunting for defects. Do not summarise what the code does, do not assess
quality, and do not tell me you agree with it. Assume there is a defect and find it.

PACKET COMPLETENESS, ASSERTED: the file below is pasted IN FULL, start to end, unabridged.
Nothing is withheld. If something you need is genuinely not here -- another module, a data
file, a caller -- say COULD NOT DETERMINE and NAME what is missing. Do NOT call anything
fabricated or absent from the record: an earlier blinded read of a partial packet returned
six confident accusations of fabrication, and all six were facts present in the record and
missing from the packet.

Answer in under 500 words. For each defect: the exact line, the exact input that
demonstrates it, and one sentence of consequence. If you find none of a shape, say so for
that shape in one line rather than inventing an objection -- a false positive costs as much
here as a miss.

"""


def write(name, engine, body):
    os.makedirs(QUEUE, exist_ok=True)
    os.makedirs(PROMPTS, exist_ok=True)
    pp = os.path.join(PROMPTS, name + ".txt")
    io.open(pp, "w", encoding="utf-8", newline="\n").write(body)
    json.dump({"engine": engine, "prompt": os.path.relpath(pp, REPO)},
              io.open(os.path.join(QUEUE, name + ".task"), "w", encoding="utf-8"))


def module_lanes(limit=None):
    """One lane per module, biggest-first, with the module inline."""
    files = []
    for pat in ("ssot/*.py", "scripts/*.py", "generate_living_ma_v13.py"):
        files += glob.glob(os.path.join(REPO, pat))
    files = [f for f in files
             if os.path.getsize(f) > 3000 and "__pycache__" not in f]
    files.sort(key=os.path.getsize, reverse=True)
    n = 0
    for f in files:
        src = io.open(f, encoding="utf-8", errors="replace").read()
        if len(src) > 240000:          # too large to inline; a lane would not finish
            continue
        rel = os.path.relpath(f, REPO).replace("\\", "/")
        name = "bug_" + rel.replace("/", "__").replace(".py", "")
        body = (HEAD + RECURRING +
                "\nTHE MODULE UNDER REVIEW: %s\n\n--- THE FILE, IN FULL ---\n%s" % (rel, src))
        write(name, "codex", body)
        n += 1
        if limit and n >= limit:
            break
    return n


def object_lanes(per=20):
    """One lane per twenty objects, for the classes established tonight."""
    objs = []
    for p in sorted(glob.glob(os.path.join(REPO, "ssot", "*", "*.json"))):
        t = os.path.basename(os.path.dirname(p))
        if os.path.basename(p) == t + ".json":
            objs.append(t)
    n = 0
    for i in range(0, len(objs), per):
        batch = objs[i:i + per]
        body = ("""You are auditing SSOT objects for FOUR specific defect classes, each of
which was found on a real object tonight. Use the repository directly: the objects are at
ssot/<topic>/<topic>.json. Answer about these %d topics ONLY:

%s

THE FOUR CLASSES, with the known positive for each:

  1  A STORED VALUE TRUNCATED MID-SENTENCE. Known positive: arni-hfref's
     grade.by_outcome.cvdeath_or_hfh_first.steps[risk_of_bias].reason was EXACTLY 400
     characters and ended "...In the same trial", a literal prefix of the 1,249-character
     table text. Look for any string value that stops mid-sentence, and for suspiciously
     round lengths (200, 300, 400, 500, 1000).
  2  A CAVEAT HELD AND NOT PROJECTED. A field whose value is a substantive statement to a
     reader, which no delivered page renders. Check the object's page via ssot/PAGE_MAP.json
     and say whether the text appears in it.
  3  A FIELD NAME THAT IS A FINDING. A key that is an English clause rather than a name.
     Say what it asserts and whether anything in the object acts on it.
  4  A PROVENANCE STRING THAT DOES NOT MATCH WHAT PRODUCED THE VALUE. A `source`,
     `read_utc`, `_source` or `basis` that names something the neighbouring value cannot
     have come from.

For each topic report only what you FIND, with the exact JSON path and the value quoted.
If a topic is clean on all four, one line: "<topic>: clean". Be exhaustive within these %d
and do not stray outside them. Do not modify any file. Under 700 words.
""" % (len(batch), "\n".join("  " + b for b in batch), len(batch)))
        write("obj_%03d" % i, "codex", body)
        n += 1
    return n


def gate_lanes(per=10):
    """The gates that structurally cannot cover v13 -- one lane per ten."""
    rep = os.path.join(REPO, "outputs", "codex_c4_v13_gate_coverage.md")
    if not os.path.isfile(rep):
        return 0
    txt = io.open(rep, encoding="utf-8", errors="replace").read()
    import re
    names = sorted(set(re.findall(r"`?(scripts/[\w/]+\.py)`?", txt)))
    n = 0
    for i in range(0, len(names), per):
        batch = names[i:i + per]
        body = ("""A prior audit classified this repository's refusal gates by whether they
could cover the output of `generate_living_ma_v13.py`, which writes HTML into sibling
`*_LivingMeta` directories and does NOT write ssot/**/*.json. Most were classed
STRUCTURALLY CANNOT.

For EACH of the %d gates below, read it in the repository and answer ONE question:

    What would it take to make this gate cover v13's HTML output -- or is that impossible,
    and why exactly?

Answer in one of exactly three forms per gate:
   EXTENDABLE  -- name the concrete change: the glob to add, the field to read from HTML
                  instead of JSON, the predicate that would still hold
   IMPOSSIBLE  -- name the property of v13 output that makes the gate's subject absent
                  from it. "It reads JSON" is not an answer; say what the gate is ABOUT and
                  why v13 pages cannot have it.
   ALREADY     -- it already reads files v13 writes; say which.

THE GATES:
%s

Be concrete and be short: two or three sentences each. Do not modify any file.
""" % (len(batch), "\n".join("  " + b for b in batch)))
        write("gate_%03d" % i, "codex", body)
        n += 1
    return n


def main():
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    lim = None
    for a in sys.argv[1:]:
        if a.startswith("--modules="):
            lim = int(a.split("=", 1)[1])
    m = module_lanes(lim)
    o = object_lanes()
    g = gate_lanes()
    q = len([f for f in os.listdir(QUEUE) if f.endswith(".task")])
    print("")
    print("   module bug-hunt lanes (one per module) %4d" % m)
    print("   object audit lanes (one per 20)        %4d" % o)
    print("   gate-coverage lanes (one per 10)       %4d" % g)
    print("   ------------------------------------------")
    print("   queued now                             %4d" % q)


if __name__ == "__main__":
    main()
