# -*- coding: utf-8 -*-
"""ADJUDICATE the open-access verified pairs, through the EXISTING gate.

⛔ REUSED, NOT REBUILT. `gate_label_vs_reason.check` is the same gate the CDSR judgements
passed. Every label must quote a span that is literally present in the row's own
title+abstract -- THE SAME TEXT the judgement was made from, not a re-read and not a slice.
A COUNTERPART must quote both limbs; a NOT_COUNTERPART must quote the disqualifying span.

⚠️⚠️ CONFLICT OF INTEREST, DECLARED RATHER THAN DISCOVERED. I built the matcher and I am
the sole labeller of its output. This project has already recorded that as a real weakness
("the labeller should not be the classifier's author") and it is recorded again here rather
than quietly repeated. These verdicts are a SINGLE-RATER judgement by an interested party;
they are not an independent adjudication and should be re-run by a lane that did not write
`axis_match.py`.

⭐ THE DECLARED COUNTERPART RULE, stated before the labels so it can be checked against
them, and taken from the CDSR judgements rather than invented here:
  * The review's UNIT OF WORK must be this topic's drug, or a coherent CLASS containing it
    (the precedent is CD004434, "endothelin receptor antagonists", accepted for bosentan).
  * The review's POPULATION must be this topic's condition.
  * A NARROWER OUTCOME SET does not disqualify; a DIFFERENT CONSTRUCT does. The precedent is
    CD007557, refused because its outcome was heparin-induced thrombocytopenia rather than
    VTE. So "echocardiographic parameters of mavacamten in HCM" is a counterpart and
    "mavacamten and atrial fibrillation risk via FAERS" is not.
  * A LANDSCAPE review ("eighteen targeted drugs", "present and future therapies") is not a
    class review and is refused: an arbitrary set of everything available is not a unit of
    work.
"""
import io, json, os, sys
from collections import Counter, defaultdict

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
os.chdir(HERE)
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace",
                              line_buffering=True)
from gate_label_vs_reason import check                                   # noqa: E402

STATES = "../../evidence/2026-08-31-axis/oa_states_twenty.json"
JUDGE = "../../evidence/2026-08-31-axis/oa_judgements.json"

d = json.load(io.open(STATES, encoding="utf-8"))
J = json.load(io.open(JUDGE, encoding="utf-8"))

rowtext, pairs, demand_pairs = {}, set(), set()
for t in d["topics"]:
    for r in ((t.get("verified") or {}).get("rows") or []):
        k = (t["app_id"], r["oa_id"])
        rowtext[k] = (r["title"] or "") + " " + (r["objectives_verbatim"] or "")
        pairs.add(k)
        if t["in_demand_list"]:
            demand_pairs.add(k)

judged = {(j["app_id"], j["cd_base"]) for j in J}

# ⛔ COVERAGE IS ASSERTED AGAINST A DECLARED SCOPE, AND THE SCOPE IS NAMED.
# The thirteen control topics are NOT judged: every one of their retrieved sets was
# TRUNCATED at the 100-row cap (up to 3,541 hits), so their verified rows are an arbitrary
# relevance-ordered window rather than a population. Judging a window and reporting it
# beside a population would be the reach-versus-coverage defect again.
scope = demand_pairs
missing, extra = scope - judged, judged - scope
print("=== COVERAGE OF THE DECLARED SCOPE ===")
print("   scope: the DEMAND LIST's verified pairs only (%d). The 13 control topics are" % len(scope))
print("   NOT judged -- all 13 were truncated at the 100-row cap, so their verified rows")
print("   are an arbitrary window, not a population. Named, not silently dropped.")
print("   verified pairs on ALL twenty : %d" % len(pairs))
print("   in scope                     : %d" % len(scope))
print("   judgements                   : %d" % len(J))
if missing or extra:
    print("REFUSING: the judgement set does not cover the scope exactly.")
    for m in sorted(missing):
        print("   unjudged in-scope pair : %s / %s" % m)
    for m in sorted(extra):
        print("   judgement out of scope : %s / %s" % m)
    sys.exit(1)
print("   exact match: HOLDS")

ref = check(J, rowtext, path="oa_judgements.json")
print("")
if ref:
    print("=== GATE REFUSED %d JUDGEMENT(S) -- NO COUNT PRINTED ===" % len(ref))
    for r in ref:
        print(r)
        print("")
    sys.exit(1)
print("=== GATE: %d/%d pass. Every label quotes a span from the row's own title+abstract. ==="
      % (len(J), len(J)))

print("")
for k, v in Counter(j["label"] for j in J).most_common():
    print("   %-22s %d" % (k, v))

by_topic = defaultdict(list)
for j in J:
    by_topic[j["app_id"]].append(j)

print("")
print("=== candidates -> verified -> judged, PER TOPIC. Never padded. ===")
print("   %-46s %8s %8s %9s %s" % ("app_id", "fetched", "verified", "COUNTERPART", "state"))

# ⛔ THE POSITIVE PROPERTY, NOT A NEGATIVE GUARD. This loop used to open with
# `if not t["in_demand_list"]: continue`, and `audit_exclusion_by_absence.py --gate`
# refused it -- correctly. A skip inside a corpus-wide loop shrinks the denominator
# invisibly: the rows it drops cannot appear in any count derived from the loop, and
# nothing in the output says how many there were. Partitioning first states BOTH parts and
# lets them be asserted to sum to the population.
in_scope = [t for t in sorted(d["topics"], key=lambda x: x["app_id"]) if t["in_demand_list"]]
out_of_scope = [t for t in d["topics"] if t["in_demand_list"] is False]
if len(in_scope) + len(out_of_scope) != len(d["topics"]):
    print("REFUSING: the partition loses topics -- %d in scope + %d out of scope != %d"
          % (len(in_scope), len(out_of_scope), len(d["topics"])))
    sys.exit(1)
print("   partition: %d in scope + %d out of scope == %d topics  HOLDS"
      % (len(in_scope), len(out_of_scope), len(d["topics"])))
topics_with = 0
for t in in_scope:
    js = by_topic.get(t["app_id"], [])
    cp = sum(1 for j in js if j["label"] == "COUNTERPART")
    topics_with += bool(cp)
    print("   %-46s %8s %8s %9d %s"
          % (t["app_id"], t["fetched"],
             (t.get("verified") or {}).get("n", 0), cp, t["state"]))

cps = [j for j in J if j["label"] == "COUNTERPART"]
ids = sorted({j["cd_base"] for j in cps})
print("")
print("   COMPARATORS (judged COUNTERPART pairs) : %d" % len(cps))
print("   INDEPENDENT TOPICS carrying one        : %d / 7" % topics_with)
print("   DISTINCT open-access reviews behind them: %d" % len(ids))
print("   verified-stage precision                : %d/%d = %.0f%%   (CDSR was 6/14 = 43%%)"
      % (len(cps), len(J), 100.0 * len(cps) / len(J)))
print("")
print("   the distinct reviews:")
for i in ids:
    print("      %s" % i)
