r"""GATE 21 -- a review that NAMES a harm outcome must report it, or refuse with a reason.

THE DEFECT. Fifteen external reviews told seven pages the same thing: the PICO names
harms and the review synthesises none. On two of those pages the complaint is exactly
right in the strict sense -- the page's OWN question and its OWN eligibility estimand name
major bleeding, and results.by_outcome carries a single efficacy outcome and nothing else.
That is a page contradicting itself, and no external reviewer should have had to find it.

WHAT THIS GATE POLICES, AND WHAT IT DELIBERATELY DOES NOT.

    POLICED.  A topic whose PICO names a harm outcome -- adjudicated as NAMED_* in
              gates/HARMS_PICO_ADJUDICATION.json -- must EITHER publish a synthesis of a
              harm, OR publish an explicit refusal carrying a reason.

    NOT POLICED.  A topic whose PICO does not name a harm. Its trials may well register
              safety outcomes nobody synthesised -- 54 of 102 assessable topics are in
              that position, measured by scripts/measure_harms_gap.py -- but that is a
              review being NARROWER THAN ITS SOURCES, not a review breaking its own word.
              ⛔ FOLDING THE TWO TOGETHER WOULD REPORT 56 BROKEN PROMISES WHERE THERE ARE
              TWO. An inflated count with a true story attached to it is still inflated,
              and it is the specific error this gate was told to avoid.

A REFUSAL IS A VALID OUTPUT AND A FALSE REASON IS NOT. casirivimab-covid names a harm
outcome -- its trial's registered primary IS a treatment-emergent SAE count -- and
publishes no pool, because k=1. That reason is CORRECT (Cochrane Handbook 6.5 section
10.10.3) and the gate passes it. The gate checks that a reason EXISTS and is pinned to a
field; it cannot check that a reason is TRUE, and says so rather than implying it can.

THE CONTROL IS SYNTHETIC, ON PURPOSE, AND THIS IS THE WHOLE DESIGN.
    The obvious control is "the gate must flag apixaban-vte-prophylaxis". It is also
    wrong: THAT CONTROL RETIRES ITSELF THE DAY THE PAGE IS FIXED -- which is the next
    commit in this very lane. A control anchored to a live defect either fails after the
    fix (and reads as a regression) or silently passes for the wrong reason. So the
    discrimination control is FOUR objects built IN MEMORY every run -- one that promises
    a harm and delivers nothing, one that promises and delivers, one that promises and
    refuses with a reason, and one that promises while AFFIRMING poolability at length
    (the shape that made the first draft of this gate report zero findings) -- and the
    gate is VACUOUS unless all four are decided correctly. It will still be able to fail
    long after the corpus stops giving it anything to find.

RATCHETED, AND THE HONEST HALF OF THAT IS PRINTED EVERY RUN. The two findings that exist
today are frozen by name in gates/GATE21_KNOWN_UNREPORTED_HARMS.json. A PASS from here
means NO NEW INSTANCES, never "clean". When the two are fixed the ratchet reports them as
retired; it never requires them to stay, because a control that demands its own defect
survive is the self-retiring failure one paragraph up, inverted.

Exit codes are the harness's: 0 PASS, 1 FAIL, 2 VACUOUS, 3 BROKEN.
"""
from __future__ import annotations

import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _harness as H                                                        # noqa: E402

sys.path.insert(0, os.path.join(H.repo_root(), "scripts"))
from harms_pico_surface import harm_mentions, harms_synthesis               # noqa: E402

ADJUDICATION = os.path.join("gates", "HARMS_PICO_ADJUDICATION.json")
FREEZE = "GATE21_KNOWN_UNREPORTED_HARMS.json"

# The dispositions under which the PICO actually UNDERTOOK to report a harm. The other
# three -- MENTION_IS_NOT_AN_OUTCOME, COMPONENT_OF_SYNTHESISED_COMPOSITE, and any future
# addition -- are not promises and are not policed here.
PROMISING = ("NAMED_AND_ABSENT", "NAMED_AND_SYNTHESISED", "NAMED_AND_REFUSED_WITH_REASON")

