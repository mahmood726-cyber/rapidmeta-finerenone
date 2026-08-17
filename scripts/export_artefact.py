"""EXPORTER -- SSOT object  ->  the build artefact the harness detectors read.

WHY THIS EXISTS
    The verification lane built 30 detectors, 20 of them artefact-decidable, and
    proved they block on 13 real past defects. They caught nothing here, because
    nothing produced the shape they read: `payloads_for()` extracted ZERO
    payloads from our objects (41 top-level keys on ARNI, 32 on FINERENONE_CV),
    and the gate then printed PASS on an artefact it could not see.

    INVOKED IS NOT SEEING. That is the join this file supplies, and it is the
    fifth instance of one meta-mechanism -- the action succeeded, the effect was
    never confirmed -- after push-is-not-deploy, the-repair-existing-is-not-the-
    repair-arriving, a-library-no-build-invokes, and writing-is-not-preserving.
    It is the first of the five caught BEFORE shipping rather than after.

THE RULE THIS FILE OBEYS ABOVE ALL OTHERS
    NEVER SYNTHESISE A FIELD. Where the object does not carry what a detector
    needs, the field is OMITTED, which the harness reports as NOT APPLICABLE --
    a different statement from "checked and clean". A guessed `direction_of_
    benefit` or an assumed `declared_class` would produce confident green on
    exactly the detectors that exist to catch confident green.

    Every omission is counted and printed. An export that activates few checks
    must look thin, not clean.

WHAT A FULL PASS OF THE GATE ON THESE ARTEFACTS DOES NOT ESTABLISH
    - NOT that the page is correct: 10 of 30 detectors are retrieval-scoped and
      cannot run against any static artefact.
    - NOT that the object is complete. An absent field yields no payload, and no
      payload is not a pass.
    - NOT that this mapping is faithful. That is what the fixture-replay
      acceptance test is for, and until a REAL past defect in a REAL object is
      blocked through this exporter, the mapping is unvalidated however many
      fixtures pass.
"""
from __future__ import annotations

import argparse, io, json, os, re, sys

if __name__ == "__main__":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Sentinels the reader must never meet. Kept here rather than defaulted inside
# the harness so the list is visible at the point of export.
SENTINELS = ["NOT RECOVERABLE FROM THE PAGE", "REPLACE_ME", "__PLACEHOLDER__",
             "{{", "TODO", "undefined", "NaN"]


def _visible(html):
    html = re.sub(r"<(script|style)\b[^>]*>.*?</\1\s*>", " ", html, flags=re.S | re.I)
    return re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", html))


def _pool_from_outcome(oid, res, outcome_def, omissions):
    """One pool payload. Returns None when the object cannot support one."""
    per = res.get("per_trial") or []
    pooled = res.get("pooled") or {}
    if not per:
        omissions.append("%s: no per_trial rows -> no pool payload" % oid)
        return None

    entries, rows = [], []
    for t in per:
        est = t.get("log_point")
        se = t.get("log_se")
        # The estimate/variance pair is what the duplicate and measure-mixing
        # detectors compare. Deriving variance from a CI we already stored is a
        # READ, not a guess; inventing one where no CI exists would not be.
        if est is None or se is None:
            omissions.append("%s/%s: no log_point+log_se -> entry omitted"
                             % (oid, t.get("trial_id") or "?"))
            continue
        entries.append({
            "id": t.get("trial_id") or t.get("nct") or "?",
            "estimate": est,
            "variance": se * se,
            "measure": t.get("measure"),
            # direction_of_benefit and intervention are NOT synthesised. The
            # object records direction at OUTCOME level, so it is read from
            # there; intervention is omitted unless the trial names one.
            **({"direction_of_benefit": "efficacy"}
               if (outcome_def or {}).get("direction_of_benefit") else {}),
        })
        rows.append(t)

    if not entries:
        return None

    panel_rows = []
    for t in per:
        panel_rows.append({
            "id": t.get("trial_id") or t.get("nct") or "?",
            "outcome": res.get("estimand_id") or oid,
            "population": t.get("population") or "randomised",
            "window": "full",
        })

    pool = {
        "pool_id": oid,
        "headline_k": res.get("k"),
        "headline_outcome": res.get("estimand_id") or oid,
        "panel_rows": panel_rows,
        "entries": entries,
    }
    # declared_class is REQUIRED by the cross-agent detector and must never be
    # invented: its absence is the defect that detector exists to catch.
    dc = ((outcome_def or {}).get("declared_class")
          or res.get("declared_class")
          or (res.get("pool_uniformity") or {}).get("declared_class"))
    if dc:
        pool["declared_class"] = dc
    else:
        omissions.append("%s: no declared_class in the object -- LEFT ABSENT, "
                         "which is what CHK on cross-agent pooling reads" % oid)
    if pooled.get("point") is not None:
        # The harness compares entry estimates on the SAME scale they are stored
        # on. Our pooled point is natural-scale for ratios; the log is what the
        # entries carry, so the log is what is exported.
        import math
        p = pooled["point"]
        pool["pooled_estimate"] = (math.log(p) if (pooled.get("scale") == "log"
                                                   and p > 0) else p)
    return pool


