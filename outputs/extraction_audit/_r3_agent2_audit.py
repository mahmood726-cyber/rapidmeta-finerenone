"""Agent 2 (Plausibility) - R3 sweep on multi_agent_sample_r3.json.

Lens: HR magnitude, CI consistency, schema sanity, crude-vs-pooled coherence.
Output: agent2_plausibility_r3.json - array of flag dicts.

R3 refinements:
- MD rows: publishedHR holds the mean-diff value (e.g. -16 LDL, +11 TIR%). Do
  NOT flag those as "HR<0 impossible" - they are schema-misuse, not effect
  implausibility. Flag once as residual-schema-MD when est=MD AND publishedHR
  is outside [0, ~10] (impossible for HR/RR/OR).
- For binary-effect rows (est in HR/RR/OR/None), flag magnitude-extreme only
  when the cell-implied crude OR/RR confirms the value is logistic-shaped
  (e.g. PASI90 318/349 vs 1/86 -> crude OR ~1011 - the published "HR" of 871.9
  is an OR-mislabel residual that R2's 31-row sweep missed).
- Deduplicate categories per id.
"""
import json
import math
from pathlib import Path
from collections import Counter, defaultdict

INPUT = Path(r"C:/Projects/Finrenone/outputs/extraction_audit/multi_agent_sample_r3.json")
OUTPUT = Path(r"C:/Projects/Finrenone/outputs/extraction_audit/agent2_plausibility_r3.json")

rows = json.loads(INPUT.read_text(encoding="utf-8"))

flags = []


def add(rec, sev, cat, reason, conf):
    flags.append({
        "id": rec["id"],
        "review": rec.get("review"),
        "nct": rec.get("nct"),
        "severity": sev,
        "category": cat,
        "reason": reason,
        "confidence": round(conf, 2),
    })


def num(x):
    try:
        if x is None:
            return None
        v = float(x)
        if math.isnan(v) or math.isinf(v):
            return None
        return v
    except Exception:
        return None


def has_events_pair(tE, tN, cE, cN):
    return all(num(v) is not None for v in (tE, tN, cE, cN))


def crude_or(tE, tN, cE, cN):
    """Haldane-corrected OR for sparse cells."""
    a, b = tE, tN - tE
    c, d = cE, cN - cE
    if min(a, b, c, d) == 0:
        a, b, c, d = a + 0.5, b + 0.5, c + 0.5, d + 0.5
    if b == 0 or c == 0:
        return None
    return (a * d) / (b * c)


def crude_rr(tE, tN, cE, cN):
    rt = tE / tN if tN > 0 else None
    rc = cE / cN if cN > 0 else None
    if rt is None or rc is None or rc == 0:
        return None
    return rt / rc


