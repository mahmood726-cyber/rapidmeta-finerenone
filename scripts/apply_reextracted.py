"""Apply workflow-confirmed 2x2 re-extractions back into every app that
references each trial.

Input: outputs/reextract_confirmed.json — a list of
  {nct, tE, tN, cE, cN, verdict, ...} produced by the ctgov-reextract-2x2
  workflow (only adversarially-confirmed rows).

Each confirmed trial's counts are written into ALL *_REVIEW apps whose realData
contains that NCT (the same trial appears across _AUTO and _AUTO_FULL twins).
Reuses the safe, numeric-field-only, parse-validated editor from
ctgov_apply_counts. Benchmark-curated apps stay protected. --apply to write.
"""
from __future__ import annotations
import argparse, io, json, sys, importlib.util
from pathlib import Path

if hasattr(sys.stdout, "buffer") and getattr(sys.stdout, "encoding", "").lower() != "utf-8":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

HERE = Path(__file__).resolve().parent.parent
CONFIRMED = HERE / "outputs" / "reextract_confirmed.json"
sys.path.insert(0, str(HERE / "scripts"))
import importlib
ac = importlib.import_module("ctgov_apply_counts")
_spec = importlib.util.spec_from_file_location("vv", HERE / "validate_living_ma_portfolio.py")
vv = importlib.util.module_from_spec(_spec); _spec.loader.exec_module(vv)
PROTECT = set(vv.BENCHMARKS.keys()) if hasattr(vv, "BENCHMARKS") else set()


def protected(app):
    stem = app.replace("_REVIEW.html", "").replace(".html", "")
    base = stem.split("_AUTO")[0]
    # exact benchmark anchor only (e.g. BIMEKIZUMAB_PSO) -- not _AUTO siblings
    return base in PROTECT


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    args = ap.parse_args()
    confirmed = {c["nct"]: c for c in json.loads(CONFIRMED.read_text(encoding="utf-8"))}
    print(f"confirmed trials to apply: {len(confirmed)}")

    # map nct -> apps that contain it
    apps = sorted(str(p.name) for p in HERE.glob("*_REVIEW.html"))
    edited_files = set()
    applied_pairs = 0
    for app in apps:
        if protected(app):
            continue
        p = HERE / app
        html = p.read_text(encoding="utf-8", errors="replace")
        trials = vv.extract_real_data(html)
        orig = html
        for nct in trials:
            c = confirmed.get(nct)
            if not c:
                continue
            counts = {k: int(c[k]) for k in ("tE", "tN", "cE", "cN")}
            if not (0 <= counts["tE"] <= counts["tN"] and 0 <= counts["cE"] <= counts["cN"]
                    and counts["tN"] > 0 and counts["cN"] > 0):
                continue
            new = ac.apply_to_html(html, nct, counts)
            if new and new != html:
                html = new
                applied_pairs += 1
        if html != orig and vv.extract_real_data(html):
            edited_files.add(app)
            if args.apply:
                p.write_text(html, encoding="utf-8")

    print(f"{'APPLIED' if args.apply else 'DRY-RUN'}: {applied_pairs} (app,trial) writes across {len(edited_files)} files")


if __name__ == "__main__":
    main()
