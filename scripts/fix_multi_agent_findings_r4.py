"""R4 fixes — apply the PubMed-anchored findings from the 16-review audit.

Three batches:
  B1 — Quarantine 3 newly-confirmed fabricated reviews
  B2 — Null wrong PMIDs with ground truth recorded for future re-extract
  B3 — Null wrong NCTs (with ground truth recorded)
"""
from __future__ import annotations
import json, re, sys, io
from pathlib import Path

if hasattr(sys.stdout, "buffer") and getattr(sys.stdout, "encoding", "").lower() != "utf-8":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

HERE = Path(__file__).resolve().parent.parent
DRY = "--dry-run" in sys.argv

# ───── B1: quarantine 3 reviews ─────
QUARANTINE_R4 = [
    ("OPIOID_INDUCED_CONSTIPATION_REVIEW",
     "R4: KODIAC-08 likely fabricated + KODIAC-04/05 PMID 24716689 unrelated + COMPOSE-3 PMID 30086124 unrelated + 2 generic names"),
    ("HEP_D_BULEVIRTIDE_NMA_REVIEW",
     "R4: 3/6 trials have NCT mismatches (MYR-204 wrong NCT, LIMT-2 wrong NCT, BLV-RW-EU likely fabricated)"),
    ("AD_PEDIATRIC_BIOLOGIC_NMA_REVIEW",
     "R4: VOYAGE-AD + Measure-UP-PED both look fabricated; 2/5 trials bad"),
]

BANNER_HTML = """
<div id="rapidmeta-quarantine-banner" role="alert" style="background:#7f1d1d;color:#fff;padding:12px 20px;font-family:system-ui,sans-serif;font-size:14px;border-bottom:3px solid #fbbf24;text-align:center;">
  ⚠ DATA-INTEGRITY QUARANTINE — Multi-agent audit (R4 PubMed-anchored) found multiple trials with fabricated/unresolvable NCTs or PMIDs. Pooled estimates on this page should NOT be cited or shipped until ground-up re-extraction is completed.
</div>
"""
QUARANTINE_MARKER = "rapidmeta-quarantine-banner"

# ───── B2: PMID nullings with ground-truth (recorded for re-extract) ─────
# Format: (review, nct, bad_pmid, true_pmid_or_None, reason)
PMID_NULLS = [
    ("BLADDER_NMIBC_NEW_NMA_REVIEW", None, "33301744", "34233186", "VISTA NCT wrong/PMID unrelated per R4"),
    ("DEPRESSION_NEW_RAPID_REVIEW", None, "31948863", "32264597", "TRANSFORM-3 PMID unrelated"),
    ("CAR_T_LBCL_BROAD_NMA_REVIEW", None, "30523697", "30501490", "JULIET PMID off-by-one"),
    ("MIS_GASTRECTOMY_NMA_REVIEW", None, "31135415", "30932736", "KLASS-02 PMID unrelated"),
    ("IBD_BIOLOGICS_REVIEW", None, "35671785", "35644145", "FORTIFY PMID off"),
    ("OPIOID_INDUCED_CONSTIPATION_REVIEW", None, "24716689", "24896818", "KODIAC-04/05 PMID unrelated"),
    ("OPIOID_INDUCED_CONSTIPATION_REVIEW", None, "30086124", "28427293", "COMPOSE-3 PMID unrelated"),
    ("GnRH_ANTAGONISTS_GYN_REVIEW", None, "32074416", "31995689", "Elaris UF-1/UF-2 PMID off"),
    ("PERIPHERAL_DCB_PAD_NMA_REVIEW", None, "32145772", None, "PASSEO-LUX PMID is COVID editorial"),
]

# ───── B3: NCT renames (point to NULLED prefix for re-extract) ─────
NCT_NULLS = [
    ("MM_BISPECIFIC_BROAD_NMA_REVIEW", "TRIMM-2", "NCT04108195",
     "R4: NCT correction per PubMed verification"),
    ("MM_BISPECIFIC_BROAD_NMA_REVIEW", "RedirecTT-1", "NCT04586426",
     "R4: NCT correction per PubMed verification"),
    ("GASTRIC_FRONTLINE_IO_NMA_REVIEW", "KEYNOTE-585", "NCT03221426",
     "R4: NCT correction per PubMed verification"),
    ("MIS_GASTRECTOMY_NMA_REVIEW", "LOGICA", "NCT02248519",
     "R4: NCT correction per PubMed verification"),
    ("MIS_GASTRECTOMY_NMA_REVIEW", "FUGES-001", "NCT03524365",
     "R4: NCT correction per PubMed verification"),
    ("ENDOMETRIOSIS_NEW_GNRH_NMA_REVIEW", "PRIMROSE-1", "NCT03070899",
     "R4: NCT correction per PubMed verification"),
    ("ENDOMETRIOSIS_NEW_GNRH_NMA_REVIEW", "PRIMROSE-2", "NCT03070951",
     "R4: NCT correction per PubMed verification"),
    ("GnRH_ANTAGONISTS_GYN_REVIEW", "Elaris EM-1", "NCT01620528",
     "R4: NCT correction per PubMed verification"),
]


# Helpers
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


def null_key(txt, nct):
    nulled = f"NULLED:{nct}"
    if nulled in txt: return txt, 0
    pat = re.compile(r'(["\'])(' + re.escape(nct) + r')(\1)(\s*:)')
    new_txt, n = pat.subn(
        lambda m: f'{m.group(1)}NULLED:{m.group(2)}{m.group(3)}{m.group(4)}', txt)
    return new_txt, n


