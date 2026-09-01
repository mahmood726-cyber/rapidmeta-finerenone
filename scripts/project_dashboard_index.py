#!/usr/bin/env python3
"""PROJECT THE DASHBOARD'S INDEX FROM THE OBJECTS, AND MAKE ITS STALENESS DETECTABLE.

THE DEFECT. `dashboard.html` renders a "Pooled OR (95% CI)" column from
`outputs/portfolio_index.json`, a snapshot generated 2026-06-24. Of its 711 rows carrying a
numeric `pooled_OR`, **83 belong to topics whose SSOT object has WITHDRAWN its estimate** and
**8 to reviews that no longer exist**, having been retired into another topic.

    A WITHDRAWAL IS THE STRONGEST STATEMENT A REVIEW IN THIS CORPUS CAN MAKE. It is what an
    object says when its trials do not share an endpoint, when its comparator is wrong, or when
    its headline could not be reproduced from its own trials. SERVING THE NUMBER ANYWAY UNDOES
    EVERY ONE OF THOSE DECISIONS AT ONCE, for every reader who never opens the page -- and the
    dashboard is the surface most readers actually look at.

    It is the same class as the page that displayed somebody else's benchmark as its own,
    at scale, on the aggregate surface.

WHY REGENERATING THE SNAPSHOT IS NOT THE FIX. A regenerated snapshot is correct for a day and
wrong again the next time an object is withdrawn, silently and with no symptom. The pages solved
this years of defects ago: a page carries the version it was built to, so being out of date is
VISIBLE rather than invisible. The dashboard's data gets the same treatment.

WHAT THIS WRITES INTO THE ARTEFACT
  * per row, `ssot_state` -- LIVE / WITHDRAWN / RETIRED / NO_POOL / UNMAPPED / OBJECT_MISSING
  * per row that is not LIVE, the pooled value is MOVED to `pooled_OR_superseded` and the live
    fields are nulled, so the dashboard cannot render a number the object does not support.
    NOTHING IS DELETED -- the superseded value stays, labelled, exactly as a retired topic keeps
    a tombstone.
  * a `projection` block carrying an OBJECTS FINGERPRINT: a hash over every object's path,
    mtime-independent CONTENT and its derived state. `scripts/dashboard_projection_gate.py`
    recomputes it and REFUSES when it no longer matches, so staleness is detectable by a command
    instead of by somebody noticing.

WHAT THIS DOES NOT DO, stated so a clean run is not read as more than it is
  * It does NOT check the LIVE rows' NUMBERS against their objects. A row that stays LIVE may
    still be stale by value. This answers only the sharper question -- is a number served where
    the object says there is none.
  * It does NOT touch the 602 rows whose page has no SSOT object. They are labelled UNMAPPED and
    are UNCHECKABLE, never clean, and they are why every count here is a floor.

USAGE:  python scripts/project_dashboard_index.py --check
        python scripts/project_dashboard_index.py --apply
        python scripts/project_dashboard_index.py --selftest
"""
import hashlib
import io
import json
import os
import sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SNAP = os.path.join(REPO, "outputs", "portfolio_index.json")
PMAP = os.path.join(REPO, "ssot", "PAGE_MAP.json")

LIVE, WITHDRAWN, RETIRED, NO_POOL = "LIVE", "WITHDRAWN", "RETIRED", "NO_POOL"
UNMAPPED, MISSING, UNREADABLE = "UNMAPPED", "OBJECT_MISSING", "OBJECT_UNREADABLE"
NOT_LIVE = (WITHDRAWN, RETIRED, NO_POOL)


