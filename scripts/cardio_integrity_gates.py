#!/usr/bin/env python
"""Per-trial data-integrity gates for a cardiology RapidMeta app.

Generalises the HFrEF gate battery (outputs/HFREF_INTEGRITY_GATES_2026-07-30.md)
so any cardio app can be run through the same checks.

Gates
  G1   per-arm count plausibility (integer, 0 <= e <= N, denominators agree)
  G1b  effect recompute from the 2x2 (logRR/logOR reproduce)
  G2   GRIM/GRIMMER            -- N/A for binary per-arm counts; stated, not skipped
  G3   Benford first-digit on counts and denominators (advisory)
  G4   arm-balance ratio (advisory)
  G5   identifier well-formedness (NCT / PMID present and valid)
  G6   ClinicalTrials.gov registry concordance: phase, enrolment, masking, arm labels
  G6b  RATE-vs-PROPORTION unit gate  <-- new; see below
  G7   Fragility Index (Walsh 2014, Fisher exact), trial-level only
  G8   published-effect vs crude-2x2 direction concordance

G6b is the gate this battery gained from the APIXABAN_ACS pilot. ClinicalTrials.gov
posts many primary outcomes with `unitOfMeasure` = "percentage of participants/100-pt
years" or "Percentage per year" -- a RATE over person-time, not a proportion. An
extractor that multiplies such a value by an arm denominator manufactures an event
count that exists in no source. G6b recomputes `value * denominator / 100` for every
posted primary outcome of every arm and BLOCKS when a ledger count reproduces it
while the unit is not a plain proportion.

Usage:
    python scripts/cardio_integrity_gates.py APIXABAN_ACS_AUTO_FULL_REVIEW.html
    python scripts/cardio_integrity_gates.py <file> --no-net   # offline gates only
"""
from __future__ import annotations

import argparse
import io
import json
import math
import os
import re
import sys
import urllib.error
import urllib.request

if __name__ == "__main__":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from cardio_inventory import balanced_slice, depth1_keys  # noqa: E402

CTGOV = "https://clinicaltrials.gov/api/v2/studies/"
# Units that ARE a plain proportion of participants. Anything else posted as a
# percentage is a rate and must not be multiplied by a denominator.
PROPORTION_UNITS = {
    "percentage of participants", "percentage of subjects", "percent of participants",
    "participants", "number of participants", "count of participants",
}


# ---------------------------------------------------------------- ledger reading
def read_ledger(path: str) -> list[dict]:
    s = open(path, encoding="utf-8", errors="replace").read()
    m = RE_REALDATA.search(s)
    if not m:
        return []
    block = balanced_slice(s, m.end() - 1)
    rows = []
    for key in depth1_keys(block):
        seg = _value_for_key(block, key)
        if seg is None:
            continue
        rows.append({
            "key": key,
            "nct": (re.search(r"NCT\d{8}", key) or [None])[0]
            if re.search(r"NCT\d{8}", key) else None,
            "name": _sfield(seg, "name"),
            "pmid": _sfield(seg, "pmid"),
            "phase": _sfield(seg, "phase"),
            "year": _nfield(seg, "year"),
            "tE": _nfield(seg, "tE"), "tN": _nfield(seg, "tN"),
            "cE": _nfield(seg, "cE"), "cN": _nfield(seg, "cN"),
            "pubHR": _nfield(seg, "pubHR"),
            "pubHR_LCI": _nfield(seg, "pubHR_LCI"),
            "pubHR_UCI": _nfield(seg, "pubHR_UCI"),
            "outcome_title": _sfield(seg, "title"),
        })
    return rows


RE_REALDATA = re.compile(r"realData\s*:\s*\{")


def _value_for_key(block: str, key: str) -> str | None:
    for pat in (rf'"{re.escape(key)}"\s*:\s*', rf"'{re.escape(key)}'\s*:\s*",
                rf"\b{re.escape(key)}\s*:\s*"):
        m = re.search(pat, block)
        if m:
            return balanced_slice(block, m.end())
    return None