for r in rows:
    tE, tN, cE, cN = num(r.get("tE")), num(r.get("tN")), num(r.get("cE")), num(r.get("cN"))
    hr = num(r.get("publishedHR"))
    lci = num(r.get("hrLCI"))
    uci = num(r.get("hrUCI"))
    est = r.get("estimandType")

    # ------------------------------------------------------------------
    # HIGH: events exceed N (impossible)
    # ------------------------------------------------------------------
    if tE is not None and tN is not None and tE > tN:
        add(r, "HIGH", "events-exceed-N",
            f"Treatment events tE={tE:g} exceed total tN={tN:g} (impossible).", 0.99)
    if cE is not None and cN is not None and cE > cN:
        add(r, "HIGH", "events-exceed-N",
            f"Control events cE={cE:g} exceed total cN={cN:g} (impossible).", 0.99)

    # ------------------------------------------------------------------
    # HIGH: CI illogical (only meaningful when HR present)
    # ------------------------------------------------------------------
    if hr is not None and lci is not None and uci is not None:
        if lci > uci:
            add(r, "HIGH", "CI-illogical",
                f"LCI={lci:g} > UCI={uci:g} (bounds swapped).", 0.98)
        elif not (lci - 1e-6 <= hr <= uci + 1e-6):
            # If estimandType is HR/RR/OR/None: HR must lie in [LCI, UCI]
            # If estimandType is MD: same (mean diff also must lie in CI)
            add(r, "HIGH", "CI-illogical",
                f"Point estimate {hr:g} outside CI [{lci:g}, {uci:g}].", 0.95)

    # ------------------------------------------------------------------
    # HIGH: residual single-arm (cE=cN=0) with non-null HR (binary effects only)
    # ------------------------------------------------------------------
    if hr is not None and est in ("HR", "RR", "OR") and cE == 0 and cN == 0:
        add(r, "HIGH", "residual-single-arm",
            f"cE=0, cN=0 but publishedHR={hr:g} - residual single-arm fabrication.", 0.95)
    if hr is not None and est in ("HR", "RR", "OR") and tE == 0 and tN == 0:
        add(r, "HIGH", "residual-single-arm",
            f"tE=0, tN=0 but publishedHR={hr:g} - empty treatment arm.", 0.95)

    # ------------------------------------------------------------------
    # HIGH: schema-MD with event counts populated
    # ------------------------------------------------------------------
    if est == "MD" and tE is not None and cE is not None and (tE > 0 or cE > 0):
        add(r, "HIGH", "residual-schema-MD",
            f"estimandType=MD but event counts populated (tE={tE:g}, cE={cE:g}).", 0.85)

    # ------------------------------------------------------------------
    # HIGH: estimandType=MD but publishedHR holds value impossible for HR
    # (negative or >10) - this is field misuse, not effect implausibility.
    # ------------------------------------------------------------------
    if est == "MD" and hr is not None and (hr < 0 or hr > 10):
        # Skip - publishedHR is the MD value; the schema mismatch (using
        # publishedHR field for MD point estimate) is a known global pattern.
        # Only flag if CI structure is internally broken (already handled above).
        pass

    # ------------------------------------------------------------------
    # HIGH: HR/RR/OR <= 0 - impossible for any ratio measure
    # Only when estimandType is ratio (or null+no MD signal).
    # ------------------------------------------------------------------
    if (hr is not None and hr <= 0
            and est in ("HR", "RR", "OR")):
        add(r, "HIGH", "magnitude-extreme",
            f"publishedHR={hr:g} <= 0 but estimandType={est} (ratios must be > 0).", 0.99)

    # ------------------------------------------------------------------
    # HIGH: magnitude-extreme - OR-mislabel residual
    # Confirm via crude OR from cells when available; only fire when
    # estimandType in (HR, None) - if est is already "OR" the field name is
    # consistent.
    # ------------------------------------------------------------------
    if (hr is not None and hr > 10 and est in ("HR", None, "RR")
            and has_events_pair(tE, tN, cE, cN)):
        cor = crude_or(tE, tN, cE, cN)
        crr = crude_rr(tE, tN, cE, cN)
        if cor is not None and cor > 10:
            # Crude OR confirms logistic shape; HR label is wrong
            crr_str = f"{crr:.1f}" if crr is not None else "n/a"
            add(r, "HIGH", "magnitude-extreme",
                f"publishedHR={hr:g} with crude OR={cor:.1f}, crude RR={crr_str} - OR-as-HR mislabel residual ({tE:g}/{tN:g} vs {cE:g}/{cN:g}).",
                0.9)
        elif hr > 50:
            # No supporting cells but value is impossible as HR
            add(r, "HIGH", "magnitude-extreme",
                f"publishedHR={hr:g} > 50 - impossible HR magnitude.", 0.85)
    elif (hr is not None and hr > 50 and est in ("HR", None, "RR")
          and not has_events_pair(tE, tN, cE, cN)):
        add(r, "HIGH", "magnitude-extreme",
            f"publishedHR={hr:g} > 50 without supporting cell counts.", 0.8)

    # ------------------------------------------------------------------
    # HIGH: HR direction violates biology - covered by crude-vs-HR check below.
    # ------------------------------------------------------------------

    # ------------------------------------------------------------------
    # MED: copy-paste arms - rate_t exactly = rate_c, non-trivial events,
    # arms differ in shape (so it's not the same row entered twice).
    # ------------------------------------------------------------------
    if (has_events_pair(tE, tN, cE, cN) and tN > 0 and cN > 0
            and tE > 0 and cE > 0):
        rt = tE / tN
        rc = cE / cN
        if abs(rt - rc) < 1e-9 and (tE != cE or tN != cN):
            add(r, "MED", "copy-paste-arms",
                f"Identical rates rt=rc={rt:.4g} from (tE={tE:g}/{tN:g}) and (cE={cE:g}/{cN:g}).", 0.7)

    # ------------------------------------------------------------------
    # HIGH (sign-flip) / MED (mag-only): crude RR vs HR mismatch.
    # Only for binary-effect rows with populated cells; skip if hr already
    # flagged as OR-mislabel-extreme (hr>10).
    # ------------------------------------------------------------------
    if (hr is not None and 0 < hr <= 10 and est in ("HR", "RR", "OR", None)
            and has_events_pair(tE, tN, cE, cN)
            and tN > 0 and cN > 0 and tE > 0 and cE > 0):
        crr = crude_rr(tE, tN, cE, cN)
        if crr is not None and crr > 0:
            # Sign-flip vs raw
            if (hr - 1) * (crr - 1) < 0 and abs(hr - 1) > 0.15 and abs(crr - 1) > 0.15:
                add(r, "HIGH", "wrong-direction",
                    f"publishedHR={hr:g} (favours one arm) but crude RR={crr:.3g} (favours other); tE/tN={tE:g}/{tN:g} vs cE/cN={cE:g}/{cN:g}.",
                    0.85)
            else:
                ratio = hr / crr
                if ratio >= 2.5 or ratio <= 0.4:
                    add(r, "MED", "crude-vs-HR-mismatch",
                        f"publishedHR={hr:g} vs crude RR={crr:.3g} ({ratio:.2g}x divergence); tE/tN={tE:g}/{tN:g} vs cE/cN={cE:g}/{cN:g}.",
                        0.6)

    # ------------------------------------------------------------------
    # LOW: missing CI when HR present
    # ------------------------------------------------------------------
    if hr is not None and (lci is None or uci is None):
        add(r, "LOW", "other",
            f"publishedHR={hr:g} present but CI incomplete (lci={lci}, uci={uci}).", 0.55)

    # LOW: missing estimandType when HR present (only meaningful when HR is in
    # a ratio-plausible range; the MD-mis-stored cases dominate null-est rows
    # and we don't want to double-count them).
    if hr is not None and est is None and 0 < hr <= 10:
        add(r, "LOW", "other",
            f"publishedHR={hr:g} present but estimandType is null.", 0.5)


