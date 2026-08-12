"""Per-app readiness for each generator feature built this round."""
import io, os, sys, json, glob
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
SS = r"F:\rapidmeta-ssot-shell\ssot"


def arm_counts(d):
    """Does any trial store per-arm EVENT counts for any outcome?"""
    ev = tot = 0
    for t in d["inputs"]["trials"]:
        for oid, blk in (t.get("by_outcome") or {}).items():
            ad = blk.get("arm_data") or {}
            for role, cell in ad.items():
                if not isinstance(cell, dict):
                    continue
                tot += 1
                if cell.get("events") is not None:
                    ev += 1
    return ev, tot


rows = []
for j in sorted(glob.glob(os.path.join(SS, "*", "*.json"))):
    d = json.load(open(j, encoding="utf-8"))
    bo = d["results"]["by_outcome"]
    n_out = len(bo)
    # charts need log_point + log_se on per_trial
    chartable = sum(
        1 for r in bo.values()
        if sum(1 for x in (r.get("per_trial") or [])
               if x.get("log_point") is not None and x.get("log_se") is not None) >= 2)
    ev, cells = arm_counts(d)
    rows.append({
        "app": d["app_id"],
        "outcomes": n_out,
        "charts_ok": chartable,
        "grade": sum(1 for r in bo.values() if r.get("grade")),
        "panels": sum(1 for r in bo.values() if r.get("panels")),
        "cross": sum(1 for r in bo.values() if (r.get("cross_engine") or {}).get("comparison")),
        "records": len((d.get("screening") or {}).get("records") or []),
        "excluded": len((d.get("screening") or {}).get("excluded") or []),
        "registration": bool(d.get("registration")),
        "attest": bool(d.get("attestations")),
        "rob": sum(1 for t in d["inputs"]["trials"] if t.get("risk_of_bias")),
        "trials": len(d["inputs"]["trials"]),
        "arm_cells": cells,
        "arm_events": ev,
    })

print("=== PER-APP READINESS (12 SSOT canonical objects) ===")
h = ("app", "out", "chartOK", "GRADE", "panels", "Rcmp", "recs", "reg", "att",
     "RoB", "trials", "armCells", "withEvents")
print("%-24s %4s %7s %5s %6s %4s %5s %4s %4s %4s %6s %8s %10s" % h)
for r in rows:
    print("%-24s %4d %7d %5d %6d %4d %5d %4s %4s %4d %6d %8d %10d"
          % (r["app"], r["outcomes"], r["charts_ok"], r["grade"], r["panels"],
             r["cross"], r["records"], "Y" if r["registration"] else "-",
             "Y" if r["attest"] else "-", r["rob"], r["trials"],
             r["arm_cells"], r["arm_events"]))

print("\n=== TOTALS ===")
print("objects                          :", len(rows))
print("outcomes total                   :", sum(r["outcomes"] for r in rows))
print("outcomes chart-ready (>=2 log_se):", sum(r["charts_ok"] for r in rows))
print("outcomes with GRADE              :", sum(r["grade"] for r in rows))
print("outcomes with R panels stored    :", sum(r["panels"] for r in rows))
print("objects with screening.records   :", sum(1 for r in rows if r["records"]))
print("objects with registration        :", sum(1 for r in rows if r["registration"]))
print("objects with attestations        :", sum(1 for r in rows if r["attest"]))
print("objects with any RoB features    :", sum(1 for r in rows if r["rob"]))
print("arm cells total / with events    : %d / %d"
      % (sum(r["arm_cells"] for r in rows), sum(r["arm_events"] for r in rows)))
json.dump(rows, open("readiness.json", "w", encoding="utf-8"), indent=1)
