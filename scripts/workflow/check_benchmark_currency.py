#!/usr/bin/env python3
# sentinel:skip-file
"""Quarterly: for each app, search PubMed for meta-analyses / NMAs
newer than the stored benchmark citation year. Flag candidates whose
publication year is more recent than the benchmark in code.

Does NOT auto-update - published meta-analyses deserve human review.
Writes a markdown report listing candidate apps and their top PubMed
hits; the workflow opens an issue from it.
"""
import argparse, json, pathlib, re, sys, time, urllib.parse, urllib.request

ROOT = pathlib.Path(__file__).resolve().parents[2]

# Free-text search term per app (mapped from filename).
# Extend as needed; apps without an entry are silently skipped.
APP_SEARCH_TERMS = {
    "ABLATION_AF_REVIEW.html":            "catheter ablation atrial fibrillation",
    "ACALABRUTINIB_CLL_REVIEW.html":      "BTK inhibitor CLL",
    "ADC_HER2_ADJUVANT_NMA_REVIEW.html":  "HER2 ADC adjuvant breast cancer",
    "ADC_HER2_LOW_NMA_REVIEW.html":       "trastuzumab deruxtecan HER2-low",
    "ADC_HER2_NMA_REVIEW.html":           "HER2 antibody-drug conjugate metastatic breast cancer",
    "ANIFROLUMAB_SLE_REVIEW.html":        "anifrolumab systemic lupus erythematosus",
    "ANTIAMYLOID_AD_NMA_REVIEW.html":     "anti-amyloid monoclonal Alzheimer",
    "ANTIAMYLOID_AD_REVIEW.html":         "anti-amyloid monoclonal Alzheimer",
    "ANTIPSYCHOTICS_SCHIZO_NMA_REVIEW.html": "antipsychotic schizophrenia network meta-analysis",
    "ANTIVEGF_NAMD_NMA_REVIEW.html":      "anti-VEGF neovascular AMD",
    "ARNI_HF_REVIEW.html":                "sacubitril valsartan heart failure",
    "ARPI_mHSPC_REVIEW.html":             "androgen receptor pathway inhibitor mHSPC",
    "ATOPIC_DERM_NMA_REVIEW.html":        "atopic dermatitis systemic biologic network",
    "ATTR_CM_REVIEW.html":                "transthyretin cardiomyopathy",
    "BELIMUMAB_SLE_REVIEW.html":          "belimumab systemic lupus",
    "BEMPEDOIC_ACID_REVIEW.html":         "bempedoic acid cardiovascular",
    "BIOLOGIC_ASTHMA_REVIEW.html":        "biologic severe asthma",
    "BTKI_CLL_NMA_REVIEW.html":           "BTK inhibitor CLL network meta-analysis",
    "CAB_PREP_HIV_REVIEW.html":           "cabotegravir PrEP HIV",
    "CANGRELOR_PCI_REVIEW.html":          "cangrelor PCI",
    "CARDIORENAL_DKD_NMA_REVIEW.html":    "SGLT2 finerenone GLP-1 diabetic kidney disease",
    "CART_DLBCL_REVIEW.html":             "CAR-T lymphoma",
    "CART_MM_REVIEW.html":                "CAR-T multiple myeloma",
    "CBD_SEIZURE_REVIEW.html":            "cannabidiol Dravet seizure",
    "CDK46_MBC_REVIEW.html":              "CDK4/6 inhibitor metastatic breast cancer",
    "CD_BIOLOGICS_NMA_REVIEW.html":       "Crohn biologic network meta-analysis",
    "CFTR_CF_REVIEW.html":                "elexacaftor tezacaftor ivacaftor cystic fibrosis",
    "CFTR_MODULATORS_NMA_REVIEW.html":    "CFTR modulator cystic fibrosis network",
    "CGRP_MIGRAINE_NMA_REVIEW.html":      "anti-CGRP migraine network meta-analysis",
    "CGRP_MIGRAINE_REVIEW.html":          "anti-CGRP monoclonal migraine",
    "COLCHICINE_CVD_REVIEW.html":         "colchicine cardiovascular",
    "COPD_TRIPLE_REVIEW.html":            "triple therapy COPD",
    "COVID_ORAL_ANTIVIRALS_REVIEW.html":  "nirmatrelvir molnupiravir COVID",
    "DOAC_AF_NMA_REVIEW.html":            "DOAC atrial fibrillation network meta-analysis",
    "DOAC_AF_REVIEW.html":                "direct oral anticoagulant atrial fibrillation",
    "DOAC_CANCER_VTE_REVIEW.html":        "DOAC cancer VTE",
    "DOAC_VTE_NMA_REVIEW.html":           "DOAC venous thromboembolism network",
    "DUPILUMAB_AD_REVIEW.html":           "dupilumab atopic dermatitis",
    "DUPILUMAB_COPD_REVIEW.html":         "dupilumab COPD",
    "ESKETAMINE_TRD_REVIEW.html":         "esketamine treatment-resistant depression",
    "EVT_BASILAR_REVIEW.html":            "endovascular thrombectomy basilar",
    "EVT_EXTENDED_WINDOW_REVIEW.html":    "endovascular thrombectomy extended window",
    "EVT_LARGECORE_REVIEW.html":          "endovascular thrombectomy large ischemic core",
    "FARICIMAB_NAMD_REVIEW.html":         "faricimab neovascular AMD",
    "FENFLURAMINE_SEIZURE_REVIEW.html":   "fenfluramine Dravet seizure",
    "FEZOLINETANT_VMS_REVIEW.html":       "fezolinetant vasomotor",
    "FINERENONE_REVIEW.html":             "finerenone CKD type 2 diabetes",
    "GLP1_CVOT_NMA_REVIEW.html":          "GLP-1 cardiovascular outcomes network",
    "GLP1_CVOT_REVIEW.html":              "GLP-1 receptor agonist cardiovascular outcomes",
    "HIGH_EFFICACY_MS_REVIEW.html":       "ocrelizumab multiple sclerosis",
    "IL23_PSORIASIS_REVIEW.html":         "IL-23 inhibitor psoriasis",
    "IL_PSORIASIS_NMA_REVIEW.html":       "psoriasis biologic network meta-analysis",
    "INCLISIRAN_REVIEW.html":             "inclisiran LDL",
    "INCRETINS_T2D_NMA_REVIEW.html":      "GLP-1 DPP-4 type 2 diabetes network",
    "INCRETIN_HFpEF_REVIEW.html":         "GLP-1 HFpEF",
    "INSULIN_ICODEC_REVIEW.html":         "insulin icodec",
    "INTENSIVE_BP_REVIEW.html":           "intensive blood pressure control",
    "IO_CHEMO_NSCLC_1L_REVIEW.html":      "immunotherapy chemotherapy NSCLC first line",
    "IV_IRON_HF_REVIEW.html":             "intravenous iron heart failure",
    "JAKI_AD_REVIEW.html":                "JAK inhibitor atopic dermatitis",
    "JAKI_RA_NMA_REVIEW.html":            "JAK inhibitor rheumatoid arthritis network",
    "JAK_RA_REVIEW.html":                 "JAK inhibitor rheumatoid arthritis",
    "JAK_UC_REVIEW.html":                 "JAK inhibitor ulcerative colitis",
    "KARXT_SCZ_REVIEW.html":              "xanomeline trospium schizophrenia",
    "LENACAPAVIR_PREP_REVIEW.html":       "lenacapavir PrEP HIV",
    "LIPID_HUB_REVIEW.html":              "statin LDL cardiovascular",
    "LU_PSMA_MCRPC_REVIEW.html":          "177Lu-PSMA-617 mCRPC",
    "MAVACAMTEN_HCM_REVIEW.html":         "mavacamten hypertrophic cardiomyopathy",
    "MIRIKIZUMAB_UC_REVIEW.html":         "mirikizumab ulcerative colitis",
    "MITRAL_FUNCMR_REVIEW.html":          "MitraClip functional mitral regurgitation",
    "NIRSEVIMAB_INFANT_RSV_REVIEW.html":  "nirsevimab infant RSV",
    "PARP_ARPI_MCRPC_REVIEW.html":        "PARP androgen receptor inhibitor mCRPC",
    "PARP_OVARIAN_REVIEW.html":           "PARP inhibitor ovarian cancer",
    "PATISIRAN_POLYNEUROPATHY_REVIEW.html": "patisiran transthyretin polyneuropathy",
    "PBC_PPAR_REVIEW.html":                "seladelpar elafibranor primary biliary cholangitis",
    "PCSK9_LIPID_NMA_REVIEW.html":         "PCSK9 inhibitor network meta-analysis",
    "PCSK9_REVIEW.html":                   "PCSK9 inhibitor cardiovascular",
    "PEGCETACOPLAN_GA_REVIEW.html":        "pegcetacoplan geographic atrophy",
    "RENAL_DENERV_REVIEW.html":            "renal denervation hypertension",
    "RISANKIZUMAB_CD_REVIEW.html":         "risankizumab Crohn",
    "RIVAROXABAN_VASC_REVIEW.html":        "rivaroxaban vascular protection",
    "ROMOSOZUMAB_OP_REVIEW.html":          "romosozumab osteoporosis",
    "RSV_VACCINE_OLDER_REVIEW.html":       "RSV vaccine older adult",
    "SEMAGLUTIDE_OBESITY_REVIEW.html":     "semaglutide cardiovascular obesity",
    "SEVERE_ASTHMA_NMA_REVIEW.html":       "severe asthma biologic network",
    "SGLT2I_HF_NMA_REVIEW.html":           "SGLT2 inhibitor heart failure pooled",
    "SGLT2_CKD_REVIEW.html":               "SGLT2 inhibitor CKD",
    "SGLT2_HF_REVIEW.html":                "SGLT2 inhibitor heart failure",
    "SGLT2_MACE_CVOT_REVIEW.html":         "SGLT2 inhibitor MACE cardiovascular",
    "SOTAGLIFLOZIN_HF_REVIEW.html":        "sotagliflozin heart failure",
    "TAVR_LOWRISK_REVIEW.html":            "TAVR low risk aortic stenosis",
    "TDXD_HER2LOW_BC_REVIEW.html":         "trastuzumab deruxtecan HER2-low breast cancer",
    "TIRZEPATIDE_OBESITY_REVIEW.html":     "tirzepatide obesity",
    "TIRZEPATIDE_T2D_REVIEW.html":         "tirzepatide type 2 diabetes",
    "TNK_VS_TPA_STROKE_REVIEW.html":       "tenecteplase alteplase stroke",
    "UC_BIOLOGICS_NMA_REVIEW.html":        "ulcerative colitis biologic network meta-analysis",
    "UPADACITINIB_CD_REVIEW.html":         "upadacitinib Crohn",
    "VENETOCLAX_AML_REVIEW.html":          "venetoclax AML",
}

