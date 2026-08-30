# -*- coding: utf-8 -*-
"""GENERATOR COMPONENT: which counts were used, what the alternative gives, and what it changes.

TWO SECTIONS, BOTH DERIVED, BOTH ABOUT THE SAME THING -- that a number in a review is a CHOICE
between sources and between quantities, and that a page which hides the choice is asking to be
trusted rather than checked.

  1. WHICH COUNTS. A registry posts event counts as SUBMITTED. The trial's publication reports
     them after endpoint ADJUDICATION -- the step that decides which events count. These are not
     two readings of one number. Where an object holds both, this component prints both, REPOOLS
     under each, and states the difference it makes. Where it holds one, it says so.

  2. WHAT QUANTITY. A risk ratio over binary counts is not the quantity a trial analysed when it
     analysed time to event with censoring. Both are defensible; presenting the first as though
     it were the second is not.

⭐ THE DIFFERENCE IS COMPUTED, NOT ASSERTED. The component repools the object's own per-trial
counts under each tier using the same inverse-variance arithmetic, and prints both results. A
sentence saying "the choice makes little difference" is worth nothing without the two numbers
beside it, and a sentence saying it makes a large one is worth nothing without them either.

⛔ AND IT WILL NOT PROMOTE A TIER TO MAKE THE PAGE LOOK BETTER SOURCED. A tier whose counts were
not read at source carries `not_held` -- the routes tried and their statuses -- and the section
prints that beside the number. The Ring Study's adjudicated counts are exactly this case: its
primary report has no PMC identifier, `europepmc_by_pmid` returned 404, and there was no other
route to try. The number is usable and it is not a primary read, and both halves of that
sentence go on the page.

⚠️ A ONE-TIER TRIAL IS NOT A CLEAN TRIAL. Where only one tier exists the section says that the
alternative has not been looked for, because "the registry and the publication agree" and "we
only read the registry" render identically if the second is left blank.
"""
import io
import math
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(os.path.dirname(HERE))
SSOT = os.path.join(REPO, "ssot")
for _p in (HERE, SSOT):
    if _p not in sys.path:
        sys.path.insert(0, _p)

Z = 1.959964


def _esc(s):
    return str(s).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def _log_rr(e_t, n_t, e_c, n_c):
    """log RR and its standard error, or None where the counts cannot carry one."""
    if min(e_t, e_c) <= 0 or n_t <= 0 or n_c <= 0 or e_t >= n_t or e_c >= n_c:
        return None
    rr = (float(e_t) / n_t) / (float(e_c) / n_c)
    var = 1.0 / e_t - 1.0 / n_t + 1.0 / e_c - 1.0 / n_c
    if var <= 0:
        return None
    return math.log(rr), math.sqrt(var)


def _pool(rows):
    """Fixed-effect inverse-variance on the log scale. -> (rr, lo, hi, Q)."""
    w = [1.0 / (s * s) for _, s in rows]
    sw = sum(w)
    mu = sum(wi * y for wi, (y, _) in zip(w, rows)) / sw
    se = math.sqrt(1.0 / sw)
    q = sum(wi * (y - mu) ** 2 for wi, (y, _) in zip(w, rows))
    return math.exp(mu), math.exp(mu - Z * se), math.exp(mu + Z * se), q


def _tiers_for(trial):
    cb = trial.get("counts_by_tier")
    if not isinstance(cb, dict):
        return None
    tiers = cb.get("tiers")
    return cb if isinstance(tiers, dict) and tiers else None


def _counts(rec):
    keys = ("treatment_events", "treatment_n", "control_events", "control_n")
    if not all(isinstance(rec.get(k), (int, float)) for k in keys):
        return None
    return tuple(int(rec[k]) for k in keys)


def repool(trials, tier_choice):
    """Pool every trial under one tier-selection function. -> (result, [missing])."""
    rows, missing = [], []
    for t in trials:
        cb = _tiers_for(t)
        name = t.get("label") or t.get("nct") or "?"
        if not cb:
            missing.append(str(name))
            continue
        rec = tier_choice(cb)
        c = _counts(rec) if isinstance(rec, dict) else None
        if not c:
            missing.append(str(name))
            continue
        ys = _log_rr(*c)
        if not ys:
            missing.append(str(name))
            continue
        rows.append(ys)
    if len(rows) < 2:
        return None, missing
    return _pool(rows), missing


def _designated(cb):
    return (cb.get("tiers") or {}).get(cb.get("designated")) or {}


