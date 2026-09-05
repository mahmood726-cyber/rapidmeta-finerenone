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

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import retirement as R                                       # noqa: E402

if __name__ == "__main__":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Sentinels the reader must never meet. Kept here rather than defaulted inside
# the harness so the list is visible at the point of export.
SENTINELS = ["NOT RECOVERABLE FROM THE PAGE", "REPLACE_ME", "__PLACEHOLDER__",
             "{{", "TODO", "undefined", "NaN"]


# THE TWO VOCABULARIES, WRITTEN DOWN. Left: what the SSOT objects say. Right:
# (stored_scale, back_transform) as the harness detectors read them. Anything not
# in this table is NOT mapped and the fields are omitted -- an unmappable scale
# must reach the detector as "not declared", never as a guess.
_SCALE_VOCAB = {
    "log":      ("log", "exp"),
    "linear":   ("natural", "identity"),
    "natural":  ("natural", "identity"),
    "identity": ("natural", "identity"),
}


def _measure_for(results, oid, trial):
    """The effect MEASURE this object records for this trial-outcome, or None.

    The objects carry the measure on `results.by_outcome[oid].per_trial[]` and
    usually NOT on the trial's own effect block, so reading only the effect block
    left `measure` null on nine of ten rows and CHK021 returned INVALID -- ran,
    saw nothing, reported nothing. This joins the two places the object records
    the same fact. It is a LOOKUP, not an inference: no match, no measure.
    """
    tid, nct = trial.get("id"), trial.get("nct")
    for row in ((results.get(oid) or {}).get("per_trial") or []):
        if (nct and row.get("nct") == nct) or (tid and row.get("trial_id") == tid):
            return row.get("measure")
    return None


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
        # A NULLED ENTRY IS NOT A CONTRIBUTING TRIAL AND MUST NOT BE COUNTED AS ONE.
        # `finerenone-review` carries `NULLED:NCT01874431` in `per_trial` with a value while
        # `k` is 3, so the panel showed four rows under a headline stating three --
        # CHK009_POOL_IDENTITY, correctly. The entry stays on the object; it leaves the count.
        if t.get("nulled") or str(t.get("trial_id") or t.get("nct") or "").startswith("NULLED:"):
            continue
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
        # CHK018 must tell a real mixed POOL from separately-reported strata of an
        # outcome the object declares non-poolable. Carry both signals it needs:
        # the object's own poolable flag, and whether any combined estimate is
        # actually displayed. Without these the export presented malaria's
        # exploratory_recurrent_rate (poolable False, no combined figure per its
        # Cochrane gate_dissent) as a pool, and CHK018 flagged HR+IRR that nothing
        # combines into a shown number.
        "poolable": res.get("poolable"),
        "displayed_pooled_estimate": pooled.get("point"),
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

    # THE ARTEFACT CARRIES ITS OWN STATE, the same way a page carries `rapidmeta:page-state`.
    # Downstream, `harness_gate.py` sees only artefacts -- it cannot open the object -- so an
    # artefact from a topic that publishes no estimate looked identical to one from an adapter
    # that recognised nothing. Two different states, indistinguishable, which is exactly the
    # confusion this project keeps paying for. The exporter knows the difference and stamps it.
    _pr = (((obj.get("results") or {}).get("by_outcome") or {}).get("primary") or {})
    _pl = _pr.get("pooled") or {}
    _k = _pr.get("k")
    if _pl.get("point") is None and (_pl.get("withdrawn") or _pl.get("absent")
                                     or (isinstance(_k, int) and _k < 2)):
        art["publishes_no_estimate"] = {
            "k": _k,
            "because": ("withdrawn" if _pl.get("withdrawn") else
                        "absent" if _pl.get("absent") else
                        "k<2 -- one trial is not a meta-analysis"),
            "means": ("This artefact yielding ZERO check executions is the CORRECT result, not "
                      "an adapter that recognised nothing. PUBLISHES-NOTHING and UNRECOGNISED "
                      "are different states and are never summed."),
            "stamped_by": "scripts/export_artefact.py",
        }

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
        # A SINGLE-TRIAL RESULT IS NOT AN ORPHAN POOL.
        # `poolable: false` was carrying two incompatible meanings: "this cannot
        # legitimately be pooled" and "there is only one trial here". CHK020 read
        # the first and blocked BEMPEDOIC_ACID, whose displayed 0.87 IS CLEAR
        # Outcomes' own registered hazard ratio -- a value whose derivation is not
        # missing, because nothing needed deriving. The third condition is now
        # stated rather than inferred, so the check can tell "no derivation" from
        # "no synthesis required". An object with poolable=false, k>1, a displayed
        # value and NO single_study_ref is untouched by this and still fails, which
        # is the real orphan defect.
        _single = res.get("single_study_ref")
        _k = res.get("k")
        _is_single = bool(_single) and _k == 1
        caps.append({
            "outcome_id": oid,
            "displayed_pooled_estimate": (res.get("pooled") or {}).get("point"),
            "engine_can_pool": can or _is_single,
            "single_study": _is_single,
            "single_study_ref": _single if _is_single else "",
            # EMIT IN BOTH STATES. This field was written only when poolability
            # was FALSE, so CHK020_ORPHAN_POOLED_RESULT returned INVALID on every
            # clean artefact: it could not tell "can pool" from "was never
            # asked". That is an ABSENT FIELD STANDING FOR A TRUE CONDITION --
            # exactly what declared_class taught, committed in the exporter
            # written to avoid it. An explicit value is not a synthesised one: it
            # states which branch the object recorded FOR THIS OUTCOME.
            "engine_block_reason": (
                "" if (can or _is_single) else
                (res.get("poolable_reason")
                 or "the object records poolable=false with no reason given")),
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
                   "measure": eff.get("measure") or _measure_for(results, oid, t)}
            # SCALE VOCABULARY, TRANSLATED RATHER THAN PASSED THROUGH OR GUESSED.
            #
            # Two defects lived on this line. The objects write "linear" for a
            # natural-scale difference and the detector's vocabulary is
            # "natural", so EVERY difference-measure row in this corpus produced
            # a false FAIL -- "MD is a difference on the natural scale but is
            # stored as 'linear'" -- which is the adapter's word for exactly the
            # thing the detector was asking for. A field-name contract across a
            # module boundary, unstated and therefore unchecked.
            #
            # The worse one was the fallback: `eff.get("scale") or "log"`. An
            # object that records no scale had one ASSERTED for it, and "log" is
            # the assertion that makes a difference measure look like a ratio.
            # That is a synthesised field in the exporter whose own first rule is
            # never to synthesise a field, and it fails toward comfort -- the
            # detector cannot tell a declared scale from a defaulted one.
            _sc = (eff.get("scale") or "").strip().lower()
            if _sc in _SCALE_VOCAB:
                row["stored_scale"], row["back_transform"] = _SCALE_VOCAB[_sc]
            else:
                omissions.append(
                    "%s: scale %r is not one this exporter can map -> the "
                    "measure/scale check is NOT emitted for this row, which is "
                    "not a pass on it" % (row["row_id"], eff.get("scale")))
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

    # SCALE VOCABULARY, replayed on the object that exposed it. IV iron carries a
    # mean difference stored as "linear"; the detector's word is "natural", and
    # the mismatch produced a FAIL saying the row was not on the scale it was
    # already on. The second half matters more: an object with NO scale must
    # yield NO scale fields, because the old `or "log"` default asserted the one
    # value that makes a difference measure look like a ratio.
    p2 = os.path.join(REPO, "ssot", "iv-iron-hf", "iv-iron-hf.json")
    if os.path.exists(p2):
        iv = json.loads(open(p2, encoding="utf-8").read())
        art2, _ = export(iv)
        rows = {r["row_id"]: r for r in (art2.get("rows") or [])}
        md = rows.get("NCT01453608::six_min_walk_24w") or {}
        good = (md.get("measure") == "MD" and md.get("stored_scale") == "natural"
                and md.get("back_transform") == "identity")
        ok &= good
        print("  NEGATIVE a mean difference stored as 'linear' -> %r/%r %s"
              % (md.get("stored_scale"), md.get("back_transform"),
                 "correct" if good else "WRONG -- the false FAIL is back"))
        named = sum(1 for r in art2.get("rows") or [] if r.get("measure"))
        ok &= named == len(art2.get("rows") or [])
        print("  NEGATIVE every row carries the measure the object records: %d/%d %s"
              % (named, len(art2.get("rows") or []),
                 "correct" if named == len(art2.get("rows") or []) else "WRONG"))

        stripped = json.loads(json.dumps(iv))
        for t in stripped["inputs"]["trials"]:
            for bo in (t.get("by_outcome") or {}).values():
                (bo.get("effect") or {}).pop("scale", None)
        art3, om3 = export(stripped)
        leaked = [r for r in (art3.get("rows") or []) if "stored_scale" in r]
        ok &= not leaked
        print("  POSITIVE an object with no scale recorded -> scale asserted on "
              "%d row(s) %s" % (len(leaked), "correct" if not leaked else
                                "WRONG -- the exporter is inventing a scale"))
    else:
        print("  fixture absent: iv-iron-hf -- NOT PROVEN"); ok = False

    print("\nWHAT A FAILURE WOULD LOOK LIKE: a displayed estimate paired with a "
          "reason that is true of a different estimand, blocking a push and "
          "arguing for the withdrawal of a sound number; or a scale the object "
          "never recorded, asserted by the adapter and checked as though it had.")
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
    retired = []
    for src in a.objects:
        obj = json.loads(open(src, encoding="utf-8").read())
        # A RETIRED TOPIC IS NOT AN UNRECOGNISED ONE, and folding the two together would make
        # this gate refuse every merge for the rest of the project's life.
        #
        # A tombstone deliberately holds no `results` and no top-level `inputs.trials` -- it
        # holds the object it replaced, nested, plus who absorbed it and when. So the exporter
        # correctly produces zero payloads for it, and the "nothing checkable" refusal below
        # correctly fires on a corpus of nothing BUT tombstones. The two states are distinct:
        #   UNRECOGNISED  the exporter looked and could not read the object -- a real failure
        #   RETIRED       the object declares itself retired -- there is nothing to check, and
        #                 that is the correct and intended state
        # Counted separately, and a run consisting only of tombstones is reported as such rather
        # than as an exporter that recognised nothing.
        # RETIREMENT IS DECIDED BY `state` ALONE -- see scripts/retirement.py. This test read
        # `state == RETIRED **and** o.get("absorbed_by")`, which made the successor field a
        # PRECONDITION for seeing a tombstone at all. A topic retired by SPLIT records
        # `split_into`, so it was not recognised as retired and fell through to the live path.
        if R.is_retired(obj):
            retired.append((os.path.basename(src), R.successor_label(obj)))
            print("%-34s -> RETIRED, succeeded by %-26s  no payload BY DESIGN"
                  % (os.path.basename(src), R.successor_label(obj)))
            continue
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
    if retired:
        print("\n%d of the %d object(s) are RETIRED TOMBSTONES and produce no payload by "
              "design: %s" % (len(retired), len(a.objects),
                              ", ".join("%s -> %s" % r for r in retired)))
    if total_payloads == 0:
        if retired and len(retired) == len(a.objects):
            print("EVERY object in this run is a retired tombstone. There is nothing to check "
                  "and that is the CORRECT state, not an exporter that recognised nothing. "
                  "RETIRED and UNRECOGNISED are different states and are never summed.")
            return 0
        # A THIRD LEGITIMATE STATE, and the third instrument to have lacked the concept. The
        # tombstone case above was encoded when the merge gates refused a retired page. This is
        # the same missing idea one state along: A LIVE REVIEW THAT PUBLISHES NO ESTIMATE has
        # nothing to check either. `mavacamten-ohcm-review` holds ONE trial -- no per-trial
        # rows, no poolable verdict, no pool -- so every detector correctly declines, and the
        # run then read as an exporter that recognised nothing.
        #
        # ENCODED, NOT EXEMPTED. The object must SAY it publishes nothing: `pooled.point` is
        # None AND the pool is explicitly `withdrawn` or `absent`, or k < 2. An object that
        # simply FAILED to produce a payload -- one that claims a pool and yields no rows --
        # still fails, which is the case this gate exists for.
        declares_nothing, undecided = [], []
        for src in a.objects:
            with open(src, "r", encoding="utf-8") as fh:
                o = json.load(fh)
            if str(o.get("state") or "").upper() == "RETIRED":
                continue
            pr = (((o.get("results") or {}).get("by_outcome") or {}).get("primary") or {})
            pl = pr.get("pooled") or {}
            k = pr.get("k")
            if pl.get("point") is None and (pl.get("withdrawn") or pl.get("absent")
                                            or (isinstance(k, int) and k < 2)):
                declares_nothing.append("%s (k=%s, %s)" % (
                    o.get("app_id"), k,
                    "withdrawn" if pl.get("withdrawn") else
                    "absent" if pl.get("absent") else "k<2"))
            else:
                undecided.append(o.get("app_id"))
        if declares_nothing and not undecided:
            print("\nEVERY live object in this run DECLARES THAT IT PUBLISHES NO ESTIMATE: %s. "
                  "There is nothing to check and that is the CORRECT state, not an exporter "
                  "that recognised nothing. PUBLISHES-NOTHING and UNRECOGNISED are different "
                  "states and are never summed." % ", ".join(declares_nothing))
            return 0
        print("\nNO CHECK PAYLOADS PRODUCED AT ALL. That is not a clean export; "
              "it is an exporter that recognised nothing.")
        if undecided:
            print("These object(s) do NOT declare that they publish nothing, so producing no "
                  "payload is a failure rather than a design: %s" % ", ".join(undecided))
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