def _sfield(seg: str, name: str) -> str | None:
    m = re.search(rf'\b{name}\s*:\s*"([^"]*)"', seg)
    return m.group(1) if m else None


def _nfield(seg: str, name: str):
    m = re.search(rf"\b{name}\s*:\s*(-?\.?\d[\d.eE+-]*|null)", seg)
    if not m:
        return None
    v = m.group(1)
    if v == "null":
        return None
    f = float(v)
    return int(f) if f.is_integer() else f


# ---------------------------------------------------------------- registry
def ctgov(nct: str, fields: str) -> dict:
    url = f"{CTGOV}{nct}?fields={fields}"
    try:
        with urllib.request.urlopen(url, timeout=30) as r:
            return json.loads(r.read().decode("utf-8"))
    except (urllib.error.URLError, TimeoutError, json.JSONDecodeError) as e:
        # Fail LOUD: an unreachable registry is "not checked", never "concordant".
        return {"_error": f"{type(e).__name__}: {e}"}


def registry_facts(nct: str) -> dict:
    d = ctgov(nct, ",".join([
        "protocolSection.identificationModule.acronym",
        "protocolSection.identificationModule.briefTitle",
        "protocolSection.designModule.phases",
        "protocolSection.designModule.enrollmentInfo",
        "protocolSection.designModule.designInfo",
        "protocolSection.statusModule.overallStatus",
        "resultsSection.outcomeMeasuresModule",
        "hasResults",
    ]))
    if "_error" in d:
        return d
    p = d.get("protocolSection", {})
    dm = p.get("designModule", {})
    out = {
        "acronym": p.get("identificationModule", {}).get("acronym"),
        "brief_title": p.get("identificationModule", {}).get("briefTitle"),
        "phases": dm.get("phases"),
        "enrollment": (dm.get("enrollmentInfo") or {}).get("count"),
        "masking": ((dm.get("designInfo") or {}).get("maskingInfo") or {}).get("masking"),
        "status": p.get("statusModule", {}).get("overallStatus"),
        "has_results": d.get("hasResults"),
        "primary_outcomes": [],
    }
    for om in (d.get("resultsSection", {}).get("outcomeMeasuresModule", {})
               .get("outcomeMeasures", []) or []):
        if om.get("type") != "PRIMARY":
            continue
        groups = {g.get("id"): g.get("title") for g in om.get("groups", []) or []}
        denoms = {}
        for dn in om.get("denoms", []) or []:
            for c in dn.get("counts", []) or []:
                denoms[c.get("groupId")] = c.get("value")
        vals = {}
        for cl in om.get("classes", []) or []:
            for cat in cl.get("categories", []) or []:
                for meas in cat.get("measurements", []) or []:
                    vals[meas.get("groupId")] = meas.get("value")
        out["primary_outcomes"].append({
            "title": om.get("title"), "unit": om.get("unitOfMeasure"),
            "param": om.get("paramType"), "groups": groups,
            "denoms": denoms, "values": vals,
        })
    return out


# ---------------------------------------------------------------- stats
def fisher_p(a: int, b: int, c: int, d: int) -> float:
    """Two-sided Fisher exact on [[a,b],[c,d]]."""
    def lc(n, k):
        return math.lgamma(n + 1) - math.lgamma(k + 1) - math.lgamma(n - k + 1)

    n = a + b + c + d
    r1, c1 = a + b, a + c
    obs = lc(r1, a) + lc(n - r1, c) - lc(n, c1)
    tot = 0.0
    lo, hi = max(0, c1 - (n - r1)), min(r1, c1)
    for x in range(lo, hi + 1):
        p = lc(r1, x) + lc(n - r1, c1 - x) - lc(n, c1)
        if p <= obs + 1e-9:
            tot += math.exp(p)
    return min(1.0, tot)


