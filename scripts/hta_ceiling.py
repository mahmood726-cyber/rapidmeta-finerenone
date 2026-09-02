"""How many topics CAN carry an HTA table, and is that ceiling real or stored?

Two questions, one script, because they share a population and splitting them
across two scripts is how one quantity acquires two numbers.

  Q1  Which objects hold a live pooled point estimate? Only those can carry a
      Summary-of-Findings or HTA table today. Publish the list so no lane
      re-derives it.

  Q2  Of the objects that hold NONE, how many hold the CELLS a pooled estimate
      could be computed from? That decides whether the ceiling is a property
      of the evidence or a property of what we have bothered to store.

UNITS, FIXED ONCE AND NAMED BEFORE EVERY NUMBER.

  OBJECT    one file matching ssot/*/*.json carrying an `app_id`. This is the
            unit of the denominator. It is NOT a page, NOT a rendered card,
            NOT an outcome, and NOT a topic directory (a directory may hold
            more than one file, and a file without app_id is not an object).
  OUTCOME   one key under results.by_outcome of an OBJECT. An object holds
            0..n outcomes. OUTCOMES ARE NOT TOPICS and the two counts must
            never be quoted against each other's denominator.
  LIVE      an outcome whose pooled block holds a point estimate and is not
            withdrawn.
  CELLS     per-arm events and denominators for BOTH arms of one outcome in
            one trial, from which a risk ratio and its variance follow.

WHAT COUNTS AS "COULD BE POOLED". Two or more trials holding CELLS for the
SAME outcome. One trial holding cells yields an estimate but not a pooled one,
so it is reported as its own state rather than folded into either answer --
folding it upward would inflate the fixable gap and folding it downward would
hide a real single-trial estimate.

Cells are read from four places, outcome-specific first, and the place used is
recorded on every row:
  1. by_outcome[oid].control / .treatment      (outcome-specific, in-object)
  2. by_outcome[oid].analysed + events         (outcome-specific, in-object)
  3. the r_validation sidecar for the topic    (outcome-specific, out-of-object)
  4. trial.arms with events + participants     (TRIAL-LEVEL: see below)

Source 4 is counted SEPARATELY and never merged into the computable count. A
trial's arms describe its primary endpoint; attaching them to an arbitrary
outcome is the wrong-denominator error, so they are reported as
CELLS_TRIAL_LEVEL_ONLY -- a lead worth chasing by hand, not a derivation.
"""
import glob
import io
import json
import os
import sys
from collections import Counter, OrderedDict

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "scripts"))

NEEDS_HORIZON = ("HR", "RATE_RATIO", "RATERATIO", "IRR")
HORIZON_OUTCOME_FIELDS = ("follow_up", "time_frame", "timeframe", "horizon",
                          "follow_up_window")
HORIZON_TRIAL_FIELDS = ("registered_primary_timeframe", "follow_up",
                        "median_follow_up", "duration")


def _period_re():
    import re
    return re.compile(
        r"[0-9]+(\.[0-9]+)?\s*(week|wk|month|mo|year|yr|day)s?", re.I)


PERIOD = _period_re()


def _plain_int(v):
    return isinstance(v, int) and isinstance(v, bool) is False


def _num(v):
    ok = isinstance(v, (int, float)) and isinstance(v, bool) is False
    return v if ok else None


def objects():
    """Every OBJECT, in path order. The denominator lives here and nowhere else."""
    out = []
    for p in sorted(glob.glob(os.path.join(ROOT, "ssot", "*", "*.json"))):
        try:
            obj = json.load(io.open(p, encoding="utf-8"))
        except Exception:
            continue
        if isinstance(obj, dict) and obj.get("app_id"):
            out.append((os.path.basename(os.path.dirname(p)), p, obj))
    return out


def live_outcomes(obj):
    """[(oid, measure)] for outcomes holding a live pooled point estimate."""
    out = []
    by = ((obj.get("results") or {}).get("by_outcome") or {})
    for oid, rec in by.items():
        if isinstance(rec, dict) is False:
            continue
        pooled = rec.get("pooled")
        if isinstance(pooled, dict) is False:
            continue
        if pooled.get("withdrawn"):
            continue
        if pooled.get("point") is None:
            continue
        out.append((oid, str(pooled.get("measure") or "").strip().upper()
                    or "(none)"))
    return sorted(out)


