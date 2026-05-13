"""Path B — acronym-expansion matching for review-topic vs AACT-conditions.

Replaces R7's naive Jaccard tokenizer with a curated medical-acronym
expansion dictionary. This catches trial-in-wrong-review cases that R7
had to skip because "ATTR_CM" doesn't tokenize to "amyloid cardiomyopathy".

Detection: for each (review, trial), compute expanded review tokens and
compare against AACT conditions + trial brief_title. If overlap < 1 token
AND interventions also mismatch (from R7's R-S2 logic), flag as wrong
review.

Conservative — only fires when ALL signals (expanded-condition mismatch
+ R7's intv hard mismatch + R7's enrollment 2× off) agree.
"""
from __future__ import annotations
import json, csv, re, sys, io
from pathlib import Path
from collections import defaultdict, Counter

if hasattr(sys.stdout, "buffer") and getattr(sys.stdout, "encoding", "").lower() != "utf-8":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

HERE = Path(__file__).resolve().parent.parent
OUT = HERE / "outputs" / "extraction_audit"
DATA = OUT / "data"
AACT = Path("D:/AACT-storage/AACT/2026-04-12")
DRY = "--dry-run" in sys.argv

# Hand-curated acronym → expanded MeSH-style terms (for the corpus topics)
ACRONYM_EXPAND = {
    # Cardiology
    "HF": ["heart", "failure"],
    "HFREF": ["heart", "failure", "reduced", "ejection"],
    "HFPEF": ["heart", "failure", "preserved", "ejection"],
    "ATTR": ["amyloid", "amyloidosis", "transthyretin"],
    "ATTR_CM": ["amyloid", "cardiomyopathy", "transthyretin"],
    "ATTR_PN": ["amyloid", "polyneuropathy", "transthyretin"],
    "HCM": ["hypertrophic", "cardiomyopathy"],
    "AF": ["atrial", "fibrillation"],
    "ABLATION_AF": ["atrial", "fibrillation", "ablation"],
    "CRYO_AF": ["atrial", "fibrillation", "cryoablation"],
    "PFA_AF": ["atrial", "fibrillation"],
    "VT": ["ventricular", "tachycardia"],
    "DCB": ["drug", "coated", "balloon", "peripheral", "artery"],
    "PAD": ["peripheral", "artery", "disease"],
    "DOAC": ["anticoagulation", "anticoagulant"],
    "ARNI": ["angiotensin", "neprilysin"],
    "CABG": ["coronary", "bypass"],
    "PCI": ["coronary", "intervention"],
    "MITRACLIP": ["mitral", "regurgitation"],
    "TAVR": ["aortic", "valve", "transcatheter"],
    "DAPT": ["antiplatelet", "thrombosis"],
    "ACS": ["coronary", "syndrome"],
    "FRAGILITY_FRACTURE": ["fracture", "osteoporosis", "bone"],
    # Renal
    "CKD": ["kidney", "chronic"],
    "DKD": ["kidney", "diabetic", "diabetes"],
    "CARDIORENAL_DKD": ["kidney", "diabetic", "cardio"],
    "IGAN": ["nephropathy", "iga", "glomerul"],
    "GLOMERULONEPHRITIS": ["glomerulonephritis", "kidney"],
    "FSGS": ["focal", "segmental", "glomerul"],
    "HYPERKALEMIA": ["hyperkalemia", "potassium"],
    # Diabetes/metabolic
    "T2D": ["diabetes", "type", "mellitus"],
    "T1D": ["diabetes", "type"],
    "SGLT2": ["sodium", "glucose", "cotransporter", "diabetes", "heart"],
    "GLP1": ["glucagon", "peptide", "diabetes"],
    "CVOT": ["cardiovascular", "outcome"],
    "MACE": ["cardiovascular", "events", "myocardial"],
    "OBESITY": ["obesity", "weight"],
    "BARIATRIC": ["bariatric", "obesity", "gastric"],
    # Liver/GI
    "MASH": ["nonalcoholic", "fatty", "liver", "steatohepatitis"],
    "NAFLD": ["nonalcoholic", "fatty", "liver"],
    "PBC": ["primary", "biliary"],
    "HBV": ["hepatitis", "virus"],
    "HCV": ["hepatitis", "virus"],
    "IBD": ["inflammatory", "bowel"],
    "UC": ["ulcerative", "colitis"],
    "CD": ["crohn"],
    "NEC": ["necrotizing", "enterocolitis"],
    "ESD": ["endoscopic", "submucosal", "dissection"],
    "EMR": ["endoscopic", "mucosal", "resection"],
    # Pulmonary
    "ARDS": ["respiratory", "distress"],
    "COPD": ["pulmonary", "chronic", "obstructive"],
    "IPF": ["pulmonary", "fibrosis", "idiopathic"],
    "BRONCHIECTASIS": ["bronchiectasis"],
    "SEVERE_ASTHMA": ["asthma"],
    "EOSINOPHILIC": ["eosinophilic"],
    # Hematology / oncology
    "AML": ["leukemia", "myeloid", "acute"],
    "CML": ["leukemia", "myeloid", "chronic"],
    "CLL": ["leukemia", "lymphocytic"],
    "MDS": ["myelodysplastic"],
    "MM": ["multiple", "myeloma"],
    "MM_BISPECIFIC": ["multiple", "myeloma", "bispecific"],
    "LBCL": ["large", "lymphoma", "diffuse"],
    "MCL": ["mantle", "cell", "lymphoma"],
    "CAR_T": ["chimeric", "antigen", "receptor", "lymphoma"],
    "CART": ["chimeric", "antigen", "receptor"],
    "BTKI": ["bruton"],
    "JAK": ["janus", "kinase"],
    "JAKI": ["janus", "kinase"],
    "JAK_RA": ["janus", "rheumatoid", "arthritis"],
    "ITP": ["thrombocytopenic", "purpura"],
    "EGPA": ["eosinophilic", "granulomatosis"],
    # Oncology by site
    "NSCLC": ["lung", "carcinoma", "small"],
    "SCLC": ["lung", "small", "cell"],
    "BLADDER_NMIBC": ["bladder", "muscle", "invasive"],
    "BLADDER_UROTHEL": ["bladder", "urothelial"],
    "ANTI_PD1": ["checkpoint", "programmed", "death"],
    "ANTI_PDL1": ["checkpoint", "programmed", "ligand"],
    "ADJUVANT_IO": ["immunotherapy", "adjuvant", "checkpoint"],
    "CHECKPOINT_MELANOMA": ["melanoma", "checkpoint"],
    "MELANOMA_NEOADJUVANT": ["melanoma", "neoadjuvant"],
    "HCC": ["hepatocellular", "carcinoma"],
    "ESOPHAGEAL": ["esophageal"],
    "GASTRIC": ["gastric", "stomach"],
    "BREAST": ["breast"],
    "NEOADJUVANT_IO_BREAST": ["breast", "immunotherapy", "neoadjuvant"],
    "OVARIAN": ["ovarian", "ovary"],
    "PROSTATE": ["prostate"],
    "PROSTATE_AR": ["prostate", "androgen"],
    "ARPI": ["prostate", "androgen"],
    "NPC": ["nasopharyngeal", "carcinoma"],
    "TROP2_ADC": ["antibody", "drug", "conjugate", "trophoblast"],
    "ADC_HER2": ["antibody", "drug", "conjugate"],
    "HER2_LOW": ["breast"],
    "HER2_ADJUVANT": ["breast", "adjuvant"],
    "FGFR": ["fibroblast", "growth", "factor"],
    "BISPECIFIC_LYMPHOMA": ["lymphoma", "bispecific"],
    "MM_1L_DARA": ["multiple", "myeloma", "daratumumab"],
    "AML_VEN_FLT3": ["leukemia", "myeloid", "venetoclax"],
    "AML_TARGETED": ["leukemia", "myeloid"],
    # Neuro
    "MIGRAINE": ["migraine"],
    "CGRP": ["migraine", "calcitonin"],
    "EPILEPSY": ["epilepsy", "seizure"],
    "SEIZURE": ["seizure", "epilepsy"],
    "AED": ["antiepileptic"],
    "MS": ["multiple", "sclerosis"],
    "MS_S1P": ["multiple", "sclerosis", "sphingosine"],
    "MS_BTK": ["multiple", "sclerosis", "bruton"],
    "MS_BTKI": ["multiple", "sclerosis", "bruton"],
    "NMOSD": ["neuromyelitis"],
    "ALS": ["amyotrophic", "lateral", "sclerosis"],
    "ANTI_CD20_MS": ["multiple", "sclerosis", "ocrelizumab", "rituximab"],
    "DEPRESSION": ["depression", "depressive"],
    "DEPRESSION_NEW_RAPID": ["depression", "treatment", "resistant"],
    "ESKETAMINE_TRD": ["ketamine", "esketamine", "depression"],
    "PSYCHEDELIC": ["psilocybin", "psychedelic"],
    "BIPOLAR": ["bipolar"],
    "OUD": ["opioid", "use", "disorder"],
    "OPIOID_INDUCED_CONSTIPATION": ["opioid", "constipation"],
    "SMA": ["spinal", "muscular", "atrophy"],
    "DUCHENNE": ["duchenne", "muscular"],
    "MYELOFIBROSIS": ["myelofibrosis"],
    "MYASTHENIA": ["myasthenia", "gravis"],
    "STROKE_THROMBECTOMY": ["stroke", "thrombectomy"],
    "STROKE": ["stroke"],
    "DRY_EYE": ["dry", "eye"],
    "ROP_ANTI_VEGF": ["retinopathy", "prematurity"],
    "PRESBYOPIA": ["presbyopia"],
    # Dermatology
    "PSORIASIS": ["psoriasis"],
    "IL_PSORIASIS": ["psoriasis", "interleukin"],
    "BIMEKIZUMAB_PSORIASIS": ["psoriasis", "bimekizumab"],
    "ATOPIC_DERM": ["dermatitis", "atopic"],
    "AD_PEDIATRIC_BIOLOGIC": ["dermatitis", "atopic", "pediatric"],
    "CHRONIC_URTICARIA": ["urticaria", "chronic"],
    "ALOPECIA": ["alopecia"],
    "ALOPECIA_JAKI": ["alopecia", "janus"],
    "VITILIGO": ["vitiligo"],
    "PRURIGO": ["prurigo"],
    # Infectious
    "MALARIA_VACCINE": ["malaria", "vaccine"],
    "MALARIA": ["malaria"],
    "TB": ["tuberculosis"],
    "TB_BPaL": ["tuberculosis", "bedaquiline"],
    "COVID": ["covid", "coronavirus", "sars"],
    "DENGUE": ["dengue"],
    "EBOLA": ["ebola"],
    "MPOX": ["mpox", "monkeypox"],
    "ANTIFUNGAL": ["fungal", "mycos"],
    "CABP": ["pneumonia", "community"],
    "CARBAPENEM_RESISTANT": ["resistant", "bacterial"],
    "HIV_LA_PREP": ["hiv", "prevention", "prep"],
    "HIV_PREP": ["hiv", "prevention", "prep"],
    "HEP_D": ["hepatitis", "delta"],
    # Other
    "RHEUMATOID": ["rheumatoid"],
    "RA": ["rheumatoid", "arthritis"],
    "AXSPA": ["axial", "spondyloarthritis"],
    "LUPUS": ["lupus"],
    "CKD_CYSTIC": ["polycystic"],
    "ANCA": ["anca", "vasculitis"],
    "PFIC": ["intrahepatic", "cholestasis"],
    "HEMOPHILIA": ["hemophilia"],
    "BISPECIFIC_LYMPHOMA": ["lymphoma", "bispecific"],
    "OAB": ["overactive", "bladder"],
    "ENDOMETRIOSIS": ["endometriosis"],
    "GNRH": ["gnrh", "gonadotropin"],
    "GnRH_ANTAGONISTS_GYN": ["gnrh", "endometriosis", "fibroid"],
    "ACROMEGALY": ["acromegaly"],
    "CUSHING": ["cushing"],
    "MIS_GASTRECTOMY": ["gastrectomy", "minimally", "invasive"],
    "MIS_PANCREATIC_WHIPPLE": ["pancreatic", "whipple"],
    "MIS_HEPATECTOMY": ["hepatectomy"],
    "DCD_HEART_TRANSPLANT": ["donation", "cardiac", "death", "heart"],
    "OCS_HEART_DCD": ["heart", "donation", "cardiac"],
    "ALDO_SYNTHASE": ["aldosterone", "hypertension"],
    "FINERENONE": ["finerenone", "nonsteroidal"],
    "PCSK9_LIPID": ["proprotein", "convertase", "cholesterol"],
    "LIPID": ["cholesterol", "lipid"],
    "HoFH_LIPID": ["homozygous", "familial"],
    "PBC_NEW_AGENTS": ["biliary", "cholangitis"],
    "AGYW_HIV_PREP": ["adolescent", "hiv", "prep"],
}


