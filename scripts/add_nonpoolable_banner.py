"""Add an honest 'not a pooled meta-analysis' banner to non-poolable AUTO apps.

After harmonization each realData outcome carries a per-cluster shortLabel.
An app is non-poolable when NO shortLabel is shared by >=2 trials (i.e. every
outcome is a single-trial summary). For those apps, inject a banner at the top
of the analysis tab making the limitation explicit.

Wording acknowledges the automated endpoint-matching (the matcher has known
false-negatives on synonym endpoints), so it never over-claims.

Idempotent (skips if banner present), --dry-run, jscheck-gated auto-revert.
"""
from __future__ import annotations
import argparse, glob, io, os, re, sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

if hasattr(sys.stdout, "buffer") and getattr(sys.stdout, "encoding", "").lower() != "utf-8":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MARKER = "rm-nonpool-banner"
ANCHOR = re.compile(r'(<section id="tab-analysis"[^>]*>)')

BANNER = (
    '<div class="' + MARKER + '" style="background:#42210b;border:1px solid #b45309;'
    'color:#fed7aa;padding:11px 15px;border-radius:10px;margin-bottom:18px;'
    'font-size:13px;line-height:1.55">'
    '<strong>⚠ Not a pooled meta-analysis.</strong> '
    'Automated endpoint-matching found no outcome with ≥2 included trials '
    'reporting the same endpoint, so each outcome below is a single-trial '
    'summary rather than a pooled estimate. If trials do share an endpoint, '
    'verify and pool manually.'
    '</div>'
)

_SL_RE = re.compile(r"\{\s*shortLabel:\s*(['\"])((?:\\.|(?!\1).)*)\1")


def is_nonpoolable(html):
    counts = {}
    for m in _SL_RE.finditer(html):
        k = m.group(2)
        counts[k] = counts.get(k, 0) + 1
    if not counts:
        return False  # unknown structure -> don't touch
    return max(counts.values()) < 2


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--glob", default="*_AUTO*_FULL_REVIEW.html")
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--limit", type=int, default=0)
    args = ap.parse_args()

    try:
        import jscheck
    except Exception:
        jscheck = None

    files = sorted(glob.glob(os.path.join(HERE, args.glob)))
    if args.limit:
        files = files[:args.limit]
    added = skipped_pool = skipped_done = no_anchor = reverted = 0
    for f in files:
        html = io.open(f, encoding="utf-8", errors="replace").read()
        if MARKER in html:
            skipped_done += 1
            continue
        if not is_nonpoolable(html):
            skipped_pool += 1
            continue
        new, n = ANCHOR.subn(lambda m: m.group(1) + BANNER, html, count=1)
        if n == 0:
            no_anchor += 1
            continue
        if args.dry_run:
            added += 1
            continue
        io.open(f, "w", encoding="utf-8", newline="").write(new)
        if jscheck is not None and jscheck.check(f):
            io.open(f, "w", encoding="utf-8", newline="").write(html)
            reverted += 1
            continue
        added += 1

    print(f"{'DRY-RUN' if args.dry_run else 'APPLIED'}")
    print(f"  banner added      : {added}")
    print(f"  skipped (poolable): {skipped_pool}")
    print(f"  skipped (has banner): {skipped_done}")
    print(f"  no analysis anchor : {no_anchor}")
    print(f"  reverted (jscheck) : {reverted}")


if __name__ == "__main__":
    main()
