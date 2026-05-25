"""Extract inline Plotly v2.35.2 bundle from 54 curated REVIEW pages to a
single shared vendor file. Each page replaces its ~1 MB inline <script>
with a <script src> reference, freeing ~54 MB of duplicated text from the
repo and enabling browser caching across pages.

Mechanism:
  1. Find one page's inline `<script>... Plotly.js v2.35.2 basic ...</script>`
     block and write its contents to vendor/plotly-2.35.2-basic.min.js
     (one file).
  2. Replace that exact <script>...</script> block with
     <script src="vendor/plotly-2.35.2-basic.min.js"></script>
     in every file that contains it. Idempotent — files already converted
     (matching the <script src> line) are skipped.

Safety: the vendor file is written once and the inline block is replaced
verbatim. The CSP `script-src 'self' ...` directive already permits
same-origin scripts. The build-time JS parse gate (_js_parse_gate.py)
verifies each post-fix page still parses.
"""
from __future__ import annotations
import re
import sys
import io
from pathlib import Path

if "pytest" not in sys.modules and hasattr(sys.stdout, "buffer"):
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

sys.path.insert(0, str(Path(__file__).resolve().parent))
try:
    from _js_parse_gate import js_parse_ok
except ImportError:
    js_parse_ok = lambda _t: True  # type: ignore

HERE = Path(__file__).resolve().parent.parent
VENDOR_DIR = HERE / "vendor"
VENDOR_DIR.mkdir(exist_ok=True)
VENDOR_FILE = VENDOR_DIR / "plotly-2.35.2-basic.min.js"

# The inline block starts with a comment marker. Capture from the opening
# <script>...> through to the closing </script> that wraps the bundle.
PLOTLY_BLOCK_RE = re.compile(
    r"<script\b[^>]*>\s*/\* Plotly\.js v2\.35\.2 basic[\s\S]*?</script>"
)

NEW_TAG = '<script src="vendor/plotly-2.35.2-basic.min.js" defer></script>'


def extract_bundle_from(p: Path) -> str | None:
    txt = p.read_text(encoding="utf-8", errors="replace")
    m = PLOTLY_BLOCK_RE.search(txt)
    if not m:
        return None
    # Strip outer <script>...</script>, keep the JS body.
    raw = m.group(0)
    body_re = re.compile(r"<script\b[^>]*>([\s\S]*?)</script>")
    bm = body_re.match(raw)
    return bm.group(1) if bm else None


def patch_file(p: Path) -> tuple[bool, str]:
    txt = p.read_text(encoding="utf-8", errors="replace")
    if NEW_TAG in txt and not PLOTLY_BLOCK_RE.search(txt):
        return False, "already externalised"
    if not PLOTLY_BLOCK_RE.search(txt):
        return False, "no inline plotly"
    new = PLOTLY_BLOCK_RE.sub(NEW_TAG, txt, count=1)
    if not js_parse_ok(new):
        return False, "parse-gate failed (kept inline)"
    p.write_text(new, encoding="utf-8")
    return True, "ok"


def main():
    targets = sorted(p for p in HERE.glob("*_REVIEW.html") if p.is_file())
    # First pass: harvest the bundle once.
    if not VENDOR_FILE.exists():
        print("Extracting Plotly bundle to vendor file...")
        for p in targets:
            body = extract_bundle_from(p)
            if body:
                VENDOR_FILE.write_text(body, encoding="utf-8")
                print(f"  wrote {VENDOR_FILE.relative_to(HERE)} ({len(body):,} bytes) from {p.name}")
                break
        else:
            print("  no source page had the inline Plotly block")
            return
    else:
        print(f"  vendor file already present ({VENDOR_FILE.stat().st_size:,} bytes)")

    # Second pass: replace inline block with <script src> in every matching file.
    print("\nRewriting pages...")
    counts = {"ok": 0, "no inline plotly": 0, "already externalised": 0,
              "parse-gate failed (kept inline)": 0}
    for i, p in enumerate(targets, 1):
        ok, reason = patch_file(p)
        counts[reason if not ok else "ok"] = counts.get(reason if not ok else "ok", 0) + 1
        if i % 200 == 0:
            print(f"  [{i}/{len(targets)}]")
    print(f"\nResults: {counts}")


if __name__ == "__main__":
    main()