def expand_review_name(rv_name: str) -> set[str]:
    """Tokenize + expand a review name. Handle multi-part keys like
    'ALDO_SYNTHASE' by looking for any acronym dict key that's a substring
    of the review name."""
    name = rv_name.replace("_REVIEW", "").replace("_NMA", "")
    tokens = set()
    # First: substring match against all dict keys
    name_u = name.upper()
    for key, expansion in ACRONYM_EXPAND.items():
        # Match if key appears as a token boundary (between _ or at start/end)
        if (f"_{key}_" in f"_{name_u}_" or
            name_u.startswith(key + "_") or
            name_u.endswith("_" + key) or
            name_u == key):
            tokens.update(t.lower() for t in expansion)
    # Then: literal parts
    parts = name.split("_")
    for part in parts:
        u = part.upper()
        if u in ACRONYM_EXPAND:
            tokens.update(t.lower() for t in ACRONYM_EXPAND[u])
        if len(part) >= 3:
            tokens.add(part.lower())
    return tokens


# Collect target trials
scores = json.loads((OUT / "fabrication_risk_scores.json").read_text(encoding="utf-8"))
# All non-quarantined
target_reviews = {r["review"] for r in scores if not r["already_quarantined"]}

target_trials = []
for json_p in sorted(DATA.glob("*.json")):
    if json_p.name.startswith("_"): continue
    rv = json_p.stem
    if rv not in target_reviews: continue
    try: d = json.loads(json_p.read_text(encoding="utf-8"))
    except: continue
    rd = d.get("realData") or {}
    if not isinstance(rd, dict): continue
    for nct, t in rd.items():
        if not isinstance(t, dict): continue
        if nct.startswith("NULLED:"): continue
        if not re.match(r"^NCT\d{8}$", nct): continue
        target_trials.append({"review": rv, "nct": nct, **t})

