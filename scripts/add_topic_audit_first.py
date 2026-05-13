"""Audit-first topic-add pipeline.

For each candidate topic (a curated list of NCTs), run the same audit
gates we developed across R1-R23, and only output trial data that passes
every gate.

Input: topic_spec = {
    "stem": "TEZEPELUMAB_ASTHMA_REVIEW",
    "name": "Tezepelumab in severe asthma",
    "ncts": ["NCT03347279", "NCT04302168", ...],
    "drug_pattern": "tezepelumab",   # required substring in AACT interventions
    "condition_patterns": ["asthma"], # required substring overlap in AACT conditions
}

Pipeline:
  Stage 1 — AACT: load studies, conditions, interventions, baseline_counts,
            outcome_measurements for each candidate NCT.
  Stage 2 — PubMed: via idconv API map PMID → fetch abstract.
  Stage 3 — Per-NCT audit gates:
              GATE-A: NCT exists in AACT
              GATE-B: drug pattern in AACT interventions
              GATE-C: condition pattern in AACT conditions
              GATE-D: PMID resolves to a paper whose title+abstract contains
                      either the drug or the condition (R7-S4 / topic-overlap)
              GATE-E: per-arm enrollment from baseline_counts matches what
                      we extract (sanity check, will populate from AACT)
              GATE-F: primary outcome measure from design_outcomes used to
                      pick the correct outcome_measurements row
  Stage 4 — Extract: from outcome_measurements use the COUNT_OF_PARTICIPANTS
            rows for the primary outcome to populate tE, tN, cE, cN.
            From the AACT primary outcome's "param_value" if numeric, get
            point estimate; from "ci_lower_limit"/"ci_upper_limit" get CI.
  Stage 5 — Output: write outputs/new_topics/<stem>.json with:
              {trials: [{nct, name, year, pmid, tE, tN, cE, cN, hr, lci,
                          uci, evidence: [{...}], audit_gates: {A:..., B:...}}],
                topic_meta: {...},
                gate_pass_rate: X/Y}

If gate_pass_rate < 80% → audit fails, mark topic NOT viable for
auto-build.
"""
from __future__ import annotations
import json, csv, re, sys, io, time, urllib.request, urllib.parse
from pathlib import Path
from collections import defaultdict

if hasattr(sys.stdout, "buffer") and getattr(sys.stdout, "encoding", "").lower() != "utf-8":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

HERE = Path(__file__).resolve().parent.parent
OUT = HERE / "outputs" / "new_topics"
OUT.mkdir(parents=True, exist_ok=True)
PMC_CACHE = HERE / "outputs" / "extraction_audit" / "pubmed_cache"
AACT = Path("D:/AACT-storage/AACT/2026-04-12")

