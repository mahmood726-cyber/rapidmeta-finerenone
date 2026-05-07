"""Build outputs/portfolio_index.json — one row per *_REVIEW.html in
the corpus, with the metrics needed to drive dashboard.html.

Per row:
  file              ABLATION_AF_REVIEW.html
  topic             ABLATION_AF
  display_name      "Ablation AF"
  type              "NMA" | "Pairwise"
  k                 number of trials
  pooled_OR         from outputs/r_validation/<topic>.json (if present)
  ci_low / ci_high  from R validation
  I2                from R validation
  tau2              from R validation
  ncts              list of NCT ids referenced in the review
  integrity_flags   count of NCTs in this review that carry concordance flags
  has_baseline      bool — at least one trial has age/female from AACT
  last_modified     git last commit date for the file (ISO)

Idempotent. Run after r_validate.py and compute_trial_integrity.py.
"""
from __future__ import annotations
import sys, io, re, json, subprocess
from pathlib import Path
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

REPO = Path(__file__).resolve().parent.parent

NCT_RE = re.compile(r"'(NCT\d{8})'\s*:")
TREATMENTS_RE = re.compile(r"treatments\s*:\s*\[([^\]]+)\]", re.DOTALL)


def display_from_topic(topic):
    parts = topic.replace("_", " ").split()
    return " ".join(p.title() if p.isupper() and len(p) > 3 else p for p in parts)


def is_nma(text):
    # Heuristic: file has the NMA tab container OR NMA_CONFIG.treatments
    if 'id="nma-network-plot"' in text: return True
    if re.search(r"const NMA_CONFIG\s*=\s*\{[^{}]*?treatments\s*:\s*\[[^\]]+\]", text, re.DOTALL): return True
    return False


def git_last_modified(path: Path) -> str:
    try:
        r = subprocess.run(
            ["git", "log", "-1", "--format=%cI", "--", path.name],
            cwd=str(REPO), capture_output=True, text=True, timeout=10,
        )
        out = (r.stdout or "").strip()
        if out: return out
    except Exception:
        pass
    return ""


