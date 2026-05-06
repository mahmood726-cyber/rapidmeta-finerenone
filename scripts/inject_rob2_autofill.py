"""Inject vendor/rob2-autofill.js + 'Auto-fill from abstracts' button
into the existing RoB-2 traffic-light widget. Idempotent."""
from __future__ import annotations
import sys, io, argparse, re
from pathlib import Path
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

REPO = Path("C:/Projects/Finrenone")

ROB_INCLUDE_RE = re.compile(r'<script\s+src="vendor/rob2-traffic-light\.js"\s*></script>')

SCRIPT_TAG = (
    '\n    <!-- RoB-2 regex auto-fill + user attest workflow -->\n'
    '    <script src="vendor/rob2-autofill.js"></script>\n'
)

# Add auto-fill button next to the existing 'Render' button
RENDER_BTN_RE = re.compile(
    r'(<button\s+onclick="window\.Rob2TrafficLight && window\.Rob2TrafficLight\.render\(\'#rob2Widget\'\)"[^>]*>\s*Render\s*</button>)'
)

NEW_BTN = (
    r'\1' +
    '<button onclick="window.Rob2Autofill && window.Rob2Autofill.open()" '
    'style="padding:4px 10px;background:#7c3aed;color:#fff;border:none;border-radius:4px;font-size:10px;font-weight:700;cursor:pointer;margin-left:6px;" '
    'title="Auto-fill RoB-2 from PubMed abstracts via regex inference; user attests each per-trial proposal">'
    '🤖 Auto-fill + attest</button>'
)


def patch(text):
    if 'vendor/rob2-autofill.js' in text:
        return text, "ALREADY"
    rb = ROB_INCLUDE_RE.search(text)
    if rb:
        text = text[:rb.end()] + SCRIPT_TAG + text[rb.end():]
    else:
        head = text.find("</head>")
        if head < 0:
            return text, "NO_HEAD"
        text = text[:head] + SCRIPT_TAG + text[head:]
    new_text, n = RENDER_BTN_RE.subn(NEW_BTN, text, count=1)
    if n == 0:
        return text, "NO_RENDER_BUTTON"
    return new_text, "PATCHED"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    files = sorted(REPO.glob("*_REVIEW.html"))
    print(f"Patching {len(files)} review HTMLs ...")
    counts = {}
    for hp in files:
        text = hp.read_text(encoding="utf-8", errors="replace")
        new_text, status = patch(text)
        counts[status] = counts.get(status, 0) + 1
        if status == "PATCHED" and not args.dry_run:
            hp.write_text(new_text, encoding="utf-8")

    print(f"\n=== Summary ===")
    for k, v in sorted(counts.items(), key=lambda x: -x[1]):
        print(f"  {k:25s} {v}")


if __name__ == "__main__":
    main()