def fragility_index(tE, tN, cE, cN, alpha=0.05):
    """Walsh 2014: min single-arm event moves to flip significance.
    Returns (fi, p0, direction) or (None, p0, reason) when undefined."""
    p0 = fisher_p(tE, tN - tE, cE, cN - cE)
    if p0 >= alpha:
        return None, p0, "not significant"
    for fi in range(1, max(tN, cN) + 1):
        # Move events in the direction that weakens the result.
        if tE / tN < cE / cN:
            if tE + fi > tN:
                break
            if fisher_p(tE + fi, tN - tE - fi, cE, cN - cE) >= alpha:
                return fi, p0, "added to treatment arm"
        else:
            if cE + fi > cN:
                break
            if fisher_p(tE, tN - tE, cE + fi, cN - cE - fi) >= alpha:
                return fi, p0, "added to control arm"
    return None, p0, "cannot be flipped within arm size"


def _isnum(v) -> bool:
    try:
        float(v)
        return True
    except (TypeError, ValueError):
        return False


BENFORD = [math.log10(1 + 1 / d) for d in range(1, 10)]


def benford(nums: list[int]):
    firsts = [int(str(abs(n))[0]) for n in nums if n and abs(n) >= 1]
    k = len(firsts)
    if k < 30:
        return {"n": k, "verdict": "UNDERPOWERED — Benford needs >=30 values",
                "chi2": None, "crit": 15.507}
    obs = [firsts.count(d) for d in range(1, 10)]
    chi2 = sum((o - k * e) ** 2 / (k * e) for o, e in zip(obs, BENFORD))
    return {"n": k, "chi2": round(chi2, 3), "crit": 15.507,
            "verdict": "no fabrication signal" if chi2 < 15.507 else "SIGNAL — investigate",
            "observed": obs}


