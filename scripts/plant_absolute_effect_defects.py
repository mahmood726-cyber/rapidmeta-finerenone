r"""Plant each defect these checks claim to catch, in a REAL store file, and
watch the check FAIL. Then restore and prove the restoration byte-identical.

WHY
    A check that has only ever been observed to PASS has not been shown to
    have a second reachable outcome. Four gate shapes in this project turned
    out to have exactly one. The only evidence that a check is a check is
    watching it go red on a defect you put there yourself.

WHAT IS PLANTED
    1. ARM ROLE SWAP        exchange control and treatment in one trial of a
                            real topic. verify_arm_roles must report a
                            RECIPROCAL and FAIL. This is the quiet defect:
                            with it planted, absolute_effects still emits a
                            plausible NNT.
    2. STORE REFUSAL        set pooled.withdrawn on a topic that currently
                            computes. absolute_effects must move it to
                            REFUSED_BY_STORE and emit NO absolute effect.
    3. MEASURE SUBSTITUTION relabel a pooled RR as an HR. absolute_effects
                            must refuse it as not convertible rather than
                            treating a hazard ratio as a risk ratio.
    4. BASELINE DELETION    remove the control-arm counts. absolute_effects
                            must emit NNT_NOT_COMPUTABLE with the named
                            NO_CONTROL_ARM_RISK reason -- never a blank,
                            never a zero, and never a substituted default.

SAFETY
    Every plant writes the ORIGINAL BYTES back and verifies the sha256 of the
    file matches what it was before. The restore runs in a finally block, so
    it happens even if a check raises.
"""
from __future__ import annotations
import sys, os, json, hashlib, subprocess

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)


def sha(path):
    with open(path, "rb") as fh:
        return hashlib.sha256(fh.read()).hexdigest()


def run_module(mod, *args):
    # NOT text=True: on Windows that decodes the child's output as the
    # console codepage (cp1252), which mangles any non-ASCII byte a store
    # reason happens to carry and has previously made a verifier accuse
    # intact objects of changed values. Decode as UTF-8 explicitly.
    p = subprocess.run([sys.executable, os.path.join(HERE, mod)] + list(args),
                       capture_output=True, cwd=ROOT)
    out = (p.stdout or b"").decode("utf-8", "replace")
    err = (p.stderr or b"").decode("utf-8", "replace")
    return p.returncode, out + err


def state_of(topic, outcome):
    """Ask absolute_effects for one row, in a fresh process-free import."""
    for m in list(sys.modules):
        if m in ("absolute_effects",):
            del sys.modules[m]
    import absolute_effects as ae
    for path, obj, name, entry, _k in ae.candidates():
        if os.path.basename(os.path.dirname(path)) == topic and name == outcome:
            return ae.evaluate(path, obj, name, entry)
    return None


class Plant(object):
    """Context manager: mutate a real file, guarantee byte-identical restore."""

    def __init__(self, path):
        self.path = path

    def __enter__(self):
        with open(self.path, "rb") as fh:
            self.original = fh.read()
        self.before = hashlib.sha256(self.original).hexdigest()
        return self

    def write_obj(self, obj):
        with open(self.path, "w", encoding="utf-8") as fh:
            json.dump(obj, fh, indent=1, ensure_ascii=False)

    def load(self):
        return json.loads(self.original.decode("utf-8"))

    def __exit__(self, *exc):
        with open(self.path, "wb") as fh:
            fh.write(self.original)
        after = sha(self.path)
        self.restored_identical = (after == self.before)
        print("    restore: sha256 before %s / after %s -> %s"
              % (self.before[:12], after[:12],
                 "BYTE-IDENTICAL" if self.restored_identical else
                 "*** DIFFERS ***"))
        return False


results = []


def record(name, planted_outcome, ok):
    results.append((name, planted_outcome, ok))
    print("    %s: %s" % ("PLANT CAUGHT" if ok else "PLANT MISSED (the check "
                          "has only one reachable outcome)", planted_outcome))


# ------------------------------------------------------------------ plant 1

def plant_arm_swap():
    topic, outcome = "apixaban-vte-prophylaxis", "major_vte"
    path = os.path.join(ROOT, "ssot", topic, topic + ".json")
    print("\n[1] ARM ROLE SWAP in %s/%s" % (topic, outcome))
    rc0, out0 = run_module("verify_arm_roles.py")
    print("    baseline verifier exit=%d (expect 0 PASS)" % rc0)
    with Plant(path) as p:
        obj = p.load()
        e = obj["results"]["by_outcome"][outcome]
        row = e["per_trial"][0]
        row["events_apixaban"], row["events_comparator"] = \
            row["events_comparator"], row["events_apixaban"]
        row["n_apixaban"], row["n_comparator"] = \
            row["n_comparator"], row["n_apixaban"]
        p.write_obj(obj)
        rc, out = run_module("verify_arm_roles.py")
        swapped_line = [l for l in out.splitlines() if "SWAPPED" in l]
        caught = rc == 1 and bool(swapped_line)
        for l in swapped_line:
            print("    " + l.strip())
        print("    verifier exit=%d (expect 1 FAIL)" % rc)
        # the point of this plant: the NUMBER still looks fine
        r = state_of(topic, outcome)
        if r and r.get("state") == "COMPUTABLE":
            print("    NOTE: with the swap planted, absolute_effects still "
                  "emits a plausible NNT of %.1f at baseline %.4f. That is "
                  "why this defect needs an INDEPENDENT witness, not a "
                  "sanity check on the output."
                  % (r["nnt"], r["baseline_value"]))
    record("arm role swap", "verify_arm_roles reports a reciprocal and exits 1",
           caught)


