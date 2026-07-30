#!/usr/bin/env python
"""Global-health / communicable-disease RapidMeta app INVENTORY scanner.

Read-only. Produces the inventory table that drives the "HFrEF upgrade
procedure" rollout (see GLOBAL_HEALTH_UPGRADE_RECIPE.md).

For every `*_REVIEW.html` in the corpus it records:
  * topic classification against a global-health / communicable-disease
    taxonomy (matched on <title> + <h1>, NOT on filename alone - filenames
    like APREPITANT_CINV match a naive /ART_/ grep and are not in scope);
  * BOTH verdict surfaces, and whether they AGREE:
      - machine  : `window.__verdict` JSON (verdict / p0_total / n_trials_seen)
      - visible  : `<div id="rapidmeta-integrity-badge">` headline, background
                   colour, fabrication-risk score and "Trials: N"
  * real-injected-data vs template/stub (byte size, distinct NCT count,
    distinct named trials, presence of an effect payload);
  * residual SGLT2i / cardio-renal contamination survivors.

Usage:
  python scripts/gh_inventory.py                 # scan, print table, write JSON
  python scripts/gh_inventory.py --all-topics    # do not filter to global health
  python scripts/gh_inventory.py --json PATH     # override output path
"""
from __future__ import annotations

import argparse
import glob
import io
import json
import os
import re
import sys

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

ROOT = os.environ.get(
    "RAPIDMETA_REPO_ROOT",
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
)

# ---------------------------------------------------------------------------
# Topic taxonomy. Ordered - first match wins, so specific beats generic.
# Patterns are matched case-insensitively against "<title> <h1>" only.
# ---------------------------------------------------------------------------
TAXONOMY = [
    # NB: IPTp/IPTi/SMC/R21 MUST carry word boundaries - a bare `IPTi` matches
    # inside "sitagl-IPTI-n" / "alogl-IPTI-n" and dragged four T2D apps into the
    # malaria bucket.
    ("malaria",            r"malaria|artemether|artesunate|lumefantrine|primaquine|tafenoquine|plasmodium|\bRTS,?S\b|\bR21\b|chemoprevention.*malaria|\bIPTp\b|\bIPTi\b|\bSMC\b"),
    ("tb-treatment",       r"\btuberculos|(\bTB\b.*(treat|regimen|MDR|XDR|drug-resist))|bedaquiline|pretomanid|delamanid|linezolid.*TB|GeneXpert|Xpert"),
    ("tb-prevention",      r"(\bTB\b|tuberculos).*(prevent|prophyla|latent|LTBI|preventive therapy)|rifapentine|isoniazid preventive|\b3HP\b|\b1HP\b|BCG"),
    ("hiv-prevention",     r"(\bHIV\b.*(prevent|PrEP|prophylax))|\bPrEP\b|cabotegravir.*prep|\bAGYW\b|\bVMMC\b|\bPMTCT\b|voluntary medical male circumcision"),
    ("hiv-treatment",      r"\bHIV\b.*(treat|\bTX\b|ART|antiretroviral|first-line|regimen|suppress)|dolutegravir|efavirenz|raltegravir|doravirine|bictegravir|cabotegravir(?!.*prep)|lenacapavir(?!.*prep)|tenofovir.*HIV|emtricitabine",),
    ("hiv-oi",             r"cryptococc|pneumocystis|\bPCP\b.*HIV|HIV.*opportunistic|toxoplasm"),
    ("vaccines-epidemic",  r"ebola|marburg|mpox|monkeypox|lassa|nipah|cholera vaccin|meningococcal.*(conjugate|A\b)|yellow fever"),
    ("vaccines-covid",     r"COVID.?19.*vaccin|SARS-CoV-2.*vaccin|mRNA-?1273|BNT162|ChAdOx|CVnCoV|NVX-CoV"),
    ("vaccines-routine",   r"rotavirus|pneumococcal conjugate|\bPCV\d|\bPPSV|prevnar|\bHPV\b|measles|polio|typhoid.*(vaccin|conjugate)|\bTyVac\b|hepatitis a vaccin|\bHEPA VACCINE\b|rabies vaccin|\bRSV\b.*(vaccin|prophyla)|\bRSVPREF3\b|nirsevimab|palivizumab|influenza vaccin|influenza recombinant|pertussis|\bDTP\b"),
    ("vaccines-dengue",    r"dengue"),
    ("covid-therapeutics", r"COVID|SARS-CoV-2|molnupiravir|nirmatrelvir|paxlovid|remdesivir|tocilizumab.*COVID|sarilumab.*COVID|bamlanivimab|etesevimab"),
    ("ntd",                r"schistosom|praziquantel|onchocerc|lymphatic filaria|ivermectin.*(LF|filaria|oncho|scabies)|albendazole|mebendazole|deworm|soil-transmitted helminth|trachoma|leishmania|trypanosom|chagas|buruli|lepros|yaws|guinea worm|dracunculi|snakebite|scabies|rabies(?!.*vaccin)|taenia|echinococc"),
    ("hepatitis",          r"hepatitis [bc]\b|\bHBV\b|\bHCV\b|sofosbuvir|ledipasvir|daclatasvir|velpatasvir|glecaprevir|pibrentasvir|grazoprevir|elbasvir|ombitasvir|paritaprevir|dasabuvir|simeprevir|direct-acting antiviral"),
    ("pneumonia-ari",      r"(childhood|child|paediatric|pediatric|community-acquired).*pneumonia|\bARI\b|acute respiratory infection|amoxicillin.*pneumonia"),
    ("diarrhoea",          r"diarrh|oral rehydration|\bORS\b|zinc.*(diarrh|child)|cholera(?!.*vaccin)|shigell|cryptosporid"),
    ("malnutrition",       r"malnutrition|\bSAM\b.*(child|acute)|wasting|stunting|ready-to-use therapeutic|\bRUTF\b|kwashiorkor|micronutrient|vitamin a supplement"),
    ("maternal-neonatal",  r"maternal|neonat|preterm|birth ?weight|postpartum h[ae]morrhage|\bPPH\b|eclampsia|kangaroo mother|umbilical|chlorhexidine.*cord|antenatal cortico"),
    ("child-mortality",    r"child mortality|under-?5 mortality|infant mortality|mass drug administration.*azithromycin|azithromycin.*child"),
    ("amr-sepsis",         r"antimicrobial resistance|\bAMR\b|sepsis|septic shock|bloodstream infection|neonatal sepsis"),
    ("sti",                r"syphilis|gonorrh|chlamyd|\bSTI\b|trichomonia|bacterial vaginosis"),
    ("anaemia-nutrition",  r"an[ae]mia.*(child|pregnan|iron|LMIC)|iron deficiency.*(pregnan|child)|hookworm"),
]