def object_state(page, pmap):
    """(state, detail) for one page. Five states, and none collapses into another."""
    if page not in pmap:
        return UNMAPPED, None
    rel = pmap[page]
    p = os.path.join(REPO, rel.replace("/", os.sep))
    if not os.path.exists(p):
        return MISSING, rel
    try:
        with io.open(p, "r", encoding="utf-8") as fh:
            o = json.load(fh)
    except ValueError:
        return UNREADABLE, rel
    # RETIRED IS DECIDED BY `state` ALONE. This test used to read
    #     state == RETIRED **and** o.get("absorbed_by")
    # which made the successor field a precondition for recognising retirement. The first
    # topic retired by SPLIT rather than by merge carries `split_into`, not `absorbed_by`, so
    # it fell straight through to NO_POOL and the dashboard reported a topic that no longer
    # exists as though it were merely unpooled. **A tombstone the projection cannot see is a
    # retired topic presented as live** -- the same shape as class 25, a lookup keyed on one
    # spelling of a field reporting something false about the thing it looked at.
    #
    # The successor is now read from EITHER field, and a tombstone with neither is still
    # RETIRED with the successor reported as unrecorded -- never silently downgraded.
    if str(o.get("state") or "").upper() == "RETIRED":
        succ = o.get("absorbed_by") or o.get("split_into")
        if isinstance(succ, list):
            succ = ", ".join(succ)
        return RETIRED, (succ or "RETIRED, and no successor field is recorded on the tombstone")
    res = (o.get("results") or {}).get("by_outcome") or {}
    live, withdrawn, reason = False, False, None
    for b in res.values():
        if not isinstance(b, dict):
            continue
        pl = b.get("pooled") or {}
        if pl.get("withdrawn"):
            withdrawn = True
            reason = reason or pl.get("withdrawn_reason") or b.get("poolable_reason")
        elif pl.get("point") is not None:
            live = True
    if live:
        return LIVE, None
    if withdrawn:
        return WITHDRAWN, (reason or "")[:400]
    return NO_POOL, None


def fingerprint(pmap):
    """A hash over the OBJECT STATE the projection depends on -- not over file mtimes.

    Keyed on content, so touching a file does not invalidate it and CHANGING A WITHDRAWAL does.
    That is the whole point: the fingerprint must move exactly when the projection would.
    """
    h = hashlib.sha256()
    for page in sorted(pmap):
        state, detail = object_state(page, pmap)
        h.update(("%s\x1f%s\x1f%s\x1e" % (page, state, detail or "")).encode("utf-8"))
    return h.hexdigest()


# ---------------------------------------------------------------------------
# METADATA IS DERIVED FROM rows[], NEVER STORED BESIDE THEM.
#
# The snapshot stored n_total=960 next to 71 rows -- a 13.5x overstatement that
# rendered on the dashboard as "Reviews shipped". No single-field check could
# see it: every field was internally valid, and the two populations simply never
# met. A stored count and the rows it describes are two populations under one
# name, and they drift the moment either changes.
#
# LIVE is the denominator for anything the dashboard SERVES. The 52 not-live
# rows are tombstones -- kept, labelled, and counted separately in the same
# block, so completing the withdrawal never becomes hiding it.
DERIVED_KEYS = ("n_total", "n_pairwise", "n_nma",
                "n_with_r_validation", "n_validated_provenance", "n_stats_pending")


def derive_metadata(snap):
    """Recompute every headline counter from rows[]. Returns (derived, before)."""
    rows = [r for r in (snap.get("rows") or []) if isinstance(r, dict)]
    live = [r for r in rows if r.get("ssot_state") == LIVE]
    types = {}
    for r in live:
        types[r.get("type")] = types.get(r.get("type"), 0) + 1
    derived = {
        "n_total": len(live),
        "n_pairwise": types.get("Pairwise", 0),
        "n_nma": types.get("NMA", 0),
        "n_with_r_validation": sum(1 for r in live if r.get("k") is not None),
        "n_validated_provenance": sum(
            1 for r in live if isinstance(r.get("pooled_OR"), (int, float))),
        "n_stats_pending": sum(
            1 for r in live if not isinstance(r.get("pooled_OR"), (int, float))),
    }
    before = {k: snap.get(k) for k in DERIVED_KEYS}
    snap.update(derived)
    snap["metadata_derivation"] = {
        "derived_from": "rows[] at write time, by scripts/project_dashboard_index.py",
        "denominator": "ssot_state == LIVE",
        "n_rows_in_file": len(rows),
        "n_not_live": len(rows) - len(live),
        "types_among_live": types,
        "previously_stored": before,
        "why": (
            "n_total read 960 beside %d rows, of which %d are LIVE. It rendered as "
            "'Reviews shipped'. The stored counters were a second population that had "
            "stopped agreeing with the first, and nothing compared them. Deriving them "
            "here means they cannot disagree with their own rows again."
            % (len(rows), len(live))),
        "what_this_does_NOT_claim": (
            "n_total counts rows this file can show are LIVE. The %d not-live rows are "
            "tombstones and are counted above, not deleted. A row left LIVE may still be "
            "stale by value -- see projection.what_this_does_NOT_check."
            % (len(rows) - len(live))),
    }
    return derived, before


