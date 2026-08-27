# -*- coding: utf-8 -*-
"""GATE: a stored effect estimate must follow from the counts stored beside it.

THE CLASS, AND WHY NOTHING CATCHES IT PASSIVELY. A stored number that does not reconcile with
its own source is invisible to every instrument on this project: renderers display it,
validators check its shape, gates check its provenance, and none of them recomputes it. It was
found by a human reading a publication.

WHAT THIS GATE FINDS -- AND THE DENOMINATOR IS THE FINDING. 178 per-trial records exist across
the corpus. EIGHT of them store event counts. So a gate that recomputes an estimate from its
own stored counts can reach 4.5% of the corpus, and the other 170 records are not "passing" --
they are unreachable.

That is the real defect, and it is architectural rather than arithmetical: THE CORPUS DOES NOT
STORE THE INPUTS TO ITS OWN ARITHMETIC. Every per-trial estimate carries a `derivation` string
saying in prose how it was obtained, and no field from which it could be recomputed. A prose
derivation is a claim about a calculation; stored counts would be the calculation. One can be
checked and the other can only be believed.

THE ROTAVIRUS CASE THAT PROMPTED THIS. NCT00241644 in rotavirus-vaccine-africa-review stores
OR 0.5615 (0.3264 to 0.9659) with derivation "DERIVED by conversion: the extractor recovered
an estimate and a variance on the analysis scale". Its publication serves 56/2974 versus
70/1443, which give OR 0.376 and RR 0.388 -- neither is 0.5615. The store holds NO counts for
it, so the discrepancy CANNOT BE ADJUDICATED FROM THE OBJECT AT ALL. It may be a different
outcome, a different timepoint, a per-protocol rather than intention-to-treat population, or
wrong. Nothing here decides that, and nothing is re-derived or fixed: re-deriving a stored
estimate from counts found elsewhere would replace an unverified number with a differently
unverified number, and would erase the evidence that they disagree.

READ-ONLY. Verdict on stdout, never in the exit status alone.
"""
import collections
import glob
import io
import json
import math
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
os.chdir(os.path.dirname(os.path.dirname(HERE)))

# the several spellings the corpus uses for the same four numbers
T_EV = ("treatment_events", "events_treatment", "events_apixaban", "e_t", "events_t")
C_EV = ("control_events", "events_control", "events_comparator", "e_c", "events_c")
T_N = ("n_treatment", "n_t", "total_treatment", "n_apixaban")
C_N = ("n_control", "n_c", "total_control", "n_comparator")


def first(r, keys):
    for k in keys:
        v = r.get(k)
        if isinstance(v, (int, float)) and not isinstance(v, bool):
            return float(v)
    return None


def main():
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace",
                                  line_buffering=True)
    tot = 0
    checkable, bad, ok, partial = [], [], [], []
    for p in sorted(glob.glob("ssot/*/*.json")):
        t = os.path.basename(os.path.dirname(p))
        if os.path.basename(p) != t + ".json":
            continue
        try:
            ob = json.load(io.open(p, encoding="utf-8"))
        except Exception:
            continue
        for oid, rr in (((ob.get("results") or {}).get("by_outcome")) or {}).items():
            for r in (rr.get("per_trial") or []):
                tot += 1
                et, ec = first(r, T_EV), first(r, C_EV)
                nt, nc = first(r, T_N), first(r, C_N)
                pt = r.get("point")
                if None in (et, ec, nc) or not isinstance(pt, (int, float)):
                    if et is not None or ec is not None:
                        partial.append((t, oid, r.get("nct"),
                                        [k for k in (T_EV + C_EV + T_N + C_N) if k in r]))
                    continue
                if nt is None:
                    partial.append((t, oid, r.get("nct"), "events present, treatment N absent"))
                    continue
                checkable.append((t, oid, r.get("nct")))
                meas = str(r.get("measure") or "").upper()
                try:
                    if meas == "OR":
                        calc = (et / (nt - et)) / (ec / (nc - ec))
                    elif meas in ("RR", "RATE_RATIO"):
                        calc = (et / nt) / (ec / nc)
                    else:
                        partial.append((t, oid, r.get("nct"), "measure %s not recomputable" % meas))
                        continue
                except ZeroDivisionError:
                    partial.append((t, oid, r.get("nct"), "a zero cell"))
                    continue
                # A ZERO EVENT COUNT MAKES THE RATIO ZERO, AND log(0) IS NOT AN ERROR TO
                # SWALLOW. It is a real state -- a zero cell -- and it gets its own arm
                # rather than an except that would drop the record out of every count.
                if calc <= 0 or float(pt) <= 0:
                    partial.append((t, oid, r.get("nct"),
                                    "a zero cell: ratio %s, stored point %s" % (calc, pt)))
                    checkable.pop()
                    continue
                rel = abs(math.log(calc) - math.log(float(pt)))
                (ok if rel < 0.02 else bad).append(
                    (t, oid, r.get("nct"), meas, float(pt), calc, rel))

    print("")
    print("GATE -- does a stored estimate follow from the counts stored beside it?")
    print("")
    print("  per-trial records in the corpus           %4d  == the denominator" % tot)
    print("  storing enough counts to recompute        %4d   %5.1f%%"
          % (len(checkable), 100.0 * len(checkable) / tot if tot else 0))
    print("  storing SOME counts but not enough        %4d" % len(partial))
    print("  storing no counts at all -- UNREACHABLE   %4d   %5.1f%%"
          % (tot - len(checkable) - len(partial),
             100.0 * (tot - len(checkable) - len(partial)) / tot if tot else 0))
    print("")
    print("  of the recomputable ones:")
    print("     reconciles with its counts             %4d" % len(ok))
    print("     DOES NOT reconcile                     %4d" % len(bad))
    for t, oid, nct, meas, pt, calc, rel in bad[:10]:
        print("   REFUSE  %-28s %-16s %s  stored %s %.4f, counts give %.4f"
              % (t[:28], str(oid)[:16], nct, meas, pt, calc))
    print("")
    print("  THE UNREACHABLE %d ARE NOT PASSING. The corpus does not store the inputs to its"
          % (tot - len(checkable) - len(partial)))
    print("  own arithmetic: each estimate carries a prose `derivation` and no field from")
    print("  which it could be recomputed. A prose derivation is a claim ABOUT a calculation;")
    print("  stored counts would BE the calculation. One can be checked, the other believed.")
    print("")
    print("  NCT00241644 (rotavirus-vaccine-africa-review) is the case in point: stored")
    print("  OR 0.5615, publication counts 56/2974 vs 70/1443 give OR 0.376 / RR 0.388, and")
    print("  the object holds NO counts, so the disagreement cannot be adjudicated from it.")
    print("  Not re-derived and not fixed -- deliberately. Replacing an unverified number")
    print("  with a differently unverified one would erase the evidence that they disagree.")
    return 1 if bad else 0


if __name__ == "__main__":
    raise SystemExit(main())
