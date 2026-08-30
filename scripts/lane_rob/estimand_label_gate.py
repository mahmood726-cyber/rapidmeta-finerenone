# -*- coding: utf-8 -*-
"""REFUSAL: a number computed from per-trial rows must carry the label of the rows it read.

⛔ THE REAL INSTANCE, CAUGHT BY HAND AND NOT BY ANY CHECK. Rewriting the pilot's interval
paragraph, I was one paste away from printing 0.703 (0.566 to 0.873) as the page's interval. The
component had computed it honestly -- from the object's per-trial rows, which are the REGISTRY
AS SUBMITTED counts. The page's headline is the ADJUDICATED pool, 0.7127. The two differ because
endpoint adjudication decides which seroconversions count, and the page devotes an entire section
to that difference.

⇒ Nothing in the arithmetic was wrong. Nothing in the rendering was wrong. The number would have
been published under a label that was not its own, on the one page that explains why the labels
are not interchangeable.

A SCHEMA THAT ENCODES A METHODOLOGICAL ASSUMPTION ENFORCES IT. The precedent in this repository
is the field-name contract that turned a silent `unknown_ratio` into a KeyError: a check nobody
had to remember caught what no reader did.

⚠️ COVERAGE IS REPORTED, NOT ASSUMED. This can only compare where BOTH sides carry a label. An
outcome whose pooled block declares no count source is not a pass -- it is outside the check's
reach, and it is counted separately and named. A baseline of zero findings over an unstated
denominator is a statement about reach.
"""
import io
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
os.chdir(os.path.dirname(os.path.dirname(HERE)))

# Grounded in what the corpus actually writes, not invented. Two carriers exist:
#   provenance  on per-trial rows   -- "REGISTRY -- ClinicalTrials.gov posted results"
#   estimand_id on per-trial rows   -- "<outcome>-estimand"
REGISTRY = re.compile(r"\bregistr(?:y|ies)\b|clinicaltrials\.gov|as submitted|as posted", re.I)
ADJUDICATED = re.compile(r"\badjudicat", re.I)
PUBLICATION = re.compile(r"\bpublication\b|\bjournal\b|primary report|full text", re.I)


def _count_source(text):
    if not text:
        return None
    if ADJUDICATED.search(text):
        return "adjudicated"
    if REGISTRY.search(text):
        return "registry as submitted"
    if PUBLICATION.search(text):
        return "publication"
    return None


def rows_label(per_trial):
    """The label the CONTRIBUTING ROWS carry. A mixture is itself a finding, not a tie-break."""
    srcs, eids = set(), set()
    for r in per_trial or []:
        if not isinstance(r, dict):
            continue
        s = _count_source(" ".join(str(r.get(k) or "") for k in
                                   ("provenance", "counts_source", "source", "how", "derivation")))
        if s:
            srcs.add(s)
        if r.get("estimand_id"):
            eids.add(str(r["estimand_id"]))
    return {"count_source": (sorted(srcs)[0] if len(srcs) == 1 else
                             ("MIXED:" + "|".join(sorted(srcs)) if srcs else None)),
            "estimand_ids": sorted(eids)}


def pooled_label(pooled, outcome_id, outcome_block):
    """The label the POOLED number is published under, from the object rather than inferred."""
    p = pooled or {}
    src = _count_source(" ".join(str(p.get(k) or "") for k in
                                 ("counts_source", "source", "provenance", "basis", "card_note")))
    eid = p.get("estimand_id") or (outcome_block or {}).get("estimand_id")
    return {"count_source": src, "estimand_ids": [str(eid)] if eid else []}


class LabelMismatch(Exception):
    pass


def check_outcome(oid, block):
    """(verdict, detail). verdict in COMPARED_OK / MISMATCH / NOT_COMPARABLE."""
    pooled = block.get("pooled") or {}
    if pooled.get("withdrawn"):
        return "NOT_COMPARABLE", "the pool is withdrawn; there is no published number to label"
    rl = rows_label(block.get("per_trial"))
    pl = pooled_label(pooled, oid, block)
    if rl["count_source"] and str(rl["count_source"]).startswith("MIXED:"):
        return "MISMATCH", ("the contributing rows do not share one count source (%s); a pooled "
                            "number cannot carry a label none of its inputs agree on"
                            % rl["count_source"][6:])
    both_src = rl["count_source"] and pl["count_source"]
    both_eid = rl["estimand_ids"] and pl["estimand_ids"]
    if not (both_src or both_eid):
        return "NOT_COMPARABLE", ("no label on %s side"
                                  % ("the pooled" if rl["count_source"] or rl["estimand_ids"]
                                     else "either"))
    if both_src and rl["count_source"] != pl["count_source"]:
        return "MISMATCH", ("rows are %r; the pooled number is published as %r"
                            % (rl["count_source"], pl["count_source"]))
    if both_eid and set(rl["estimand_ids"]) != set(pl["estimand_ids"]):
        return "MISMATCH", ("rows carry estimand %s; the pooled number is published under %s"
                            % (rl["estimand_ids"], pl["estimand_ids"]))
    return "COMPARED_OK", "labels agree (%s)" % (rl["count_source"] or rl["estimand_ids"])


