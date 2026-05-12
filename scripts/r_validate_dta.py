"""Python wrapper that runs R mada::reitsma cross-validation on each DTA review.

For each *_DTA_REVIEW.html in the repo:
  1. Extract the JSON from <script type="application/json" id="dta-trials">
  2. Build the trials array (primary_tier ∪ sensitivity_tier_added)
  3. Write input JSON to outputs/r_validation/dta/<REVIEW>.input.json
  4. Call Rscript scripts/r_validate_dta.R
  5. Save result to outputs/r_validation/dta/<REVIEW>.json

Idempotent.
"""
from __future__ import annotations
import io, json, re, subprocess, sys
from pathlib import Path

if sys.platform == "win32" and hasattr(sys.stdout, "buffer"):
    try:
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    except Exception:
        pass

REPO = Path(__file__).resolve().parent.parent
OUT_DIR = REPO / "outputs" / "r_validation" / "dta"
OUT_DIR.mkdir(parents=True, exist_ok=True)
R_SCRIPT = REPO / "scripts" / "r_validate_dta.R"
# P0-5 fix: env var → PATH lookup → hardcoded fallback.
import os as _os, shutil as _shutil
RSCRIPT_EXE = (
    _os.environ.get("RSCRIPT_EXE")
    or _shutil.which("Rscript")
    or r"C:\Program Files\R\R-4.5.2\bin\Rscript.exe"
)

DTA_JSON_RE = re.compile(
    r'<script\s+type="application/json"\s+id="dta-trials"\s*>(.*?)</script>',
    re.DOTALL,
)

# P1-7 fix: path-traversal guard.
import re as _re_p17
_STEM_OK = _re_p17.compile(r"^[A-Za-z0-9_.-]+$")
def _stem_safe(s) -> bool:
    return isinstance(s, str) and bool(_STEM_OK.match(s)) and ".." not in s


def extract_dta_trials(html_path: Path) -> dict | None:
    text = html_path.read_text(encoding="utf-8", errors="replace")
    m = DTA_JSON_RE.search(text)
    if not m:
        return None
    try:
        data = json.loads(m.group(1))
    except json.JSONDecodeError as e:
        print(f"  {html_path.name}: JSON parse error: {e}")
        return None
    trials = []
    for tier_key in ("primary_tier", "sensitivity_tier_added", "sensitivity_tier"):
        for t in (data.get(tier_key) or []):
            if all(k in t for k in ("TP", "FP", "FN", "TN")):
                trials.append({
                    "studlab": t.get("studlab") or t.get("name") or "?",
                    "TP": int(t["TP"]),
                    "FP": int(t["FP"]),
                    "FN": int(t["FN"]),
                    "TN": int(t["TN"]),
                    "tier": tier_key,
                })
    return {"review": html_path.stem, "trials": trials} if trials else None


def run_rscript(input_path: Path, output_path: Path) -> tuple[bool, str]:
    try:
        result = subprocess.run(
            [RSCRIPT_EXE, str(R_SCRIPT), str(input_path), str(output_path)],
            capture_output=True, text=True, timeout=120,
        )
    except subprocess.TimeoutExpired:
        return False, "timeout"
    except FileNotFoundError:
        return False, f"Rscript not found at {RSCRIPT_EXE}"
    if result.returncode != 0:
        return False, f"exit {result.returncode}: {result.stderr.strip()[:300]}"
    return output_path.exists(), result.stdout.strip()


def main() -> None:
    dta_files = sorted(REPO.glob("*_DTA_REVIEW.html"))
    print(f"Found {len(dta_files)} DTA reviews")
    n_ok, n_skip, n_fail = 0, 0, 0
    for hp in dta_files:
        stem = hp.stem
        extracted = extract_dta_trials(hp)
        if not extracted:
            print(f"  {stem}: no DTA trial JSON found — skip")
            n_skip += 1
            continue
        if len(extracted["trials"]) < 4:
            print(f"  {stem}: only k={len(extracted['trials'])} trials — reitsma needs k≥4")
            n_skip += 1
            continue
        input_path  = OUT_DIR / f"{stem}.input.json"
        output_path = OUT_DIR / f"{stem}.json"
        input_path.write_text(json.dumps(extracted, indent=2), encoding="utf-8")
        ok, msg = run_rscript(input_path, output_path)
        if ok:
            result = json.loads(output_path.read_text(encoding="utf-8"))
            if result.get("fit_ok"):
                print(f"  {stem}: [OK] k={result['k']} Se={result['sens_pool']:.3f} "
                      f"Sp={result['spec_pool']:.3f} DOR={result['dor']:.1f} AUC={result.get('auc',0):.3f}")
                n_ok += 1
            else:
                print(f"  {stem}: [WARN] fit failed — {result.get('error')}")
                n_fail += 1
        else:
            print(f"  {stem}: [FAIL] Rscript failed: {msg}")
            n_fail += 1
    print(f"\nOK: {n_ok}  skipped: {n_skip}  failed: {n_fail}")


if __name__ == "__main__":
    main()