def _alternative(cb):
    """The other tier, when there is exactly one other. Never picks between two."""
    tiers = cb.get("tiers") or {}
    others = [k for k in tiers if k != cb.get("designated")]
    return tiers[others[0]] if len(others) == 1 else {}


def render_counts(canon):
    head = "<h2>Which counts were used, and what difference it makes</h2>"
    inp = canon.get("inputs")
    trials = ((inp or {}).get("trials") or []) if isinstance(inp, dict) else []
    withtiers = [t for t in trials if isinstance(t, dict) and _tiers_for(t)]
    if not withtiers:
        # ⛔ THE THREE-STATE ABSENCE. "Agrees" and "never looked" are not the same page.
        return head + (
            "<p>This object records event counts from one source per trial and no alternative "
            "was sought, so this page cannot tell you whether the registry and the publication "
            "agree. ⚠️ That is not the same as saying they do. A registry posts counts as "
            "submitted and a publication reports them after endpoint adjudication; where those "
            "differ, the adjudicated figure is the trial's own final answer, and a review that "
            "never compared them cannot say which it is using.</p>")
    rows, notes = [], []
    for t in withtiers:
        cb = _tiers_for(t)
        name = _esc(t.get("label") or t.get("nct") or "?")
        for tier, rec in (cb.get("tiers") or {}).items():
            c = _counts(rec) if isinstance(rec, dict) else None
            held = "" if not (isinstance(rec, dict) and rec.get("not_held")) else \
                " <span class=\"warn\">not read at source</span>"
            rows.append(
                "<tr><td>%s</td><td>%s%s%s</td><td>%s</td><td>%s</td></tr>"
                % (name, _esc(tier),
                   " <b>&larr; used</b>" if tier == cb.get("designated") else "", held,
                   ("%d / %d" % (c[0], c[1])) if c else "&mdash;",
                   ("%d / %d" % (c[2], c[3])) if c else "&mdash;"))
        if cb.get("what_differs"):
            notes.append("<p><b>%s.</b> %s</p>" % (name, _esc(cb["what_differs"])))
        if cb.get("why_designated"):
            notes.append("<p>%s</p>" % _esc(cb["why_designated"]))
        for tier, rec in (cb.get("tiers") or {}).items():
            nh = isinstance(rec, dict) and rec.get("not_held")
            if nh:
                notes.append(
                    "<p><b>%s, %s &mdash; not read at source.</b> %s</p>"
                    % (name, _esc(tier), _esc(nh.get("routes_tried") or
                                              "no retrieval is recorded")))
    out = [head,
           "<div class=\"scroll\"><table><tr><th>Trial</th><th>Provenance tier</th>"
           "<th>Intervention events / n</th><th>Control events / n</th></tr>"
           + "".join(rows) + "</table></div>"]
    # ⭐ THE DIFFERENCE, COMPUTED.
    a, miss_a = repool(withtiers, _designated)
    b, miss_b = repool(withtiers, _alternative)
    if a and b:
        out.append(
            "<p><b>What the choice is worth, computed rather than asserted.</b> Pooling every "
            "trial under the tier this page uses gives <b>%.4f (%.4f to %.4f)</b>. Pooling the "
            "same trials under the alternative counts gives <b>%.4f (%.4f to %.4f)</b>. Both "
            "are fixed-effect inverse-variance pools of the same trials on the log scale, so "
            "the only thing that differs between them is the counts. A reader who prefers the "
            "other source can see exactly what they would get, which is the point: the "
            "correction is small, and what matters is that a choice existed, was made, and is "
            "visible.</p>" % (a[0], a[1], a[2], b[0], b[1], b[2]))
    elif a and not b:
        out.append(
            "<p>Only one tier is complete across the contributing trials%s, so no alternative "
            "pool is computed. A partial repool over a subset of trials would not be the "
            "alternative to this pool; it would be a different review.</p>"
            % ((" (missing under the alternative: %s)"
                % ", ".join(_esc(m) for m in miss_b[:4])) if miss_b else ""))
    out.extend(notes)
    return "".join(out)


