#!/usr/bin/env python3
"""PLANT THE DEFECT IN THE D5 SELECTION DECLARATION, INCLUDING THE BRANCH THAT CANNOT FIRE.

The declaration emitted by `_selection_declaration` has four states. Three of them occur in
the corpus as it stands. The fourth, `LAYERS_DISAGREE`, occurs ZERO times -- the two layers
that carry `endpoint_rank_in_its_own_trial` agree on all 14 records where both are present.

  A BRANCH WITH NO REACHABLE INPUT IS NOT A GUARD. This project shipped a P0 check whose
  finding was unreachable, and shipped a verdict guard whose separator class meant it passed
  107 of 107 packets it could not fail on. A branch nobody has watched execute is a claim,
  not a check. So `LAYERS_DISAGREE` is planted here explicitly: the two layers are made to
  disagree in a real corpus file and the state is REQUIRED to appear.

FOUR PLANTS, one per state, plus one for the cross-layer FALLBACK that was the defect this
declaration was fixed for. Each mutates a real corpus file, requires the declaration tally
to move in a stated direction, restores the file, and asserts the restoration by sha256 read
back from disk -- never off an exit code, because this project has read success off a shell
that never ran.

TARGET `sglt2-hf`: 4 records carry the rank on BOTH layers and 7 on the rendered layer, so
one file exercises the both-layers path, the fallback path and the disagreement path. The
requirement is asserted at run time, not assumed, so this fails loudly rather than passing
vacuously if a later session's work removes what it exercises.

`evidence/2026-08-19-batch1/rob2.json` is snapshotted and restored too: the assessor MERGES
into it, so a plant that left it holding planted values would poison every later reader.
"""
import hashlib
import io
import json
import os
import subprocess
import sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TOPIC = "sglt2-hf"
TARGET = os.path.join(REPO, "ssot", TOPIC, TOPIC + ".json")
ASSESS = os.path.join(REPO, "scripts", "rob2_assess_2026_08_19.py")
ROB2 = os.path.join(REPO, "evidence", "2026-08-19-batch1", "rob2.json")
TOPICS = ["ablation-af-heart-failure", "ablation-af-medical-therapy", "alirocumab-lipid",
          "attr-cm-review", "bempedoic-acid-review", "early-rhythm-control-af",
          "iv-iron-hf", "sglt2-hf"]

CND = "COULD_NOT_DETERMINE"
THEIRS = "NO_SELECTION_BY_THIS_REVIEW"
OURS = "SELECTED_BY_THIS_REVIEW"
DISAGREE = "LAYERS_DISAGREE"


def sha(path):
    with open(path, "rb") as fh:
        return hashlib.sha256(fh.read()).hexdigest()


