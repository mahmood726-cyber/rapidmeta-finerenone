"""Inject ROB-NMA + Transitivity matrix panels into NMA reviews. Idempotent."""
from __future__ import annotations
import sys, io, argparse, re
from pathlib import Path
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

REPO = Path(__file__).resolve().parent.parent

OUTCOME_INCLUDE_RE = re.compile(r'<script\s+src="vendor/outcome-switching\.js"\s*></script>')

SCRIPT_TAG = (
    '\n    <!-- ROB-NMA (Lunny 2025) + Transitivity matrix (Brignardello-Petersen 2023 / Lasch 2025) -->\n'
    '    <script src="vendor/rob-nma.js"></script>\n'
    '    <script src="vendor/transitivity-matrix.js"></script>\n'
)

# Inject after the consistency panel which is in the NMA tab
CONSISTENCY_END_RE = re.compile(
    r'(<div id="nmaConsResult"></div>\s*</div>)'
)

PANEL = '''

                            <div class="glass p-10 rounded-[40px] border border-slate-800 mt-10">
                                <h3 class="text-sm font-bold opacity-60 uppercase tracking-[0.3em] mb-2">ROB-NMA + Transitivity (Cochrane 2025)</h3>
                                <p class="text-[11px] text-slate-400 mb-4">
                                    Lunny 2025 BMJ ROB-NMA tool (17 items, 3 domains) with auto-prefill from existing modules + transitivity effect-modifier balance per Brignardello-Petersen 2023 GRADE-NMA Article 5 / Lasch 2025 Res Synth Methods.
                                </p>
                                <div style="display:flex;gap:10px;margin-bottom:14px;">
                                    <button onclick="window.RobNma && window.RobNma.render('#robNmaResult')"
                                        style="padding:6px 14px;background:#0891b2;color:#fff;border:none;border-radius:6px;font-size:11px;font-weight:700;cursor:pointer;">
                                        Run ROB-NMA assessment
                                    </button>
                                    <button onclick="window.TransitivityMatrix && window.TransitivityMatrix.render('#transitivityResult')"
                                        style="padding:6px 14px;background:#7c3aed;color:#fff;border:none;border-radius:6px;font-size:11px;font-weight:700;cursor:pointer;">
                                        Transitivity matrix
                                    </button>
                                </div>
                                <div id="robNmaResult" style="margin-bottom:14px;"></div>
                                <div id="transitivityResult"></div>
                            </div>
                            '''


def patch(text):
    if 'vendor/rob-nma.js' in text:
        return text, "ALREADY"
    om = OUTCOME_INCLUDE_RE.search(text)
    if om:
        text = text[:om.end()] + SCRIPT_TAG + text[om.end():]
    else:
        head = text.find("</head>")
        if head < 0:
            return text, "NO_HEAD"
        text = text[:head] + SCRIPT_TAG + text[head:]
    new_text, n = CONSISTENCY_END_RE.subn(r'\1' + PANEL, text, count=1)
    if n == 0:
        return text, "NO_CONSISTENCY_PANEL"
    return new_text, "PATCHED"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    files = sorted(REPO.glob("*_NMA_REVIEW.html"))
    print(f"Patching {len(files)} *_NMA_REVIEW.html files ...")
    counts = {}
    for hp in files:
        text = hp.read_text(encoding="utf-8", errors="replace")
        new_text, status = patch(text)
        counts[status] = counts.get(status, 0) + 1
        if status == "PATCHED" and not args.dry_run:
            hp.write_text(new_text, encoding="utf-8")

    print(f"\n=== Summary ===")
    for k, v in sorted(counts.items(), key=lambda x: -x[1]):
        print(f"  {k:30s} {v}")
    if args.dry_run:
        print("  DRY RUN.")


if __name__ == "__main__":
    main()