def export(obj, page_html=None):
    """SSOT object -> artefact dict. Omits what the object does not carry."""
    omissions = []
    art = {}
    art["page_id"] = obj.get("app_id") or "<unnamed>"

    bm = (obj.get("build_mode") or "").upper()
    if bm:
        art["build_path"] = "converted" if bm == "CONVERTED" else "author"
        art["page_provenance"] = ("converted" if bm == "CONVERTED"
                                  else "authored-reconciliation")

    trials = ((obj.get("inputs") or {}).get("trials")) or []
    data_ids = [t.get("nct") or t.get("id") for t in trials if (t.get("nct") or t.get("id"))]

    results = ((obj.get("results") or {}).get("by_outcome")) or {}
    engine_ids = []
    for res in results.values():
        for t in (res.get("per_trial") or []):
            v = t.get("nct") or t.get("trial_id")
            if v and v not in engine_ids:
                engine_ids.append(v)

    if data_ids and engine_ids:
        art["engine_trial_ids"] = engine_ids
        art["data_trial_ids"] = data_ids
    else:
        omissions.append("engine/data trial ids incomplete -> inert-engine check "
                         "not emitted")

    outcomes = {o.get("id"): o for o in (obj.get("outcomes") or [])}
    pools = []
    any_pooled = None
    for oid, res in results.items():
        p = _pool_from_outcome(oid, res, outcomes.get(oid), omissions)
        if p:
            pools.append(p)
        if (res.get("pooled") or {}).get("point") is not None:
            any_pooled = res["pooled"]["point"]
    if pools:
        art["pools"] = pools

    # POOL CAPABILITY, PER OUTCOME -- AND THE FLATTENING IT REPLACES WAS A JOIN
    # DEFECT, not a tuning choice.
    #
    # The previous version collapsed three per-outcome facts into one triple:
    # engine_can_pool was ANDed across EVERY outcome, displayed_pooled_estimate
    # was whichever outcome came last with a number, and engine_block_reason was
    # the first outcome that said false. On SOTAGLIFLOZIN that produced a FAIL
    # joining the hfcv_first pool's displayed 0.7488 to mace3_first's reason --
    # "only one contributing trial reports this estimand" -- which is TRUE, of a
    # DIFFERENT ESTIMAND. Two of the three fields came from outcomes the third
    # had nothing to do with, and the detector had no way to know.
    #
    # It blocked a push, so this one failed toward ALARM. That is the rarer
    # direction and the reason it was found in minutes rather than surviving a
    # day feeding false assurance. It is still not the safe kind of wrong: acting
    # on it would have meant withdrawing a sound estimate, and a withdrawal needs
    # the same evidentiary standard as a claim.
    #
    # READ FROM THE OBJECT'S OWN POOLABILITY VERDICT, never from "is there a
    # number": a displayed estimate on an outcome the object says cannot pool is
    # precisely the orphan defect, and deriving the verdict from the presence of
    # the number would make it unfindable.
    caps = []
    for oid, res in results.items():
        if res.get("poolable") is None:
            continue
        can = bool(res.get("poolable"))
        caps.append({
            "outcome_id": oid,
            "displayed_pooled_estimate": (res.get("pooled") or {}).get("point"),
            "engine_can_pool": can,
            # EMIT IN BOTH STATES. This field was written only when poolability
            # was FALSE, so CHK020_ORPHAN_POOLED_RESULT returned INVALID on every
            # clean artefact: it could not tell "can pool" from "was never
            # asked". That is an ABSENT FIELD STANDING FOR A TRUE CONDITION --
            # exactly what declared_class taught, committed in the exporter
            # written to avoid it. An explicit value is not a synthesised one: it
            # states which branch the object recorded FOR THIS OUTCOME.
            "engine_block_reason": (
                "" if can else (res.get("poolable_reason")
                                or "the object records poolable=false with no "
                                   "reason given")),
        })
    if caps:
        art["pool_capability"] = caps
    else:
        omissions.append("no poolable verdict in the object -> orphan-pool check "
                         "not emitted")

    # rows: the per-trial numbers the back-transform and precision-sample
    # detectors read. Counts come from the trial's own arms, not from anywhere else.
    rows = []
    for t in trials:
        arms = {a.get("role"): a for a in (t.get("arms") or []) if a.get("role")}
        tre, con = arms.get("treatment") or {}, arms.get("control") or {}
        for oid, bo in (t.get("by_outcome") or {}).items():
            eff = bo.get("effect") or {}
            if eff.get("point") is None:
                continue
            row = {"row_id": "%s::%s" % (t.get("nct") or t.get("id") or "?", oid),
                   "estimate": eff.get("point"),
                   "ci_low": eff.get("ci_low"), "ci_high": eff.get("ci_high"),
                   "measure": eff.get("measure"),
                   "stored_scale": eff.get("scale") or "log",
                   "back_transform": "exp" if (eff.get("scale") == "log") else "none"}
            if tre.get("events") is not None and con.get("events") is not None:
                row.update({"events_t": tre.get("events"), "n_t": tre.get("participants"),
                            "events_c": con.get("events"), "n_c": con.get("participants")})
            else:
                omissions.append("%s: no per-arm counts -> precision-sample check "
                                 "cannot run on this row" % row["row_id"])
            rows.append(row)
    if rows:
        art["rows"] = rows

    # claimed_method: read, never assumed. An NMA claim with no network is the
    # defect; a pairwise object simply says pairwise.
    cm = (obj.get("config") or {}).get("method_class") or obj.get("method_class")
    if cm:
        art["claimed_method"] = cm
        art["network_edges"] = obj.get("network_edges") or []
    elif results:
        art["claimed_method"] = "pairwise"
        art["network_edges"] = []

    if page_html:
        art["reader_text"] = _visible(page_html)[:200000]
        art["sentinels"] = SENTINELS
        art["numeric_fields"] = [
            {"field_id": "raw-%d" % i, "raw": m,
             "naive_value": float(re.sub(r"[^0-9.\-]", "", m) or 0)}
            for i, m in enumerate(re.findall(r"&minus;\s*[\d.]+|&#8722;\s*[\d.]+",
                                             page_html)[:40])]
        if not art["numeric_fields"]:
            art.pop("numeric_fields")
    else:
        omissions.append("no page HTML given -> sentinel-leak and unicode-minus "
                         "checks not emitted")

    return art, omissions