# Signals that a topic is Africa / LMIC-anchored beyond the disease itself.
AFRICA_ANCHOR = re.compile(
    r"sub-?saharan|\bAfrica|\bLMIC|low-?income|low- ?and middle-?income|"
    r"resource-limited|resource-poor|\bWHO\b|Uganda|Kenya|Tanzania|Nigeria|Ghana|"
    r"Malawi|Zambia|Zimbabwe|Mozambique|Ethiopia|Rwanda|Burkina|Mali\b|Niger\b|"
    r"South Africa|Botswana|Senegal|C[oô]te d.Ivoire|Cameroon|DRC|Democratic Republic",
    re.I,
)

# Residual base-engine contamination survivors (SGLT2-HF / finerenone origin).
CONTAM = {
    "sglt2":        re.compile(r"SGLT2|SGLT-2|dapagliflozin|empagliflozin|canagliflozin|sotagliflozin", re.I),
    "sglt2_ae":     re.compile(r"Fournier|genital mycotic|diabetic ketoacidosis|\bDKA\b", re.I),
    "hf_trials":    re.compile(r"DAPA-HF|EMPEROR-(Reduced|Preserved)|DELIVER\b|EMPA-REG", re.I),
    "finerenone":   re.compile(r"finerenone|FIDELIO|FIGARO", re.I),
    "sglt2hf_title": re.compile(r"SGLT2-HF", re.I),
}
# finerenone appears legitimately in repo/asset URLs (rapidmeta-finerenone).
FINERENONE_URL = re.compile(r"rapidmeta-finerenone", re.I)