def enforce(canon, where="<object>"):
    """Build-time refusal. Raises LabelMismatch on any mismatch; silent otherwise."""
    bad = []
    for oid, block in (((canon.get("results") or {}).get("by_outcome")) or {}).items():
        v, d = check_outcome(oid, block)
        if v == "MISMATCH":
            bad.append("%s: %s" % (oid, d))
    if bad:
        raise LabelMismatch(
            "BUILD REFUSED at %s: a pooled number would be published under a label that is not "
            "its own.\n  %s\nThis is the near-swap that nearly put the registry-as-submitted "
            "0.703 on a page whose headline is the adjudicated 0.713." % (where, "\n  ".join(bad)))


# --------------------------------------------------------------------- controls
def _controls():
    """Both directions. A refusal that cannot publish is as useless as one that cannot refuse."""
    out = []
    # NEGATIVE CONTROL -- the near-swap itself, in miniature. MUST refuse.
    swap = {"results": {"by_outcome": {"primary": {
        "per_trial": [{"provenance": "REGISTRY -- ClinicalTrials.gov posted results",
                       "point": 0.67}, {"provenance": "REGISTRY -- posted results", "point": 0.73}],
        "pooled": {"point": 0.7127, "counts_source": "adjudicated publications"}}}}}
    try:
        enforce(swap, "control:near-swap")
        out.append(("negative: rows registry, headline adjudicated", "PUBLISHED", "REFUSE"))
    except LabelMismatch:
        out.append(("negative: rows registry, headline adjudicated", "REFUSED", "REFUSE"))
    # POSITIVE CONTROL -- correctly matched. MUST publish, or the refusal is vacuous.
    ok = {"results": {"by_outcome": {"primary": {
        "per_trial": [{"provenance": "REGISTRY -- ClinicalTrials.gov posted results"},
                      {"provenance": "REGISTRY -- posted results"}],
        "pooled": {"point": 0.7038, "counts_source": "registry as submitted"}}}}}
    try:
        enforce(ok, "control:matched")
        out.append(("positive: rows registry, headline registry", "PUBLISHED", "PUBLISH"))
    except LabelMismatch:
        out.append(("positive: rows registry, headline registry", "REFUSED", "PUBLISH"))
    # POSITIVE CONTROL 2 -- estimand_id agreement must also publish.
    eid = {"results": {"by_outcome": {"o1": {
        "per_trial": [{"estimand_id": "o1-estimand"}, {"estimand_id": "o1-estimand"}],
        "pooled": {"estimand_id": "o1-estimand"}}}}}
    try:
        enforce(eid, "control:estimand-match")
        out.append(("positive: estimand ids agree", "PUBLISHED", "PUBLISH"))
    except LabelMismatch:
        out.append(("positive: estimand ids agree", "REFUSED", "PUBLISH"))
    # NEGATIVE CONTROL 2 -- estimand_id disagreement must refuse.
    eid2 = {"results": {"by_outcome": {"o1": {
        "per_trial": [{"estimand_id": "o1-estimand"}, {"estimand_id": "o1-estimand"}],
        "pooled": {"estimand_id": "o2-estimand"}}}}}
    try:
        enforce(eid2, "control:estimand-mismatch")
        out.append(("negative: estimand ids differ", "PUBLISHED", "REFUSE"))
    except LabelMismatch:
        out.append(("negative: estimand ids differ", "REFUSED", "REFUSE"))
    return out


POOLED_ON_PAGE = re.compile(
    r"(?:pooled|Pooled)[^0-9\n]{0,40}?([-−]?\d+\.\d{2,4})\s*\(\s*"
    r"([-−]?\d+\.\d{2,4})\s*(?:to|–|—|-)\s*([-−]?\d+\.\d{2,4})\s*\)")


# A pooled value appearing inside prose that DISCUSSES it -- a reviewer's figure, a retracted
# headline, a confession -- is not the page's published number.
DISCUSSED = re.compile(
    r"external review|reviewer|still read|was withdrawn|withdrawal|previously|earlier version|"
    r"this page computes|it published|could not see|retract|superseded|as submitted|"
    r"disagreement|instead of|rather than|historical|used to", re.I)


def _rendered(raw):
    t = re.sub(r"(?is)<(script|style).*?</\1>", " ", raw)
    return re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", t))


