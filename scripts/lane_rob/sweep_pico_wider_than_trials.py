# -*- coding: utf-8 -*-
"""Sweep: a stated population wider than the union of its trials' eligibility.

THE CLASS, FROM TWO INSTANCES. iv-iron-hf states a PICO covering all heart failure while
every contributing trial imposed an ejection-fraction ceiling. incretin-hfpef states a scope
broader than any trial in it: the evidence is obesity-related HFpEF/HFmrEF at BMI >= 30 with
LVEF thresholds of >= 45% or >= 50%. Two instances of one shape: the review claims a
population no trial studied. Under RoB 2's companion question in GRADE that is an
indirectness finding by definition -- leaving the PICO broad AND rating indirectness "not
serious" is not an available combination.

WHAT IS DETECTABLE, AND WHY THIS LOOKS FOR NUMBERS. Comparing free-text populations for
breadth is a judgement, and a keyword instrument would be inference wearing a field name.
A NUMERIC ELIGIBILITY THRESHOLD is different: if every trial's registered eligibility carries
"LVEF <= 40%" or "BMI >= 30" and the review's stated population carries no such bound, the
review is quantifiably wider than its evidence and a reader cannot see it. That is a
high-precision signal, and it is deliberately not the whole class: a PICO can be wider in
ways no number expresses, and those will not be flagged.

!! THIS INSTRUMENT FAILS ITS OWN KNOWN-ANSWER TEST AND ITS COUNT MUST NOT BE QUOTED AS A
!! MEASURE OF THE CLASS.
!!
!! It returns 25 topics of 155, and it misses BOTH founding examples -- iv-iron-hf and
!! incretin-hfpef-review, the two cases external reviewers actually found. Neither review
!! states a numeric bound, so neither was skipped for that reason; the miss is on the trial
!! side, where the gate requires EVERY trial to yield a THRESH match and the pattern does
!! not cover every phrasing a registry uses. So the 25 are topics matching a narrow
!! pattern, not a measured population, and recall is unknown and demonstrably below 100%.
!!
!! NOT TUNED AGAINST THOSE TWO. Widening the regex until iv-iron-hf and incretin-hfpef
!! appear would fit the instrument to the only two cases available to validate it, and
!! destroy the one measurement of it anyone has. Whoever extends it should widen the
!! pattern against registry phrasing in general, then check these two as HELD-OUT cases,
!! and record whether they were found.
!!
!! PRECISION IS BETTER THAN RECALL HERE: of the 25, 2 (arni-hfref, omecamtiv-heartfail)
!! narrow their population correctly in PROSE without a number, so they are likely false
!! positives -- the check asks "does the review state a numeric bound", which is not the
!! same question as "is the review wider than its trials".

READ-ONLY. Writes nothing.
"""
import collections
import glob
import io
import json
import os
import re
import sys

# GUARDED. A module-level stdout reassignment closes the CALLER's stdout the moment
# this file is imported, and every script here is now importable -- three separate
# checks of this lane's own output died that way before it was fixed at the source.
if __name__ == "__main__":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8",
                                  errors="replace", line_buffering=True)
HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(os.path.dirname(HERE))
os.chdir(REPO)
# THE SPARSE WORKTREE DOES NOT CARRY THE REGISTRY CACHE, and falling back rather than
# failing is right here: the cache is read-only reference data, identical in every
# worktree. The fallback is named so a reader knows which copy was read.
CACHE = ".ctgov-raw-cache"
if not os.path.isdir(CACHE):
    CACHE = r"F:\rapidmeta-ssot-shell\.ctgov-raw-cache"
if not os.path.isdir(CACHE):
    sys.exit("REFUSED: no registry cache found; this sweep needs eligibility text and "
             "will not guess at it.")
print("registry cache: %s" % CACHE)

