"""Was a harmonised outcome available at SOME rank that we did not look for?

WHY THIS EXISTS, AND WHY IT DID NOT BEFORE. An independent reviewer from another model
family judged our SGLT2 withdrawal disproportionate: the four trials genuinely differed on
their PRIMARY endpoint, but a matched two-component outcome sat one rank down -- the
EMPEROR trials' own primary, and DAPA-HF's SECONDARY, in a registration we had already
read. The rebuilt pool is HR 0.7636 (0.7062-0.8258) with tau-squared 0 and I-squared 0.
WE WITHHELD AN UNAMBIGUOUS, HOMOGENEOUS ESTIMATE.

THE ASYMMETRY THAT LET IT HAPPEN. Every guard built this week protects against CLAIMING
TOO MUCH -- net-deletion refusal, the content gate, the estimand checks, the four-limb
reading. NOT ONE protects against WITHHOLDING TOO MUCH. A project whose ethic is caution
will build only the checks that catch overreach, and will not notice the errors that look
like restraint.

THE FAILURE MODE OF THIS SWEEP IS THAT IT FINDS NOTHING. It is examining verdicts produced
by the same reasoning that is now writing the examiner. So it is DELIBERATELY MECHANICAL:

  IT DOES NOT READ OUR VERDICT TEXT AT ALL. No poolable_reason, no which_limb_fails, no
  withdrawal note. It compares registered outcome STRINGS across trials and nothing else.
  The verdict cannot influence the test, because the test never sees it.

THREE CATEGORIES, NOT TWO:
  DISPROPORTIONATE  an outcome concept appears in EVERY trial in the set at SOME rank.
                    A recoverable estimate we did not build.
  STANDS            no concept is common to all trials at any recorded rank. The
                    withdrawal is supported and that is a real finding for that topic.
  UNASSESSABLE      the object does not record enough registry detail to tell.
                    NOT A PASS. Reported separately and counted.

Matching is on normalised concept tokens, not whole strings -- "Time to First Event of
Adjudicated Cardiovascular Death or Adjudicated Hospitalisation for Heart Failure" and
"Composite Endpoint of CV Death or Hospitalization Due to Heart Failure" are the same
concept in different words, and a whole-string match would call them different. That
normalisation is the same discipline the entity/case defects taught: MATCHING TEXT YOU DO
NOT CONTROL REQUIRES NORMALISING IT FIRST.
"""
from __future__ import annotations
import io
import json
import os
import re
import sys

if __name__ == "__main__":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# concept -> the surface forms that denote it. Deliberately coarse: a false DISPROPORTIONATE
# costs one hand-read, a false STANDS costs a withheld estimate.
# adverse_events REMOVED from the concept list, not carried as noise. EVERY trial reports
# adverse events, so it matched 15 topics and none of them is a poolable efficacy question.
# Carrying known-false flags trains a reader to skim the list, which is exactly how this
# corpus ended up with gates nobody read.
CONCEPTS = {
    "cv_death": r"cardiovascular death|cv death|death from cardiovascular|vascular death",
    "hf_hosp": r"hospitali\w*\s+(?:for|due to|because of)\s+heart failure|heart failure hospitali",
    "all_death": r"all[- ]cause mortality|all[- ]cause death|death from any cause|overall survival",
    "mi": r"myocardial infarction",
    "stroke": r"\bstroke\b",
    "clinical_cure": r"clinical cure|clinical response|clinical success",
    "micro_cure": r"microbiologic\w* (?:eradication|response|success|cure)",
    "hiv_infection": r"hiv[- ]1? ?(?:infection|incidence|seroconversion)",
    "ldl": r"ldl|low density lipoprotein",
    "kccq": r"kccq|kansas city",
    "egfr": r"egfr|glomerular filtration",
    "hf_event": r"worsening heart failure|urgent (?:heart failure )?visit|heart failure event",
}
COMPILED = {k: re.compile(v, re.I) for k, v in CONCEPTS.items()}


def concepts_of(texts):
    got = set()
    for t in texts or []:
        if not isinstance(t, str):
            continue
        for k, rx in COMPILED.items():
            if rx.search(t):
                got.add(k)
    return got


def main() -> int:
    ss = os.path.join(REPO, "ssot")
    disp, stands, unassessable = [], [], []
    for d in sorted(os.listdir(ss)):
        f = os.path.join(ss, d, d + ".json")
        if not os.path.exists(f):
            continue
        try:
            o = json.load(io.open(f, encoding="utf-8"))
        except Exception:
            continue
        bo = (o.get("results") or {}).get("by_outcome") or {}
        # is ANY outcome block a withdrawal / non-pool?
        withdrawn = any(isinstance(b, dict) and (b.get("poolable") is False
                        or (b.get("pooled") or {}).get("withdrawn"))
                        for b in bo.values())
        if not withdrawn:
            continue
        trials = ((o.get("inputs") or {}).get("trials") or [])
        sets = []
        for t in trials:
            if not isinstance(t, dict):
                continue
            texts = []
            for key in ("registered_primaries", "registered_secondaries",
                        "registered_outcomes"):
                v = t.get(key)
                if isinstance(v, list):
                    texts += v
                elif isinstance(v, str):
                    texts.append(v)
            if texts:
                sets.append(concepts_of(texts))
        if len(sets) < 2:
            unassessable.append((d, "%d trial(s) record registered outcome text"
                                 % len(sets)))
            continue
        common = set.intersection(*sets)
        if common:
            disp.append((d, len(sets), sorted(common)))
        else:
            stands.append((d, len(sets), [sorted(s)[:3] for s in sets[:3]]))

    total = len(disp) + len(stands) + len(unassessable)
    print("WITHDRAWN / NON-POOLED TOPICS EXAMINED: %d" % total)
    print()
    print("  DISPROPORTIONATE -- a concept common to EVERY trial at some rank: %d"
          % len(disp))
    for d, n, c in disp:
        print("      %-44s k=%d  shared: %s" % (d[:43], n, ", ".join(c)[:44]))
    print()
    print("  WITHDRAWAL STANDS -- no concept common to all trials: %d" % len(stands))
    print()
    print("  UNASSESSABLE -- object lacks the registry detail. NOT A PASS: %d"
          % len(unassessable))
    print()
    print("DENOMINATOR: %d withdrawals checked, %d potentially affected, %d unassessable."
          % (total, len(disp), len(unassessable)))
    print()
    print("THIS SWEEP NEVER READ A VERDICT. It compares registered outcome strings and")
    print("nothing else, because it examines verdicts produced by the same reasoning that")
    print("wrote it. A DISPROPORTIONATE flag is where to look, not what you will find:")
    print("a shared concept does not prove a poolable quantity -- the SGLT2 case needed a")
    print("hand read to confirm the matched endpoint was the same first-event composite.")
    json.dump({"disproportionate": [d for d, _, _ in disp],
               "stands": [d for d, _, _ in stands],
               "unassessable": [d for d, _ in unassessable]},
              io.open(os.path.join(REPO, ".proportionality.json"), "w",
                      encoding="utf-8", newline="\n"), ensure_ascii=False, indent=1)
    return 0


if __name__ == "__main__":
    sys.exit(main())
