"""Reconstruct the APIXABAN_VTE review: kill the invalid pooled RR 2.44 and split
the conflated question into five coherent, comparator- and population-specific ones.

Every number written here was verified in this session against ClinicalTrials.gov
API v2 posted results and the PubMed abstract of the primary publication. Sources
are recorded per number in outputs/apixaban_vte_correction_ledger.json.

Nothing is back-computed from a percentage and nothing is imputed. Where a count
could not be read off a primary surface it is carried as published-effect prose in
the trial snippet and is NOT written as a switchable 2x2 outcome.

The script is anchor-based and idempotent: it asserts each anchor is present exactly
once, and re-running it on an already-patched file is a no-op that reports SKIP.
"""
import io
import json
import re
import sys

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

FULL = "APIXABAN_VTE_AUTO_FULL_REVIEW.html"

applied, skipped, failed = [], [], []


def sub_once(text, old, new, tag, *, required=True):
    """Replace `old` exactly once. Idempotent: if `new` is already present, SKIP."""
    n = text.count(old)
    if n == 1:
        applied.append(tag)
        return text.replace(old, new, 1)
    if new and new in text:
        skipped.append(tag + " (already applied)")
        return text
    (failed if required else skipped).append(f"{tag} (anchor count={n})")
    return text


# =========================================================================
# 1. The corrected ledger.
#
#    Five records, five DIFFERENT questions. Every record carries the scope
#    fields the compatibility gate reads (rmPopulation / rmIntervention /
#    rmComparator / rmEndpointKind) so the gate can name WHY a set is not
#    poolable rather than just refusing.
#
#    Per-outcome denominators go in nT/nC, which the app's outcome switcher
#    honours (see setSelectedOutcome: `null!=oc.nT&&(t.data.tN=oc.nT)`).
#    That is what lets AMPLIFY carry safety-population counts for major
#    bleeding without silently re-using the ITT efficacy denominators.
# =========================================================================

AMPLIFY_SNIPPET = (
    "AMPLIFY (Agnelli 2013, N Engl J Med 2013;369:799-808, PMID 23808982, "
    "DOI 10.1056/NEJMoa1302507; ClinicalTrials.gov NCT00643201 posted results). "
    "Acute VTE treatment: apixaban 10 mg BID x7d then 5 mg BID x6 months vs "
    "enoxaparin followed by warfarin, 5,395 patients analysed. Recurrent VTE or "
    "VTE-related death 59/2609 vs 71/2635 (RR 0.84, 95% CI 0.60-1.18; noninferior). "
    "ISTH major bleeding 15/2676 vs 49/2689 (RR 0.31, 95% CI 0.17-0.55; superior). "
    "Major-or-CRNM bleeding 4.3% vs 9.7% (RR 0.44, 95% CI 0.36-0.55) - reported as a "
    "published effect only; per-arm counts for that composite were not read off a "
    "primary surface, so no 2x2 is claimed for it."
)

AMPLIFY_EXT_SNIPPET = (
    "AMPLIFY-EXT (Agnelli 2013, N Engl J Med 2013;368:699-708, PMID 23216615, "
    "DOI 10.1056/NEJMoa1207541; ClinicalTrials.gov NCT00633893 posted results). "
    "EXTENDED treatment after 6-12 months of anticoagulation: apixaban 2.5 mg BID or "
    "5 mg BID vs PLACEBO for 12 months, 2,486 randomised. Recurrent symptomatic VTE or "
    "VTE-related death: placebo 73/829 (8.8%), apixaban 2.5 mg 14/840 (1.7%), apixaban "
    "5 mg 14/813 (1.7%). Major bleeding 0.5% / 0.2% / 0.1%; CRNM bleeding 2.3% / 3.0% / "
    "4.2% - published percentages only, per-arm safety counts not read off a primary "
    "surface. THREE-ARM TRIAL: both apixaban contrasts share the SAME placebo group, so "
    "they must never be combined with each other."
)

COBRRA_SNIPPET = (
    "COBRRA (Castellucci 2026, N Engl J Med 2026;394:1051-1060, PMID 41812192, "
    "DOI 10.1056/NEJMoa2510703; ClinicalTrials.gov NCT03266783 posted results). "
    "Acute symptomatic PE or proximal DVT, PROBE design, apixaban vs RIVAROXABAN for "
    "3 months, 2,760 randomised. Clinically relevant bleeding 44/1345 vs 96/1355 "
    "(RR 0.46, 95% CI 0.33-0.65; P<0.001). Head-to-head DOAC comparison: the comparator "
    "is another anticoagulant, NOT placebo and NOT conventional therapy."
)

GYN_SNIPPET = (
    "Guntupalli 2020 (JAMA Netw Open 2020;3(6):e207410, PMID 32589230, "
    "DOI 10.1001/jamanetworkopen.2020.7410; ClinicalTrials.gov NCT02366871 posted "
    "results). POSTOPERATIVE THROMBOPROPHYLAXIS after surgery for gynaecologic "
    "malignancy - not treatment of an established VTE. Apixaban 2.5 mg PO BID vs "
    "enoxaparin 40 mg SC daily for 28 days, 90-day follow-up, 400 randomised. "
    "Co-primary outcomes: ISTH major bleeding 1/204 vs 1/196 and clinically relevant "
    "non-major bleeding 12/204 vs 19/196. Secondary VTE 2/204 vs 3/196. Registered "
    "PHASE2."
)