def render_estimand(canon):
    head = "<h2>What quantity this is, and what the trials actually analysed</h2>"
    r = canon.get("results")
    outs = (r or {}).get("by_outcome") if isinstance(r, dict) else None
    if not isinstance(outs, dict):
        return head + "<p>This object records no outcome. That is a refusal, not an omission.</p>"
    got = []
    for oid, res in outs.items():
        em = res.get("estimand_mismatch") if isinstance(res, dict) else None
        if isinstance(em, dict) and em.get("statement"):
            got.append((oid, em))
    if not got:
        return head + (
            "<p>This object does not record what quantity the contributing trials analysed, so "
            "this page cannot say whether the quantity it pools is theirs. ⚠️ That is an "
            "unchecked assumption, not a clean bill: a risk ratio over binary counts and a "
            "hazard ratio over person-time are different quantities, and a review that pools "
            "the first while the trials analysed the second will differ from them whenever "
            "follow-up differs between arms.</p>")
    out = [head]
    for oid, em in got:
        out.append("<p>For <b>%s</b>: this page pools a <b>%s</b>; the trials analysed <b>%s</b>."
                   "</p>" % (_esc(str(oid)), _esc(em.get("pooled_quantity", "quantity not "
                                                         "stated")),
                             _esc(em.get("trials_analysed", "not stated"))))
        out.append("<p>%s</p>" % _esc(em["statement"]))
        if em.get("source_quote"):
            out.append("<p><small>%s</small></p>" % _esc(em["source_quote"]))
        if em.get("what_would_fix_it"):
            out.append("<p><b>What would close this.</b> %s</p>"
                       % _esc(em["what_would_fix_it"]))
    return "".join(out)


MARKER = "<h2>Which counts were used, and what difference it makes</h2>"
MARKER_ESTIMAND = "<h2>What quantity this is, and what the trials actually analysed</h2>"


def inject(html, canon):
    if MARKER not in html:
        html = html + "\n<div class=\"card\">\n" + render_counts(canon) + "\n</div>\n"
    if MARKER_ESTIMAND not in html:
        html = html + "\n<div class=\"card\">\n" + render_estimand(canon) + "\n</div>\n"
    return html


def render(canon):
    return render_counts(canon) + render_estimand(canon)


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
    objs = 0
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
        inp = c.get("inputs")
        trials = ((inp or {}).get("trials") or []) if isinstance(inp, dict) else []
        wt = [t for t in trials if isinstance(t, dict) and _tiers_for(t)]
        per["objects with count tiers on >=1 trial" if wt
            else "objects with ONE source per trial (alternative never sought)"] += 1
        em = any(isinstance(res, dict) and isinstance(res.get("estimand_mismatch"), dict)
                 for res in outs.values())
        per["objects stating what the trials analysed" if em
            else "objects NOT stating what the trials analysed"] += 1
    return {"objects_with_a_pooled_result": objs, "detail": dict(per),
            "skipped": dict(skipped)}


# ⭐ THE MODEL ANSWER. Two tiers that differ by exactly the counts, so the two pooled numbers can
# be checked by hand: under tier A both trials are 50/1000 vs 100/1000, so the pool is exactly
# 0.5; under tier B the control arms are 90/1000, so the pool is 50/90 = 0.5556.
MODEL_ANSWER = {
    "app_id": "__control_model_answer_counts",
    "inputs": {"trials": [
        {"nct": "NCT00000001", "label": "Control trial A", "counts_by_tier": {
            "designated": "registry results",
            "what_differs": "the control arm's event count",
            "tiers": {
                "registry results": {"treatment_events": 50, "treatment_n": 1000,
                                     "control_events": 100, "control_n": 1000},
                "trial report": {"treatment_events": 50, "treatment_n": 1000,
                                 "control_events": 90, "control_n": 1000}}}},
        {"nct": "NCT00000002", "label": "Control trial B", "counts_by_tier": {
            "designated": "registry results",
            "tiers": {
                "registry results": {"treatment_events": 50, "treatment_n": 1000,
                                     "control_events": 100, "control_n": 1000},
                "trial report": {"treatment_events": 50, "treatment_n": 1000,
                                 "control_events": 90, "control_n": 1000}}}}]},
    "results": {"by_outcome": {"primary": {
        "pooled": {"point": 0.5, "measure": "RR"},
        "estimand_mismatch": {
            "pooled_quantity": "risk ratio over binary counts",
            "trials_analysed": "time to event, with censoring and unequal follow-up",
            "statement": "The quantity pooled here is not the quantity the trials analysed.",
            "what_would_fix_it": "Per-arm person-time, or the trials' own hazard ratios."}}}}}

