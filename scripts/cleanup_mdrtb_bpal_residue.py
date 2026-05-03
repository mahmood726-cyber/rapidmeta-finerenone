"""Phase-2 cleanup of SGLT2/HF residue in MDRTB_BPAL_REVIEW.html.

Surgical replacements for the high-impact user-visible strings only.
Deeper scaffold residue (CSS class names containing 'sglt2-', deep-JS
internal labels, tooltip overlays) is left as-is — those don't surface
in the end-user UI of the BPaL app and would require deeper template
re-engineering to remove cleanly.
"""
from __future__ import annotations
import re
import sys
from pathlib import Path

FILE = Path("MDRTB_BPAL_REVIEW.html")

# Each entry: (description, old, new). Order matters (longer first to avoid
# substring collision).
REPLACEMENTS = [
    # ---- 1. App header badge ----
    ("Header v1.0 badge", 'SGLT2-HF v1.0', 'BPaL/BPaLM v0.1'),

    # ---- 2. Review title ----
    ("Review title row",
     'SGLT2 Inhibitors for Heart Failure Outcomes: A Living Systematic Review and Meta-Analysis of Randomized Controlled Trials',
     'Bedaquiline-Pretomanid-Linezolid (BPaL) and BPaL+Moxifloxacin (BPaLM) for Multidrug-Resistant Pulmonary Tuberculosis: A Pairwise Systematic Review and Meta-Analysis'),

    # ---- 3. molMap dictionary ----
    ("Trial-to-molecule dictionary",
     "{ 'DAPA-HF': 'Dapagliflozin', 'DELIVER': 'Dapagliflozin', 'EMPEROR-Reduced': 'Empagliflozin', 'EMPEROR-Preserved': 'Empagliflozin', 'SOLOIST-WHF': 'Sotagliflozin' }",
     "{ 'Nix-TB': 'BPaL', 'ZeNix': 'BPaL (LZD-dose comparison)', 'TB-PRACTECAL': 'BPaLM' }"),

    # ---- 4. Population placeholder ----
    ("Population placeholder", 'value="Adults with heart failure"',
     'value="Adults with multidrug-resistant or pre-XDR/XDR pulmonary tuberculosis"'),

    # ---- 5. PubMed query examples (2 occurrences) ----
    ("PubMed query example 1",
     '(dapagliflozin OR empagliflozin OR sotagliflozin OR "sglt2") AND "heart failure" AND (TITLE:randomized OR PUB_TYPE:"Randomized Controlled Trial")',
     '(bedaquiline AND pretomanid AND linezolid) AND ("multidrug-resistant" OR "MDR" OR "XDR") AND tuberculosis AND (TITLE:randomized OR PUB_TYPE:"Randomized Controlled Trial")'),

    # ---- 6. Subgroup analysis row ----
    ("Subgroup HFrEF vs HFpEF",
     'By HF phenotype (HFrEF vs HFpEF/HFmrEF); Q-between test for interaction',
     'By baseline drug-resistance pattern (MDR vs pre-XDR vs XDR); HIV co-infection; Q-between test for interaction'),

    # ---- 7. Subgroup dropdown option ----
    ("Subgroup dropdown EF Phenotype",
     '<option value="group">EF Phenotype (HFrEF vs HFpEF)</option>',
     '<option value="group">Resistance pattern (MDR vs pre-XDR vs XDR)</option>'),

    # ---- 8. Indication dropdown ----
    ("Indication dropdown HF option",
     '<option value="Heart Failure">Heart Failure</option>',
     '<option value="MDR-TB">MDR-TB</option>'),

    # ---- 9. CT.gov search URL example ----
    ("CT.gov example URL query.term",
     'query.term=heart%20failure%20sglt2',
     'query.term=multidrug-resistant%20tuberculosis%20bedaquiline'),

    # ---- 10. Protocol .md link path (file does not exist either way; just label) ----
    ("Protocol filename reference",
     'protocols/sglt2_hf_protocol_v1.0_2026-04-19.md',
     'protocols/bpal_mdrtb_protocol_v0.1_2026-05-03.md'),
]


def main() -> int:
    if not FILE.exists():
        print(f"ERROR: {FILE} not found", file=sys.stderr)
        return 1
    text = FILE.read_text(encoding="utf-8")
    original_size = len(text)

    applied = []
    skipped = []
    for desc, old, new in REPLACEMENTS:
        count = text.count(old)
        if count == 0:
            skipped.append(f"{desc}: no match")
            continue
        text = text.replace(old, new)
        applied.append(f"{desc}: {count} occurrence(s) replaced")

    FILE.write_text(text, encoding="utf-8")
    print(f"Applied {len(applied)} replacement groups, skipped {len(skipped)}")
    for a in applied:
        print(f"  + {a}")
    for s in skipped:
        print(f"  - {s}")

    new_size = len(text)
    print(f"Size delta: {new_size - original_size:+d} bytes")

    # Recount residue
    residual = {
        "SGLT2": text.count("SGLT2"),
        "sglt2": text.count("sglt2"),
        "dapagliflozin": text.count("dapagliflozin") + text.count("Dapagliflozin"),
        "empagliflozin": text.count("empagliflozin") + text.count("Empagliflozin"),
        "heart failure": text.count("heart failure") + text.count("Heart Failure"),
    }
    print("\nResidual counts (lower = better; deep-scaffold residue is unavoidable in non-UI code):")
    for k, v in residual.items():
        print(f"  {k}: {v}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
