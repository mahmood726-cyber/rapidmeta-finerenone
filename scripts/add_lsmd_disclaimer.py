"""
REM-CONT-1: append a single LSMD/MMRM-transparency clause to the PICO
`out` field of dashboards whose continuous outcomes lack an analytic-
method declaration.

The continuous-conventions audit (audit_continuous_conventions.py)
flagged 81/92 outcomes across 27 dashboards as LSMD_NOT_DECLARED:
their title says "change from baseline" but does not name the
analytic method. A reader cannot tell from the dashboard alone
whether the pooled `md` is a raw arithmetic difference or a
model-adjusted estimate.

Per-outcome editing of titles requires trial-by-trial knowledge of
the published analytic method (MMRM vs ANCOVA vs LSMD). That is
manual work for ~80 outcomes. The conservative blanket fix this
script applies: append a short disclaimer to the dashboard's PICO
`out` field stating that pooled MDs reflect the trial-published
primary analytic method (typically LSMD via MMRM or ANCOVA-adjusted
change from baseline) and that per-trial details live in each trial's
snippet.

Disclaimer is appended exactly once per dashboard. Idempotent: skips
if the sentinel phrase is already present.

Usage:
  python scripts/add_lsmd_disclaimer.py [--dry-run]
"""
from __future__ import annotations

import argparse
import io
import re
import sys
from pathlib import Path

ROOT = Path(r"C:\Projects\Finrenone")

TARGETS = [
    "AFLIBERCEPT_HD_REVIEW.html",
    "ALDO_SYNTHASE_NMA_REVIEW.html",
    "ANTIAMYLOID_AD_REVIEW.html",
    "ARNI_HF_REVIEW.html",
    "ATTR_PN_NMA_REVIEW.html",
    "CFTR_CF_REVIEW.html",
    "CGRP_MIGRAINE_REVIEW.html",
    "COPD_TRIPLE_REVIEW.html",
    "DELANDISTROGENE_DMD_REVIEW.html",
    "DUPILUMAB_COPD_REVIEW.html",
    "ENSIFENTRINE_COPD_REVIEW.html",
    "ESKETAMINE_TRD_REVIEW.html",
    "FARICIMAB_NAMD_REVIEW.html",
    "FEZOLINETANT_VMS_REVIEW.html",
    "INCLISIRAN_REVIEW.html",
    "INSULIN_ICODEC_REVIEW.html",
    "KARXT_SCZ_REVIEW.html",
    "MITAPIVAT_THALASSEMIA_REVIEW.html",
    "PATISIRAN_POLYNEUROPATHY_REVIEW.html",
    "PEGCETACOPLAN_GA_REVIEW.html",
    "RENAL_DENERV_REVIEW.html",
    "ROMOSOZUMAB_OP_REVIEW.html",
    "SEMAGLUTIDE_OBESITY_REVIEW.html",
    "TEPLIZUMAB_T1D_REVIEW.html",
    "TIRZEPATIDE_OBESITY_REVIEW.html",
    "TIRZEPATIDE_T2D_REVIEW.html",
    "ZURANOLONE_PPD_REVIEW.html",
]

DISCLAIMER = (
    # IMPORTANT: must be apostrophe-free. The PICO `out` field is a
    # single-quoted JS string literal (`out: '...'`). An unescaped
    # apostrophe (e.g. "trial's") terminates the string and breaks the
    # dashboard with `SyntaxError: Unexpected identifier`. Hot-fix
    # 2026-04-30 after the first version of this script broke 27 dashboards.
    " Pooled mean differences reflect the trial-published primary "
    "analytic method (typically LSMD via MMRM or ANCOVA-adjusted change "
    "from baseline; see per-trial snippet for the trial-specific model)."
)
SENTINEL = "Pooled mean differences reflect the trial-published primary"

PROTOCOL_RE = re.compile(
    r"(protocol:\s*\{\s*pop:\s*'(?:[^'\\]|\\.)*',\s*int:\s*'(?:[^'\\]|\\.)*',\s*comp:\s*'(?:[^'\\]|\\.)*',\s*out:\s*')((?:[^'\\]|\\.)*?)(')"
)


def patch_one(path: Path, dry_run: bool) -> dict:
    text = path.read_text(encoding="utf-8")
    if SENTINEL in text:
        return {"file": path.name, "status": "already_patched", "edits": 0}

    m = PROTOCOL_RE.search(text)
    if not m:
        return {"file": path.name, "status": "anchor_missing", "edits": 0}

    new_out = m.group(2) + DISCLAIMER
    new_text = text[:m.start(2)] + new_out + text[m.end(2):]
    if not dry_run:
        path.write_text(new_text, encoding="utf-8", newline="")
    return {"file": path.name, "status": "patched", "edits": 1}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    if hasattr(sys.stdout, "buffer"):
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace", line_buffering=True)

    print("Mode:", "DRY-RUN" if args.dry_run else "WRITE")
    counts: dict[str, int] = {}
    for name in TARGETS:
        path = ROOT / name
        if not path.exists():
            print(f"  MISSING: {name}")
            counts["missing"] = counts.get("missing", 0) + 1
            continue
        r = patch_one(path, dry_run=args.dry_run)
        counts[r["status"]] = counts.get(r["status"], 0) + 1
        print(f"  {r['file']:42} {r['status']}")
    print(f"  totals: {counts}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
