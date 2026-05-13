"""Effect-size plausibility audit (Agent 2, Round 2)."""
import json
import math
import sys
import io

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

INPUT = "C:/Projects/Finrenone/outputs/extraction_audit/multi_agent_sample_r2.json"
OUTPUT = "C:/Projects/Finrenone/outputs/extraction_audit/agent2_plausibility_r2.json"

with open(INPUT, "r", encoding="utf-8") as f:
    trials = json.load(f)

print(f"Loaded {len(trials)} trials")

findings = []

def add(t, severity, category, reason, confidence):
    findings.append({
        "id": t.get("id"),
        "review": t.get("review"),
        "nct": t.get("nct"),
        "severity": severity,
        "category": category,
        "reason": reason,
        "confidence": confidence,
    })

# Drug-class direction priors: drug-vs-placebo expected direction for the named outcome contexts
# We won't rigidly enforce this — only flag obvious violations.
# Known SGLT2 drugs: dapagliflozin, empagliflozin, canagliflozin, ertugliflozin, sotagliflozin
# Statins: atorvastatin, rosuvastatin, simvastatin, etc.

def lower(x):
    return (x or "").lower()

for t in trials:
    nct = t.get("nct")
    name = lower(t.get("name"))
    grp = lower(t.get("group"))
    review = lower(t.get("review", ""))
    hr = t.get("publishedHR")
    lci = t.get("hrLCI")
    uci = t.get("hrUCI")
    tE = t.get("tE")
    tN = t.get("tN")
    cE = t.get("cE")
    cN = t.get("cN")
    et = t.get("estimandType")

    # ---- HIGH: schema MD with event counts ----
    if et == "MD" and (tE is not None and tE != 0 or cE is not None and cE != 0):
        # only flag if event counts are nontrivial
        if (isinstance(tE,(int,float)) and tE > 0) or (isinstance(cE,(int,float)) and cE > 0):
            add(t, "HIGH", "schema-MD-with-events",
                f"estimandType='MD' but event counts populated (tE={tE}, cE={cE}); MDs operate on means, not counts.",
                0.95)

    # ---- HIGH: single-arm fabricated HR (cE=cN=0) ----
    if (cE == 0 and cN == 0) and hr is not None:
        add(t, "HIGH", "single-arm-fab-HR",
            f"Comparator arm has cE=0, cN=0 (no comparator) but HR={hr} reported — fabricated comparator.",
            0.95)
    elif (tE == 0 and tN == 0) and hr is not None:
        add(t, "HIGH", "single-arm-fab-HR",
            f"Treatment arm has tE=0, tN=0 but HR={hr} reported — single-arm/missing data with fabricated HR.",
            0.9)

    # ---- HIGH: CI illogical ----
    if hr is not None and lci is not None and uci is not None:
        try:
            hrf = float(hr); lcif = float(lci); ucif = float(uci)
            if lcif > hrf + 1e-9:
                add(t, "HIGH", "CI-illogical",
                    f"LCI ({lcif}) > HR ({hrf}); confidence interval lower bound exceeds point estimate.",
                    0.98)
            elif hrf > ucif + 1e-9:
                add(t, "HIGH", "CI-illogical",
                    f"HR ({hrf}) > UCI ({ucif}); point estimate exceeds upper CI bound.",
                    0.98)
            # Check sign-flip CI: HR<1 but CI strictly >1, or HR>1 with CI strictly <1
            if hrf < 1 and lcif > 1:
                add(t, "HIGH", "CI-illogical",
                    f"HR={hrf}<1 but LCI={lcif}>1 — CI doesn't contain point estimate.",
                    0.95)
            if hrf > 1 and ucif < 1:
                add(t, "HIGH", "CI-illogical",
                    f"HR={hrf}>1 but UCI={ucif}<1 — CI doesn't contain point estimate.",
                    0.95)
        except (TypeError, ValueError):
            pass

    # ---- HIGH: magnitude extreme ----
    if hr is not None:
        try:
            hrf = float(hr)
            if hrf > 50:
                add(t, "HIGH", "magnitude-extreme",
                    f"HR={hrf} — likely OR mislabelled as HR or extreme rare-event response (e.g., placebo-vs-active for very-high-efficacy biologic).",
                    0.9)
            elif hrf > 10 and hrf <= 50:
                # only flag if it claims to be HR explicitly
                if et == "HR":
                    add(t, "HIGH", "magnitude-extreme",
                        f"estimandType='HR' but value={hrf} > 10 — implausible hazard ratio.",
                        0.85)
                else:
                    add(t, "MED", "magnitude-extreme",
                        f"Effect size={hrf} > 10 (estimandType={et}); suspicious magnitude even if OR.",
                        0.7)
            if 0 < hrf < 0.01:
                add(t, "HIGH", "magnitude-extreme",
                    f"HR={hrf} < 0.01 — implausibly small.",
                    0.85)
        except (TypeError, ValueError):
            pass

    # ---- MED: crude vs reported HR mismatch (binary RCT) ----
    if all(isinstance(x,(int,float)) for x in (tE, tN, cE, cN)) and hr is not None:
        try:
            hrf = float(hr)
            if tN > 0 and cN > 0 and cE > 0 and tE >= 0:
                crude_rr = (tE/tN) / (cE/cN)
                # Only flag if both crude and HR are finite, non-zero, and disagree by >2x
                if hrf > 0 and crude_rr > 0:
                    ratio = max(crude_rr/hrf, hrf/crude_rr)
                    if ratio > 2.0 and abs(hrf - 1.0) > 0.05:
                        # skip if HR is extreme (already caught), or if et indicates OR (OR can diverge from RR with high baseline)
                        if hrf < 20 and crude_rr < 20:
                            # OR can differ from RR substantially when baseline rate is high; suppress if estimandType=OR and baseline>0.3
                            baseline = cE/cN
                            if et == "OR" and baseline > 0.2:
                                pass  # OR-RR drift is expected
                            else:
                                add(t, "MED", "crude-vs-HR-mismatch",
                                    f"crude_RR={crude_rr:.2f} (tE/tN={tE}/{tN}, cE/cN={cE}/{cN}) vs reported HR={hrf} differ by {ratio:.1f}x.",
                                    0.6)
        except (TypeError, ValueError, ZeroDivisionError):
            pass

    # ---- LOW: missing CI or estimandType ----
    if hr is not None and (lci is None or uci is None):
        add(t, "LOW", "other",
            f"HR={hr} reported but CI missing (LCI={lci}, UCI={uci}).",
            0.9)
    if hr is not None and et is None:
        add(t, "LOW", "other",
            f"HR={hr} reported but estimandType is null — cannot validate scale (HR/OR/RR/MD).",
            0.9)

    # ---- MED/HIGH: drug-class wrong direction ----
    # SGLT2 inhibitors should reduce HF outcomes (HR<1 vs placebo in MACE/HF reviews)
    sglt2_drugs = ["dapagliflozin","empagliflozin","canagliflozin","ertugliflozin","sotagliflozin"]
    if any(d in grp for d in sglt2_drugs) and "placebo" in grp:
        if hr is not None:
            try:
                hrf = float(hr)
                if hrf > 1.5 and ("hf" in review or "heart" in review or "mace" in review or "cv" in review):
                    add(t, "HIGH", "wrong-direction",
                        f"SGLT2i vs placebo with HR={hrf}>1.5 in CV/HF context — opposite to canonical literature consensus.",
                        0.75)
            except (TypeError, ValueError):
                pass

# de-dup: prefer HIGH > MED > LOW for the same id
seen = {}
order = {"HIGH":0, "MED":1, "LOW":2}
for f in findings:
    key = (f["id"], f["category"])
    if key not in seen or order[f["severity"]] < order[seen[key]["severity"]]:
        seen[key] = f

result = sorted(seen.values(), key=lambda x: (order[x["severity"]], x["id"]))

print(f"Total findings: {len(result)}")
by_sev = {}
by_cat = {}
for f in result:
    by_sev[f["severity"]] = by_sev.get(f["severity"], 0) + 1
    by_cat[f["category"]] = by_cat.get(f["category"], 0) + 1
print(f"By severity: {by_sev}")
print(f"By category: {by_cat}")

with open(OUTPUT, "w", encoding="utf-8") as f:
    json.dump(result, f, indent=2, ensure_ascii=False)

print(f"Wrote {OUTPUT}")
