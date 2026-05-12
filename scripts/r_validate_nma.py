"""Python wrapper that runs R netmeta cross-validation on every binary NMA
review.

Inputs: NMA_CONFIG.comparisons + realData per-trial e/n cells.

Outputs: outputs/r_validation/nma/<REVIEW>.json
"""
from __future__ import annotations
import io, json, math, os, shutil, subprocess, sys
from pathlib import Path

if sys.platform == "win32" and hasattr(sys.stdout, "buffer"):
    try:
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    except Exception:
        pass

REPO = Path(__file__).resolve().parent.parent
DATA_DIR = REPO / "outputs" / "extraction_audit" / "data"
OUT_DIR = REPO / "outputs" / "r_validation" / "nma"
OUT_DIR.mkdir(parents=True, exist_ok=True)
R_SCRIPT = REPO / "scripts" / "r_validate_nma.R"
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


def _is_int_like(x):
    return isinstance(x, (int, float)) and not isinstance(x, bool) and math.isfinite(x)


def build_comparisons(rd: dict, nma_cfg: dict) -> list[dict]:
    """Build a flat list of contrast rows. cfg.comparisons has
    [{t1, t2, trials: [NCT_ID]}]; we materialise to one row per trial."""
    out = []
    comps = nma_cfg.get("comparisons") or []
    for comp in comps:
        if not (isinstance(comp, dict) and comp.get("t1") and comp.get("t2")):
            continue
        for ref in (comp.get("trials") or []):
            t = rd.get(ref) if isinstance(ref, str) else ref
            if not isinstance(t, dict):
                continue
            tE, tN, cE, cN = t.get("tE"), t.get("tN"), t.get("cE"), t.get("cN")
            if not all(_is_int_like(v) for v in (tE, tN, cE, cN)):
                continue
            if not (tN > 0 and cN > 0 and tE >= 0 and cE >= 0 and tE <= tN and cE <= cN):
                continue
            out.append({
                "studlab": t.get("name") or ref,
                "t1": comp["t1"], "t2": comp["t2"],
                "e1": int(tE), "n1": int(tN), "e2": int(cE), "n2": int(cN),
            })
    return out


def main() -> None:
    index = json.loads((DATA_DIR / "_index.json").read_text(encoding="utf-8"))
    candidates = []
    for entry in index:
        if not entry.get("has_realData"):
            continue
        if not entry.get("has_NMA_CONFIG"):
            continue
        stem = entry["stem"]
        if not _stem_safe(stem):
            print(f"  skip (unsafe stem): {stem!r}")
            continue
        doc = json.loads((DATA_DIR / f"{stem}.json").read_text(encoding="utf-8"))
        rd = doc.get("realData") or {}
        cfg = doc.get("NMA_CONFIG") or {}
        comps = build_comparisons(rd, cfg)
        if len(comps) >= 2:
            # P0-8 fix: ordered-priority reference selection.
            #   1. cfg.reference (explicit author choice)
            #   2. case-insensitive match against {Placebo, Control, Sham,
            #      Standard care, Standard of care, SoC, Usual care, No
            #      treatment}
            #   3. highest-degree node in the contrast graph (most-connected)
            treatments = cfg.get("treatments") or []
            explicit = cfg.get("reference") if isinstance(cfg.get("reference"), str) else None
            ref = None
            if explicit and explicit in treatments:
                ref = explicit
            else:
                preferred = ["Placebo", "Control", "Sham", "Standard care",
                             "Standard of care", "SoC", "Usual care", "No treatment"]
                for p in preferred:
                    for t in treatments:
                        if str(t).strip().lower() == p.lower():
                            ref = t; break
                    if ref: break
                if ref is None and treatments:
                    # Highest-degree node fallback
                    from collections import Counter
                    deg = Counter()
                    for c in comps:
                        deg[c["t1"]] += 1; deg[c["t2"]] += 1
                    if deg:
                        ref = deg.most_common(1)[0][0]
            candidates.append((stem, treatments, comps, ref))

    print(f"Binary NMA review candidates: {len(candidates)}")
    n_ok, n_fail = 0, 0
    for stem, trts, comps, ref in candidates:
        input_path  = OUT_DIR / f"{stem}.input.json"
        output_path = OUT_DIR / f"{stem}.json"
        input_path.write_text(json.dumps({
            "review": stem, "treatments": trts, "comparisons": comps,
            "reference": ref,
        }, indent=2), encoding="utf-8")
        try:
            r = subprocess.run(
                [RSCRIPT_EXE, str(R_SCRIPT), str(input_path), str(output_path)],
                capture_output=True, text=True, timeout=120,
            )
        except subprocess.TimeoutExpired:
            print(f"  {stem}: [FAIL] timeout"); n_fail += 1; continue
        if r.returncode != 0:
            print(f"  {stem}: [FAIL] exit {r.returncode}: {r.stderr.strip()[:200]}")
            n_fail += 1; continue
        result = json.loads(output_path.read_text(encoding="utf-8"))
        if result.get("fit_ok"):
            n_trts = result.get("n_treatments") or 0
            kcomp = result.get("k_comparisons") or 0
            tau2 = result.get("tau2"); tau2 = 0.0 if tau2 is None else tau2
            i2 = result.get("I2"); i2 = 0.0 if i2 is None else i2
            print(f"  {stem}: OK {n_trts} trts, {kcomp} contrasts, tau2={tau2:.3f}, I2={i2:.0f}%")
            n_ok += 1
        else:
            print(f"  {stem}: [WARN] {result.get('error')}")
            n_fail += 1
    print(f"\nOK: {n_ok}  failed: {n_fail}")


if __name__ == "__main__":
    main()
