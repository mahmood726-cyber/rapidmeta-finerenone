#!/usr/bin/env python3
"""RE-POOL `bococizumab-lipid-review` WITH THE TRIAL ITS OWN SEARCH FOUND AND ITS OBJECT LACKED.

WHAT THIS IS NOT. It is not a correction of the estimate. The odds-ratio-from-counts was already
replaced on 2026-08-18 by the registry's own least-squares mean differences, and that
replacement stands untouched. THE MEASURE WAS FIXED AND THE EVIDENCE BASE WAS NEVER CHECKED --
the object recorded "search: not recorded on the page this object was built from".

The executed search (2026-08-19, `scripts/screen_bococizumab_2026_08_19.py`) surfaced 22
registrations and screened them to zero. FIVE are eligible, poolable, have posted LDL results
and are absent from the object. ONE of the five joins this pool, and the reason the other four
do not is the point of this file.

SPIRE-FH (NCT01968980, n=370) JOINS. Its registered primary is
    "Percent Change From Baseline in Low Density Lipoprotein Cholesterol (LDL-C) at Week 12"
-- the identical endpoint at the identical timepoint as all five incumbents -- and it posts a
least-squares mean difference of -54.5 (-59.5 to -49.5) in its own `analyses` block, which is
the SAME PROVENANCE as every value already in the pool. Nothing is derived.

THE OTHER FOUR ARE DOSE-RANGING TRIALS, AND A DOSE-RANGING TRIAL IS NOT ONE CONTRAST.

    NCT01342211   4 dose arms vs one placebo   LS mean differences  -5.63, -2.30, -37.72, -49.11
    NCT01350141   2 dose arms vs one placebo                       -21.81, -46.42
    NCT02055976   6 dose/route arms vs 2 placebos   -47.53 to -71.53, at Day 85 AND Day 113
    NCT01592240   dosing-SCHEDULE arms, percent change posted only as "Week 12 and 24" combined

Each of them randomised DOSE. Pooling one of their arms against placebo means choosing which
arm, and there is no rule in this review that chooses it: the effect inside NCT01342211 runs
from -2.30 to -49.11 depending on which dose is picked, which is a spread wider than the entire
pool. THE CHOICE WOULD BE OURS AND IT WOULD LOOK LIKE THE TRIAL'S. Same discipline as
`apixaban-vte-treatment` applied to NCT01195727 -- in scope, and contributing no single effect
estimate -- and the same reason the timepoint matters: three of the four post Day 85 or Day 113
rather than Week 12, so even the chosen contrast would not be the pooled estimand.

    A CONTINUOUS ENDPOINT HAS THE COMPOSITE PROBLEM TOO. It has no components to mismatch, so
    the mismatch moves to the TIMEPOINT and to the DOSE. "Percent change in LDL-C" is one name
    covering Week 12, Day 85, Day 113, and "Week 12 and 24" combined, at doses from 0.25 mg/kg
    to 150 mg. P37 is not about composites; it is about NAMES.

USAGE:  python scripts/repool_bococizumab_2026_08_19.py
        python scripts/repool_bococizumab_2026_08_19.py --selftest
"""
import io
import json
import math
import os
import sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(REPO, "scripts"))
import headline_reproducible_gate as HG                                    # noqa: E402

DEST = os.path.join(REPO, "evidence", "2026-08-19-batch1", "bococizumab_repool.json")
Z = 1.959963984540054
T = HG._T

# (trial, nct, MD, ci_low, ci_high, n analysed, registered outcome title) -- every row READ
# from the trial's own posted `analyses` block. Not one is derived by us.
INCUMBENT = [
    ("SPIRE-LDL", "NCT01968967", -56.2, -58.3, -54.0, 2139,
     "Percent Change From Baseline in Fasting Low Density Lipoprotein Cholesterol (LDL-C) at "
     "Week 12"),
    ("SPIRE-LL", "NCT02100514", -49.9, -54.0, -45.8, 746,
     "Percent Change From Baseline in Fasting Low Density Lipoprotein Cholesterol (LDL-C) at "
     "Week 12"),
    ("SPIRE-HR", "NCT01968954", -57.0, -61.0, -53.1, 711,
     "Percent Change From Baseline in Low Density Lipoprotein-Cholesterol (LDL-C) at Week 12"),
    ("SPIRE-AI", "NCT02458287", -63.4, -72.0, -54.7, 299,
     "Percent Change From Baseline at Week 12 in Fasting Low Density Lipoprotein Cholesterol "
     "(LDL-C) Level"),
    ("SPIRE-SI", "NCT02135029", -54.5, -60.1, -49.0, 184,
     "Percent Change From Baseline in Fasting Low Density Lipoprotein Cholesterol (LDL-C) at "
     "Week 12"),
]
RECOVERED = [
    ("SPIRE-FH", "NCT01968980", -54.5, -59.5, -49.5, 370,
     "Percent Change From Baseline in Low Density Lipoprotein Cholesterol (LDL-C) at Week 12"),
]
# Eligible, poolable, posted results -- and NOT pooled, each with its reason and its own
# numbers, so a reader can see exactly what the refusal costs.
DOSE_RANGING = {
    "NCT01342211": {"n": 93, "timepoint": "Day 85",
                    "contrasts": [-5.63, -2.30, -37.72, -49.11],
                    "why": "four dose arms against one placebo; the effect runs from -2.30 to "
                           "-49.11 across them, a spread wider than the whole pool"},
    "NCT01350141": {"n": 46, "timepoint": "Day 85", "contrasts": [-21.81, -46.42],
                    "why": "two dose arms against one placebo"},
    "NCT02055976": {"n": 218, "timepoint": "Day 85 and Day 113",
                    "contrasts": [-49.838, -66.754, -71.534, -47.531, -62.624, -64.268],
                    "why": "six dose/route arms against two separate placebos, and TWO "
                           "co-primary timepoints"},
    "NCT01592240": {"n": 354, "timepoint": "Week 12 and 24, combined in one measure",
                    "contrasts": [],
                    "why": "its PRIMARY is ABSOLUTE change; percent change is posted only at "
                           "SECONDARY rank and only as a combined 'Week 12 and 24' measure, so "
                           "there is no Week-12 percent-change contrast to take"},
}


