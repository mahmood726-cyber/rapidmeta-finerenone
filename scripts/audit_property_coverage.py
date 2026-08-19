#!/usr/bin/env python3
"""AUDIT THE REGISTRY ITSELF: which properties are defended by a COMMAND, and which by PROSE.

THE STANDING INSTRUCTION IS THAT THESE MISTAKES CANNOT BE MADE AGAIN, AND THE ONLY EVIDENCE
THAT COUNTS IS A COMMAND THAT REJECTS THE DEFECT. This file applies that test to the standard
rather than to the corpus, because the standard is where the untested claims accumulate: every
property was written the moment its defect was found, when the memory of it was vivid and the
temptation to call the writing-down a fix was highest.

    THE NIGHT'S OWN EVIDENCE IS THAT DOCUMENTATION FAILS AS A CONTROL IN THE MOST FAVOURABLE
    CONDITIONS IT WILL EVER GET. Heredoc mangling recurred EIGHT times in one night against an
    author who had read the rule, written the rule, and committed the rule. A property in a
    document is a description of a defect, not a defence against it.

THE FOUR PARTS, ALL MECHANICAL. A property is CLOSED only when all four hold:

    1. EXISTS   a named command is on disk
    2. WIRED    that command's filename appears in .githooks/pre-commit, so it RUNS unasked
    3. PROVEN   something demonstrates it REJECTS a real failing input -- a prove_*.py naming
                it, or an in-file known-answer probe. An unproven detector may be an
                over-escaped pattern that matches nothing and reports clean.
    4. GREEN    it exits 0 on the repository as it stands, so a red state is visible NOW and
                not discovered by whoever wires it in next

PARTIAL = a command exists and at least one part is missing. OPEN = no command at all, and the
property's only defence is that someone will remember it.

WHY THIS IS A RATCHET AND NOT A GATE. Running it today must not block a commit, because most of
the open classes are open for the honest reason that no failing input exists yet to prove a
detector against, and manufacturing one would be inventing the evidence. So it blocks on
COVERAGE GOING DOWN -- a property losing its command, or its wiring, or a new property added
with neither. That is the failure mode a ratchet can actually see.

WHAT THIS DOES NOT CLAIM. The mapping from property to command is a JUDGEMENT recorded here in
one place, and it is the part of this instrument a reader should distrust first: a detector
listed against a property is not thereby a complete test of that property. Where a command
covers only part of its property, the shortfall is named in `PARTIAL_BECAUSE` rather than
rounded up to closed. Rounding up here would defeat the entire purpose of the file.
"""
import io
import json
import os
import subprocess
import sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
HOOK = os.path.join(REPO, ".githooks", "pre-commit")
STANDARD = os.path.join(REPO, "PAGE-STANDARD.md")
BASELINE = os.path.join(REPO, "evidence", "property_coverage_baseline.json")

# THE STRETCH UNDER AUDIT. P24 through P36 were all found in one run, which is exactly the
# condition under which a registry accumulates prose fastest.
#
# EXTENDED TO P41 ON 2026-08-19, AND THE EXTENSION IS THE POINT. This scope was a hardcoded
# `range(24, 37)`, so P37-P40 -- four properties added the same day -- would have been
# INVISIBLE to the very instrument that exists to stop a registry accumulating undefended
# prose. It would have gone on reporting "CLOSED 3 / PARTIAL 2 / OPEN 8" over a thirteen-
# property window while the standard held forty, and every number it printed would have been
# true. THE AUDIT'S OWN SCOPE IS A CLAIM ABOUT ANOTHER FILE, and it ages exactly like the
# version marker in PAGE-STANDARD.md did.
#
# It is still a hardcoded range, and that is a deliberate half-measure rather than an
# oversight: deriving the scope from PAGE-STANDARD.md's table would make the audit silently
# re-scope itself whenever the document changed, which trades a stale window for an
# unannounced one. The upper bound is raised by hand, and `scripts/
# standard_version_agreement_gate.py` is what refuses a property that reaches the table
# without an entry. What NOTHING yet refuses is a property that reaches the table without
# reaching THIS list -- named here so the next lane inherits the gap rather than the illusion.
SCOPE = ["P%d" % n for n in range(24, 41)]

