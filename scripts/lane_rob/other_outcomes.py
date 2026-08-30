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


def _has_figure(v):
    """Does this reading actually carry a NUMBER a reader would take away?"""
    return bool(re.search(r"\d", str(v or "")))


def _attribution(row):
    """A short phrase naming where a borrowed figure came from. Never a bare tier name."""
    if row.get("attribution"):
        return str(row["attribution"])
    src = row.get("source")
    if isinstance(src, dict):
        what = str(src.get("what") or "")
        if "COMPARATOR" in what.upper():
            return "the comparator's own pooled figure"
        if what:
            return what.split(",")[0]
    return "a prior synthesis"


def _utf8_once():
    """⛔ WRAP STDOUT ONCE. Two plants in one process each wrapped it, and the second wrap
    closed the first's buffer -- the bug this project's own lessons file describes, hit twice
    tonight in two different modules. A guard, not a convention."""
    if getattr(sys.stdout, "_oo_wrapped", False):
        return
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace",
                                  line_buffering=True)
    sys.stdout._oo_wrapped = True


def _trials_cell(row):
    """The trial name PLUS its registry identifier, in the same cell as the attribution.

    ⛔ A LABEL ON OUR OBJECT IS NOT AN IDENTITY -- THE REGISTRY IS. A row reading "ASPIRE, 2629
    women" attributes its numbers to a trial by a NAME WE WROTE. Correct today is not the same
    property as checkable: if a label anywhere in this object were flipped, every such cell would
    follow it silently, and a reader would have nothing to check it against.

    ⭐ AND THIS IS THE ANSWER TO A FINDING ABOUT THE JUDGES. Six blinded judges read the page and
    NONE checked a trial name against a registry -- which is precisely the work this page claims
    to make possible. It is hard to blame them while the identifier lives in the object and not
    in the cell. Putting the NCT beside the name makes the check one click rather than a search.
    """
    base = _cell(row.get("trials"))
    ids = row.get("trial_ids") or []
    ids = [i for i in ids if isinstance(i, str) and i.startswith("NCT")]
    if not ids:
        return base
    links = " ".join(
        "<a href=\"https://clinicaltrials.gov/study/%s\">%s</a>" % (_esc(i), _esc(i))
        for i in ids)
    return "%s<br><small>%s</small>" % (base, links)