def page_leg(extra_pairs=()):
    """⛔ THE LEG THAT WOULD ACTUALLY HAVE CAUGHT THE NEAR-SWAP.

    The object leg above compares the contributing ROWS with the POOLED block inside one object,
    and on the pilot those agree: both are registry-as-submitted, 0.7038. The near-swap was a
    level up -- the OBJECT's number about to be printed on a PAGE whose headline is the
    adjudicated 0.7127. A check confined to one file cannot see a disagreement between two.

    So this leg compares the pooled point the object holds with the pooled point the page shows,
    and reports the count-source wording each side carries. Different numbers under the same
    heading is the shape; the labels say which is which.
    """
    pm_file = os.path.join("ssot", "PAGE_MAP.json")
    pm = json.load(io.open(pm_file, encoding="utf-8")) if os.path.exists(pm_file) else {}
    pairs = [(p, o) for p, o in pm.items()
             if isinstance(o, str) and os.path.exists(o) and os.path.exists(p)]
    pairs += [(p, o) for p, o in extra_pairs if os.path.exists(p) and os.path.exists(o)]
    rows, reached, unreadable = [], 0, 0
    for page, store in pairs:
        try:
            obj = json.load(io.open(store, encoding="utf-8"))
            txt = _rendered(io.open(page, encoding="utf-8", errors="replace").read())
        except Exception:
            unreadable += 1
            continue
        # ⛔ COMPARE AGAINST EVERY OUTCOME THE OBJECT HOLDS, NOT THE FIRST ONE.
        #
        # Taking the first non-withdrawn pool made this leg compare sglt2's page headline
        # (0.7835, the three-component pool) against the object's first outcome (0.7636, the
        # harmonised pool) and call the object and page divergent. They are two different
        # outcomes of the same review, both correct. A pairing error reported as a data defect.
        held_all = []
        for _oid, b in (((obj.get("results") or {}).get("by_outcome")) or {}).items():
            pl = (b or {}).get("pooled") or {}
            if pl.get("withdrawn") or not isinstance(pl.get("point"), (int, float)):
                continue
            held_all.append((_oid, float(pl["point"]),
                             rows_label(b.get("per_trial"))["count_source"]))
        held = held_all[0] if held_all else None
        # ⛔ A NUMBER DISCUSSED IS NOT A NUMBER PUBLISHED, and the first version of this leg had
        # a 3 of 3 FALSE-POSITIVE RATE because it took the first "pooled (a to b)" in the text:
        #   dapivirine  "An external review supplied the pooled figure 0.7118 ... This page
        #               computes 0.7127" -- a declared contrast with a reviewer
        #   sglt2       the withdrawal note QUOTING the historical headline it retracts
        #   incretin    prose confessing a defect: "it published a pooled odds ratio of 0.4846
        #               that the corpus's own card-alignment checking could not see"
        # Every one is the page doing the right thing, reported as the defect -- this project's
        # measured bias, and the same class the integrity layer solved for `statistic-rendered-
        # twice`. So a match inside a contrastive or historical clause does not count.
        m = None
        for cand in POOLED_ON_PAGE.finditer(txt):
            near = txt[max(0, cand.start() - 320):cand.end() + 200]
            if DISCUSSED.search(near):
                continue
            m = cand
            break
        if held is None or not m:
            continue
        reached += 1
        shown = float(m.group(1).replace("−", "-"))
        dp = len(m.group(1).split(".")[1])
        # compare in the DISPLAYED representation, as gate_index_estimates does, and against
        # ANY outcome the object holds -- a page may headline any one of them.
        if any(round(h, dp) == round(shown, dp) for _o, h, _l in held_all):
            continue
        near = txt[max(0, m.start() - 400):m.end() + 400]
        rows.append({"page": os.path.basename(page),
                     "held": [round(h, 4) for _o, h, _l in held_all][:4], "shown": shown,
                     "rows_label": held[2],
                     "page_says": _count_source(near) or "no count source stated near it"})
    return rows, reached, len(pairs), unreadable