RAMBLE_SNIPPET = (
    "RAMBLE (ClinicalTrials.gov NCT02829957 posted results; NO journal publication "
    "found on PubMed - the registry is the only source). 19 menstruating patients aged "
    "18-50 anticoagulated for VTE or atrial fibrillation, randomised open-label to "
    "RIVAROXABAN (n=8) or APIXABAN (n=11) for 3 months. PRIMARY OUTCOME IS CONTINUOUS: "
    "PBAC score at 3 months, median (full range) - rivaroxaban 292 (74-600), n=6; "
    "apixaban 146 (3-378), n=10. It is NOT a binary event outcome and no risk ratio can "
    "be formed from it; medians with full ranges at n=6 and n=10 cannot be converted to "
    "mean and SD without fabricating a distribution for a heavily skewed score. The "
    "counts 3 and 1 previously shown as 'PBAC' are the SECONDARY outcome 'crossed over "
    "to another anticoagulant', and the arm carrying 3 is RIVAROXABAN. Severely "
    "underpowered pilot; every bleeding and thrombotic secondary is 0-3 events."
)

def js(v):
    """Python value -> JS literal. None -> null, never the identifier `None`.

    This is the guard from the 2026-05-24 placeholder-leak incident: a bare
    Python None interpolated into a JS object literal renders as the identifier
    `None` and the whole app dies with a ReferenceError.
    """
    if v is None:
        return "null"
    if isinstance(v, bool):
        return "!0" if v else "!1"
    if isinstance(v, (int, float)):
        return repr(v)
    if isinstance(v, str):
        return json.dumps(v, ensure_ascii=False)
    if isinstance(v, (list, tuple)):
        return "[" + ",".join(js(x) for x in v) + "]"
    if isinstance(v, dict):
        return "{" + ",".join(f"{json.dumps(k)}:{js(x)}" for k, x in v.items()) + "}"
    raise TypeError(type(v))


def outcome(label, title, otype, tE, cE, nT, nC, estimand="RR", extra=None):
    o = {
        "shortLabel": label,
        "title": title,
        "type": otype,
        "tE": tE,
        "cE": cE,
        "nT": nT,
        "nC": nC,
        "matchScore": 95 if otype in ("PRIMARY", "CONTINUOUS") else 70,
        "estimandType": estimand,
    }
    if extra:
        o.update(extra)
    return o


def evidence(label, source, text):
    return {"label": label, "source": source, "text": text, "fullText": text, "highlights": []}


def record(*, name, pmid, doi, phase, year, tN, cN, tE, cE, question, population,
           intervention, comparator, endpoint_kind, outcomes, rob, rob_source,
           snippet, nct, docs, phase_eligible=True):
    return {
        "name": name,
        "pmid": pmid,
        "doi": doi,
        "phase": phase,
        "year": year,
        "tE": tE,
        "tN": tN,
        "cE": cE,
        "cN": cN,
        "group": question,
        "publishedHR": None,
        "hrLCI": None,
        "hrUCI": None,
        "pubHR": None,
        "pubHR_LCI": None,
        "pubHR_UCI": None,
        "allOutcomes": outcomes,
        "rob": rob,
        "robSource": rob_source,
        "snippet": snippet,
        "sourceUrl": f"https://clinicaltrials.gov/study/{nct}",
        "ctgovUrl": f"https://clinicaltrials.gov/study/{nct}",
        # --- scope fields read by the estimand-compatibility gate ---
        "rmQuestion": question,
        "rmPopulation": population,
        "rmIntervention": intervention,
        "rmComparator": comparator,
        "rmEndpointKind": endpoint_kind,
        "rmPhaseEligible": phase_eligible,
        # --- honest provenance, replacing the empty evidence[] that made the
        #     panel report "No source" for trials that plainly have sources ---
        "rmCtgovResults": True,
        "rmProtocolDocument": docs.get("protocol", False),
        "rmSapDocument": docs.get("sap", False),
        "evidence": docs["evidence"],
    }


