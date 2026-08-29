#!/usr/bin/env python3
"""A PAGE THAT DENIES HOLDING A RISK-OF-BIAS ASSESSMENT WHILE HOLDING ONE.

Flagged independently by two external reviews, on lefamulin and on sglt2-hf, and called
there the fifth and sixth instance of the class. Both quote the same shape: "no risk-of-bias
assessment is recorded" printed beside a two-assessor, result-level RoB 2 table that is
visibly on the page.

THE DISTINCTION THAT MATTERS, and it is the whole finding: ASSESSED is not ADJUDICATED.
Where two assessors have read every contributing result and nobody has resolved their
disagreement, the true sentence is "assessed, not adjudicated" -- which is a statement about
a missing FINAL judgement. "No assessment is recorded" is a statement about missing WORK, and
it is false. The first understates what the review has done; the second misdescribes it, and
it is the one that gets used to justify a GRADE downgrade for being unassessed.

THE TEST IS MECHANICAL. The page denies; the object is asked whether it holds anything. The
object is read through grade_authority._rob_state, which is the same reader the rest of the
pipeline uses, so this cannot disagree with the resolver about what exists.

WHAT IT CANNOT SEE: a denial phrased in words not in DENIALS below, and a page whose RoB
lives somewhere _rob_state does not look. It finds contradiction, never absence of it.
"""
import collections
import glob
import html as _h
import io
import json
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(ROOT, "ssot"))
sys.path.insert(0, os.path.join(ROOT, "gates"))
import grade_authority as ga            # noqa: E402
import _harness as H                    # noqa: E402

DENIALS = [
    "no risk-of-bias assessment is recorded",
    "no per-trial risk-of-bias (rob-2) assessment is recorded",
    "no result-level rob 2 assessment exists",
    "no risk-of-bias assessment exists",
]


def rendered(p):
    s = io.open(p, encoding="utf-8", errors="replace").read()
    s = re.sub(r"(?is)<(script|style).*?</\1>", " ", s)
    return re.sub(r"\s+", " ", _h.unescape(re.sub(r"<[^>]+>", " ", s)))


def holds_rob(canon):
    """What the object actually holds, by the pipeline's own reader plus a structural look."""
    try:
        st = ga._rob_state(canon)
    except Exception:
        st = {}
    n_results = st.get("results_assessed") or 0
    per_trial = 0
    for t in ((canon.get("inputs") or {}).get("trials") or []):
        if isinstance(t, dict) and (t.get("rob") or t.get("rob2") or t.get("risk_of_bias")):
            per_trial += 1
    return st, n_results, per_trial


def _controls():
    """POSITIVE: an object with assessed results must be reported as HOLDING one.
    NEGATIVE: an object with nothing must NOT be -- otherwise every honest denial in the
    corpus is flagged and the sweep says nothing."""
    # THE SHAPE IS TAKEN FROM A REAL OBJECT, NOT INVENTED. The first version of this control
    # used {"rob2": {"per_result": [...], "assessors": 2}} -- a shape I made up -- and it
    # failed, correctly, because rob_block reads canon['rob2']['trials'] or
    # canon['risk_of_bias']['by_outcome']. The control caught that I did not know the
    # contract, which is exactly what a positive control is for.
    pos = {"risk_of_bias": {"by_outcome": {"primary": {
        "NCT01": {"trial": "TRIAL-A", "nct": "NCT01",
                  "domains": {"D1_randomisation": {"judgement": "LOW", "reason": "x"}},
                  "overall": {"judgement": "LOW"}}}}}}
    neg = {"inputs": {"trials": [{"nct": "NCT1"}, {"nct": "NCT2"}]}}
    # A THIRD LEG, because rob_block says so itself: "a block with no by_outcome is a shell,
    # not an assessment". A shell must not count as holding one, or every page with an empty
    # risk_of_bias key becomes a false denial.
    shell = {"risk_of_bias": {"tool": "RoB 2", "version": "2.0"}}
    _, np_, pp = holds_rob(pos)
    _, nn, pn = holds_rob(neg)
    _, ns, ps = holds_rob(shell)
    ok = (np_ + pp) > 0 and (nn + pn) == 0 and (ns + ps) == 0
    print("CONTROLS, both legs, every run")
    print("  POSITIVE  object with 2 assessed results -> holds: %s" % ((np_ + pp) > 0))
    print("  NEGATIVE  object with only trial ids     -> holds: %s  (must be False)"
          % ((nn + pn) > 0))
    print("  CONTROLS PASS: %s\n" % ok)
    return ok


def main():
    if not _controls():
        print("CONTROLS FAILED -- findings below are not reportable.")
        return 3
    objs, _ = H.topic_objects(ROOT)
    by_tid = {}
    for p in objs:
        try:
            by_tid[H.topic_id(p)] = json.load(io.open(p, encoding="utf-8"))
        except Exception:
            pass
    kinds = collections.Counter()
    findings = []
    for pg in sorted(glob.glob(os.path.join(ROOT, "*.html"))):
        raw = io.open(pg, encoding="utf-8", errors="replace").read()
        if "risk" not in raw.lower():
            continue
        t = rendered(pg).lower()
        hit = [d for d in DENIALS if d in t]
        # EVERY PAGE THAT REACHES HERE IS CLASSIFIED, NONE IS SILENTLY DROPPED.
        #
        # This read `if not hit: continue`, and scripts/audit_exclusion_by_absence.py refused
        # the commit for it -- correctly. A page that denies in wording DENIALS does not know
        # would have been skipped without appearing anywhere, and the clean-looking count
        # would have been a reach figure wearing a coverage figure's clothes. That is the
        # exact failure this project has recorded eight times. The absence is now a COUNTED
        # KIND, so the denominator is visible and the residual risk is legible: any number in
        # "mentions risk of bias, matches no known denial phrasing" could contain a denial
        # this sweep cannot read.
        if hit:
            m = re.search(r'data-store="ssot/([^/"]+)/', raw)
            tid = m.group(1) if m else None
            if tid in by_tid:
                st, n_results, per_trial = holds_rob(by_tid[tid])
                if n_results or per_trial:
                    kinds["DENIES while the object HOLDS one"] += 1
                    findings.append((os.path.basename(pg), tid, hit[0],
                                     n_results, per_trial, st))
                else:
                    kinds["denies, and the object holds nothing (honest)"] += 1
            else:
                kinds["denies, page not mappable to an object"] += 1
        else:
            kinds["mentions risk of bias, matches no known denial phrasing"] += 1
    print("KINDS BEFORE COUNTS")
    for k, v in kinds.most_common():
        print("   %-46s %d" % (k, v))
    print("\nFALSE DENIALS: %d\n" % len(findings))
    for pg, tid, phrase, nr, pt, st in findings:
        print("  %-44s %s" % (pg[:44], tid[:30]))
        print("       says   : \"%s\"" % phrase)
        print("       holds  : %d assessed result(s), %d trial-level block(s); "
              "dual=%s adjudicated=%s"
              % (nr, pt, st.get("dual"), st.get("adjudicated")))
        true = ("assessed, NOT ADJUDICATED" if st.get("assessed") and not st.get("adjudicated")
                else "an assessment is recorded")
        print("       true   : %s\n" % true)
    return 1 if findings else 0


if __name__ == "__main__":
    sys.exit(main())