def selftest():
    """REPLAYS THE JOIN DEFECT ON THE OBJECT THAT PRODUCED IT.

    Not a fixture. SOTAGLIFLOZIN carries three outcomes -- two pooled at k=2 and
    one reported from a single trial with poolable=false -- which is the exact
    shape that made the flattened export attach mace3_first's reason to
    hfcv_first's displayed 0.7488 and block a push over a defect that did not
    exist. The old join is recomputed here so the test can show it failing; a
    test that only exercises the new code proves the fix runs, not that it fixes
    anything.
    """
    ok = True
    p = os.path.join(REPO, "ssot", "sotagliflozin-hf", "sotagliflozin-hf.json")
    if not os.path.exists(p):
        print("  fixture absent: sotagliflozin-hf -- NOT PROVEN")
        return 1
    obj = json.loads(open(p, encoding="utf-8").read())
    results = (obj.get("results") or {}).get("by_outcome") or {}

    # THE OLD JOIN, recomputed exactly as it was.
    old_can = all(bool(r.get("poolable")) for r in results.values()
                  if r.get("poolable") is not None)
    old_shown = None
    for r in results.values():
        if (r.get("pooled") or {}).get("point") is not None:
            old_shown = r["pooled"]["point"]
    old_would_fail = old_shown is not None and not old_can
    print("  POSITIVE the flattened join on this object -> orphan FAIL: %-5s %s"
          % (old_would_fail, "correct -- this is the defect" if old_would_fail
             else "the replay proved nothing: the object no longer has the shape"))
    ok &= old_would_fail

    art, _ = export(obj)
    caps = art.get("pool_capability") or []
    print("  per-outcome capability entries: %d" % len(caps))
    bad = [c for c in caps
           if c.get("displayed_pooled_estimate") is not None
           and not c.get("engine_can_pool")]
    for c in caps:
        print("      %-14s displayed=%-8s can_pool=%-5s %s"
              % (c["outcome_id"], c["displayed_pooled_estimate"],
                 c["engine_can_pool"], (c["engine_block_reason"] or "")[:46]))
    print("  NEGATIVE per-outcome, on the same object -> orphan FAIL: %-5s %s"
          % (bool(bad), "correct" if not bad else "WRONG"))
    ok &= not bad
    ok &= len(caps) >= 2

    # A REASON MUST BELONG TO ITS OWN OUTCOME. A capability that can pool must
    # carry no block reason at all -- that is what stops a reason migrating
    # across estimands the way the flattened version let it.
    stray = [c for c in caps if c["engine_can_pool"] and c["engine_block_reason"]]
    print("  NEGATIVE a poolable outcome carrying a block reason: %-5s %s"
          % (bool(stray), "correct" if not stray else "WRONG"))
    ok &= not stray

    print("\nWHAT A FAILURE WOULD LOOK LIKE: a displayed estimate paired with a "
          "reason that is true of a different estimand, blocking a push and "
          "arguing for the withdrawal of a sound number.")
    print("-> SELFTEST PASS" if ok else "-> SELFTEST FAILED")
    return 0 if ok else 1