def plant_page_leg():
    """⛔ A LEG THAT FINDS NOTHING MUST BE SHOWN CAPABLE OF FINDING SOMETHING.

    Zero divergences is the same output a broken traversal produces. So a page/object pair is
    written to a temporary directory -- one where the page headlines a number the object does
    not hold, and one where it headlines a number the object does -- and both directions are
    asserted before the corpus figure above is believed.
    """
    import tempfile
    d = tempfile.mkdtemp(prefix="rob_labelgate_")
    obj = {"results": {"by_outcome": {"primary": {
        "per_trial": [{"provenance": "REGISTRY -- ClinicalTrials.gov posted results"}],
        "pooled": {"point": 0.7038, "counts_source": "registry as submitted"}}}}}
    op = os.path.join(d, "obj.json")
    json.dump(obj, io.open(op, "w", encoding="utf-8"))
    bad = os.path.join(d, "bad.html")
    io.open(bad, "w", encoding="utf-8").write(
        "<p>Pooled: RR 0.9123 (0.8000 to 0.9900)</p>")
    good = os.path.join(d, "good.html")
    io.open(good, "w", encoding="utf-8").write(
        "<p>Pooled: RR 0.7038 (0.5670 to 0.8740)</p>")
    out = []
    div, _r, _p, _u = page_leg([(bad, op)])
    out.append(("page headlines a number the object does not hold",
                "FLAGGED" if any(x["page"] == "bad.html" for x in div) else "MISSED", "FLAGGED"))
    div2, _r, _p, _u = page_leg([(good, op)])
    out.append(("page headlines the object's own number",
                "FLAGGED" if any(x["page"] == "good.html" for x in div2) else "QUIET", "QUIET"))
    return out


def main():
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace",
                                  line_buffering=True)
    print("")
    print("ESTIMAND-LABEL REFUSAL")
    print("")
    print("  CONTROLS -- both directions, because a gate that cannot publish is as useless")
    print("  as one that cannot refuse:")
    held = True
    for name, got, want in _controls():
        ok = got == ("REFUSED" if want == "REFUSE" else "PUBLISHED")
        held &= ok
        print("    %-44s %-9s %s" % (name, got, "OK" if ok else "*** want %s ***" % want))
    if not held:
        print("")
        print("  CONTROLS FAILED -- no corpus number is printed. A gate that does not reproduce")
        print("  the answer already established is not trusted for anything else.")
        return 2

    counts = {"COMPARED_OK": 0, "MISMATCH": 0, "NOT_COMPARABLE": 0}
    findings, objects = [], 0
    for d in sorted(os.listdir("ssot")):
        p = os.path.join("ssot", d, d + ".json")
        if not os.path.exists(p):
            continue
        objects += 1
        try:
            o = json.load(io.open(p, encoding="utf-8"))
        except Exception:
            continue
        for oid, block in (((o.get("results") or {}).get("by_outcome")) or {}).items():
            if not isinstance(block, dict):
                continue
            v, det = check_outcome(oid, block)
            counts[v] += 1
            if v == "MISMATCH":
                findings.append((d, oid, det))
    total = sum(counts.values())
    print("")
    print("  objects examined                        %5d" % objects)
    print("  outcome blocks                          %5d" % total)
    print("    both sides carry a label (COVERED)    %5d   %5.1f%%"
          % (counts["COMPARED_OK"] + counts["MISMATCH"],
             100.0 * (counts["COMPARED_OK"] + counts["MISMATCH"]) / max(1, total)))
    print("    labels agree                          %5d" % counts["COMPARED_OK"])
    print("    LABEL MISMATCH                        %5d" % counts["MISMATCH"])
    print("    no label on one or both sides         %5d   <- OUTSIDE THE CHECK, not a pass"
          % counts["NOT_COMPARABLE"])
    if findings:
        print("")
        for d, oid, det in findings[:15]:
            print("    %-30s %-28s %s" % (d, oid[:28], det[:80]))
        if len(findings) > 15:
            print("    ... and %d more" % (len(findings) - 15))

    # The pilot is HAND-BUILT and therefore absent from PAGE_MAP, so it is named explicitly.
    # Leaving it out would exclude the one page the near-swap actually happened on.
    extra = [("DAPIVIRINE_RING_PILOT_REVIEW.html",
              os.path.join("ssot", "agyw-hiv-prep-review", "agyw-hiv-prep-review.json"))]
    div, reached, pairs, unreadable = page_leg(extra)
    print("")
    print("  PAGE LEG -- the object's number against the page's headline")
    pheld = True
    for name, got, want in plant_page_leg():
        ok = (got == want)
        pheld &= ok
        print("    plant: %-46s %-8s %s" % (name, got, "OK" if ok else "*** want %s ***" % want))
    if not pheld:
        print("    PLANT FAILED -- the page leg's count below is not trusted.")
    print("    page/object pairs available            %5d   (%d from PAGE_MAP + %d named)"
          % (pairs, pairs - len(extra), len(extra)))
    print("    pairs where BOTH sides state a pool    %5d   %5.1f%%  <- the check's reach"
          % (reached, 100.0 * reached / max(1, pairs)))
    print("    unreadable                             %5d" % unreadable)
    print("    DIVERGENT                              %5d" % len(div))
    for r in div[:12]:
        print("      %-42s object %s (%s)  page %s (%s)"
              % (r["page"][:42], r["held"], r["rows_label"] or "unlabelled",
                 r["shown"], r["page_says"]))
    if len(div) > 12:
        print("      ... and %d more" % (len(div) - 12))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
