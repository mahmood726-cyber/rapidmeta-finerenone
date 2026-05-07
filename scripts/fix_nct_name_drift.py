"""Align nctAcronyms[NCT] to match realData[NCT].name for the 7
WARNs surfaced by Sentinel P0-rapidmeta-data-integrity.

Strategy: the substantive data-of-record is realData[NCT].name. The
nctAcronyms map is a display-label cache. When they disagree, prefer
realData and update nctAcronyms.

We do NOT touch realData. We do NOT touch the 'b'-suffixed parallel
NCT entries (these are intentional disambiguation in PNH for two
trials registered together; their names are correct already).

Idempotent.
"""
from __future__ import annotations
import sys, io, re
from pathlib import Path
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

REPO = Path(__file__).resolve().parent.parent

TARGETS = [
    'MALARIA_VACCINE_REVIEW.html',
    'PNH_NEW_COMPLEMENT_REVIEW.html',
    'PRIMAQUINE_GAMETOCYTE_DR_REVIEW.html',
    'ROTAVIRUS_VACCINE_AFRICA_REVIEW.html',
]

# (NCT, expected new acronym value) — derived from realData.name
FIXES = {
    'NCT03896724': 'R21/Matrix-M Phase 2b (Datoo 2021)',
    'NCT04704830': 'R21/Matrix-M Phase 3 (Datoo 2024)',
    'NCT04434092': 'COMMODORE-2',  # Registry truth; AACT confirms NCT04434092 = COMMODORE 2
    'NCT01365598': 'Eziefula 2014 Uganda',
    'NCT02174900': 'SAFEPRIM Burkina Faso',
    'NCT00241644': 'Rotarix Africa (Madhi 2010)',
    'NCT00362648': 'RotaTeq Africa (Armah 2010)',
}

# For PNH NCT04434092 specifically: realData.name says COMMODORE-1 but
# AACT says it's COMMODORE-2. Fix realData too — registry is truth.
REALDATA_FIXES = {
    'PNH_NEW_COMPLEMENT_REVIEW.html': {
        'NCT04434092': ('COMMODORE-1', 'COMMODORE-2'),
    },
}


def patch_nct_acronyms(text, fixes):
    """Update each 'NCT...': 'OLD' inside an nctAcronyms object to 'NEW'."""
    n = 0
    for nct, new_acronym in fixes.items():
        pat = re.compile(r"('" + re.escape(nct) + r"'\s*:\s*)'([^']+)'")
        def replacer(m):
            nonlocal n
            old = m.group(2)
            if old == new_acronym:
                return m.group(0)
            n += 1
            return m.group(1) + "'" + new_acronym + "'"
        text = pat.sub(replacer, text, count=1)
    return text, n


def patch_realdata_name(text, nct, old_name, new_name):
    """Update realData[NCT].name from old to new. Idempotent."""
    pat = re.compile(
        r"('" + re.escape(nct) + r"'\s*:\s*\{\s*\n?\s*"
        r"name\s*:\s*)'" + re.escape(old_name) + r"'"
    )
    new, n = pat.subn(r"\1'" + new_name + "'", text, count=1)
    return new, n


def main():
    total_acronym_fixes = 0
    total_realdata_fixes = 0
    for fname in TARGETS:
        hp = REPO / fname
        if not hp.exists(): continue
        text = hp.read_text(encoding="utf-8", errors="replace")
        # Step 1: fix nctAcronyms
        new, n_acro = patch_nct_acronyms(text, FIXES)
        # Step 2: realData fixes (PNH only)
        n_real = 0
        if fname in REALDATA_FIXES:
            for nct, (old, new_name) in REALDATA_FIXES[fname].items():
                new, n_one = patch_realdata_name(new, nct, old, new_name)
                n_real += n_one
        if n_acro > 0 or n_real > 0:
            hp.write_text(new, encoding="utf-8")
            total_acronym_fixes += n_acro
            total_realdata_fixes += n_real
            print(f"  {fname}: nctAcronyms {n_acro}, realData {n_real}")
    print(f"\nTotal nctAcronyms updates: {total_acronym_fixes}")
    print(f"Total realData updates:    {total_realdata_fixes}")


if __name__ == "__main__":
    main()
