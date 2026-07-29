"""HFrEF GDMT network (28 trials) - per-trial data-integrity gates.

Runs the gates defined in outputs/extraction_audit/FINAL_INTEGRITY_REPORT_V2.md
against the settled OURS-STRICT network embedded in
HFREF_NMA_AUTO_FULL_REVIEW.html (script id="hfref-fit-data").

This script runs the DETERMINISTIC gates only. Source-lookup gates (PMID identity
via PubMed, registry concordance via ClinicalTrials.gov) are performed separately
by lookup and merged in by hfref_integrity_report.py -- they cannot be computed
from the file alone and are never inferred here.

Gate map (methodology doc -> this network):
  M01  2x2 sanity (0 <= e <= N)            -> G1   APPLIES
  M08  GRIM granularity                    -> G2   N/A (no reported means; the
                                                   outcome is a binary count)
  M09  Benford first-digit                 -> G3   APPLIES (advisory)
  M06  baseline-N ratio                    -> G4   APPLIES (arm-balance advisory)
  M03/M04 NCT / PMID format                -> G5   APPLIES
  R7/R9/R10 AACT concordance               -> G6   APPLIES to registry subset only
  Fragility Index (Walsh 2014)             -> G7   APPLIES to significant contrasts

Exit 0 always: this is an audit reporter, not a build gate. Findings are
classified FINDING / NA / PASS and written to outputs/hfref_integrity_gates.json.
"""
from __future__ import annotations
import sys, io, json, re, math
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
APP = REPO / "HFREF_NMA_AUTO_FULL_REVIEW.html"
OUT = REPO / "outputs" / "hfref_integrity_gates.json"

# NOTE: fragility_index_check reassigns sys.stdout at module level. Import it
# FIRST and let it own that reassignment - wrapping stdout ourselves as well
# closes the underlying buffer and every later print() raises
# "I/O operation on closed file".
sys.path.insert(0, str(REPO / "scripts"))
from fragility_index_check import compute_fragility, fishers_two_sided  # noqa: E402


def load_payload():
    s = APP.read_text(encoding="utf-8")
    m = re.search(r'<script id="hfref-fit-data" type="application/json">(.*?)</script>', s, re.S)
    if not m:
        raise SystemExit("FATAL: hfref-fit-data payload not found")
    return json.loads(m.group(1))


def is_nonneg_int(x):
    return isinstance(x, int) and not isinstance(x, bool) and x >= 0


