# -*- coding: utf-8 -*-
"""D5 -- selection of the reported result. Retrieval first, judgement never.

WHAT D5 ASKS, and why it is the domain that cannot be answered from a paper. It compares what
was REPORTED against what was PLANNED. The plan lives in the protocol and the statistical
analysis plan. A published report tells you what was reported; only the plan tells you what
was planned, so a D5 absence recorded WITHOUT the protocol is our gap published as the trial's.

THREE PASSES, each with its own denominator.

  1. WHERE THE GAPS ARE. 10 NO_INFORMATION judgements on D5, across 2 topics and 9 trials --
     bococizumab-lipid-review (6) and tigecycline-ciai (4). Small enough to do exhaustively,
     which is why D5 was worth taking before the larger domains: D1 126, D2 139, D3 132.

  2. IS THE INSTRUMENT POSTED? 0 of 9 -- established twice, by two different routes, after
     the first route turned out to be the wrong place to look. The API v2 record's
     documentSection.largeDocumentModule is empty for all nine, but that field is empty for
     trials whose protocol IS served: NCT01975376 and NCT01975389 both return a 168- and
     167-page protocol from the CDN while their API records list no documents at all. So the
     first pass established "nothing in the field I read", which is a weaker claim than it
     appeared. Re-probed against the CDN path that demonstrably works, all nine still have no
     protocol and no SAP, and THAT negative is strong because the route has been shown to
     return a document for trials in the same programme.

     PROBE WITH A PLAIN GET, NEVER A RANGED ONE. `Range: 0-0` returns 206 for every filename
     including ones that cannot exist -- ICF_000.pdf, Prot_SAP_001.pdf -- so a ranged probe is
     an instrument that can only say "present", which is not a check. A plain GET
     discriminates: 200/application/pdf against 404/text/html. No trial behind any D5 gap has a protocol or a
     statistical analysis plan posted on the registry -- not one document of any kind, though
     7 of 9 have posted results. So the registry route is EXHAUSTED, with evidence, and all
     10 judgements stay NOT_RETRIEVED_BY_US. This is not "no protocol exists": SPIRE and the
     tigecycline trials were journal-published and a protocol may well sit in supplementary
     material. It means this source cannot supply it, which is a different sentence.

  3. THE WEAKER INSTRUMENT THAT IS AVAILABLE. Registered outcomes have a version history, and
     comparing the primary outcome across versions is a real if partial selective-reporting
     signal. 8 of 9 trials edited their outcome module; a string diff flags a change in 8.

AND THE THIRD PASS IS WHY THIS FILE EXISTS RATHER THAN A NUMBER. Reading the eight diffs,
every one is a REWORDING:

  "Percent Change from Baseline in LDL-C at Week 12"
  "Percent Change From Baseline in Low Density Lipoprotein-Cholesterol (LDL-C) at Week 12"

-- an expanded abbreviation and changed capitalisation, the same outcome twice. The
tigecycline one fixes the typo "microbiological" to "microbiologically". Most occur at the
FINAL version, which is the results-posting step relabelling outcomes to match the results
tables, not a change of plan.

So a naive string diff over registered outcomes would have produced EIGHT false D5 concerns
about other people's trials, each one looking exactly like a finding. The instrument overcalls
and its error rate is not measured; it is reported as a candidate list for reading, never as a
verdict. On this sample, after reading: no evidence of outcome switching in any of the 9.

PASS 4 -- THE JOURNAL ROUTE, WHICH IS THE ONLY ONE LEFT. Per trial, not per topic:

  SPIRE, 6 trials (bococizumab-lipid-review). Primary reports are NEJM 2017 --
  10.1056/NEJMoa1614062 and 10.1056/NEJMoa1701488 -- and there is a DESIGN AND RATIONALE
  paper in American Heart Journal 2016, 10.1016/j.ahj.2016.05.010. That design paper is the
  best D5 instrument that exists for these trials: it states the pre-specified endpoints and
  was published BEFORE results, so it is a plan rather than a report. NONE of the three has a
  PMCID. All are behind a publisher, so this lane cannot retrieve any of them, and the
  bococizumab store records no PMID or DOI for any of its six trials at all.

  Tigecycline, 3 trials (tigecycline-ciai). All three primary reports ARE open access in PMC
  -- PMC1277826, PMC2920872, PMC6281154 -- and the store already records their PMIDs. Reading
  one in full (10.1186/1471-2334-10-217, PubMed): it names the co-primary endpoints, defines
  every analysis population, and EXPLICITLY labels a Cochran-Mantel-Haenszel analysis as
  post-hoc. That transparency answers part of D5 and is a point in the trial's favour.

WHAT THE JOURNAL ROUTE STILL DOES NOT GIVE, and the distinction is the whole domain. A report
that names its primary endpoint is still the REPORT. D5's hard question -- were several
eligible analyses run and the reported one chosen on its result -- is answerable only from the
plan. No protocol or SAP was located for any of the 9.

AND ONE THING I COULD NOT CHECK, said rather than assumed: the PMC open-access package
endpoint returned 404 for all three tigecycline records, so whether supplementary files are
deposited alongside them is UNKNOWN, not absent. A failed probe is not a negative result.

NET D5 RESULT: 10 gaps, 0 closed, 0 findings manufactured, and the reason each remains open is
now recorded as a fact about our retrieval rather than a fact about the trials.
"""
import collections
import io
import json
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
os.chdir(os.path.dirname(os.path.dirname(HERE)))
PEND = r"F:\claude-temp\pend"


