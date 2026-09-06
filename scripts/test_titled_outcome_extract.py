# -*- coding: utf-8 -*-
"""Tests for the four titled-outcome extraction rules. Each fires on a known-hard case and each
was written to FAIL before the rule it guards existed. Run: python scripts/test_titled_outcome_extract.py

Real-trial cases read the AACT snapshot; if it is absent those are SKIPPED (not passed) and the
controlled fake-table cases still run -- the rules are proven on controlled input regardless."""
from __future__ import annotations
import io, os, sys
sys.path.insert(0, "scripts")
import titled_outcome_extract as T
import reproduce_benchmark as RB

RESULTS = []


def ok(name, cond, detail=""):
    RESULTS.append((name, bool(cond), detail))


def fake(groups, meas_rows, counts):
    """Build a minimal tables dict. meas_rows: list of (group, title, classification, units,
    param_type, param_value). counts: {group: N}. One outcome_id 'O1'."""
    meas = []
    for g, title, cls, units, pt, val in meas_rows:
        meas.append({"nct_id": "NCTFAKE", "outcome_id": "O1", "ctgov_group_code": g,
                     "classification": cls, "category": "", "title": title, "units": units,
                     "param_type": pt, "param_value": str(val), "param_value_num": str(val)})
    return {"meas": {"NCTFAKE": meas}, "groups": {"NCTFAKE": groups},
            "counts": {"NCTFAKE": {"O1": dict(counts)}}, "ae": {"NCTFAKE": []}}


# ---- RULE 1 core: parse_class_denoms ------------------------------------------------
ok("R1 parse '(n=2629, 2616)'", T.parse_class_denoms("Alanine aminotransferase, high (n=2629, 2616)") == [2629, 2616])
ok("R1 parse '(n=343; n=334; n=345)'", T.parse_class_denoms("Week 2 (n=343; n=334; n=345)") == [343, 334, 345])
ok("R1 no n= -> None", T.parse_class_denoms("Cardiovascular death") is None)

# ---- RULE 1 integration: class-title N OVERRIDES outcome_counts ----------------------
# outcome_counts carries a WRONG randomised total (999); the class title carries the analysis N.
tb = fake({"OG000": "Drug", "OG001": "Placebo"},
          [("OG000", "CV composite", "Cardiovascular death (n=200, 100)", "percentage of subjects", "NUMBER", 10),
           ("OG001", "CV composite", "Cardiovascular death (n=200, 100)", "percentage of subjects", "NUMBER", 5)],
          {"OG000": 999, "OG001": 999})
r = T.extract_titled("NCTFAKE", "cv_death", tb, trt_terms=("drug",))
ok("R1 uses class-title N not outcome_counts",
   r.get("denom_source") == "class_title" and r.get("tN") == 200 and r.get("cN") == 100
   and r.get("tE") == 20 and r.get("cE") == 5, str(r))

# ---- RULE 2: arithmetic (pct*N) and direct count ------------------------------------
tb2 = fake({"OG000": "Drug", "OG001": "Placebo"},
           [("OG000", "CV composite", "Cardiovascular death", "percentage of subjects", "NUMBER", 4.7),
            ("OG001", "CV composite", "Cardiovascular death", "percentage of subjects", "NUMBER", 6.0)],
           {"OG000": 4668, "OG001": 4672})
r2 = T.extract_titled("NCTFAKE", "cv_death", tb2, trt_terms=("drug",))
ok("R2 arithmetic pct*N (LEADER CV death shape)",
   r2.get("event_route") == "arithmetic(pct*N)" and r2.get("tE") == 219 and r2.get("cE") == 280, str(r2))

# ---- RULE 2b: incidence RATE units are REFUSED (AMPLITUDE-O/HARMONY MACE=5 bug) -------
tbR = fake({"OG000": "Drug", "OG001": "Placebo"},
           [("OG000", "MACE composite", "Cardiovascular death", "events per 100 participant-years", "NUMBER", 3.9),
            ("OG001", "MACE composite", "Cardiovascular death", "events per 100 participant-years", "NUMBER", 5.3)],
           {"OG000": 2717, "OG001": 1359})
rR = T.extract_titled("NCTFAKE", "cv_death", tbR, trt_terms=("drug",))
ok("R2b rate units refused (not a fabricated count)", "tE" not in rR, str(rR))

