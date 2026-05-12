"""Apply NCT-collision fixes.

Two operations:

A. NULL_WRONG_NCT — set nct=null on trials where the NCT belongs to a
   different disease entity than the review topic. Verified against AACT
   2026-04-12.

   - CAR_T_LBCL_BROAD_NMA_REVIEW : NCT02601313 (ZUMA-2 Mantle Cell Lymphoma,
     NOT Large B-Cell Lymphoma) → null nct.
   - CHECKPOINT_MELANOMA_1L_REVIEW : NCT02388906 (CheckMate-238 Adjuvant
     Melanoma, NOT 1L Metastatic) → null nct.

B. MARK_DUPLICATE_REVIEW — emit a manifest entry for human deletion. Two
   review name-variant pairs share trials byte-for-byte (different extracted
   values, same trial set):
   - MALARIA_VACCINE_REVIEW   vs MALARIA_VACCINES_REVIEW
   - JAKI_RA_NMA_REVIEW       vs JAK_RA_REVIEW

C. FLAG_DATA_DIVERGENCE — for 5 legitimate companion pairs where the same
   NCT appears in both reviews but extracted values diverge, write a human
   action list so a domain expert can reconcile against source papers.

Output:
  outputs/extraction_audit/nct_collision_fix_manifest.json
  outputs/extraction_audit/nct_collision_actions.csv

Modifies (idempotent):
  data/*REVIEW.js  — sets nct=null on 2 trials (Op A only)
"""
from __future__ import annotations
import csv, json, re, sys, os, io
from pathlib import Path

if hasattr(sys.stdout, "buffer") and getattr(sys.stdout, "encoding", "").lower() != "utf-8":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

HERE = Path(__file__).resolve().parent.parent
DATA_DIR = HERE / "data"

# A. WRONG-NCT attribution to null
# NB: CHECKPOINT_MELANOMA_1L_REVIEW's NCT02388906 was initially flagged but on
# inspection that review is a mixed metastatic+adjuvant 1L-therapy review (it
# also contains KEYNOTE-054 adjuvant), so CheckMate-238 is legitimately scoped.
# The only true mislabel is CAR_T_LBCL_BROAD_NMA naming NCT02601313 as "ZUMA-1"
# — ZUMA-1 is NCT02348216 (axi-cel in LBCL); NCT02601313 is ZUMA-2 (brexu in
# MCL), a different trial. Null and flag for re-extraction.
NULL_OPS = [
    {
        "review": "CAR_T_LBCL_BROAD_NMA_REVIEW",
        "nct": "NCT02601313",
        "reason": "Per AACT 2026-04-12 NCT02601313 is ZUMA-2 (Brexucabtagene Autoleucel "
                   "in R/R Mantle Cell Lymphoma), not ZUMA-1 (axi-cel in R/R LBCL = "
                   "NCT02348216). The review labelled this entry 'ZUMA-1' under the "
                   "wrong NCT; data may correspond to either trial. Nulling NCT to "
                   "force re-extraction.",
        "aact_title": "Study of Brexucabtagene Autoleucel (KTE-X19) in Participants With "
                       "Relapsed/Refractory Mantle Cell Lymphoma",
    },
]

# B. Duplicate-review pairs flagged for human deletion
DUP_REVIEW_PAIRS = [
    {
        "name_variant_a": "MALARIA_VACCINE_REVIEW",
        "name_variant_b": "MALARIA_VACCINES_REVIEW",
        "shared_ncts": ["NCT00866619", "NCT04704830"],
        "reason": "Singular/plural variant of the same review topic; shared trial set with "
                   "divergent extracted values. Recommend: keep one, delete the other (user "
                   "judgment — neither auto-deletable).",
    },
    {
        "name_variant_a": "JAKI_RA_NMA_REVIEW",
        "name_variant_b": "JAK_RA_REVIEW",
        "shared_ncts": ["NCT01710358", "NCT02629159", "NCT02889796"],
        "reason": "Acronym-variant of the same review topic (JAKi vs JAK); shared trial set "
                   "(baricitinib + upadacitinib + filgotinib RA trials) with divergent "
                   "extracted values. Recommend: keep one, delete the other.",
    },
]

