#!/usr/bin/env python3
"""PLANT THE DEFECT AND WATCH THE ENUMERATION MOVE, THEN RESTORE AND ASSERT IT.

An enumeration nobody has ever seen respond to a change is a number, not a measurement.
This plants four defects, one per class the enumerator claims to distinguish, in a REAL
corpus file, requires the count to move in the stated direction, and then restores the
file and asserts the restoration byte-for-byte against a hash taken before the first
write. If the hash does not match at the end, this exits non-zero and says so: a plant
that cannot prove it cleaned up is worse than no plant.

  WHY A REAL FILE AND NOT A FIXTURE. A fixture proves the classifier's logic; it cannot
  prove the classifier is READING the corpus, that the path it walks is the path the
  corpus uses, or that a field it expects is where it expects it. Two of the three
  selector defects in this project's last week were in the WALK, not in the logic, and a
  fixture cannot see them.

  WHY THE HASH AND NOT `git checkout`. `git checkout` restores. It does not prove the
  restoration happened, and this project has read success off a shell that never ran.
  The hash is checked in-process, after the restore, on bytes read back from disk.

TARGET: `ablation-af-review`, chosen because its four rows carry BOTH marker kinds the
enumerator distinguishes -- the bare `PRIMARY` rank token and an as-printed `derivation`
-- so one file exercises both axes. It is verified clean in git before anything is
written, and this script refuses to run if it is not.

  THE TARGET IS PART OF THE CONTROL, SO IT IS PINNED HERE BY ITS PROPERTIES, NOT BY ITS
  STATE. The requirement is `>= 1 bare-PRIMARY row and >= 1 as-printed row`, asserted at
  run time. If a later session's work removes those properties this script FAILS LOUDLY
  rather than silently passing on a file that no longer exercises anything -- the control
  that dies on success, which is the most-repeated lesson in this repo.
"""
import hashlib
import io
import json
import os
import subprocess
import sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TOPIC = "ablation-af-review"
TARGET = os.path.join(REPO, "ssot", TOPIC, TOPIC + ".json")
ENUM = os.path.join(REPO, "scripts", "enumerate_converter_derived_effects_2026_08_24.py")
OUT = os.path.join(REPO, "outputs", "converter_derived_effects_2026_08_24.json")


def sha(path):
    with open(path, "rb") as fh:
        return hashlib.sha256(fh.read()).hexdigest()


