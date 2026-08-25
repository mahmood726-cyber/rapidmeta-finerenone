"""Refuse a protocol whose own wording forces two factors to move together.

THE TRIGGER IS SYNTACTIC, WHICH IS THE POINT. It needs no insight into what a protocol is
for -- it reads the words that create exclusions and then asks whether any cell survives in
which one factor varies while the other is held fixed.

WHY IT EXISTS. Two collinear designs shipped in one week, both from sound motives:

  * a site-lane protocol said "a judge never marks its own lab" -- entirely reasonable, and it
    gave every judge a different mix of RAISERS. The reported 2.2x judge spread was Simpson's
    paradox; stratified, judges differ 1.1x and raisers 2.1x.

  * this lane assigned panel families as
        family = ("openai", "google")[(idx + role_offset) % 2]
    so student and editor on the same page were ALWAYS different families. Across 149 pages
    the marginals were flawless -- ~50/50 either way -- and every PAGE-LEVEL comparison of
    role was simultaneously a comparison of family.

Neither was caught by asking "are the groups balanced?", because both WERE balanced. The
question that catches them is:

    FOR THE COMPARISON I ACTUALLY WANT, DOES ANYTHING ELSE VARY WITH IT?

WHAT THIS CHECKS. Any file naming an assignment together with an exclusion word -- never,
only, excluding, other than, must not, always different -- is flagged for a stated
justification. The check cannot know whether a given exclusion is harmful, so it does not
guess: it requires the author to have written down which comparison survives it.

DECLARE with a line anywhere in the same file:

    # collinearity-checked: <which comparison remains identified, and why>

That is deliberately a sentence rather than a flag. The failure mode is not forgetting to
tick a box; it is never having asked, and a sentence cannot be written without asking.
"""
import io
import os
import re
import sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

RATER = r"famil(?:y|ies)|judge|rater|reviewer|assessor|seat|persona|panelist|lane"

# RULE 1 -- ROTATION, matched against CODE. A rater collection subscripted by a counter
# modulo n. The modulo IS the exclusion: unit i can only ever be read by rater (i % n), so
# rater is a deterministic function of unit and nothing varying with unit is separable from
# it. Round 1 was  family = ("openai", "google")[(idx + role_offset) % 2]  and this matches
# exactly that shape. A mechanism lives in code, so it is matched in code.
ROTATION = re.compile(r"(?i)\b(?:" + RATER + r")\w*\b[^\n]{0,70}%\s*\d")

# RULE 2 -- STATED EXCLUSION, matched against PROSE, but only in a file that assigns raters
# in code. "A judge never marks its own lab" is a policy, and policies are written in
# sentences; the code condition is what stops it firing on every file containing "only".
EXCLUSION = re.compile(
    r"\bnever\b|\bonly\b|\bexcluding\b|\bother than\b|\bmust not\b|"
    r"\balways different\b|\bnot its own\b|\bexcept\b", re.I)
ASSIGNS_IN_CODE = re.compile(
    r"(?i)\b(?:" + RATER + r")\w*\b[^\n]{0,60}"
    r"(?:\[|=\s*\(|=\s*\[|\bfor\b|\bassign|\ballocat|\brotat|\balternat)")

DECLARED = re.compile(r"#\s*collinearity-checked:\s*\s", re.I)

SKIP_DIRS = {".git", "node_modules", "__pycache__", "figs", "build-artefacts", "outputs"}


def code_only(text):
    """The file with comments and string literals removed.

    A MECHANISM lives in code; a POLICY lives in prose. The first version of this check ran
    both patterns over raw text -- so all six of its hits were docstring matches, and it
    could not have caught round 1 at all. Splitting the two is what makes it a real check.
    """
    import io as _io, tokenize as _tk
    out = []
    try:
        for tok in _tk.generate_tokens(_io.StringIO(text).readline):
            out.append(chr(10) * tok.string.count(chr(10))
                       if tok.type in (_tk.COMMENT, _tk.STRING) else tok.string)
    except Exception:
        return text                  # unparseable: keep the wider net, never the narrower
    return "".join(out)


def scan(path):
    try:
        raw = io.open(path, encoding="utf-8", errors="replace").read()
    except Exception:
        return None
    code = code_only(raw)
    hit = None
    m = ROTATION.search(code)
    if m:
        hit = ("rotation", m.group(0).strip()[:58], code[:m.start()].count(chr(10)) + 1)
    else:
        ex = EXCLUSION.search(raw)
        if ex and ASSIGNS_IN_CODE.search(code):
            hit = ("stated exclusion", ex.group(0), raw[:ex.start()].count(chr(10)) + 1)
    if hit is None:
        return None
    return (("declared",) if DECLARED.search(raw) else ("undeclared",)) + hit



