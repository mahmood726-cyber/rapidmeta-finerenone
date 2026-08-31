# -*- coding: utf-8 -*-
"""GATE: every judged label is checked against its own free-text reason, and REFUSED on
contradiction. A bare label is not checkable. A label whose stated reason quotes the
object it judges is.

  G1  every quoted span must be literally present in the row's own text -- and the text
      searched is the SAME text the judgement was made from (title + objectives_verbatim),
      not a re-read, not a slice.
  G2  a COUNTERPART must quote BOTH limbs: an intervention span and a condition span.
      A one-limbed reason cannot support a two-limbed claim.
  G3  a NOT_COUNTERPART must quote the DISQUALIFYING span. "It just isn't one" is not a
      reason.
  G4  a NOT_COUNTERPART whose disqualifying quote does not appear is the dangerous case:
      the refusal would then be a statement about the harness dressed as a statement
      about the object.

Refusal names the offending path and line FIRST, the rule second, the gate third.
"""
import io, json, os, re, sys

GATE = "rekey20/gate_label_vs_reason.py"
LABELS = ("COUNTERPART", "NOT_COUNTERPART", "UNDECIDABLE_BY_RULE")


def _norm(t):
    return re.sub(r"[^a-z0-9]+", " ", (t or "").lower()).strip()


def check(judgements, rowtext, path="judgements.json"):
    """rowtext: (app_id, cd_base) -> the exact text the judgement was made from."""
    refusals = []
    for i, j in enumerate(judgements, 1):
        loc = "%s:%d  (%s / %s)" % (path, i, j.get("app_id"), j.get("cd_base"))
        lab = j.get("label")
        if lab not in LABELS:
            refusals.append("%s\n  rule: label %r is not one of %s\n  found by: %s"
                            % (loc, lab, LABELS, GATE))
            continue
        hay = _norm(rowtext.get((j["app_id"], j["cd_base"])))
        if not hay:
            refusals.append("%s\n  rule: no row text held for this pair -- a judgement about a "
                            "row that was never shown cannot be checked\n  found by: %s" % (loc, GATE))
            continue
        quoted = (j.get("quotes_intervention", []) + j.get("quotes_condition", [])
                  + j.get("quotes_disqualifying", []))
        if not quoted:
            refusals.append("%s\n  rule: the reason quotes nothing. A label with no quoted span "
                            "from the object is not checkable against it\n  found by: %s" % (loc, GATE))
            continue
        for q in quoted:
            if _norm(q) not in hay:
                refusals.append(
                    "%s\n  rule: the reason quotes %r, which does not appear in the row's own "
                    "title+objectives -- the text this judgement was made from. Either the quote "
                    "is fabricated or the gate is searching different bytes than were shown; "
                    "both are refusals, and the second is the one that turns a true statement "
                    "into an accusation\n  found by: %s" % (loc, q[:90], GATE))
        if lab == "COUNTERPART":
            if not j.get("quotes_intervention") or not j.get("quotes_condition"):
                refusals.append("%s\n  rule: COUNTERPART asserts BOTH intervention and condition "
                                "match; the reason quotes only %s\n  found by: %s"
                                % (loc, "intervention" if j.get("quotes_intervention") else "condition", GATE))
        if lab == "NOT_COUNTERPART" and not j.get("quotes_disqualifying"):
            refusals.append("%s\n  rule: NOT_COUNTERPART must quote the span that disqualifies "
                            "the pair\n  found by: %s" % (loc, GATE))
        # contradiction: a NOT_COUNTERPART whose reason contains no negating language while
        # its quotes are the same spans a COUNTERPART would cite.
        if lab == "NOT_COUNTERPART":
            r = (j.get("reason") or "").lower()
            if not re.search(r"\bnot\b|\bdifferent\b|\bdisjoint\b|\bexclud|\bnoise\b|\brather than\b", r):
                refusals.append("%s\n  rule: the label says NOT_COUNTERPART but the reason states "
                                "no ground of difference -- label and reason contradict\n  found by: %s"
                                % (loc, GATE))
    return refusals