# a numeric clinical bound, as registries write them
THRESH = re.compile(
    r"\b(LVEF|ejection fraction|EF)\b[^.\n]{0,40}?([<>]=?|\u2264|\u2265|less than|greater than|"
    r"at least|no more than)\s*(\d{1,3})\s*%|"
    r"\b(BMI|body[- ]mass index)\b[^.\n]{0,40}?([<>]=?|\u2264|\u2265|at least|greater than)\s*"
    r"(\d{1,2}(?:\.\d)?)|"
    r"\b(eGFR|creatinine clearance)\b[^.\n]{0,40}?([<>]=?|\u2264|\u2265)\s*(\d{1,3})",
    re.I)

idx = {}
for f in os.listdir(CACHE):
    m = re.match(r"(NCT\d+)_", f)
    if m:
        idx[m.group(1)] = os.path.join(CACHE, f)


def eligibility_text(nct):
    p = idx.get(nct)
    if not p:
        return ""
    try:
        j = json.load(io.open(p, encoding="utf-8"))
    except Exception:
        return ""
    el = (((j.get("protocolSection") or {}).get("eligibilityModule")) or {})
    return str(el.get("eligibilityCriteria") or "")


def population_text(obj):
    bits = []
    for k in ("population", "question", "title"):
        v = obj.get(k)
        if isinstance(v, str):
            bits.append(v)
    sc = obj.get("scope") or {}
    if isinstance(sc, dict):
        for v in sc.values():
            if isinstance(v, str):
                bits.append(v)
    for o in (obj.get("outcomes") or []):
        if isinstance(o, dict) and isinstance(o.get("population"), str):
            bits.append(o["population"])
    return " ".join(bits)


rows = []
for p in sorted(glob.glob("ssot/*/*.json")):
    topic = os.path.basename(os.path.dirname(p))
    if os.path.basename(p) != topic + ".json":
        continue
    try:
        obj = json.load(io.open(p, encoding="utf-8"))
    except Exception:
        continue
    trials = [t for t in ((obj.get("inputs") or {}).get("trials") or [])
              if isinstance(t, dict) and t.get("nct")]
    if len(trials) < 1:
        continue
    per_trial = {}
    for t in trials:
        hits = set()
        for m in THRESH.finditer(eligibility_text(t["nct"])):
            g = [x for x in m.groups() if x]
            if len(g) >= 3:
                hits.add(("%s %s %s" % (g[0], g[1], g[2])).lower())
        per_trial[t["nct"]] = hits
    with_bound = [n for n, h in per_trial.items() if h]
    if not with_bound or len(with_bound) != len(per_trial):
        continue                      # not EVERY trial bounded -> not this defect
    pop = population_text(obj)
    pop_bounded = bool(THRESH.search(pop))
    if pop_bounded:
        continue                      # the review states a bound of its own
    rows.append({"topic": topic, "n_trials": len(per_trial),
                 "bounds": sorted({b for h in per_trial.values() for b in h})[:6],
                 "population_head": re.sub(r"\s+", " ", pop)[:120]})

print("=" * 94)
print("PICO WIDER THAN EVERY TRIAL IN IT (numeric eligibility bounds only)")
print("=" * 94)
n_topics = len({os.path.basename(os.path.dirname(p)) for p in glob.glob("ssot/*/*.json")})
print("  topics scanned                                 %4d" % n_topics)
print("  topics where EVERY trial carries a numeric bound")
print("  and the review states none                     %4d  <- A LOWER BOUND" % len(rows))
print("")
for r in sorted(rows, key=lambda x: -x["n_trials"]):
    print("  %-40s %d trial(s), all bounded" % (r["topic"][:40], r["n_trials"]))
    print("      trial bounds: %s" % "; ".join(r["bounds"]))
    print("      review says:  %s" % (r["population_head"] or "(no population text found)"))
json.dump(rows, io.open(r"F:\claude-temp\pend\pico_sweep.json", "w", encoding="utf-8"),
          indent=1)
print("")
print("  detail -> pico_sweep.json")
print("")
print("  Each of these is either a PICO to narrow or an indirectness rating to revisit.")
print("  Leaving the population broad AND indirectness 'not serious' is not available.")
print("  NOT the whole class: a PICO can be wider in ways no number expresses.")
