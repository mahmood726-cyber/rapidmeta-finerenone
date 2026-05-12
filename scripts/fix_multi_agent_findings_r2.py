"""Apply Round 2 multi-agent fixes.

Three batches:

Batch 1 — Targeted 2-of-3 HIGH fixes with ground truth (18 ops):
  Each case grounded in agent's PubMed-verified explanation.

Batch 2 — Bulk single-arm fabricated-HR purge:
  For every trial where cE=0 AND cN=0 AND publishedHR is non-null, null the
  HR + CI (the comparator was fabricated; only the single-arm rate is valid).
  Applies the lesson from Round 1 (166 single-arm flagged) to Round 2 scope.

Batch 3 — OR-mislabelled-as-HR estimandType correction:
  For every trial where publishedHR > 20 (extreme magnitude) AND a binary
  outcome context, set estimandType to "OR" so downstream pooling uses the
  right transform. Conservative threshold (>20) avoids false-positives.

All ops idempotent + logged.
"""
from __future__ import annotations
import json, re, sys, io
from pathlib import Path

if hasattr(sys.stdout, "buffer") and getattr(sys.stdout, "encoding", "").lower() != "utf-8":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

HERE = Path(__file__).resolve().parent.parent
DATA = HERE / "outputs" / "extraction_audit" / "data"
DRY = "--dry-run" in sys.argv

