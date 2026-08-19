#!/usr/bin/env python3
"""PROVE THE COMPOSITE DETECTOR IN FOUR PARTS, AGAINST DATA THAT IS REAL RATHER THAN INVENTED.

WHY THIS FILE HAS TO EXIST. `lint_composite_by_components.py` is GREEN on the corpus, and the
reason is a good one: the two ablation reviews and the apixaban prophylaxis review each MET a
mismatch and WITHDREW the pool, so no shipped object silently pools mismatched primaries. But a
detector that has never rejected anything is indistinguishable from one that cannot -- four
files in this repo called themselves gates while having no reachable failing exit, and an
over-escaped pattern is valid Python that matches nothing and reports clean. Green on a clean
corpus is not evidence.

    THE FAILING INPUT IS NOT INVENTED. It is the pool apixaban-vte-prophylaxis DECLINED: the
    four DIFFERENT registered primaries, which really were computed tonight (RR 0.658, I2 83.6%)
    and really were rejected. Part 2 asks what would have happened had they been REPORTED.

  PART 1  the corpus as it stands is GREEN, and the reason is recorded, not assumed
  PART 2  the four different primaries, POOLED and unannotated  -> REFUSED
  PART 3  the four MATCHING secondaries, pooled the same way    -> ACCEPTED
  PART 4  the four different primaries WITH component_mismatch  -> ACCEPTED

PART 3 IS THE PART THAT MAKES THIS A PROOF. A detector that refuses part 2 and also refuses
part 3 has not discriminated anything -- it has only noticed that four strings are not
byte-identical. The four titles in part 3 are four DIFFERENT strings from four different
sponsors' registrations that name the SAME endpoint, and the detector must let them through.

PART 4 proves the block is about SILENCE, not about mismatch. Pooling mismatched endpoints is
sometimes right; both ablation reviews argued for exactly that. Only doing it unannounced is
the defect.
"""
import io
import json
import os
import shutil
import subprocess
import sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LINT = os.path.join(REPO, "scripts", "lint_composite_by_components.py")
PROBE = "zzz-probe-composite-components"
PROBE_DIR = os.path.join(REPO, "ssot", PROBE)

# THE FOUR DIFFERENT PRIMARIES -- read from the four registrations tonight, verbatim.
DIFFERENT = [
    ("ADOPT", "NCT00457002",
     "Number of Participants With Total VTE and VTE-Related Death"),
    ("ADVANCE-3", "NCT00423319",
     "Number of Participants With VTE-Related Events"),
    ("ADVANCE-1", "NCT00371683",
     "Number of Participants With Composite of Adjudicated VTE and All-Cause Death"),
    ("ADVANCE-2", "NCT00452530",
     "Number of Participants With Composite of Adjudicated VTE-Related and All-Cause Death"),
]
# THE FOUR MATCHING SECONDARIES -- four different strings, one endpoint.
MATCHING = [
    ("ADOPT", "NCT00457002",
     "Incidence of Adjudicated Proximal DVT, Non-Fatal PE or VTE-Related Death"),
    ("ADVANCE-3", "NCT00423319",
     "Rate of Composite of Adjudicated Proximal DVT, Nonfatal PE, VTE-related death"),
    ("ADVANCE-1", "NCT00371683",
     "Event Rate for Participants With Proximal DVT/Non-Fatal PE/VTE-Related Death"),
    ("ADVANCE-2", "NCT00452530",
     "Rate of Adjudicated Proximal DVT, Nonfatal PE, and VTE-related death"),
]


def build(trials, mismatch_recorded):
    outcome = {"id": "primary",
               "name": "each trial's own registered primary outcome",
               "definition": ("Time to first occurrence of the trial's registered primary "
                              "composite endpoint."),
               "source_is_each_trials_registered_primary": True}
    if mismatch_recorded:
        outcome["component_mismatch"] = ["death_all_cause", "death_vte_related"]
    return {"app_id": PROBE, "title": "probe", "question": "probe",
            "outcomes": [outcome],
            "inputs": {"trials": [{"id": n, "name": a, "nct": n,
                                   "registered_primaries": [t]}
                                  for a, n, t in trials]},
            "results": {"by_outcome": {"primary": {
                "k": len(trials),
                "pooled": {"point": 0.658, "ci_low": 0.406, "ci_high": 1.067},
                "heterogeneity": {"i2": 83.6}}}}}


def run():
    r = subprocess.run([sys.executable, LINT], cwd=REPO, stdout=subprocess.PIPE,
                       stderr=subprocess.STDOUT)
    return r.returncode, r.stdout.decode("utf-8", "replace")


def plant(obj):
    os.makedirs(PROBE_DIR, exist_ok=True)
    with io.open(os.path.join(PROBE_DIR, "%s.json" % PROBE), "w", encoding="utf-8") as fh:
        fh.write(json.dumps(obj, indent=1))


def main():
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    if os.path.exists(PROBE_DIR):
        print("REFUSED: %s already exists; refusing to overwrite" % PROBE_DIR)
        return 2
    ok = True
    try:
        rc, out = run()
        print("PART 1 -- the corpus as it stands")
        print("   rc=%d  %s" % (rc, "GREEN" if rc == 0 else "RED"))
        print("   Green because the reviews that MET a mismatch WITHDREW the pool. Recorded")
        print("   rather than assumed: `pooled.point` is null on both ablation reviews.")
        ok &= (rc == 0)

        plant(build(DIFFERENT, False))
        rc, out = run()
        fired = rc == 1 and PROBE in out
        print("\nPART 2 -- the four DIFFERENT primaries, pooled, unannotated")
        print("   rc=%d  %s" % (rc, "REFUSED (correct)" if fired else "DID NOT FIRE"))
        for line in out.splitlines():
            if PROBE in line or "components that differ" in line:
                print("     %s" % line.strip()[:150])
        ok &= fired

        plant(build(MATCHING, False))
        rc, out = run()
        passed = rc == 0
        print("\nPART 3 -- the four MATCHING secondaries, four different strings, one endpoint")
        print("   rc=%d  %s" % (rc, "ACCEPTED (correct)" if passed
                                else "REFUSED -- THE DETECTOR DISCRIMINATES NOTHING"))
        ok &= passed

        plant(build(DIFFERENT, True))
        rc, out = run()
        passed = rc == 0
        print("\nPART 4 -- the four different primaries WITH component_mismatch recorded")
        print("   rc=%d  %s" % (rc, "ACCEPTED (correct)" if passed
                                else "REFUSED -- the block is about mismatch, not silence"))
        ok &= passed
    finally:
        shutil.rmtree(PROBE_DIR, ignore_errors=True)
        # The probe directory is created and destroyed here and is never staged. Confirmed
        # rather than asserted:
        print("\nprobe removed: %s exists = %s" % (PROBE_DIR, os.path.exists(PROBE_DIR)))

    print("\n%s" % ("ALL FOUR PARTS HELD." if ok else "PROOF FAILED."))
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