def main():
    files = sorted(REPO.glob("*_REVIEW.html"))
    print(f"Indexing {len(files)} reviews ...")

    # Load auxiliary JSONs once
    r_dir = REPO / "outputs/r_validation"
    integrity_path = REPO / "outputs/trial_integrity.json"
    integrity = json.loads(integrity_path.read_text()) if integrity_path.exists() else {}
    aact_baselines_path = REPO / "outputs/aact_baselines.json"
    aact_baselines = json.loads(aact_baselines_path.read_text()) if aact_baselines_path.exists() else {}

    rows = []
    n_with_r = 0
    for hp in files:
        text = hp.read_text(encoding="utf-8", errors="replace")
        topic = hp.stem.replace("_REVIEW", "")
        ncts = sorted(set(NCT_RE.findall(text)))
        # Treatment count for NMA
        treat_match = TREATMENTS_RE.search(text)
        n_treatments = 0
        if treat_match:
            inner = treat_match.group(1)
            n_treatments = len(re.findall(r"'[^']+'", inner))

        rtype = "NMA" if is_nma(text) else "Pairwise"

        row = {
            "file": hp.name,
            "topic": topic,
            "display_name": display_from_topic(topic),
            "type": rtype,
            "n_trials": len(ncts),
            "n_treatments": n_treatments if rtype == "NMA" else None,
            "ncts": ncts,
        }

        # R validation
        rj = r_dir / f"{topic}.json"
        if rj.exists():
            try:
                r = json.loads(rj.read_text())
                if not r.get("error"):
                    row["k"] = r.get("k")
                    row["pooled_OR"] = r.get("pooled_OR")
                    row["ci_low"] = r.get("ci_low_OR")
                    row["ci_high"] = r.get("ci_high_OR")
                    row["I2"] = r.get("I2")
                    row["tau2"] = r.get("tau2")
                    row["PI_low"] = r.get("PI_low_OR")
                    row["PI_high"] = r.get("PI_high_OR")
                    n_with_r += 1
            except Exception:
                pass

        # Integrity flags within this review
        flag_count = sum(1 for nct in ncts if integrity.get(nct, {}).get("any_flag"))
        retro_count = sum(1 for nct in ncts if integrity.get(nct, {}).get("retro_registered"))
        overdue_count = sum(1 for nct in ncts if integrity.get(nct, {}).get("results_overdue"))
        row["integrity_flags"] = flag_count
        row["retro_count"] = retro_count
        row["overdue_count"] = overdue_count

        # Has baseline data
        row["n_with_baseline"] = sum(1 for nct in ncts if aact_baselines.get(nct))

        # Last modified
        row["last_modified"] = git_last_modified(hp)

        rows.append(row)

    # Assign domain bucket based on filename keywords (best-effort)
    BUCKETS = [
        ("Cardiology", ["HF","CARDIO","CHF","HFREF","HFPEF","ARNI","SGLT2","CV","ATTR","STROKE","ACS","DOAC","AF","COL","MI","RENAL_DENERV","INCLISIRAN","STATIN","TNK","TPA","ABLATION","HCM","AFICAMTEN","BEMPEDOIC","HFCM","CABG","ROCKET","STEMI","SOTAGLIFLOZIN","PCSK9","TIRZEPATIDE","NOAC","PAH","PAD"]),
        ("Oncology",   ["ONCO","BREAST","LUNG","NSCLC","SCLC","PROSTATE","OVARIAN","HEMAT","LEUKEMI","LYMPHOMA","CLL","BTK","MYELOMA","MM_","MELANOMA","HEPATOC","HCC","COLO","GASTRIC","ENDOMETRIAL","CHECKPOINT","CART","ADC","KRAS","ALK","CDK","PARP","ARPI","TARLATAMAB","PDL1","PD1","ROS1","FGFR"]),
        ("Endocrine",  ["DIABETES","T1D","T2D","INSULIN","GLP1","INCRETIN","HBA1C","OBESITY","WEIGHT","CKD"]),
        ("ID/Vaccine", ["HIV","TB","TUBERC","MALARIA","HEPATITIS","HEPC","DENGUE","COVID","INFLUENZA","RSV","VACCINE","ANTIBIOTIC","SEPSIS","BACTER","CHOLER","TYPHOID","PEDIATRIC_HIV","PREP","ART","MDR","BPAL","ROTAVIRUS","SCHISTOSOM","YELLOW_FEVER","HPV","PNEUMONIA","CRYPTO","CARBAPENEM"]),
        ("Neuro",      ["MS","ALZHEIM","DEMENTIA","ANTIAMYLOID","CGRP","MIGRAINE","EPILEP","STROKE","SEIZURE","DRAVET","LGS","CBD","FENFLURAMINE","ANTI_CD20","DMD","DELANDISTROGENE"]),
        ("GI/IBD",     ["UC","CROHN","CD_","IBS","IBD","BIOLOGIC","UPADAC","TOFACITINIB","JAK_UC","UC_","JAK_UC_","INFLAMMATORY","BARIATRIC","RYGB","SG_","RYGB_VS_SG","H_PYLORI"]),
        ("Resp/Allergy",["ASTHMA","COPD","TEZE","DUPI","CFTR","CYSTIC","PULM"]),
        ("Renal",      ["DKD","KIDNEY","CKD","HEMODIA","DIALYSIS","GLOMERUL","FINERENONE","NEPH","AKI"]),
        ("Rheum",      ["RA_","JAKI_RA","SLE","LUPUS","BELIMUMAB","ANIFROL","SPONDYL","PSORIASIS","PSA","HIDR","ALOPECIA","AXSPA","BIOLOGICS","JIA","GOUT","URICOSURIC"]),
        ("Derm",       ["ATOPIC","DERM","ALOPECIA","VITILIG","HIDR","BIMEK"]),
        ("Hem",        ["AML","CML","HEMOPH","SICKLE","SCD","MITAPIVAT","THALAS","RUSFER","POLYC","PV_","PNH"]),
        ("Ophth",      ["NAMD","DR_","RETINOPATHY","UVEITIS","DIABETIC_RETIN","DIABETIC_MACULAR","ANTIVEGF","AVACINCAPTAD","PEGCETACO","GA_","DIABETIC_MAC","AFLIBERCEPT"]),
        ("Psych",      ["DEPRESS","ANXIETY","SCHIZO","ANTIPSYCH","BIPOLAR","ZURANOLONE","PPD","ADHD","MENTAL"]),
        ("OB-GYN",     ["PREGNANCY","POSTPARTUM","PPH_","HRT","CONTRACEP","FERTILITY","WOMEN_HEALTH","AGYW","IRON_FCM","HPV"]),
        ("Critical",   ["ICU","ARDS","SEPSIS","PRONE","TRAUMA","RESUSCIT","HYDROCORT"]),
        ("Other",      []),
    ]
    def bucket_of(topic):
        u = topic.upper()
        for name, keys in BUCKETS:
            for k in keys:
                if k in u: return name
        return "Other"
    for r in rows:
        r["bucket"] = bucket_of(r["topic"])

    out = REPO / "outputs/portfolio_index.json"
    out.write_text(json.dumps({
        "generated": __import__("datetime").datetime.now().isoformat(timespec="seconds"),
        "n_total": len(rows),
        "n_pairwise": sum(1 for r in rows if r["type"] == "Pairwise"),
        "n_nma": sum(1 for r in rows if r["type"] == "NMA"),
        "n_with_r_validation": n_with_r,
        "rows": rows,
    }, indent=2))

    print(f"\n=== Summary ===")
    print(f"  Total reviews:        {len(rows)}")
    print(f"  Pairwise:             {sum(1 for r in rows if r['type'] == 'Pairwise')}")
    print(f"  NMA:                  {sum(1 for r in rows if r['type'] == 'NMA')}")
    print(f"  With R validation:    {n_with_r}")
    print(f"  With ≥1 integrity flag: {sum(1 for r in rows if r['integrity_flags']>0)}")
    print(f"\nWritten: {out}")


if __name__ == "__main__":
    main()
