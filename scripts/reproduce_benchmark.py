#!/usr/bin/env python
"""Reproduce a published meta-analysis benchmark FROM THE REGISTRY, and fail when
we stop reproducing it. This is the harness form of a measurement that was, until
now, a sentence someone typed: "all-cause death crude RR 0.849 on k=10, per-trial
counts exact against published." If every transcript were deleted, this script
still produces that number -- and exits non-zero the day it no longer does.

WHAT IT DOES, for one outcome (default all_cause_death):
  * reads a benchmark file (benchmarks/*.json) -- the FIXED, pre-registered target;
  * for each of the benchmark's trials it can resolve to a registration, extracts
    the outcome from AACT;
  * computes the crude risk ratio, prints its denominator and, trial by trial,
    which it could and could not populate and why;
  * checks per-trial anchor counts against published values (extraction validity);
  * asserts the pooled crude RR is within a stated tolerance of the benchmark's
    own recorded crude; exits 1 when it is not.

DEATH, EXTRACTED HONESTLY (three rules learned the hard way, each encoded here):
  1. The all-cause-death count is the AE-module "deaths" total (reported_event_totals,
     event_type='deaths'), denominator = that module's at-risk. Many big CVOTs leave
     it blank and carry death only in a titled mortality OUTCOME.
  2. HEART-FID cross-check: where BOTH the AE-module death and the trial's own titled
     all-cause-mortality outcome exist and DISAGREE, the trial is REFUSED, not picked.
     The AE-module window and the titled-outcome window are not the same quantity.
  3. The titled mortality count is read from the SPECIFIC "all-cause death" outcome by
     TITLE, never by summing every outcome whose title contains a mortality word --
     that summed a composite into PIONEER-6's death and produced a phantom 92/134.

NOT_RUN, never a false zero: if the AACT snapshot is unreachable, or the benchmark's
trials cannot be resolved to registrations, the script says NOT_RUN and exits 0. An
absent source is not a reproduction failure.
"""
from __future__ import annotations
import csv, json, os, sys, io
from collections import defaultdict

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

GLP1 = ("semaglutide", "liraglutide", "dulaglutide", "exenatide", "lixisenatide",
        "albiglutide", "efpeglenatide", "tirzepatide")
CTRL = ("placebo", "control", "comparator", "standard", "sham", "usual care", "matching")
MORT_TITLE = ("all-cause mortality", "all cause mortality", "all-cause death",
              "all cause death", "death from any cause", "deaths from any cause")

# Trial -> NCT, per benchmark. VERIFIED BY TITLE against the snapshot (the control that
# built the topic). Where a trial could not be resolved to the RIGHT registration it is
# left None WITH A REASON rather than guessed -- three Galli trials resolved by name to an
# fMRI study, an insulin trial and a bone substudy, and a wrong NCT is worse than an absent
# one (it pools the wrong trial's deaths). Extend per benchmark; unknown -> NOT_RUN.
BENCHMARK_NCTS = {
    "galli-2025-glp1-jacc": {
        "ELIXA": "NCT01147250", "LEADER": "NCT01179048", "FIGHT": "NCT01800968",
        "SUSTAIN-6": "NCT01720446", "LIVE-Jorsal": "NCT01472640", "EXSCEL": "NCT01144338",
        "HARMONY OUTCOMES": "NCT02465515", "PIONEER-6": "NCT02692716",
        "REWIND": "NCT01394952", "AMPLITUDE-O": "NCT03496298", "STEP-HFpEF": "NCT04788511",
        "SELECT": "NCT03574597", "STEP-HFpEF DM": "NCT04916470", "FLOW": "NCT03819153",
        "GRADE": "NCT01794143", "SUMMIT": "NCT04847557", "SOUL": "NCT03914326",
        # Deliberately unresolved -- name-match hit the wrong trial; not guessed:
        "Kyhl et al.": None, "Chen et al.": None, "Zhang et al.": None,
        "STRIDE": None,   # not in the 2026-08-30 snapshot
    },
}
# Published anchor counts (trt_deaths, ctrl_deaths) -- extraction-validity check. These
# are the trials whose all-cause death is known from the paper; if AACT stops returning
# them the extraction has broken and the script must fail even if the pool still averages out.
ANCHORS = {
    "galli-2025-glp1-jacc": {
        "NCT02692716": (23, 45),    # PIONEER-6, published HR 0.51
        "NCT01144338": (507, 584),  # EXSCEL
        "NCT01394952": (536, 592),  # REWIND
    },
}
TOL = 0.05  # allowed absolute drift of our crude RR from the benchmark's own crude


