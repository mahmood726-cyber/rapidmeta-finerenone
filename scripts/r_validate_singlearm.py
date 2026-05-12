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

# P1-3 fix: only wrap stdout once; idempotent against multiple imports.
if (sys.platform == "win32"
    and hasattr(sys.stdout, "buffer")
    and getattr(sys.stdout, "encoding", "").lower() != "utf-8"):
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

# P1-7 fix: path-traversal guard. stem comes from _index.json; refuse any
# value with path separators, ".." segments, or non-[A-Za-z0-9_-.] chars.
import re as _re_p17
_STEM_OK = _re_p17.compile(r"^[A-Za-z0-9_.-]+$")
def _stem_safe(s) -> bool:
    return isinstance(s, str) and bool(_STEM_OK.match(s)) and ".." not in s


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
    # P1-1/2/4/5 fix: shared runner with idempotency, parallelism, stderr
    # persistence, and schema validation.
    from r_validate_common import (hash_input, already_validated, write_sidecar,
                                    parallel_run, validate_index_entry,
                                    validate_r_output)
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--force", action="store_true", help="rerun even if sha matches")
    ap.add_argument("--max-workers", type=int, default=4)
    args = ap.parse_args()

    index = json.loads((DATA_DIR / "_index.json").read_text(encoding="utf-8"))
    candidates = []
    n_invalid = 0
    for entry in index:
        if not validate_index_entry(entry):  # P1-5 schema
            n_invalid += 1
            continue
        if not entry.get("has_realData"):
            continue
        stem = entry["stem"]
        doc = json.loads((DATA_DIR / f"{stem}.json").read_text(encoding="utf-8"))
        rd = doc.get("realData") or {}
        trials = pick_singlearm_trials(rd)
        if len(trials) >= 2:
            candidates.append((stem, trials))

    print(f"Single-arm review candidates: {len(candidates)}  invalid-index: {n_invalid}")
    jobs, deferred_results, skipped_idempotent = [], [], 0
    for stem, trials in candidates:
        input_path  = OUT_DIR / f"{stem}.input.json"
        output_path = OUT_DIR / f"{stem}.json"
        sha_sidecar = OUT_DIR / f"{stem}.input.sha256"
        error_log   = OUT_DIR / f"{stem}.error.log"
        payload = {"review": stem, "trials": trials}
        expected_sha = hash_input(payload, R_SCRIPT)
        if not args.force and already_validated(output_path, sha_sidecar, expected_sha):
            skipped_idempotent += 1; deferred_results.append((stem, None, True)); continue
        input_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
        jobs.append((R_SCRIPT, input_path, output_path, error_log))
        deferred_results.append((stem, sha_sidecar, expected_sha))

    if jobs:
        print(f"  running {len(jobs)} job(s) on {args.max_workers}-worker pool  "
              f"(skipped {skipped_idempotent} idempotent)")
        results = parallel_run(jobs, max_workers=args.max_workers)
    else:
        results = []
        print(f"  all {skipped_idempotent} jobs idempotent — nothing to run")

    n_ok = 0
    n_fail = 0
    res_iter = iter(results)
    for stem, sidecar, sha_or_done in deferred_results:
        if sha_or_done is True:
            n_ok += 1; continue  # already-validated cache hit
        r = next(res_iter)
        output_path = OUT_DIR / f"{stem}.json"
        if not r["ok"]:
            print(f"  {stem}: [FAIL] exit {r['exit']}: {r['stderr'].strip()[:200]}")
            n_fail += 1; continue
        try:
            result = json.loads(output_path.read_text(encoding="utf-8"))
        except Exception as e:
            print(f"  {stem}: [FAIL] parse: {e}"); n_fail += 1; continue
        if not validate_r_output(result):  # P1-5
            print(f"  {stem}: [FAIL] schema mismatch"); n_fail += 1; continue
        write_sidecar(sidecar, sha_or_done)
        if result.get("fit_ok"):
            lp = result.get("logit_pool") or {}
            pool = (lp.get("pool") or 0) * 100
            lci = (lp.get("lci") or 0) * 100
            uci = (lp.get("uci") or 0) * 100
            i2 = lp.get("I2") or 0
            print(f"  {stem}: [OK] k={result['k']} prop={pool:.1f}% [{lci:.1f}-{uci:.1f}%] I2={i2:.0f}%")
            n_ok += 1
        else:
            print(f"  {stem}: [WARN] {result.get('error')}")
            n_fail += 1
    print(f"\nOK: {n_ok}  failed: {n_fail}  (idempotent-skipped: {skipped_idempotent})")
    sys.exit(1 if n_fail else 0)


if __name__ == "__main__":
    main()
