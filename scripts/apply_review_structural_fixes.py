"""Idempotent codemod for *_REVIEW.html structural fixes.

Applies two byte-identical replacements across the RapidMeta scaffold:

(P1-2) `highlightEvidence` → regex-auto-highlight version that lights up
  P-values, signed decimals, percentages, n=N counts, and 3+ digit integers
  in addition to per-row literal terms (with overlap merge).

(P1-3) CT.gov design-metadata evidence row relabeled so the trial-profile
  data-source toggle no longer appears to contradict the curated D1-D5
  RoB-2 narrative.

Usage:
  python scripts/apply_review_structural_fixes.py --dry-run
  python scripts/apply_review_structural_fixes.py --apply
"""
from __future__ import annotations
import argparse
import os
import sys
from pathlib import Path

OLD_HE = """        const highlightEvidence = (text, highlights) => {


            let safe = escapeHtml(text);


            const terms = sanitizeHighlightTerms(highlights);


            if (terms.length === 0) return safe;


            terms.forEach(h => {


                const escaped = escapeHtml(h);


                safe = safe.replace(new RegExp(escaped.replace(/[.*+?^${}()|[\\]\\\\]/g, '\\\\$&'), 'g'),


                    `<span class="highlight-data">${escaped}</span>`);


            });


            return safe;


        };"""

NEW_HE = """        const HIGHLIGHT_AUTO_PATTERNS = [
            /P\\s*[<>=]\\s*0?\\.\\d+/g,           // P-values: P=0.0004, P<0.0001
            /\\b\\d+(?:\\.\\d+)?\\s*%/g,            // percentages: 22%, 2.1%
            /-?\\d+\\.\\d+/g,                     // signed decimals: -0.41, 1.30
            /\\bn\\s*=\\s*\\d+\\b/gi,               // n=N counts: n=202
            /\\b\\d{3,}\\b/g                      // multi-digit integers: 637, 2023
        ];


        const highlightEvidence = (text, highlights) => {


            const terms = sanitizeHighlightTerms(highlights);


            const ranges = [];


            for (const re of HIGHLIGHT_AUTO_PATTERNS) {


                for (const m of String(text ?? '').matchAll(re)) {


                    ranges.push([m.index, m.index + m[0].length]);


                }


            }


            for (const term of terms) {


                const escapedTerm = String(term).replace(/[.*+?^${}()|[\\]\\\\]/g, '\\\\$&');


                const re = new RegExp(escapedTerm, 'g');


                for (const m of String(text ?? '').matchAll(re)) {


                    ranges.push([m.index, m.index + m[0].length]);


                }


            }


            if (ranges.length === 0) return escapeHtml(text);


            ranges.sort((a, b) => a[0] - b[0] || b[1] - a[1]);


            const merged = [];


            for (const [s, e] of ranges) {


                if (merged.length && s < merged[merged.length - 1][1]) {


                    merged[merged.length - 1][1] = Math.max(merged[merged.length - 1][1], e);


                } else {


                    merged.push([s, e]);


                }


            }


            let out = '';


            let cursor = 0;


            const src = String(text ?? '');


            for (const [s, e] of merged) {


                out += escapeHtml(src.substring(cursor, s));


                out += `<span class="highlight-data">${escapeHtml(src.substring(s, e))}</span>`;


                cursor = e;


            }


            out += escapeHtml(src.substring(cursor));


            return out;


        };"""

OLD_CTGOV = """                    items.push({


                        label: 'Design — Allocation & masking',


                        source: `CT.gov ${nct} protocolSection.designModule`,


                        text: `Allocation: ${allocText}. Masking: ${maskText}${whoMasked ? ' (' + whoMasked + ')' : ''}.`,


                        highlights: [allocText, maskText, whoMasked].filter(Boolean)


                    });"""

NEW_CTGOV = """                    items.push({


                        label: 'CT.gov design metadata (informs RoB — NOT a RoB-2 judgment)',


                        source: `CT.gov ${nct} protocolSection.designModule (auto-derived from registry; see \"Risk of Bias (RoB 2.0)\" evidence row and RoB tab for the curated 5-domain assessment)`,


                        text: `[CT.gov registry metadata] Allocation: ${allocText}. Masking: ${maskText}${whoMasked ? ' (' + whoMasked + ')' : ''}. — Note: this row is structured CT.gov registration metadata, not a RoB-2 domain rating. The curated D1–D5 RoB-2 judgments are in the separate \"Risk of Bias (RoB 2.0)\" evidence row and in the RoB tab. Do not treat the two as conflicting; they answer different questions.`,


                        highlights: [allocText, maskText, whoMasked].filter(Boolean)


                    });"""


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--apply", action="store_true", help="Write changes to disk (default: dry-run)")
    parser.add_argument("--root", default=".", help="Root directory containing *_REVIEW.html files")
    args = parser.parse_args()

    root = Path(args.root)
    files = sorted(root.glob("*_REVIEW.html"))

    stats = {"he_applied": 0, "he_already": 0, "he_missing": 0,
             "ctgov_applied": 0, "ctgov_already": 0, "ctgov_missing": 0,
             "files_changed": 0}
    skipped: list[str] = []

    for f in files:
        text = f.read_text(encoding="utf-8")
        original = text
        any_change = False

        # P1-2: highlightEvidence
        if NEW_HE in text:
            stats["he_already"] += 1
        elif OLD_HE in text:
            text = text.replace(OLD_HE, NEW_HE, 1)
            stats["he_applied"] += 1
            any_change = True
        else:
            stats["he_missing"] += 1
            skipped.append(f"{f.name}: highlightEvidence not found")

        # P1-3: CT.gov design metadata label
        if NEW_CTGOV in text:
            stats["ctgov_already"] += 1
        elif OLD_CTGOV in text:
            text = text.replace(OLD_CTGOV, NEW_CTGOV, 1)
            stats["ctgov_applied"] += 1
            any_change = True
        else:
            stats["ctgov_missing"] += 1
            # Only log if highlightEvidence was found — otherwise it's a DTA file
            if "highlightEvidence" in original:
                skipped.append(f"{f.name}: CT.gov design block not found")

        if any_change:
            stats["files_changed"] += 1
            if args.apply:
                f.write_text(text, encoding="utf-8")

    print(f"Files scanned: {len(files)}")
    print(f"Mode: {'APPLY' if args.apply else 'DRY-RUN'}")
    print()
    print(f"P1-2 highlightEvidence: applied={stats['he_applied']}, already-fixed={stats['he_already']}, not-found={stats['he_missing']}")
    print(f"P1-3 CT.gov metadata:    applied={stats['ctgov_applied']}, already-fixed={stats['ctgov_already']}, not-found={stats['ctgov_missing']}")
    print(f"Files {'changed' if args.apply else 'would-change'}: {stats['files_changed']}")
    if skipped:
        print(f"\nNotes ({len(skipped)} entries):")
        for s in skipped[:20]:
            print(f"  {s}")
        if len(skipped) > 20:
            print(f"  ... and {len(skipped) - 20} more")
    return 0


if __name__ == "__main__":
    sys.exit(main())