# Field names that carry a PUBLISHED refusal and its reason. Read as a pair: a refusal
# flag with no reason beside it is not a reasoned refusal, it is a blank.
REFUSAL_REASON_KEYS = ("withdrawn_reason", "why", "why_not_pooled", "poolable_reason",
                       "not_pooled", "not_pooled_either", "reason", "refusal_reason")

# ⛔ POLARITY, AND THE VALUE THAT MEANS REFUSED -- NOT THE PRESENCE OF THE KEY.
#
# The first draft of this gate tested `key in node`, so `poolable: True` -- a declaration
# that the efficacy outcome IS poolable, beside a `poolable_reason` explaining WHY it is
# -- counted as a refusal. Both apixaban pages then read as REFUSED_WITH_REASON and the
# gate reported ZERO findings where the measurement had found two. A GATE THAT READS AN
# AFFIRMATION AS ITS OPPOSITE FAILS SILENTLY AND IN THE FLATTERING DIRECTION.
#
# This is the repository's own inverted-guard class -- the signal that blocked the
# disclaimer and passed the assertion -- committed here by someone who had read that
# entry. A mention is not a claim, and a field is not a value.
REFUSAL_FLAG_KEYS = {"withdrawn": True, "poolable": False,
                     "permanently_refused": True, "refused": True}


def published_refusal(obj):
    """-> (bool, where). Does this object publish a refusal to report, WITH a reason?

    RE-DERIVED FROM THE OBJECT EVERY RUN, never read from the adjudication file. A gate
    that trusts a stored verdict cannot notice the day the object stops supporting it --
    it would pass a page whose refusal had been deleted, because a file still said the
    page had one.
    """
    found = []

    def visit(node, path):
        if isinstance(node, dict):
            flagged = any(node.get(k) is refusing
                          for k, refusing in REFUSAL_FLAG_KEYS.items() if k in node)
            reason = next((k for k in REFUSAL_REASON_KEYS
                           if isinstance(node.get(k), str) and len(node[k]) > 40), None)
            if flagged and reason:
                found.append("%s.%s" % (path, reason) if path else reason)
            for k, v in node.items():
                visit(v, "%s.%s" % (path, k) if path else k)
        elif isinstance(node, list):
            for i, v in enumerate(node):
                visit(v, "%s[%d]" % (path, i))

    visit((obj.get("results") or {}).get("by_outcome") or {}, "results.by_outcome")
    return bool(found), found[:3]


def decide(obj, disposition):
    """The whole rule, in one place, so the synthetic probes and the corpus share it.

    -> one of:
        NOT_POLICED       the PICO names no harm, or the mention is not an undertaking
        REPORTED          a harm synthesis exists
        REFUSED_WITH_REASON  no synthesis, but a refusal carrying a reason is published
        PROMISED_NOT_REPORTED   ⛔ neither. The finding.
    """
    if disposition not in PROMISING:
        return "NOT_POLICED", []
    present, where = harms_synthesis(obj)
    if present:
        return "REPORTED", where
    refused, rwhere = published_refusal(obj)
    if refused:
        return "REFUSED_WITH_REASON", rwhere
    return "PROMISED_NOT_REPORTED", []


