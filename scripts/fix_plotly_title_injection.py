"""Fix unescaped double-quote inside Plotly's bundled SVG-icon string array.

Bug: 4 *_REVIEW.html files had an injected template-literal substitution
inserted into Plotly v2.35.2's `newplotlylogo` icon SVG:

  '<title>${escapeHtml(document.title || "RapidMeta meta-analysis report")}</title>'

The outer string is double-quoted. The inner `"RapidMeta..."` is ALSO
double-quoted - which closes the outer string. The parser then encounters
`RapidMeta` as a bare identifier and emits SyntaxError "Unexpected identifier
'RapidMeta'", killing Plotly's IIFE and (cascading) every later script tag.

Affected: ANTI_CD20_MS, JAKI_RA_NMA, PSA_BIOLOGICS, SPONDYLOARTHRITIS reviews.

Fix: replace the injected fragment with a plain static title that uses
escaped inner quotes. The title text is decorative (Plotly's logo SVG only
shown if a user explicitly downloads the chart) so the lost dynamic-title
behavior is acceptable.
"""
import re
import sys
import io
from pathlib import Path

if "pytest" not in sys.modules and hasattr(sys.stdout, "buffer"):
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

HERE = Path(__file__).resolve().parent.parent

OLD = '<title>${escapeHtml(document.title || "RapidMeta meta-analysis report")}</title>'
NEW = '<title>RapidMeta meta-analysis report</title>'


def main():
    n = 0
    for p in sorted(HERE.glob("*.html")):
        if not p.is_file():
            continue
        txt = p.read_text(encoding="utf-8", errors="replace")
        if OLD in txt:
            p.write_text(txt.replace(OLD, NEW), encoding="utf-8")
            n += 1
            print(f"  fixed: {p.name}")
    print(f"\nFixed {n} files.")


if __name__ == "__main__":
    main()