def se_from_ci(lo, hi):
    """The standard error the printed interval implies, at 95 per cent. DERIVED, and said so."""
    return (hi - lo) / (2.0 * Z)


def pool(rows, label):
    ys = [r[2] for r in rows]
    vs = [se_from_ci(r[3], r[4]) ** 2 for r in rows]
    k = len(ys)
    wf = [1.0 / v for v in vs]
    mf = sum(w * y for w, y in zip(wf, ys)) / sum(wf)
    q = sum(w * (y - mf) ** 2 for w, y in zip(wf, ys))
    i2 = max(0.0, (q - (k - 1)) / q) * 100.0 if q > 0 else 0.0
    out = {"label": label, "k": k, "q": round(q, 4), "df": k - 1, "i2_pct": round(i2, 1),
           "n_participants": sum(r[5] for r in rows),
           "per_trial": [{"trial": r[0], "nct": r[1], "md": r[2], "ci_low": r[3],
                          "ci_high": r[4], "n": r[5], "outcome_title": r[6],
                          "provenance": "READ from the trial's posted `analyses` block "
                                        "(least-squares mean difference with its 95% CI)"}
                         for r in rows]}
    for how in ("REML", "PM"):
        t2 = HG._tau2(ys, vs, how)
        w = [1.0 / (v + t2) for v in vs]
        sw = sum(w)
        mu = sum(a * b for a, b in zip(w, ys)) / sw
        se = math.sqrt(1.0 / sw)
        rec = {"tau2": round(t2, 4), "md": round(mu, 4),
               "ci_low": round(mu - Z * se, 4), "ci_high": round(mu + Z * se, 4),
               "interval": "Wald, normal"}
        qh = sum(wi * (y - mu) ** 2 for wi, y in zip(w, ys)) / (k - 1)
        qf = max(1.0, qh)
        seh = math.sqrt(qf / sw)
        tc = T.get(k - 1)
        rec["hksj"] = {"q_hksj": round(qh, 4), "floored_to": round(qf, 4),
                       "floor_applied": qf > qh + 1e-12, "t_df": k - 1, "t_crit": tc,
                       "md": round(mu, 4), "ci_low": round(mu - tc * seh, 4),
                       "ci_high": round(mu + tc * seh, 4),
                       "interval": "Knapp-Hartung-Sidik-Jonkman, t on k-1 df, "
                                   "floor max(1, Q/(k-1))"}
        out[how] = rec
    return out