def resolve_aact():
    """The snapshot dir, or None. Honours AACT_ROOT / AACT_DIR (as the corpus does),
    then a few candidate roots. None means NOT_RUN, never a zero."""
    for env in (os.environ.get("AACT_ROOT"), os.environ.get("AACT_DIR")):
        if env and os.path.isdir(env) and os.path.isfile(os.path.join(env, "studies.txt")):
            return env
    cands = []
    for base in ("F:/AACT-storage/AACT", "C:/AACT", "D:/AACT", "F:/AACT",
                 os.path.join(os.path.expanduser("~"), "AACT")):
        if os.path.isdir(base):
            if os.path.isfile(os.path.join(base, "studies.txt")):
                cands.append(base)
            else:  # dated snapshot subdirs; take the newest
                subs = [os.path.join(base, d) for d in os.listdir(base)
                        if os.path.isfile(os.path.join(base, d, "studies.txt"))]
                cands.extend(sorted(subs))
    return cands[-1] if cands else None


def load_maps(aact, ncts):
    """Filtered AACT reads for just the benchmark's NCTs."""
    want = {n for n in ncts if n}
    intv = defaultdict(list)
    rgroup = defaultdict(dict)      # nct -> {group_code: title}
    totals = defaultdict(list)      # nct -> [(event_type, code, affected, at_risk)]
    om = defaultdict(list)          # nct -> [(title, group_code, param_value)]
    def rows(name):
        with open(os.path.join(aact, name), encoding="utf-8", errors="replace") as f:
            for r in csv.DictReader(f, delimiter="|"):
                if (r.get("nct_id") or "").strip().upper() in want:
                    yield r
    for r in rows("interventions.txt"):
        intv[r["nct_id"].upper()].append((r.get("name") or "").strip().lower())
    for r in rows("result_groups.txt"):
        rgroup[r["nct_id"].upper()][r.get("ctgov_group_code")] = (r.get("title") or "")
    for r in rows("reported_event_totals.txt"):
        totals[r["nct_id"].upper()].append(
            (r.get("event_type"), r.get("ctgov_group_code"),
             r.get("subjects_affected"), r.get("subjects_at_risk")))
    for r in rows("outcome_measurements.txt"):
        # BROAD capture (any death/mortality outcome); the SPECIFIC all-cause, non-composite
        # one is selected per-trial in extract_death. Selection there, never summing here.
        t = (r.get("title") or "").lower()
        if r.get("param_type") == "COUNT_OF_PARTICIPANTS" and ("death" in t or "mortalit" in t):
            om[r["nct_id"].upper()].append(
                (r.get("title") or "", r.get("ctgov_group_code"), r.get("param_value")))
    return intv, rgroup, totals, om


def _num(x):
    try:
        return int(x)
    except (TypeError, ValueError):
        return None