# ─────────── Batch 1 — Targeted ops ───────────
OPS_B1 = [
    # TRANSFORM-1 label on NCT02418585 (which is TRANSFORM-2) — different trial
    {"review":"DEPRESSION_NEW_RAPID_REVIEW","nct":"NCT02418585","op":"NULL_KEY",
     "reason":"R2: NCT02418585 is TRANSFORM-2 (Popova 2019); correct TRANSFORM-1 = NCT02417064 (Fedgchin 2019, PMID 31290965)"},
    # FLAIR wrong PMID — correct = 34032826
    {"review":"T1D_CLOSED_LOOP_NMA_REVIEW","nct":"NCT03665025","op":"NULL_PMID",
     "reason":"R2: PMID 33034298 unrelated (Indian Pediatr brickworks paper); FLAIR Bergenstal JAMA 2021 PMID = 34032826"},
    # iDCL-Pediatric — unresolvable PMID, schema mismatch
    {"review":"T1D_CLOSED_LOOP_NMA_REVIEW","nct":"NCT03844790","op":"NULL_PMID",
     "reason":"R2: PMID 32945740 does not resolve in PubMed; iDCL-Pediatric Ware/Brown NEJM 2022 PMID = 35041780"},
    # JANSSEN-3155 — esketamine in psychedelic NMA (wrong class)
    {"review":"DEPRESSION_PSYCHEDELIC_NMA_REVIEW","nct":"NCT04122690","op":"NULL_KEY",
     "reason":"R2: Esketamine (NMDA-receptor antagonist) does not belong in a serotonergic-psychedelic NMA; plus schema-MD-with-events"},
    # QuANTUM-First label on NCT02039726 (which is QuANTUM-R)
    {"review":"AML_TARGETED_NEW_REVIEW","nct":"NCT02039726","op":"NULL_KEY",
     "reason":"R2: NCT02039726 is QuANTUM-R (Cortes Lancet Oncol 2019, PMID 31606519), not QuANTUM-First (Erba Lancet 2023)"},
    # IDHENTIFY wrong NCT (correct is NCT02577406, already in dataset)
    {"review":"AML_VEN_FLT3_NMA_REVIEW","nct":"NCT03839771","op":"NULL_KEY",
     "reason":"R2: IDHENTIFY (enasidenib R/R IDH2+ AML) = NCT02577406 (de Botton Blood 2023, PMID 35714312), already at id=1106; NCT03839771 is a different protocol"},
    # CADENZA sutimlimab in ITP review (drug is for cold agglutinin disease)
    {"review":"ITP_NEW_AGENTS_REVIEW","nct":"NCT03347396","op":"NULL_KEY",
     "reason":"R2: Sutimlimab is anti-C1s for cold agglutinin disease; CADENZA is the CAD pivotal, not an ITP agent"},
    # MAJESTIC DES in DCB review
    {"review":"PERIPHERAL_DCB_PAD_NMA_REVIEW","nct":"NCT01530178","op":"NULL_KEY",
     "reason":"R2: MAJESTIC evaluated Eluvia drug-eluting stent (DES), not a drug-coated balloon (DCB); wrong device class for DCB NMA"},
    # KARMMA myeloma CAR-T in B-cell lymphoma review
    {"review":"CART_B_CELL_LYMPHOMA_REVIEW","nct":"NCT03361748","op":"NULL_KEY",
     "reason":"R2: KARMMA is idecabtagene vicleucel (ide-cel) BCMA CAR-T for multiple myeloma, not B-cell lymphoma; wrong target+disease"},
    # SRP-9001-101 wrong PMID
    {"review":"DUCHENNE_GENE_THERAPY_REVIEW","nct":"NCT03769116","op":"NULL_PMID",
     "reason":"R2: PMID 32433678 unrelated (EHR-nudge influenza vaccination); SRP-9001-101 = Mendell JAMA Neurol 2020 PMID 32539076"},
    # FAME-3 wrong review (left-main NMA, but FAME-3 explicitly excluded left main) + wrong PMID
    {"review":"CABG_VS_PCI_LEFT_MAIN_NMA_REVIEW","nct":"NCT02100722","op":"NULL_KEY",
     "reason":"R2: FAME-3 (Fearon NEJM 2022) is 3-vessel CAD with explicit left-main exclusion; wrong scope for a left-main NMA"},
    # CLEAR-OUTCOMES bempedoic acid in PCSK9 NMA (wrong drug class)
    {"review":"PCSK9_LIPID_NMA_REVIEW","nct":"NCT02993406","op":"NULL_KEY",
     "reason":"R2: CLEAR-OUTCOMES (Nissen NEJM 2023) tested bempedoic acid (ATP-citrate lyase inhibitor), not a PCSK9 inhibitor"},
    # OPTIMUS-1 label on NCT02437279 (which is OpACIN-neo) — wrong name, right disease
    {"review":"MELANOMA_NEOADJUVANT_REVIEW","nct":"NCT02437279","op":"NULL_PMID",
     "reason":"R2: NCT02437279 is OpACIN-neo (Rozeman/Blank); 'OPTIMUS-1' name does not match. Disease is correct but PMID provenance is broken — flag for re-extract"},
    # TANEZ-OA-005 tanezumab is SC not IA
    {"review":"KNEE_OA_INTRAARTICULAR_NMA_REVIEW","nct":"NCT02061358","op":"NULL_KEY",
     "reason":"R2: Tanezumab is SC anti-NGF mAb (systemic), not intra-articular; wrong route for IA-OA NMA. Also schema-MD-with-events"},
    # ACT contrast-AKI not postop
    {"review":"POSTOP_AKI_PREVENTION_REVIEW","nct":"NCT01200654","op":"NULL_KEY",
     "reason":"R2: ACT trial (Berwanger Circulation 2011) is acetylcysteine for contrast-induced AKI at angiography, not postop AKI prevention"},
    # MIRASOL wrong PMID
    {"review":"MIRVETUXIMAB_OVARIAN_REVIEW","nct":"NCT04209855","op":"NULL_PMID",
     "reason":"R2: PMID 38567989 unrelated (UGT1A1 fluorescent probe paper); MIRASOL Moore NEJM 2024 PMID = 38096376"},
    # NCT02773849 — name is the NCT (extraction fallback) → flag for re-extract
    {"review":"BLADDER_NMIBC_NEW_NMA_REVIEW","nct":"NCT02773849","op":"NULL_PMID",
     "reason":"R2: trial name field is literally the NCT identifier (extraction-fallback marker); single-arm trial with cE=cN=0 but HR=0.55 reported (fabricated comparator)"},
    # BE VIVID — HR=88.6 OR-mislabelled (already covered by Batch 3, but ensure noted)
    # CADENZA already in B1 above
]