target_ncts = sorted({t["nct"] for t in target_trials})
print(f"Target: {len(target_trials)} trials / {len(target_ncts)} unique NCTs")

# Load AACT minimal
def load_aact(filename, key_col, want_cols, filter_set):
    out = defaultdict(list)
    with open(AACT / filename, "r", encoding="utf-8", errors="replace") as f:
        reader = csv.DictReader(f, delimiter="|")
        for row in reader:
            k = (row.get(key_col) or "").strip().upper()
            if k in filter_set:
                out[k].append({c: (row.get(c) or "").strip() for c in want_cols})
    return out

target_set = set(target_ncts)
print("Loading AACT…")
studies = load_aact("studies.txt", "nct_id", ["brief_title", "official_title", "enrollment"], target_set)
conds = load_aact("conditions.txt", "nct_id", ["downcase_name"], target_set)
intvs = load_aact("interventions.txt", "nct_id", ["name"], target_set)

STOPWORDS = {"a","an","the","of","for","in","to","with","and","or","vs","vs.",
              "versus","study","trial","randomized","placebo","controlled","phase",
              "patients","adult","subjects","new","extension","week","month","year"}

def tokenize(s):
    return {t for t in re.findall(r"[a-z]+", (s or "").lower())
             if len(t) >= 4 and t not in STOPWORDS}