def horizon_for(obj, oid):
    """(text, field) for THIS outcome, or (None, None).

    A trial-level period is accepted only from a trial that CONTRIBUTES this
    outcome. Lending another trial's follow-up to this row is the same
    wrong-denominator error the participants column shed.
    """
    trials = (obj.get("inputs") or {}).get("trials") or []
    for t in trials:
        if isinstance(t, dict) is False:
            continue
        e = (t.get("by_outcome") or {}).get(oid)
        if isinstance(e, dict) is False:
            continue
        for f in HORIZON_OUTCOME_FIELDS:
            v = e.get(f)
            if isinstance(v, str) and v.strip() and PERIOD.search(v):
                return v.strip(), "by_outcome.%s" % f
    for t in trials:
        if isinstance(t, dict) is False:
            continue
        if isinstance((t.get("by_outcome") or {}).get(oid), dict) is False:
            continue
        for f in HORIZON_TRIAL_FIELDS:
            v = t.get(f)
            if isinstance(v, str) and v.strip() and PERIOD.search(v):
                return v.strip(), "trial.%s" % f
    return None, None


def in_object_cells(obj):
    """{oid: n_trials_holding_cells} from outcome-specific in-object fields."""
    per = Counter()
    for t in ((obj.get("inputs") or {}).get("trials") or []):
        if isinstance(t, dict) is False:
            continue
        for oid, e in ((t.get("by_outcome") or {})).items():
            if isinstance(e, dict) is False:
                continue
            c, tr = e.get("control"), e.get("treatment")
            if (isinstance(c, dict) and isinstance(tr, dict)
                    and _plain_int(c.get("events")) and _plain_int(c.get("n"))
                    and _plain_int(tr.get("events"))
                    and _plain_int(tr.get("n"))):
                per[oid] += 1
    return per


def trial_level_cells(obj):
    """Count of trials whose ARMS carry events + participants for both roles.

    Trial-level and therefore never merged into the computable count -- arms
    describe the trial's primary endpoint, not an arbitrary outcome.
    """
    n = 0
    for t in ((obj.get("inputs") or {}).get("trials") or []):
        if isinstance(t, dict) is False:
            continue
        roles = {}
        for a in (t.get("arms") or []):
            if isinstance(a, dict) is False:
                continue
            r = str(a.get("role") or "").lower()
            ev = a.get("events")
            np_ = a.get("participants")
            if r in ("treatment", "control") and _plain_int(ev) and _plain_int(np_):
                roles[r] = True
        rpc = t.get("registration_primary_counts")
        if isinstance(rpc, dict) and all(
                _num(rpc.get(k)) is not None for k in
                ("treatment_events", "control_events",
                 "treatment_n", "control_n")):
            roles["treatment"] = roles["control"] = True
        if len(roles) == 2:
            n += 1
    return n


def sidecar_cells(sidecar):
    """n_studies holding a 2x2 in an r_validation sidecar.

    SCHEMA, READ FROM THE FILES RATHER THAN ASSUMED. A sidecar is FLAT and
    describes exactly ONE outcome: pooled statistics at the top level and a
    `trials` list whose rows carry `tE`, `tN`, `cE`, `cN` -- treatment events
    and denominator, control events and denominator.

    A first version of this function looked for `outcomes` / `by_outcome` /
    `results` containers holding rows keyed `ai/bi/ci/di`, none of which exist
    anywhere in this corpus. It therefore returned 0 for all 755 sidecars, and
    0 is exactly what a real data gap looks like. It was caught only because
    692 of 746 had been reported as holding cells earlier in this project, so
    the zero contradicted a known number. A zero measures the instrument until
    something independent says otherwise.
    """
    if isinstance(sidecar, dict) is False:
        return 0
    trials = sidecar.get("trials")
    if isinstance(trials, list) is False:
        return 0
    n = 0
    for s in trials:
        if isinstance(s, dict) is False:
            continue
        if all(_num(s.get(k)) is not None for k in ("tE", "tN", "cE", "cN")):
            n += 1
    return n


import re as _re

_NCT = _re.compile(r"NCT\d{7,8}")


def _norm_topic(s):
    s = s.lower().replace("_", "-")
    for suf in ("-auto-full-review", "-auto-full", "-review", "-full"):
        if s.endswith(suf):
            s = s[:-len(suf)]
    return _re.sub(r"[^a-z0-9]", "", s)


def _sidecar_index():
    idx = {}
    for p in glob.glob(os.path.join(ROOT, "outputs", "r_validation",
                                    "*.json")):
        name = os.path.splitext(os.path.basename(p))[0]
        try:
            idx.setdefault(_norm_topic(name), []).append(
                (name, json.load(io.open(p, encoding="utf-8"))))
        except Exception:
            continue
    return idx