def _probes():
    """Three objects built in memory. Synthetic, so they never retire.

    Each is the MINIMUM that exercises one branch -- a bigger fixture would let a probe
    pass for a reason other than the one it is testing.
    """
    promise = {"question": "does it work, and what about major bleeding?",
               "outcomes": [{"id": "eff", "name": "efficacy", "definition": "efficacy"}]}
    absent = dict(promise, results={"by_outcome": {"eff": {"k": 2}}})
    reported = dict(promise, outcomes=[
        {"id": "eff", "name": "efficacy", "definition": "efficacy"},
        {"id": "bleed", "name": "major bleeding", "definition": "major bleeding"}],
        results={"by_outcome": {"eff": {"k": 2}, "bleed": {"k": 2}}})
    refused = dict(promise, results={"by_outcome": {"eff": {
        "pooled": {"withdrawn": True,
                   "withdrawn_reason": "k=1: a single registration cannot be pooled, "
                                       "Cochrane Handbook 6.5 section 10.10.3."}}}})
    # THE POLARITY PROBE, and the reason there are four and not three. This object
    # AFFIRMS that its efficacy outcome is poolable and says at length why -- the exact
    # shape that made the first draft read both apixaban pages as reasoned refusals and
    # report zero findings. It must come out PROMISED_NOT_REPORTED. A probe set that
    # exercises three branches and not the inverted one is a probe set that passes the
    # bug it was written after.
    affirmed = dict(promise, results={"by_outcome": {"eff": {
        "poolable": True,
        "poolable_reason": "All four register the same composite at secondary rank and "
                           "each title was read rather than matched by name."}}})
    return [
        ("__control_promise_absent__", absent, "NAMED_AND_ABSENT", "PROMISED_NOT_REPORTED"),
        ("__control_promise_reported__", reported, "NAMED_AND_SYNTHESISED", "REPORTED"),
        ("__control_promise_refused__", refused, "NAMED_AND_REFUSED_WITH_REASON",
         "REFUSED_WITH_REASON"),
        ("__control_poolability_affirmed_is_not_a_refusal__", affirmed,
         "NAMED_AND_ABSENT", "PROMISED_NOT_REPORTED"),
    ]