# ------------------------------------------------------------------ plant 2

def plant_store_refusal():
    topic, outcome = "nirsevimab-infant-rsv-review", "primary"
    path = os.path.join(ROOT, "ssot", topic, topic + ".json")
    print("\n[2] STORE REFUSAL planted on %s/%s" % (topic, outcome))
    before = state_of(topic, outcome)
    print("    before: state=%s" % (before or {}).get("state"))
    with Plant(path) as p:
        obj = p.load()
        e = obj["results"]["by_outcome"][outcome]
        e["pooled"]["withdrawn"] = True
        e["pooled"]["withdrawn_reason"] = "PLANTED FOR THE PLANT TEST"
        p.write_obj(obj)
        r = state_of(topic, outcome)
        print("    after : state=%s reason=%r"
              % (r.get("state"), r.get("store_reason_verbatim")))
        caught = (r.get("state") == "REFUSED_BY_STORE"
                  and r.get("store_reason_verbatim")
                  == "PLANTED FOR THE PLANT TEST"
                  and "nnt" not in r)
    record("store refusal honoured first",
           "state becomes REFUSED_BY_STORE, verbatim reason carried, no NNT "
           "emitted", caught)


# ------------------------------------------------------------------ plant 3

def plant_measure_substitution():
    topic, outcome = "cab-prep-hiv-review", "primary"
    path = os.path.join(ROOT, "ssot", topic, topic + ".json")
    print("\n[3] MEASURE SUBSTITUTION (RR relabelled HR) on %s/%s"
          % (topic, outcome))
    before = state_of(topic, outcome)
    print("    before: state=%s measure=%s"
          % ((before or {}).get("state"), (before or {}).get("measure")))
    with Plant(path) as p:
        obj = p.load()
        obj["results"]["by_outcome"][outcome]["pooled"]["measure"] = "HR"
        p.write_obj(obj)
        r = state_of(topic, outcome)
        print("    after : state=%s" % r.get("state"))
        print("    reason: %s" % str(r.get("reason"))[:150])
        caught = (r.get("state") == "NNT_NOT_COMPUTABLE"
                  and "MEASURE_NOT_CONVERTIBLE:HR" in str(r.get("reason")))
    record("hazard ratio not treated as a risk ratio",
           "state becomes NNT_NOT_COMPUTABLE with MEASURE_NOT_CONVERTIBLE:HR",
           caught)


# ------------------------------------------------------------------ plant 4

def plant_baseline_deletion():
    topic, outcome = "agyw-hiv-prep-review", "primary"
    path = os.path.join(ROOT, "ssot", topic, topic + ".json")
    print("\n[4] BASELINE DELETION on %s/%s" % (topic, outcome))
    before = state_of(topic, outcome)
    print("    before: state=%s baseline=%.4f"
          % ((before or {}).get("state"), (before or {}).get("baseline_value")))
    with Plant(path) as p:
        obj = p.load()
        e = obj["results"]["by_outcome"][outcome]
        for r_ in e.get("per_trial") or []:
            ap = r_.get("as_posted")
            if isinstance(ap, dict):
                for k in list(ap):
                    if "placebo" in k:
                        del ap[k]
        for t in (obj.get("inputs") or {}).get("trials") or []:
            bo = t.get("by_outcome")
            if isinstance(bo, dict) and outcome in bo:
                bo[outcome].pop("control", None)
        p.write_obj(obj)
        r = state_of(topic, outcome)
        print("    after : state=%s" % r.get("state"))
        print("    reason: %s" % str(r.get("reason"))[:160])
        caught = (r.get("state") == "NNT_NOT_COMPUTABLE"
                  and "NO_CONTROL_ARM_RISK" in str(r.get("reason"))
                  and "baseline_value" not in r)
    record("no baseline is ever substituted",
           "state becomes NNT_NOT_COMPUTABLE with NO_CONTROL_ARM_RISK and no "
           "baseline_value", caught)


# ------------------------------------------------------------------ plant 5

def _classify(stem):
    for m in list(sys.modules):
        if m in ("tau2_blast_radius", "absolute_effects_sidecar"):
            del sys.modules[m]
    import tau2_blast_radius as tb
    return tb.classify(os.path.join(ROOT, "outputs", "r_validation",
                                    stem + ".json"))