def proven_sidecar_for(topic, obj, idx):
    """The topic's sidecar, ACCEPTED ONLY ON SHARED TRIAL REGISTRATIONS.

    Returns (sidecar_or_None, state). A normalised filename match alone is a
    name, and a name is not an identity: of 155 objects, 121 have a name match
    and 14 of those share NO registration with the file they matched. Accepting
    names would have attributed another topic's 2x2 cells to those 14, silently
    and in a way that raises the headline number -- the direction that gets
    checked least.

    States are reported separately rather than collapsed into "unmapped",
    because they are different facts:
      PROVEN_BY_NCT_OVERLAP           usable
      NAME_MATCH_REFUTED_BY_NCT       a name collision, correctly rejected
      NAME_MATCH_BUT_OBJECT_HAS_NO_NCT  unprovable either way, not rejected
      NO_NAME_MATCH                   no candidate at all
    """
    cands = idx.get(_norm_topic(topic), [])
    if len(cands) == 0:
        return None, "NO_NAME_MATCH"
    obj_ncts = set(_NCT.findall(json.dumps(
        (obj.get("inputs") or {}).get("trials") or [])))
    if len(obj_ncts) == 0:
        return None, "NAME_MATCH_BUT_OBJECT_HAS_NO_NCT"
    for _name, side in cands:
        side_ncts = set(_NCT.findall(json.dumps(side.get("trials") or [])))
        if side_ncts & obj_ncts:
            return side, "PROVEN_BY_NCT_OVERLAP"
    return None, "NAME_MATCH_REFUTED_BY_NCT"


