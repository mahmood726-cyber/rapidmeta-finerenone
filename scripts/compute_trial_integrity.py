"""Compute pre-registration concordance heuristics per corpus NCT
from AACT 2026-04-12 snapshot.

Three flags per trial (NEUTRAL framing — concordance, NOT trustworthiness):

  retro_registered      first_posted_date > start_date (registry posted
                        AFTER trial start)
  retro_months          months between (positive ⇒ retro)

  results_overdue       primary_completion_date passed > 12 months ago
                        AND results never posted (FDAAA-style)
  results_late_months   months overdue (positive ⇒ late)

  status_unknown        completion_status = "Unknown" or terminated
                        without posted results

Outputs: outputs/trial_integrity.json — { NCT: { flag fields...,
         start_date, first_posted, primary_completion_date, results_first_posted } }

Inline evidence is preserved verbatim from AACT so each flag is
defensible against challenge.
"""
from __future__ import annotations
import sys, io, json, csv
from pathlib import Path
from datetime import date, datetime
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

REPO = Path(__file__).resolve().parent.parent
AACT = Path("D:/AACT-storage/AACT/2026-04-12")
TODAY = date.today()


def parse_date(s):
    s = (s or "").strip()
    if not s: return None
    for fmt in ("%Y-%m-%d", "%m/%d/%Y", "%Y-%m"):
        try:
            return datetime.strptime(s, fmt).date()
        except ValueError:
            continue
    return None


def months_between(d1, d2):
    if not d1 or not d2: return None
    return round((d1 - d2).days / 30.4375, 1)


def main():
    ncts = set((REPO / "outputs/corpus_ncts.txt").read_text().split())
    print(f"Loaded {len(ncts)} corpus NCTs")

    trial_data = {}
    studies_path = AACT / "studies.txt"
    print(f"Streaming {studies_path.stat().st_size/1e6:.1f} MB of studies.txt ...")
    with studies_path.open("r", encoding="utf-8", errors="replace") as f:
        header = f.readline().rstrip("\n").split("|")
        col = {n: i for i, n in enumerate(header)}
        n_rows = 0
        n_kept = 0
        for line in f:
            n_rows += 1
            parts = line.rstrip("\n").split("|")
            if len(parts) < len(header): continue
            nct = parts[col["nct_id"]]
            if nct not in ncts: continue
            n_kept += 1
            d = {
                "nct_id": nct,
                "start_date": parts[col["start_date"]] or None,
                "first_posted": parts[col["study_first_posted_date"]] or None,
                "primary_completion_date": parts[col["primary_completion_date"]] or None,
                "completion_date": parts[col["completion_date"]] or None,
                "results_first_posted": parts[col["results_first_posted_date"]] or None,
                "overall_status": parts[col["overall_status"]] or None,
            }
            trial_data[nct] = d
    print(f"  scanned {n_rows:,}, matched {n_kept}")

    # Compute flags
    out = {}
    for nct, d in trial_data.items():
        start = parse_date(d["start_date"])
        first_posted = parse_date(d["first_posted"])
        prim_comp = parse_date(d["primary_completion_date"])
        results_posted = parse_date(d["results_first_posted"])

        retro_months = months_between(first_posted, start) if first_posted and start else None
        retro_registered = bool(retro_months and retro_months > 1.0)  # >1 month grace

        # Results-overdue: primary_completion > 12 months ago AND no results posted
        results_late_months = None
        results_overdue = False
        if prim_comp and not results_posted:
            elapsed = months_between(TODAY, prim_comp)
            if elapsed and elapsed > 12:
                results_overdue = True
                results_late_months = elapsed
        elif prim_comp and results_posted:
            results_late_months = months_between(results_posted, prim_comp)

        status = (d["overall_status"] or "").strip()
        status_concern = status in ("Unknown status", "Suspended", "Terminated", "Withdrawn")

        any_flag = retro_registered or results_overdue or status_concern

        out[nct] = {
            "start_date": d["start_date"],
            "first_posted": d["first_posted"],
            "primary_completion_date": d["primary_completion_date"],
            "results_first_posted": d["results_first_posted"],
            "overall_status": d["overall_status"],
            "retro_registered": retro_registered,
            "retro_months": retro_months,
            "results_overdue": results_overdue,
            "results_late_months": results_late_months,
            "status_concern": status_concern,
            "any_flag": any_flag,
        }

    matched = len(out)
    flagged = sum(1 for v in out.values() if v["any_flag"])
    retro = sum(1 for v in out.values() if v["retro_registered"])
    overdue = sum(1 for v in out.values() if v["results_overdue"])
    status_n = sum(1 for v in out.values() if v["status_concern"])

    print(f"\n=== Summary ===")
    print(f"  Matched NCTs:       {matched} / {len(ncts)}")
    print(f"  Any-flag:           {flagged} ({100*flagged/max(1,matched):.1f}%)")
    print(f"    retro-registered: {retro}")
    print(f"    results-overdue:  {overdue}")
    print(f"    status-concern:   {status_n}")

    out_path = REPO / "outputs/trial_integrity.json"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(out, indent=2))
    print(f"\nWritten: {out_path}")


if __name__ == "__main__":
    main()