def main():
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    old = pool(INCUMBENT, "the five trials on the object -- REML, as published 2026-08-18")
    new = pool(INCUMBENT + RECOVERED, "the six the executed search supports")

    print("OLD  k=%d  n=%d  MD %.4f (%.4f to %.4f)  tau2 %.3f  I2 %.1f%%"
          % (old["k"], old["n_participants"], old["REML"]["md"], old["REML"]["ci_low"],
             old["REML"]["ci_high"], old["REML"]["tau2"], old["i2_pct"]))
    print("NEW  k=%d  n=%d  MD %.4f (%.4f to %.4f)  tau2 %.3f  I2 %.1f%%"
          % (new["k"], new["n_participants"], new["REML"]["md"], new["REML"]["ci_low"],
             new["REML"]["ci_high"], new["REML"]["tau2"], new["i2_pct"]))
    print("     HKSJ on %d df: %.4f (%.4f to %.4f)"
          % (new["REML"]["hksj"]["t_df"], new["REML"]["hksj"]["md"],
             new["REML"]["hksj"]["ci_low"], new["REML"]["hksj"]["ci_high"]))
    print("\nthe trial that joined:  SPIRE-FH NCT01968980  MD -54.5 (-59.5 to -49.5)  n=370")
    print("not pooled, with reasons: %s" % ", ".join(sorted(DOSE_RANGING)))

    out = {
        "topic": "bococizumab-lipid-review",
        "repooled_utc": "2026-08-19",
        "what_this_is_not": (
            "NOT a correction of the estimate. The odds-ratio-from-counts was replaced on "
            "2026-08-18 and that replacement stands. This checks the EVIDENCE BASE, which had "
            "never been checked -- the object recorded 'search: not recorded on the page this "
            "object was built from'."),
        "estimand": {
            "definition": "percent change from baseline in LDL-C at WEEK 12",
            "and_the_timepoint_is_part_of_it": (
                "Three of the four dose-ranging trials post Day 85 or Day 113 instead, and one "
                "posts 'Week 12 and 24' combined in a single measure. A CONTINUOUS ENDPOINT "
                "HAS NO COMPONENTS TO MISMATCH, so the mismatch moves to the TIMEPOINT and the "
                "DOSE -- and 'percent change in LDL-C' is one name covering all of them. P37 "
                "is about names, not about composites."),
        },
        "previous": old,
        "current": new,
        "the_trial_that_joined": {
            "nct": "NCT01968980", "name": "SPIRE-FH", "n": 370,
            "why_it_joins": ("Its registered primary is the identical endpoint at the identical "
                             "timepoint, and it posts a least-squares mean difference in its "
                             "own `analyses` block -- the same provenance as every value "
                             "already in the pool. Nothing is derived."),
            "why_it_was_absent": ("This review had no executed search until 2026-08-19. Its "
                                  "five trials were the five somebody put on a page."),
        },
        "eligible_poolable_and_NOT_pooled": {
            "_why_shown": ("Each is eligible, has posted LDL results, and is absent from the "
                           "pool for a stated reason with its own numbers beside it, so the "
                           "cost of the refusal is inspectable rather than asserted."),
            "reason": ("A DOSE-RANGING TRIAL IS NOT ONE CONTRAST. Each randomised DOSE; "
                       "pooling one arm against placebo means choosing which arm, and no rule "
                       "in this review chooses it. THE CHOICE WOULD BE OURS AND IT WOULD LOOK "
                       "LIKE THE TRIAL'S."),
            "trials": DOSE_RANGING,
        },
        "estimator_note": (
            "REML with an inverse-variance random-effects model, unchanged from the published "
            "pool so that the two are comparable on one estimator; Paule-Mandel and a floored "
            "Knapp-Hartung interval are carried beside it. Standard errors are DERIVED from "
            "each printed 95 per cent interval and are labelled so -- the point estimates and "
            "intervals themselves are read."),
        "and_what_did_NOT_move": (
            "The answer. Adding a sixth trial and 370 participants moves the pooled mean "
            "difference by less than half a percentage point. THAT IS THE FINDING AND IT IS "
            "NOT A NULL RESULT: a review whose evidence base was never checked turned out to "
            "have the right answer, and nothing about the way it was built could have told "
            "anyone that. The check is what distinguishes a correct estimate from a lucky one."),
    }
    with io.open(DEST, "w", encoding="utf-8") as fh:
        fh.write(json.dumps(out, indent=1))
    print("\nwrote %s" % DEST)
    return 0


def selftest():
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    fails = []

    def check(name, got, want, tol=1e-3):
        ok = abs(got - want) <= tol if isinstance(want, float) else got == want
        print("  %-58s %s  %s" % (name, "ok" if ok else "FAIL", got))
        if not ok:
            fails.append(name)

    # The published pool must REPRODUCE from the five stored rows. If it does not, either the
    # stored value or this arithmetic is wrong, and the re-pool would be built on sand.
    old = pool(INCUMBENT, "x")
    check("the published MD -55.4593 reproduces from its own five rows",
          old["REML"]["md"], -55.4593, 0.02)
    check("...and its published I2 of 65.1%", old["i2_pct"], 65.1, 0.6)
    check("...and its published tau2 of 9.3148", old["REML"]["tau2"], 9.3148, 0.15)

    # SPIRE-FH's interval must imply a standard error consistent with its posted SEM of 2.54.
    check("SPIRE-FH's printed CI implies its posted standard error 2.54",
          se_from_ci(-59.5, -49.5), 2.551, 0.02)

    # And the recovered trial must actually MOVE something, or adding it proves nothing.
    new = pool(INCUMBENT + RECOVERED, "y")
    check("k rises 5 -> 6", new["k"], 6)
    check("n rises by SPIRE-FH's 370",
          new["n_participants"] - old["n_participants"], 370)

    print("\n%s" % ("ALL KNOWN ANSWERS HELD" if not fails else "FAILED: %s" % fails))
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(selftest() if "--selftest" in sys.argv else main())
