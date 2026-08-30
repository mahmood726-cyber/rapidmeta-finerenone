# -*- coding: utf-8 -*-
"""GENERATOR COMPONENT: safety, and every other outcome the trials reported -- with its tier.

WHY THE SECTION IS "EVERY OTHER OUTCOME" AND NOT "SAFETY". A table headed *safety* invites a
reader to assume that what is absent from it was safe. This section lists what the trials
reported, what they measured and did not report in a usable form, and what they never measured
at all -- because a table that lists only what was FOUND reads as a table of everything that
EXISTS, and that is the same defect as a scan reporting its reach as its population.

⛔ EVERY ROW CARRIES ITS PROVENANCE TIER, AND THE TIERS ARE NOT EQUAL.

    trial report · trial supplement · regulatory review · posted protocol or SAP ·
    registry results · prior-meta table (UNVERIFIED) · absent by design · absent

A number read from the trial's own report is not the same evidence as a number lifted from
another team's extraction table. Both are usable; presenting them in one undifferentiated
column is what makes a review look better sourced than it is. The tier is a COLUMN, not a
footnote, so it cannot be skimmed past.

⛔ AND WHERE A PRIOR-META VALUE IS USED, THE OBJECT MUST SAY WHETHER THE PRIMARY READ WAS
ATTEMPTED AND WHAT STOPPED IT. "We took this from someone else's table" is a fact about our
retrieval, and a row that hides it is claiming a document we do not hold. A row at the
prior-meta tier with no `why_the_primary_read_did_not_land` is REFUSED rather than printed,
because the missing field is the whole difference between a sourced number and a borrowed one.

⚠️ THREE STATES, NOT TWO, AND THE THIRD IS THE ONE EVERYONE DROPS. "Measured and reported",
"measured but not reported in a usable form", and "never measured" are different findings about
the trials. Collapsing the last two into a blank cell tells a reader nothing and lets a gap in
the evidence read as a gap in this page.
"""
import io
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(os.path.dirname(HERE))
SSOT = os.path.join(REPO, "ssot")
for _p in (HERE, SSOT):
    if _p not in sys.path:
        sys.path.insert(0, _p)

# Strongest first. The order is the standing-orders tier order and is not re-decided here.
TIERS = ("trial report", "trial supplement", "regulatory review", "posted protocol or SAP",
         "registry results", "prior-meta table (unverified)", "absent by design", "absent")

# A tier that is a borrowing rather than a read must account for itself.
BORROWED = ("prior-meta table (unverified)",)

TIER_NOTE = {
    "trial report": "read from the trial's own report",
    "trial supplement": "read from the trial's supplementary appendix",
    "regulatory review": "read from a regulator's review of the product",
    "posted protocol or SAP": "read from the posted protocol or statistical analysis plan",
    "registry results": "read from the registry's posted results",
    "prior-meta table (unverified)": "taken from another team's extraction table and NOT read "
                                     "at source",
    "absent by design": "the trials did not measure this",
    "absent": "the trials did not report this in a form that can be used here",
}


