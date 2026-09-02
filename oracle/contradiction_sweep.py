# -*- coding: utf-8 -*-
"""I-squared versus tau-squared: a contradiction readable inside one artefact.

WHY THIS NEEDS NO ORACLE. I-squared and tau-squared are not independent. I-squared
above zero requires Q > df; and Q > df forces tau-squared above zero under both
DerSimonian-Laird (tau2 = (Q - df)/C) and REML. So an artefact storing I2 > 0
BESIDE tau2 = 0 contradicts ITSELF. No refit, no metafor, no per-trial rows.

THAT IS THE POINT. The external oracle is limited by coverage -- most stored blocks
lack refittable per-trial rows, so ~324 estimates are UNCOVERED. This check reads
two numbers that are already in the file, so it reaches EVERY artefact holding both
fields. A contradiction needs no ground truth to interpret.

IT DETECTS THE THIRD FAILURE MODE. The tau-squared defect is fixed in code and the
OMECAMTIV artefacts still store tau2 = 0.0 beside I2 = 27.39 -- generated 2026-05-26,
before either fix. Code-fixed / corpus-stale is its own state and no code-level test
can see it.

POPULATION IS NAMED, NOT ASSUMED. `747 top-level files in outputs/r_validation/` is
NOT the same population as `351 binary sidecars`. Counts are reported against the
files actually opened and the subset actually holding both fields.
"""
import glob
import io
import json
import os

ROOT = r"F:\rapidmeta-ssot-shell\outputs\r_validation"
EPS_TAU = 1e-12          # tau2 treated as zero at or below this
EPS_I2 = 1e-9            # I2 treated as zero at or below this


def num(v):
    if isinstance(v, bool):
        return None
    if isinstance(v, (int, float)):
        return float(v)
    return None


def main():
    files = sorted(glob.glob(os.path.join(ROOT, "*.json")))
    opened = 0
    unreadable = []
    both = []              # holds BOTH fields as numbers
    contradictions = []
    missing_field = 0

    for p in files:
        try:
            d = json.load(io.open(p, encoding="utf-8"))
        except Exception as e:
            unreadable.append((os.path.basename(p), repr(e)[:60]))
            continue
        opened += 1
        if not isinstance(d, dict):
            missing_field += 1
            continue
        # KEY MEMBERSHIP, not .get -- absent and null are different facts
        has_t = "tau2" in d
        has_i = "I2" in d
        t = num(d.get("tau2")) if has_t else None
        i2 = num(d.get("I2")) if has_i else None
        if t is None or i2 is None:
            missing_field += 1
            continue
        both.append(os.path.basename(p))
        if t <= EPS_TAU and i2 > EPS_I2:
            contradictions.append({
                "file": os.path.basename(p), "tau2": t, "I2": i2,
                "Q": num(d.get("Q")), "Qdf": num(d.get("Qdf")),
                "k": d.get("k"), "generated_on": d.get("generated_on"),
                "generated_by": d.get("generated_by"),
                "method": d.get("method"),
            })

    print("POPULATION, NAMED")
    print("  directory                    : %s" % ROOT)
    print("  *.json files found           : %d" % len(files))
    print("  opened                       : %d" % opened)
    print("  unreadable                   : %d" % len(unreadable))
    print("  missing tau2 and/or I2       : %d  (UNCHECKABLE, not clean)" % missing_field)
    print("  HOLDING BOTH FIELDS          : %d   <- the denominator" % len(both))
    print()
    n = len(both)
    print("RESULT")
    print("  self-contradictory (I2 > 0 with tau2 = 0) : %d of %d  (%.1f%%)"
          % (len(contradictions), n, 100.0 * len(contradictions) / max(1, n)))
    print()
    if contradictions:
        by_date = {}
        for c in contradictions:
            by_date.setdefault(str(c.get("generated_on")), 0)
            by_date[str(c.get("generated_on"))] += 1
        print("  by generated_on:", dict(sorted(by_date.items())))
        print()
        print("  first 25, named:")
        for c in contradictions[:25]:
            print("   %-46s I2=%8.4f tau2=%s Q=%s df=%s k=%s %s"
                  % (c["file"][:46], c["I2"], c["tau2"], c["Q"], c["Qdf"],
                     c["k"], c["generated_on"]))
    json.dump({"root": ROOT, "files_found": len(files), "opened": opened,
               "unreadable": unreadable[:50], "missing_field": missing_field,
               "denominator_holding_both": n,
               "n_contradictory": len(contradictions),
               "contradictions": contradictions},
              io.open("contradiction_sweep_out.json", "w", encoding="utf-8"), indent=1)


if __name__ == "__main__":
    main()