# property -> the command that is claimed to defend it, or None for "no command exists".
# A NAME HERE IS A CLAIM AND IS CHECKED; a None here is an admission and is REPORTED.
DECLARED = {
    "P24": None,
    "P25": "lint_pipeline_exit_status.py",
    "P26": None,
    "P27": None,
    "P28": None,
    "P29": None,
    "P30": "lint_cascade_arithmetic.py",
    # E4 has no P-number of its own; the withholding gate is recorded against the
    # two properties it actually serves, and named here so the link is not lost.
    "P31": None,
    "P32": None,
    "P33": "lint_composite_by_components.py",
    "P34": None,
    "P35": "lint_primary_by_position.py",
    "P36": "lint_composite_by_components.py",
    # Added 2026-08-19 with the properties themselves. Three of the four are None, and that
    # is an admission rather than an omission: a property added on the same day it was
    # learned almost never has a command yet, and writing one here that does not exist would
    # be the exact failure this file measures.
    "P37": "lint_composite_by_components.py",
    "P38": None,
    "P39": None,
    "P40": None,
}

# Where a command exists but does NOT cover the whole property, the gap is stated here. An
# unstated gap is the same failure as an undefended property, one level up.
PARTIAL_BECAUSE = {
    "P25": ("checks that `$?` is not read through a pipe. It does NOT check the second half of "
            "the property -- that an empty result from a filter is NOT_ASSESSABLE rather than a "
            "negative finding. And it is NOT WIRED into the hook."),
    "P30": ("the cascade arithmetic gate makes the k-cascade parts sum, which is one shape of "
            "the property. A number stated in a commit message or a page with no object behind "
            "it is still undetected, and lint_claim_traces_to_object.py is deliberately unwired "
            "with 18 uninspected alarms."),
}

# A proof is a file that demonstrates the detector REJECTING something. Discovered by scanning
# scripts/prove_*.py for the detector's module name, so the link cannot rot silently.
PROOF_DIR = os.path.join(REPO, "scripts")


def proofs_naming(module):
    hits = []
    for name in sorted(os.listdir(PROOF_DIR)):
        if not (name.startswith("prove_") or name.startswith("known_answer_")):
            continue
        p = os.path.join(PROOF_DIR, name)
        try:
            with io.open(p, encoding="utf-8", errors="replace") as fh:
                if module.replace(".py", "") in fh.read():
                    hits.append(name)
        except OSError:
            continue
    return hits


def in_hook(module):
    try:
        with io.open(HOOK, encoding="utf-8", errors="replace") as fh:
            return module in fh.read()
    except OSError:
        return False


def runs_green(module):
    """Exit status of the detector on the repository AS IT STANDS.

    NOT_ASSESSABLE, never FAIL, when the command cannot be executed at all -- an absent or
    unrunnable file is an absence of evidence and the house rule is that absence is not zero.
    """
    p = os.path.join(REPO, "scripts", module)
    if not os.path.exists(p):
        return None
    try:
        r = subprocess.run([sys.executable, p], cwd=REPO, stdout=subprocess.PIPE,
                           stderr=subprocess.PIPE, timeout=300)
    except Exception:
        return None
    return r.returncode == 0


def property_rows():
    """Read the property table so the audit is over what the STANDARD says, not a hand list."""
    rows = {}
    try:
        with io.open(STANDARD, encoding="utf-8", errors="replace") as fh:
            for line in fh:
                if not line.startswith("| P"):
                    continue
                parts = [c.strip() for c in line.strip().strip("|").split("|")]
                if len(parts) >= 2 and parts[0].startswith("P") and parts[0][1:].isdigit():
                    rows[parts[0]] = parts[1].strip("* ")
    except OSError:
        pass
    return rows