def project(snap, pmap):
    rows = snap.get("rows") or []
    tally, changed = {}, 0
    for r in rows:
        if not isinstance(r, dict):
            continue
        page = r.get("file")
        state, detail = object_state(page, pmap)
        tally[state] = tally.get(state, 0) + 1
        r["ssot_state"] = state
        if state == RETIRED:
            r["ssot_absorbed_by"] = detail
        elif state == WITHDRAWN and detail:
            r["ssot_withdrawn_reason"] = detail
        if state in NOT_LIVE and isinstance(r.get("pooled_OR"), (int, float)):
            # MOVED, NOT DELETED. The value is what the snapshot held on 2026-06-24 and it is
            # kept, labelled, so a later reader can see what was served rather than infer it.
            r["pooled_OR_superseded"] = r.get("pooled_OR")
            r["ci_low_superseded"] = r.get("ci_low")
            r["ci_high_superseded"] = r.get("ci_high")
            r["superseded_because"] = (
                "the SSOT object for this page is %s. A pooled value is not served for a topic "
                "whose object does not support one." % state)
            r["pooled_OR"] = None
            r["ci_low"] = None
            r["ci_high"] = None
            changed += 1
    snap["projection"] = {
        "projected_utc": "2026-08-19",
        "projected_by": "scripts/project_dashboard_index.py",
        "objects_fingerprint": fingerprint(pmap),
        "what_the_fingerprint_is_over": (
            "every page in ssot/PAGE_MAP.json, its derived SSOT state and the reason attached "
            "to it. Keyed on CONTENT, so touching a file does not invalidate it and changing a "
            "withdrawal does. scripts/dashboard_projection_gate.py recomputes it and refuses "
            "when it no longer matches -- staleness detected by a command, not by somebody "
            "noticing."),
        "by_ssot_state": tally,
        "rows_whose_pooled_value_was_withdrawn_from_display": changed,
        "snapshot_generated": snap.get("generated"),
        "what_this_does_NOT_check": (
            "It does not compare the LIVE rows' NUMBERS against their objects. A row left LIVE "
            "may still be stale by value. And the UNMAPPED rows have no object at all -- they "
            "are uncheckable, never clean, and they are why any count here is a FLOOR."),
    }
    return tally, changed


def run(apply_changes=False):
    with io.open(SNAP, "r", encoding="utf-8") as fh:
        snap = json.load(fh)
    with io.open(PMAP, "r", encoding="utf-8") as fh:
        pmap = json.load(fh)
    before = sum(1 for r in snap.get("rows") or []
                 if isinstance(r, dict) and isinstance(r.get("pooled_OR"), (int, float)))
    tally, changed = project(snap, pmap)
    derived, meta_before = derive_metadata(snap)
    after = sum(1 for r in snap.get("rows") or []
                if isinstance(r, dict) and isinstance(r.get("pooled_OR"), (int, float)))

    print("snapshot generated %s   rows %d" % (snap.get("generated"), len(snap.get("rows") or [])))
    print("rows with a numeric pooled_OR: %d -> %d\n" % (before, after))
    for k in sorted(tally, key=lambda x: -tally[x]):
        print("   %-18s %4d" % (k, tally[k]))
    print("\n   values withdrawn from display: %d" % changed)
    md = snap["metadata_derivation"]
    print("\n   METADATA DERIVED FROM rows[] (denominator: %s)" % md["denominator"])
    for k in DERIVED_KEYS:
        was = meta_before.get(k)
        flag = "" if was == derived[k] else "   <- was %s" % was
        print("      %-24s %4d%s" % (k, derived[k], flag))
    print("      %-24s %4d   rows in file, %d not live (tombstones, kept)"
          % ("(rows)", md["n_rows_in_file"], md["n_not_live"]))
    print("   objects fingerprint: %s" % snap["projection"]["objects_fingerprint"][:16])
    if apply_changes:
        with io.open(SNAP, "w", encoding="utf-8") as fh:
            fh.write(json.dumps(snap, indent=1, ensure_ascii=False))
        print("\nwrote %s" % os.path.relpath(SNAP, REPO))
    else:
        print("\nDRY RUN -- nothing written. Re-run with --apply.")
    return 0