REAL_DATA = {
    "NCT00643201": record(
        name="AMPLIFY", pmid="23808982", doi="10.1056/NEJMoa1302507",
        phase="III", year=2013, tN=2609, cN=2635, tE=59, cE=71,
        question="A. Acute VTE treatment: apixaban vs enoxaparin/warfarin",
        population="Acute symptomatic DVT or PE, treatment",
        intervention="Apixaban 10 mg BID x7d then 5 mg BID",
        comparator="Enoxaparin followed by warfarin (conventional therapy)",
        endpoint_kind="binary",
        outcomes=[
            outcome("RecurrentVTEorVTEDeath",
                    "Recurrent symptomatic VTE or VTE-related death (6 months, primary)",
                    "PRIMARY", 59, 71, 2609, 2635),
            outcome("MajorBleeding",
                    "ISTH major bleeding (safety population; denominators differ from ITT)",
                    "SAFETY", 15, 49, 2676, 2689),
        ],
        rob=["low", "low", "low", "low", "low"],
        rob_source="Randomised, double-blind, double-dummy; adjudicated outcomes; ITT analysis.",
        snippet=AMPLIFY_SNIPPET, nct="NCT00643201",
        docs={"protocol": True, "sap": True, "evidence": [
            evidence("CT.gov Structured Results",
                     "ClinicalTrials.gov NCT00643201 Results Section (API v2, fetched 2026-07-30)",
                     "Apixaban: 59/2609. Enoxaparin + Warfarin: 71/2635. Primary outcome: "
                     "adjudicated composite of symptomatic recurrent VTE or VTE-related death."),
            evidence("Primary publication abstract",
                     "PubMed PMID 23808982, N Engl J Med 2013;369(9):799-808",
                     "Primary efficacy outcome 59 of 2609 (2.3%) vs 71 of 2635 (2.7%); RR 0.84 "
                     "(95% CI 0.60-1.18). Major bleeding 0.6% vs 1.8%; RR 0.31 (95% CI 0.17-0.55)."),
        ]},
    ),
    "NCT00633893": record(
        name="AMPLIFY-EXT", pmid="23216615", doi="10.1056/NEJMoa1207541",
        phase="III", year=2013, tN=840, cN=829, tE=14, cE=73,
        question="B. Extended treatment after 6-12 months: apixaban vs placebo",
        population="VTE, extended treatment after 6-12 months of anticoagulation",
        intervention="Apixaban 2.5 mg BID (default contrast) or 5 mg BID",
        comparator="Placebo",
        endpoint_kind="binary",
        outcomes=[
            outcome("RecurrentVTEorVTEDeath_2p5mg",
                    "Recurrent symptomatic VTE or VTE-related death - apixaban 2.5 mg BID vs placebo (primary)",
                    "PRIMARY", 14, 73, 840, 829),
            outcome("RecurrentVTEorVTEDeath_5mg",
                    "Recurrent symptomatic VTE or VTE-related death - apixaban 5 mg BID vs the SAME placebo arm (primary)",
                    "PRIMARY", 14, 73, 813, 829),
        ],
        rob=["low", "low", "low", "low", "low"],
        rob_source="Randomised, double-blind, placebo-controlled; adjudicated outcomes; ITT analysis.",
        snippet=AMPLIFY_EXT_SNIPPET, nct="NCT00633893",
        docs={"protocol": True, "sap": True, "evidence": [
            evidence("CT.gov Structured Results",
                     "ClinicalTrials.gov NCT00633893 Results Section (API v2, fetched 2026-07-30)",
                     "Three arms: apixaban 2.5 mg (840), apixaban 5 mg (813), placebo (829). "
                     "Both apixaban arms are compared against the same placebo group."),
            evidence("Primary publication abstract",
                     "PubMed PMID 23216615, N Engl J Med 2013;368(8):699-708",
                     "Recurrent VTE or VTE-related death: 73 of 829 placebo (8.8%), 14 of 840 "
                     "apixaban 2.5 mg (1.7%), 14 of 813 apixaban 5 mg (1.7%)."),
        ]},
    ),
    "NCT03266783": record(
        name="COBRRA", pmid="41812192", doi="10.1056/NEJMoa2510703",
        phase="IV", year=2026, tN=1345, cN=1355, tE=44, cE=96,
        question="C. Acute VTE treatment, DOAC vs DOAC: apixaban vs rivaroxaban",
        population="Acute symptomatic PE or proximal DVT, treatment",
        intervention="Apixaban 10 mg BID x7d then 5 mg BID",
        comparator="Rivaroxaban 15 mg BID x21d then 20 mg daily",
        endpoint_kind="binary",
        outcomes=[
            outcome("ClinicallyRelevantBleeding",
                    "Adjudicated clinically relevant bleeding, major or CRNM, 3 months (primary)",
                    "PRIMARY", 44, 96, 1345, 1355),
            outcome("MajorBleeding", "Adjudicated major bleeding, 3 months",
                    "SECONDARY", 5, 32, 1345, 1355),
            outcome("CRNMBleeding", "Adjudicated clinically relevant non-major bleeding, 3 months",
                    "SECONDARY", 39, 67, 1345, 1355),
            outcome("RecurrentVTE", "Adjudicated recurrent VTE, 3 months",
                    "SECONDARY", 15, 14, 1345, 1355),
        ],
        rob=["low", "low", "some-concerns", "low", "low"],
        rob_source="PROBE design: open-label allocation with blinded adjudicated end-points.",
        snippet=COBRRA_SNIPPET, nct="NCT03266783",
        docs={"protocol": True, "sap": True, "evidence": [
            evidence("CT.gov Structured Results",
                     "ClinicalTrials.gov NCT03266783 Results Section (API v2, fetched 2026-07-30)",
                     "Apixaban Group: 44/1345. Rivaroxaban Group: 96/1355. Major bleeding 5 vs 32; "
                     "CRNM 39 vs 67; recurrent VTE 15 vs 14."),
            evidence("Primary publication abstract",
                     "PubMed PMID 41812192, N Engl J Med 2026;394(11):1051-1060",
                     "A primary-outcome event occurred in 44 of 1345 (3.3%) apixaban and 96 of 1355 "
                     "(7.1%) rivaroxaban; RR 0.46 (95% CI 0.33-0.65), P<0.001."),
        ]},
    ),
    "NCT02366871": record(
        name="Guntupalli 2020 (gynaecologic-cancer surgery)", pmid="32589230",
        doi="10.1001/jamanetworkopen.2020.7410",
        phase="II", year=2020, tN=204, cN=196, tE=1, cE=1,
        question="D. Postoperative thromboprophylaxis after gynaecologic-cancer surgery: apixaban vs enoxaparin",
        population="Women undergoing surgery for suspected or confirmed gynaecologic malignancy - PROPHYLAXIS, no prior VTE",
        intervention="Apixaban 2.5 mg PO BID for 28 days post-op",
        comparator="Enoxaparin 40 mg SC daily for 28 days post-op",
        endpoint_kind="binary",
        outcomes=[
            outcome("MajorBleeding", "ISTH major bleeding, day 1 to day 90 (co-primary)",
                    "PRIMARY", 1, 1, 204, 196),
            outcome("CRNMBleeding",
                    "Clinically relevant non-major bleeding, day 1 to day 90 (co-primary)",
                    "PRIMARY", 12, 19, 204, 196),
            outcome("VTE", "Venous thromboembolism (DVT or PE), day 1 to day 90",
                    "SECONDARY", 2, 3, 204, 196),
        ],
        rob=["low", "some-concerns", "low", "low", "some-concerns"],
        rob_source="PROBE design: open-label allocation, blinded end-point assessment. "
                   "Registry: alloc=RANDOMIZED, masking=SINGLE, assessor_masked=t.",
        snippet=GYN_SNIPPET, nct="NCT02366871",
        docs={"protocol": True, "sap": True, "evidence": [
            evidence("CT.gov Structured Results",
                     "ClinicalTrials.gov NCT02366871 Results Section (API v2, fetched 2026-07-30)",
                     "Oral Apixaban (204) vs Subcutaneous Enoxaparin (196). Major bleeding 1 vs 1; "
                     "CRNM bleeding 12 vs 19; VTE 2 vs 3."),
            evidence("Registry documents",
                     "ClinicalTrials.gov NCT02366871 document section",
                     "Study Protocol and Statistical Analysis Plan (Prot_SAP_001.pdf) and Informed "
                     "Consent Form (ICF_000.pdf) are attached to the registry record. Contents not read."),
            evidence("Primary publication abstract",
                     "PubMed PMID 32589230, JAMA Netw Open 2020;3(6):e207410",
                     "Major bleeding 1 patient (0.5%) vs 1 patient (0.5%); OR 1.04 (95% CI 0.07-16.76); "
                     "P>.99. CRNM 12 (5.4%) vs 19 (9.7%). VTE 2 (1.0%) vs 3 (1.5%)."),
        ]},
    ),
    "NCT02829957": record(
        name="RAMBLE", pmid="", doi="",
        phase="II/III", year=2020, tN=11, cN=8, tE=None, cE=None,
        question="E. Menstrual blood loss during anticoagulation: apixaban vs rivaroxaban",
        population="Menstruating patients aged 18-50 anticoagulated for VTE or atrial fibrillation",
        intervention="Apixaban 10 mg BID x7d then 5 mg BID (n=11)",
        comparator="Rivaroxaban 15 mg BID x7d then 20 mg daily (n=8)",
        endpoint_kind="continuous",
        outcomes=[
            outcome("PbacScore",
                    "PBAC score at 3 months (PRIMARY, CONTINUOUS): rivaroxaban median 292 "
                    "(full range 74-600), n=6; apixaban median 146 (full range 3-378), n=10. "
                    "No risk ratio exists for this outcome.",
                    "CONTINUOUS", None, None, 10, 6, estimand="MD"),
            outcome("CrossedOverAnticoagulant",
                    "Crossed over to another anticoagulant, 3 months (secondary): apixaban 1/11 vs rivaroxaban 3/8",
                    "SECONDARY", 1, 3, 11, 8),
            outcome("CRNMBleeding",
                    "Clinically relevant non-major bleeding, 3 months (secondary)",
                    "SECONDARY", 0, 3, 11, 8),
            outcome("DiscontinuedDrug",
                    "Discontinued planned drug administration, 3 months (secondary)",
                    "SECONDARY", 2, 4, 11, 8),
            outcome("MajorHaemorrhage", "Major haemorrhage, 3 months (secondary)",
                    "SECONDARY", 0, 0, 11, 8),
            outcome("VTE", "Venous thromboembolism, 3 months (secondary)",
                    "SECONDARY", 0, 0, 11, 8),
        ],
        rob=["low", "high", "some-concerns", "high", "high"],
        rob_source="Open-label, no masking of participants or of the self-reported PBAC primary "
                   "outcome; 3 of 8 and 1 of 11 did not complete; n=19. Registry: alloc=RANDOMIZED, "
                   "masking=NONE.",
        snippet=RAMBLE_SNIPPET, nct="NCT02829957",
        docs={"protocol": True, "sap": True, "evidence": [
            evidence("CT.gov Structured Results",
                     "ClinicalTrials.gov NCT02829957 Results Section (API v2, fetched 2026-07-30)",
                     "Participant flow: FG000 Rivaroxaban STARTED 8, FG001 Apixaban STARTED 11. "
                     "PRIMARY 'PBAC Scores', paramType MEDIAN, dispersion Full Range, unit 'score on "
                     "a scale': Rivaroxaban 292 [74, 600] n=6; Apixaban 146 [3, 378] n=10. "
                     "SECONDARY 'Number of Participants Who Crossed Over to Another Anticoagulant': "
                     "Rivaroxaban 3, Apixaban 1."),
            evidence("Registry documents",
                     "ClinicalTrials.gov NCT02829957 document section",
                     "A Study Protocol (Prot_000.pdf) and a separate Statistical Analysis Plan "
                     "(SAP_001.pdf) are both attached to the registry record. Contents not read."),
            evidence("Publication status",
                     "PubMed search, 2026-07-30",
                     "No journal publication of RAMBLE was found. The registry record is the only "
                     "source. The trial was previously matched to PMID 26272306, which is De Crem "
                     "2015, a retrospective rivaroxaban-vs-VKA questionnaire study cited in RAMBLE's "
                     "own BACKGROUND reference list - not RAMBLE."),
        ]},
    ),
}

