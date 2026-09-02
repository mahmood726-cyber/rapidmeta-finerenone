# -*- coding: utf-8 -*-
"""Re-derive EVERY number in REPORT-SCORED-RUN.md from scores.json, independently.

⛔ WHY THIS EXISTS. Numbers in a report are transcribed by hand from a run's stdout, and a
transcription error is invisible: it is internally consistent, it is plausible, and nobody
re-derives it because the run "already printed it". Every claim below is recomputed from the
JSON and compared to the string actually present in the published markdown.

⭐ IT CHECKS THE FILE, NOT MY MEMORY OF THE FILE. Each row asserts the literal text appears in
the report, so a number that was corrected in one place and not another FAILS here rather than
shipping.

⚠️ SCOPE, STATED SO IT CANNOT BE READ AS COVERAGE: this checks the numbers it was told to
check. A number in the report that has no row here is UNVERIFIED, and the count of rows is
printed so that is visible.
"""
import io
import json
import os
import sys
from collections import Counter

if __name__ == "__main__":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace",
                                  line_buffering=True)

HERE = os.path.dirname(os.path.abspath(__file__))
BASE = os.path.abspath(os.path.join(HERE, "..", "..", "evidence", "2026-09-01-scored-run"))
SCORES = os.path.join(BASE, "scores.json")
REPORT = os.path.join(BASE, "REPORT-SCORED-RUN.md")
CRIT = ("S2", "S3", "S4", "S5", "S6", "S7")