def _effect_cell(row, tier):
    """⛔ A BORROWED NUMBER CARRIES ITS SOURCE IN ITS OWN CELL.

    The tier lived in a separate column and the reason in a paragraph below the table, so the
    figure travelled without either: a reader who copies "RR 0.97 (0.89 to 1.07)" out of this
    page takes an unattributed number with them, and an unsourced claim drifts to its strongest
    form. ⚠️ A CAVEAT THAT TRAILS A CONCLUSION DOES NOT TRAVEL -- it has to share the sentence.

    The gonorrhoea row was already correct because its reading is prose that names the
    comparator; the two rows carrying FIGURES were the ones that were not. So the rule is keyed
    to whether the cell carries a number, not to the tier alone.
    """
    v = _cell(row.get("effect"))
    if tier in BORROWED and _has_figure(row.get("effect")):
        return "%s &mdash; <span class=\"warn\">%s, not read at source</span>" % (
            v, _esc(_attribution(row)))
    return v


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
                   _cell(row.get("control")), _effect_cell(row, tier),
                   _trials_cell(row), cls, _esc(row.get("tier"))))
            printed += 1
        if body:
            out.append("<div class=\"scroll\"><table><tr><th>Outcome</th><th>Intervention</th>"
                       "<th>Control</th><th>Reading</th><th>Trials</th>"
                       "<th>Provenance tier</th></tr>" + "".join(body) + "</table></div>")
            out.append("<p><b>What the tiers mean.</b> %s</p>"
                       % " ".join("<i>%s</i> &mdash; %s." % (_esc(t), TIER_NOTE[t])
                                  for t in TIERS if t in tiers_used))
            # ⛔ THE `break` PRINTED ONE EXPLANATION AND SUPPRESSED THE REST. With one borrowed
            # row that is indistinguishable from printing them all; with five it means a reader
            # sees the provenance note for chlamydia and nothing for syphilis, gonorrhoea,
            # trichomoniasis or HPV -- four rows whose numbers are the comparator's, presented
            # as though only the first were. A coverage gap inside the very component that
            # exists to report provenance.
            if any(t in BORROWED for t in tiers_used):
                for row in rows:
                    if (isinstance(row, dict)
                            and str(row.get("tier") or "").strip().lower() in BORROWED
                            and row.get("why_the_primary_read_did_not_land")):
                        out.append("<p><b>%s.</b> %s</p>"
                                   % (_esc(row.get("outcome")),
                                      _esc(row["why_the_primary_read_did_not_land"])))

            # ⛔ A QUALIFICATION STORED AND NOT SHOWN IS A QUALIFICATION NOBODY CAN ACT ON, and
            # this component has now hidden one three times in a night: the retirement note,
            # the retrieval states, and the estimand note below. The fix is to stop adding a
            # renderer branch per field and print EVERY qualification a row carries, so the
            # next field to be typed is visible the moment it exists.
            #
            # ⚠️ THE ESTIMAND NOTE IS THE ONE THAT MATTERS HERE. A composite INCIDENCE RATE
            # PER PERSON-YEAR and a per-organism RISK RATIO differ on three axes at once, and
            # a reader shown both in one table will compare them unless told not to.
            QUALS = [
                ("estimand_note", "What this figure is, and is not"),
                ("prespecified_basis", "Prespecified?"),
                ("replaces", "What this replaces"),
                ("what_is_still_missing", "What is still missing"),
                ("retrieval_state", "Retrieval state"),
            ]
            quals = [(row, k, lab) for row in rows if isinstance(row, dict)
                     for k, lab in QUALS if row.get(k)]
            if quals:
                out.append("<h3>Qualifications carried by these rows</h3>")
                last = None
                for row, k, lab in quals:
                    if row.get("outcome") != last:
                        out.append("<p><b>%s</b></p>" % _esc(row.get("outcome")))
                        last = row.get("outcome")
                    out.append("<p><small><i>%s.</i> %s</small></p>"
                               % (_esc(lab), _esc(row.get(k))))

            # ⭐ THE PRIMARY-SOURCE READ, PRINTED PER ROW. The object now records, for each
            # borrowed outcome, that the primary trials WERE read and what state that read
            # returned. Held in the object and shown nowhere, it would be a fact nobody can
            # check -- which is the failure this project keeps finding in its own work.
            pr = [r for r in rows if isinstance(r, dict) and r.get("primary_read_2026_08_30")]
            if pr:
                out.append("<h3>What the primary trials say about these outcomes</h3>")
                out.append(
                    "<p>Each borrowed row below was checked against the trial reports "
                    "themselves. <b>Three states are distinguished, and they are not the same "
                    "thing:</b> <i>RETRIEVED_NO_VALUE</i> &mdash; the document was read and the "
                    "value is not in it; <i>NOT_RETRIEVABLE_OPEN_ACCESS</i> &mdash; the document "
                    "could not be read at all, which is a fact about this review's reach and "
                    "not about the trial; <i>RETRIEVED_QUALITATIVE_ONLY</i> &mdash; the trial "
                    "states a direction and gives no figure.</p>")
                for row in pr:
                    d = row["primary_read_2026_08_30"]
                    out.append(
                        "<p><b>%s.</b> %s<br><small>ASPIRE: <code>%s</code> &middot; "
                        "Ring Study: <code>%s</code>. %s</small></p>"
                        % (_esc(row.get("outcome")), _esc(d.get("finding")),
                           _esc(d.get("aspire_state")), _esc(d.get("ring_study_state")),
                           _esc(d.get("why_the_borrowed_figure_stands"))))
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
        # ⛔ A BORROWED ROW THAT CARRIES A FIGURE -- the case the in-cell attribution control
        # exists for. Without it that control passed VACUOUSLY: the fixture had borrowed rows and
        # rows with figures, and none that was both. An assertion that never meets its case is
        # indistinguishable from one that passes.
        {"outcome": "Chlamydia", "treatment": "not stated in what we hold",
         "control": "not stated in what we hold", "effect": "RR 0.97 (0.89 to 1.07)",
         "trials": "two trials", "tier": "prior-meta table (unverified)",
         "source": {"what": "a prior review, THE DESIGNATED COMPARATOR"},
         "why_the_primary_read_did_not_land":
             "the underlying counts are in a supplement this retrieval did not obtain"},
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