# C. Legitimate companion-pair divergences (drug-specific + class NMA both legit)
DIVERGENT_PAIRS = [
    {
        "nct": "NCT03775200",
        "trial": "Psilocybin TRD (Carhart-Harris)",
        "review_a": "DEPRESSION_NEW_RAPID_REVIEW",
        "review_b": "DEPRESSION_PSYCHEDELIC_NMA_REVIEW",
        "issue": "Different extracted N: (14,14,8,13) vs (79,79,35,79) — one is wrong.",
    },
    {
        "nct": "NCT02418585",
        "trial": "Esketamine TRANSFORM-2",
        "review_a": "ESKETAMINE_TRD_REVIEW",
        "review_b": "DEPRESSION_NEW_RAPID_REVIEW",
        "issue": "ESKETAMINE_TRD has continuous (N=114,109); DEPRESSION_NEW_RAPID has binary "
                  "(36/115 vs 30/113). May be different outcomes — verify.",
    },
    {
        "nct": "NCT02668653",
        "trial": "QuANTUM-First (quizartinib AML + FLT3-ITD)",
        "review_a": "AML_VEN_FLT3_NMA_REVIEW",
        "review_b": "AML_TARGETED_NEW_REVIEW",
        "issue": "AML_TARGETED has (188/245, 89/122 HR 0.76); AML_VEN_FLT3_NMA has "
                  "(145/268, 169/271 HR 0.78). Different outcomes likely (OS vs EFS).",
    },
    {
        "nct": "NCT03860935",
        "trial": "ATTRibute-CM (acoramidis)",
        "review_a": "ACORAMIDIS_ATTR_CM_REVIEW",
        "review_b": "ATTR_CM_REVIEW",
        "issue": "ACORAMIDIS_ATTR_CM has (76/421, 62/211 HR 0.78); ATTR_CM has "
                  "(79/409, 52/202 HR 0.72). Close but not identical — extraction noise.",
    },
    {
        "nct": "NCT02388906",
        "trial": "CheckMate-238 (nivolumab vs ipilimumab adjuvant melanoma)",
        "review_a": "ADJUVANT_IO_MELANOMA_REVIEW",
        "review_b": "CHECKPOINT_MELANOMA_1L_REVIEW",
        "review_c": "ADJUVANT_IO_PAN_TUMOR_REVIEW",
        "issue": "Adjuvant melanoma trial legitimately in all three (1L-therapy review "
                  "is mixed metastatic+adjuvant). HR differs 0.65 vs 0.71 vs 0.71 — "
                  "likely OS vs RFS endpoint difference.",
    },
    {
        "nct": "NCT03410992",
        "trial": "BE READY (bimekizumab Ps PASI100)",
        "review_a": "BIMEKIZUMAB_PSORIASIS_REVIEW",
        "review_b": "IL_PSORIASIS_NMA_REVIEW",
        "issue": "BIMEKIZUMAB has (273/349, 1/86 OR 67.27); IL_PSORIASIS_NMA has "
                  "(318/349, 1/86 OR 871.9). Event counts diverge (273 vs 318) — one wrong.",
    },
]


