# -*- coding: utf-8 -*-
"""AACT as the primary CT.gov route — a JOIN instead of a fetch, with a guard that REFUSES.

⭐ WHY THIS EXISTS. CT.gov posted results are a mandatory route for every outcome on every
topic. Done per trial over HTTP that is one call per trial per outcome; done against AACT it is
a query. ***THAT IS THE DIFFERENCE BETWEEN ONE TOPIC AND EIGHT.***

⭐ AND IT WAS PROVEN BEFORE IT WAS TRUSTED. The dapivirine STI 2x2 was derived by hand from the
registry JSON an hour before this module existed -- 682/1271 against 315/624 -- and AACT
reproduces all four cells exactly, plus the verbatim definition that had to be pasted in by
hand. ***EARN ONE ANSWER EXPENSIVELY, THEN USE IT TO VALIDATE THE CHEAP ROUTE.*** A source that
has not been checked against a known answer is not a source, it is a hope.

⛔⛔⛔ THE STALENESS GUARD IS A REFUSAL, NOT A WARNING, AND THAT IS THE WHOLE DESIGN.

The snapshot is a CLAIM ABOUT A VERSION. `F:\\AACT-storage\\AACT\\2026-04-12` carries updates
through 2026-04-08; a trial whose results were first posted after that date is NOT IN IT. Asking
this source about such a trial returns nothing -- and ***AN EMPTY RETURN AND A REFUSAL ARE
INDISTINGUISHABLE DOWNSTREAM***, which is the failure that produced five false zeros this week.

    results_first_posted_date > snapshot_date  ->  SNAPSHOT_TOO_OLD, with BOTH dates

`results_first_posted_date` is a column in `studies.txt`, so this is not a policy anyone has to
remember. It is a join, and it fires by itself.

⚠️ TWO THINGS TRAVEL WITH EVERY FIGURE FROM HERE:
  * THE SNAPSHOT DATE, never the query date. Posted results change; a figure without its
    version is not checkable.
  * THAT THE SOURCE IS THE REGISTRY, NOT THE PUBLICATION. A registry-derived count and a
    publication-derived count are different claims, and RoB 2 sometimes rates them differently.
    Anything leaning on this -- participant_flows and baseline_measurements for D2/D3 among
    them -- must be able to see which tier answered.
"""
import io
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(os.path.dirname(HERE))

DEFAULT_ROOT = r"F:\AACT-storage\AACT\2026-04-12"

STATE_POSTED = "POSTED"
STATE_NO_RESULTS = "NO_RESULTS_POSTED"
STATE_NO_TERM_MATCH = "POSTED_BUT_NO_TERM_MATCHED"
STATE_TOO_OLD = "SNAPSHOT_TOO_OLD"
STATE_NOT_IN_SNAPSHOT = "TRIAL_NOT_IN_SNAPSHOT"

TIER = "registry results"
SOURCE_KIND = "REGISTRY, not the publication"


def _rows(path, want=None, limit=None):
    """Stream a pipe-delimited AACT table. `want` filters lines cheaply before splitting."""
    with io.open(path, encoding="utf-8", errors="replace") as f:
        hdr = f.readline().rstrip("\n").split("|")
        idx = {k: i for i, k in enumerate(hdr)}
        n = 0
        for line in f:
            if want and want not in line:
                continue
            yield idx, line.rstrip("\n").split("|")
            n += 1
            if limit and n >= limit:
                return


def snapshot_date(root=None):
    """The snapshot's OWN date, read from the data rather than the folder name.

    ⚠️ A FOLDER NAME IS A LABEL SOMEONE TYPED. The same argument as a trial label not being an
    identity: the date that matters is the one the contents support.
    """
    root = root or DEFAULT_ROOT
    m = re.search(r"(\d{4}-\d{2}-\d{2})", os.path.basename(root))
    folder = m.group(1) if m else None
    mx = ""
    p = os.path.join(root, "studies.txt")
    if os.path.exists(p):
        for idx, c in _rows(p, limit=400000):
            i = idx.get("last_update_submitted_qc_date")
            if i is not None and len(c) > i and c[i] > mx:
                mx = c[i]
    return {"folder_label": folder, "max_update_in_data": mx or None,
            "root": root,
            "note": ("the folder is labelled %s and the data carries updates through %s"
                     % (folder, mx or "unknown"))}