def extract_death(nct, rgroup, totals, om):
    """(trt, ctrl, note) where trt/ctrl are (deaths, n) or None. Applies the HEART-FID
    cross-check and returns a refusal note when AE and titled disagree."""
    def side(code):
        t = (rgroup.get(nct, {}).get(code) or "").lower()
        if any(d in t for d in GLP1):
            return "TRT"
        if any(c in t for c in CTRL):
            return "CTRL"
        return "?"
    # Pair each arm's deaths with THAT arm's at-risk, then sum across a side's arms. A two-dose
    # trial (AMPLITUDE-O: 65 deaths across both efpeglenatide arms) must be divided by both
    # arms' N (~2718), not one -- taking max() here halved the denominator, inflated the death
    # rate, and pushed the pooled crude toward the benchmark by coincidence (a false pass the
    # anchors could not catch). Dedupe serious/other, which report the same arm N.
    deaths_by_group, n_by_group = {}, {}
    for et, code, aff, risk in totals.get(nct, []):
        if et == "deaths":
            a = _num(aff)
            if a is not None:
                deaths_by_group[code] = a
        elif et in ("serious", "other"):
            rk = _num(risk)
            if rk:
                n_by_group[code] = max(n_by_group.get(code, 0), rk)
    ae, at = defaultdict(int), defaultdict(int)
    ae_seen = bool(deaths_by_group)
    for code, d in deaths_by_group.items():
        ae[side(code)] += d
        if code in n_by_group:
            at[side(code)] += n_by_group[code]
    # TITLED MORTALITY, WITHOUT SUMMING ACROSS OUTCOMES. Group by title, take ONE all-cause,
    # non-composite outcome. Summing a composite (whose title also carries a death word) into
    # the all-cause row is what gave PIONEER-6 a phantom 92/134 instead of 23/45.
    by_title = defaultdict(lambda: defaultdict(int))
    for title, code, val in om.get(nct, []):
        v = _num(val)
        if v is not None:
            by_title[title][side(code)] += v

    def _composite(t):
        t = t.lower()
        return any(w in t for w in ("composite", "mace", "nonfatal", "non-fatal",
                                    "myocardial", "stroke", "hospitali", " mi ",
                                    "cardiovascular death"))
    cand = {t: d for t, d in by_title.items()
            if ("all-cause" in t.lower() or "all cause" in t.lower()
                or "any cause" in t.lower() or "any-cause" in t.lower())}
    cand = {t: d for t, d in cand.items() if not _composite(t)} or \
           {t: d for t, d in by_title.items() if not _composite(t)}
    ttl = defaultdict(int); ttl_seen = False
    if cand:
        best = min(cand.items(),
                   key=lambda kv: sum(v for v in kv[1].values()))  # pure all-cause < a bundle
        ttl = defaultdict(int, best[1]); ttl_seen = True
    have_ae = ae_seen and "TRT" in ae and "CTRL" in ae
    have_ttl = ttl_seen and "TRT" in ttl and "CTRL" in ttl
    if have_ae and have_ttl:
        dis = (abs(ae["TRT"] - ttl["TRT"]) > max(2, 0.1 * ttl["TRT"]) or
               abs(ae["CTRL"] - ttl["CTRL"]) > max(2, 0.1 * ttl["CTRL"]))
        if dis:
            return None, None, ("REFUSED (HEART-FID): AE-module %d/%d vs titled %d/%d disagree"
                                % (ae["TRT"], ae["CTRL"], ttl["TRT"], ttl["CTRL"]))
    if have_ae and "TRT" in at and "CTRL" in at:
        return (ae["TRT"], at["TRT"]), (ae["CTRL"], at["CTRL"]), "AE-module"
    if have_ttl and "TRT" in at and "CTRL" in at:
        return (ttl["TRT"], at["TRT"]), (ttl["CTRL"], at["CTRL"]), "titled-outcome"
    if have_ttl and not ("TRT" in at and "CTRL" in at):
        return None, None, "titled death present but no arm denominator in AE totals"
    return None, None, ("no AE-module death and no titled mortality outcome"
                        if not (ae_seen or ttl_seen) else "death present but arms unresolved")


