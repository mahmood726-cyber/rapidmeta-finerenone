"""Remove the 30 empty reviews:
  - Delete <REVIEW>.html files
  - Delete outputs/extraction_audit/data/<REVIEW>.json
  - Remove the <a class="card …">…</a> entries from index.html
  - Update review-count strings in index.html headers/copy
  - Preserve the audit trail in empty_reviews_notice.json + this script
"""
from __future__ import annotations
import json, re, sys, io
from pathlib import Path

if hasattr(sys.stdout, "buffer") and getattr(sys.stdout, "encoding", "").lower() != "utf-8":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

HERE = Path(__file__).resolve().parent.parent
OUT = HERE / "outputs" / "extraction_audit"
DATA = OUT / "data"
DRY = "--dry-run" in sys.argv

d = json.loads((OUT / "empty_reviews_notice.json").read_text(encoding="utf-8"))
all_empty = sorted({x["review"] for x in d.get("cleanup_zeroed", [])
                                  | {x["review"] for x in d.get("never_extracted", [])}}
                    if False else
                   [x["review"] for x in d.get("cleanup_zeroed", [])] +
                   [x["review"] for x in d.get("never_extracted", [])])
all_empty = list(dict.fromkeys(all_empty))
print(f"Empty reviews to remove: {len(all_empty)}")

# Stage 1: delete HTML + extracted JSON
deleted_html = []
deleted_json = []
for rv in all_empty:
    html_p = HERE / f"{rv}.html"
    json_p = DATA / f"{rv}.json"
    if html_p.exists():
        if not DRY: html_p.unlink()
        deleted_html.append(rv)
    if json_p.exists():
        if not DRY: json_p.unlink()
        deleted_json.append(rv)

# Stage 2: remove <a class="card …"><REVIEW.html"…</a> entries from index.html
idx_p = HERE / "index.html"
idx = idx_p.read_text(encoding="utf-8")
removed_from_index = []
for rv in all_empty:
    # Match the full <a class="card ..."> ... </a> for this review href, including
    # any leading whitespace + trailing newline, plus card-host wrapper if present.
    # Patterns observed in the index:
    #   <a href="REVIEW.html" class="card xx"><span class="name">...</span><span class="pub">...</span></a>
    #   <div class="card-host">  <a ...>...</a>  <a class="claim-chip">...</a>  </div>
    pat_simple = re.compile(
        r'[ \t]*<a href="' + re.escape(rv) + r'\.html"[^>]*class="card[^"]*"[^>]*>.*?</a>[ \t]*\n?',
        re.DOTALL | re.IGNORECASE
    )
    pat_host = re.compile(
        r'[ \t]*<div class="card-host">\s*<a href="' + re.escape(rv) + r'\.html"[^>]*>.*?</a>\s*(?:<a class="claim-chip"[^>]*>.*?</a>\s*)?</div>[ \t]*\n?',
        re.DOTALL | re.IGNORECASE
    )
    new_idx, n_host = pat_host.subn("", idx)
    if n_host == 0:
        new_idx, n_simple = pat_simple.subn("", idx)
        if n_simple > 0:
            idx = new_idx
            removed_from_index.append((rv, n_simple, "simple"))
    else:
        idx = new_idx
        removed_from_index.append((rv, n_host, "host"))

# Stage 2b: also remove entries from the E156-chip JS dictionary
removed_from_chip_dict = []
for rv in all_empty:
    pat_dict = re.compile(
        r'"' + re.escape(rv) + r'\.html"\s*:\s*\{[^{}]*?\}\s*,?\s*',
        re.DOTALL
    )
    new_idx, n = pat_dict.subn("", idx)
    if n > 0:
        idx = new_idx
        removed_from_chip_dict.append((rv, n))

# Stage 2c: remove <tr> rows from review tables ("Therapeutic Area" tables)
removed_from_table = []
for rv in all_empty:
    pat_tr = re.compile(
        r'\s*<tr>[^<]*<td[^>]*>\s*<a href="' + re.escape(rv) +
        r'\.html"[^>]*>.*?</tr>',
        re.DOTALL | re.IGNORECASE
    )
    new_idx, n = pat_tr.subn("", idx)
    if n > 0:
        idx = new_idx
        removed_from_table.append((rv, n))

# Stage 3: refresh review counts in index.html
# Original: "421 therapeutic topics", "418", "411" — replace with new count
remaining_count = 411 - len(deleted_html)  # was 411 reviews before removal
# Find current "418 therapeutic topics" or "421" string and adjust
for old in [r"\b421\b", r"\b418\b", r"\b411\b"]:
    p = re.compile(old)
    idx = p.sub(str(remaining_count), idx)

if not DRY:
    idx_p.write_text(idx, encoding="utf-8")

print(f"\nDeleted HTML files: {len(deleted_html)}")
print(f"Deleted JSON snapshots: {len(deleted_json)}")
print(f"Removed from index.html card grid: {len(removed_from_index)}")
for rv, n, kind in removed_from_index:
    print(f"  {kind}: {rv} ({n} match{'es' if n != 1 else ''})")
print(f"Removed from E156-chip JS dict: {len(removed_from_chip_dict)}")
print(f"Removed from review tables: {len(removed_from_table)}")

(OUT / "removed_empty_reviews.json").write_text(json.dumps({
    "removed_reviews": all_empty,
    "deleted_html": deleted_html,
    "deleted_json": deleted_json,
    "removed_from_index": [{"review": r, "matches": n, "kind": k} for r, n, k in removed_from_index],
    "new_review_count": remaining_count,
}, indent=2, ensure_ascii=False), encoding="utf-8")
print(f"\nNew review count: {remaining_count}")
print(f"Log → outputs/extraction_audit/removed_empty_reviews.json")