def plant_retrieval_states():
    """⭐ THE THREE RETRIEVAL STATES MUST STAY THREE, AND THEY MUST REACH THE PAGE.

    `RETRIEVED_NO_VALUE` (the document was read and the value is not in it) and
    `NOT_RETRIEVABLE_OPEN_ACCESS` (the document could not be read) are different facts about
    different things -- the first is about the evidence, the second about THIS REVIEW'S REACH.
    Collapsing them into "no data" reports our limitation as a property of the trial, which is
    the same error as a scan reporting its own reach as coverage.

    ⛔ AND BOTH WAYS. A row carrying the states must print them; a row carrying none must not
    invent one. The second half is what stops the component filling a silence with a state.
    """
    _utf8_once()
    base = {"outcome": "Chlamydia", "tier": "prior-meta table (unverified)",
            "effect": "RR 0.97 (0.89 to 1.07)",
            "why_the_primary_read_did_not_land": "the comparator is the only source held",
            "trials": "2 trials"}
    with_states = dict(base, primary_read_2026_08_30={
        "finding": "ASPIRE reports STIs only as a composite.",
        "aspire_state": "RETRIEVED_NO_VALUE",
        "ring_study_state": "NOT_RETRIEVABLE_OPEN_ACCESS",
        "why_the_borrowed_figure_stands": "no primary-source alternative is reachable"})
    def page(row):
        return _plain(render({"results": {"by_outcome": {"primary": {
            "other_outcomes": {"rows": [row]}}}}}))
    a, b = page(with_states), page(base)
    ok_a = ("RETRIEVED_NO_VALUE" in a and "NOT_RETRIEVABLE_OPEN_ACCESS" in a
            and a.count("RETRIEVED_NO_VALUE") != a.count("NOT_RETRIEVABLE_OPEN_ACCESS") - 99)
    ok_b = ("RETRIEVED_NO_VALUE" not in b and "NOT_RETRIEVABLE_OPEN_ACCESS" not in b)
    print("")
    print("PLANT -- the three retrieval states")
    print("   row WITH a primary read prints both states          %s   [%s]"
          % (ok_a, "PASS" if ok_a else "FAIL"))
    print("   row WITHOUT one invents neither                     %s   [%s]"
          % (ok_b, "PASS" if ok_b else "FAIL"))
    print("   ⚠️ the second is the one that matters: a component that")
    print("      defaults a missing state has turned silence into a finding.")
    assert ok_a, "a row carrying retrieval states did not print them"
    assert ok_b, "a row carrying no retrieval state had one invented for it"
    return 0


def plant():
    _utf8_once()
    html = render(MODEL_ANSWER)
    t = _plain(html)
    tiers = re.findall(r"<td class=\"tier[^\"]*\">([^<]*)</td>", html)
    print("MODEL ANSWER -- four rows, four tiers, three states of evidence.")
    assert tiers == ["trial report", "prior-meta table (unverified)",
                     "prior-meta table (unverified)", "absent by design", "absent"], tiers
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
    # ⭐ A BORROWED NUMBER MUST NAME ITS SOURCE IN THE CELL THAT CARRIES IT.
    # ⚠️ The tier column and the paragraph below the table are both FOOTNOTES: a reader who
    # copies the figure out takes neither with them. This control asserts the attribution shares
    # the cell with the number, and that a borrowed row WITHOUT a figure is not padded with one.
    h = render(MODEL_ANSWER)
    import re as _re
    cells = _re.findall(r"<tr>.*?</tr>", h, _re.S)
    figure_rows = [c for c in cells
                   if "prior-meta table (unverified)" in c and _re.search(r"\d", _plain(c))]
    print("REFUSAL CONTROL -- a borrowed FIGURE names its source in its own cell")
    ok = True
    for c in figure_rows:
        if "not read at source" not in c:
            ok = False
    print("   borrowed rows carrying a figure: %d   all attributed in-cell: %s   [%s]"
          % (len(figure_rows), ok, "PASS" if ok and figure_rows else "FAIL"))
    assert figure_rows and ok, "a borrowed figure travels without its source"
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
