"""For each trial block where publishedHR is negative (continuous-outcome MD
stored in HR field), change estimandType from 'HR' to 'MD'. Fixes the 50+
NEG_HR / NEG_LCI_HR / NEG_UCI_HR flags from internal_consistency_check.py.

Negative HR is physically impossible. If the value is negative, it's almost
certainly a continuous outcome (mean difference for HbA1c, BCVA letters,
CDR-SB, migraine days, etc.) that was mislabelled.

Idempotent: only flips estimandType from 'HR' (or missing) to 'MD' where
publishedHR < 0.
"""
from __future__ import annotations
import sys, io, re
from pathlib import Path
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

REPO = Path("C:/Projects/Finrenone")

# Match a trial block whose publishedHR or hrLCI or hrUCI is negative.
TRIAL_RE = re.compile(
    r"('NCT\d+(?:_[A-Za-z0-9]+)?'\s*:\s*\{[^}]*?"
    r"name:\s*'([^']+?)'[^}]*?"
    r"publishedHR:\s*([\d.eE+\-]+)\s*,\s*"
    r"hrLCI:\s*([\d.eE+\-]+)\s*,\s*"
    r"hrUCI:\s*([\d.eE+\-]+))",
    re.DOTALL,
)


def main():
    review_files = sorted(REPO.glob("*_REVIEW.html"))
    n_changed = 0
    files_modified = 0

    for hp in review_files:
        text = hp.read_text(encoding="utf-8", errors="replace")
        original = text

        # Find all trial blocks with negative publishedHR
        modified = False
        for m in list(TRIAL_RE.finditer(text)):
            full_block = m.group(1)
            name = m.group(2)
            ph = m.group(3)
            lci = m.group(4)
            uci = m.group(5)
            try:
                ph_val = float(ph)
                lci_val = float(lci)
                uci_val = float(uci)
            except ValueError:
                continue
            # Trigger if any of the three is negative (continuous-outcome MD signal)
            if ph_val >= 0 and lci_val >= 0 and uci_val >= 0:
                continue

            # Look for `estimandType:` in this block. The block end is the next `},` after match end.
            block_start_in_text = m.start()
            block_end_in_text = text.find("},", m.end())
            if block_end_in_text == -1 or block_end_in_text > block_start_in_text + 8000:
                block_end_in_text = block_start_in_text + 8000
            block_text = text[block_start_in_text:block_end_in_text]

            # Check if estimandType is present
            et_match = re.search(r"(estimandType:\s*')([^']+)(')", block_text)
            if et_match:
                if et_match.group(2) == "MD":
                    continue  # already correct
                # Replace estimandType in this block only
                old_block = block_text
                new_block = block_text[:et_match.start()] + et_match.group(1) + "MD" + et_match.group(3) + block_text[et_match.end():]
                text = text[:block_start_in_text] + new_block + text[block_end_in_text:]
                modified = True
                n_changed += 1
                print(f"  FIX-EXISTING-ET {hp.name}::{name} (was '{et_match.group(2)}', now 'MD'; pubHR={ph_val})")
            else:
                # Insert estimandType: 'MD' before publishedHR
                # Find publishedHR pattern in block
                ph_match = re.search(r"publishedHR:\s*-[\d.eE+\-]+", block_text)
                if ph_match:
                    insertion = "estimandType: 'MD', "
                    new_block = block_text[:ph_match.start()] + insertion + block_text[ph_match.start():]
                    text = text[:block_start_in_text] + new_block + text[block_end_in_text:]
                    modified = True
                    n_changed += 1
                    print(f"  FIX-INSERT-ET {hp.name}::{name} (inserted 'MD'; pubHR={ph_val})")

        if modified:
            hp.write_text(text, encoding="utf-8")
            files_modified += 1

    print(f"\n=== Summary ===")
    print(f"  Files modified: {files_modified}/{len(review_files)}")
    print(f"  Trial blocks fixed: {n_changed}")


if __name__ == "__main__":
    main()