PUBMED_BASE = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils"
STORED_YEAR_RE = re.compile(r"citation:\s*'[^']+\s+(\d{4})'")


def latest_stored_year(app_html: str) -> int | None:
    """Scan PUBLISHED_META_BENCHMARKS entries for the newest cited year."""
    years = [int(m.group(1)) for m in STORED_YEAR_RE.finditer(app_html)]
    return max(years) if years else None


def pubmed_search(term: str, mindate: int) -> list[dict]:
    """Return up to 5 most recent meta-analyses / NMAs matching the term."""
    q = f'({term}) AND (meta-analysis[Publication Type] OR network meta-analysis[Title/Abstract])'
    params = urllib.parse.urlencode({
        "db": "pubmed", "term": q, "retmode": "json", "retmax": "5",
        "sort": "pub+date", "mindate": f"{mindate}/01/01", "maxdate": "3000",
    })
    try:
        with urllib.request.urlopen(f"{PUBMED_BASE}/esearch.fcgi?{params}", timeout=15) as r:
            ids = json.loads(r.read().decode()).get("esearchresult", {}).get("idlist", [])
    except Exception as e:
        return [{"error": str(e)[:100]}]
    if not ids:
        return []
    sparams = urllib.parse.urlencode({"db": "pubmed", "id": ",".join(ids), "retmode": "json"})
    try:
        with urllib.request.urlopen(f"{PUBMED_BASE}/esummary.fcgi?{sparams}", timeout=15) as r:
            summary = json.loads(r.read().decode()).get("result", {})
    except Exception as e:
        return [{"error": str(e)[:100]}]
    hits = []
    for pmid in ids:
        doc = summary.get(pmid, {})
        if not doc:
            continue
        year = None
        pubdate = doc.get("pubdate", "")
        ym = re.search(r"\b(20\d{2})\b", pubdate)
        if ym:
            year = int(ym.group(1))
        hits.append({
            "pmid": pmid,
            "title": doc.get("title", "")[:200],
            "year": year,
            "journal": doc.get("fulljournalname", ""),
        })
    return hits


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--report", required=True)
    args = ap.parse_args()
    rep = ROOT / args.report
    rep.parent.mkdir(parents=True, exist_ok=True)

    candidates = []
    for app_name, search_term in APP_SEARCH_TERMS.items():
        app_path = ROOT / app_name
        if not app_path.exists():
            continue
        html = app_path.read_text(encoding="utf-8", errors="replace")
        stored_year = latest_stored_year(html)
        if stored_year is None:
            continue  # app has no benchmarks (legacy retrofit or NMA template)
        hits = pubmed_search(search_term, mindate=stored_year + 1)
        newer = [h for h in hits if h.get("year") and h["year"] > stored_year]
        if newer:
            candidates.append({
                "app": app_name,
                "stored_year": stored_year,
                "search": search_term,
                "hits": newer,
            })
        time.sleep(0.35)  # courtesy rate-limit; eutils allows 3/sec without key

    if not candidates:
        print("All benchmarks are current.")
        if rep.exists():
            rep.unlink()
        return 0

    lines = [
        "# Benchmark refresh candidates",
        "",
        f"Found newer published meta-analyses for **{len(candidates)}** app(s) since the stored benchmark.",
        "",
        "Review each candidate manually. Auto-updating is intentionally out of scope - published MAs deserve human review before replacing a reference in the UI.",
        "",
    ]
    for c in candidates:
        lines.append(f"## {c['app']}")
        lines.append(f"- Stored benchmark year: **{c['stored_year']}**")
        lines.append(f"- PubMed search: `{c['search']}`")
        lines.append(f"- Candidate hits (year > {c['stored_year']}):")
        for h in c["hits"]:
            pmid = h.get("pmid", "?")
            title = h.get("title", "")
            year = h.get("year", "?")
            journal = h.get("journal", "")
            lines.append(f"  - **{year}** {journal}: {title} ([PubMed:{pmid}](https://pubmed.ncbi.nlm.nih.gov/{pmid}/))")
        lines.append("")

    rep.write_text("\n".join(lines), encoding="utf-8")
    print(f"Wrote benchmark-currency report with {len(candidates)} candidate(s) to {rep}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
