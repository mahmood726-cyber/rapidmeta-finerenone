"""Inject RoB-2 traffic-light widget into Extraction tab. Idempotent."""
from __future__ import annotations
import sys, io, argparse, re
from pathlib import Path
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

REPO = Path("C:/Projects/Finrenone")

OS_INCLUDE_RE = re.compile(r'<script\s+src="vendor/outcome-switching\.js"\s*></script>')

SCRIPT_TAG = (
    '\n    <!-- RoB-2 traffic-light visualization -->\n'
    '    <script src="vendor/rob2-traffic-light.js"></script>\n'
)

OS_PANEL_RE = re.compile(
    r'(<div id="osAudit">[\s\S]*?</div>\s*</div>)'
)

PANEL = '''

                <div class="bg-slate-900/50 mt-4 p-4 rounded-lg border border-slate-800">
                    <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:10px;">
                        <h4 class="text-xs font-bold uppercase text-blue-400 tracking-widest">Cochrane RoB-2 (per-domain traffic light)</h4>
                        <button onclick="window.Rob2TrafficLight && window.Rob2TrafficLight.render('#rob2Widget')"
                            style="padding:4px 10px;background:#0891b2;color:#fff;border:none;border-radius:4px;font-size:10px;font-weight:700;cursor:pointer;">
                            Render
                        </button>
                    </div>
                    <div id="rob2Widget"><span style="color:#64748b;font-size:11px;font-style:italic;">Click "Render" to see RoB-2 status across all trials. Stub-only state (default 'low' across all 5 domains) is flagged for completion.</span></div>
                </div>
                '''


def patch(text):
    if 'vendor/rob2-traffic-light.js' in text:
        return text, "ALREADY"
    om = OS_INCLUDE_RE.search(text)
    if om:
        text = text[:om.end()] + SCRIPT_TAG + text[om.end():]
    else:
        head = text.find("</head>")
        if head < 0:
            return text, "NO_HEAD"
        text = text[:head] + SCRIPT_TAG + text[head:]
    new_text, n = OS_PANEL_RE.subn(r'\1' + PANEL, text, count=1)
    if n == 0:
        return text, "NO_OS_PANEL"
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