# ---------------------------------------------------------------------------
# CONTROLS. Run on every invocation, before any finding is reported. Two must be
# CAUGHT and two must be CLEAN: a check whose controls are all positive cannot
# distinguish working from broken. The first version of this file passed a
# positive-only reading and still missed panel_the_corpus, its founding case.
# If any control fails, the run reports NOTHING and exits 2.
# ---------------------------------------------------------------------------
CONTROLS = [
    ("round1_rotation", True,
     '"""Round 1."""@NFAMILIES=("openai","google")@Ndef a(idx,off):@N'
     '    family = FAMILIES[(idx + off) % 2]@N'),
    ("sitelane_exclusion", True,
     '"""A judge never marks its own lab."""@NJUDGES=["a","b"]@Nfor judge in JUDGES:@N    pass@N'),
    ("prose_only_no_code", False,
     '"""Only family A cannot pick its own arm; judges never mark their own lab."""@NX=1@N'),
    ("fully_crossed", False,
     '"""Every rater sees every item."""@NFAMS=["a","b"]@N'
     'jobs=[(p,f) for p in pages for f in FAMS]@N'),
]


def run_controls():
    """Route the four known-answer cases through the SHARED assertion.

    A per-file reimplementation of a control is how a control drifts, so this calls
    instrument_controls.require_controls rather than asserting privately. The positive
    control is round 1's real rule as it appears in panel_the_corpus line 161; the negative
    is a fully-crossed design, which this check must never flag.
    """
    import tempfile
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    from instrument_controls import require_controls

    d = tempfile.mkdtemp(prefix="collin_ctl_")
    got = {}
    for name, must_catch, src in CONTROLS:
        fp = os.path.join(d, "ctl_%s.py" % name)
        io.open(fp, "w", encoding="utf-8").write(src.replace("@N", chr(10)))
        got[name] = scan(fp) is not None

    require_controls(
        "lint_collinear_protocol",
        ("round1 rotation, the rule this check exists for "
         "(panel_the_corpus:161)", got["round1_rotation"], True),
        ("fully-crossed design, which is identified and must not be flagged",
         got["fully_crossed"], True))
    require_controls(
        "lint_collinear_protocol (rule 2)",
        ("site-lane stated exclusion in a file that assigns judges",
         got["sitelane_exclusion"], True),
        ("prose-only file naming no rater in code", got["prose_only_no_code"], True))
    return []


def main():
    _f = run_controls()
    if _f:
        print("CONTROLS FAILED -- no findings reported:")
        for _x in _f:
            print("    " + _x)
        return 2
    rot, prose, declared, scanned = [], [], 0, 0
    for root, dirs, files in os.walk(os.path.join(REPO, "scripts")):
        dirs[:] = [d for d in dirs if d not in SKIP_DIRS]
        for fn in files:
            if not fn.endswith(".py"):
                continue
            scanned += 1
            r = scan(os.path.join(root, fn))
            if r is None:
                continue
            if r[0] == "declared":
                declared += 1
                continue
            rel = os.path.relpath(os.path.join(root, fn), REPO)
            (rot if r[1] == "rotation" else prose).append((rel, r[2], r[3]))

    print("scripts scanned                     : %d" % scanned)
    print("declared (justification written)    : %d" % declared)
    print("ROTATION, undeclared   [BLOCKING]   : %d" % len(rot))
    print("stated exclusion       [advisory]   : %d" % len(prose))

    if prose:
        print()
        print("ADVISORY -- prose exclusion in a file that names a rater in code. On its first")
        print("run this rule flagged 12 files and 11 were prose ('only', 'never' in a")
        print("docstring). It is printed for review and does NOT block, because a gate that")
        print("refuses what it cannot prove teaches people to bypass it.")
        for rel, why, line in prose:
            print("    %-54s %s (line %d)" % (rel, why, line))

    if not rot:
        print()
        print("No undeclared rotation. BLOCKING rule 1 is a mechanism check: a rater")
        print("collection subscripted by a counter modulo n. It proves a justification was")
        print("written, not that the design is identified.")
        return 0

    print()
    for rel, why, line in rot:
        print("  %-52s %s (line %d)" % (rel, why, line))
    print()
    print("REFUSED: a rater is being chosen as a function of the unit index. Every factor")
    print("that varies with the unit is then inseparable from the rater. State which")
    print("comparison survives, in the same file:")
    print()
    print("    # collinearity-checked: <which comparison remains identified, and why>")
    print()
    print("The question is not 'are the groups balanced' -- round 1 was balanced 50/50 and")
    print("was still confounded on every page. It is: for the comparison I actually want,")
    print("does anything else vary with it?")
    return 1


if __name__ == "__main__":
    sys.exit(main())