NEW_LEDGER_JS = "realData:{" + ",".join(
    f"{k}:{js(v)}" for k, v in REAL_DATA.items()
) + "}"


# =========================================================================
# 2. The estimand-compatibility gate.
#
#    The old gate only fired at k<2. The app's own analysis banner already
#    said "Not a pooled meta-analysis", and the injected Overmind gate said
#    "NOT POOLABLE" - but at k=2 nothing actually stopped computeCore from
#    emitting a diamond. This closes that: the gate is now FAIL-CLOSED on
#    the estimand signature, so an incompatible set cannot produce a pooled
#    estimate no matter how many trials it holds.
# =========================================================================

COMPAT_GATE_JS = r"""
/* --- RapidMeta estimand-compatibility gate (fail-closed) -------------------
   A pooled estimate is only meaningful when every contributing trial answers the
   SAME question: same population, same intervention, same comparator, and an
   endpoint of the same kind. Two trials that both mention apixaban do not
   qualify. This returns a reason string when pooling must be refused, or "" when
   the set is coherent. Fail-closed: anything it cannot verify is refused. */
rmPoolBlockReason(trials){
  try{
    const ts=(trials??[]).filter(t=>t&&t.data);
    if(ts.length<2) return "";           /* k<2 is handled by the single-trial path */
    const sig=t=>[t.data.rmPopulation,t.data.rmIntervention,t.data.rmComparator,
                  t.data.rmEndpointKind].map(v=>String(v??"")).join(" | ");
    const missing=ts.filter(t=>!t.data.rmPopulation||!t.data.rmComparator);
    if(missing.length>0)
      return "Pooling refused: "+missing.length+" trial(s) carry no declared population or "+
             "comparator, so comparability cannot be established. A pooled estimate is only "+
             "emitted when every contributing trial is verified to answer the same question.";
    const groups=new Map();
    for(const t of ts){const s=sig(t);if(!groups.has(s))groups.set(s,[]);groups.get(s).push(t);}
    if(groups.size<=1) return "";
    const lines=[...groups.entries()].map(([s,g])=>{
      const names=g.map(t=>t.data.name??t.id).join(", ");
      const p=s.split(" | ");
      return names+" — population: "+p[0]+"; intervention: "+p[1]+"; comparator: "+p[2]+
             "; endpoint type: "+p[3];
    });
    return "NOT POOLABLE — the selected trials answer "+groups.size+" different questions, "+
           "so no single pooled estimate is defined over them:\n• "+lines.join("\n• ")+
           "\nNo pooled effect, heterogeneity statistic, Bayesian posterior, sequential-analysis "+
           "boundary, NNT or GRADE rating is produced for an incompatible set. Select one question "+
           "at a time.";
  }catch(e){
    return "Pooling refused: the compatibility check could not be evaluated, so the analysis "+
           "fails closed rather than emitting an unverified pooled estimate.";
  }
},"""