def main():
    idx = _sidecar_index()

    def _sidecar_for(topic, obj=None):
        return proven_sidecar_for(topic, obj or {}, idx)[0]

    objs = objects()
    have, havent = [], []
    for topic, path, obj in objs:
        live = live_outcomes(obj)
        (have if live else havent).append((topic, path, obj, live))

    print("UNIT: OBJECT (ssot/*/*.json carrying an app_id)")
    print("  objects                                   %d" % len(objs))
    print("  hold >=1 LIVE pooled point estimate       %d" % len(have))
    print("  hold NONE                                 %d" % len(havent))
    print("  identity: %d + %d == %d"
          % (len(have), len(havent), len(objs)))
    print("")

    # ---- Q1: the list -------------------------------------------------
    listing = []
    for topic, path, obj, live in have:
        rows = []
        for oid, measure in live:
            h, f = horizon_for(obj, oid)
            rows.append(OrderedDict([
                ("outcome", oid),
                ("measure", measure),
                ("needs_time_horizon", measure in NEEDS_HORIZON),
                ("time_horizon", h),
                ("time_horizon_field", f),
            ]))
        listing.append(OrderedDict([
            ("topic", topic),
            ("app_id", obj.get("app_id")),
            ("path", os.path.relpath(path, ROOT).replace("\\", "/")),
            ("n_live_outcomes", len(rows)),
            ("outcomes", rows),
        ]))

    n_rows = sum(x["n_live_outcomes"] for x in listing)
    print("UNIT: OUTCOME (a live pooled outcome; NOT a topic)")
    print("  live pooled outcomes across those objects %d" % n_rows)
    hz = [r for x in listing for r in x["outcomes"] if r["needs_time_horizon"]]
    print("  of which the measure needs a period       %d" % len(hz))
    print("    hold a period                           %d"
          % len([r for r in hz if r["time_horizon"]]))
    print("    hold none                               %d"
          % len([r for r in hz if r["time_horizon"] is None]))
    print("")
    print("MEASURE MIX (unit: OUTCOME)")
    for k, v in sorted(Counter(r["measure"] for x in listing
                               for r in x["outcomes"]).items()):
        print("   %-18s %d" % (k, v))
    print("")

    # ---- Q2: the ceiling ----------------------------------------------
    print("=" * 70)
    print("IS THE CEILING REAL? -- objects with NO live pooled estimate")
    print("UNIT: OBJECT. denominator %d" % len(havent))
    states = Counter()
    map_states = Counter()
    detail = []
    n_mapped = 0
    for topic, path, obj, _live in havent:
        per = in_object_cells(obj)
        side_obj, map_state = proven_sidecar_for(topic, obj, idx)
        map_states[map_state] += 1
        if side_obj is not None:
            n_mapped += 1
        best_in = max(per.values()) if per else 0
        best_side = sidecar_cells(side_obj)
        best = max(best_in, best_side)
        tl = trial_level_cells(obj)
        if best >= 2:
            st = "COMPUTABLE_NOT_COMPUTED"
        elif best == 1:
            st = "SINGLE_TRIAL_CELLS_ONLY"
        elif tl >= 2:
            st = "CELLS_TRIAL_LEVEL_ONLY"
        elif side_obj is None:
            # NOT a data gap. No sidecar resolved for this topic, so the
            # out-of-object cells were never looked at. Reporting this as
            # "no cells" would be a scan reporting its own reach as coverage.
            st = "NOT_MEASURED_NO_SIDECAR_MAPPED"
        else:
            st = "NO_CELLS_AND_SIDECAR_WAS_READ"
        states[st] += 1
        detail.append(OrderedDict([
            ("topic", topic),
            ("state", st),
            ("max_trials_with_cells_for_one_outcome", best),
            ("from_in_object", best_in),
            ("from_sidecar", best_side),
            ("trials_with_trial_level_arms", tl),
            ("sidecar_mapping_state", map_state),
        ]))
    print("  topic -> sidecar, PROVEN BY SHARED NCT     %d of %d"
          % (n_mapped, len(havent)))
    for k in sorted(map_states):
        print("     %-34s %d" % (k, map_states[k]))
    print("    (a low mapping rate would make every sidecar figure below a")
    print("     statement about the MAPPER, not about the evidence)")
    print("")
    for k in ("COMPUTABLE_NOT_COMPUTED", "SINGLE_TRIAL_CELLS_ONLY",
              "CELLS_TRIAL_LEVEL_ONLY", "NO_CELLS_AND_SIDECAR_WAS_READ",
              "NOT_MEASURED_NO_SIDECAR_MAPPED"):
        print("  %-28s %d" % (k, states.get(k, 0)))
    print("  identity: %d == %d" % (sum(states.values()), len(havent)))
    print("")
    ceiling_now = len(have)
    ceiling_max = len(have) + states.get("COMPUTABLE_NOT_COMPUTED", 0)
    print("  CEILING TODAY (unit: OBJECT)              %d of %d"
          % (ceiling_now, len(objs)))
    print("  CEILING IF THE COMPUTABLE ARE COMPUTED    %d of %d"
          % (ceiling_max, len(objs)))
    unmeasured = states.get("NOT_MEASURED_NO_SIDECAR_MAPPED", 0)
    checked = len(havent) - unmeasured
    if checked:
        rate = states.get("COMPUTABLE_NOT_COMPUTED", 0) / float(checked)
        print("")
        print("  THE CEILING ABOVE IS A LOWER BOUND. %d of the %d objects"
              % (unmeasured, len(havent)))
        print("  without an estimate were NEVER LOOKED AT for out-of-object")
        print("  cells, because no sidecar resolved for their topic. Among the")
        print("  %d that WERE looked at, %d were computable (%.0f%%)."
              % (checked, states.get("COMPUTABLE_NOT_COMPUTED", 0),
                 100.0 * rate))
        print("  Projecting that rate onto the unmeasured %d would put the"
              % unmeasured)
        print("  ceiling near %d of %d -- PROJECTION, NOT A MEASUREMENT, and"
              % (int(round(ceiling_max + rate * unmeasured)), len(objs)))
        print("  it is quoted only to size the mapper as the next lever.")
    print("")
    print("  COMPUTABLE_NOT_COMPUTED, BY NAME")
    for d in detail:
        if d["state"] == "COMPUTABLE_NOT_COMPUTED":
            print("    %-32s cells for %d trials on one outcome "
                  "(in-object %d, sidecar %d)"
                  % (d["topic"][:32],
                     d["max_trials_with_cells_for_one_outcome"],
                     d["from_in_object"], d["from_sidecar"]))

    out = OrderedDict([
        ("unit_of_denominator", "OBJECT = one ssot/*/*.json carrying app_id"),
        ("n_objects", len(objs)),
        ("n_objects_with_live_pooled_estimate", len(have)),
        ("n_objects_without", len(havent)),
        ("n_live_pooled_outcomes", n_rows),
        ("ceiling_today_objects", ceiling_now),
        ("ceiling_if_computable_computed_objects", ceiling_max),
        ("states_of_objects_without", dict(states)),
        ("objects_without_mapped_to_a_sidecar", n_mapped),
        ("sidecar_mapping_states", dict(map_states)),
        ("ceiling_is_a_lower_bound_because_unmapped",
         states.get("NOT_MEASURED_NO_SIDECAR_MAPPED", 0)),
        ("objects_with_live_pooled_estimate", listing),
        ("objects_without_live_pooled_estimate", detail),
    ])
    d = os.path.join(ROOT, "evidence", "2026-09-02-hta-ceiling")
    if os.path.isdir(d) is False:
        os.makedirs(d)
    p = os.path.join(d, "hta_ceiling.json")
    io.open(p, "w", encoding="utf-8", newline="\n").write(
        json.dumps(out, indent=1, ensure_ascii=False))
    print("")
    print("wrote %s" % os.path.relpath(p, ROOT))
    return out


if __name__ == "__main__":
    main()