def main(argv=None):
    # UTF-8 output, rebound INSIDE the function: a module-scope stdout rebind trips the
    # recurring-traps lint and breaks pytest capture / re-import (learned the hard way).
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace",
                                  line_buffering=True)
    argv = list(sys.argv[1:] if argv is None else argv)
    outcome = "all_cause_death"
    if "--outcome" in argv:
        i = argv.index("--outcome"); outcome = argv[i + 1]; del argv[i:i + 2]
    if not argv:
        print("usage: reproduce_benchmark.py <benchmark.json> [--outcome all_cause_death]")
        return 2
    bpath = argv[0]
    bench = json.load(open(bpath, encoding="utf-8"))
    bid = bench.get("benchmark_id", "")
    print("BENCHMARK: %s  (%s)" % (bid, os.path.basename(bpath)))
    print("OUTCOME  : %s\n" % outcome)

    ncts = BENCHMARK_NCTS.get(bid)
    if ncts is None:
        print("NOT_RUN: no trial->registration map is wired for this benchmark. A name "
              "match is not an identity (three Galli trials name-match the wrong study), so "
              "this reports NOT_RUN rather than guessing.")
        return 0
    aact = resolve_aact()
    if not aact:
        print("NOT_RUN: no AACT snapshot found (set AACT_ROOT or AACT_DIR). An absent "
              "snapshot is NOT a reproduction of zero.")
        return 0
    print("AACT snapshot: %s" % aact)

    # the benchmark's own recorded crude, from its per-outcome event counts
    per = {}
    for blk in bench.values():
        if isinstance(blk, dict) and isinstance(blk.get("per_outcome"), list):
            for o in blk["per_outcome"]:
                per[o.get("outcome")] = o
    tgt = per.get(outcome)
    their_crude = None
    if tgt and all(tgt.get(k) for k in ("events_glp1", "n_glp1", "events_ctrl", "n_ctrl")):
        their_crude = (tgt["events_glp1"] / tgt["n_glp1"]) / (tgt["events_ctrl"] / tgt["n_ctrl"])

    intv, rgroup, totals, om = load_maps(aact, list(ncts.values()))
    anchors = ANCHORS.get(bid, {})

    print("\nPER-TRIAL EXTRACTION")
    dt = nt = dc = nc = 0
    used = []
    unresolved, refused, nodata = [], [], []
    for name, nct in sorted(ncts.items()):
        if not nct:
            unresolved.append(name); print("  %-18s -- NCT not resolved for this benchmark" % name); continue
        trt, ctrl, note = extract_death(nct, rgroup, totals, om)
        if trt and ctrl:
            dt += trt[0]; nt += trt[1]; dc += ctrl[0]; nc += ctrl[1]; used.append((name, nct, trt, ctrl))
            flag = ""
            exp = anchors.get(nct)   # anchors is a dict; .get avoids the substring-lint heuristic
            if exp is not None:
                ok = (trt[0], ctrl[0]) == exp
                flag = "  ANCHOR %s expected %s" % ("OK" if ok else "*** MISMATCH ***", exp)
            print("  %-18s %s  trt %d/%d  ctrl %d/%d  [%s]%s"
                  % (name, nct, trt[0], trt[1], ctrl[0], ctrl[1], note, flag))
        else:
            (refused if note.startswith("REFUSED") else nodata).append((name, note))
            print("  %-18s %s  -- %s" % (name, nct, note))

    print("\nSUMMARY")
    k = len(used)
    crude = (dt / nt) / (dc / nc) if (nt and nc and dc) else None
    print("  populated : %d of %d resolvable trials" % (k, len([n for n in ncts.values() if n])))
    print("  unresolved: %d   refused (cross-check): %d   no usable data: %d"
          % (len(unresolved), len(refused), len(nodata)))
    print("  pooled crude: trt %d/%d vs ctrl %d/%d" % (dt, nt, dc, nc))
    print("  OUR crude RR : %s" % ("%.4f" % crude if crude else "n/a"))
    if their_crude:
        print("  THEIR crude  : %.4f  (from benchmark events %d/%d vs %d/%d, k=%s)"
              % (their_crude, tgt["events_glp1"], tgt["n_glp1"], tgt["events_ctrl"],
                 tgt["n_ctrl"], tgt.get("k")))
    to = [o for o in (bench.get("their_outcomes") or []) if o.get("outcome") == outcome]
    if to:
        print("  THEIR pooled : %s (IRR)" % to[0].get("irr"))

    # ---- verdict ----
    fails = []
    for name, nct, trt, ctrl in used:
        exp = anchors.get(nct)
        if exp is not None and (trt[0], ctrl[0]) != exp:
            fails.append("anchor %s (%s): got %d/%d, published %s"
                         % (name, nct, trt[0], ctrl[0], exp))
    _used_ncts = {u[1] for u in used}
    missing_anchor = [nct for nct in anchors if nct not in _used_ncts]
    for nct in missing_anchor:
        fails.append("anchor %s not populated at all -- extraction no longer reaches it" % nct)
    if their_crude is not None and crude is not None and abs(crude - their_crude) > TOL:
        fails.append("crude RR %.4f drifted > %.2f from the benchmark crude %.4f"
                     % (crude, TOL, their_crude))
    if crude is None:
        fails.append("no crude RR could be computed -- nothing populated")

    print()
    if fails:
        print("REPRODUCTION FAILED:")
        for f in fails:
            print("   - %s" % f)
        return 1
    print("REPRODUCTION HELD: anchors exact, crude RR %.4f within %.2f of the benchmark's "
          "%.4f. (k=%d here vs their k=%s -- the gap is the trials that carry death only "
          "outside the AE module; reported above, not hidden.)"
          % (crude, TOL, their_crude if their_crude else float('nan'), k, tgt.get("k") if tgt else "?"))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