# Candidate topics — pilot (Path X + Y + Z, 2026-05-13)
TOPICS = [
    # Path X — recent landmark trials not yet covered
    {"stem": "TEZEPELUMAB_ASTHMA_REVIEW", "name": "Tezepelumab in severe asthma",
     "ncts": ["NCT03347279", "NCT04039113", "NCT03406078", "NCT03968978"],
     "drug_patterns": ["tezepelumab"], "condition_patterns": ["asthma"]},
    {"stem": "AVACOPAN_ANCA_REVIEW", "name": "Avacopan in ANCA-associated vasculitis",
     "ncts": ["NCT02994927", "NCT02222155"],
     "drug_patterns": ["avacopan"], "condition_patterns": ["anca", "vasculitis", "granulomatosis"]},
    {"stem": "ZURANOLONE_PPD_MDD_REVIEW", "name": "Zuranolone in MDD and PPD",
     "ncts": ["NCT04442737", "NCT04476030"],
     "drug_patterns": ["zuranolone", "sage-217"], "condition_patterns": ["depress"]},
    {"stem": "TOFERSEN_SOD1_ALS_REVIEW", "name": "Tofersen in SOD1+ ALS",
     "ncts": ["NCT02623699", "NCT04856982"],
     "drug_patterns": ["tofersen"], "condition_patterns": ["amyotrophic", "lateral", "sclerosis"]},
    {"stem": "VAMOROLONE_DMD_REVIEW", "name": "Vamorolone in Duchenne",
     "ncts": ["NCT03439670", "NCT03038399"],
     "drug_patterns": ["vamorolone"], "condition_patterns": ["duchenne", "muscular"]},

    # Path Y — modern oncology bispecifics + ADCs
    {"stem": "TALQUETAMAB_MM_REVIEW", "name": "Talquetamab (GPRC5D bispecific) in R/R MM",
     "ncts": ["NCT03399799", "NCT04634552", "NCT05012774"],
     "drug_patterns": ["talquetamab"], "condition_patterns": ["multiple myeloma"]},
    {"stem": "ELRANATAMAB_MM_REVIEW", "name": "Elranatamab (BCMA bispecific) in R/R MM",
     "ncts": ["NCT03269136", "NCT04649359", "NCT05020236"],
     "drug_patterns": ["elranatamab", "pf-06863135"], "condition_patterns": ["multiple myeloma"]},
    {"stem": "EPCORITAMAB_LYMPHOMA_REVIEW", "name": "Epcoritamab (CD20xCD3) in R/R DLBCL/FL",
     "ncts": ["NCT03625037", "NCT04628494"],
     "drug_patterns": ["epcoritamab"], "condition_patterns": ["lymphoma"]},
    {"stem": "GLOFITAMAB_LYMPHOMA_REVIEW", "name": "Glofitamab (CD20xCD3) in R/R DLBCL",
     "ncts": ["NCT03075696", "NCT04408638"],
     "drug_patterns": ["glofitamab", "ro7082859"], "condition_patterns": ["lymphoma"]},
    {"stem": "MIRVETUXIMAB_OVARIAN_REVIEW", "name": "Mirvetuximab soravtansine FRα+ ovarian",
     "ncts": ["NCT04209855", "NCT04296890"],
     "drug_patterns": ["mirvetuximab"], "condition_patterns": ["ovarian"]},
    {"stem": "OLUTASIDENIB_AML_REVIEW", "name": "Olutasidenib in R/R IDH1+ AML",
     "ncts": ["NCT02719574"],
     "drug_patterns": ["olutasidenib"], "condition_patterns": ["myeloid leukemia"]},
    {"stem": "SELPERCATINIB_RET_REVIEW", "name": "Selpercatinib in RET+ NSCLC/MTC (LIBRETTO)",
     "ncts": ["NCT03157128", "NCT04194944"],
     "drug_patterns": ["selpercatinib"], "condition_patterns": ["lung", "thyroid"]},

    # Path Z — underserved areas (pediatric, rare, tropical)
    {"stem": "MARALIXIBAT_PFIC_REVIEW", "name": "Maralixibat in PFIC (MARCH-PFIC + cohort)",
     "ncts": ["NCT03905330", "NCT02057692"],
     "drug_patterns": ["maralixibat"], "condition_patterns": ["cholestasis", "pfic"]},
    {"stem": "ODEVIXIBAT_PFIC_REVIEW", "name": "Odevixibat in PFIC (PEDFIC-1/2)",
     "ncts": ["NCT03566238", "NCT03659916"],
     "drug_patterns": ["odevixibat"], "condition_patterns": ["cholestasis", "pfic"]},
    {"stem": "SUTIMLIMAB_CAD_REVIEW", "name": "Sutimlimab in cold agglutinin disease",
     "ncts": ["NCT03347396", "NCT03347422"],
     "drug_patterns": ["sutimlimab"], "condition_patterns": ["agglutinin"]},
    {"stem": "NEMOLIZUMAB_PRURIGO_REVIEW", "name": "Nemolizumab in prurigo nodularis (OLYMPIA)",
     "ncts": ["NCT04501666", "NCT04204616"],
     "drug_patterns": ["nemolizumab"], "condition_patterns": ["prurigo"]},
]

