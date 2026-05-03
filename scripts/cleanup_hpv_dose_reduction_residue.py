"""Phase-2 residue cleanup for HPV_DOSE_REDUCTION_NMA_REVIEW.html.

Surgical replacement of high-impact user-visible KRAS/NSCLC strings
inherited from the KRAS_G12C_NMA template clone.
"""
from __future__ import annotations
import sys
from pathlib import Path

FILE = Path("HPV_DOSE_REDUCTION_NMA_REVIEW.html")

REPLACEMENTS = [
    # Header badge
    ("App badge", 'KRAS NMA v1.0', 'HPV NMA v0.1'),
    ("App badge variant", 'KRAS-G12C NMA v1.0', 'HPV NMA v0.1'),

    # Section headers
    ("Section 1 title row",
     "KRAS-G12C Inhibitors (Sotorasib, Adagrasib) Versus Docetaxel in Pretreated KRAS-G12C-Mutated Advanced NSCLC: A Network Meta-Analysis",
     "Single-Dose vs Multi-Dose HPV Vaccination in Sub-Saharan African Adolescents and Young Adults: A Pairwise + NMA Methods Note"),

    ("KRAS-G12C Inhibitors header simple", 'KRAS-G12C Inhibitors', 'HPV Vaccination'),

    # Population placeholder
    ("Population placeholder",
     'value="Treatment-naive advanced clear-cell KRAS-G12C+ NSCLC (any IMDC risk)"',
     'value="HIV-negative females aged 9-20 years in sub-Saharan Africa with no history of HPV vaccination"'),

    # Comparator placeholder
    ("Comparator placeholder",
     'value="Docetaxel monotherapy (active reference)"',
     'value="Delayed-vaccination control (KEN-SHE) or 3-dose schedule (DoRIS immunobridging)"'),

    # Participants row
    ("Participants row",
     'Advanced NSCLC 1L',
     'HIV-negative females 9-20y, sub-Saharan Africa'),

    # Population text
    ("Population text",
     'Adults with KRAS-G12C-mutated locally advanced unresectable or metastatic NSCLC',
     'HIV-negative females aged 9-20 years in sub-Saharan Africa with no history of HPV vaccination'),

    # PubMed query example (multiple variants — try the most-used)
    ("PubMed query example",
     'KRAS-G12C+ NSCLC first line sotorasib sotorasib sotorasib docetaxel',
     '("HPV vaccine" OR "papillomavirus vaccine") AND ("single dose" OR "1-dose" OR "1 dose") AND (Africa OR Kenya OR Tanzania)'),

    # CT.gov query (the IMDC-risk RCC mistake — template was actually RCC-clean too, with wrong label)
    ("CT.gov query intervention",
     'query.intr=renal AND cell AND carcinoma AND first AND line AND sotorasib AND sotorasib AND sotorasib AND docetaxel',
     'query.intr=HPV AND vaccine AND single AND dose'),

    # Mol-name dictionary (deep JS — may not exist in this template)
    ("Trial-mol map sotorasib",
     "'CodeBreaK 200': 'Sotorasib', 'KRYSTAL-12': 'Adagrasib'",
     "'KEN-SHE bivalent': 'HPV bivalent (Cervarix)', 'KEN-SHE nonavalent': 'HPV nonavalent (Gardasil-9)', 'DoRIS 1d-vs-3d bivalent': 'HPV bivalent (Cervarix)'"),
]


def main() -> int:
    if not FILE.exists():
        print(f"ERROR: {FILE} not found", file=sys.stderr)
        return 1
    text = FILE.read_text(encoding="utf-8")
    original_size = len(text)

    applied = []
    for desc, old, new in REPLACEMENTS:
        count = text.count(old)
        if count > 0:
            text = text.replace(old, new)
            applied.append((desc, count))

    FILE.write_text(text, encoding="utf-8")
    print(f"Applied {len(applied)} of {len(REPLACEMENTS)} replacement groups")
    for desc, count in applied:
        print(f"  + {desc}: {count} occurrence(s)")
    skipped = [d for d, _, _ in REPLACEMENTS if not any(d == a[0] for a in applied)]
    for s in skipped:
        print(f"  - {s}: no match")

    print(f"Size delta: {len(text) - original_size:+d} bytes")

    # Residual count
    residual = {
        "KRAS": text.count("KRAS"),
        "sotorasib/Sotorasib": text.count("sotorasib") + text.count("Sotorasib"),
        "NSCLC": text.count("NSCLC"),
        "docetaxel/Docetaxel": text.count("docetaxel") + text.count("Docetaxel"),
        "HPV": text.count("HPV"),
        "vaccin": text.count("vaccin"),
    }
    print("\nResidual counts:")
    for k, v in residual.items():
        print(f"  {k}: {v}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
