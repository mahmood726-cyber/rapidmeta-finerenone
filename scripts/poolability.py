"""POOLABILITY -- can this topic support a pooled estimate at all?

THE RULE THIS IMPLEMENTS
    The corpus should carry POOLABLE QUESTIONS. Where a topic cannot support a
    pooled estimate it is replaced by one that can, rather than kept as a page
    presenting an unpoolable set.

THE DISTINCTION THAT MAKES THE RULE SAFE
    (A) POOLABLE AS POSED. Nothing to do.

    (B) POOLABLE AFTER A STATED ADJUSTMENT. The question is mis-specified but a
        poolable question exists nearby, and the defect can be NAMED. FINERENONE
        pooled a kidney outcome with a CV outcome while both DKD trials report the
        CV composite; DOAC_CANCER_VTE mixed an efficacy-plus-harm composite with
        pure efficacy while all three trials report recurrent VTE separately.
        The adjustment is stated BEFORE any number exists. That ordering is the
        entire guard: adjust because the trials cannot answer the question, never
        because a different question yields a nicer estimate.

    (C) NOT POOLABLE. Trials too clinically distinct, no common outcome, or a
        single trial. THESE MUST NOT BE REPLACED WITH A MANUFACTURED QUESTION SO
        THE PAGE CAN SHOW A NUMBER. "Replace with a topic where pooling is
        possible" must not become "keep adjusting until a number appears". The
        honest output is a page presenting the trials separately with the reason -
        as MITRAL now does for COAPT and MITRA-FR at I-squared 88 - or removal of
        the topic. A page reporting two discordant trials separately and explaining
        the discordance is more useful than a pooled estimate that conceals it.

        NOTHING IS REMOVED BY THIS SCRIPT. Category C is a list for a human.

WHAT A CLASSIFICATION DOES NOT ESTABLISH -- written in advance
    - NOT that a category-A page's estimate is correct. Poolable is not right.
    - NOT that a category-B adjustment is the BEST question, only that one exists.
    - NOT clinical judgement. Whether two populations are "too distinct" is a
      clinician's call; this flags candidates on mechanical signals and says so.
    - The test for a replacement question is whether a clinician would actually ask
      it. No script can check that, which is why category C goes to a human.
"""
from __future__ import annotations
import json, os, re, sys, io, glob, collections
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

if __name__ == "__main__":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

HARM = re.compile(r"\b(bleed\w*|h[ae]morrhag\w*|adverse events?|serious adverse|toxicit\w*)\b", re.I)
EFF = re.compile(r"\b(death|mortality|survival|stroke|myocardial infarction|hospitali[sz]ation|"
                 r"thromboembol\w*|\bVTE\b|infection|cure|clearance|response)\b", re.I)


def classify(path):
    d = json.loads(open(path, encoding="utf-8", errors="replace").read())
    c = d.get("canonical") or {}
    # BOTH SCHEMAS -- see arm_identity_gate. UNASSESSABLE on 100% of the v1
    # objects was this gate reading the extraction artefact's shape only.
    import object_shapes as _os
    trials = _os.trials_of(d)
    est = c.get("estimand") or {}
    _k, rep = _os.pooled_of(d)
    k = _k if _k is not None else rep.get("k")
    reasons = []

    if not trials or k is None:
        return "UNASSESSABLE", ["no trials or no pooled result recorded"]
    if k == 1 or len(trials) == 1:
        return "C_NOT_POOLABLE", ["a single trial: there is nothing to pool"]

    # multiple declared outcomes is the object saying so itself
    od = est.get("outcome_definition") or ""
    if od.startswith("Multiple trial-declared outcomes"):
        reasons.append("the object itself records MULTIPLE trial-declared outcomes, so the "
                       "trials are not reporting one common quantity")

    defs = [(t.get("outcome") or {}).get("definition") or "" for t in trials]
    named = [x for x in defs if x]
    h = sum(1 for x in named if HARM.search(x) and not EFF.search(x))
    e = sum(1 for x in named if EFF.search(x) and not HARM.search(x))
    if h and e:
        reasons.append("harm endpoints pooled with efficacy endpoints (%d vs %d): the two move "
                       "in opposite directions by construction" % (h, e))
    if len(named) < len(trials):
        reasons.append("%d of %d trials carry no outcome definition, so a common outcome cannot "
                       "be established" % (len(trials) - len(named), len(trials)))

    i2 = rep.get("I2")
    if i2 is not None and i2 >= 90:
        reasons.append("I-squared %.0f%%: the trials disagree so strongly that an average "
                       "conceals more than it conveys" % i2)

    if reasons:
        # a NAMED defect with a common quantity still available -> adjustable
        adjustable = (len(named) >= 2 and not (h and e) and (i2 is None or i2 < 90))
        return ("B_POOLABLE_AFTER_ADJUSTMENT" if adjustable else "C_NOT_POOLABLE"), reasons
    return "A_POOLABLE_AS_POSED", ["k=%s, one common outcome, no mixed directions" % k]


def main() -> int:
    paths = sorted(glob.glob(sys.argv[1]))
    tot = collections.Counter()
    rows = []
    for p in paths:
        try:
            v, why = classify(p)
        except Exception:
            continue
        tot[v] += 1
        rows.append((os.path.basename(p).replace(".html.canonical.json", ""), v, why))
    n = sum(tot.values())
    print("topics assessed: %d" % n)
    for k in ("A_POOLABLE_AS_POSED", "B_POOLABLE_AFTER_ADJUSTMENT", "C_NOT_POOLABLE",
              "UNASSESSABLE"):
        print("  %-30s %4d  %5.1f%%" % (k, tot[k], 100 * tot[k] / n if n else 0))
    print("\nCATEGORY C -- FOR A HUMAN DECISION, nothing removed by this script:")
    for pg, v, why in rows:
        if v == "C_NOT_POOLABLE":
            print("  %-46s %s" % (pg[:46], why[0][:88]))
    json.dump([{"page": r[0], "category": r[1], "reasons": r[2]} for r in rows],
              open(r"F:\E156\outputs\codex-corpus-scan\POOLABILITY.json", "w",
                   encoding="utf-8"), indent=1)
    return 0


if __name__ == "__main__":
    sys.exit(main())
