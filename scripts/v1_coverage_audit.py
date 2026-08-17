"""V1 COVERAGE AUDIT -- for each standard property, does a check exist, and can it SEE?

WHY THIS EXISTS
    On 2026-08-17 `arm_identity_gate` returned UNCHECKABLE and `poolability`
    returned UNASSESSABLE on 100% of a real v1 object -- two of the standard's
    own properties, in gates I wrote, which I had been citing as coverage. If a
    page had shipped with "all eleven v1 properties pass", that sentence would
    have been about gates that RAN, not properties that HOLD.

    Two blind out of eleven is not a reason to assume the other nine see. It is
    a reason to measure all of them.

    LOGGED AS A SAVE, NOT ONLY A DEFECT: those two gates returned UNCHECKABLE
    rather than PASS. That single design choice is what stood between us and a
    false green, and this repo has far more logged failures than logged saves.
    A three-state verdict is worth its cost the first time it is right.

WHAT THIS AUDIT DOES NOT ESTABLISH -- written in advance
    - NOT that a PASS is correct. It records what each checker returned, not
      whether the checker is right.
    - NOT that a property with no checker is unmet -- only that nothing
      automated is watching it, which is a different and equally important fact.
    - NOT that a checker seeing ONE object sees all of them. Coverage is
      per-object and reported that way.
"""
from __future__ import annotations
import io, json, os, subprocess, sys

if __name__ == "__main__":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# (property, checker script or None, argv builder). None = no automated check.
def _obj(o, p):
    return [o]


def _page(o, p):
    return [p]


def _page_obj(o, p):
    return [p, o]


CHECKS = [
    ("tabbed_build",             "checkbuild-equivalent", None),
    ("estimate_preserved",       "checkbuild-equivalent", None),
    ("card_matches_page",        "card_alignment_gate.py", _page),
    ("extraction_table",         "extraction_table_gate.py", _page),
    ("sections_in_both_surfaces", "section_manifest_gate.py", _obj),  # needs a docmodel too
    ("build_stamp",              "build_stamp_gate.py", _page),
    ("subject_match",            "subject_match_gate.py", _page_obj),
    ("arm_identity",             "arm_identity_gate.py", _obj),
    ("poolable_or_withheld",     "poolability.py", _obj),
    ("estimand_definition_read", "estimand_definition_gate.py", _obj),
    ("identity_by_registration", "identity_by_registration_gate.py", _obj),
    ("no_synthesised_absence",   "absence_reason_gate.py", lambda o, p: [p, o]),
    ("self_contained",           "external_dependency_census.py", None),
    ("display_change_announced", None, None),
]

# Words a checker uses when it ran but could not see. Treated as UNCHECKABLE,
# never as a pass -- that distinction is the whole point of this file.
BLIND = ("UNCHECKABLE", "UNASSESSABLE", "no checkable", "NOT PROVEN",
         "fixtures absent", "not applicable", "0 check")


def run(script, argv):
    p = os.path.join(REPO, "scripts", script)
    if not os.path.exists(p):
        return "NO CHECKER", ""
    try:
        r = subprocess.run([sys.executable, p] + argv, cwd=REPO,
                           capture_output=True, text=True, timeout=180)
    except subprocess.TimeoutExpired:
        return "TIMEOUT", ""
    out = (r.stdout or "") + (r.stderr or "")
    # DROP TALLY LINES BEFORE CLASSIFYING. The first cut substring-searched the
    # whole output for "UNCHECKABLE" and matched card_alignment_gate's own tally
    # LABEL ("  UNCHECKABLE  508"), reporting a working gate as blind. That is
    # the AF_-inside-TAF_TDF over-match, committed inside the audit written to
    # find exactly this class. Normalise and compare the whole field, never a
    # fragment: a line that is <word> <integer> is a count, not a verdict.
    import re as _re
    lines = [l for l in out.splitlines()
             if not _re.match(r"^\s*[A-Za-z_]+\s+\d+\s*$", l)]
    out = chr(10).join(lines)
    if any(b.lower() in out.lower() for b in BLIND):
        return "UNCHECKABLE", out.strip().splitlines()[-1][:90] if out.strip() else ""
    # A CRASH IS ITS OWN VERDICT. A traceback means the gate never examined the
    # subject, so scoring it FAIL asserts a defect on a page nobody opened, and
    # scoring it PASS is worse. Exit 2 is the same statement made deliberately.
    last = out.strip().splitlines()[-1][:90] if out.strip() else ""
    if "Traceback (most recent call last)" in out:
        return "ERROR", last
    if r.returncode == 2:
        return "NOT RUN", last
    if r.returncode == 0:
        return "PASS", ""
    return "FAIL", last


def main():
    targets = []
    m = json.loads(open(os.path.join(REPO, "ssot", "PAGE_MAP.json"),
                        encoding="utf-8").read())
    want = sys.argv[1:] or ["ARNI_HF_REVIEW.html", "FINERENONE_CV_REVIEW.html"]
    for page in want:
        if page in m:
            targets.append((page, m[page]))
        else:
            print("no object mapped for %s -- skipped, not passed" % page)

    tally = {}
    for page, obj in targets:
        print("\n=== %s  <-  %s" % (page, obj))
        for prop, script, build in CHECKS:
            if script is None:
                state, note = "NO CHECKER", ""
            elif build is None:
                state, note = "NOT WIRED HERE", ""
            else:
                state, note = run(script, build(obj, page))
            tally[state] = tally.get(state, 0) + 1
            print("   %-26s %-14s %s" % (prop, state, note))

    print("\nVERDICT DISTRIBUTION across %d object(s) x %d propert(ies):"
          % (len(targets), len(CHECKS)))
    for k in sorted(tally, key=lambda x: -tally[x]):
        print("   %-16s %d" % (k, tally[k]))
    blind = tally.get("UNCHECKABLE", 0) + tally.get("NO CHECKER", 0) + \
        tally.get("NOT WIRED HERE", 0) + tally.get("TIMEOUT", 0)
    total = sum(tally.values())
    print("\n   NOT ESTABLISHED BY ANY RUNNING CHECK: %d of %d (%.0f%%)"
          % (blind, total, 100.0 * blind / total if total else 0))
    print("   A property with no checker, or a checker that cannot see, is NOT a "
          "passing property. It is an unmeasured one.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
