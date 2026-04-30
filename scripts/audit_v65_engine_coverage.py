"""
Portfolio reverification: Cochrane v6.5 / RevMan-2025 engine coverage.

Mirrors the Sentinel `cochrane_v65_invariants.py` rule but emits a
per-dashboard coverage matrix CSV instead of WARN findings. Lets you see
at a glance which of the 170 dashboards already carry the v6.5
invariants and which still need backfill -- so we can finish hardening
the existing portfolio before adding new topics.

Eight invariants checked (same set as Sentinel rule):
  V1. REML iteration   (`tau2_reml`)
  V2. REML primary     (`const tau2_dl =` + `tau2 = (k >= 2) ? tau2_reml`)
  V3. Q-profile tau2   (`qProfileTau2CI(`)
  V4. qchisq low-df    (`qchisq` + `df === 1`)
  V5. HKSJ floor       (`Math.max(1, qStar)`)
  V6. PI df=k-1        (`// PI df = k-1 per Cochrane Handbook v6.5`)
  V7. ROB-ME           (`_assessROBME(`)
  V8. MH pool          (`_mhPool(`)

Pairwise *_REVIEW.html dashboards expected to satisfy all eight.
DTA *_DTA_REVIEW.html dashboards loaded from rapidmeta-dta-engine-v1.js
are skipped (different engine; separate Sentinel rule).
"""
from __future__ import annotations

import argparse
import csv
import io
import sys
from pathlib import Path

ROOT = Path(r"C:\Projects\Finrenone")
DEFAULT_CSV = ROOT / "outputs" / "v65_engine_coverage.csv"

CHECKS = [
    ("V1_REML_iter",     ["tau2_reml"]),
    ("V2_REML_primary",  ["const tau2_dl =", "const tau2 = (k >= 2) ? tau2_reml"]),
    ("V3_Qprofile_tau2", ["qProfileTau2CI("]),
    ("V4_qchisq_lowdf",  ["qchisq", "df === 1"]),
    ("V5_HKSJ_floor",    ["Math.max(1, qStar)"]),
    ("V6_PI_df_kminus1", ["// PI df = k-1 per Cochrane Handbook v6.5"]),
    ("V7_ROBME",         ["_assessROBME("]),
    ("V8_MH_pool",       ["_mhPool("]),
]


def is_pairwise_dashboard(text: str, name: str) -> bool:
    if name.endswith("_DTA_REVIEW.html"):
        return False
    return ("realData:" in text) or ("realData =" in text)


def check_file(path: Path) -> dict:
    try:
        text = path.read_text(encoding="utf-8", errors="replace")
    except Exception:
        return {"dashboard": path.name, "skipped": "read_error"}

    if not is_pairwise_dashboard(text, path.name):
        return {"dashboard": path.name, "skipped": "not_pairwise_engine"}

    row = {"dashboard": path.name}
    failed: list[str] = []
    for label, needles in CHECKS:
        ok = all(n in text for n in needles)
        row[label] = "ok" if ok else "FAIL"
        if not ok:
            failed.append(label)
    row["fail_count"] = len(failed)
    row["failed"] = ";".join(failed)
    return row


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--csv", type=Path, default=DEFAULT_CSV)
    ap.add_argument("--root", type=Path, default=ROOT)
    args = ap.parse_args()

    if hasattr(sys.stdout, "buffer"):
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace", line_buffering=True)

    dashboards = sorted(p for p in args.root.glob("*_REVIEW.html") if p.is_file())

    rows: list[dict] = []
    skipped_dta = 0
    for p in dashboards:
        r = check_file(p)
        if r.get("skipped") == "not_pairwise_engine":
            skipped_dta += 1
            continue
        if "skipped" in r:
            continue
        rows.append(r)

    args.csv.parent.mkdir(parents=True, exist_ok=True)
    fields = ["dashboard"] + [c[0] for c in CHECKS] + ["fail_count", "failed"]
    with args.csv.open("w", encoding="utf-8", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=fields)
        w.writeheader()
        w.writerows(rows)

    total = len(rows)
    fully_compliant = sum(1 for r in rows if r["fail_count"] == 0)
    partial = sum(1 for r in rows if 0 < r["fail_count"] < len(CHECKS))
    none = sum(1 for r in rows if r["fail_count"] == len(CHECKS))

    print(f"{len(dashboards)} dashboards on disk")
    print(f"  pairwise engine (audited): {total}")
    print(f"  DTA / non-pairwise (skipped): {skipped_dta}")
    print(f"")
    print(f"v6.5 invariant compliance:")
    print(f"  fully compliant (8/8):     {fully_compliant}")
    print(f"  partial (1-7 missing):     {partial}")
    print(f"  none (all 8 missing):      {none}")
    print(f"")
    print(f"Per-check failure counts:")
    for label, _ in CHECKS:
        n_fail = sum(1 for r in rows if r.get(label) == "FAIL")
        print(f"  {label:24} FAIL: {n_fail}")

    print(f"")
    print(f"CSV written: {args.csv}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