def main():
    p = load_payload()
    trials = p["trials"]
    contrasts = p["study_contrasts"]
    results = {"gates": {}, "per_trial": {}, "meta": {}}

    results["meta"] = {
        "n_trials": len(trials),
        "n_study_contrasts": len(contrasts),
        "coverage": p.get("coverage"),
        "engine": p.get("engine"),
    }

    # ---------------- G1: per-arm event-count plausibility (M01) -------------
    g1 = []
    for t in trials:
        tot_n = tot_e = 0
        for a in t["arms"]:
            e, n, tr = a["events"], a["n"], a["treat"]
            tag = f"{t['name']}/{tr}"
            if not is_nonneg_int(e):
                g1.append({"trial": t["name"], "arm": tr, "issue": "events not a non-negative integer", "value": e})
            if not is_nonneg_int(n) or n <= 0:
                g1.append({"trial": t["name"], "arm": tr, "issue": "N not a positive integer", "value": n})
            if is_nonneg_int(e) and is_nonneg_int(n) and e > n:
                g1.append({"trial": t["name"], "arm": tr, "issue": f"events {e} exceeds N {n}"})
            tot_n += n if is_nonneg_int(n) else 0
            tot_e += e if is_nonneg_int(e) else 0
        # internal totals must agree with the arm rows
        if t.get("total_n") != tot_n:
            g1.append({"trial": t["name"], "issue": f"total_n {t.get('total_n')} != sum of arms {tot_n}"})
        if t.get("total_events") != tot_e:
            g1.append({"trial": t["name"], "issue": f"total_events {t.get('total_events')} != sum of arms {tot_e}"})
        if t.get("n_arms") != len(t["arms"]):
            g1.append({"trial": t["name"], "issue": f"n_arms {t.get('n_arms')} != len(arms) {len(t['arms'])}"})

    results["gates"]["G1_per_arm_count_plausibility"] = {
        "status": "RAN", "applies": True,
        "checked_arms": sum(len(t["arms"]) for t in trials),
        "findings": g1,
    }

    # ---------------- G1b: ledger arms vs fitted study_contrasts ------------
    g1b = []
    armmap = {}
    for t in trials:
        for a in t["arms"]:
            armmap[(t["name"], a["treat"])] = (a["events"], a["n"])
    for c in contrasts:
        for side, (tk, ek, nk) in {"1": ("treat1", "event1", "n1"), "2": ("treat2", "event2", "n2")}.items():
            key = (c["studlab"], c[tk])
            if key not in armmap:
                g1b.append({"contrast": f"{c['studlab']} {c['treat1']} vs {c['treat2']}",
                            "issue": f"arm {c[tk]} absent from trial ledger"})
                continue
            e, n = armmap[key]
            if (c[ek], c[nk]) != (e, n):
                g1b.append({"contrast": f"{c['studlab']} {c['treat1']} vs {c['treat2']}",
                            "issue": f"{c[tk]}: contrast ({c[ek]}/{c[nk]}) != ledger ({e}/{n})"})
        # recompute logRR/seLogRR from the counts and compare to the fitted value
        e1, n1, e2, n2 = c["event1"], c["n1"], c["event2"], c["n2"]
        if min(e1, e2) > 0 and n1 > 0 and n2 > 0:
            lrr = math.log((e1 / n1) / (e2 / n2))
            se = math.sqrt(1 / e1 - 1 / n1 + 1 / e2 - 1 / n2)
            if abs(lrr - c["logRR"]) > 1e-8:
                g1b.append({"contrast": f"{c['studlab']} {c['treat1']} vs {c['treat2']}",
                            "issue": f"logRR mismatch: recomputed {lrr:.11f} vs stored {c['logRR']}"})
            if abs(se - c["seLogRR"]) > 1e-8:
                g1b.append({"contrast": f"{c['studlab']} {c['treat1']} vs {c['treat2']}",
                            "issue": f"seLogRR mismatch: recomputed {se:.11f} vs stored {c['seLogRR']}"})

    results["gates"]["G1b_contrast_vs_ledger_and_recompute"] = {
        "status": "RAN", "applies": True,
        "checked_contrasts": len(contrasts), "findings": g1b,
    }

    # ---------------- G2: GRIM / GRIMMER -- applicability -------------------
    results["gates"]["G2_GRIM_GRIMMER"] = {
        "status": "NOT_APPLICABLE", "applies": False,
        "reason": ("GRIM/GRIMMER test whether a reported MEAN of a bounded integer-scale "
                   "item is reconstructible as X/N. This network's only outcome is "
                   "all-cause mortality, a binary per-arm event count. No means, SDs or "
                   "Likert-scale items are extracted or fitted, so there is nothing for "
                   "GRIM to test. Replaced by G1 (per-arm count plausibility: integer, "
                   "0 <= events <= N, denominators agree with the fitted contrasts)."),
        "findings": [],
    }

    # ---------------- G3: Benford first-digit (M09), advisory ---------------
    def first_digit(x):
        a = abs(x)
        if a == 0:
            return None
        while a < 1:
            a *= 10
        while a >= 10:
            a /= 10
        return int(a)

    pool = []
    for t in trials:
        for a in t["arms"]:
            for v in (a["events"], a["n"]):
                d = first_digit(v)
                if d:
                    pool.append(d)
    obs = [pool.count(d) for d in range(1, 10)]
    exp = [len(pool) * math.log10(1 + 1 / d) for d in range(1, 10)]
    chi2 = sum((o - e) ** 2 / e for o, e in zip(obs, exp) if e > 0)
    results["gates"]["G3_benford_first_digit"] = {
        "status": "RAN", "applies": True, "advisory": True,
        "n_values": len(pool), "chi2": round(chi2, 3), "df": 8,
        "crit_0.05": 15.507,
        "signal": "no fabrication signal" if chi2 < 15.507 else "DEVIATION",
        "findings": [],
    }

    # ---------------- G4: arm-balance / baseline-N ratio (M06) --------------
    g4 = []
    for t in trials:
        ns = [a["n"] for a in t["arms"]]
        if min(ns) > 0:
            ratio = max(ns) / min(ns)
            if ratio > 2.0:
                g4.append({"trial": t["name"], "arm_Ns": ns, "ratio": round(ratio, 3),
                           "note": "randomisation ratio >2:1 - verify against source"})
    results["gates"]["G4_arm_balance_ratio"] = {
        "status": "RAN", "applies": True, "advisory": True,
        "threshold": "max(N)/min(N) > 2.0", "findings": g4,
    }

    # ---------------- G5: identifier format (M03/M04) -----------------------
    g5 = []
    reg = {"ctgov": [], "other_registry": [], "none": []}
    for t in trials:
        pmid, nct = t.get("pmid"), t.get("nct")
        if pmid is not None and not re.fullmatch(r"\d{1,8}", str(pmid)):
            g5.append({"trial": t["name"], "issue": f"PMID malformed: {pmid}"})
        if pmid is None:
            g5.append({"trial": t["name"], "issue": "no PMID in ledger",
                       "ledger_note": t.get("pmid_note")})
        if nct is None:
            reg["none"].append(t["name"])
        elif re.fullmatch(r"NCT\d{8}", str(nct)):
            reg["ctgov"].append({"trial": t["name"], "nct": nct})
        else:
            reg["other_registry"].append({"trial": t["name"], "id": nct})
    results["gates"]["G5_identifier_format"] = {
        "status": "RAN", "applies": True, "findings": g5, "registry_split": reg,
    }

    # ---------------- G7: Fragility Index (Walsh 2014) ----------------------
    fi_rows = []
    for c in contrasts:
        r = compute_fragility(c["event1"], c["n1"], c["event2"], c["n2"])
        row = {"trial": c["studlab"], "contrast": f"{c['treat1']} vs {c['treat2']}",
               "e1": c["event1"], "n1": c["n1"], "e2": c["event2"], "n2": c["n2"]}
        if r is None:
            row.update({"verdict": "UNCOMPUTABLE", "FI": None, "p0": None})
        else:
            row.update({"verdict": r["verdict"], "FI": r["FI"],
                        "p0": round(r["p0"], 5),
                        "p_flipped": round(r["p_flipped"], 5) if r.get("p_flipped") is not None else None,
                        "flip_target": r.get("flip_target")})
        fi_rows.append(row)
    results["gates"]["G7_fragility_index"] = {
        "status": "RAN", "applies": True,
        "method": "Walsh 2014, Fisher exact two-sided; FI<=1 FAIL, FI<=3 WARN, else OK",
        "rows": fi_rows,
        "n_significant": sum(1 for r in fi_rows if r["verdict"] not in ("NOT_SIGNIFICANT", "UNCOMPUTABLE")),
    }

    # ---------------- NMA-level contrasts whose CI excludes 1 ---------------
    pw = p["nma_config"].get("pairwise") or []
    if not pw:
        # league table lives under a different key in this payload
        for k in ("league", "pairwise_all", "contrasts_all"):
            if isinstance(p.get(k), list):
                pw = p[k]
                break
    results["meta"]["nma_pairwise_key_found"] = bool(pw)

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(results, indent=1), encoding="utf-8")

    # ---------------- console summary --------------------------------------
    print("=" * 72)
    print("HFrEF 28-trial network - per-trial data-integrity gates")
    print("=" * 72)
    for name, g in results["gates"].items():
        st = g["status"]
        n = len(g.get("findings", []))
        extra = ""
        if name.startswith("G3"):
            extra = f"  chi2={g['chi2']} ({g['signal']})"
        if name.startswith("G7"):
            extra = f"  significant contrasts={g['n_significant']}"
            n = sum(1 for r in g["rows"] if r["verdict"] in ("FAIL", "WARN"))
        print(f"  {name:42s} {st:16s} findings={n}{extra}")
    print()
    print(f"Registry split: CT.gov={len(reg['ctgov'])}  "
          f"other-registry={len(reg['other_registry'])}  none={len(reg['none'])}")
    print(f"\nWritten: {OUT}")


if __name__ == "__main__":
    main()
