"""Python wrapper that runs R metafor cross-validation on every review whose
primary outcome is continuous (mean difference or SMD).

Detection: ≥2 trials with an `allOutcomes[]` entry having both `md` and `se`
(modern shape), OR a CDR-SB/MMSE/ETDRS/etc. instrument label with `pubHR`/
`pubHR_LCI`/`pubHR_UCI` carrying MD + 95% CI (legacy shape).

Outputs to outputs/r_validation/continuous/<REVIEW>.json
"""
from __future__ import annotations
import io, json, math, os, re, shutil, subprocess, sys
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
OUT_DIR = REPO / "outputs" / "r_validation" / "continuous"
OUT_DIR.mkdir(parents=True, exist_ok=True)
R_SCRIPT = REPO / "scripts" / "r_validate_continuous.R"
# P0-5 fix: env var → PATH lookup → hardcoded fallback.
RSCRIPT_EXE = (
    os.environ.get("RSCRIPT_EXE")
    or shutil.which("Rscript")
    or r"C:\Program Files\R\R-4.5.2\bin\Rscript.exe"
)

# P1-7 fix: path-traversal guard.
import re as _re_p17
_STEM_OK = _re_p17.compile(r"^[A-Za-z0-9_.-]+$")
def _stem_safe(s) -> bool:
    return isinstance(s, str) and bool(_STEM_OK.match(s)) and ".." not in s

# Instrument labels that encode MD scale (must match vendor/nma-forest-continuous.js)
CONT_LABEL_RE = re.compile(
    r"^(CDR_?SB|CDR-?SB|MMSE|ADAS|PPF[Ee]V1|FEV1|BCVA|KCCQ|SF36|EQ5D|EQ-?5D|"
    r"ETDRS|HADS|PHQ|GAD|HRSD|MADRS|YBOCS|SLEDAI|UPDRS|MD|change|score)",
    re.IGNORECASE,
)


def _is_finite(x):
    return isinstance(x, (int, float)) and not isinstance(x, bool) and math.isfinite(x)


def collect_continuous_yi_vi(rd: dict) -> list[dict]:
    out = []
    for nct, t in (rd or {}).items():
        if not isinstance(t, dict):
            continue
        ao = t.get("allOutcomes") if isinstance(t.get("allOutcomes"), list) else None
        if not ao:
            continue
        yi = vi = None
        # Variant 1: explicit type='CONTINUOUS' with md+se
        for o in ao:
            if not isinstance(o, dict): continue
            if (o.get("type") or "").upper() == "CONTINUOUS" and _is_finite(o.get("md")) and _is_finite(o.get("se")) and o["se"] > 0:
                yi = float(o["md"]); vi = float(o["se"]) ** 2; break
        # Variant 2: instrument label + pubHR/pubHR_LCI/pubHR_UCI carrying MD.
        # P0-6 fix: require explicit MD/SMD scale signal — either o.scale set,
        # OR the value-pattern is unambiguously MD (negative, OR same-sign CI
        # with |value| > 1.5 which is implausible for a ratio measure).
        if yi is None:
            for o in ao:
                if not isinstance(o, dict): continue
                lab = o.get("shortLabel") or ""
                if not (CONT_LABEL_RE.match(lab) and
                        _is_finite(o.get("pubHR")) and
                        _is_finite(o.get("pubHR_LCI")) and
                        _is_finite(o.get("pubHR_UCI")) and
                        o["pubHR_UCI"] > o["pubHR_LCI"]):
                    continue
                # Scale-disambiguation gate
                explicit_scale = (o.get("scale") or "").upper()
                value = float(o["pubHR"])
                lci_v, uci_v = float(o["pubHR_LCI"]), float(o["pubHR_UCI"])
                is_md_unambiguous = (
                    explicit_scale in ("MD", "SMD") or
                    value < 0 or
                    lci_v < 0 or
                    abs(value) > 1.5  # ratio measures rarely exceed 1.5 on natural scale
                )
                if not is_md_unambiguous:
                    # Ambiguous (positive value in [0, 1.5], no explicit scale,
                    # both CI bounds positive) — could be HR/OR/RR. Skip to
                    # avoid mislabelling.
                    continue
                # back-compute SE from 95% CI on natural scale: (UCI-LCI)/3.92
                se = (uci_v - lci_v) / 3.92
                if se > 0:
                    yi = value; vi = se ** 2; break
        if yi is None:
            continue
        out.append({"studlab": t.get("name") or nct, "yi": yi, "vi": vi})
    return out


