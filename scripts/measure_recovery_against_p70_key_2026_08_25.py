"""Can the registry reproduce the numbers a Cochrane meta-analysis row claims?

WHAT THIS USES. The join is now validated at scale -- 8,651 labels, resolution 74% held out,
zero of 1,688 pre-2005 labels carrying a registration, and the era stratification reproducing
the 2005 ICMJE policy change the pipeline was never told about. That gives an ANSWER KEY: 967
(review, study) pairs whose trial registration is known. This measures what the registry can
give back for them.

THE UNIT AND THE TIERS. Two different things are recoverable and they are never summed:

  TIER A  DENOMINATORS. Do the two arm sizes the Cochrane row states appear as arm sizes in
          the registry's posted participant flow? Unit: the trial.
  TIER B  EVENT COUNTS. Does any posted outcome measure report, for two arms, the two event
          counts the Cochrane row states? Unit: the row, because one trial contributes many.

A trial with no posted results supports neither, and that is a THIRD state -- NO RESULTS
POSTED -- not a recovery failure. Conflating "the registry does not have it" with "the
registry disagrees" would turn a transparency fact into an accuracy claim.

MATCHING IS EXACT. Arm sizes and event counts must match to the integer. A tolerance would
make the measurement a statement about how close is close enough, and there is no principled
value for that. Near-misses are counted separately so the exactness is visible rather than
hidden: a pair off by one or two is recorded as NEAR, never as recovered.

THE NULL, and it carries more weight here than anywhere else in this programme. Small integers
collide. An arm of 100 and an arm of 100 are the same number in every trial that has one, so
"the registry contains these two numbers" is a weak claim by construction. Every Cochrane row
is therefore ALSO scored against a DIFFERENT trial's registry record, by a fixed derangement.
The null is the floor; the difference between the rate and the null is the only part that is
about recovery.

Usage:  python measure_recovery_against_p70_key_2026_08_25.py [--limit N]
"""
import io
import json
import os
import re
import subprocess
import sys
import time

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(REPO, "scripts"))
SCRATCH = (r"F:\claude-temp\claude\F--rapidmeta-finerenone"
           r"\e2e2a1d5-c19e-44de-90ab-690dbc5235a1\scratchpad\p70")
JOIN = os.path.join(REPO, "outputs", "join_end_to_end_wide_2026_08_25.json")
COUNTS = os.path.join(SCRATCH, "counts_wide.json")
CACHE = os.path.join(SCRATCH, "ctgov_full")
OUT = os.path.join(REPO, "outputs", "recovery_against_p70_key_2026_08_25.json")

STUDY = "https://clinicaltrials.gov/api/v2/studies/%s"
NEAR = 2


def get(nct):
    os.makedirs(CACHE, exist_ok=True)
    fp = os.path.join(CACHE, nct + ".json")
    if os.path.exists(fp) and os.path.getsize(fp) > 200:
        return io.open(fp, encoding="utf-8", errors="replace").read()
    for attempt in (1, 2, 3):
        r = subprocess.run(["curl", "-sSL", "-g", "--max-time", "90", STUDY % nct],
                           capture_output=True)
        body = (r.stdout or b"").decode("utf-8", "replace")
        if body.lstrip().startswith("{") and '"protocolSection"' in body:
            io.open(fp, "w", encoding="utf-8").write(body)
            return body
        time.sleep(2 * attempt)
    return None


def _int(x):
    try:
        return int(str(x).replace(",", "").strip())
    except (ValueError, AttributeError):
        return None


def arm_sizes(rec):
    """Every per-arm participant count the registry posts, from flow then baseline."""
    rs = rec.get("resultsSection") or {}
    out = []
    pf = rs.get("participantFlowModule") or {}
    for per in (pf.get("periods") or []):
        for ms in (per.get("milestones") or []):
            if (ms.get("type") or "").upper() != "STARTED":
                continue
            for a in (ms.get("achievements") or []):
                v = _int(a.get("numSubjects"))
                if v:
                    out.append(v)
    if not out:
        bc = rs.get("baselineCharacteristicsModule") or {}
        for den in (bc.get("denoms") or []):
            for c in (den.get("counts") or []):
                v = _int(c.get("value"))
                if v:
                    out.append(v)
    return out