def main(argv):
    gate = H.Gate("21 HARMS PROMISED BUT NOT REPORTED",
                  "a PICO that names a harm outcome must report it or refuse with a reason")
    gate.expect_case(
        "discriminates",
        "four SYNTHETIC objects -- promise-and-omit, promise-and-deliver, "
        "promise-and-refuse-with-a-reason, and promise-while-AFFIRMING-poolability -- decided correctly, every run")
    gate.requires_control()

    repo = H.repo_root()
    adj_path = os.path.join(repo, ADJUDICATION)
    if not os.path.exists(adj_path):
        gate.broken("%s is absent. This gate cannot separate a named outcome from a "
                    "population name by itself, and will not guess." % ADJUDICATION)
        gate.kinds({"topics reached": 0})
        return gate.report(denominator="no adjudication file")
    adj = {r["app_id"]: r for r in H.load(adj_path)["rows"]}

    # -- the synthetic discrimination control, before anything real is read -----------
    wrong = [(pid, want, got)
             for pid, obj, disp, want in _probes()
             for got, _w in [decide(obj, disp)] if got != want]
    if wrong:
        for pid, want, got in wrong:
            gate.broken("probe %s: expected %s, got %s" % (pid, want, got))
    else:
        gate.saw("discriminates")

    # -- the corpus ------------------------------------------------------------------
    paths, path_kinds = H.topic_objects(repo)
    live, tombstones, verdicts = {}, [], {}
    for p in paths:
        obj = H.load(p)
        if "question" in obj:
            live[H.topic_id(p)] = obj
        else:
            tombstones.append(H.topic_id(p))

    unadjudicated, findings = [], []
    for app_id, obj in sorted(live.items()):
        if not harm_mentions(obj):
            verdicts[app_id] = "NO_HARM_IN_PICO"
            continue
        row = adj.get(app_id)
        if row is None:
            unadjudicated.append(app_id)
            continue
        v, where = decide(obj, row["disposition"])
        verdicts[app_id] = v
        if v == "PROMISED_NOT_REPORTED":
            findings.append((app_id, row))
        elif v == "NOT_POLICED":
            verdicts[app_id] = "MENTION_IS_NOT_A_PROMISE"
        else:
            verdicts[app_id] = "%s (%s)" % (v, ", ".join(where[:1]) or "-")

    if unadjudicated:
        gate.broken("%d topic(s) whose PICO carries a harm term have no row in %s: %s. "
                    "A detector cannot tell an outcome from a population, so this gate "
                    "REFUSES rather than deciding it either way."
                    % (len(unadjudicated), ADJUDICATION, ", ".join(unadjudicated[:6])))

    # KNOWN-NEGATIVES ARE THE ADJUDICATED NON-PROMISES AND THE DELIVERED PROMISES. Every
    # one of them is a case established as clean for THIS gate's question; a match is the
    # gate accusing a clean page, which is the failure the repo contract refuses outright.
    negatives = [a for a, r in adj.items()
                 if a in live and (r["disposition"] not in PROMISING
                                   or r["disposition"] != "NAMED_AND_ABSENT")]
    negatives = [a for a in negatives if a not in [f[0] for f in findings]]
    fp = [a for a in negatives
          if verdicts.get(a, "").startswith("PROMISED_NOT_REPORTED")]
    gate.control(len(negatives), len(fp), fp[:5], accuses=True)

    counts = {}
    for v in verdicts.values():
        counts[v.split(" (")[0]] = counts.get(v.split(" (")[0], 0) + 1
    gate.kinds({
        "live topics (question + outcomes + results)": len(live),
        "  NO_HARM_IN_PICO -- not policed, and not a defect": counts.get("NO_HARM_IN_PICO", 0),
        "  MENTION_IS_NOT_A_PROMISE -- population, registry label, or prose about a source":
            counts.get("MENTION_IS_NOT_A_PROMISE", 0),
        "  REPORTED -- a harm synthesis exists": counts.get("REPORTED", 0),
        "  REFUSED_WITH_REASON -- no synthesis, a reason is published":
            counts.get("REFUSED_WITH_REASON", 0),
        "  PROMISED_NOT_REPORTED -- the finding": counts.get("PROMISED_NOT_REPORTED", 0),
        "tombstone (retired; makes no claim, cannot break one)": len(tombstones),
        "other json under ssot/<t>/ (not a topic object)":
            path_kinds["other json under ssot/<t>/"],
    })
    gate.coverage(len(live), len(live) + len(tombstones),
                  "tombstones: retired objects that carry no question, so there is no "
                  "undertaking for them to break")
    gate.note("this gate checks that a refusal EXISTS and carries a reason. IT CANNOT "
              "CHECK THAT A REASON IS TRUE. A refusal with a false reason passes here "
              "and is worse than no refusal; that one is on the reader.")
    gate.note("topics whose PICO names no harm are NOT policed. 54 of 102 assessable "
              "topics have a trial that registered a harm nobody synthesised -- measured "
              "by scripts/measure_harms_gap.py, a different class, deliberately not "
              "counted here.")

    new = H.ratchet(gate, FREEZE, [f[0] for f in findings],
                    "topics whose PICO names a harm outcome and which publish neither a "
                    "synthesis of it nor a reasoned refusal",
                    escalated="the harms lane, 2026-09-03")
    for app_id, row in findings:
        mark = "NEW " if app_id in new else "frozen "
        gate.note("%s%s -- by_outcome=%s -- %s"
                  % (mark, app_id,
                     list(((live[app_id].get("results") or {}).get("by_outcome") or {})),
                     row["quote"][:120]))
    for app_id in new:
        gate.finding("promised-not-reported", "%s names a harm outcome in its PICO and "
                     "publishes neither a synthesis of one nor a reasoned refusal"
                     % app_id, numerator=1, denominator=len(live))

    return gate.report(denominator="%d live topics; %d carry a harm term in the PICO; "
                                   "%d of those are undertakings"
                                   % (len(live), len([a for a in live if harm_mentions(live[a])]),
                                      len([a for a in adj if a in live
                                           and adj[a]["disposition"] in PROMISING])))


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
