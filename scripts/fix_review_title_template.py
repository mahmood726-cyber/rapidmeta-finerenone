"""Fix the ReviewTitle template-fallback bug across the corpus.

Audit (Agent 8) found 62 of 231 review files have ReviewTitle that's
completely wrong — a template default leaked across files. The page
<title> tag is correct in all cases (per spot-check), so we derive the
correct ReviewTitle from <title>.

Strategy:
  1. Extract <title> content (e.g.,
     "RapidMeta Cardiology | GLP-1 RA Class NMA for MACE in T2D
     CV-Outcomes v1.0").
  2. Strip the prefix "RapidMeta {Specialty} | " and the version suffix
     " v1.0" / " v0.1" etc.
  3. Replace the ReviewTitle row's <td> content with the cleaned title.
  4. Idempotent: only patches files where the current ReviewTitle is one
     of the known wrong templates OR the cleaned <title> doesn't already
     match.

Use --dry-run first.
"""
from __future__ import annotations
import sys, io, argparse, re
from pathlib import Path
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

REPO = Path("C:/Projects/Finrenone")

TITLE_TAG_RE = re.compile(r'<title>\s*([^<]+?)\s*</title>')

# Match the "Review Title" row in the registration section.
# Capture the existing <td> content so we can compare.
REVIEW_TITLE_ROW_RE = re.compile(
    r'(<tr><td class="p-4 w-1/4 font-bold text-slate-400">Review Title</td>'
    r'<td class="p-4 text-slate-300">)([^<]*?)(</td></tr>)',
    re.MULTILINE,
)

# Known wrong template snippets — when the ReviewTitle starts with these,
# we always overwrite. Surfaced by Agent 8.
KNOWN_WRONG_TEMPLATES = [
    "Network Meta-Analysis of Sodium-Glucose Co-transporter-2 Inhibitors",
    "Checkpoint Inhibitor plus Platinum-Doublet Chemotherapy",
    "Long-Acting Cabotegravir Injection",
    "Anifrolumab (Type I Interferon Receptor Monoclonal Antibody)",
]


def clean_page_title(t: str) -> str:
    """Strip 'RapidMeta {Specialty} | ' prefix and ' v0.1' / ' v1.0'
    version suffix."""
    # Remove prefix
    t = re.sub(r'^\s*RapidMeta\s+[A-Za-z][A-Za-z\-\/ ]*?\s*\|\s*', '', t)
    # Remove version suffix " v0.1", " v1.0", " v12.5", " v0.1 (...)"
    t = re.sub(r'\s+v\d+(\.\d+)*([^\)]*)?$', '', t)
    return t.strip()


def patch(text: str):
    """Returns (new_text, status, old_title, new_title)."""
    title_m = TITLE_TAG_RE.search(text)
    if not title_m:
        return text, "NO_PAGE_TITLE", None, None
    page_title = clean_page_title(title_m.group(1))
    if not page_title:
        return text, "EMPTY_PAGE_TITLE", None, None

    rt_m = REVIEW_TITLE_ROW_RE.search(text)
    if not rt_m:
        return text, "NO_REVIEW_TITLE_ROW", None, None
    current_rt = rt_m.group(2).strip()

    if current_rt == page_title:
        return text, "ALREADY_MATCHES", current_rt, page_title

    # Decide whether to overwrite.
    # 1. ALWAYS overwrite if current matches a known-wrong template.
    is_known_wrong = any(t in current_rt for t in KNOWN_WRONG_TEMPLATES)
    # 2. Otherwise only overwrite if cleaned page title is a clear
    #    descriptor (not just "Review" or empty after cleaning).
    if not is_known_wrong:
        # Per Agent-8 observation: most non-flagged files already have the
        # correct ReviewTitle. Skip those — don't risk overwriting bespoke
        # ReviewTitle text with a less-descriptive page title.
        return text, "BESPOKE_KEEP", current_rt, page_title

    new_text = text[:rt_m.start(2)] + page_title + text[rt_m.end(2):]
    return new_text, "PATCHED", current_rt, page_title


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    files = sorted(REPO.glob("*_REVIEW.html"))
    print(f"Scanning {len(files)} review HTMLs ...")

    counts = {}
    patches = []
    for hp in files:
        text = hp.read_text(encoding="utf-8", errors="replace")
        new_text, status, old, new = patch(text)
        counts[status] = counts.get(status, 0) + 1
        if status == "PATCHED":
            patches.append((hp.name, old[:60], new[:80]))
            if not args.dry_run:
                hp.write_text(new_text, encoding="utf-8")

    print(f"\n=== Summary ===")
    for k, v in sorted(counts.items(), key=lambda x: -x[1]):
        print(f"  {k:25s} {v}")

    print(f"\n=== Sample of patched files ({len(patches)} total) ===")
    for fname, old, new in patches[:25]:
        print(f"  {fname}")
        print(f"    old: {old}")
        print(f"    new: {new}")
    if len(patches) > 25:
        print(f"  ... and {len(patches) - 25} more")
    if args.dry_run:
        print("\n  DRY RUN — no files written.")


if __name__ == "__main__":
    main()