def plant_heterogeneity():
    """A real homogeneous pool, made heterogeneous, must stop reading as
    LEGITIMATELY_ZERO. Without this the classifier could be returning that
    state for every file and would look exactly as it does now."""
    stem = None
    import json as _j
    import glob as _g
    for p in sorted(_g.glob(os.path.join(ROOT, "outputs", "r_validation",
                                         "*.json"))):
        if os.path.basename(p).startswith("_"):
            continue
        try:
            d = _j.load(open(p, encoding="utf-8"))
        except Exception:
            continue
        if not isinstance(d, dict) or d.get("tau2") != 0.0:
            continue
        rows = [t for t in (d.get("trials") or [])
                if isinstance(t, dict) and isinstance(t.get("yi"), (int, float))
                and isinstance(t.get("vi"), (int, float)) and t["vi"] > 0]
        if len(rows) < 3:
            continue
        # The precondition is the CLASSIFIED STATE, not the stored tau2. A
        # first version of this plant selected on stored tau2 alone and drew
        # a file already in INTERVAL_WIDENS_ONLY, so the plant could not
        # change the state and reported MISSED for a working classifier.
        cand = os.path.basename(p)[:-5]
        if _classify(cand)["state"] == "LEGITIMATELY_ZERO":
            stem = cand
            break
    if stem is None:
        record("heterogeneity is detected", "no suitable file found", False)
        return
    path = os.path.join(ROOT, "outputs", "r_validation", stem + ".json")
    print("\n[5] HETEROGENEITY PLANTED into %s" % stem)
    before = _classify(stem)
    print("    before: state=%s tau2_correct=%.6g"
          % (before["state"], before.get("tau2_correct", 0.0)))
    with Plant(path) as p:
        obj = p.load()
        rows = [t for t in obj["trials"]
                if isinstance(t.get("yi"), (int, float))]
        # push the trial estimates far apart; variances untouched
        for i, t in enumerate(rows):
            t["yi"] = 2.5 if i % 2 == 0 else -2.5
        p.write_obj(obj)
        after = _classify(stem)
        print("    after : state=%s tau2_correct=%.6g"
              % (after["state"], after.get("tau2_correct", 0.0)))
        caught = (before["state"] == "LEGITIMATELY_ZERO"
                  and after["state"] != "LEGITIMATELY_ZERO"
                  and after.get("tau2_correct", 0.0) > 0.0)
    record("heterogeneity is detected, not erased",
           "a homogeneous pool stops reading LEGITIMATELY_ZERO once its "
           "trials disagree", caught)


def plant_flip_direction():
    """The classifier must see a flip in BOTH directions. The earlier
    delegated pass tested only excludes-null -> includes-null, which cannot
    see a claim the correction CREATES. This plants that direction."""
    print("\n[6] CLAIM_CREATED direction")
    import tau2_blast_radius as tb
    # constructed, not read from disk: two trials that agree strongly, so the
    # correct estimator finds no heterogeneity and the interval tightens.
    # A first version used tau2=0.30 here and the "wide" interval still
    # excluded the null, so the plant reported MISSED for a working check.
    # 0.60 is chosen so the wide interval genuinely spans zero -- the plant
    # has to actually create the condition it claims to test.
    ys = [0.9, 0.95, 0.92, 0.94]
    vs = [0.02, 0.02, 0.02, 0.02]
    mu_s, lo_s, hi_s = tb.pool(ys, vs, 0.60)   # a large tau2 -> wide, spans 0
    mu_c, lo_c, hi_c = tb.pool(ys, vs, 0.0)    # no tau2 -> tight, excludes 0
    created = (not tb.excludes_null(lo_s, hi_s)) and tb.excludes_null(lo_c, hi_c)
    print("    wide  interval %.4f..%.4f excludes null: %s"
          % (lo_s, hi_s, tb.excludes_null(lo_s, hi_s)))
    print("    tight interval %.4f..%.4f excludes null: %s"
          % (lo_c, hi_c, tb.excludes_null(lo_c, hi_c)))
    record("the CLAIM_CREATED direction is reachable",
           "excludes_null distinguishes both directions, so a flip that "
           "CREATES a claim would be classified rather than missed", created)


def main():
    print("PLANTING DEFECTS IN REAL STORE FILES, WATCHING THE CHECKS FAIL")
    print("Every plant is reverted and the revert is verified by sha256.")
    plants = [plant_arm_swap, plant_store_refusal,
              plant_measure_substitution, plant_baseline_deletion,
              plant_heterogeneity, plant_flip_direction]
    for fn in plants:
        fn()
    print("\n" + "=" * 70)
    print("PLANT SUMMARY")
    bad = 0
    for name, expect, ok in results:
        print("  %-42s %s" % (name, "CAUGHT" if ok else "MISSED"))
        if not ok:
            bad += 1
            print("      expected: %s" % expect)
    print("  %d of %d planted defects were caught." % (len(results) - bad,
                                                       len(results)))
    return 1 if bad else 0


if __name__ == "__main__":
    raise SystemExit(main())