# ─── AACT bulk load (shared across all topics) ───
all_ncts = sorted({nct for t in TOPICS for nct in t["ncts"]})
nct_set = set(all_ncts)
print(f"Total candidate NCTs: {len(all_ncts)}")

def load_aact(filename, key_col, want_cols, filter_set):
    out = defaultdict(list)
    with open(AACT / filename, "r", encoding="utf-8", errors="replace") as f:
        reader = csv.DictReader(f, delimiter="|")
        for row in reader:
            k = (row.get(key_col) or "").strip().upper()
            if k in filter_set:
                out[k].append({c: (row.get(c) or "").strip() for c in want_cols})
    return out

print("Loading AACT…")
studies = load_aact("studies.txt", "nct_id",
                     ["brief_title", "official_title", "enrollment", "acronym",
                      "start_date", "primary_completion_date"], nct_set)
conds = load_aact("conditions.txt", "nct_id", ["downcase_name"], nct_set)
intvs = load_aact("interventions.txt", "nct_id", ["name", "intervention_type"], nct_set)
baseline = load_aact("baseline_counts.txt", "nct_id",
                      ["ctgov_group_code", "count", "scope", "units"], nct_set)
outcomes = load_aact("outcome_measurements.txt", "nct_id",
                      ["ctgov_group_code", "title", "param_type", "param_value_num",
                       "param_value", "dispersion_value"], nct_set)
design_outs = load_aact("design_outcomes.txt", "nct_id",
                        ["outcome_type", "measure"], nct_set)
print(f"  studies: {len(studies)}  conds: {len(conds)}  intvs: {len(intvs)}")

# ─── PubMed via idconv ───
def map_pmids_via_idconv(pmids):
    """Convert PMID → PMC. Returns {pmid_str: pmcid_or_None}."""
    out = {}
    if not pmids: return out
    BATCH = 200
    for i in range(0, len(pmids), BATCH):
        batch = pmids[i:i+BATCH]
        params = {"ids": ",".join(batch), "format": "json",
                  "tool": "rapidmeta-pilot", "email": "test@test.com"}
        url = "https://www.ncbi.nlm.nih.gov/pmc/utils/idconv/v1.0/?" + urllib.parse.urlencode(params)
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "rapidmeta/1.0"})
            with urllib.request.urlopen(req, timeout=60) as r:
                payload = json.loads(r.read())
            for rec in payload.get("records", []):
                pmid = rec.get("pmid")
                pmc = rec.get("pmcid")
                if pmid:
                    out[str(pmid)] = pmc.replace("PMC", "") if pmc else None
        except Exception as e:
            print(f"  idconv batch error: {e}")
        time.sleep(0.4)
    return out

def fetch_pubmed_metadata(pmids):
    """Fetch PubMed via efetch. Returns {pmid: {title, abstract, journal, doi, year}}."""
    out = {}
    if not pmids: return out
    BATCH = 50
    import xml.etree.ElementTree as ET
    for i in range(0, len(pmids), BATCH):
        batch = pmids[i:i+BATCH]
        params = {"db": "pubmed", "id": ",".join(batch), "rettype": "abstract", "retmode": "xml"}
        url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi?" + urllib.parse.urlencode(params)
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "rapidmeta/1.0"})
            with urllib.request.urlopen(req, timeout=60) as r:
                xml_data = r.read()
            root = ET.fromstring(xml_data)
            for art in root.findall(".//PubmedArticle"):
                pmid_el = art.find(".//PMID")
                if pmid_el is None: continue
                pmid = pmid_el.text.strip()
                title_el = art.find(".//ArticleTitle")
                title = "".join(title_el.itertext()).strip() if title_el is not None else ""
                abs_pieces = []
                for at in art.findall(".//Abstract/AbstractText"):
                    txt = "".join(at.itertext()).strip()
                    if txt: abs_pieces.append(txt)
                abstract = " ".join(abs_pieces)
                year_el = art.find(".//PubDate/Year")
                year = year_el.text if year_el is not None else None
                doi = ""
                for aid in art.findall(".//ArticleId"):
                    if aid.get("IdType") == "doi":
                        doi = (aid.text or "").strip()
                        break
                out[pmid] = {"title": title, "abstract": abstract,
                              "year": int(year) if year and year.isdigit() else None,
                              "doi": doi}
        except Exception as e:
            print(f"  efetch error: {e}")
        time.sleep(0.4)
    return out