def find_block_by_name(txt, name_pattern):
    """Locate realData block by matching the 'name' field."""
    # First find all NCT-keyed blocks, then pick the one with matching name
    nct_pat = re.compile(r'(["\'])(NCT\d{8})\1\s*:\s*\{')
    for m in nct_pat.finditer(txt):
        nct = m.group(2)
        block = find_block(txt, nct)
        if not block: continue
        _, _, bs, be = block
        body = txt[bs:be]
        if re.search(r'(["\']?)name\1\s*:\s*["\']' + re.escape(name_pattern) + r'["\']',
                     body, re.IGNORECASE):
            return nct, block
    return None, None


log = {"batch1": [], "batch2": [], "batch3": []}

# B1: Quarantine
print("Batch 1 — Quarantine 3 newly-confirmed fabricated reviews")
for rv, reason in QUARANTINE_R4:
    html_path = HERE / f"{rv}.html"
    if not html_path.exists():
        log["batch1"].append({"review": rv, "status": "FILE_MISSING"})
        continue
    txt = html_path.read_text(encoding="utf-8")
    if QUARANTINE_MARKER in txt:
        log["batch1"].append({"review": rv, "status": "ALREADY_QUARANTINED"})
        continue
    body_pat = re.compile(r"(<body[^>]*>)", re.IGNORECASE)
    new_txt, n = body_pat.subn(lambda m: m.group(1) + "\n" + BANNER_HTML, txt, count=1)
    if n == 0:
        log["batch1"].append({"review": rv, "status": "BODY_TAG_NOT_FOUND"})
        continue
    if not DRY: html_path.write_text(new_txt, encoding="utf-8")
    log["batch1"].append({"review": rv, "status": "QUARANTINED", "reason": reason})

# B2: PMID nullings — locate block by PMID value if NCT not provided
print("\nBatch 2 — PMID nullings with ground-truth recorded")
for rv, nct, bad_pmid, true_pmid, reason in PMID_NULLS:
    html_path = HERE / f"{rv}.html"
    if not html_path.exists():
        log["batch2"].append({"review": rv, "pmid": bad_pmid, "status": "FILE_MISSING"})
        continue
    txt = html_path.read_text(encoding="utf-8")
    # Find any trial whose pmid matches bad_pmid
    pmid_pat = re.compile(r'(["\']?)pmid\1\s*:\s*["\']' + re.escape(bad_pmid) + r'["\']', re.IGNORECASE)
    matches = list(pmid_pat.finditer(txt))
    if not matches:
        log["batch2"].append({"review": rv, "pmid": bad_pmid, "status": "PMID_NOT_FOUND_OR_ALREADY_NULL"})
        continue
    n_replaced = 0
    new_txt = txt
    for m in pmid_pat.finditer(new_txt):
        new_txt = (new_txt[:m.start()] + 'pmid: null' + new_txt[m.end():])
        n_replaced += 1
    if n_replaced > 0:
        if not DRY: html_path.write_text(new_txt, encoding="utf-8")
        log["batch2"].append({"review": rv, "pmid": bad_pmid, "true_pmid_hint": true_pmid,
                                "status": "NULLED_PMID", "count": n_replaced, "reason": reason})
    else:
        log["batch2"].append({"review": rv, "pmid": bad_pmid, "status": "NO_REPLACEMENT"})

# B3: NCT key nulling by name
print("\nBatch 3 — NCT renames (by trial name match) with ground-truth recorded")
for rv, name, true_nct, reason in NCT_NULLS:
    html_path = HERE / f"{rv}.html"
    if not html_path.exists():
        log["batch3"].append({"review": rv, "name": name, "status": "FILE_MISSING"})
        continue
    txt = html_path.read_text(encoding="utf-8")
    found_nct, block = find_block_by_name(txt, name)
    if not found_nct:
        log["batch3"].append({"review": rv, "name": name, "status": "NAME_NOT_FOUND"})
        continue
    if found_nct == true_nct:
        log["batch3"].append({"review": rv, "name": name, "found_nct": found_nct,
                                "status": "ALREADY_CORRECT_NCT"})
        continue
    new_txt, n = null_key(txt, found_nct)
    if n > 0:
        if not DRY: html_path.write_text(new_txt, encoding="utf-8")
        log["batch3"].append({"review": rv, "name": name, "old_nct": found_nct,
                                "true_nct_hint": true_nct, "status": "NULLED_KEY",
                                "reason": reason})
    else:
        log["batch3"].append({"review": rv, "name": name, "status": "NULL_FAILED"})

# Counts
n_b1 = sum(1 for r in log["batch1"] if r["status"] == "QUARANTINED")
n_b2 = sum(1 for r in log["batch2"] if r["status"] == "NULLED_PMID")
n_b3 = sum(1 for r in log["batch3"] if r["status"] == "NULLED_KEY")

out_p = HERE / "outputs" / "extraction_audit" / "multi_agent_fixes_applied_r4.json"
out_p.write_text(json.dumps(log, indent=2, ensure_ascii=False), encoding="utf-8")
print(f"\n{'DRY-RUN ' if DRY else ''}Total R4: B1={n_b1} quarantines + B2={n_b2} PMID nulls + B3={n_b3} NCT nulls")
print(f"Log → {out_p}")
