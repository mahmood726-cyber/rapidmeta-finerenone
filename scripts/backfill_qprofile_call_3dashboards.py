"""
Targeted backfill: insert Q-profile tau2 CI call site into the three
v6.5-non-compliant dashboards identified by audit_v65_engine_coverage.py
(2026-04-30).

These three dashboards (COLCHICINE_CVD, GLP1_CVOT, SGLT2_HF) ship the
qProfileTau2CI helper (defined as `const qProfileTau2CI = (yi, vi, df,
alpha) => { ... }`) but never invoke it. The result is silent: the
engine's REML primary point estimate renders fine, but the tau2
confidence interval the v6.5 / RevMan-2025 reproducibility checklist
mandates is never computed and never displayed.

Patch (each dashboard):
  1. After `const tau2 = (k >= 2) ? tau2_reml : tau2_dl;`, insert the
     three-line Q-profile call.
  2. Add `tau2Lo, tau2Hi` to the engine's published-ratio return
     object (the one ending with `fragQuot: '--', fragilityNA: true`).

Idempotent: skips a file if `qProfileTau2CI(_qpYi` already present.

The companion V8/MH-pool gap is NOT addressed here -- the older engine
in those three dashboards lacks `_petoPool` / `_remlHksjPool` anchors
the standard add_mh_pool.py needs. Tracked separately as a re-clone
task in outputs/reverification_triage.md (REM-ENG-1 part 2).

Usage:
  python scripts/backfill_qprofile_call_3dashboards.py
  python scripts/backfill_qprofile_call_3dashboards.py --dry-run
"""
from __future__ import annotations

import argparse
import io
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
TARGETS = [
    ROOT / "COLCHICINE_CVD_REVIEW.html",
    ROOT / "GLP1_CVOT_REVIEW.html",
    ROOT / "SGLT2_HF_REVIEW.html",
]

# Patch 1: insert Q-profile call after REML primary line.
# Spacing is the dashboards' double-blank-line convention.
ANCHOR_REML = (
    "                // Primary tau2 = REML when k>=2 (Cochrane v6.5 default), else DL.\n"
    "                const tau2 = (k >= 2) ? tau2_reml : tau2_dl;\n"
    "\n"
    "\n"
    "                let sWR = 0, sWRY = 0;"
)
REPLACEMENT_REML = (
    "                // Primary tau2 = REML when k>=2 (Cochrane v6.5 default), else DL.\n"
    "                const tau2 = (k >= 2) ? tau2_reml : tau2_dl;\n"
    "\n"
    "\n"
    "                // Q-profile tau2 CI (Cochrane v6.5 / RevMan-2025: Viechtbauer 2007).\n"
    "                const _qpYi = plotData.map(d => d.logOR);\n"
    "                const _qpVi = plotData.map(d => d.vi);\n"
    "                const { tau2_lo: tau2Lo, tau2_hi: tau2Hi } = qProfileTau2CI(_qpYi, _qpVi, df, 1 - confLevel);\n"
    "\n"
    "\n"
    "                let sWR = 0, sWRY = 0;"
)

# Patch 2: thread tau2Lo, tau2Hi through the published-ratio engine
# return object so the stat card can render them.
ANCHOR_RETURN = (
    "                    plotData, Q, k, df, I2, tau2, sWR, pLogOR, pSE, confLevel, zCrit, pOR, lci, uci,\n"
    "\n"
    "\n"
    "                    hksjLCI, hksjUCI, piLCI, piUCI, qPvalue, eggerResult, fragIdx: 0, fragQuot: '--', fragilityNA: true"
)
REPLACEMENT_RETURN = (
    "                    plotData, Q, k, df, I2, tau2, tau2Lo, tau2Hi, sWR, pLogOR, pSE, confLevel, zCrit, pOR, lci, uci,\n"
    "\n"
    "\n"
    "                    hksjLCI, hksjUCI, piLCI, piUCI, qPvalue, eggerResult, fragIdx: 0, fragQuot: '--', fragilityNA: true"
)

# Idempotency sentinel: if the dashboard already has the call site, skip.
SENTINEL = "qProfileTau2CI(_qpYi"


def patch_one(path: Path, dry_run: bool) -> dict:
    text = path.read_text(encoding="utf-8")
    result = {"file": path.name, "status": "unknown", "changes": []}

    if SENTINEL in text:
        result["status"] = "already_patched"
        return result

    if ANCHOR_REML not in text:
        result["status"] = "anchor_missing_reml"
        return result
    if ANCHOR_RETURN not in text:
        result["status"] = "anchor_missing_return"
        return result

    new_text = text.replace(ANCHOR_REML, REPLACEMENT_REML, 1)
    result["changes"].append("REML+Qprofile call inserted")
    new_text = new_text.replace(ANCHOR_RETURN, REPLACEMENT_RETURN, 1)
    result["changes"].append("tau2Lo, tau2Hi added to return object")

    if not dry_run:
        path.write_text(new_text, encoding="utf-8", newline="")
    result["status"] = "patched"
    return result


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    if hasattr(sys.stdout, "buffer"):
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace", line_buffering=True)

    print("Mode:", "DRY-RUN" if args.dry_run else "WRITE")
    for path in TARGETS:
        if not path.exists():
            print(f"  MISSING: {path}")
            continue
        r = patch_one(path, dry_run=args.dry_run)
        print(f"  {r['file']:42} {r['status']:24} {' / '.join(r['changes'])}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