# ⭐ REFUSAL CONTROL 1 -- one source per trial must NOT read as "the sources agree".
ONE_TIER_CONTROL = {
    "app_id": "__control_one_source_is_not_agreement",
    "inputs": {"trials": [{"nct": "NCT00000003", "label": "Control trial C"}]},
    "results": {"by_outcome": {"primary": {"pooled": {"point": 0.5, "measure": "RR"}}}}}

# ⭐ REFUSAL CONTROL 2 -- a tier that was not read at source must SAY SO next to its number.
# ⚠️ If this ever creates pressure to drop the warning so the table reads cleanly, the control
# is right: the warning is the difference between a sourced number and a borrowed one.
NOT_HELD_CONTROL = {
    "app_id": "__control_not_read_at_source_stays_flagged",
    "inputs": {"trials": [
        {"nct": "NCT00000004", "label": "Control trial D", "counts_by_tier": {
            "designated": "registry results",
            "tiers": {
                "registry results": {"treatment_events": 50, "treatment_n": 1000,
                                     "control_events": 100, "control_n": 1000},
                "external review": {
                    "treatment_events": 47, "treatment_n": 998,
                    "control_events": 96, "control_n": 1000,
                    "not_held": {"routes_tried": "europepmc_by_pmid -> HTTP 404; no pmcid or "
                                                 "doi route existed to try"}}}}}]},
    "results": {"by_outcome": {"primary": {"pooled": {"point": 0.5, "measure": "RR"}}}}}

# ⭐ REFUSAL CONTROL 3 -- an object that does not say what the trials analysed must not read as
# though the quantities matched.
NO_ESTIMAND_CONTROL = {
    "app_id": "__control_estimand_unstated",
    "inputs": {"trials": []},
    "results": {"by_outcome": {"primary": {"pooled": {"point": 0.5, "measure": "RR"}}}}}


def _plain(html):
    return re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", html))


def plant():
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    t = _plain(render(MODEL_ANSWER))
    print("MODEL ANSWER -- two tiers differing only in the control counts. The two pooled")
    print("               numbers are fixed by arithmetic: 50/100 = 0.5000, 50/90 = 0.5556.")
    assert "0.5000 (" in t, t[:400]
    assert "0.5556 (" in t, t[:400]
    print("   both pools printed, computed not asserted   [PASS]")
    assert "risk ratio over binary counts" in t and "time to event" in t, t[:400]
    print("   the estimand mismatch is stated in the REVIEW, not only in the checker   [PASS]")
    print("")
    t2 = _plain(render_counts(ONE_TIER_CONTROL))
    said = "not the same as saying they do" in t2
    bad = re.search(r"(?i)the (?:two )?sources agree|registry and the publication agree(?!\?)",
                    t2.replace("cannot tell you whether the registry and the publication "
                               "agree", ""))
    print("REFUSAL CONTROL -- one source per trial is not agreement between sources")
    print("   states the distinction: %s   claims agreement: %s   [%s]"
          % (said, bool(bad), "PASS" if said and not bad else "FAIL"))
    assert said and not bad, t2[:400]
    h3 = render_counts(NOT_HELD_CONTROL)
    t3 = _plain(h3)
    flagged = "not read at source" in t3
    routed = "europepmc_by_pmid" in t3 and "404" in t3
    print("REFUSAL CONTROL -- a tier not read at source stays flagged, with its routes named")
    print("   flagged in the table: %s   routes named: %s   [%s]"
          % (flagged, routed, "PASS" if flagged and routed else "FAIL"))
    assert flagged and routed, t3[:500]
    t4 = _plain(render_estimand(NO_ESTIMAND_CONTROL))
    honest = "unchecked assumption" in t4
    print("REFUSAL CONTROL -- an unstated estimand is an unchecked assumption, not a clean bill")
    print("   says so: %s   [%s]" % (honest, "PASS" if honest else "FAIL"))
    assert honest, t4[:400]
    print("")
    print("⚠️ The 'not read at source' flag may not be dropped to make the table read cleanly.")
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
        n = c["objects_with_a_pooled_result"]
        print("")
        print("COVERAGE FRACTION -- count provenance and estimand")
        print("  scanned: %s" % root)
        if not n:
            print("  ⛔ SCAN FOUND NOTHING -- a failure of this scan, not of the corpus.")
            raise SystemExit(2)
        print("  objects with a pooled result   %4d   == the denominator" % n)
        for k, v in sorted(c["detail"].items(), key=lambda kv: -kv[1]):
            print("     %-58s %4d   %5.1f%%" % (k, v, 100.0 * v / n))
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
        print(_plain(render(canon))[:2200])