def main():
    src = open(FULL, encoding="utf-8", newline="").read()
    before = len(src)
    print(f"{FULL}: {before:,} bytes")

    # ---- 1. swap the ledger --------------------------------------------
    m = re.search(r'realData:\{NCT02366871:\{name:"NCT02366871".*?evidence:\[\]\}\},async init\(\)',
                  src, re.S)
    if m:
        src = src[:m.start()] + NEW_LEDGER_JS + ",async init()" + src[m.end():]
        applied.append("L1 realData ledger rebuilt (2 records -> 5, arms/outcomes/provenance corrected)")
    elif '"NCT00643201"' in src or "NCT00643201:{" in src:
        skipped.append("L1 realData ledger (already applied)")
    else:
        failed.append("L1 realData ledger (anchor not found)")

    # ---- 2. auto-include set + acronyms ---------------------------------
    src = sub_once(
        src,
        'AUTO_INCLUDE_TRIAL_IDS=new Set(["NCT02366871","NCT02829957"])',
        'AUTO_INCLUDE_TRIAL_IDS=new Set(["NCT00643201","NCT00633893","NCT03266783",'
        '"NCT02366871","NCT02829957"])',
        "L2 auto-include set extended to the five adjudicated trials",
    )
    src = sub_once(
        src,
        'nctAcronyms:{NCT02366871:"NCT02366871",NCT02829957:"(RAMBLE)"}',
        'nctAcronyms:{NCT00643201:"AMPLIFY",NCT00633893:"AMPLIFY-EXT",NCT03266783:"COBRRA",'
        'NCT02366871:"Guntupalli 2020 (gyn-onc prophylaxis)",NCT02829957:"RAMBLE"}',
        "L3 trial acronyms corrected",
    )

    # ---- 3. retire the pre-2015 rule ------------------------------------
    src = sub_once(
        src,
        'query:"",rctOnly:!0,post2015:!0',
        'query:"",rctOnly:!0,post2015:!1',
        "P1 pre-2015 exclusion RETIRED (it was the rule that excluded AMPLIFY and AMPLIFY-EXT)",
    )

    # ---- 4. phase-II auto-exclusion must not silently drop reviewed trials
    src = sub_once(
        src,
        'return Object.entries(this.realData??{}).filter(([,data])=>!isPhaseTwoLike(data?.phase??"")).map(([id])=>id)',
        'return Object.entries(this.realData??{}).filter(([,data])=>!0===data?.rmPhaseEligible||!isPhaseTwoLike(data?.phase??"")).map(([id])=>id)',
        "P2 phase-II auto-exclusion no longer silently drops reviewed-eligible trials "
        "(NCT02366871 is registered PHASE2 and was previously mislabelled III to survive this filter)",
    )

    # ---- 5. install the compatibility gate ------------------------------
    src = sub_once(
        src,
        "hasAnalysisReadyTrials(trials=this.state.trials){",
        COMPAT_GATE_JS.strip() + "\nhasAnalysisReadyTrials(trials=this.state.trials){",
        "G1 estimand-compatibility gate installed on RapidMeta",
    )

    # ---- 6. make the analysis path fail closed --------------------------
    src = sub_once(
        src,
        "const c=this.computeCore(trials);",
        'const _rmBlock=RapidMeta.rmPoolBlockReason?RapidMeta.rmPoolBlockReason(trials):"";'
        'if(_rmBlock){RapidMeta.state.results=null,RapidMeta.save(),this.updateStatCards(null),'
        'this.renderDemographics(trials),this.renderEmptyAnalysis(_rmBlock);'
        'try{window.__rmShowPoolBlock&&window.__rmShowPoolBlock(_rmBlock)}catch(e){}return}'
        'try{window.__rmHidePoolBlock&&window.__rmHidePoolBlock()}catch(e){}'
        "const c=this.computeCore(trials);",
        "G2 analysis fails closed on an incompatible set: no pooled effect, heterogeneity, "
        "Bayesian posterior, TSA, NNT, funnel, L'Abbe, fragility index or GRADE is computed",
    )

    # ---- 7. PICO: replace the foreign-template defaults ------------------
    src = sub_once(
        src,
        'pop:"Adults randomised in trials registered on ClinicalTrials.gov for Thromboembolism",'
        'int:"Apixaban (AACT-verified intervention name)",'
        'comp:"Active comparator or placebo as registered on AACT",'
        'out:"Trial-declared primary outcome (AACT design_outcomes); event counts from AACT outcome_measurements",'
        'subgroup:"Subgroup analyses per parent trial protocol"',
        'pop:"SEPARATE QUESTIONS - select one at a time. A: acute VTE treatment. B: extended '
        'treatment after 6-12 months. C: acute VTE treatment, DOAC head-to-head. D: postoperative '
        'thromboprophylaxis after gynaecologic-cancer surgery. E: menstrual blood loss during '
        'anticoagulation.",'
        'int:"Apixaban",'
        'comp:"Question-specific: enoxaparin/warfarin (A), placebo (B), rivaroxaban (C and E), '
        'enoxaparin (D). NOT a common comparator - these are not pooled.",'
        'out:"Question-specific: recurrent VTE or VTE-related death (A, B); clinically relevant '
        'bleeding (C); ISTH major and CRNM bleeding (D); PBAC score, a continuous outcome (E).",'
        'subgroup:"None pre-specified. No subgroup analysis is reported."',
        "T1 PICO rewritten to the five declared questions (was templated AACT boilerplate)",
    )
    src = sub_once(
        src,
        'value="Adults randomised in trials registered on ClinicalTrials.gov for Thromboembolism" aria-label="Population (PICO)"',
        'value="SEPARATE QUESTIONS - select one at a time; see the protocol notes below" aria-label="Population (PICO)"',
        "T2 PICO population input default",
    )
    src = sub_once(
        src,
        'value="Placebo" aria-label="Comparator (PICO)"',
        'value="Question-specific (enoxaparin/warfarin, placebo, rivaroxaban, enoxaparin) - not a common comparator" aria-label="Comparator (PICO)"',
        "T3 PICO comparator default was 'Placebo'; no trial in this review has a placebo arm "
        "except AMPLIFY-EXT",
    )
    src = sub_once(
        src,
        'value="Blood eosinophils, smoking status, ICS use" aria-label="Subgroup analyses"',
        'value="None pre-specified" aria-label="Subgroup analyses"',
        "T4 PICO subgroup plan default was an asthma/COPD template residue",
    )
    src = sub_once(
        src,
        'value="Number of Participants With Incidence of Major Bleeding" aria-label="Outcome (PICO)"',
        'value="Question-specific - see the outcome selector above the forest plot" aria-label="Outcome (PICO)"',
        "T5 PICO primary-outcome default",
    )

    # ---- 8. drop the ICMJE / PROSPERO equivalence claim ------------------
    src = sub_once(
        src,
        " Per ICMJE 2023, GitHub commit hash + timestamp constitutes a verifiable "
        "pre-registration record equivalent to PROSPERO for tracking outcome / "
        "eligibility / analysis-plan changes.",
        " The commit hash and timestamp are a genuine immutable record of when the protocol "
        "text changed. They are NOT a prospective registration: this review is not registered "
        "with PROSPERO or any other registry, and no claim of equivalence to such a registration "
        "is made.",
        "T6 'equivalent to PROSPERO per ICMJE' claim removed; the GitHub timestamp is kept and "
        "described accurately",
    )

    # ---- 9. header badge: stop asserting a passed audit ------------------
    src = sub_once(
        src,
        '<strong style="font-size:14px;letter-spacing:0.04em;">INTERNAL CHECKS PASSED</strong>'
        '<span style="font-size:11.5px;">Fabrication-risk score: <strong>0.275</strong> '
        '· Trials: <strong>2</strong></span>',
        '<strong style="font-size:14px;letter-spacing:0.04em;">RECONSTRUCTED — NOT AUDIT-CLEARED</strong>'
        '<span style="font-size:11.5px;">Trials: <strong>5</strong> across <strong>5 separate '
        'questions</strong> · no pooled estimate is produced</span>',
        "H1 header badge no longer claims INTERNAL CHECKS PASSED",
    )
    src = sub_once(
        src,
        'Multi-source audit completed (AACT 2026-04-12 + PubMed + 10 internal-consistency rounds). '
        'Routine pre-publication human spot-check recommended.',
        'Extraction re-verified 2026-07-30 against ClinicalTrials.gov API v2 posted results and '
        'PubMed abstracts (2 sources per trial). NOT done: no full texts read, no independent dual '
        'human screening or dual extraction, no GRADE or RoB 2 re-derivation for the new question '
        'set. The previous pooled estimate over this corpus was invalid and has been removed.',
        "H2 header sub-line replaced with the honest verification state",
    )
    src = sub_once(
        src,
        "Audited via AACT 2026-04-12 + PubMed + 14 internal-consistency rounds. See ",
        "Sources: ClinicalTrials.gov API v2 posted results + PubMed abstracts, fetched 2026-07-30. "
        "The AACT 2026-04-12 snapshot was NOT reachable and has not been used. See ",
        "H3 AACT audit claim corrected",
        required=False,
    )

    # ---- 10. patient-facing / plain-language contamination ---------------
    src = sub_once(
        src,
        'outcomeText={default:"major cardiovascular events",MACE:"major cardiovascular events",'
        'HF_CV_First:"heart failure worsening or cardiovascular death",Renal40:"major kidney events",'
        'KidneyComp:"kidney events",ACM:"death from any cause",ACH:"hospitalization for heart failure",'
        'Hyperkalemia:"hyperkalemia events"}',
        'outcomeText={default:"the selected outcome",'
        'RecurrentVTEorVTEDeath:"recurrent blood clots or death from a blood clot",'
        'RecurrentVTEorVTEDeath_2p5mg:"recurrent blood clots or death from a blood clot",'
        'RecurrentVTEorVTEDeath_5mg:"recurrent blood clots or death from a blood clot",'
        'ClinicallyRelevantBleeding:"bleeding that needed medical attention",'
        'MajorBleeding:"serious bleeding",CRNMBleeding:"bleeding that needed medical attention",'
        'VTE:"blood clots",RecurrentVTE:"recurrent blood clots",'
        'MajorHaemorrhage:"serious bleeding",'
        'CrossedOverAnticoagulant:"switching to a different blood thinner",'
        'DiscontinuedDrug:"stopping the study drug early"}',
        "C1 plain-language outcome text: cardiorenal template ('major cardiovascular events', "
        "'major kidney events') replaced with the VTE/bleeding outcomes actually in this review",
    )

    # the string-concat idiom left inside a template literal, which renders literally
    for i, frag in enumerate([
        "' + (RapidMeta.state.protocol?.int || 'the intervention') + '",
        "' + (RapidMeta.state.protocol?.int ?? 'The intervention') + '",
    ]):
        n = src.count(frag)
        if n:
            src = src.replace(frag, "apixaban")
            applied.append(f"C2.{i+1} literal template-concat leak removed from the patient "
                           f"summary ({n} occurrence(s)) - it rendered as raw source text")
        else:
            skipped.append(f"C2.{i+1} template-concat leak (not present)")

    # the topic slug leaked into user-visible prose as if it were the drug name
    slug_visible = [
        ('"% lower risk with apixaban_vte_auto"', '"% lower risk with apixaban"'),
        ('"% higher risk with apixaban_vte_auto"', '"% higher risk with apixaban"'),
        ('"% lower odds with apixaban_vte_auto."', '"% lower odds with apixaban."'),
        ('"% higher odds with apixaban_vte_auto."', '"% higher odds with apixaban."'),
        ('Math.round(absRRR)+"% lower risk with apixaban_vte_auto"',
         'Math.round(absRRR)+"% lower risk with apixaban"'),
        ('Math.round(absRRR)+"% higher risk with apixaban_vte_auto"',
         'Math.round(absRRR)+"% higher risk with apixaban"'),
        ('"in favor of apixaban_vte_auto"', '"in favor of apixaban"'),
        ("published apixaban_vte_auto corridor", "published apixaban corridor"),
        ("CT.gov-tracked apixaban_vte_auto record", "CT.gov-tracked apixaban record"),
        ("the apixaban_vte_auto watchlist", "the apixaban watchlist"),
        ("the curated apixaban_vte_auto set", "the curated apixaban set"),
        ("whether apixaban_vte_auto’s benefit varies", "whether apixaban’s benefit varies"),
        ("in the apixaban_vte_auto arm", "in the apixaban arm"),
    ]
    slug_fixed = 0
    for old, new in slug_visible:
        c = src.count(old)
        if c:
            src = src.replace(old, new)
            slug_fixed += c
    if slug_fixed:
        applied.append(f"C3 internal topic slug 'apixaban_vte_auto' removed from {slug_fixed} "
                       f"user-visible string(s) (build pipeline had substituted the slug where the "
                       f"drug name belonged)")
    else:
        skipped.append("C3 slug exposure (already applied)")

    # the arm-detection regex still looks for finerenone's development code
    arm_regex_old = r"/apixaban_vte_auto|bay\s*94|treatment|active/i"
    arm_regex_new = r"/\bapixaban\b|treatment|active|intervention/i"
    c = src.count(arm_regex_old)
    if c:
        src = src.replace(arm_regex_old, arm_regex_new)
        applied.append(f"C4 CT.gov arm-detection regex: 'bay 94' (finerenone's development code) "
                       f"and the topic slug replaced with the actual drug name, {c} occurrence(s)")
    else:
        skipped.append("C4 arm-detection regex (already applied)")

    for old, new, tag in [
        ('(?:apixaban_vte_auto|bay\\s*94|treatment|active)',
         '(?:apixaban|treatment|active|intervention)',
         "C5 abstract-mining arm regexes"),
        ('(?:finerenone|treatment|experimental|intervention|drug)',
         '(?:apixaban|treatment|experimental|intervention|drug)',
         "C6 abstract-mining drug regexes (finerenone)"),
        ('(?:finerenone|treatment|experimental|intervention)',
         '(?:apixaban|treatment|experimental|intervention)',
         "C7 abstract-mining drug regexes (finerenone, 2nd form)"),
        ('(?:apixaban_vte_auto|treatment|active)',
         '(?:apixaban|treatment|active)',
         "C8 abstract-mining N-pattern regex"),
        ('["apixaban_vte_auto","bay 94","treatment","active"]',
         '["apixaban","treatment","active","intervention"]',
         "C9 arm-position keyword list"),
        ('/apixaban_vte_auto|bay\\s*94/i', '/\\bapixaban\\b/i',
         "C10 context-match regex"),
        ('/\\bapixaban_vte_auto\\b|\\bbay\\s*94/i', '/\\bapixaban\\b/i',
         "C11 title-scoring regex"),
    ]:
        c = src.count(old)
        if c:
            src = src.replace(old, new)
            applied.append(f"{tag}: {c} occurrence(s)")
        else:
            skipped.append(f"{tag} (already applied or absent)")

    # verdict / manuscript prose defaults
    src = sub_once(
        src,
        'verdictOutcome={default:"the matched cardiovascular composite endpoint",',
        'verdictOutcome={default:"the selected outcome",',
        "C12 verdict prose default was 'the matched cardiovascular composite endpoint'",
    )
    src = sub_once(
        src,
        'ocProse={default:"the matched cardiovascular composite endpoint across CKD trials",',
        'ocProse={default:"the selected outcome",',
        "C13 manuscript prose default was 'the matched cardiovascular composite endpoint across "
        "CKD trials'",
    )
    src = sub_once(
        src,
        '(RapidMeta.state?.protocol?.out ?? "MACE Composite")',
        '(RapidMeta.state?.protocol?.out ?? "")',
        "C14 protocol-outcome fallback was 'MACE Composite'",
        required=False,
    )
    src = sub_once(
        src,
        '?.endpointLabel ?? "MACE")',
        '?.endpointLabel ?? "")',
        "C15 reviewer-endpoint fallback was 'MACE'",
        required=False,
    )

    # Arabic localisation table still carries the source template's drug and endpoint
    for old, new, tag in [
        ('apixaban_vte_auto:"الفينيرينون"',
         'apixaban:"أبيكسابان"',
         "C16 Arabic table mapped the topic slug to the Arabic for finerenone"),
        ('"Primary Result":"نتيجة MACE الأولية"',
         '"Primary Result":"النتيجة الأولية"',
         "C17 Arabic 'Primary Result' rendered as 'Primary MACE result'"),
    ]:
        c = src.count(old)
        if c:
            src = src.replace(old, new)
            applied.append(f"{tag}: {c} occurrence(s)")
        else:
            skipped.append(f"{tag} (already applied or absent)")

    # remaining slug occurrences in Arabic prose
    c = src.count("apixaban_vte_auto")
    ui_slug = re.findall(r'"[^"]*apixaban_vte_auto[^"]*"', src)
    ui_slug = [s for s in ui_slug if "rapid_meta_" not in s and "_v1_0" not in s]

    # ---- 11. the unconditional analysis banner must state the real reason
    src = sub_once(
        src,
        "<strong>⚠ Not a pooled meta-analysis.</strong> Automated endpoint-matching found no "
        "outcome with ≥2 included trials reporting the same endpoint, so each outcome below is "
        "a single-trial summary rather than a pooled estimate. If trials do share an endpoint, "
        "verify and pool manually.",
        "<strong>⛔ No pooled estimate is produced by this review.</strong> The five included "
        "trials answer five different questions — acute VTE treatment against conventional "
        "therapy (AMPLIFY), extended treatment against placebo (AMPLIFY-EXT), acute treatment "
        "against another DOAC (COBRRA), postoperative thromboprophylaxis after gynaecologic-cancer "
        "surgery against enoxaparin (Guntupalli 2020), and menstrual blood loss against rivaroxaban "
        "on a continuous score (RAMBLE). Population, comparator and endpoint differ, so no single "
        "pooled effect is defined over them. Each outcome below is a SINGLE-TRIAL estimate. The gate "
        "is fail-closed: it refuses to pool rather than inviting you to pool manually.",
        "T7 analysis banner now states the real reason and stops suggesting manual pooling",
    )

    # ---- 12. PRISMA: stop emitting unbalanced integers -------------------
    src = sub_once(
        src,
        'document.getElementById("p-inc").innerText=r.k',
        'document.getElementById("p-inc").innerText=r.k;'
        '(function(){try{var ids=["p-reg","p-reg-exc","p-reg-scr","p-reg-excl2","p-pm","p-oa",'
        '"p-ref","p-scr","p-exc"];var recorded=RapidMeta.state.searchLog&&RapidMeta.state.searchLog.length>0;'
        'if(!recorded){ids.forEach(function(id){var el=document.getElementById(id);'
        'if(el)el.innerText="not recorded"});}}catch(e){}})()',
        "T8 PRISMA boxes show 'not recorded' when no search session backs them, instead of "
        "emitting integers that do not balance",
    )

    open(FULL, "w", encoding="utf-8", newline="").write(src)

    print(f"\nwrote {FULL}: {before:,} -> {len(src):,} bytes\n")
    print(f"APPLIED ({len(applied)}):")
    for a in applied:
        print("  +", a)
    if skipped:
        print(f"\nSKIPPED ({len(skipped)}):")
        for s in skipped:
            print("  .", s)
    if failed:
        print(f"\nFAILED ({len(failed)}):")
        for f in failed:
            print("  !", f)
    if ui_slug:
        print(f"\nREMAINING user-visible slug strings ({len(ui_slug)}):")
        for s in ui_slug[:20]:
            print("  ?", s[:150])
    print(f"\ntotal 'apixaban_vte_auto' occurrences left (storage keys + filenames are legitimate): {c}")

    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