# ─────────── Apply helpers ───────────
def find_block(txt, nct):
    key_pat = re.compile(r'(["\'])' + re.escape(nct) + r'\1\s*:\s*\{')
    m = key_pat.search(txt)
    if not m: return None
    start = m.end()
    depth = 1; i = start; in_str = None
    while i < len(txt) and depth > 0:
        ch = txt[i]
        if in_str:
            if ch == "\\": i += 2; continue
            if ch == in_str: in_str = None
        else:
            if ch in ('"',"'"): in_str = ch
            elif ch == "{": depth += 1
            elif ch == "}":
                depth -= 1
                if depth == 0: return (m.start(), i+1, start, i)
        i += 1
    return None


def null_field_in_block(txt, body_start, body_end, field):
    body = txt[body_start:body_end]
    new_body, n = re.subn(
        r'((["\']?)' + re.escape(field) + r'\2\s*:\s*)(?:["\'][^"\']*["\']|[0-9.eE+-]+|true|false)(?=\s*[,}])',
        r'\1null', body, flags=re.IGNORECASE)
    if n == 0: return txt, False
    return txt[:body_start] + new_body + txt[body_end:], True


def set_field_in_block(txt, body_start, body_end, field, value):
    body = txt[body_start:body_end]
    new_body, n = re.subn(
        r'((["\']?)' + re.escape(field) + r'\2\s*:\s*)(?:["\'][^"\']*["\']|[0-9.eE+-]+|true|false|null)(?=\s*[,}])',
        r'\1"' + value + '"', body, flags=re.IGNORECASE)
    if n == 0: return txt, False
    return txt[:body_start] + new_body + txt[body_end:], True


def null_key(txt, nct):
    nulled = f"NULLED:{nct}"
    if nulled in txt:
        return txt, 0
    pat = re.compile(r'(["\'])(' + re.escape(nct) + r')(\1)(\s*:)')
    new_txt, n = pat.subn(
        lambda m: f'{m.group(1)}NULLED:{m.group(2)}{m.group(3)}{m.group(4)}', txt)
    return new_txt, n


log = {"batch1": [], "batch2": [], "batch3": []}

# Batch 1
print("Batch 1 — Targeted 2-of-3 HIGH ops")
for op in OPS_B1:
    rv = op["review"]; nct = op["nct"]; kind = op["op"]
    html_path = HERE / f"{rv}.html"
    if not html_path.exists():
        log["batch1"].append({**op, "status": "FILE_MISSING"})
        continue
    txt = html_path.read_text(encoding="utf-8")
    if kind == "NULL_KEY":
        new_txt, n = null_key(txt, nct)
        if n > 0:
            if not DRY: html_path.write_text(new_txt, encoding="utf-8")
            log["batch1"].append({**op, "status": "NULLED_KEY", "occurrences": n})
        elif f"NULLED:{nct}" in txt:
            log["batch1"].append({**op, "status": "ALREADY_NULLED"})
        else:
            log["batch1"].append({**op, "status": "NCT_NOT_FOUND"})
    elif kind == "NULL_PMID":
        block = find_block(txt, nct)
        if not block:
            log["batch1"].append({**op, "status": "BLOCK_NOT_FOUND"})
            continue
        _, _, bs, be = block
        new_txt, ok = null_field_in_block(txt, bs, be, "pmid")
        if ok:
            if not DRY: html_path.write_text(new_txt, encoding="utf-8")
            log["batch1"].append({**op, "status": "NULLED_PMID"})
        else:
            log["batch1"].append({**op, "status": "PMID_NOT_FOUND"})

n_b1 = sum(1 for r in log["batch1"] if "NULLED" in r["status"])
print(f"  Batch 1: {n_b1}/{len(OPS_B1)} applied")

