"""R5b extended — broader pool-level reproduction validation.

Adds 16 more published reference MAs to the original 4. Tests pool
reproduction across cardiology + oncology + diabetes + anticoagulation
to broaden the validation footprint.

Each target: published pooled HR + CI + trial NCT list for a specific
outcome. We pool the OVERLAP of our extracted trials with that NCT set.
"""
from __future__ import annotations
import json, sys, io, math
from pathlib import Path

if hasattr(sys.stdout, "buffer") and getattr(sys.stdout, "encoding", "").lower() != "utf-8":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

HERE = Path(__file__).resolve().parent.parent
OUT = HERE / "outputs" / "extraction_audit"
DATA = OUT / "data"

# Extended target list (original 4 + 16 more)
TARGETS = [
    # Original 4
    {"name": "SGLT2i in HF — Vaduganathan 2022",
     "pmid": "36041474", "doi": "10.1016/S0140-6736(22)01429-5",
     "pub_HR": 0.80, "pub_LCI": 0.75, "pub_UCI": 0.85,
     "ncts": ["NCT03036124", "NCT03057977", "NCT03619213", "NCT03057951"],
     "our_review": "SGLT2I_HF_NMA_REVIEW"},
    {"name": "DOAC vs warfarin AF — Ruff 2014",
     "pmid": "24315724", "doi": "10.1016/S0140-6736(13)62343-0",
     "pub_HR": 0.81, "pub_LCI": 0.73, "pub_UCI": 0.91,
     "ncts": ["NCT00403767", "NCT00412984", "NCT00262600", "NCT00781391"],
     "our_review": "DOAC_AF_NMA_REVIEW"},
    {"name": "FIDELITY cardiorenal — Agarwal 2022",
     "pmid": "34529029", "doi": "10.1093/eurheartj/ehab777",
     "pub_HR": 0.86, "pub_LCI": 0.78, "pub_UCI": 0.95,
     "ncts": ["NCT02540993", "NCT02545049"],
     "our_review": "CARDIORENAL_DKD_NMA_REVIEW"},
    {"name": "SGLT2 MACE 3-CVOT — Zelniker 2019",
     "pmid": "30424892", "doi": "10.1016/S0140-6736(18)32590-X",
     "pub_HR": 0.89, "pub_LCI": 0.83, "pub_UCI": 0.96,
     "ncts": ["NCT01131676", "NCT01032629", "NCT01730534"],
     "our_review": "SGLT2_MACE_CVOT_REVIEW"},
    # 16 more
    {"name": "GLP-1 RA MACE — Sattar Lancet D&E 2021",
     "pmid": "34186050", "doi": "10.1016/S2213-8587(21)00203-5",
     "pub_HR": 0.86, "pub_LCI": 0.80, "pub_UCI": 0.93,
     "ncts": ["NCT01179048", "NCT01147250", "NCT01394952", "NCT01720446",
              "NCT01455896", "NCT02465515", "NCT03914326"],
     "our_review": "GLP1_CVOT_NMA_REVIEW"},
    {"name": "GLP-1 RA HHF — Sattar Lancet D&E 2021",
     "pmid": "34186050", "doi": "10.1016/S2213-8587(21)00203-5",
     "pub_HR": 0.89, "pub_LCI": 0.82, "pub_UCI": 0.98,
     "ncts": ["NCT01179048", "NCT01147250", "NCT01394952"],
     "our_review": "GLP1_CVOT_NMA_REVIEW"},
    {"name": "Sacubitril/valsartan HFrEF — PARADIGM-HF anchor only",
     "pmid": "25176015", "doi": "10.1056/NEJMoa1409077",
     "pub_HR": 0.80, "pub_LCI": 0.73, "pub_UCI": 0.87,
     "ncts": ["NCT01035255"],
     "our_review": "ARNI_HF_REVIEW"},
    {"name": "Vericiguat HFrEF — Armstrong NEJM 2020",
     "pmid": "32222134", "doi": "10.1056/NEJMoa1915928",
     "pub_HR": 0.90, "pub_LCI": 0.82, "pub_UCI": 0.98,
     "ncts": ["NCT02861534"],
     "our_review": "VERICIGUAT_HF_REVIEW"},
    {"name": "Tafamidis ATTR-CM — Maurer ATTR-ACT NEJM 2018",
     "pmid": "30145929", "doi": "10.1056/NEJMoa1805689",
     "pub_HR": 0.70, "pub_LCI": 0.51, "pub_UCI": 0.96,
     "ncts": ["NCT01994889"],
     "our_review": "ATTR_CM_REVIEW"},
    {"name": "Acoramidis ATTRibute-CM — Gillmore NEJM 2024",
     "pmid": "38109320", "doi": "10.1056/NEJMoa2305434",
     "pub_HR": 0.42, "pub_LCI": 0.29, "pub_UCI": 0.61,
     "ncts": ["NCT03860935"],
     "our_review": "ACORAMIDIS_ATTR_CM_REVIEW"},
    {"name": "Bempedoic acid CV outcomes — CLEAR-OUTCOMES Nissen 2023",
     "pmid": "36876740", "doi": "10.1056/NEJMoa2215024",
     "pub_HR": 0.87, "pub_LCI": 0.79, "pub_UCI": 0.96,
     "ncts": ["NCT02993406"],
     "our_review": "PCSK9_LIPID_NMA_REVIEW"},
    {"name": "Patiromer hyperkalaemia — AMBER Agarwal 2019",
     "pmid": "31515080", "doi": "10.1016/S0140-6736(19)32135-X",
     "pub_HR": None,  # outcome was binary 12wk; skip pool comparison
     "ncts": ["NCT03533790"],
     "our_review": "HYPERKALEMIA_K_BINDER_NMA_REVIEW"},
    # Oncology
    {"name": "Pembrolizumab adjuvant melanoma — KEYNOTE-054",
     "pmid": "29658430", "doi": "10.1056/NEJMoa1802357",
     "pub_HR": 0.57, "pub_LCI": 0.46, "pub_UCI": 0.70,
     "ncts": ["NCT02362594"],
     "our_review": "ADJUVANT_IO_MELANOMA_REVIEW"},
    {"name": "Nivolumab adjuvant melanoma — CheckMate-238",
     "pmid": "28891423", "doi": "10.1056/NEJMoa1709030",
     "pub_HR": 0.65, "pub_LCI": 0.51, "pub_UCI": 0.83,
     "ncts": ["NCT02388906"],
     "our_review": "ADJUVANT_IO_MELANOMA_REVIEW"},
    {"name": "Pembrolizumab 1L NSCLC — KEYNOTE-189",
     "pmid": "29658856", "doi": "10.1056/NEJMoa1801005",
     "pub_HR": 0.49, "pub_LCI": 0.38, "pub_UCI": 0.64,
     "ncts": ["NCT02578680"],
     "our_review": "NSCLC_PD1_1L_REVIEW"},
    # Anticoagulation specific
    {"name": "Apixaban single-trial AF — ARISTOTLE",
     "pmid": "21870978", "doi": "10.1056/NEJMoa1107039",
     "pub_HR": 0.79, "pub_LCI": 0.66, "pub_UCI": 0.95,
     "ncts": ["NCT00412984"],
     "our_review": "DOAC_AF_NMA_REVIEW"},
    # Osteoporosis
    {"name": "Denosumab vertebral fracture — FREEDOM",
     "pmid": "19671655", "doi": "10.1056/NEJMoa0809493",
     "pub_HR": 0.32, "pub_LCI": 0.26, "pub_UCI": 0.41,
     "ncts": ["NCT00089791"],
     "our_review": "FRAGILITY_FRACTURE_REVIEW"},
    # Diabetes
    {"name": "Finerenone FIGARO-DKD CV composite (primary)",
     "pmid": "34449181", "doi": "10.1056/NEJMoa2110956",
     "pub_HR": 0.87, "pub_LCI": 0.76, "pub_UCI": 0.98,
     "ncts": ["NCT02545049"],
     "our_review": "FINERENONE_REVIEW"},
    # Closed-loop pediatric T1D
    {"name": "Closed-loop pediatric T1D iDCL — Brown NEJM 2022",
     "pmid": "35041780", "doi": "10.1056/NEJMoa2210834",
     "pub_HR": None,  # primary was TIR difference (continuous); skip pool
     "ncts": ["NCT03844790"],
     "our_review": "T1D_CLOSED_LOOP_NMA_REVIEW"},
]


