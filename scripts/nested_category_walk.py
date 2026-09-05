#!/usr/bin/env python
"""Walk a registry outcome's nested classes and categories, and select a value by
CLASS TITLE -- never by index.

A cause-specific or timepoint-specific value often sits under
outcome_measurements' classification (the "class") and category, not in the
outcome title. A walk over outcome titles alone misses it: the nested walk moved
all-cause-death reach from 36 to 42 of 79 trials, and apixaban prophylaxis from 1
of 5 to 5 of 5 (four of its five hide deaths inside a bundled adverse-event
outcome).

THE DANGER, and why the walk must match the class TITLE. ODYSSEY CHOICE I
(NCT01926782) reports one outcome under TWO sibling classes -- "At Week 24" and
"At averaged Week 21 to 24" -- both with a null category. A reader taking the
class by INDEX gets whichever the registry happened to order first, which is a
different timepoint from the one asked for. The title is the identity; the index
is not.

walk(measurements) -> flat rows (class_title, category_title, group, value).
pick(rows, class_title=..., category_title=...) -> rows whose titles MATCH, in the
order found, never sliced by position. Ambiguity (a wanted class absent, or a
title matching more than one distinct class) is returned as such, not resolved by
taking the first.
"""
from __future__ import annotations


def walk(measurements):
    """measurements: iterable of dicts with classification/category/ctgov_group_code/
    param_value (AACT outcome_measurements shape). Yields normalised rows so a value
    nested under a class+category is reachable, not just top-level outcome titles."""
    out = []
    for m in measurements:
        out.append({
            "class_title": (m.get("classification") or "").strip(),
            "category_title": (m.get("category") or "").strip(),
            "group": m.get("ctgov_group_code"),
            "value": m.get("param_value"),
            "param_type": m.get("param_type"),
        })
    return out


def pick(rows, class_title=None, category_title=None):
    """Rows whose class/category titles match the request, BY TITLE. Never [0]."""
    sel = rows
    if class_title is not None:
        sel = [r for r in sel if r["class_title"] == class_title]
    if category_title is not None:
        sel = [r for r in sel if r["category_title"] == category_title]
    return sel


def _selftest():
    out, ok = [], True

    def check(name, got, want):
        nonlocal ok
        good = got == want
        ok &= good
        out.append((name, "OK" if good else "*** FAIL ***", got, want))

    # ODYSSEY CHOICE I (NCT01926782): one outcome, two timepoint classes, null category.
    # Real values from the 2026-08-30 snapshot.
    meas = [
        {"classification": "At averaged Week 21 to 24", "category": "",
         "ctgov_group_code": "OG000", "param_value": "-54", "param_type": "LEAST_SQUARES_MEAN"},
        {"classification": "At averaged Week 21 to 24", "category": "",
         "ctgov_group_code": "OG001", "param_value": "-56.9", "param_type": "LEAST_SQUARES_MEAN"},
        {"classification": "At Week 24", "category": "",
         "ctgov_group_code": "OG000", "param_value": "-52.7", "param_type": "LEAST_SQUARES_MEAN"},
        {"classification": "At Week 24", "category": "",
         "ctgov_group_code": "OG001", "param_value": "-58.8", "param_type": "LEAST_SQUARES_MEAN"},
    ]
    rows = walk(meas)

    # BY TITLE: asking for "At Week 24" returns only the week-24 values.
    wk24 = [r["value"] for r in pick(rows, class_title="At Week 24")]
    check("pick class 'At Week 24' -> week-24 values only", wk24, ["-52.7", "-58.8"])

    # BY INDEX would take rows[0], which here is the AVERAGED class -- the wrong timepoint.
    by_index_first_class = rows[0]["class_title"]
    check("rows[0] is the AVERAGED class (why index is wrong)",
          by_index_first_class, "At averaged Week 21 to 24")
    check("title-match != index-match here", wk24 != [rows[0]["value"], rows[1]["value"]], True)

    # A wanted class that is ABSENT returns nothing, rather than falling through to [0].
    check("absent class -> empty, not a silent [0]",
          pick(rows, class_title="At Week 52"), [])

    # The nested walk reaches a value under a class+category a title-only scan misses.
    meas2 = [{"classification": "Cardiac disorders", "category": "Sudden cardiac death",
              "ctgov_group_code": "EG000", "param_value": "7", "param_type": "NUMBER"}]
    r2 = pick(walk(meas2), class_title="Cardiac disorders", category_title="Sudden cardiac death")
    check("value reachable under class+category", [r["value"] for r in r2], ["7"])
    return ok, out


if __name__ == "__main__":
    import sys, io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    good, rowsr = _selftest()
    print("nested_category_walk selftest")
    for name, verdict, got, want in rowsr:
        print("  %-48s %-12s got=%s want=%s" % (name, verdict, got, want))
    print("\n%s" % ("ALL PASS" if good else "FAILURES ABOVE"))
    raise SystemExit(0 if good else 1)