def _esc(s):
    return (str(s).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;"))


def _cell(v):
    """An em dash is MARKUP, not content -- escaping the default turned every blank cell into
    the literal string `&amp;mdash;` on the rendered page. Caught by reading the DISPLAYED
    bytes rather than the source."""
    s = "" if v is None else str(v).strip()
    if not s or s in ("—", "&mdash;", "-"):
        return "&mdash;"
    return _esc(s)


def _rows(res):
    oo = res.get("other_outcomes")
    if isinstance(oo, dict):
        return oo.get("rows") or [], oo.get("_note") or ""
    if isinstance(oo, list):
        return oo, ""
    return [], ""


def check_row(row):
    """-> (ok, reason). A row that cannot account for its own tier is not printed."""
    tier = str(row.get("tier") or "").strip().lower()
    if not tier:
        return False, "no provenance tier is recorded"
    if tier not in TIERS:
        return False, "the tier %r is not one of the recognised tiers" % row.get("tier")
    if tier in BORROWED and not row.get("why_the_primary_read_did_not_land"):
        # ⛔ NOT A HEDGE, A REFUSAL. See the module docstring.
        return False, ("the value is at the prior-meta tier but the object does not record why "
                       "the primary read did not land, so the row would claim a document we do "
                       "not hold")
    if not row.get("outcome"):
        return False, "the row names no outcome"
    return True, ""


def render(canon):
    head = "<h2>Safety, and every other outcome these trials reported</h2>"
    r = canon.get("results")
    outs = (r or {}).get("by_outcome") if isinstance(r, dict) else None
    if not isinstance(outs, dict) or not outs:
        return head + ("<p>This object records no outcome at all, so there is nothing to list "
                       "beside the primary one. That is a refusal, not an omission.</p>")
    out, printed = [head], 0
    for _oid, res in outs.items():
        if not isinstance(res, dict):
            continue
        rows, note = _rows(res)
        if not rows:
            continue
        body, refused, tiers_used = [], [], set()
        for row in rows:
            if not isinstance(row, dict):
                continue
            ok, why = check_row(row)
            if not ok:
                refused.append((row.get("outcome") or "an unnamed row", why))
                continue
            tier = str(row.get("tier")).strip().lower()
            tiers_used.add(tier)
            cls = "warn" if tier in BORROWED else ("muted" if tier.startswith("absent") else "")
            body.append(
                "<tr><td>%s</td><td>%s</td><td>%s</td><td>%s</td><td>%s</td>"
                "<td class=\"tier %s\">%s</td></tr>"
                % (_esc(row.get("outcome")), _cell(row.get("treatment")),
                   _cell(row.get("control")), _cell(row.get("effect")),
                   _cell(row.get("trials")), cls, _esc(row.get("tier"))))
            printed += 1
        if body:
            out.append("<div class=\"scroll\"><table><tr><th>Outcome</th><th>Intervention</th>"
                       "<th>Control</th><th>Reading</th><th>Trials</th>"
                       "<th>Provenance tier</th></tr>" + "".join(body) + "</table></div>")
            out.append("<p><b>What the tiers mean.</b> %s</p>"
                       % " ".join("<i>%s</i> &mdash; %s." % (_esc(t), TIER_NOTE[t])
                                  for t in TIERS if t in tiers_used))
            if any(t in BORROWED for t in tiers_used):
                for row in rows:
                    if (isinstance(row, dict)
                            and str(row.get("tier") or "").strip().lower() in BORROWED
                            and row.get("why_the_primary_read_did_not_land")):
                        out.append("<p><b>%s.</b> %s</p>"
                                   % (_esc(row.get("outcome")),
                                      _esc(row["why_the_primary_read_did_not_land"])))
                        break
        if note:
            out.append("<p>%s</p>" % _esc(note))
        for name, why in refused:
            out.append("<p><b>%s &mdash; not shown.</b> %s.</p>" % (_esc(name), _esc(why)))
    if not printed:
        # ⛔ THE ABSENCE IS PRINTED, for the reason in the docstring: a vanished section reads as
        # a review that looked and found nothing worth reporting.
        out.append(
            "<p>This object records no outcome besides the one pooled above. That is a "
            "statement about what has been extracted into this review, not about what the "
            "trials measured: a trial that reported harms this review has not extracted will "
            "look, from this page, exactly like a trial that reported none.</p>")
    return "".join(out)


MARKER = "<h2>Safety, and every other outcome these trials reported</h2>"


def inject(html, canon):
    if MARKER in html:
        return html
    return html + "\n<div class=\"card\">\n" + render(canon) + "\n</div>\n"


# ---------------------------------------------------------------------------------------------
# COVERAGE, and the controls.
# ---------------------------------------------------------------------------------------------

def coverage(root=None):
    import collections
    import glob
    import json
    root = root or SSOT
    per = collections.Counter()
    skipped = collections.Counter()
    objs = with_rows = 0
    for f in sorted(glob.glob(os.path.join(root, "*", "*.json"))):
        try:
            c = json.load(io.open(f, encoding="utf-8"))
        except Exception:
            # ⛔ COUNTED, NOT SKIPPED. A `continue` here removes the file from the denominator
            # and the coverage figure silently becomes a reach figure.
            skipped["file did not parse as JSON"] += 1
            continue
        if not isinstance(c, dict):
            skipped["top level is not an object"] += 1
            continue
        r = c.get("results")
        outs = r.get("by_outcome") if isinstance(r, dict) else None
        if not isinstance(outs, dict) or not outs:
            skipped["no results.by_outcome recorded"] += 1
            continue
        objs += 1
        hit = False
        for _oid, res in outs.items():
            if not isinstance(res, dict):
                continue
            rows, _n = _rows(res)
            if not rows:
                per["no other-outcome rows recorded"] += 1
                continue
            hit = True
            for row in rows:
                ok, _why = check_row(row) if isinstance(row, dict) else (False, "")
                per["row PRINTED" if ok else "row REFUSED (tier not accounted for)"] += 1
        with_rows += 1 if hit else 0
    return {"objects_with_a_pooled_result": objs, "objects_with_other_outcome_rows": with_rows,
            "detail": dict(per), "total": sum(per.values()),
            "skipped": dict(skipped)}


# ⭐ THE MODEL ANSWER. All three states present, and a borrowed row that accounts for itself.
MODEL_ANSWER = {
    "app_id": "__control_model_answer_other_outcomes",
    "results": {"by_outcome": {"primary": {"other_outcomes": {"_note": "control", "rows": [
        {"outcome": "Any serious adverse event", "treatment": "52 (4%)", "control": "48 (4%)",
         "effect": "no material difference", "trials": "one trial, 2629 people",
         "tier": "trial report"},
        {"outcome": "Incident sexually transmitted infections", "treatment": "not stated",
         "control": "not stated", "effect": "reported as similar", "trials": "one trial",
         "tier": "prior-meta table (unverified)",
         "why_the_primary_read_did_not_land":
             "the counts are in a supplementary appendix this retrieval did not obtain"},
        {"outcome": "Herpes simplex virus", "treatment": "&mdash;", "control": "&mdash;",
         "effect": "NOT MEASURABLE &mdash; not screened for", "trials": "&mdash;",
         "tier": "absent by design"},
        {"outcome": "Acceptability", "treatment": "&mdash;", "control": "&mdash;",
         "effect": "NOT REPORTED in a poolable form", "trials": "&mdash;",
         "tier": "absent"}]}}}}}

# ⭐ REFUSAL CONTROL 1 -- a borrowed value that does not say why the primary read did not land.
# ⚠️ If this ever creates pressure to print the row anyway, the control is right: the row would
# be presenting another team's extraction as though it were our own read.
UNACCOUNTED_BORROW_CONTROL = {
    "app_id": "__control_refusal_unaccounted_borrow",
    "results": {"by_outcome": {"primary": {"other_outcomes": {"rows": [
        {"outcome": "Gonorrhoea", "treatment": "&mdash;", "control": "&mdash;",
         "effect": "RR 1.00 (0.87 to 1.15)", "trials": "two trials",
         "tier": "prior-meta table (unverified)"}]}}}}}

# ⭐ REFUSAL CONTROL 2 -- a row with no tier at all.
NO_TIER_CONTROL = {
    "app_id": "__control_refusal_no_tier",
    "results": {"by_outcome": {"primary": {"other_outcomes": {"rows": [
        {"outcome": "Any serious adverse event", "treatment": "52 (4%)", "control": "48 (4%)",
         "effect": "no material difference"}]}}}}}

# ⭐ REFUSAL CONTROL 3 -- an object with nothing at all must still SAY something.
EMPTY_CONTROL = {"app_id": "__control_empty",
                 "results": {"by_outcome": {"primary": {"pooled": {"point": 0.7}}}}}


def _plain(html):
    return re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", html))


def plant():
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    html = render(MODEL_ANSWER)
    t = _plain(html)
    tiers = re.findall(r"<td class=\"tier[^\"]*\">([^<]*)</td>", html)
    print("MODEL ANSWER -- four rows, four tiers, three states of evidence.")
    assert tiers == ["trial report", "prior-meta table (unverified)", "absent by design",
                     "absent"], tiers
    print("   tier column: %s   [PASS]" % "; ".join(tiers))
    assert "NOT MEASURABLE" in t and "NOT REPORTED" in t, t[:400]
    print("   'not measured' and 'not reported in a usable form' both printed   [PASS]")
    assert "supplementary appendix this retrieval did not obtain" in t, t[:600]
    print("   the borrowed row states what stopped the primary read   [PASS]")
    for name in ("gonorrh", "chlamyd", "trichomon"):
        pass
    print("")
    for obj, must_say, what in (
            (UNACCOUNTED_BORROW_CONTROL, "does not record why the primary read did not land",
             "a borrowed value that cannot account for itself"),
            (NO_TIER_CONTROL, "no provenance tier is recorded", "a row with no tier"),
            (EMPTY_CONTROL, "look, from this page, exactly like",
             "an object with no other outcomes at all")):
        h = render(obj)
        tt = _plain(h)
        said = must_say.lower() in tt.lower()
        # ⛔ AND THE REFUSED ROW MUST NOT ALSO HAVE BEEN PRINTED.
        no_row = "<td class=\"tier" not in h
        print("REFUSAL CONTROL -- %s" % what)
        print("   reason stated: %s   row withheld: %s   [%s]"
              % (said, no_row, "PASS" if said and no_row else "FAIL"))
        assert said and no_row, tt[:400]
    print("")
    print("⚠️ A row may not be promoted to a stronger tier to make the table look better")
    print("   sourced. The tier is the row's own account of where its number came from.")
    return 0


if __name__ == "__main__":
    if "--plant" in sys.argv:
        raise SystemExit(plant())
    import json
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace",
                                  line_buffering=True)
    if "--coverage" in sys.argv:
        root = SSOT
        for i, a in enumerate(sys.argv):
            if a == "--root" and i + 1 < len(sys.argv):
                root = sys.argv[i + 1]
        c = coverage(root)
        n, m = c["objects_with_a_pooled_result"], c["total"]
        print("")
        print("COVERAGE FRACTION -- safety and other outcomes")
        print("  scanned: %s" % root)
        if not n:
            print("  ⛔ SCAN FOUND NOTHING -- a failure of this scan, not of the corpus.")
            raise SystemExit(2)
        print("  objects with a pooled result          %4d   == the object denominator" % n)
        print("  objects carrying other-outcome rows   %4d   %5.1f%%"
              % (c["objects_with_other_outcome_rows"],
                 100.0 * c["objects_with_other_outcome_rows"] / n))
        for k, v in sorted(c["detail"].items(), key=lambda kv: -kv[1]):
            print("     %-46s %4d   %5.1f%%" % (k, v, 100.0 * v / m if m else 0.0))
        if c.get("skipped"):
            print("")
            print("  SKIPPED, by kind -- these files were NOT in any denominator "
                  "above:")
            for _k, _v in sorted(c["skipped"].items(), key=lambda kv: -kv[1]):
                print("     %-46s %4d" % (_k, _v))
            print("  ⚠️ A skip that is not counted turns a coverage figure into a "
                  "reach figure.")
        raise SystemExit(0)
    os.chdir(REPO)
    for path in sys.argv[1:] or ["ssot/agyw-hiv-prep-review/agyw-hiv-prep-review.json"]:
        canon = json.load(io.open(path, encoding="utf-8"))
        print("=" * 78)
        print(os.path.basename(path))
        print(_plain(render(canon))[:1800])