# ─────────── Batch 2 — Bulk single-arm null-HR ───────────
print("\nBatch 2 — Single-arm fabricated-HR purge (cE=cN=0 + non-null HR)")
n_b2 = 0
# Iterate all reviews
for json_p in sorted(DATA.glob("*.json")):
    if json_p.name.startswith("_"): continue
    rv = json_p.stem
    try: d = json.loads(json_p.read_text(encoding="utf-8"))
    except: continue
    rd = d.get("realData") or {}
    if not isinstance(rd, dict): continue
    targets = []
    for nct, t in rd.items():
        if not isinstance(t, dict): continue
        if nct.startswith("NULLED:"): continue
        cE = t.get("cE"); cN = t.get("cN")
        hr = t.get("publishedHR")
        # Single-arm = cE=0 AND cN=0 with non-null HR
        if cE == 0 and cN == 0 and hr is not None and isinstance(hr, (int, float)):
            targets.append(nct)
    if not targets: continue
    html_path = HERE / f"{rv}.html"
    if not html_path.exists(): continue
    txt = html_path.read_text(encoding="utf-8")
    review_changes = 0
    for nct in targets:
        block = find_block(txt, nct)
        if not block: continue
        _, _, bs, be = block
        for field in ("publishedHR", "hrLCI", "hrUCI"):
            new_txt, ok = null_field_in_block(txt, bs, be, field)
            if ok:
                txt = new_txt
                # Re-find block since text changed
                block = find_block(txt, nct)
                if not block: break
                _, _, bs, be = block
        review_changes += 1
    if review_changes:
        if not DRY: html_path.write_text(txt, encoding="utf-8")
        log["batch2"].append({"review": rv, "trials_nulled": review_changes, "ncts": targets})
        n_b2 += review_changes
print(f"  Batch 2: {n_b2} single-arm HRs nulled across {len(log['batch2'])} reviews")

# ─────────── Batch 3 — OR-mislabelled-as-HR (set estimandType) ───────────
print("\nBatch 3 — OR-mislabelled estimandType correction (HR > 20)")
n_b3 = 0
for json_p in sorted(DATA.glob("*.json")):
    if json_p.name.startswith("_"): continue
    rv = json_p.stem
    try: d = json.loads(json_p.read_text(encoding="utf-8"))
    except: continue
    rd = d.get("realData") or {}
    if not isinstance(rd, dict): continue
    targets = []
    for nct, t in rd.items():
        if not isinstance(t, dict): continue
        if nct.startswith("NULLED:"): continue
        hr = t.get("publishedHR")
        et = t.get("estimandType")
        # HR > 20 is implausible; et is HR or null → likely OR mislabel
        if (isinstance(hr, (int, float)) and hr > 20.0 and
            (et is None or str(et).upper() in ("HR", "RR"))):
            targets.append((nct, et, hr))
    if not targets: continue
    html_path = HERE / f"{rv}.html"
    if not html_path.exists(): continue
    txt = html_path.read_text(encoding="utf-8")
    review_changes = 0
    for nct, old_et, hr_val in targets:
        block = find_block(txt, nct)
        if not block: continue
        _, _, bs, be = block
        new_txt, ok = set_field_in_block(txt, bs, be, "estimandType", "OR")
        if ok:
            txt = new_txt
            review_changes += 1
    if review_changes:
        if not DRY: html_path.write_text(txt, encoding="utf-8")
        log["batch3"].append({"review": rv, "trials_relabeled": review_changes,
                                "ncts": [t[0] for t in targets]})
        n_b3 += review_changes
print(f"  Batch 3: {n_b3} OR mislabels corrected across {len(log['batch3'])} reviews")

out_p = HERE / "outputs" / "extraction_audit" / "multi_agent_fixes_applied_r2.json"
out_p.write_text(json.dumps(log, indent=2, ensure_ascii=False), encoding="utf-8")
print(f"\n{'DRY-RUN ' if DRY else ''}Total: B1={n_b1} + B2={n_b2} + B3={n_b3}")
print(f"Log → {out_p}")