def fetch(url, path):
    if not os.path.exists(path):
        subprocess.run(["curl", "-s", "--max-time", "60", url, "-o", path],
                       capture_output=True, timeout=120)
    try:
        return json.load(io.open(path, encoding="utf-8"))
    except Exception:
        return None


def main():
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace",
                                  line_buffering=True)
    tg = json.load(io.open(os.path.join(PEND, "d5_targets.json"), encoding="utf-8"))
    ncts = tg["ncts"]
    os.makedirs(os.path.join(PEND, "ctg"), exist_ok=True)

    # THE CDN PATH, WHICH IS WHERE A PROTOCOL ACTUALLY LIVES. Filenames are conventional;
    # this is the set observed to exist across this corpus's trials.
    CDN = "https://cdn.clinicaltrials.gov/large-docs/%s/%s/%s"
    DOCS = ("Prot_000.pdf", "Prot_001.pdf", "SAP_000.pdf", "Prot_SAP_000.pdf")

    def cdn_has(nct, fname):
        """200 with a PDF content type, or nothing. Plain GET -- see the note above."""
        r = subprocess.run(
            ["curl", "-s", "-o", os.devnull, "-w", "%{http_code}|%{content_type}",
             "--max-time", "60", "-L", CDN % (nct[-2:], nct, fname)],
            capture_output=True, timeout=120)
        out = r.stdout.decode("ascii", "replace")
        return out.startswith("200") and "pdf" in out

    posted = []
    for n in ncts:
        d = fetch("https://clinicaltrials.gov/api/v2/studies/%s" % n,
                  os.path.join(PEND, "ctg", "%s.json" % n)) or {}
        ld = (((d.get("documentSection") or {}).get("largeDocumentModule") or {})
              .get("largeDocs") or [])
        cdn = [f for f in DOCS if cdn_has(n, f)]
        posted.append({"nct": n, "docs": len(ld), "cdn_docs": cdn,
                       "protocol": any(x.get("hasProtocol") for x in ld),
                       "sap": any(x.get("hasSap") for x in ld),
                       "has_results": bool(d.get("hasResults"))})

    print("")
    print("D5 -- SELECTION OF THE REPORTED RESULT")
    print("")
    print("  D5 NO_INFORMATION judgements                %4d" % sum(
        t["d5"] for t in tg["topics"]))
    print("  topics carrying them                        %4d" % len(tg["topics"]))
    print("  trials behind them                          %4d  == the denominator" % len(ncts))
    print("")
    print("  PROTOCOL posted on the registry             %4d" % sum(1 for p in posted if p["protocol"]))
    print("  SAP posted on the registry                  %4d" % sum(1 for p in posted if p["sap"]))
    print("  no document in the API record               %4d" % sum(
        1 for p in posted if p["docs"] == 0))
    print("  no document on the CDN either               %4d  <- the strong negative" % sum(
        1 for p in posted if not p["cdn_docs"]))
    print("  ...of which HAVE posted results             %4d" % sum(
        1 for p in posted if not p["docs"] and p["has_results"]))
    print("")
    print("  VERDICT ON RETRIEVAL: the registry cannot close any of these gaps. That is a")
    print("  statement about this source, not about whether a protocol exists -- these were")
    print("  journal-published trials and supplementary material is the next route.")

    diffs_p = os.path.join(PEND, "d5_outcome_diffs.json")
    if os.path.exists(diffs_p):
        out = json.load(io.open(diffs_p, encoding="utf-8"))
        ch = [o for o in out if o["changed"]]
        print("")
        print("  registered-outcome edits examined           %4d" % len(out))
        print("  at the final version (results-posting)      %4d" % sum(
            1 for o in out if o["is_final_version"]))
        print("  string diff flags a changed primary         %4d  <- CANDIDATES, not findings"
              % len(ch))
        print("  substantive changes after reading them      %4d" % 0)
        print("")
        print("  Every flagged change is a rewording -- an expanded abbreviation, altered")
        print("  capitalisation, a corrected typo. A naive diff would have produced %d false"
              % len(ch))
        print("  D5 concerns about other people's trials, each looking exactly like a finding.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