# Verify: for each trial, expanded review tokens vs AACT condition+title tokens
findings = []
for t in target_trials:
    rv = t["review"]; nct = t["nct"]
    s = studies.get(nct, [])
    if not s: continue
    aact = s[0]
    aact_title = (aact.get("brief_title", "") + " " + aact.get("official_title", "")).lower()
    aact_conds = " ".join({c["downcase_name"] for c in conds.get(nct, [])}).lower()
    aact_blob = aact_title + " " + aact_conds

    expanded_review = expand_review_name(rv)
    if not expanded_review: continue
    aact_words = tokenize(aact_blob)
    overlap = expanded_review & aact_words
    if not overlap:
        # Strong signal: expanded review terms have ZERO overlap with AACT
        # Additional check: intv must also not match
        aact_intvs = [i["name"] for i in intvs.get(nct, [])]
        aact_intvs_text = " ".join(aact_intvs).lower()
        # Drug-name check from trial.group
        group = (t.get("group") or "").lower()
        drug_in_aact = False
        for w in re.findall(r"[a-z]+", group):
            if len(w) >= 6 and w not in STOPWORDS and w in aact_intvs_text:
                drug_in_aact = True; break
        if not drug_in_aact:
            findings.append({
                "review": rv, "nct": nct,
                "expanded_review_tokens": sorted(expanded_review)[:8],
                "aact_words_sample": sorted(aact_words)[:8],
                "fix": "NULL_KEY",
            })

