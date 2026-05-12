"""Python wrapper that runs R dosresmeta cross-validation on a single
dose-response review.

Usage:
  python scripts/r_validate_doseresp.py --review <REVIEW_NAME>

Inputs:
  tests/dose_response_fixtures/<REVIEW>.json

Outputs:
  outputs/r_validation/doseresp/<REVIEW>.input.json
  outputs/r_validation/doseresp/<REVIEW>.json

Exit codes:
  0 = success
  2 = fixture missing/empty or invalid --review argument
  3 = R script timeout
  4 = R script non-zero exit
  5 = R did not write the expected output JSON
"""
from __future__ import annotations
import argparse, io, json, os, re, shutil, subprocess, sys
from pathlib import Path

if sys.platform == "win32" and hasattr(sys.stdout, "buffer"):
    try:
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    except Exception:
        pass

REPO = Path(__file__).resolve().parent.parent
OUT_DIR = REPO / "outputs" / "r_validation" / "doseresp"
OUT_DIR.mkdir(parents=True, exist_ok=True)
R_SCRIPT = REPO / "scripts" / "r_validate_doseresp.R"
RSCRIPT_EXE = (
    os.environ.get("RSCRIPT_EXE")
    or shutil.which("Rscript")
    or r"C:\Program Files\R\R-4.5.2\bin\Rscript.exe"
)
FIXTURE_DIR = REPO / "tests" / "dose_response_fixtures"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--review", required=True,
                        help="Fixture stem (e.g. gl1992_alcohol_bc)")
    args = parser.parse_args()
    if not re.fullmatch(r'[A-Za-z0-9_\-]+', args.review):
        print(f"ERROR: --review must be alphanumeric + underscore + hyphen only (got: {args.review!r})", file=sys.stderr)
        return 2

    fixture_path = FIXTURE_DIR / f"{args.review}.json"
    if not fixture_path.exists():
        print(f"ERROR: fixture not found: {fixture_path}", file=sys.stderr)
        return 2

    fx = json.loads(fixture_path.read_text(encoding="utf-8"))
    trials = fx.get("trials", [])
    if not trials:
        print(f"ERROR: fixture has no trials: {fixture_path}", file=sys.stderr)
        return 2

    input_path  = OUT_DIR / f"{args.review}.input.json"
    output_path = OUT_DIR / f"{args.review}.json"
    input_path.write_text(json.dumps({"review": args.review, "trials": trials},
                                      indent=2), encoding="utf-8")

    try:
        r = subprocess.run(
            [RSCRIPT_EXE, str(R_SCRIPT), str(input_path), str(output_path)],
            capture_output=True, text=True, timeout=120,
        )
    except subprocess.TimeoutExpired:
        print(f"{args.review}: timeout"); return 3

    if r.returncode != 0:
        print(f"{args.review}: exit {r.returncode}\nstderr: {r.stderr.strip()[:500]}")
        return 4

    if not output_path.exists():
        print(f"{args.review}: R did not write {output_path}"); return 5

    result = json.loads(output_path.read_text(encoding="utf-8"))
    print(f"{args.review}: OK — linear={result.get('linear',{}).get('fit_ok')}, "
          f"rcs={result.get('rcs',{}).get('fit_ok')}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