def main():
    S = json.load(io.open(SCORES, encoding="utf-8"))
    md = io.open(REPORT, encoding="utf-8").read()
    rows = S["rows"]
    scored = [r for r in rows if r.get("state") == "SCORED"]

    disp = Counter(r.get("state") for r in rows)
    joint = Counter(r["derived"][c] for r in scored for c in CRIT)
    cells = len(scored) * len(CRIT)

    # ⛔ THEIR SIDE REFUSED BY OUR HARNESS -- and the first version of this line derived 18,
    # not the 17 the report claims, while the check still PASSED because it only asked
    # whether the sentence appeared. The 18th cell is S2's NO_FROZEN_TOPIC_TERMS, which
    # refuses BOTH sides (§5.2 covers 6 of 14 topics) and is therefore not "their side
    # refused". A cell only counts here if theirs is refused and OURS IS NOT.
    theirs_refused = sum(
        1 for r in scored for c in CRIT
        if r["derived"][c] == "NOT_SCOREABLE"
        and str(r["theirs"][c]["verdict"]).startswith("NOT_SCOREABLE")
        and not str(r["ours"][c]["verdict"]).startswith("NOT_SCOREABLE"))
    s7_ours_better = sum(1 for r in scored if r["derived"]["S7"] == "OURS_BETTER")

    checks = []

    def chk(label, value, must_appear, expect=None):
        """⛔ THREE CONDITIONS, NOT ONE. The first version asserted only that `must_appear`
        was in the report, so a derived 18 sat happily beside a published 17 and the row
        printed OK. A presence test is not a comparison.

            (a) the derived value equals the value this row DECLARES it should be
            (b) the declared value appears as a token inside the quoted report text
            (c) the quoted report text is actually in the file

        (b) is what ties the row to the sentence: a row that declares 17 while quoting a
        sentence containing no 17 is a row pointing at the wrong sentence.
        """
        want = value if expect is None else expect
        ok_val = str(value) == str(want)
        ok_tok = str(want) in must_appear
        ok_txt = must_appear in md
        checks.append((label, value, want, must_appear, ok_val and ok_tok and ok_txt,
                       "" if (ok_val and ok_tok and ok_txt) else
                       ("derived %s != declared %s" % (value, want) if not ok_val else
                        ("declared %s not in the quoted text" % want if not ok_tok else
                         "quoted text not in the report"))))

    chk("pairs SCORED", disp["SCORED"], "SCORED                                        10")
    chk("cells = scored x 6", cells, "60 CRITERION CELLS")
    chk("OURS_BETTER", joint["OURS_BETTER"], "OURS_BETTER              23")
    chk("COMPARATOR_BETTER", joint["COMPARATOR_BETTER"], "COMPARATOR_BETTER         0")
    chk("NOT_SCOREABLE", joint["NOT_SCOREABLE"], "NOT_SCOREABLE            21")
    chk("TIE_NEITHER", joint["TIE_NEITHER_SATISFIES"], "TIE_NEITHER_SATISFIES    11")
    chk("TIE_BOTH", joint["TIE_BOTH_SATISFY"], "TIE_BOTH_SATISFY          5")
    both_refused = sum(
        1 for r in scored for c in CRIT
        if r["derived"][c] == "NOT_SCOREABLE"
        and str(r["theirs"][c]["verdict"]).startswith("NOT_SCOREABLE")
        and str(r["ours"][c]["verdict"]).startswith("NOT_SCOREABLE"))
    ours_only = sum(
        1 for r in scored for c in CRIT
        if r["derived"][c] == "NOT_SCOREABLE"
        and not str(r["theirs"][c]["verdict"]).startswith("NOT_SCOREABLE")
        and str(r["ours"][c]["verdict"]).startswith("NOT_SCOREABLE"))
    chk("theirs refused, ours scoreable", theirs_refused,
        "    theirs refused, OURS SCOREABLE      16     the comparison lost to our harness")
    chk("both sides refused", both_refused,
        "    BOTH sides refused                   2     S2 no frozen topic terms")
    chk("only ours refused", ours_only,
        "    only OURS refused                    3     S3 / S5 / S7 on 38753662")
    # ⭐ THE KINDS MUST SUM TO THE POPULATION. A decomposition that does not add up is not a
    # decomposition; this is the check that would have caught 17-vs-18 immediately.
    chk("decomposition sums to the population", theirs_refused + both_refused + ours_only,
        "                                        21", expect=joint["NOT_SCOREABLE"])
    chk("S7 share of OURS_BETTER", s7_ours_better,
        "**S7 alone supplies 9 of the 23 `OURS_BETTER` cells**")
    chk("no-pooled-estimate refusals", disp["NOT_SCOREABLE_NO_POOLED_ESTIMATE_OUR_SIDE"],
        "NOT_SCOREABLE_NO_POOLED_ESTIMATE_OUR_SIDE      7")
    chk("surface-disagreement refusals", disp["NOT_SCOREABLE_SURFACE_DISAGREEMENT"],
        "NOT_SCOREABLE_SURFACE_DISAGREEMENT             3")
    chk("no-study-list refusals (THEIRS)", disp["NOT_SCOREABLE_NO_STUDY_LIST"],
        "NOT_SCOREABLE_NO_STUDY_LIST                    2    THEIRS")
    chk("table-not-machine-readable refusals", disp["NOT_SCOREABLE_TABLE_NOT_MACHINE_READABLE"],
        "NOT_SCOREABLE_TABLE_NOT_MACHINE_READABLE       2")
    chk("rubric sha", S["rubric_sha256"][:16], S["rubric_sha256"][:16])

    for c in ("S4", "S6"):
        n = sum(1 for r in scored
                if str(r["theirs"][c]["verdict"]).startswith("NOT_SCOREABLE"))
        want = {"S4": "S4  theirs NOT_SCOREABLE_INPUTS_ABSENT            9 of 10",
                "S6": "S6  theirs NOT_SCOREABLE_MATERIAL_NOT_RETRIEVED   8 of 10"}[c]
        chk("%s theirs refused" % c, n, want)

    n_s2_ours = sum(1 for r in scored if r["ours"]["S2"]["verdict"] == "NOT_SATISFIED")
    n_s2_theirs = sum(1 for r in scored if r["theirs"]["S2"]["verdict"] == "NOT_SATISFIED")
    chk("S2 ours NOT_SATISFIED", n_s2_ours,
        "S2  ours NOT_SATISFIED 9 · theirs NOT_SATISFIED 9")
    chk("S2 theirs NOT_SATISFIED", n_s2_theirs,
        "S2  ours NOT_SATISFIED 9 · theirs NOT_SATISFIED 9")

    bad = 0
    print("=== EVERY REPORTED NUMBER, RE-DERIVED FROM scores.json ===")
    print("   %-34s %10s %10s  %s" % ("claim", "derived", "declared", "verdict"))
    for label, value, want, _text, ok, why in checks:
        if not ok:
            bad += 1
        print("   %-34s %10s %10s  %s" % (label, value, want, "OK" if ok else "FAIL: " + why))
    print("")
    print("   rows checked : %d" % len(checks))
    print("   ⚠️ a number in the report with no row here is UNVERIFIED, not confirmed.")

    # ⭐ DETECTOR CONTROL. The first version of this file passed 18 of 18 while one derived
    # value disagreed with the published one -- it could not fail, and a check that cannot
    # fail is not evidence. These three planted rows must each be caught.
    plants = [("plant: derived != declared", 23, 99, "OURS_BETTER              23"),
              ("plant: declared absent from the quoted text", 23, 23, "no numeral here"),
              ("plant: quoted text absent from the report", 23, 23,
               "OURS_BETTER              99")]
    pbad = 0
    print("")
    print("   -- detector control: each of these MUST be caught --")
    for label, val, want, text in plants:
        caught = not (str(val) == str(want) and str(want) in text and text in md)
        pbad += 0 if caught else 1
        print("   %-46s %s" % (label, "caught" if caught else "MISSED -- CHECK IS BLIND"))
    if pbad:
        print("")
        print("   ⛔ %d planted error(s) not caught. The check itself is broken." % pbad)
        return 1

    if bad:
        print("")
        print("   ⛔ %d claim(s) in the report do not match the data. NOT PUBLISHABLE." % bad)
        return 1
    print("   every checked claim matches the run.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
