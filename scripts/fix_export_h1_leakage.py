"""Fix template-clone H1 leakage in 55 review files.

The print/export template inside each review's JS contains a hardcoded
H1 string left over from a finerenone parent template:

    <h1>hfref quadruple therapy in Cardio-Kidney-Metabolic Disease</h1>

For 55 files, that H1 doesn't match the file's actual title. Same pattern
in 4 files for the export <title>:

    <title>RapidMeta Rheumatology | JAK Inhibitors NMA in MTX-IR RA v1.0

Fix: replace both with `${document.title.split('|').slice(1).join('|').trim()}`
so the export uses the host page's own title at runtime.

Idempotent.
"""
from __future__ import annotations
import sys, io, re
from pathlib import Path
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

REPO = Path(__file__).resolve().parent.parent

# Pattern 1: hardcoded body H1 inside printHtml template literal
H1_LEAK_PATTERN = re.compile(
    r'<h1>hfref quadruple therapy in Cardio-Kidney-Metabolic Disease</h1>'
)
H1_REPLACEMENT = '<h1>${escapeHtml((document.title || "Meta-analysis report").split("|").slice(1).join("|").trim() || document.title || "Meta-analysis report")}</h1>'

# Pattern 2: hardcoded export <title> stale from a JAK template
TITLE_LEAK_PATTERN = re.compile(
    r'<title>RapidMeta Rheumatology \| JAK Inhibitors NMA in MTX-IR RA v1\.0</title>'
)
TITLE_REPLACEMENT = '<title>${escapeHtml(document.title || "RapidMeta meta-analysis report")}</title>'


def main():
    files = sorted(REPO.glob("*_REVIEW.html"))
    n_h1 = 0
    n_title = 0
    n_files_h1 = 0
    n_files_title = 0
    for hp in files:
        text = hp.read_text(encoding="utf-8", errors="replace")
        new_text, h1_count = H1_LEAK_PATTERN.subn(H1_REPLACEMENT, text)
        new_text, title_count = TITLE_LEAK_PATTERN.subn(TITLE_REPLACEMENT, new_text)
        if h1_count > 0 or title_count > 0:
            hp.write_text(new_text, encoding="utf-8")
            if h1_count > 0:
                n_files_h1 += 1
                n_h1 += h1_count
            if title_count > 0:
                n_files_title += 1
                n_title += title_count
    print(f"Files with H1 leakage fixed:    {n_files_h1} (replacements: {n_h1})")
    print(f"Files with title leakage fixed: {n_files_title} (replacements: {n_title})")


if __name__ == "__main__":
    main()