def get_trial(rv, nct):
    p = DATA / f"{rv}.json"
    if not p.exists(): return None
    try: d = json.loads(p.read_text(encoding="utf-8"))
    except: return None
    rd = d.get("realData") or {}
    return rd.get(nct) if isinstance(rd, dict) else None


def log_hr_from_trial(t):
    if not t: return None
    hr = t.get("publishedHR"); lci = t.get("hrLCI"); uci = t.get("hrUCI")
    if None in (hr, lci, uci): return None
    try: hr = float(hr); lci = float(lci); uci = float(uci)
    except: return None
    if hr <= 0 or lci <= 0 or uci <= 0: return None
    log_hr = math.log(hr)
    se = (math.log(uci) - math.log(lci)) / (2 * 1.959964)
    if se <= 0: return None
    return log_hr, se


def pool_RE_HKSJ(yis_sis):
    k = len(yis_sis)
    if k < 1: return None
    yis = [y for y, _ in yis_sis]; sis2 = [s*s for _, s in yis_sis]
    if k == 1: return {"pool_HR": round(math.exp(yis[0]),4), "k": 1, "method": "single-trial",
                       "lci": round(math.exp(yis[0] - 1.96*math.sqrt(sis2[0])), 4),
                       "uci": round(math.exp(yis[0] + 1.96*math.sqrt(sis2[0])), 4)}
    wis_fe = [1.0/s2 for s2 in sis2]; sum_w = sum(wis_fe)
    yhat_fe = sum(w*y for w, y in zip(wis_fe, yis)) / sum_w
    Q = sum(w*(y-yhat_fe)**2 for w, y in zip(wis_fe, yis))
    df = k - 1
    c = sum_w - sum(w*w for w in wis_fe) / sum_w
    tau2 = max(0.0, (Q - df) / c) if c > 0 else 0.0
    wis_re = [1.0/(s2+tau2) for s2 in sis2]; sum_w_re = sum(wis_re)
    yhat_re = sum(w*y for w, y in zip(wis_re, yis)) / sum_w_re
    if k >= 3:
        rss = sum(w*(y-yhat_re)**2 for w, y in zip(wis_re, yis))
        var_h = max(rss/(k-1), 1.0) / sum_w_re
        se_re = math.sqrt(var_h)
        t_crit = {2: 12.706, 3: 4.303, 4: 3.182, 5: 2.776, 6: 2.571, 7: 2.447, 8: 2.365, 9: 2.306, 10: 2.262}
        t = t_crit.get(k-1, 1.96)
    else:
        se_re = math.sqrt(1.0/sum_w_re); t = 1.96
    return {"pool_HR": round(math.exp(yhat_re),4), "k": k,
            "lci": round(math.exp(yhat_re-t*se_re),4),
            "uci": round(math.exp(yhat_re+t*se_re),4)}