RE_TITLE   = re.compile(r"<title>(.*?)</title>", re.S | re.I)
RE_H1      = re.compile(r"<h1[^>]*>(.*?)</h1>", re.S | re.I)
RE_VERDICT = re.compile(r"window\.__verdict\s*=\s*(\{.*?\});", re.S)
RE_BADGE   = re.compile(
    r'<div id="rapidmeta-integrity-badge".*?</div>\s*</div>', re.S
)
RE_BADGE_BG      = re.compile(r'id="rapidmeta-integrity-badge"[^>]*background:(#[0-9a-fA-F]{3,6})')
RE_BADGE_HEAD    = re.compile(r'id="rapidmeta-integrity-badge".*?<strong[^>]*>(.*?)</strong>', re.S)
RE_BADGE_TRIALS  = re.compile(r'Trials:\s*<strong>(\d+)</strong>')
RE_BADGE_FABRISK = re.compile(r'Fabrication-risk score:\s*<strong>([\d.]+)</strong>')
RE_NCT           = re.compile(r"\bNCT\d{8}\b")
RE_TAG           = re.compile(r"<[^>]+>")

# Green backgrounds = the badge is asserting a clean bill of health.
GREEN_BG = {"#15803d", "#166534", "#16a34a", "#22c55e", "#14532d"}


def strip_tags(s: str) -> str:
    return re.sub(r"\s+", " ", RE_TAG.sub(" ", s)).strip()


def classify(text: str) -> str | None:
    for name, pat in TAXONOMY:
        if re.search(pat, text, re.I):
            return name
    return None