# Extract PMIDs from AACT references (study_references.txt has PMIDs per NCT)
# But simpler: use AACT id_information for PMIDs OR find primary-result PMIDs
# via study_references.txt if present
def get_pmids_for_ncts(ncts):
    """Return {nct: [primary_pmid_or_None]} via AACT study_references."""
    out = {nct: [] for nct in ncts}
    ref_file = AACT / "study_references.txt"
    if not ref_file.exists(): return out
    with open(ref_file, "r", encoding="utf-8", errors="replace") as f:
        reader = csv.DictReader(f, delimiter="|")
        for row in reader:
            nct = (row.get("nct_id") or "").strip().upper()
            if nct not in out: continue
            pmid = (row.get("pmid") or "").strip()
            rtype = (row.get("reference_type") or "").lower()
            if pmid and pmid.isdigit():
                if "result" in rtype or "primary" in rtype:
                    out[nct].insert(0, pmid)  # priority
                else:
                    out[nct].append(pmid)
    return out


print("Mapping NCT → primary PMID from study_references…")
nct_pmids = get_pmids_for_ncts(all_ncts)
all_pmids = list({p for v in nct_pmids.values() for p in v[:1]})
print(f"  primary PMIDs to fetch: {len(all_pmids)}")

if all_pmids:
    pubmed_meta = fetch_pubmed_metadata(all_pmids)
    print(f"  fetched abstracts: {len(pubmed_meta)}")
else:
    pubmed_meta = {}