def event_pairs(rec):
    """Every (a, b) pair of per-group counts the registry posts for any outcome measure."""
    rs = rec.get("resultsSection") or {}
    pairs = []
    for om in ((rs.get("outcomeMeasuresModule") or {}).get("outcomeMeasures") or []):
        for cl in (om.get("classes") or []):
            for cat in (cl.get("categories") or []):
                vals = [_int(m.get("value")) for m in (cat.get("measurements") or [])]
                vals = [v for v in vals if v is not None]
                if len(vals) >= 2:
                    pairs.append(vals)
    ae = rs.get("adverseEventsModule") or {}
    for key in ("seriousEvents", "otherEvents"):
        for ev in (ae.get(key) or []):
            vals = [_int(s.get("numAffected")) for s in (ev.get("stats") or [])]
            vals = [v for v in vals if v is not None]
            if len(vals) >= 2:
                pairs.append(vals)
    return pairs


def has_pair(pool, a, b, slack=0):
    """Can two DISTINCT positions in pool carry a and b (within slack)?"""
    if a is None or b is None:
        return False
    for i, x in enumerate(pool):
        if abs(x - a) > slack:
            continue
        for j, y in enumerate(pool):
            if i != j and abs(y - b) <= slack:
                return True
    return False


def pair_in_groups(pairs, a, b, slack=0):
    for vals in pairs:
        if has_pair(vals, a, b, slack):
            return True
    return False


def run_controls():
    from instrument_controls import require_controls
    rec = {"resultsSection": {"participantFlowModule": {"periods": [{"milestones": [
        {"type": "STARTED", "achievements": [{"numSubjects": "4209"},
                                             {"numSubjects": "4233"}]}]}]}}}
    sizes = arm_sizes(rec)
    require_controls(
        "recovery_p70 (denominators)",
        ("the two arm sizes the row states are found in the posted flow",
         has_pair(sizes, 4209, 4233), True),
        ("a pair the registry does NOT post is reported as found",
         has_pair(sizes, 1234, 5678), True))
    require_controls(
        "recovery_p70 (distinctness)",
        ("a row claiming the SAME size twice needs two arms of that size",
         has_pair([4209, 4233], 4209, 4209), False),
        ("one arm is allowed to satisfy both halves of a pair",
         has_pair([4209], 4209, 4209), True))


