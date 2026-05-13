"""R24 — AACT design_outcomes outcome-type verification.

For each trial we have estimandType for, check that the AACT primary outcome
is compatible.

AACT outcome_type values:
  - primary
  - secondary
  - other

Our estimandType values: HR, RR, OR, MD, SMD, RD, WMD

Rules:
  - If primary outcome is time-to-event (mentions "time to", "free survival",
    "first occurrence", "hazard"), estimandType should be HR.
  - If primary outcome is binary count (mentions "proportion", "number of",
    "incidence", "percentage", "responders"), estimandType should be OR/RR.
  - If primary outcome is continuous (mentions "change", "difference",
    "mean", "score"), estimandType should be MD/SMD.

For each trial:
  if estimandType + primary outcome are SEMANTICALLY INCOMPATIBLE
  → flag for re-extract (don't auto-fix; needs source-paper to determine
    which is right).
"""
from __future__ import annotations
import json, csv, re, sys, io
from pathlib import Path
from collections import defaultdict, Counter

if hasattr(sys.stdout, "buffer") and getattr(sys.stdout, "encoding", "").lower() != "utf-8":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

HERE = Path(__file__).resolve().parent.parent
OUT = HERE / "outputs" / "extraction_audit"
DATA = OUT / "data"
AACT = Path("D:/AACT-storage/AACT/2026-04-12")
DRY = "--dry-run" in sys.argv

target = []
for json_p in sorted(DATA.glob("*.json")):
    if json_p.name.startswith("_"): continue
    rv = json_p.stem
    try: d = json.loads(json_p.read_text(encoding="utf-8"))
    except: continue
    rd = d.get("realData") or {}
    if not isinstance(rd, dict): continue
    for nct, t in rd.items():
        if not isinstance(t, dict): continue
        if nct.startswith("NULLED:"): continue
        if not re.match(r"^NCT\d{8}$", nct): continue
        et = (t.get("estimandType") or "").upper()
        if not et: continue
        target.append({"review": rv, "nct": nct, "estimandType": et})

target_ncts = sorted({t["nct"] for t in target})
print(f"Trials with estimandType: {len(target)}  unique NCTs: {len(target_ncts)}")

# Load AACT design_outcomes (primary only)
target_set = set(target_ncts)
primary_outcomes = defaultdict(list)
print("Loading design_outcomes.txt…")
with open(AACT / "design_outcomes.txt", "r", encoding="utf-8", errors="replace") as f:
    reader = csv.DictReader(f, delimiter="|")
    for row in reader:
        nct = (row.get("nct_id") or "").strip().upper()
        if nct not in target_set: continue
        if (row.get("outcome_type") or "").lower() != "primary": continue
        primary_outcomes[nct].append({
            "measure": (row.get("measure") or "").lower(),
            "time_frame": (row.get("time_frame") or "").lower(),
        })
print(f"  NCTs with primary outcomes: {len(primary_outcomes)}")


TTE_KEYWORDS = ["time to", "time-to", "free survival", "first occurrence",
                 "hazard", "event-free", "progression-free", "overall survival",
                 "mortality", "death", "hospitalization for", "incidence of"]
BINARY_KEYWORDS = ["proportion", "number of", "percentage", "responders",
                    "response rate", "achieving", "with event", "rate of",
                    "remission", "complete response", "objective response"]
CONTINUOUS_KEYWORDS = ["change in", "change from", "difference in",
                        "mean", "score", "level", "concentration",
                        "from baseline", "least-squares mean"]


def classify_outcome(measure):
    m = measure.lower()
    is_tte = any(k in m for k in TTE_KEYWORDS)
    is_binary = any(k in m for k in BINARY_KEYWORDS)
    is_cont = any(k in m for k in CONTINUOUS_KEYWORDS)
    if is_tte and not is_cont: return "TTE"
    if is_cont and not is_tte: return "CONTINUOUS"
    if is_binary and not is_cont: return "BINARY"
    return None


def estimand_compatible(et, aact_type):
    et = (et or "").upper()
    if aact_type == "TTE": return et in ("HR",)
    if aact_type == "CONTINUOUS": return et in ("MD", "SMD", "WMD", "RD")
    if aact_type == "BINARY": return et in ("OR", "RR", "HR", "RD")  # HR for time-to-binary OK
    return True  # Unknown — don't penalize


findings = []
for t in target:
    nct = t["nct"]; rv = t["review"]; et = t["estimandType"]
    outs = primary_outcomes.get(nct, [])
    if not outs: continue
    aact_types = [classify_outcome(o["measure"]) for o in outs]
    aact_types = [x for x in aact_types if x is not None]
    if not aact_types: continue
    # If ALL primary outcomes are of one type AND incompatible with et → flag
    if len(set(aact_types)) == 1:
        aact_type = aact_types[0]
        if not estimand_compatible(et, aact_type):
            findings.append({
                "review": rv, "nct": nct, "estimandType": et,
                "aact_outcome_type": aact_type,
                "aact_measure_sample": outs[0]["measure"][:80],
                "fix": "FLAG_ONLY",  # no auto-fix; needs source-paper
            })

print(f"Estimand/outcome-type mismatches: {len(findings)}")
# Counts by directional category
from collections import Counter
direction = Counter()
for f in findings:
    direction[(f["estimandType"], f["aact_outcome_type"])] += 1
print("By direction:")
for k, n in direction.most_common():
    print(f"  extracted={k[0]:5s} → AACT={k[1]}: {n}")

out_p = OUT / "r24_design_outcomes.json"
direction_jsonable = {f"{k[0]}→{k[1]}": v for k, v in direction.items()}
out_p.write_text(json.dumps({"findings": findings, "by_direction": direction_jsonable,
                              "summary": {"flagged": len(findings)}},
                             indent=2, ensure_ascii=False), encoding="utf-8")
print(f"\nLog → {out_p}  (flag-only, no destructive auto-fix this round)")
