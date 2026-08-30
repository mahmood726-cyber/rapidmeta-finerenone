# -*- coding: utf-8 -*-
"""GENERATOR COMPONENT: the GRADE certainty profile, domain by domain, with its reasons.

⭐ THIS IS THE ONE AXIS THE COMPARATOR WON, AND THE DATA WAS ALREADY IN THE OBJECT.

All six blinded judges named formal GRADE certainty for our own estimate as something the
Cochrane review had and we did not. Measured against the two pages: the hand-built pilot
contains the string "GRADE" ZERO times. The object it was built from carries a complete
profile -- starting certainty, five domains, a move and a verbatim reason for each, a summary,
and an explicit note that no domain was rated UP. ⚠️ The review did the assessment and the page
did not print it. That is not a methods gap; it is a rendering gap, and it cost us the only
axis we lost.

⛔ THE FINAL RATING IS RECOMPUTED FROM THE STEPS, AND A RATING THAT DOES NOT FOLLOW FROM ITS
OWN REASONS IS REFUSED. Starting certainty minus the declared downgrades must equal the stored
certainty. If it does not, the component prints the disagreement and withholds the rating
rather than picking one -- a certainty rating whose own domain table contradicts it is worse
than none, because it carries the authority of a formal method while disagreeing with it.

⛔ NOT ASSESSABLE IS NEVER "NO DOWNGRADE". Publication bias at k = 2 cannot be assessed: a
funnel plot has essentially no power there. Rendering that as "no downgrade" tells a reader the
domain was checked and found clean. The three states are DOWNGRADED, NO DOWNGRADE, and NOT
ASSESSABLE, and the third is printed as itself.

⭐ AND A DOWNGRADE THAT WAS WARRANTED BUT NOT APPLIED IS THE MOST INFORMATIVE ROW IN THE TABLE.
This object carries one: at k = 2 the modified Hartung-Knapp interval includes no difference
where the unadjusted one excludes it, so an imprecision downgrade is warranted -- and it is not
applied, because at k = 2 the t multiplier is 12.71 and only a very large effect survives that
adjustment at all, which makes the adjusted interval weak evidence in either direction. The
component prints the disagreement instead of resolving it silently. Naming what we chose not to
do, and why, is the part nobody else prints.
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

LEVELS = ["VERY LOW", "LOW", "MODERATE", "HIGH"]

# A move is a downgrade only when it says by how much. "down 1 level(s)" / "down 2 levels".
DOWN = re.compile(r"down\s+(\d+)\s*level", re.I)
NOT_ASSESSABLE = re.compile(r"not assessable|no rating applied|cannot be assessed", re.I)
NOT_APPLIED = re.compile(r"not applied|warranted and not applied", re.I)
UP = re.compile(r"\bup\s+(\d+)\s*level", re.I)


def _esc(s):
    return str(s).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def step_state(move):
    """-> (state, levels_moved). Three states, never two.

    ⛔ ORDER MATTERS. `not applied` is tested BEFORE the downgrade pattern, because the string
    that records a warranted-but-withheld downgrade contains "down 1 level" too -- and reading
    it as an applied downgrade would make the arithmetic below disagree with a rating that is
    in fact correct.
    """
    m = str(move or "")
    if NOT_ASSESSABLE.search(m):
        return "NOT ASSESSABLE", 0
    if NOT_APPLIED.search(m):
        return "warranted, NOT applied", 0
    d = DOWN.search(m)
    if d:
        return "downgraded", -int(d.group(1))
    u = UP.search(m)
    if u:
        return "rated up", int(u.group(1))
    return "no downgrade", 0


def recompute(block):
    """Starting certainty plus the declared moves. -> (level or None, moves, why)."""
    start = str(block.get("starting_certainty") or "").strip().upper()
    if start not in LEVELS:
        return None, 0, "the object does not record a starting certainty"
    i = LEVELS.index(start)
    moved = 0
    for st in (block.get("steps") or []):
        if not isinstance(st, dict):
            continue
        _state, delta = step_state(st.get("move"))
        moved += delta
    j = max(0, min(len(LEVELS) - 1, i + moved))
    return LEVELS[j], moved, ""


def render(canon):
    head = "<h2>How certain this is, and why &mdash; the certainty profile</h2>"
    g = canon.get("grade")
    outs = (g or {}).get("by_outcome") if isinstance(g, dict) else None
    if not isinstance(outs, dict) or not outs:
        # ⛔ THE ABSENCE IS PRINTED. A page with no certainty section reads as a page whose
        # evidence needed no qualification.
        return head + (
            "<p>This review records no formal certainty assessment, so none is shown. ⚠️ That "
            "is a gap in this review, not a property of the evidence: a reader comparing it "
            "with a guideline or a Cochrane review will find a GRADE rating there and nothing "
            "to set against it here.</p>")
    out = [head]
    if g.get("approach"):
        out.append("<p><small>%s%s</small></p>"
                   % (_esc(g["approach"]),
                      (" Assessed %s." % _esc(g["assessed_utc"])) if g.get("assessed_utc")
                      else ""))
    for oid, blk in outs.items():
        if not isinstance(blk, dict):
            continue
        name = _esc(str(oid)[:60])
        stored = str(blk.get("certainty") or "").strip().upper()
        derived, moved, why = recompute(blk)
        rows = []
        for st in (blk.get("steps") or []):
            if not isinstance(st, dict):
                continue
            state, delta = step_state(st.get("move"))
            cls = {"downgraded": "warn", "NOT ASSESSABLE": "muted",
                   "warranted, NOT applied": "stop", "rated up": "good"}.get(state, "good")
            rows.append(
                "<tr><td>%s</td><td class=\"cert-state %s\">%s</td><td>%s</td><td>%s</td></tr>"
                % (_esc(str(st.get("domain", "?")).replace("_", " ")), cls, state,
                   ("%+d" % delta) if delta else "&mdash;", _esc(st.get("reason", ""))))
        out.append("<h3>%s%s</h3>" % (name, (" &mdash; k = %s" % _esc(blk["k"]))
                                      if blk.get("k") is not None else ""))
        # ⛔ THE RATING IS PRINTED ONLY IF IT FOLLOWS FROM THE TABLE ABOVE IT.
        if derived is None:
            out.append("<p><b>No rating is shown.</b> %s, so the certainty cannot be derived "
                       "from its own steps and a stored value would be an assertion rather "
                       "than a result.</p>" % _esc(why))
        elif stored and stored != derived:
            out.append(
                "<p><b>No rating is shown, and this is a finding.</b> The object stores "
                "<b>%s</b>, but starting from %s and applying the declared moves (%+d) gives "
                "<b>%s</b>. A certainty rating that disagrees with its own domain table is "
                "worse than none: it carries the authority of a formal method while "
                "contradicting it. Both numbers are printed here rather than one being "
                "chosen.</p>"
                % (_esc(stored), _esc(blk.get("starting_certainty")), moved, _esc(derived)))
        else:
            out.append(
                "<p>Starting at <b>%s</b> for randomised evidence and applying the moves below "
                "(%+d), the certainty in this estimate is <b>%s</b>. The rating is recomputed "
                "from the table rather than stored beside it, so a table and a rating cannot "
                "drift apart.</p>"
                % (_esc(blk.get("starting_certainty")), moved, _esc(derived)))
        if rows:
            out.append("<div class=\"scroll\"><table><tr><th>Domain</th><th>Reading</th>"
                       "<th>Levels</th><th>Reason</th></tr>" + "".join(rows) + "</table></div>")
        else:
            out.append("<p>No domain assessment is recorded for this outcome, so the rating "
                       "above rests on nothing this page can show you.</p>")
        na = [st for st in (blk.get("steps") or [])
              if isinstance(st, dict) and step_state(st.get("move"))[0] == "NOT ASSESSABLE"]
        if na:
            out.append(
                "<p><b>Not assessable is not the same as no concern.</b> %s could not be "
                "assessed here, so %s neither raised nor lowered the rating. A domain that was "
                "never checkable is shown as itself rather than folded into &ldquo;no "
                "downgrade&rdquo;, which would tell you it had been checked and found "
                "clean.</p>"
                % (_esc(", ".join(str(s.get("domain", "?")).replace("_", " ") for s in na)),
                   "it" if len(na) == 1 else "they"))
        withheld = [st for st in (blk.get("steps") or [])
                    if isinstance(st, dict)
                    and step_state(st.get("move"))[0] == "warranted, NOT applied"]
        if withheld:
            out.append(
                "<p><b>A downgrade was warranted and deliberately not applied.</b> It is listed "
                "above with its reason. The rating would be one level lower had it been "
                "applied, and a reader who disagrees with the judgement can see exactly which "
                "one it was and move it themselves.</p>")
        if blk.get("rating_up_not_applied"):
            out.append("<p>%s</p>" % _esc(blk["rating_up_not_applied"]))
        if blk.get("summary"):
            out.append("<p>%s</p>" % _esc(blk["summary"]))
    return "".join(out)


MARKER = "<h2>How certain this is, and why &mdash; the certainty profile</h2>"


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
        g = c.get("grade")
        gouts = (g or {}).get("by_outcome") if isinstance(g, dict) else None
        if not isinstance(gouts, dict) or not gouts:
            per["no certainty assessment recorded"] += 1
            continue
        for _oid, blk in gouts.items():
            if not isinstance(blk, dict):
                continue
            derived, _m, _w = recompute(blk)
            stored = str(blk.get("certainty") or "").strip().upper()
            if derived is None:
                per["refused: no starting certainty"] += 1
            elif stored and stored != derived:
                per["REFUSED: the stored rating does not follow from its steps"] += 1
            else:
                per["RENDERED: rating recomputed and agrees"] += 1
    return {"objects_with_a_pooled_result": objs, "detail": dict(per),
            "total": sum(per.values()),
            "skipped": dict(skipped)}


# ⭐ THE MODEL ANSWER, keyed to GRADE's own arithmetic rather than to this file: HIGH, down one
# for risk of bias, down one for indirectness, publication bias not assessable, and one
# warranted downgrade withheld => LOW. Anyone can check that on paper.
MODEL_ANSWER = {
    "grade": {"approach": "GRADE, Cochrane Handbook chapter 14.", "assessed_utc": "2026-08-21",
              "by_outcome": {"primary": {
                  "k": 2, "starting_certainty": "HIGH", "certainty": "LOW",
                  "steps": [
                      {"domain": "risk_of_bias", "move": "HIGH to MODERATE, down 1 level(s)",
                       "reason": "Both results are SOME_CONCERNS."},
                      {"domain": "inconsistency", "move": "no downgrade",
                       "reason": "tau-squared is exactly zero."},
                      {"domain": "indirectness", "move": "MODERATE to LOW, down 1 level(s)",
                       "reason": "Both registrations set a minimum age of 18."},
                      {"domain": "imprecision",
                       "move": "LOW to VERY LOW -- WARRANTED AND NOT APPLIED, see reason",
                       "reason": "At k = 2 the t multiplier is 12.71."},
                      {"domain": "publication_bias",
                       "move": "NOT ASSESSABLE -- no rating applied",
                       "reason": "k = 2; a funnel plot has essentially no power."}],
                  "rating_up_not_applied": "No domain is rated up.",
                  "summary": "LOW certainty."}}}}

# ⭐ REFUSAL CONTROL 1 -- a stored rating that does not follow from its own steps.
# ⚠️ If this ever creates pressure to print the stored value anyway, the control is right.
INCONSISTENT_CONTROL = {
    "grade": {"by_outcome": {"primary": {
        "starting_certainty": "HIGH", "certainty": "HIGH",
        "steps": [{"domain": "risk_of_bias", "move": "HIGH to MODERATE, down 1 level(s)",
                   "reason": "x"}]}}}}

# ⭐ REFUSAL CONTROL 2 -- no assessment at all must be stated, not rendered as an empty table.
NO_GRADE_CONTROL = {"results": {"by_outcome": {"primary": {"pooled": {"point": 0.7}}}}}

# ⭐ REFUSAL CONTROL 3 -- NOT ASSESSABLE must never render as "no downgrade".
NOT_ASSESSABLE_CONTROL = {
    "grade": {"by_outcome": {"primary": {
        "starting_certainty": "HIGH", "certainty": "HIGH",
        "steps": [{"domain": "publication_bias",
                   "move": "NOT ASSESSABLE -- no rating applied", "reason": "k = 2."}]}}}}


def _plain(html):
    return re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", html))


def plant():
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    derived, moved, _w = recompute(MODEL_ANSWER["grade"]["by_outcome"]["primary"])
    print("MODEL ANSWER -- HIGH, two applied downgrades, one withheld, one not assessable.")
    print("               GRADE's own arithmetic gives LOW; this file does not get a vote.")
    assert derived == "LOW" and moved == -2, (derived, moved)
    print("   recomputed %s (%+d)   [PASS]" % (derived, moved))
    html = render(MODEL_ANSWER)
    t = _plain(html)
    states = re.findall(r"<td class=\"cert-state [^\"]*\">([^<]*)</td>", html)
    assert states == ["downgraded", "no downgrade", "downgraded", "warranted, NOT applied",
                      "NOT ASSESSABLE"], states
    print("   domain readings: %s   [PASS]" % "; ".join(states))
    assert "the certainty in this estimate is" in t and "LOW" in t, t[:400]
    print("   the rating is printed because it follows from the table   [PASS]")
    assert "warranted and deliberately not applied" in t, t[:600]
    print("   the withheld downgrade is disclosed, not hidden   [PASS]")
    print("")
    t2 = _plain(render(INCONSISTENT_CONTROL))
    said = "does not follow from its own steps" in t2 or "disagrees with its own domain" in t2
    # ⛔ AND IT MUST NOT HAVE PRINTED THE RATING ANYWAY.
    asserted = "the certainty in this estimate is" in t2
    print("REFUSAL CONTROL -- a rating that does not follow from its own steps")
    print("   states the disagreement: %s   withholds the rating: %s   [%s]"
          % (said, not asserted, "PASS" if said and not asserted else "FAIL"))
    assert said and not asserted, t2[:400]
    t3 = _plain(render(NO_GRADE_CONTROL))
    honest = "gap in this review" in t3
    print("REFUSAL CONTROL -- no assessment is a gap in the review, stated")
    print("   says so: %s   [%s]" % (honest, "PASS" if honest else "FAIL"))
    assert honest, t3[:400]
    h4 = render(NOT_ASSESSABLE_CONTROL)
    t4 = _plain(h4)
    st4 = re.findall(r"<td class=\"cert-state [^\"]*\">([^<]*)</td>", h4)
    print("REFUSAL CONTROL -- not assessable is never rendered as no downgrade")
    print("   reading: %s   explained: %s   [%s]"
          % (st4, "not the same as no concern" in t4,
             "PASS" if st4 == ["NOT ASSESSABLE"] and "not the same as no concern" in t4
             else "FAIL"))
    assert st4 == ["NOT ASSESSABLE"] and "not the same as no concern" in t4, (st4, t4[:300])
    print("")
    print("⚠️ The recomputation may not be softened into 'approximately agrees'. A rating that")
    print("   contradicts its own domain table is a finding, not a rounding difference.")
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
        print("COVERAGE FRACTION -- certainty profile")
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