# ─── Audit gates per NCT per topic ───
def audit_nct_in_topic(nct, topic):
    """Return {gate: bool, evidence: str, extracted_data: dict}."""
    gates = {}; extracted = {"nct": nct}
    # GATE-A: in AACT
    s = studies.get(nct, [])
    gates["A_aact_exists"] = bool(s)
    if not s:
        return {"gates": gates, "extracted": extracted}
    aact = s[0]
    extracted["aact_title"] = aact.get("brief_title", "")
    extracted["aact_acronym"] = aact.get("acronym", "")
    extracted["start_date"] = aact.get("start_date", "")
    extracted["primary_completion_date"] = aact.get("primary_completion_date", "")

    # GATE-B: drug pattern in AACT interventions
    intv_text = " ".join(i["name"] for i in intvs.get(nct, [])).lower()
    drug_match = any(p.lower() in intv_text for p in topic["drug_patterns"])
    gates["B_drug_in_intvs"] = drug_match
    extracted["aact_intvs"] = [i["name"] for i in intvs.get(nct, [])]

    # GATE-C: condition pattern in AACT conditions
    cond_text = " ".join(c["downcase_name"] for c in conds.get(nct, [])).lower()
    cond_match = any(p.lower() in cond_text for p in topic["condition_patterns"])
    gates["C_condition_in_aact"] = cond_match
    extracted["aact_conditions"] = sorted({c["downcase_name"] for c in conds.get(nct, [])})

    # GATE-D: PMID topic-overlap
    pmids = nct_pmids.get(nct, [])
    primary_pmid = pmids[0] if pmids else None
    extracted["pmid"] = primary_pmid
    pmid_topic_ok = False
    pmid_year = None
    pmid_doi = ""
    if primary_pmid and primary_pmid in pubmed_meta:
        meta = pubmed_meta[primary_pmid]
        pmid_year = meta.get("year")
        pmid_doi = meta.get("doi", "")
        blob = (meta.get("title", "") + " " + meta.get("abstract", "")).lower()
        pmid_topic_ok = (any(p.lower() in blob for p in topic["drug_patterns"]) or
                          any(p.lower() in blob for p in topic["condition_patterns"]))
        extracted["pubmed_year"] = pmid_year
        extracted["pubmed_doi"] = pmid_doi
    gates["D_pmid_topic_match"] = pmid_topic_ok

    # GATE-E: per-arm baseline counts
    bg_counts = {b["ctgov_group_code"]: int(b["count"])
                  for b in baseline.get(nct, [])
                  if b.get("scope", "").lower() == "overall"
                  and b.get("units", "") == "Participants"
                  and b.get("count", "").isdigit()}
    # Drop the "total" row
    total_n = sum(bg_counts.values())
    per_arm = {k: v for k, v in bg_counts.items() if v * 2 != total_n}
    gates["E_two_arms"] = len(per_arm) >= 2
    extracted["aact_per_arm_counts"] = per_arm

    # GATE-F: primary outcome from design_outcomes
    primary_outs = [o for o in design_outs.get(nct, [])
                     if o["outcome_type"].lower() == "primary"]
    gates["F_primary_outcome_known"] = bool(primary_outs)
    extracted["aact_primary_outcome_measure"] = primary_outs[0]["measure"][:200] if primary_outs else ""

    # Extract event counts if possible
    om = outcomes.get(nct, [])
    om_counts = [(o["ctgov_group_code"], o.get("param_value_num") or o.get("param_value", ""))
                  for o in om
                  if (o.get("param_type") or "").upper() in ("COUNT_OF_PARTICIPANTS", "NUMBER", "COUNT")]
    extracted["aact_outcome_count_rows"] = om_counts[:10]

    return {"gates": gates, "extracted": extracted}


# ─── Run pipeline ───
results = {}
for topic in TOPICS:
    stem = topic["stem"]
    print(f"\n=== {stem} ({topic['name']}) ===")
    topic_audit = {"topic": topic, "trials": [], "gate_summary": defaultdict(int),
                    "n_total": 0, "n_pass_all": 0}
    for nct in topic["ncts"]:
        r = audit_nct_in_topic(nct, topic)
        topic_audit["trials"].append(r)
        topic_audit["n_total"] += 1
        n_pass = sum(1 for v in r["gates"].values() if v)
        n_gates = len(r["gates"])
        for k, v in r["gates"].items():
            if v: topic_audit["gate_summary"][k] += 1
        all_pass = all(r["gates"].values())
        if all_pass: topic_audit["n_pass_all"] += 1
        print(f"  {nct}: {n_pass}/{n_gates} gates — {'PASS' if all_pass else 'FAIL'}")
        for g, v in r["gates"].items():
            print(f"     {g}: {'✓' if v else '✗'}")
    topic_audit["gate_summary"] = dict(topic_audit["gate_summary"])
    pass_rate = topic_audit["n_pass_all"] / max(topic_audit["n_total"], 1)
    topic_audit["pass_rate"] = pass_rate
    topic_audit["verdict"] = "VIABLE" if pass_rate >= 0.5 else "NOT_VIABLE"
    out_p = OUT / f"{stem}.json"
    out_p.write_text(json.dumps(topic_audit, indent=2, ensure_ascii=False, default=str),
                      encoding="utf-8")
    print(f"  → {stem}: pass_rate={pass_rate:.0%} verdict={topic_audit['verdict']}")

print("\n=== Summary ===")
for topic in TOPICS:
    stem = topic["stem"]
    p = json.loads((OUT / f"{stem}.json").read_text(encoding="utf-8"))
    print(f"  {stem:40s} {p['n_pass_all']}/{p['n_total']} pass — {p['verdict']}")