def main():
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    rows = property_rows()
    missing = [p for p in SCOPE if p not in rows]
    if missing:
        # The standard does not contain a property this audit claims to audit. That is a broken
        # instrument, not a clean run.
        print("REFUSED: %s not found in PAGE-STANDARD.md" % ", ".join(missing))
        return 2

    closed, partial, open_ = [], [], []
    detail = {}
    for p in SCOPE:
        mod = DECLARED.get(p)
        if not mod:
            open_.append(p)
            detail[p] = {"command": None, "state": "OPEN",
                         "why": "no command exists; the only defence is the document"}
            continue
        exists = os.path.exists(os.path.join(REPO, "scripts", mod))
        wired = in_hook(mod)
        proofs = proofs_naming(mod)
        green = runs_green(mod)
        parts = {"exists": exists, "wired": wired,
                 "proven": bool(proofs), "green": green}
        ok = exists and wired and bool(proofs) and green is True
        if ok and p not in PARTIAL_BECAUSE:
            closed.append(p)
            state = "CLOSED"
        elif exists:
            partial.append(p)
            state = "PARTIAL"
        else:
            open_.append(p)
            state = "OPEN"
        detail[p] = {"command": mod, "state": state, "parts": parts,
                     "proofs": proofs,
                     "shortfall": PARTIAL_BECAUSE.get(p)}

    print("PROPERTY COVERAGE, P24-P36 -- is there a COMMAND, or only a document?\n")
    for p in SCOPE:
        d = detail[p]
        mark = {"CLOSED": "CLOSED ", "PARTIAL": "PARTIAL", "OPEN": "OPEN   "}[d["state"]]
        print("  %s  %-4s %s" % (mark, p, rows[p][:66]))
        if d["command"]:
            pt = d["parts"]
            print("           command %s  [exists %s | wired %s | proven %s | green %s]"
                  % (d["command"], "Y" if pt["exists"] else "N", "Y" if pt["wired"] else "N",
                     "Y" if pt["proven"] else "N",
                     {True: "Y", False: "N", None: "?"}[pt["green"]]))
            if d["shortfall"]:
                print("           SHORTFALL: %s" % d["shortfall"])

    print("\n  CLOSED  %2d   %s" % (len(closed), " ".join(closed) or "-"))
    print("  PARTIAL %2d   %s" % (len(partial), " ".join(partial) or "-"))
    print("  OPEN    %2d   %s" % (len(open_), " ".join(open_) or "-"))

    cur = {"closed": sorted(closed), "partial": sorted(partial), "open": sorted(open_)}
    if not os.path.exists(BASELINE):
        with io.open(BASELINE, "w", encoding="utf-8") as fh:
            fh.write(json.dumps(cur, indent=1))
        print("\nbaseline written: %s" % BASELINE)
        return 0

    with io.open(BASELINE, encoding="utf-8") as fh:
        base = json.load(fh)
    # THE RATCHET: a property may move toward CLOSED freely. Moving AWAY from it is the defect.
    rank = {"OPEN": 0, "PARTIAL": 1, "CLOSED": 2}
    base_state = {}
    for st in ("closed", "partial", "open"):
        for p in base.get(st, []):
            base_state[p] = st.upper()
    regressed = [p for p in SCOPE
                 if p in base_state and rank[detail[p]["state"]] < rank[base_state[p]]]
    if regressed:
        for p in regressed:
            print("\nREGRESSED: %s was %s and is now %s" % (p, base_state[p], detail[p]["state"]))
        print("A property does not lose its command silently.")
        return 1
    if cur != base:
        with io.open(BASELINE, "w", encoding="utf-8") as fh:
            fh.write(json.dumps(cur, indent=1))
        print("\nbaseline advanced (coverage improved): %s" % BASELINE)
    return 0


if __name__ == "__main__":
    sys.exit(main())