# ---------------------------------------------------------------- gates
def run(path: str, use_net: bool = True) -> dict:
    rows = read_ledger(path)
    findings: list[dict] = []

    def add(gate, sev, trial, msg, **extra):
        findings.append({"gate": gate, "severity": sev, "trial": trial,
                         "message": msg, **extra})

    # ---- G1 per-arm count plausibility
    for r in rows:
        tag = r["name"] or r["key"]
        for lab, e, n in (("treatment", r["tE"], r["tN"]), ("control", r["cE"], r["cN"])):
            if e is None or n is None:
                add("G1", "MEDIUM", tag, f"{lab} arm has a missing count or denominator "
                                         f"(e={e}, N={n})")
                continue
            if not float(e).is_integer() or not float(n).is_integer():
                add("G1", "HIGH", tag, f"{lab} arm count is non-integer (e={e}, N={n})")
            if n <= 0:
                add("G1", "HIGH", tag, f"{lab} arm denominator is not positive (N={n})")
            elif e < 0 or e > n:
                add("G1", "HIGH", tag, f"{lab} arm violates 0<=e<=N (e={e}, N={n})")

    # ---- G4 arm balance
    for r in rows:
        if r["tN"] and r["cN"]:
            hi, lo = max(r["tN"], r["cN"]), min(r["tN"], r["cN"])
            ratio = hi / lo
            if ratio >= 1.5:
                add("G4", "ADVISORY", r["name"] or r["key"],
                    f"arm-balance ratio {ratio:.2f}:1 ({r['tN']} vs {r['cN']}) — "
                    f"confirm the randomisation ratio in the source", ratio=round(ratio, 3))

    # ---- G5 identifiers
    for r in rows:
        tag = r["name"] or r["key"]
        if not r["nct"]:
            add("G5", "MEDIUM", tag, f"ledger key '{r['key']}' contains no valid NCT id")
        if not r["pmid"]:
            add("G5", "MEDIUM", tag, "no PMID — the extraction cannot be source-verified")
        elif not re.fullmatch(r"\d{5,9}", r["pmid"]):
            add("G5", "HIGH", tag, f"malformed PMID '{r['pmid']}'")

    # ---- G3 Benford
    pool = [v for r in rows for v in (r["tE"], r["cE"], r["tN"], r["cN"])
            if isinstance(v, int)]
    bf = benford(pool)

    # ---- G7 fragility + G8 direction concordance
    frag = []
    for r in rows:
        if None in (r["tE"], r["tN"], r["cE"], r["cN"]):
            continue
        # Fisher's exact is undefined on an implausible 2x2. G1 has already raised
        # those rows; computing a fragility index on them would crash (or worse,
        # return a number). Skip and say so.
        if not (0 <= r["tE"] <= r["tN"] and 0 <= r["cE"] <= r["cN"]
                and r["tN"] > 0 and r["cN"] > 0):
            frag.append({"trial": r["name"] or r["key"], "fi": None, "p": None,
                         "note": "SKIPPED — 2x2 failed G1 plausibility; FI undefined"})
            continue
        fi, p0, note = fragility_index(r["tE"], r["tN"], r["cE"], r["cN"])
        frag.append({"trial": r["name"] or r["key"], "fi": fi, "p": round(p0, 5),
                     "note": note})
        if fi is not None and fi <= 3:
            add("G7", "HIGH", r["name"] or r["key"],
                f"fragility index {fi} at p={p0:.4f} — {fi} event(s) overturn it", fi=fi)
        # G8: does the crude 2x2 point the same way as the published effect?
        if r["pubHR"] is not None and r["tN"] and r["cN"]:
            crude = (r["tE"] / r["tN"]) / (r["cE"] / r["cN"]) if r["cE"] else None
            if crude:
                pub_lt1, crude_lt1 = r["pubHR"] < 1, crude < 1
                if pub_lt1 != crude_lt1:
                    add("G8", "HIGH", r["name"] or r["key"],
                        f"published effect {r['pubHR']} and crude 2x2 RR {crude:.3f} point "
                        f"in OPPOSITE directions — counts and effect cannot both be right",
                        pubHR=r["pubHR"], crude_rr=round(crude, 4))

    # ---- G6 / G6b registry
    registry: dict = {}
    if use_net:
        for r in rows:
            if not r["nct"]:
                continue
            f = registry_facts(r["nct"])
            registry[r["nct"]] = f
            tag = r["name"] or r["key"]
            if "_error" in f:
                add("G6", "MEDIUM", tag,
                    f"registry NOT CHECKED for {r['nct']}: {f['_error']} — "
                    f"this is 'unchecked', not 'concordant'")
                continue

            # phase
            reg_ph = (f.get("phases") or [""])[0].replace("PHASE", "")
            led_ph = {"I": "1", "II": "2", "III": "3", "IV": "4",
                      "1": "1", "2": "2", "3": "3", "4": "4"}.get(
                          (r["phase"] or "").strip().upper())
            if reg_ph and led_ph and reg_ph != led_ph:
                add("G6", "HIGH", tag,
                    f"phase discordance: ledger says phase {r['phase']}, registry says "
                    f"{f['phases']} for {r['nct']}",
                    ledger_phase=r["phase"], registry_phase=f["phases"])

            # enrolment vs ledger total
            led_tot = (r["tN"] or 0) + (r["cN"] or 0)
            reg_n = f.get("enrollment")
            if reg_n and led_tot and led_tot > reg_n:
                add("G6", "HIGH", tag,
                    f"ledger total N {led_tot} EXCEEDS registry enrolment {reg_n}")
            elif reg_n and led_tot and led_tot < reg_n * 0.9:
                add("G6", "ADVISORY", tag,
                    f"ledger total N {led_tot} is {100*led_tot/reg_n:.0f}% of registry "
                    f"enrolment {reg_n} — arms may be dropped or pooled; state which")

            # ---- G6b RATE-vs-PROPORTION unit gate (the pilot's root cause)
            for om in f.get("primary_outcomes", []):
                unit = (om.get("unit") or "").strip().lower()
                is_prop = unit in PROPORTION_UNITS
                # Candidate denominators: every registry arm denominator PLUS the
                # ledger's own two. An extractor can invent a denominator that
                # matches no arm (the AUGUSTUS 1153 case), so registry-only
                # candidates silently miss the very worst instances.
                cand: list[tuple[str, float]] = []
                for dn_gid, dn in (om.get("denoms") or {}).items():
                    try:
                        cand.append((f"registry:{(om.get('groups') or {}).get(dn_gid, dn_gid)}",
                                     float(dn)))
                    except (TypeError, ValueError):
                        pass
                reg_denoms = {c[1] for c in cand}
                for led_n_lab, led_n_val in (("ledger:tN", r["tN"]), ("ledger:cN", r["cN"])):
                    if led_n_val and float(led_n_val) not in reg_denoms:
                        cand.append((led_n_lab + " (MATCHES NO REGISTRY ARM)",
                                     float(led_n_val)))

                for gid, val in (om.get("values") or {}).items():
                    try:
                        v = float(val)
                    except (TypeError, ValueError):
                        continue
                    grp = (om.get("groups") or {}).get(gid, gid)
                    for led_e, led_n, side in ((r["tE"], r["tN"], "treatment"),
                                               (r["cE"], r["cN"], "control")):
                        if led_e is None or not led_n:
                            continue
                        for dlab, dnv in cand:
                            if abs(v * dnv / 100.0 - led_e) > 0.75:
                                continue
                            if not is_prop:
                                add("G6b", "CRITICAL", tag,
                                    f"{side} count {led_e} reproduces posted value {v} "
                                    f"x {dlab}={dnv:.0f} / 100, but the posted unit is "
                                    f"'{om.get('unit')}' — a RATE over person-time, NOT a "
                                    f"proportion. The count is MANUFACTURED and appears "
                                    f"in no source.",
                                    posted_value=v, posted_unit=om.get("unit"),
                                    posted_group=grp, denom_used=dlab,
                                    ledger_count=led_e)
                            elif "MATCHES NO REGISTRY ARM" in dlab:
                                add("G6b", "HIGH", tag,
                                    f"{side} count {led_e} = posted {v}% of group '{grp}' "
                                    f"applied to {dlab}={dnv:.0f} — the denominator "
                                    f"corresponds to no arm of this trial",
                                    posted_group=grp, denom_used=dlab, ledger_count=led_e)

                # ---- G6c ARM ORIENTATION
                # Which registry group does each ledger slot actually reproduce?
                # If the TREATMENT slot reproduces a placebo/comparator group, the
                # ledger has the arms the wrong way round and every effect estimate
                # computed from it points the wrong way.
                def owner(led_e, led_n):
                    hits = []
                    for gid2, val2 in (om.get("values") or {}).items():
                        try:
                            v2 = float(val2)
                        except (TypeError, ValueError):
                            continue
                        for dlab, dnv in cand:
                            if led_e is not None and abs(v2 * dnv / 100.0 - led_e) <= 0.75:
                                hits.append((om.get("groups") or {}).get(gid2, gid2))
                    return sorted(set(hits))

                t_owner, c_owner = owner(r["tE"], r["tN"]), owner(r["cE"], r["cN"])

                # ---- G6d POSTED-RESULTS RECONCILABILITY
                # The trial HAS posted results, yet the ledger count reproduces no
                # arm of them. That count has no located source (the CARMEN class).
                # Only assert this for proportion-unit outcomes, where a count is
                # genuinely recoverable; for rate units, non-recovery is expected.
                if is_prop:
                    for led_e, side, own in ((r["tE"], "treatment", t_owner),
                                             (r["cE"], "control", c_owner)):
                        if led_e is None or own:
                            continue
                        recoverable = sorted({
                            round(float(v2) * dnv / 100.0)
                            for v2 in (om.get("values") or {}).values()
                            for _, dnv in cand
                            if _isnum(v2)
                        })
                        add("G6d", "CRITICAL", tag,
                            f"{side} count {led_e} reconciles with NO arm of the posted "
                            f"results for outcome '{(om.get('title') or '')[:60]}'. "
                            f"Recoverable counts are {recoverable}. This count has no "
                            f"located source.",
                            ledger_count=led_e, recoverable=recoverable,
                            outcome=om.get("title"))
                pl = re.compile(r"placebo|vitamin k|comparator|control|no aspirin", re.I)
                if t_owner and all(pl.search(o) for o in t_owner):
                    add("G6c", "CRITICAL", tag,
                        f"ARMS SWAPPED: the ledger's TREATMENT slot (e={r['tE']}, "
                        f"N={r['tN']}) reproduces the registry's {t_owner} group. Every "
                        f"effect estimate from this row points the wrong way.",
                        treatment_slot_owner=t_owner, control_slot_owner=c_owner)
                elif t_owner and c_owner and t_owner == c_owner:
                    add("G6c", "MEDIUM", tag,
                        f"both ledger slots reproduce the same registry group(s) "
                        f"{t_owner} — arm attribution is ambiguous and unverified",
                        treatment_slot_owner=t_owner, control_slot_owner=c_owner)

    return {
        "app": os.path.basename(path),
        "k_trials": len(rows),
        "n_arm_rows": 2 * len(rows),
        "ledger": rows,
        "gates": {
            "G1_G4_G5_G6_G6b_G7_G8_findings": findings,
            "G2_grim": {"applicable": False,
                        "why": "binary per-arm counts only; no means or SDs to "
                               "reconstruct. N/A — not passed."},
            "G3_benford": bf,
            "G7_fragility": frag,
        },
        "registry": registry,
        "counts": {
            "CRITICAL": sum(1 for f in findings if f["severity"] == "CRITICAL"),
            "HIGH": sum(1 for f in findings if f["severity"] == "HIGH"),
            "MEDIUM": sum(1 for f in findings if f["severity"] == "MEDIUM"),
            "ADVISORY": sum(1 for f in findings if f["severity"] == "ADVISORY"),
        },
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("app")
    ap.add_argument("--no-net", action="store_true")
    ap.add_argument("--out")
    args = ap.parse_args()

    path = args.app if os.path.isabs(args.app) else os.path.join(REPO, args.app)
    res = run(path, use_net=not args.no_net)

    stem = re.sub(r"(_AUTO)?(_FULL)?_REVIEW\.html$", "", os.path.basename(path))
    out = args.out or os.path.join(REPO, "outputs", f"{stem.lower()}_integrity_gates.json")
    os.makedirs(os.path.dirname(out), exist_ok=True)
    with open(out, "w", encoding="utf-8") as fh:
        json.dump(res, fh, indent=1)

    c = res["counts"]
    print(f"APP: {res['app']}")
    print(f"  k trials = {res['k_trials']}   arm rows = {res['n_arm_rows']}")
    print(f"  CRITICAL={c['CRITICAL']}  HIGH={c['HIGH']}  MEDIUM={c['MEDIUM']}  "
          f"ADVISORY={c['ADVISORY']}")
    print(f"  G2 GRIM: N/A ({res['gates']['G2_grim']['why'][:52]}…)")
    b = res["gates"]["G3_benford"]
    print(f"  G3 Benford: n={b['n']} chi2={b['chi2']} -> {b['verdict']}")
    print("  G7 fragility:")
    for f in res["gates"]["G7_fragility"]:
        print(f"      {f['trial'][:28]:<28} FI={f['fi']!s:<5} p={f['p']}  {f['note']}")
    print("\n  FINDINGS")
    for f in res["gates"]["G1_G4_G5_G6_G6b_G7_G8_findings"]:
        print(f"   [{f['severity']:<8}] {f['gate']:<4} {f['trial'][:24]:<24} {f['message']}")
    print(f"\nwrote {out}")
    # A gate that cannot fail is theatre: exit non-zero when blocking findings exist.
    return 1 if (c["CRITICAL"] or c["HIGH"]) else 0


if __name__ == "__main__":
    raise SystemExit(main())