def main():
    run_controls()
    raw = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace",
                           write_through=True)

    def log(s):
        raw.write(s + chr(10))
        raw.flush()

    join = json.load(io.open(JOIN, encoding="utf-8"))["rows"]
    counts = json.load(io.open(COUNTS, encoding="utf-8"))
    by_trial = {}
    for rv in counts:
        for r in (rv.get("rows") or []):
            if r.get("kind") == "dichotomous":
                by_trial.setdefault((rv["file"], r["study"]), []).append(r)

    keyed = []
    for j in join:
        if not j.get("nct"):
            continue
        rows = by_trial.get((j.get("review"), j.get("label")))
        if rows:
            keyed.append({"review": j["review"], "label": j["label"], "nct": j["nct"],
                          "year": j.get("year"), "rows": rows})
    limit = None
    if "--limit" in sys.argv:
        limit = int(sys.argv[sys.argv.index("--limit") + 1])
        keyed = keyed[:limit]

    log("answer key: %d (review, study) pairs with a known NCT and >=1 dichotomous row"
        % len(keyed))
    log("dichotomous rows behind them: %d" % sum(len(k["rows"]) for k in keyed))
    log("matching is EXACT; near-misses (<=%d) counted separately, never as recovered" % NEAR)
    log("")

    # fixed derangement for the null
    ncts = [k["nct"] for k in keyed]
    null_of = {k["nct"]: ncts[(i + 1) % len(ncts)] for i, k in enumerate(keyed)}

    recs, missing = {}, []
    for i, k in enumerate(keyed, 1):
        if k["nct"] in recs:
            continue
        body = get(k["nct"])
        if body is None:
            missing.append(k["nct"])
            continue
        try:
            recs[k["nct"]] = json.loads(body)
        except ValueError:
            missing.append(k["nct"])
        if i % 50 == 0:
            log("   fetched %d/%d" % (i, len(keyed)))
        time.sleep(0.2)

    out = []
    tA = {"n": 0, "no_results": 0, "hit": 0, "near": 0, "null": 0}
    tB = {"n": 0, "no_results": 0, "hit": 0, "near": 0, "null": 0}
    for k in keyed:
        rec = recs.get(k["nct"])
        if rec is None:
            out.append(dict(k, rows=len(k["rows"]), status="MISSING"))
            continue
        posted = bool(rec.get("hasResults"))
        sizes = arm_sizes(rec) if posted else []
        pairs = event_pairs(rec) if posted else []
        nrec = recs.get(null_of[k["nct"]]) or {}
        nsizes = arm_sizes(nrec)
        npairs = event_pairs(nrec)

        # TIER A -- trial level, using the first row that states both denominators
        den = next((r for r in k["rows"] if r.get("e_n") and r.get("c_n")), None)
        a_state = None
        if den:
            tA["n"] += 1
            if not posted:
                tA["no_results"] += 1
                a_state = "NO RESULTS POSTED"
            elif has_pair(sizes, _int(den["e_n"]), _int(den["c_n"])):
                tA["hit"] += 1
                a_state = "recovered"
            elif has_pair(sizes, _int(den["e_n"]), _int(den["c_n"]), NEAR):
                tA["near"] += 1
                a_state = "near"
            else:
                a_state = "not found"
            if has_pair(nsizes, _int(den["e_n"]), _int(den["c_n"])):
                tA["null"] += 1

        # TIER B -- row level
        b_hits = 0
        for r in k["rows"]:
            tB["n"] += 1
            if not posted:
                tB["no_results"] += 1
                continue
            a, b = _int(r.get("e_cases")), _int(r.get("c_cases"))
            if pair_in_groups(pairs, a, b):
                tB["hit"] += 1
                b_hits += 1
            elif pair_in_groups(pairs, a, b, NEAR):
                tB["near"] += 1
            if pair_in_groups(npairs, a, b):
                tB["null"] += 1

        out.append({"review": k["review"], "label": k["label"], "nct": k["nct"],
                    "year": k.get("year"), "rows": len(k["rows"]), "has_results": posted,
                    "tierA": a_state, "tierB_hits": b_hits,
                    "n_arm_sizes": len(sizes), "n_outcome_pairs": len(pairs)})

    def line(name, t):
        n = t["n"]
        if not n:
            log("%s: NOT MEASURABLE -- nothing to score" % name)
            return
        assessable = n - t["no_results"]
        log("%s" % name)
        log("   units                       : %d" % n)
        log("   NO RESULTS POSTED           : %d  (%.0f%%)  -- a third state, not a failure"
            % (t["no_results"], 100.0 * t["no_results"] / n))
        log("   assessable                  : %d" % assessable)
        if assessable:
            log("   RECOVERED exactly           : %d / %d  (%.0f%% of assessable)"
                % (t["hit"], assessable, 100.0 * t["hit"] / assessable))
            log("   near (<=%d, NOT recovered)   : %d" % (NEAR, t["near"]))
        log("   NULL, a different trial     : %d / %d  (%.0f%%)"
            % (t["null"], n, 100.0 * t["null"] / n))

    log("")
    log("trials fetched %d   MISSING %d" % (len(recs), len(missing)))
    log("")
    line("TIER A -- arm denominators (unit: trial)", tA)
    log("")
    line("TIER B -- event counts (unit: Cochrane row)", tB)
    log("")
    log("Tier A and Tier B are different units and are never summed.")

    json.dump({"key": "967-pair answer key from the validated join, restricted to pairs with "
                      "at least one dichotomous Cochrane row",
               "matching": "exact integers; near <= %d counted separately" % NEAR,
               "third_state": "NO RESULTS POSTED is reported separately from a recovery "
                              "failure -- the registry not having it is not the registry "
                              "disagreeing",
               "tierA": tA, "tierB": tB, "fetched": len(recs), "missing": missing,
               "rows": out},
              io.open(OUT, "w", encoding="utf-8"), indent=1)
    log("wrote %s" % os.path.relpath(OUT, REPO))
    return 0


if __name__ == "__main__":
    sys.exit(main())