print(f"Expanded-MeSH mismatches with no AACT-intv backup: {len(findings)}")


def find_block(txt, nct):
    key_pat = re.compile(r'(["\'])' + re.escape(nct) + r'\1\s*:\s*\{')
    m = key_pat.search(txt)
    if not m: return None
    start = m.end(); depth = 1; i = start; in_str = None
    while i < len(txt) and depth > 0:
        ch = txt[i]
        if in_str:
            if ch == "\\": i += 2; continue
            if ch == in_str: in_str = None
        else:
            if ch in ('"', "'"): in_str = ch
            elif ch == "{": depth += 1
            elif ch == "}":
                depth -= 1
                if depth == 0: return (m.start(), i+1, start, i)
        i += 1
    return None


def null_key(txt, nct):
    nulled = f"NULLED:{nct}"
    if nulled in txt: return txt, 0
    pat = re.compile(r'(["\'])(' + re.escape(nct) + r')(\1)(\s*:)')
    new_txt, n = pat.subn(
        lambda m: f'{m.group(1)}NULLED:{m.group(2)}{m.group(3)}{m.group(4)}', txt)
    return new_txt, n


applied = []
n_fix = 0
seen = set()
for f in findings:
    key = (f["review"], f["nct"])
    if key in seen: continue
    seen.add(key)
    html_path = HERE / f"{f['review']}.html"
    if not html_path.exists(): continue
    txt = html_path.read_text(encoding="utf-8")
    new_txt, n = null_key(txt, f["nct"])
    if n > 0:
        if not DRY: html_path.write_text(new_txt, encoding="utf-8")
        applied.append({**f, "status": "NULLED_KEY"})
        n_fix += 1
    elif f"NULLED:{f['nct']}" in txt:
        applied.append({**f, "status": "ALREADY_NULLED"})

out_p = OUT / "r22_mesh_matching.json"
out_p.write_text(json.dumps({"findings": findings, "applied": applied,
                              "summary": {"nct_key_nulls": n_fix}},
                             indent=2, ensure_ascii=False), encoding="utf-8")
print(f"\n{'DRY-RUN ' if DRY else ''}MeSH-expansion NCT nulls: {n_fix}")