results = []
print(f"R5b extended — testing {len(TARGETS)} reference MAs\n")
for tgt in TARGETS:
    if tgt.get("pub_HR") is None:
        print(f"  {tgt['name'][:60]}: SKIP (no pooled HR — continuous outcome)")
        results.append({**tgt, "verdict": "SKIP_NO_POOLED_HR"})
        continue
    rv = tgt["our_review"]; ncts = tgt["ncts"]
    yi_si = []; with_data = []; missing = []
    for nct in ncts:
        t = get_trial(rv, nct)
        if t is None:
            missing.append(nct); continue
        lhr = log_hr_from_trial(t)
        if lhr is None:
            missing.append(nct); continue
        yi_si.append(lhr); with_data.append(nct)
    if not yi_si:
        results.append({**tgt, "verdict": "INSUFFICIENT_OVERLAP", "overlap": 0, "missing": missing})
        print(f"  {tgt['name'][:60]}: INSUFFICIENT (0/{len(ncts)} trials)")
        continue
    pool = pool_RE_HKSJ(yi_si)
    delta_log = abs(math.log(pool["pool_HR"]) - math.log(tgt["pub_HR"]))
    verdict = ("EXCELLENT" if delta_log < 0.01 else
               "MATCHES" if delta_log < 0.025 else
               "WITHIN-FLOOR" if delta_log < 0.05 else
               "DIVERGE")
    result = {**tgt, "overlap": len(with_data), "trial_overlap_pct": round(100*len(with_data)/len(ncts), 1),
              "with_data": with_data, "missing": missing,
              "our_pool": pool, "delta_log_HR": round(delta_log, 4), "verdict": verdict}
    results.append(result)
    print(f"  {verdict:12s} {tgt['name'][:55]}")
    print(f"               pub HR {tgt['pub_HR']:.2f} vs ours {pool['pool_HR']}  Δ|log|={delta_log:.4f}  (k={len(yi_si)}/{len(ncts)})")

(OUT / "r5b_extended_results.json").write_text(
    json.dumps(results, indent=2, ensure_ascii=False), encoding="utf-8")

# Summary
from collections import Counter
verdict_counts = Counter(r["verdict"] for r in results)
print(f"\n{'='*60}\nR5b extended summary:")
for k, v in verdict_counts.most_common():
    print(f"  {k}: {v}")
within_floor = sum(verdict_counts.get(k, 0) for k in ["EXCELLENT", "MATCHES", "WITHIN-FLOOR"])
testable = sum(1 for r in results if "delta_log_HR" in r)
print(f"\nReproduction rate within floor: {within_floor}/{testable}")