def scan(path: str) -> dict:
    s = open(path, encoding="utf-8", errors="replace").read()
    fname = os.path.basename(path)
    title = strip_tags(RE_TITLE.search(s).group(1)) if RE_TITLE.search(s) else ""
    h1s = " | ".join(strip_tags(m.group(1))[:120] for m in list(RE_H1.finditer(s))[:3])
    header = f"{title} {h1s}"

    rec: dict = {
        "file": fname,
        "bytes": len(s),
        "title": title[:160],
        "topic": classify(header) or classify(fname.replace("_", " ")),
        "africa_anchor": bool(AFRICA_ANCHOR.search(header)),
        "africa_mentions": len(AFRICA_ANCHOR.findall(s)),
    }

    # --- surface 1: machine verdict -----------------------------------------
    m = RE_VERDICT.search(s)
    if m:
        try:
            v = json.loads(m.group(1))
        except json.JSONDecodeError:
            v = {}
        counts = v.get("counts", {}) or {}
        rec["verdict"] = v.get("verdict")
        rec["p0_total"] = v.get("p0_total")
        rec["n_trials_seen"] = counts.get("n_trials_seen")
        rec["p2_evidence_incomplete"] = counts.get("P2_evidence_incomplete")
        rec["p1_total"] = sum(int(x) for k, x in counts.items()
                              if k.startswith("P1_") and isinstance(x, (int, float)))
        rec["verdict_reasons"] = v.get("reasons", [])
    else:
        rec["verdict"] = None

    # --- surface 2: visible integrity badge ---------------------------------
    if 'id="rapidmeta-integrity-badge"' in s:
        rec["badge"] = True
        mh = RE_BADGE_HEAD.search(s)
        rec["badge_headline"] = strip_tags(mh.group(1))[:80] if mh else None
        mb = RE_BADGE_BG.search(s)
        rec["badge_bg"] = mb.group(1).lower() if mb else None
        rec["badge_green"] = rec["badge_bg"] in GREEN_BG
        mt = RE_BADGE_TRIALS.search(s)
        rec["badge_trials"] = int(mt.group(1)) if mt else None
        mf = RE_BADGE_FABRISK.search(s)
        rec["badge_fabrisk"] = float(mf.group(1)) if mf else None
    else:
        rec["badge"] = False
        rec["badge_green"] = False
        rec["badge_trials"] = None
        rec["badge_headline"] = None

    # --- do the two surfaces agree? -----------------------------------------
    disagree = []
    if rec["badge"] and rec["verdict"] is not None:
        if rec["badge_green"] and (rec.get("p0_total") or 0) > 0:
            disagree.append("green_badge_over_P0")
        if rec["badge_green"] and rec["verdict"] not in ("STABLE", "PASS", "CLEAN"):
            disagree.append(f"green_badge_over_verdict={rec['verdict']}")
        if rec["badge_green"] and (rec.get("p1_total") or 0) > 0:
            disagree.append(f"green_badge_over_P1={rec['p1_total']}")
        bt, nt = rec.get("badge_trials"), rec.get("n_trials_seen")
        if bt is not None and nt is not None and bt != nt:
            disagree.append(f"trial_count_badge{bt}_vs_verdict{nt}")
        # A green "checks passed" badge on an app whose own verdict says every
        # trial is missing evidence rows is the false-green pattern.
        if rec["badge_green"] and nt and rec.get("p2_evidence_incomplete") == nt:
            disagree.append("green_badge_all_trials_missing_evidence")
    elif rec["badge"] and rec["verdict"] is None:
        disagree.append("badge_without_machine_verdict")
    rec["badge_disagreement"] = disagree

    # --- real data vs template ----------------------------------------------
    # NCT12345678 is the "Add Study Manually" form's input placeholder, present
    # in every clone. It is UI chrome, not a cited registry ID.
    ncts = set(RE_NCT.findall(s)) - {"NCT12345678"}
    rec["n_nct"] = len(ncts)
    rec["has_trials_array"] = bool(re.search(r"\bTRIALS\s*=\s*\[", s))
    if len(s) < 20_000:
        rec["data_state"] = "stub"
    elif rec["n_nct"] == 0 and not rec.get("n_trials_seen"):
        rec["data_state"] = "template"
    elif rec["n_nct"] == 0:
        rec["data_state"] = "no-registry-ids"
    else:
        rec["data_state"] = "injected"

    # --- residual contamination ---------------------------------------------
    contam = {}
    for key, pat in CONTAM.items():
        hits = pat.findall(s)
        if key == "finerenone":
            hits = [h for h in hits if True]
            n = len(hits) - len(FINERENONE_URL.findall(s))
            n = max(0, n)
        else:
            n = len(hits)
        if n:
            contam[key] = n
    rec["contamination"] = contam
    return rec


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--all-topics", action="store_true")
    ap.add_argument("--json", default=os.path.join(ROOT, "outputs", "gh_inventory.json"))
    args = ap.parse_args()

    files = sorted(glob.glob(os.path.join(ROOT, "*_REVIEW.html")))
    rows = []
    for p in files:
        try:
            rec = scan(p)
        except Exception as exc:  # noqa: BLE001 - inventory must not die on one file
            rows.append({"file": os.path.basename(p), "error": repr(exc)})
            continue
        if args.all_topics or rec.get("topic"):
            rows.append(rec)

    rows.sort(key=lambda r: (r.get("topic") or "~", r.get("file", "")))
    os.makedirs(os.path.dirname(args.json), exist_ok=True)
    with open(args.json, "w", encoding="utf-8") as fh:
        json.dump({"n_scanned": len(files), "n_in_scope": len(rows), "rows": rows},
                  fh, indent=1)

    print(f"scanned {len(files)} review apps; {len(rows)} in scope\n")
    hdr = f"{'topic':<20}{'file':<46}{'data':<11}{'trials':>7}{'badge':>7}{'verdict':<10} flags"
    print(hdr)
    print("-" * len(hdr))
    for r in rows:
        if "error" in r:
            print(f"{'ERROR':<20}{r['file']:<46}{r['error'][:60]}")
            continue
        flags = list(r["badge_disagreement"])
        if r["contamination"]:
            flags.append("CONTAM:" + ",".join(f"{k}={v}" for k, v in r["contamination"].items()))
        print(f"{(r['topic'] or '-'):<20}{r['file']:<46}{r['data_state']:<11}"
              f"{str(r.get('n_trials_seen') or '-'):>7}"
              f"{str(r.get('badge_trials') or '-'):>7}"
              f"{str(r.get('verdict') or '-'):<10} {'; '.join(flags)}")
    print(f"\nwrote {args.json}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