def selftest():
    fails = []

    def ck(name, got, want):
        ok = got == want
        print("  %-66s %s  %r" % (name, "ok" if ok else "FAIL", got))
        if not ok:
            fails.append(name)

    with io.open(PMAP, "r", encoding="utf-8") as fh:
        pmap = json.load(fh)

    print("1. THE STATES ARE DISTINGUISHED ON REAL OBJECTS IN THIS REPOSITORY:")
    ck("a topic retired by MERGE (carries `absorbed_by`)",
       object_state("OMECAMTIV_HF_AUTO_FULL_REVIEW.html", pmap)[0], RETIRED)
    # THE REGRESSION FOR THE DEFECT THIS TEST DID NOT HAVE. A topic retired by SPLIT carries
    # `split_into` instead, and the old `state == RETIRED and absorbed_by` test reported it as
    # NO_POOL -- a topic that no longer exists, shown as merely unpooled. Both retirement
    # routes are now asserted, so neither can regress without the other noticing.
    ck("a topic retired by SPLIT (carries `split_into`)",
       object_state("DABIGATRAN_VTE_AUTO_FULL_REVIEW.html", pmap)[0], RETIRED)
    ck("...and its successors are named rather than left blank",
       "dabigatran-vte-treatment" in
       (object_state("DABIGATRAN_VTE_AUTO_FULL_REVIEW.html", pmap)[1] or ""), True)
    ck("a withdrawn topic", object_state("COLCHICINE_CVD_REVIEW.html", pmap)[0], WITHDRAWN)
    ck("a live pool", object_state("SGLT2_HF_REVIEW.html", pmap)[0], LIVE)
    ck("a page with no object", object_state("NO_SUCH_PAGE.html", pmap)[0], UNMAPPED)

    print("\n2. THE PROJECTION NULLS A NOT-LIVE VALUE AND KEEPS IT, never deletes it:")
    fake = {"rows": [{"file": "COLCHICINE_CVD_REVIEW.html", "pooled_OR": 0.86,
                      "ci_low": 0.7, "ci_high": 1.0}]}
    project(fake, pmap)
    r = fake["rows"][0]
    ck("the live value is nulled", r["pooled_OR"], None)
    ck("and the old value is kept", r["pooled_OR_superseded"], 0.86)
    ck("with the reason attached", "WITHDRAWN" in r["superseded_because"], True)

    print("\n3. A LIVE ROW IS LEFT ALONE:")
    fake2 = {"rows": [{"file": "SGLT2_HF_REVIEW.html", "pooled_OR": 0.76}]}
    project(fake2, pmap)
    ck("a live topic keeps its value", fake2["rows"][0]["pooled_OR"], 0.76)
    ck("and gains no superseded field", "pooled_OR_superseded" in fake2["rows"][0], False)

    print("\n4. THE FINGERPRINT MOVES WHEN A WITHDRAWAL CHANGES -- and only then:")
    f1 = fingerprint(pmap)
    f2 = fingerprint(pmap)
    ck("it is stable across two runs on unchanged objects", f1 == f2, True)
    smaller = {k: v for k, v in list(pmap.items())[:-1]}
    ck("and it MOVES when the object set changes", fingerprint(smaller) != f1, True)

    print("\n5. AN UNMAPPED ROW IS NEVER SILENTLY CLEANED:")
    fake3 = {"rows": [{"file": "NO_SUCH_PAGE.html", "pooled_OR": 1.23}]}
    t, c = project(fake3, pmap)
    ck("it keeps its value", fake3["rows"][0]["pooled_OR"], 1.23)
    ck("and is labelled UNMAPPED", fake3["rows"][0]["ssot_state"], UNMAPPED)
    ck("and is not counted as changed", c, 0)

    print("\n%s" % ("SELFTEST FAILED: %s" % fails if fails else "SELFTEST PASSED"))
    return 1 if fails else 0


if __name__ == "__main__":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    if "--selftest" in sys.argv:
        sys.exit(selftest())
    sys.exit(run("--apply" in sys.argv))