def main() -> None:
    # P1-1/2/4/5: idempotency + parallelism + stderr capture + schema validation.
    from r_validate_common import (hash_input, already_validated, write_sidecar,
                                    parallel_run, validate_index_entry,
                                    validate_r_output)
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--force", action="store_true")
    ap.add_argument("--max-workers", type=int, default=4)
    args = ap.parse_args()

    index = json.loads((DATA_DIR / "_index.json").read_text(encoding="utf-8"))
    candidates = []
    for entry in index:
        if not validate_index_entry(entry): continue
        if not entry.get("has_realData"): continue
        stem = entry["stem"]
        doc = json.loads((DATA_DIR / f"{stem}.json").read_text(encoding="utf-8"))
        rd = doc.get("realData") or {}
        trials = collect_continuous_yi_vi(rd)
        if len(trials) >= 2:
            candidates.append((stem, trials))

    print(f"Continuous-outcome review candidates: {len(candidates)}")
    jobs, deferred, skipped = [], [], 0
    for stem, trials in candidates:
        input_path  = OUT_DIR / f"{stem}.input.json"
        output_path = OUT_DIR / f"{stem}.json"
        sha_sidecar = OUT_DIR / f"{stem}.input.sha256"
        error_log   = OUT_DIR / f"{stem}.error.log"
        payload = {"review": stem, "scale": "MD", "trials": trials}
        expected_sha = hash_input(payload, R_SCRIPT)
        if not args.force and already_validated(output_path, sha_sidecar, expected_sha):
            skipped += 1; deferred.append((stem, None, True)); continue
        input_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
        jobs.append((R_SCRIPT, input_path, output_path, error_log))
        deferred.append((stem, sha_sidecar, expected_sha))

    if jobs:
        print(f"  running {len(jobs)} job(s) on {args.max_workers}-worker pool  (skipped {skipped} idempotent)")
        results = parallel_run(jobs, max_workers=args.max_workers)
    else:
        results = []; print(f"  all {skipped} jobs idempotent — nothing to run")

    n_ok = n_fail = 0
    res_iter = iter(results)
    for stem, sidecar, sha_or_done in deferred:
        if sha_or_done is True: n_ok += 1; continue
        r = next(res_iter)
        output_path = OUT_DIR / f"{stem}.json"
        if not r["ok"]:
            print(f"  {stem}: [FAIL] exit {r['exit']}: {r['stderr'].strip()[:200]}")
            n_fail += 1; continue
        try:
            result = json.loads(output_path.read_text(encoding="utf-8"))
        except Exception as e:
            print(f"  {stem}: [FAIL] parse: {e}"); n_fail += 1; continue
        if not validate_r_output(result):
            print(f"  {stem}: [FAIL] schema"); n_fail += 1; continue
        write_sidecar(sidecar, sha_or_done)
        if result.get("fit_ok"):
            print(f"  {stem}: [OK] k={result['k']} pool={result['pool']:.3f} "
                  f"[{result['lci']:.3f}, {result['uci']:.3f}] tau2={result['tau2']:.4f} I2={result['I2']:.0f}%")
            n_ok += 1
        else:
            print(f"  {stem}: [WARN] {result.get('error')}")
            n_fail += 1
    print(f"\nOK: {n_ok}  failed: {n_fail}  (idempotent-skipped: {skipped})")
    sys.exit(1 if n_fail else 0)


if __name__ == "__main__":
    main()