# ---- RULE 4: 0/0 -> NOT_DISCRIMINATING ---------------------------------------------
tb4 = fake({"OG000": "Drug", "OG001": "Placebo"},
           [("OG000", "CV composite", "Cardiovascular death", "Participants", "COUNT_OF_PARTICIPANTS", 0),
            ("OG001", "CV composite", "Cardiovascular death", "Participants", "COUNT_OF_PARTICIPANTS", 0)],
           {"OG000": 100, "OG001": 100})
r4 = T.extract_titled("NCTFAKE", "cv_death", tb4, trt_terms=("drug",))
ok("R4 0/0 -> NOT_DISCRIMINATING", r4.get("status") == "NOT_DISCRIMINATING", str(r4))

# ---- AMPLITUDE-O pooled multi-dose guard (no double count) ---------------------------
# A pre-pooled "4 mg+6 mg" TRT group PLUS single-dose groups: must use pooled, not sum all.
tbA = fake({"OG000": "Efpeglenatide 4 mg+6 mg", "OG001": "Efpeglenatide 4 mg",
            "OG002": "Efpeglenatide 6 mg", "OG003": "Placebo"},
           [("OG000", "CV composite", "Cardiovascular death", "Participants", "COUNT_OF_PARTICIPANTS", 60),
            ("OG001", "CV composite", "Cardiovascular death", "Participants", "COUNT_OF_PARTICIPANTS", 30),
            ("OG002", "CV composite", "Cardiovascular death", "Participants", "COUNT_OF_PARTICIPANTS", 30),
            ("OG003", "CV composite", "Cardiovascular death", "Participants", "COUNT_OF_PARTICIPANTS", 49)],
           {"OG000": 2718, "OG001": 1359, "OG002": 1359, "OG003": 1355})
rA = T.extract_titled("NCTFAKE", "cv_death", tbA, trt_terms=("efpeglenatide",))
ok("AMPLITUDE-O pooled arm not double-counted (tE=60 not 120, tN=2718)",
   rA.get("tE") == 60 and rA.get("tN") == 2718, str(rA))

# ---- REAL cases (need AACT) ----------------------------------------------------------
aact = RB.resolve_aact()
if not aact:
    ok("AACT snapshot present", False, "SKIP: no snapshot; real-trial cases not run")
else:
    tb_real = T.load_tables(aact, ["NCT03037931", "NCT02692716", "NCT01179048"])
    # HEART-FID death: titled 131/158, N 1532/1533 -> RR ~0.830; AE cross-check DISAGREES (354/367)
    hf = T.extract_titled("NCT03037931", "all_cause_death", tb_real, trt_terms=("ferric carboxymaltose", "carboxymaltose"))
    ok("HEART-FID titled death 131/158 N 1532/1533",
       hf.get("tE") == 131 and hf.get("cE") == 158 and hf.get("tN") == 1532 and hf.get("cN") == 1533, str(hf))
    ae = T.ae_crosscheck("NCT03037931", tb_real, "all_cause_death", trt_terms=("ferric carboxymaltose", "carboxymaltose"))
    ok("RULE 3 AE cross-check DISAGREES and is not substituted",
       ae and ae["tE"] != hf.get("tE") and abs(ae["tE"] - 354) <= 5, "titled=%s ae=%s" % (hf.get("tE"), ae))
    # PIONEER-6 death 23/45
    p6 = T.extract_titled("NCT02692716", "all_cause_death", tb_real)
    ok("PIONEER-6 death 23/45", p6.get("tE") == 23 and p6.get("cE") == 45, str(p6))
    # LEADER CV death arithmetic 219/280
    ld = T.extract_titled("NCT01179048", "cv_death", tb_real)
    ok("LEADER CV death arithmetic 219/280",
       ld.get("tE") == 219 and ld.get("cE") == 280 and ld.get("event_route") == "arithmetic(pct*N)", str(ld))


if __name__ == "__main__":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    npass = sum(1 for _, c, _ in RESULTS if c)
    print("titled_outcome_extract tests: %d/%d passed\n" % (npass, len(RESULTS)))
    for name, c, detail in RESULTS:
        print("  %-52s %s%s" % (name, "OK" if c else "*** FAIL ***", ("   " + detail[:120]) if not c else ""))
    raise SystemExit(0 if npass == len(RESULTS) else 1)
