"""Python wrapper that runs R metafor cross-validation on every single-arm
proportion review.

A "single-arm review" is one whose realData contains ≥2 trials where:
  - t.cN ∈ {None, 0, ''}     (no comparator arm)
  - t.tE, t.tN finite, tN > 0, tE ≤ tN

Idempotent. Outputs to outputs/r_validation/singlearm/<REVIEW>.json
"""
from __future__ import annotations
import io, json, os, shutil, subprocess, sys
from pathlib import Path

if sys.platform == "win32" and hasattr(sys.stdout, "buffer"):
    try:
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    except Exception:
        pass

REPO = Path(__file__).resolve().parent.parent
DATA_DIR = REPO / "outputs" / "extraction_audit" / "data"
OUT_DIR = REPO / "outputs" / "r_validation" / "singlearm"
OUT_DIR.mkdir(parents=True, exist_ok=True)
R_SCRIPT = REPO / "scripts" / "r_validate_singlearm.R"
# P0-5 fix: env var → PATH lookup → hardcoded fallback. Portable across
# Linux/Mac/CI and survives R-version upgrades.
RSCRIPT_EXE = (
    os.environ.get("RSCRIPT_EXE")
    or shutil.which("Rscript")
    or r"C:\Program Files\R\R-4.5.2\bin\Rscript.exe"
)


def pick_singlearm_trials(rd: dict) -> list[dict]:
    """Match vendor/single-arm-proportion.js variant-4 logic: tE/tN present,
    cN/cE missing or 0."""
    out = []
    for nct, t in (rd or {}).items():
        if not isinstance(t, dict):
            continue
        tE, tN, cN, cE = t.get("tE"), t.get("tN"), t.get("cN"), t.get("cE")
        if not (isinstance(tE, (int, float)) and isinstance(tN, (int, float))):
            continue
        if not (tN > 0 and tE >= 0 and tE <= tN):
            continue
        if not (cN in (None, 0, "", 0.0) and cE in (None, 0, "", 0.0)):
            continue
        out.append({"studlab": t.get("name") or nct, "e": int(tE), "n": int(tN)})
    return out


def main() -> None:
    index = json.loads((DATA_DIR / "_index.json").read_text(encoding="utf-8"))
    candidates = []
    for entry in index:
        if not entry.get("has_realData"):
            continue
        stem = entry["stem"]
        doc = json.loads((DATA_DIR / f"{stem}.json").read_text(encoding="utf-8"))
        rd = doc.get("realData") or {}
        trials = pick_singlearm_trials(rd)
        if len(trials) >= 2:
            candidates.append((stem, trials))

    print(f"Single-arm review candidates: {len(candidates)}")
    n_ok, n_fail = 0, 0
    for stem, trials in candidates:
        input_path  = OUT_DIR / f"{stem}.input.json"
        output_path = OUT_DIR / f"{stem}.json"
        input_path.write_text(json.dumps({"review": stem, "trials": trials},
                                          indent=2), encoding="utf-8")
        try:
            r = subprocess.run(
                [RSCRIPT_EXE, str(R_SCRIPT), str(input_path), str(output_path)],
                capture_output=True, text=True, timeout=90,
            )
        except subprocess.TimeoutExpired:
            print(f"  {stem}: ✗ timeout"); n_fail += 1; continue
        if r.returncode != 0:
            print(f"  {stem}: ✗ exit {r.returncode}: {r.stderr.strip()[:200]}")
            n_fail += 1; continue
        result = json.loads(output_path.read_text(encoding="utf-8"))
        if result.get("fit_ok"):
            lp = result.get("logit_pool") or {}
            pool = (lp.get("pool") or 0) * 100
            lci = (lp.get("lci") or 0) * 100
            uci = (lp.get("uci") or 0) * 100
            i2 = lp.get("I2") or 0
            print(f"  {stem}: ✓ k={result['k']} prop={pool:.1f}% [{lci:.1f}–{uci:.1f}%] I²={i2:.0f}%")
            n_ok += 1
        else:
            print(f"  {stem}: ⚠ {result.get('error')}")
            n_fail += 1
    print(f"\nOK: {n_ok}  failed: {n_fail}")


if __name__ == "__main__":
    main()