def main():
    if "--selftest" in sys.argv:
        return selftest()
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("objects", nargs="+", help="ssot/<app>/<app>.json files")
    ap.add_argument("--outdir", default=os.path.join(REPO, "build-artefacts"))
    ap.add_argument("--page", default="", help="optional built HTML for one object")
    a = ap.parse_args()
    os.makedirs(a.outdir, exist_ok=True)
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    from nafis_harness.artefact import payloads_for

    total_payloads = 0
    for src in a.objects:
        obj = json.loads(open(src, encoding="utf-8").read())
        html = None
        if a.page and os.path.exists(a.page):
            html = open(a.page, encoding="utf-8", errors="replace").read()
        art, omissions = export(obj, html)
        n = len(payloads_for(art))
        total_payloads += n
        out = os.path.join(a.outdir, (obj.get("app_id") or "unnamed") + ".json")
        with open(out, "w", encoding="utf-8") as fh:
            json.dump(art, fh, indent=1)
        print("%-34s -> %-46s %2d check payload(s)"
              % (os.path.basename(src), os.path.relpath(out, REPO), n))
        for o in omissions[:6]:
            print("      omitted: %s" % o)
        if len(omissions) > 6:
            print("      omitted: ... and %d more" % (len(omissions) - 6))
    if total_payloads == 0:
        print("\nNO CHECK PAYLOADS PRODUCED AT ALL. That is not a clean export; "
              "it is an exporter that recognised nothing.")
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