def trial_gate(ncts, snap, root=None):
    """Can this snapshot SPEAK about each trial? -> {nct: (ok, state, evidence)}.

    ⛔ THE REFUSAL IS THE POINT. A trial whose results posted after the snapshot returns nothing
    from AACT, and nothing is indistinguishable from "no results exist". This says which.
    """
    root = root or DEFAULT_ROOT
    want = set(ncts)
    seen = {}
    p = os.path.join(root, "studies.txt")
    for idx, c in _rows(p):
        i = idx["nct_id"]
        if len(c) <= i or c[i] not in want:
            continue
        rfp = c[idx["results_first_posted_date"]] if "results_first_posted_date" in idx else ""
        seen[c[i]] = rfp or ""
        if len(seen) == len(want):
            break
    cut = snap.get("folder_label") or snap.get("max_update_in_data") or ""
    out = {}
    for n in ncts:
        if n not in seen:
            out[n] = (False, STATE_NOT_IN_SNAPSHOT, {
                "why": ("this trial does not appear in the snapshot at all. ⚠️ That "
                        "is a fact about the SNAPSHOT, not about the trial."),
                "snapshot_date": cut})
            continue
        rfp = seen[n]
        if rfp and cut and rfp > cut:
            out[n] = (False, STATE_TOO_OLD, {
                "why": ("this trial's results were first posted AFTER the snapshot was taken, "
                        "so this source cannot speak about them. ⛔ THIS IS NOT "
                        "'no results posted' — the results exist and are newer than the copy "
                        "we hold."),
                "results_first_posted": rfp, "snapshot_date": cut,
                "what_to_do": "use the live per-trial route for this trial only"})
            continue
        out[n] = (True, None, {"results_first_posted": rfp or None, "snapshot_date": cut})
    return out


def outcomes_for(ncts, root=None):
    """Every posted outcome measure for these trials. ONE PASS over each table."""
    root = root or DEFAULT_ROOT
    want = set(ncts)
    oms = {}
    for idx, c in _rows(os.path.join(root, "outcomes.txt")):
        if len(c) <= idx["nct_id"] or c[idx["nct_id"]] not in want:
            continue
        oms[c[idx["id"]]] = {
            "outcome_id": c[idx["id"]], "nct": c[idx["nct_id"]],
            "type": c[idx["outcome_type"]], "title": c[idx["title"]],
            "definition_verbatim": c[idx["description"]],
            "time_frame": c[idx["time_frame"]],
            "units": c[idx.get("units", 0)] if "units" in idx else None,
            "param_type": c[idx["param_type"]] if "param_type" in idx else None,
            "denoms": {}, "counts": {},
        }
    if not oms:
        return oms
    for idx, c in _rows(os.path.join(root, "outcome_counts.txt")):
        oid = c[idx["outcome_id"]] if len(c) > idx["outcome_id"] else None
        if oid in oms and c[idx["scope"]] == "Measure":
            oms[oid]["denoms"][c[idx["ctgov_group_code"]]] = c[idx["count"]]
    for idx, c in _rows(os.path.join(root, "outcome_measurements.txt")):
        oid = c[idx["outcome_id"]] if len(c) > idx["outcome_id"] else None
        if oid in oms:
            oms[oid]["counts"][c[idx["ctgov_group_code"]]] = c[idx["param_value"]]
    return oms


def as_record(om, snap):
    """One posted outcome, with its version and its tier, ready to store."""
    poolable = len(om.get("counts") or {}) >= 2 and len(om.get("denoms") or {}) >= 2
    return {
        "state": STATE_POSTED, "tier": TIER, "source_kind": SOURCE_KIND,
        "nct": om["nct"], "outcome_id": om["outcome_id"],
        "title": om["title"], "definition_verbatim": om["definition_verbatim"],
        "declared_type": om["type"], "param_type": om.get("param_type"),
        "time_frame": om.get("time_frame"), "units": om.get("units"),
        "counts": om["counts"], "denoms": om["denoms"], "poolable": poolable,
        "snapshot_date": snap.get("folder_label"),
        "snapshot_note": snap.get("note"),
        "⚠️": ("The snapshot date above is the version this figure came from, NOT the date it "
               "was queried. This is a REGISTRY count, not a publication count; the two are "
               "different claims and may be rated differently for risk of bias."),
    }