def null_nct_in_review(review_stem: str, target_nct: str) -> tuple[bool, str]:
    """Idempotently rename `realData["NCT..."]` and `nctAcronyms["NCT..."]`
    keys to "NULLED:<NCT>" in the review HTML so cross-review aggregation
    no longer pairs them. Returns (changed, message).

    The review data lives inline in <REVIEW>.html (not a separate data/*.js
    file). We rename the key rather than delete the object: this preserves
    the local row but breaks the cross-review NCT identity match.
    """
    html_path = HERE / f"{review_stem}.html"
    if not html_path.exists():
        return False, f"HTML file not found: {html_path.name}"
    txt = html_path.read_text(encoding="utf-8")
    # Rename in realData and nctAcronyms
    nulled_marker = f"NULLED:{target_nct}"
    if nulled_marker in txt:
        return False, f"{html_path.name}: {target_nct} already nulled (marker present)"
    # Replace any "<NCT>" or '<NCT>' that appears as a quoted JS object key
    pat = re.compile(
        r'(["\'])(' + re.escape(target_nct) + r')(\1)(\s*:)',
        re.IGNORECASE
    )
    new_txt, n = pat.subn(lambda m: f'{m.group(1)}NULLED:{m.group(2)}{m.group(3)}{m.group(4)}', txt)
    if n == 0:
        return False, f"{html_path.name}: no quoted-key occurrence of {target_nct} found"
    html_path.write_text(new_txt, encoding="utf-8")
    return True, f"{html_path.name}: renamed {n} key(s) {target_nct} → NULLED:{target_nct}"


# Execute Op A: null wrong-NCTs
print("=" * 70)
print("Op A — NULL_WRONG_NCT (auto-fix)")
print("=" * 70)
ops_log = []
for op in NULL_OPS:
    changed, msg = null_nct_in_review(op["review"], op["nct"])
    print(f"  {'✓' if changed else '○'} {msg}")
    ops_log.append({**op, "changed": changed, "message": msg})

# Op B + C: write the manifest only
print()
print("=" * 70)
print("Op B — DUPLICATE_REVIEW_PAIRS (user judgment required)")
print("=" * 70)
for d in DUP_REVIEW_PAIRS:
    print(f"  ⚠ {d['name_variant_a']} <=> {d['name_variant_b']}")
    print(f"     shared NCTs: {d['shared_ncts']}")
    print(f"     {d['reason'][:100]}")

print()
print("=" * 70)
print("Op C — LEGITIMATE_DIVERGENT_VALUES (human source-paper verification)")
print("=" * 70)
for d in DIVERGENT_PAIRS:
    print(f"  ⚠ {d['nct']} ({d['trial']})")
    print(f"     {d['review_a']} vs {d['review_b']}")
    print(f"     {d['issue']}")

# Write manifest
manifest = {
    "fix_applied": ops_log,
    "duplicate_review_pairs": DUP_REVIEW_PAIRS,
    "divergent_value_pairs": DIVERGENT_PAIRS,
}
out_path = HERE / "outputs" / "extraction_audit" / "nct_collision_fix_manifest.json"
out_path.parent.mkdir(parents=True, exist_ok=True)
with open(out_path, "w", encoding="utf-8") as f:
    json.dump(manifest, f, indent=2)
print(f"\nManifest → {out_path}")

# Write actions CSV
csv_path = HERE / "outputs" / "extraction_audit" / "nct_collision_actions.csv"
with open(csv_path, "w", encoding="utf-8", newline="") as f:
    w = csv.writer(f)
    w.writerow(["op", "nct", "review_or_pair", "action", "auto", "rationale"])
    for o in ops_log:
        w.writerow(["A", o["nct"], o["review"],
                    "nct nulled" if o["changed"] else "manual-check",
                    o["changed"], o["reason"]])
    for d in DUP_REVIEW_PAIRS:
        for nct in d["shared_ncts"]:
            w.writerow(["B", nct, f"{d['name_variant_a']} | {d['name_variant_b']}",
                        "delete one of the duplicate reviews", False, d["reason"]])
    for d in DIVERGENT_PAIRS:
        w.writerow(["C", d["nct"], f"{d['review_a']} | {d['review_b']}",
                    "verify against source paper", False, d["issue"]])
print(f"Actions CSV → {csv_path}")

n_auto = sum(1 for o in ops_log if o["changed"])
print(f"\nAUTO-FIXED: {n_auto} NCT-nulled")
print(f"USER-ACTION: {len(DUP_REVIEW_PAIRS) * 2} duplicate-review-pair members + "
      f"{len(DIVERGENT_PAIRS)} divergent-value pairs")