def measure():
    r = subprocess.run([sys.executable, ENUM], cwd=REPO,
                       stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    if r.returncode != 0:
        raise RuntimeError("enumerator exited %d: %s"
                           % (r.returncode, r.stdout.decode("utf-8", "replace")[-800:]))
    with io.open(OUT, encoding="utf-8") as fh:
        d = json.load(fh)
    return {"rows": d["rows"],
            "point_ours": d["axis1_whose_number"].get("POINT_COMPUTED_HERE", 0),
            "interval_ours": d["axis1_whose_number"].get(
                "POINT_PRINTED_INTERVAL_COMPUTED_HERE", 0),
            "as_printed": d["axis1_whose_number"].get("AS_PRINTED", 0),
            "cnd_no_field": d["axis1_whose_number"].get(
                "COULD_NOT_DETERMINE__no_provenance_field", 0),
            "cnd_unmatched": d["axis1_whose_number"].get(
                "COULD_NOT_DETERMINE__prose_present_unmatched", 0),
            "selection_ours": d["axis2_whose_choice"].get("SELECTION_BY_THIS_REVIEW", 0),
            "primary_theirs": d["axis2_whose_choice"].get("TRIALS_OWN_PRIMARY", 0),
            "cnd_no_rank": d["axis2_whose_choice"].get(
                "COULD_NOT_DETERMINE__no_rank_field", 0)}


def load():
    with io.open(TARGET, encoding="utf-8") as fh:
        return json.load(fh)


def save(obj):
    with io.open(TARGET, "w", encoding="utf-8") as fh:
        fh.write(json.dumps(obj, indent=1, ensure_ascii=False))


def first_row(obj, pred):
    for oid, blk in ((obj.get("results") or {}).get("by_outcome") or {}).items():
        for i, r in enumerate((blk or {}).get("per_trial") or []):
            if isinstance(r, dict) and pred(r):
                return oid, i, r
    return None, None, None


# Each plant: (name, mutate(obj) -> bool applied, {counter: expected delta})
def _p_rank_to_secondary(obj):
    oid, i, r = first_row(obj, lambda r: str(
        r.get("endpoint_rank_in_its_own_trial") or "").strip().lower() == "primary")
    if r is None:
        return False
    r["endpoint_rank_in_its_own_trial"] = "SECONDARY"
    return True


def _p_rank_removed(obj):
    oid, i, r = first_row(obj, lambda r: str(
        r.get("endpoint_rank_in_its_own_trial") or "").strip().lower() == "primary")
    if r is None:
        return False
    del r["endpoint_rank_in_its_own_trial"]
    return True


def _p_derivation_removed(obj):
    oid, i, r = first_row(obj, lambda r: r.get("derivation") is not None)
    if r is None:
        return False
    del r["derivation"]
    return True


def _p_derivation_to_computed(obj):
    oid, i, r = first_row(obj, lambda r: r.get("derivation") is not None
                          and "derived_here" not in r and not r.get("how"))
    if r is None:
        return False
    r["derivation"] = ("risk ratio computed here from the two counts on this row, with a "
                       "normal-approximation interval on the log scale")
    return True


def _p_derivation_unmatched(obj):
    oid, i, r = first_row(obj, lambda r: r.get("derivation") is not None
                          and "derived_here" not in r and not r.get("how"))
    if r is None:
        return False
    r["derivation"] = "obtained by a route this marker table does not describe"
    return True


PLANTS = (
    ("a bare-PRIMARY rank flipped to SECONDARY",
     _p_rank_to_secondary, {"selection_ours": +1, "primary_theirs": -1}),
    ("a bare-PRIMARY rank field deleted",
     _p_rank_removed, {"primary_theirs": -1, "cnd_no_rank": +1}),
    ("an as-printed `derivation` field deleted",
     _p_derivation_removed, {"as_printed": -1, "cnd_no_field": +1}),
    ("an as-printed `derivation` rewritten as a computation",
     _p_derivation_to_computed, {"as_printed": -1, "point_ours": +1}),
    ("a `derivation` rewritten to match no declared marker",
     _p_derivation_unmatched, {"as_printed": -1, "cnd_unmatched": +1}),
)


def main():
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    if not os.path.exists(TARGET):
        print("REFUSED: target %s does not exist." % TARGET)
        return 1
    dirty = subprocess.run(["git", "status", "--porcelain", "--", TARGET], cwd=REPO,
                           stdout=subprocess.PIPE).stdout.decode().strip()
    if dirty:
        print("REFUSED: target is already modified in the worktree (%r). This script "
              "restores by hash and must not be given a file whose clean state is "
              "unknown." % dirty)
        return 1

    baseline_hash = sha(TARGET)
    with open(TARGET, "rb") as fh:
        baseline_bytes = fh.read()

    obj = load()
    n_primary = sum(1 for oid, blk in ((obj.get("results") or {}).get("by_outcome") or {}).items()
                    for r in ((blk or {}).get("per_trial") or [])
                    if isinstance(r, dict) and str(
                        r.get("endpoint_rank_in_its_own_trial") or "").strip().lower() == "primary")
    n_deriv = sum(1 for oid, blk in ((obj.get("results") or {}).get("by_outcome") or {}).items()
                  for r in ((blk or {}).get("per_trial") or [])
                  if isinstance(r, dict) and r.get("derivation") is not None)
    print("TARGET %s  sha256 %s" % (os.path.relpath(TARGET, REPO), baseline_hash[:16]))
    print("   bare-PRIMARY rows: %d   rows with a `derivation`: %d" % (n_primary, n_deriv))
    if n_primary < 1 or n_deriv < 1:
        print("REFUSED: the target no longer carries the properties this control needs "
              "(>=1 bare-PRIMARY row and >=1 row with a `derivation`). This is the "
              "control expiring on someone's success, not a pass. Re-key it.")
        return 1

    base = measure()
    print("   BASELINE %s" % json.dumps(base, sort_keys=True))
    print()

    failures, restored_ok = [], True
    for name, mutate, expect in PLANTS:
        obj = load()
        if not mutate(obj):
            failures.append("%s -- NO ROW TO PLANT INTO" % name)
            print("FAIL  %-52s no row to plant into" % name)
            continue
        save(obj)
        try:
            got = measure()
        finally:
            with open(TARGET, "wb") as fh:
                fh.write(baseline_bytes)
        ok = True
        deltas = []
        for k, want in expect.items():
            d = got[k] - base[k]
            deltas.append("%s %+d(want %+d)" % (k, d, want))
            if d != want:
                ok = False
        if got["rows"] != base["rows"]:
            ok = False
            deltas.append("rows moved %d->%d" % (base["rows"], got["rows"]))
        print("%-4s  %-52s %s" % ("PASS" if ok else "FAIL", name, "  ".join(deltas)))
        if not ok:
            failures.append(name)

    after = sha(TARGET)
    print()
    print("RESTORATION: sha256 %s %s baseline %s"
          % (after[:16], "==" if after == baseline_hash else "!=", baseline_hash[:16]))
    if after != baseline_hash:
        restored_ok = False
        print("CRITICAL: the target was NOT restored. Run "
              "`git checkout -- %s` and re-verify." % os.path.relpath(TARGET, REPO))
    final = measure()
    if final != base:
        restored_ok = False
        print("CRITICAL: the enumeration does not return to baseline after restore.")
    else:
        print("the enumeration returns to baseline after restore.")

    if failures or not restored_ok:
        print()
        print("PLANT FAILED: %s" % ("; ".join(failures) or "restoration"))
        return 1
    print()
    print("PLANT PASSED: %d of %d planted defects moved the enumeration in the stated "
          "direction, and the target is byte-identical to its pre-plant state."
          % (len(PLANTS), len(PLANTS)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
