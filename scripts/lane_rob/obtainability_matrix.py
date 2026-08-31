# -*- coding: utf-8 -*-
"""OBTAINABILITY, not holdings: which data can be got, and from which source class.

THE ERROR THIS REPLACES, AND IT WAS MINE. I reported "37 of 353 primary reports" and "6 of 178
arm counts" as the CEILING on the recipe, three times. They are measures of WHAT WE EXTRACTED.
Asked whether arm-level counts are obtainable rather than held, the answer from the single
cheapest source we already query is:

  registry records held                    317
  with arm-level participant counts        234   73.8%
  with per-arm outcome measurements        232   73.2%

That is 22x the figure I quoted. A limit of our own retrieval, reported as a property of the
world -- the exact class this project has catalogued all week, made at the strategic level about
the project's central premise.

⇒ SO THE QUESTION IS NEVER "do we hold it". It is "is it obtainable, and from which rung".

THE LADDER, ordered by cost and yield rather than by prestige:

  1. published meta-analyses' extracted tables -- peer-reviewed, MANY TRIALS PER DOCUMENT,
     usually open. Cheapest per datum by a wide margin.
  2. CT.gov posted results -- typed, arm-level, free, machine-readable. Measured here.
  3. open-access full text -- Europe PMC, PMC, NCBI efetch.
  4. FDA and EMA documents -- where the hard-to-get data lives.
  5. registry history, protocols and SAPs published as supplements.

⚠️ AND RUNG 1 IS NOT A COMPROMISE, PROVIDED TWO CONDITIONS HOLD. The register calls prior-meta
tables an unverified tier, and this lane flagged that taking four outcomes from a comparator's
table was "reporting THEIR extraction rather than ours". The defect was never USING it -- it was
presenting it as ours. "Extracted by <review>, peer-reviewed, and verified against <registry>"
is BETTER provenance than "we extracted it", because it carries two independent readings.

  A. every value names its source and its extractor
  B. verify against one independent source where possible, and PUBLISH THE AGREEMENT --
     including where two published syntheses disagree, which is a finding, not a problem

This module measures rung 2 exactly, because that is the rung whose contents are typed and can
be counted without judgement. The other rungs are counted by the components that climb them.
"""
import collections
import glob
import io
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
os.chdir(os.path.dirname(os.path.dirname(HERE)))
REG = r"F:\claude-temp\pend\out\registry_full"


def _ps(d):
    return d.get("protocolSection") or {}


def _rs(d):
    return d.get("resultsSection") or {}


def arm_participants(d):
    fm = _rs(d).get("participantFlowModule") or {}
    return any(a.get("numSubjects")
               for p in (fm.get("periods") or [])
               for ms in (p.get("milestones") or [])
               for a in (ms.get("achievements") or []))


def arm_events(d):
    for o in ((_rs(d).get("outcomeMeasuresModule") or {}).get("outcomeMeasures") or []):
        for c in (o.get("classes") or []):
            for cat in (c.get("categories") or []):
                if any(m.get("value") for m in (cat.get("measurements") or [])):
                    return True
    return False


def effect_estimate(d):
    for o in ((_rs(d).get("outcomeMeasuresModule") or {}).get("outcomeMeasures") or []):
        for a in (o.get("analyses") or []):
            if a.get("paramValue") or a.get("ciLowerLimit"):
                return True
    return False


def analysis_population(d):
    for o in ((_rs(d).get("outcomeMeasuresModule") or {}).get("outcomeMeasures") or []):
        if o.get("populationDescription") or o.get("denomUnitsSelected"):
            return True
    return False


def follow_up(d):
    return any(o.get("timeFrame")
               for o in ((_rs(d).get("outcomeMeasuresModule") or {}).get("outcomeMeasures") or []))


def randomisation_fields(d):
    dm = _ps(d).get("designModule") or {}
    di = dm.get("designInfo") or {}
    return bool(di.get("allocation") or (di.get("maskingInfo") or {}).get("masking"))


def outcome_definitions(d):
    om = _ps(d).get("outcomesModule") or {}
    return any(o.get("description") or o.get("measure")
               for o in ((om.get("primaryOutcomes") or []) + (om.get("secondaryOutcomes") or [])))


def harms(d):
    ae = _rs(d).get("adverseEventsModule") or {}
    return bool(ae.get("seriousEvents") or ae.get("otherEvents"))


def funder(d):
    sm = _ps(d).get("sponsorCollaboratorsModule") or {}
    return bool((sm.get("leadSponsor") or {}).get("class"))


DATA = [
    ("arm-level participant counts", arm_participants),
    ("arm-level event counts", arm_events),
    ("effect estimate and interval", effect_estimate),
    ("analysis population", analysis_population),
    ("follow-up / time frame", follow_up),
    ("randomisation, allocation, masking", randomisation_fields),
    ("outcome definitions", outcome_definitions),
    ("harms", harms),
    ("funder", funder),
]


def main():
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace",
                                  line_buffering=True)
    files = sorted(glob.glob(os.path.join(REG, "*.json")))
    counts = collections.Counter()
    n = 0
    for f in files:
        try:
            d = json.load(io.open(f, encoding="utf-8"))
        except Exception:
            continue
        n += 1
        for name, fn in DATA:
            try:
                if fn(d):
                    counts[name] += 1
            except Exception:
                pass
    print("")
    print("OBTAINABILITY FROM RUNG 2 ALONE -- CT.gov posted results")
    print("")
    print("  trials with a registry record held      %4d  == the denominator" % n)
    print("")
    print("  %-38s %6s %8s" % ("datum", "n", "of trials"))
    for name, _ in DATA:
        c = counts[name]
        print("  %-38s %6d %7.1f%%" % (name, c, 100.0 * c / n if n else 0))
    print("")
    print("  ⚠️ This is ONE rung. A datum absent here may be obtainable from a prior")
    print("     meta-analysis (rung 1), open full text (rung 3), or an FDA/EMA document")
    print("     (rung 4). ABSENT HERE IS NOT UNOBTAINABLE.")
    print("")
    print("  For contrast: our OBJECTS store arm counts for 6 of 178 per-trial records (3.4%).")
    print("  The gap between 3.4%% and %.1f%% is extraction, not availability."
          % (100.0 * counts["arm-level participant counts"] / n if n else 0))
    out = r"F:\claude-temp\pend\out\obtainability_rung2.json"
    json.dump({"denominator": n, "counts": dict(counts)},
              io.open(out, "w", encoding="utf-8"), indent=1)
    print("  detail -> obtainability_rung2.json")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