def measure():
    r = subprocess.run([sys.executable, ASSESS] + TOPICS, cwd=REPO,
                       stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    if r.returncode != 0:
        raise RuntimeError("assessor exited %d: %s"
                           % (r.returncode, r.stdout.decode("utf-8", "replace")[-900:]))
    with io.open(ROB2, encoding="utf-8") as fh:
        d = json.load(fh)
    out = {"records": 0, CND: 0, THEIRS: 0, OURS: 0, DISAGREE: 0, "fallback_layer": 0}
    for _t, per_topic in (d.get("by_topic") or {}).items():
        for _oid, per in per_topic.items():
            for _i, rec in per.items():
                out["records"] += 1
                sd = rec.get("our_selection_declared_not_rated") or {}
                st = sd.get("state")
                if st in out:
                    out[st] += 1
                if "page renders" in (sd.get("read_from") or ""):
                    out["fallback_layer"] += 1
    return out


def load():
    with io.open(TARGET, encoding="utf-8") as fh:
        return json.load(fh)


def save(obj):
    with io.open(TARGET, "w", encoding="utf-8") as fh:
        fh.write(json.dumps(obj, indent=1, ensure_ascii=False))


def _both_layer_keys(obj):
    """(outcome, identifier) pairs whose rank is present on BOTH layers."""
    inp = set()
    for tr in ((obj.get("inputs") or {}).get("trials") or []):
        ident = tr.get("nct") or tr.get("id")
        for oid, b in (tr.get("by_outcome") or {}).items():
            if b.get("endpoint_rank_in_its_own_trial") is not None:
                inp.add((oid, ident))
    rend = set()
    for oid, b in ((obj.get("results") or {}).get("by_outcome") or {}).items():
        for r in ((b or {}).get("per_trial") or []):
            if isinstance(r, dict) and r.get("endpoint_rank_in_its_own_trial") is not None:
                rend.add((oid, r.get("nct") or r.get("trial_id")))
    return sorted(inp & rend), sorted(rend - inp)


def _inputs_block(obj, key):
    oid, ident = key
    for tr in ((obj.get("inputs") or {}).get("trials") or []):
        if (tr.get("nct") or tr.get("id")) == ident:
            b = (tr.get("by_outcome") or {}).get(oid)
            if b is not None:
                return b
    return None


def _rendered_row(obj, key):
    oid, ident = key
    for r in (((obj.get("results") or {}).get("by_outcome") or {}).get(oid) or {}).get("per_trial") or []:
        if isinstance(r, dict) and (r.get("nct") or r.get("trial_id")) == ident:
            return r
    return None


def _p_layers_disagree(obj):
    both, _ = _both_layer_keys(obj)
    if not both:
        return False
    k = both[0]
    row = _rendered_row(obj, k)
    if row is None:
        return False
    row["endpoint_rank_in_its_own_trial"] = "SECONDARY"
    blk = _inputs_block(obj, k)
    if blk is None or str(blk.get("endpoint_rank_in_its_own_trial")).strip() == "SECONDARY":
        return False
    return True


def _p_both_layers_removed(obj):
    both, _ = _both_layer_keys(obj)
    if not both:
        return False
    k = both[0]
    blk, row = _inputs_block(obj, k), _rendered_row(obj, k)
    if blk is None or row is None:
        return False
    del blk["endpoint_rank_in_its_own_trial"]
    del row["endpoint_rank_in_its_own_trial"]
    return True


def _p_inputs_layer_removed(obj):
    """The defect that was fixed: the rank present ONLY on the rendered layer must still be
    read. Removing the inputs layer must NOT move any state -- only `read_from`."""
    both, _ = _both_layer_keys(obj)
    if not both:
        return False
    blk = _inputs_block(obj, both[0])
    if blk is None:
        return False
    del blk["endpoint_rank_in_its_own_trial"]
    return True


def _reads_as_theirs(rank):
    """THE CLASSIFIER'S OWN RULE, not one spelling of it.

    The first version of this predicate required the bare token `primary` and the plant
    REFUSED, because every both-layer row in the target says "the trial's own primary
    composite endpoint". That is the third narrow-predicate defect in this day's work -- the
    marker list, the rank matcher, and now the harness that tests them. A plant keyed to one
    spelling of what it is trying to flip tests the spelling, not the flip.
    """
    low = str(rank).strip().lower()
    return low in ("primary", "primary endpoint", "primary outcome") or "own primary" in low


def _p_both_layers_to_secondary(obj):
    both, _ = _both_layer_keys(obj)
    for k in both:
        blk, row = _inputs_block(obj, k), _rendered_row(obj, k)
        if blk is None or row is None:
            continue
        if not _reads_as_theirs(blk.get("endpoint_rank_in_its_own_trial")):
            continue
        blk["endpoint_rank_in_its_own_trial"] = "SECONDARY"
        row["endpoint_rank_in_its_own_trial"] = "SECONDARY"
        return True
    return False


PLANTS = (
    ("the two layers made to disagree -- THE UNREACHABLE BRANCH",
     _p_layers_disagree, {DISAGREE: +1, THEIRS: -1}),
    ("the rank removed from BOTH layers",
     _p_both_layers_removed, {CND: +1, THEIRS: -1}),
    ("the rank removed from the INPUTS layer only (the fixed defect)",
     _p_inputs_layer_removed, {CND: 0, THEIRS: 0, OURS: 0, "fallback_layer": +1}),
    ("a both-layer PRIMARY rewritten to SECONDARY on both",
     _p_both_layers_to_secondary, {OURS: +1, THEIRS: -1}),
)


def main():
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    for p in (TARGET, ROB2):
        if not os.path.exists(p):
            print("REFUSED: %s does not exist." % p)
            return 1
    dirty = subprocess.run(["git", "status", "--porcelain", "--", TARGET], cwd=REPO,
                           stdout=subprocess.PIPE).stdout.decode().strip()
    if dirty:
        print("REFUSED: target already modified in the worktree (%r). This restores by hash "
              "and must not be given a file whose clean state is unknown." % dirty)
        return 1

    target_hash = sha(TARGET)
    with open(TARGET, "rb") as fh:
        target_bytes = fh.read()
    with open(ROB2, "rb") as fh:
        rob2_bytes = fh.read()

    obj = load()
    both, rend_only = _both_layer_keys(obj)
    print("TARGET %s  sha256 %s" % (os.path.relpath(TARGET, REPO), target_hash[:16]))
    print("   records with the rank on BOTH layers: %d   on the rendered layer only: %d"
          % (len(both), len(rend_only)))
    if len(both) < 1:
        print("REFUSED: the target no longer carries a record with the rank on both layers, "
              "which is what three of these four plants exercise. This is the control "
              "expiring on someone's success, not a pass. Re-key it.")
        return 1

    base = measure()
    print("   BASELINE %s" % json.dumps(base, sort_keys=True))
    if base[DISAGREE] != 0:
        print("NOTE: %s is no longer zero in the corpus. The plant below still has to move "
              "it, but the branch is now reachable without one." % DISAGREE)
    print()

    failures = []
    for name, mutate, expect in PLANTS:
        obj = load()
        if not mutate(obj):
            failures.append("%s -- NO ROW TO PLANT INTO" % name)
            print("FAIL  %-58s no row to plant into" % name)
            continue
        save(obj)
        try:
            got = measure()
        finally:
            with open(TARGET, "wb") as fh:
                fh.write(target_bytes)
        ok, deltas = True, []
        for k, want in expect.items():
            d = got[k] - base[k]
            deltas.append("%s %+d(want %+d)" % (k, d, want))
            if d != want:
                ok = False
        if got["records"] != base["records"]:
            ok = False
            deltas.append("records moved %d->%d" % (base["records"], got["records"]))
        print("%-4s  %-58s %s" % ("PASS" if ok else "FAIL", name, "  ".join(deltas)))
        if not ok:
            failures.append(name)

    # RESTORE BOTH ARTEFACTS. The assessor merges into rob2.json, so leaving it holding a
    # planted value would poison every later reader of it.
    with open(ROB2, "wb") as fh:
        fh.write(rob2_bytes)
    after_t, restored = sha(TARGET), True
    print()
    print("RESTORATION target   sha256 %s %s %s"
          % (after_t[:16], "==" if after_t == target_hash else "!=", target_hash[:16]))
    if after_t != target_hash:
        restored = False
        print("CRITICAL: the corpus file was NOT restored. Run `git checkout -- %s`."
              % os.path.relpath(TARGET, REPO))
    final = measure()
    if final != base:
        restored = False
        print("CRITICAL: the declaration tally does not return to baseline after restore: "
              "%s" % json.dumps(final, sort_keys=True))
    else:
        print("the declaration tally returns to baseline after restore.")

    if failures or not restored:
        print()
        print("PLANT FAILED: %s" % ("; ".join(failures) or "restoration"))
        return 1
    print()
    print("PLANT PASSED: %d of %d planted defects moved the declaration in the stated "
          "direction -- including %s, which no corpus input reaches today."
          % (len(PLANTS), len(PLANTS), DISAGREE))
    return 0


if __name__ == "__main__":
    sys.exit(main())
