"""Build the blinded RoB-2 evidence packet, one per trial, per protocol section 9.

The packet carries EVIDENCE ONLY. The recorded bias-relevant features are included
because section 9 names them as inputs, but each is labelled as an input and the
packet says explicitly that no existing prose may stand in for a domain judgement.
No prior rating, no GRADE text and no wording from the object's own risk-of-bias
reasoning is included, so an assessor cannot copy a judgement it was meant to make.
"""
import io, json, sys, os
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

OBJ = r"F:\rapidmeta-ssot-shell\ssot\arni-hfref\arni-hfref.json"
d = json.load(open(OBJ, encoding="utf-8"))
OID = "cvdeath_or_hfh_first"
res = d["results"]["by_outcome"][OID]
per = {r["trial_id"]: r for r in res["per_trial"]}

INSTR = """You are performing a Cochrane RoB-2 assessment. Follow it exactly.

TOOL: RoB-2 for randomized trials.
VARIANT: effect of ASSIGNMENT to intervention (intention-to-treat). Not the
adherence variant.
UNIT: assess THE RESULT BEING POOLED, not the trial overall. The result is the
composite of cardiovascular death or first hospitalisation for heart failure,
expressed as a time-to-first-event hazard ratio.

Assess all five domains:
 D1 bias arising from the randomization process
 D2 bias due to deviations from intended interventions (effect of assignment)
 D3 bias due to missing outcome data
 D4 bias in measurement of the outcome
 D5 bias in selection of the reported result

For EACH domain give:
  - an answer to each relevant signalling question: Y / PY / PN / N / NI
    (NI = no information)
  - a domain judgement: LOW / SOME CONCERNS / HIGH
  - a one-paragraph rationale naming the evidence it rests on
  - the sources you relied on, and say plainly if you did NOT have the trial
    protocol or statistical analysis plan for that domain

Then an OVERALL judgement by the standard algorithm: LOW only if every domain is
LOW; HIGH if any domain is HIGH, or if multiple domains raise SOME CONCERNS in a
way that substantially lowers confidence; SOME CONCERNS otherwise.

RULES:
- The "recorded features" below are INPUTS. They are not judgements. Do not treat
  any sentence in them as a domain rating, and do not reuse their wording as your
  rationale.
- If information is absent, answer NI and say so. Do not infer from plausibility.
- Do not soften a judgement because the trial is large or well known.

Return STRICT JSON only, no prose outside it:
{"trial":"...","domains":{"D1":{"signalling":{"1.1":"Y",...},"judgement":"LOW",
"rationale":"...","sources":["..."],"protocol_available":true|false}, ...},
"overall":{"judgement":"...","rationale":"..."}}
"""

FEATURES = {
    "paradigm-hf": [
        "Design, as recorded: phase 3, double-blind, randomised 1:1 against an "
        "active comparator.",
        "Recorded: stopped early by prespecified rule for overwhelming benefit.",
        "Analysis population: full analysis set 4187 / 4212 against a randomised "
        "total of 4209 / 4233; 37 participants at sites closed for serious GCP "
        "violations and 6 inadvertently randomised who never received drug.",
        "The pooled result is this trial's OWN PRIMARY endpoint.",
    ],
    "parachute-hf": [
        "Design, as recorded: OPEN-LABEL, multicentre randomised, with BLINDED "
        "endpoint adjudication.",
        "The pooled result is this trial's FIRST SECONDARY endpoint. Its "
        "registered primary is a win ratio over a hierarchical composite that "
        "includes a 12-week NT-proBNP change.",
        "Analysis population: full analysis set 462 / 460, equal to the "
        "randomised totals.",
        "Population is heart failure due to chronic Chagas cardiomyopathy.",
    ],
    "parallel-hf": [
        "Design, as recorded: phase 3, double-blind, double-dummy.",
        "The pooled result is this trial's OWN PRIMARY composite endpoint.",
        "Analysis population: full analysis set 111 / 112 against a randomised "
        "total of 112 / 113; one mis-randomised participant per arm.",
        "Population is Japanese adults with HFrEF.",
    ],
}

out = {}
for t in d["inputs"]["trials"]:
    tid = t["id"]
    p = per.get(tid, {})
    bo = t["by_outcome"][OID]
    tx, ct = bo.get("treatment") or {}, bo.get("control") or {}
    pkt = {
        "trial": t.get("name") or tid,
        "registry_id": t.get("nct"),
        "primary_publication_pmid": t.get("pmid"),
        "year": t.get("year"),
        "design_as_recorded": t.get("design"),
        "population_as_recorded": t.get("population"),
        "comparator_basis": t.get("comparator_type_basis"),
        "result_being_assessed": {
            "outcome": "composite of cardiovascular death or first hospitalisation "
                       "for heart failure, time to first event",
            "measure": p.get("measure"),
            "point": p.get("point"), "ci_low": p.get("ci_low"),
            "ci_high": p.get("ci_high"), "ci_level": p.get("ci_level"),
            "endpoint_rank_in_its_own_trial": p.get("endpoint_rank_in_its_own_trial"),
        },
        "arm_data": {
            "intervention_events": tx.get("events"), "intervention_analysed": tx.get("n"),
            "intervention_randomised": tx.get("randomised"),
            "comparator_events": ct.get("events"), "comparator_analysed": ct.get("n"),
            "comparator_randomised": ct.get("randomised"),
            "denominator_note": bo.get("denominator_note"),
        },
        "recorded_features_ARE_INPUTS_NOT_JUDGEMENTS": FEATURES.get(tid, []),
        "sources_available_to_you": [
            "registry record at https://clinicaltrials.gov/study/%s" % t.get("nct"),
            "primary publication PMID %s" % t.get("pmid"),
        ],
        "protocol_or_sap_supplied": False,
    }
    out[tid] = pkt

D = os.path.dirname(os.path.abspath(__file__))
json.dump({"instructions": INSTR, "packets": out},
          open(os.path.join(D, "rob2_packets.json"), "w", encoding="utf-8"),
          indent=1, ensure_ascii=False)
for tid, p in out.items():
    txt = INSTR + "\n\nTRIAL PACKET (JSON):\n" + json.dumps(p, indent=1, ensure_ascii=False)
    open(os.path.join(D, "rob2_prompt_%s.txt" % tid), "w", encoding="utf-8").write(txt)
    print("packet %-14s %5d chars  protocol_supplied=%s"
          % (tid, len(txt), p["protocol_or_sap_supplied"]))