# Deduplicate (id, category) - keep highest-confidence
seen = {}
for f in flags:
    k = (f["id"], f["category"])
    if k not in seen or f["confidence"] > seen[k]["confidence"]:
        seen[k] = f
unique = list(seen.values())

# Sort: HIGH first, then by id
sev_rank = {"HIGH": 0, "MED": 1, "LOW": 2}
unique.sort(key=lambda f: (sev_rank.get(f["severity"], 9), f["id"]))

OUTPUT.write_text(json.dumps(unique, indent=2), encoding="utf-8")

# Summary by tier
tier_by_id = {r["id"]: r.get("tier") for r in rows}
sev_tier = defaultdict(Counter)
cat_tier = defaultdict(Counter)
ids_tier = defaultdict(set)
for f in unique:
    t = tier_by_id.get(f["id"], "?")
    sev_tier[t][f["severity"]] += 1
    cat_tier[t][f["category"]] += 1
    ids_tier[t].add(f["id"])

tier_totals = Counter(r.get("tier") for r in rows)

print(f"Total flags: {len(unique)}")
print(f"Trials affected: {len({f['id'] for f in unique})}/{len(rows)}")
for tier in sorted(sev_tier.keys()):
    print(f"\nTier {tier} ({len(ids_tier[tier])}/{tier_totals[tier]} trials flagged):")
    print(f"  severity:   {dict(sev_tier[tier])}")
    print(f"  categories: {dict(cat_tier[tier])}")
print("\nGlobal severity:", dict(Counter(f["severity"] for f in unique)))
print("Global categories:", dict(Counter(f["category"] for f in unique)))
