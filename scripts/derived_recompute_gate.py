"""DERIVED RECOMPUTE GATE -- a derived value must follow from the CURRENT inputs.

THE DEFECT. `CODE-FIXED, CORPUS-STALE` is the most common defect this project
has. A synthesis is corrected; the blocks derived from it are not; and the page
goes on serving the old number, internally consistent with a snapshot of an
operand that no longer exists.

    ARNI. `count_panels.rd.point` is -0.023053, recomputed at build time by
    metafor from the per-arm counts. Beside it, `count_panels.nnt` carries its
    OWN copy of that operand -- `pooled_rd: -0.044191` -- and an NNT of 22.629,
    which is exactly 1/0.044191. The NNT is perfectly consistent with the stale
    copy, which is why every internal-consistency check passes and the page
    ships the old number. Recomputed from the live RD the NNT is 43.4.

    Bococizumab. The outcome is k=6, pooled MD -55.24. Its leave-one-out block
    holds FIVE analyses, each recording k=4 -- the shape of a k=5 synthesis --
    and its estimator-comparison panel reports REML at -55.4593 with tau-squared
    9.3148, which is not the headline the same object registers.

WHAT THIS GATE DOES, IN THREE RULES

    LOO_ARITY
        A leave-one-out block over k trials has exactly k analyses and each
        records k-1. Pure arithmetic on the object's own numbers; no topic
        knowledge, no external source.

    HEADLINE_ESTIMATOR_ROW
        An estimator-comparison panel contains a row for the estimator the
        outcome actually registered. That row must reproduce the outcome's own
        headline point estimate. When it does not, the panel was computed from a
        different synthesis from the one on the page.

    OPERAND_COPY
        A derived block that stores its own copy of an operand must agree with
        the authoritative value of that operand, AND the derived value must be
        recomputable from the AUTHORITATIVE operand rather than from the copy.
        Both halves are needed: checking only the formula passes a block that is
        internally perfect and externally superseded, which is precisely how the
        ARNI NNT survived.

    A rule whose inputs are absent returns NOT_APPLICABLE and is counted
    separately. A rule whose inputs are present but unusable returns
    UNDETERMINABLE. Neither is a pass.

WHAT IT CANNOT SEE -- printed with every verdict

    * Any derivation not in DERIVATIONS below. The table is declared, not
      inferred, so a new derived block is invisible until somebody adds it. The
      coverage line says how many objects each rule could apply to, so a rule
      that applies to nothing reads NOT OBSERVED rather than SAFE.
    * A stale value that is stale in EVERY surface at once. This gate compares
      surfaces; if the whole object was rebuilt wrongly it agrees with itself.
    * Whether the authoritative operand is itself correct. It is taken as
      authoritative because the object names it so, not because it was verified.
    * Anything on the page that no object field corresponds to.

USAGE

    python scripts/derived_recompute_gate.py --selftest
    python scripts/derived_recompute_gate.py ssot/<app>/<app>.json ...
    python scripts/derived_recompute_gate.py --diff origin/main   # DEFAULT SCOPE
    python scripts/derived_recompute_gate.py --all

Exit code: +1 if anything FAILED, +2 if anything could not be judged.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)
if HERE not in sys.path:
    sys.path.insert(0, HERE)


# --------------------------------------------------------------------------
# path access

def dig(obj, path):
    """Fetch a dotted path. Returns (found, value) -- never a bare None, because
    a field that is absent and a field whose value is null are different facts
    and this gate has to tell them apart."""
    cur = obj
    for part in path.split("."):
        if isinstance(cur, dict) and part in cur:
            cur = cur[part]
        else:
            return False, None
    return True, cur


def is_num(v):
    return isinstance(v, (int, float)) and not isinstance(v, bool)


# --------------------------------------------------------------------------
# the declared derivations
#
# Each entry says: the derived field, the operand it is derived FROM, the
# formula, and the copy of the operand the derived block keeps beside itself.
# The copy is what makes the drift visible; the formula is what makes the
# consequence measurable.

def _reciprocal(x):
    return None if not x else 1.0 / abs(x)


DERIVATIONS = [
    {"name": "NNT from the pooled risk difference",
     "derived": "count_panels.nnt.nnt",
     "operand": "count_panels.rd.point",
     "operand_copy": "count_panels.nnt.pooled_rd",
     "formula": "NNT = 1 / |RD|",
     "fn": _reciprocal,
     "rel_tol": 0.005},
    {"name": "the lower NNT bound from the risk-difference interval",
     "derived": "count_panels.nnt.nnt_low",
     "operand": "count_panels.rd.ci_high",
     "operand_copy": "count_panels.nnt.rd_ci_high",
     "formula": "NNT_low = 1 / |RD upper bound|",
     "fn": _reciprocal,
     "rel_tol": 0.005},
    {"name": "the upper NNT bound from the risk-difference interval",
     "derived": "count_panels.nnt.nnt_high",
     "operand": "count_panels.rd.ci_low",
     "operand_copy": "count_panels.nnt.rd_ci_low",
     "formula": "NNT_high = 1 / |RD lower bound|",
     "fn": _reciprocal,
     "rel_tol": 0.005},
]

# Where a leave-one-out block and an estimator panel live inside an outcome.
LOO_PATHS = ("sensitivity.analyses", "sensitivity.leave_one_out")
ESTIMATOR_PATHS = ("sensitivity.between_study_variance_method_comparison.methods",)

PASS, FAIL, UNDET, NA = "PASS", "FAIL", "UNDETERMINABLE", "NOT_APPLICABLE"


def as_list(value):
    """A list, or [] for anything that is not one.

    THE CORPUS DOES NOT KEEP THE SHAPE ITS SCHEMA IMPLIES. Some objects store
    `screening.excluded` as an INTEGER -- a count rather than a collection --
    and iterating it killed a corpus sweep on the first such object, so
    everything after it was never examined at all. A crash mid-sweep is worse
    than a wrong verdict, because the wrong verdict is visible and the
    unexamined remainder is not.
    """
    return value if isinstance(value, list) else []


class Finding(object):
    def __init__(self, rule, outcome, state, detail, expected=None, found=None):
        self.rule, self.outcome, self.state = rule, outcome, state
        self.detail, self.expected, self.found = detail, expected, found

    def as_dict(self):
        return {"rule": self.rule, "outcome": self.outcome, "state": self.state,
                "detail": self.detail, "expected": self.expected,
                "found": self.found}


# --------------------------------------------------------------------------
# the rules

# A LEAVE-ONE-OUT ROW, NOT MERELY A SENSITIVITY ROW. `sensitivity.analyses` is a
# general list: tigecycline-ciai holds eight analyses of which exactly three are
# leave-one-out, and counting all eight against k=3 accused a correct block.
# Three more objects hold an EMPTY analyses list, which means no leave-one-out was
# performed, not that a stale one is present. Both were false accusations by this
# gate on its own first corpus run; both are kept as controls below.
_LOO_ROW = re.compile(r"(?i)leave[- ]?(one[- ]?)?out|omitting|removing\b|"
                      r"\bomitted\b|without (the )?(study|trial)")


def _loo_rows(rows):
    out = []
    for r in rows:
        if not isinstance(r, dict):
            continue
        if r.get("omitted"):
            out.append(r)
            continue
        blob = " ".join(str(r.get(f, "")) for f in
                        ("id", "changed", "label", "analysis", "name"))
        if _LOO_ROW.search(blob):
            out.append(r)
    return out


def rule_loo_arity(outcome_id, outcome):
    k = outcome.get("k")
    rows = None
    for p in LOO_PATHS:
        found, v = dig(outcome, p)
        if found and isinstance(v, list):
            rows, used = v, p
            break
    if rows is None:
        return [Finding("LOO_ARITY", outcome_id, NA,
                        "no leave-one-out block on this outcome")]
    all_rows, rows = rows, _loo_rows(rows)
    if not rows:
        return [Finding("LOO_ARITY", outcome_id, NA,
                        "%s holds %d analysis/analyses and none of them is a "
                        "leave-one-out row, so no leave-one-out was performed "
                        "here" % (used, len(all_rows)))]
    if is_num(k) and k < 2:
        return [Finding("LOO_ARITY", outcome_id, NA,
                        "leave-one-out is not defined at k=%s" % k)]
    if not is_num(k):
        return [Finding("LOO_ARITY", outcome_id, UNDET,
                        "a leave-one-out block is present but the outcome "
                        "records no k to check it against")]
    out = []
    if len(rows) != k:
        out.append(Finding(
            "LOO_ARITY", outcome_id, FAIL,
            "%s holds %d analyses for a synthesis of %d trials. Leaving one out "
            "of %d gives %d analyses, so this block was computed from a "
            "different synthesis." % (used, len(rows), k, k, k),
            expected=k, found=len(rows)))
    bad = [(i, r.get("k")) for i, r in enumerate(rows)
           if isinstance(r, dict) and is_num(r.get("k")) and r["k"] != k - 1]
    if bad:
        out.append(Finding(
            "LOO_ARITY", outcome_id, FAIL,
            "%d of %d leave-one-out rows record k=%s; omitting one trial from %d "
            "leaves %d." % (len(bad), len(rows),
                            "/".join(str(b[1]) for b in bad[:4]), k, k - 1),
            expected=k - 1, found=[b[1] for b in bad]))
    missing = [i for i, r in enumerate(rows)
               if not isinstance(r, dict) or not is_num(r.get("k"))]
    if missing and not out:
        out.append(Finding("LOO_ARITY", outcome_id, UNDET,
                           "%d leave-one-out row(s) record no k" % len(missing)))
    if not out:
        out.append(Finding("LOO_ARITY", outcome_id, PASS,
                           "%d analyses, each at k=%d, for a synthesis of %d"
                           % (len(rows), k - 1, k)))
    return out


def rule_headline_estimator_row(outcome_id, outcome):
    rows = None
    for p in ESTIMATOR_PATHS:
        found, v = dig(outcome, p)
        if found and isinstance(v, list):
            rows = v
            break
    if rows is None:
        return [Finding("HEADLINE_ESTIMATOR_ROW", outcome_id, NA,
                        "no estimator-comparison panel on this outcome")]
    est = outcome.get("estimator_used") or outcome.get("estimator")
    found, point = dig(outcome, "pooled.point")
    if not est or not found or not is_num(point):
        return [Finding("HEADLINE_ESTIMATOR_ROW", outcome_id, UNDET,
                        "an estimator panel is present but the outcome does not "
                        "name both a registered estimator (%r) and a headline "
                        "point (%r)" % (est, point if found else "absent"))]
    # The registered estimator is written as a PHRASE -- "REML random-effects,
    # inverse-variance" -- while the panel labels rows with the bare token
    # "REML". An exact comparison finds nothing and reports the panel
    # unauditable, which is a statement about the matcher dressed up as a
    # statement about the object. Match the row label as a whole word inside the
    # registered phrase instead, and refuse only when that is ambiguous.
    labels = sorted({str(r.get("between_study_variance_estimator", "")).strip()
                     for r in rows if isinstance(r, dict)} - {""})
    est_s = str(est)
    hit = [lab for lab in labels
           if lab.upper() == est_s.upper()
           or re.search(r"(?i)\b%s\b" % re.escape(lab), est_s)]
    if len(hit) != 1:
        return [Finding("HEADLINE_ESTIMATOR_ROW", outcome_id, UNDET,
                        "the registered estimator %r matches %d of the panel's "
                        "rows (%s); with none or several there is no row this "
                        "gate may hold to the headline"
                        % (est, len(hit), ", ".join(labels)))]
    est = hit[0]
    matches = [r for r in rows if isinstance(r, dict)
               and str(r.get("between_study_variance_estimator", "")).strip()
               == est]
    # The headline interval method is not always recorded, so agreement on the
    # POINT is what is required: every interval method shares one point estimate.
    pts = [r["point"] for r in matches if is_num(r.get("point"))]
    if not pts:
        return [Finding("HEADLINE_ESTIMATOR_ROW", outcome_id, UNDET,
                        "the %s row(s) carry no numeric point" % est)]
    # tolerance: the headline may be stored at display precision.
    tol = max(abs(point) * 0.002, 0.011)
    off = [p for p in pts if abs(p - point) > tol]
    if off:
        return [Finding(
            "HEADLINE_ESTIMATOR_ROW", outcome_id, FAIL,
            "the %s row of the estimator panel gives %s, while the outcome's "
            "registered headline is %s. The panel and the headline are not the "
            "same synthesis." % (est, ", ".join("%g" % p for p in off), point),
            expected=point, found=off)]
    return [Finding("HEADLINE_ESTIMATOR_ROW", outcome_id, PASS,
                    "the %s row reproduces the headline %g within %g"
                    % (est, point, tol))]


def rule_operand_copy(outcome_id, outcome):
    out = []
    for d in DERIVATIONS:
        f_dv, dv = dig(outcome, d["derived"])
        f_op, op = dig(outcome, d["operand"])
        f_cp, cp = dig(outcome, d["operand_copy"])
        if not f_dv:
            out.append(Finding(d["name"], outcome_id, NA,
                               "%s is not present on this outcome" % d["derived"]))
            continue
        if not is_num(dv):
            out.append(Finding(d["name"], outcome_id, UNDET,
                               "%s is present but not numeric" % d["derived"]))
            continue
        if not f_op or not is_num(op):
            out.append(Finding(
                d["name"], outcome_id, UNDET,
                "%s is shown, but its operand %s is absent from this object, so "
                "there is nothing to recompute it from. A derived value with no "
                "live operand must not be displayed."
                % (d["derived"], d["operand"])))
            continue

        # (a) the copy the derived block keeps beside itself
        if f_cp and is_num(cp) and abs(cp - op) > max(abs(op) * 1e-6, 1e-9):
            out.append(Finding(
                d["name"], outcome_id, FAIL,
                "%s keeps its own copy of the operand as %g, while the "
                "authoritative %s is %g. The derived block is a snapshot of an "
                "operand that no longer exists."
                % (d["operand_copy"], cp, d["operand"], op),
                expected=op, found=cp))

        # (b) recomputation from the AUTHORITATIVE operand, not from the copy
        want = d["fn"](op)
        if want is None:
            out.append(Finding(d["name"], outcome_id, UNDET,
                               "%s is undefined at operand %g"
                               % (d["formula"], op)))
            continue
        if abs(dv - want) > abs(want) * d["rel_tol"]:
            out.append(Finding(
                d["name"], outcome_id, FAIL,
                "%s shows %g. Recomputed from the current %s (%g) by %s it is "
                "%g. The page must decline to show a value it cannot recompute, "
                "not show the old one."
                % (d["derived"], dv, d["operand"], op, d["formula"], want),
                expected=want, found=dv))
        else:
            out.append(Finding(d["name"], outcome_id, PASS,
                               "%s = %g reproduces %s from the live operand"
                               % (d["derived"], dv, d["formula"])))
    return out


RULES = (rule_loo_arity, rule_headline_estimator_row, rule_operand_copy)


# --------------------------------------------------------------------------

def judge_object(path, repo):
    rec = {"object": os.path.relpath(path, repo).replace(os.sep, "/"),
           "state": None, "detail": "", "findings": [], "outcomes": 0}
    try:
        with open(path, "rb") as fh:
            obj = json.loads(fh.read().decode("utf-8", "replace"))
    except Exception as exc:
        rec["state"] = "NO_RECORD"
        rec["detail"] = "object unreadable: %s" % exc
        return rec

    found, by_outcome = dig(obj, "results.by_outcome")
    if not found or not isinstance(by_outcome, dict) or not by_outcome:
        rec["state"] = "NO_RECORD"
        rec["detail"] = "object carries no results.by_outcome"
        return rec

    for oid, outcome in by_outcome.items():
        if not isinstance(outcome, dict):
            continue
        rec["outcomes"] += 1
        for rule in RULES:
            for f in rule(oid, outcome):
                rec["findings"].append(f.as_dict())

    states = {f["state"] for f in rec["findings"]}
    if FAIL in states:
        rec["state"] = FAIL
    elif UNDET in states:
        rec["state"] = UNDET
    elif PASS in states:
        rec["state"] = PASS
    else:
        rec["state"] = NA
        rec["detail"] = "no declared derivation applies to this object"
    return rec


# --------------------------------------------------------------------------
# scope

def diff_objects(base, repo):
    r = subprocess.run(["git", "diff", "--name-only", "%s...HEAD" % base,
                        "--", "ssot/*.json"], cwd=repo, capture_output=True,
                       text=True, encoding="utf-8", errors="replace")
    if r.returncode != 0:
        return None, (r.stderr or "").strip()[:200]
    out = []
    for n in r.stdout.split("\n"):
        n = n.strip()
        p = os.path.join(repo, n.replace("/", os.sep))
        if n and os.path.exists(p) and _is_canonical(n):
            out.append(p)
    return out, None


def _is_canonical(rel):
    parts = rel.split("/")
    return (len(parts) == 3 and parts[0] == "ssot"
            and parts[2] == parts[1] + ".json")


def all_objects(repo):
    root = os.path.join(repo, "ssot")
    if not os.path.isdir(root):
        return []
    out = []
    for name in sorted(os.listdir(root)):
        p = os.path.join(root, name, name + ".json")
        if os.path.exists(p):
            out.append(p)
    return out


# --------------------------------------------------------------------------

def report(records, n_in_scope, scope_note, wall, cpu, not_reached):
    fails = [r for r in records if r["state"] == FAIL]
    undet = [r for r in records if r["state"] in (UNDET, "NO_RECORD", "TIMED_OUT")]
    passes = [r for r in records if r["state"] == PASS]
    na = [r for r in records if r["state"] == NA]

    for r in fails:
        print("\nFAIL  %s" % r["object"])
        for f in [x for x in r["findings"] if x["state"] == FAIL]:
            print("      [%s] outcome %s" % (f["rule"], f["outcome"]))
            print("      %s" % f["detail"])
    for r in undet:
        print("\n%-14s %s -- %s" % (r["state"], r["object"], r["detail"][:120]))
        for f in [x for x in r["findings"] if x["state"] == UNDET][:4]:
            print("      [%s] %s" % (f["rule"], f["detail"]))

    # per-rule reach, so a rule that applied to nothing cannot read as clean
    reach = {}
    for r in records:
        for f in r["findings"]:
            d = reach.setdefault(f["rule"], {PASS: 0, FAIL: 0, UNDET: 0, NA: 0})
            d[f["state"]] += 1

    print("\n" + "-" * 74)
    print("COVERAGE   %d of %d %s" % (len(records), n_in_scope, scope_note))
    print("           %d PASS, %d FAIL, %d could not be judged, %d had no "
          "declared derivation" % (len(passes), len(fails), len(undet), len(na)))
    print("PER RULE   (a rule that judged nothing reads NOT OBSERVED, not SAFE)")
    for rule in sorted(reach):
        d = reach[rule]
        judged = d[PASS] + d[FAIL] + d[UNDET]
        print("           %-52s %s"
              % (rule[:52],
                 "NOT OBSERVED -- 0 judged, %d not applicable" % d[NA]
                 if judged == 0 else
                 "%d judged: %d pass, %d fail, %d undeterminable (%d n/a)"
                 % (judged, d[PASS], d[FAIL], d[UNDET], d[NA])))
    if not_reached:
        print("           NOT REACHED: %d object(s)" % len(not_reached))
    print("BLIND TO   derivations absent from the declared table; a value stale "
          "in every surface")
    print("           at once; whether the authoritative operand is itself "
          "right.")
    print("COST       %.2fs wall, %.2fs CPU" % (wall, cpu))
    if not records:
        print("VERDICT    NOT OBSERVED -- nothing in scope carried an object to "
              "read.")
    return (1 if fails else 0) + (2 if (undet or not_reached) else 0)


# --------------------------------------------------------------------------
# self-test

def _obj(k, loo_rows, loo_k, est_point, rd_point, nnt_copy, nnt_value,
         extra_rows=()):
    return {"results": {"by_outcome": {"o1": {
        "k": k,
        "estimator": "REML",
        "pooled": {"point": -55.24},
        "sensitivity": {
            "analyses": [{"omitted": "t%d" % i, "k": loo_k, "point": -55.0}
                         for i in range(loo_rows)] + list(extra_rows),
            "between_study_variance_method_comparison": {"methods": [
                {"between_study_variance_estimator": "REML",
                 "interval_method": "Wald", "point": est_point, "tau2": 9.3},
                {"between_study_variance_estimator": "DL",
                 "interval_method": "Wald", "point": -55.43, "tau2": 8.0}]}},
        "count_panels": {
            "rd": {"measure": "RD", "point": rd_point,
                   "ci_low": -0.0628555, "ci_high": 0.0167496},
            "nnt": {"pooled_rd": nnt_copy, "rd_ci_low": -0.0628555,
                    "rd_ci_high": 0.0167496, "nnt": nnt_value,
                    "nnt_low": 1 / 0.0167496, "nnt_high": 1 / 0.0628555}},
    }}}}


def selftest():
    import shutil
    import tempfile

    root = tempfile.mkdtemp(prefix="derivgate_")
    try:
        def write(name, obj):
            d = os.path.join(root, "ssot", name)
            os.makedirs(d, exist_ok=True)
            p = os.path.join(d, name + ".json")
            with open(p, "w", encoding="utf-8") as fh:
                json.dump(obj, fh)
            return p

        # The plant reproduces both real defects at once:
        #   five leave-one-out rows at k=4 for a k=6 synthesis (bococizumab),
        #   an NNT of 22.629 from a superseded RD copy (ARNI).
        planted = write("__control_stale",
                        _obj(k=6, loo_rows=5, loo_k=4, est_point=-55.4593,
                             rd_point=-0.02305292779417, nnt_copy=-0.044191,
                             nnt_value=22.628984))
        fixed = write("__control_fixed",
                      _obj(k=6, loo_rows=6, loo_k=5, est_point=-55.24,
                           rd_point=-0.02305292779417,
                           nnt_copy=-0.02305292779417,
                           nnt_value=1 / 0.02305292779417))

        ok = True
        print("=== the plant must fire before the fix is allowed to pass ===")
        r = judge_object(planted, root)
        fired = {f["rule"] for f in r["findings"] if f["state"] == FAIL}
        want = {"LOO_ARITY", "HEADLINE_ESTIMATOR_ROW",
                "NNT from the pooled risk difference"}
        good = r["state"] == FAIL and want <= fired
        ok = ok and good
        print("  %-14s %-8s planted stale object: rules that fired = %s"
              % (r["state"], "correct" if good else "WRONG", sorted(fired)))

        r = judge_object(fixed, root)
        good = r["state"] == PASS
        ok = ok and good
        print("  %-14s %-8s the same object with every derivation refreshed"
              % (r["state"], "correct" if good else "WRONG"))

        # THE TWO FALSE ACCUSATIONS THIS GATE MADE ON ITS OWN FIRST CORPUS RUN,
        # kept permanently as negative controls.
        r = judge_object(write("__control_mixed_sensitivity",
                               _obj(k=3, loo_rows=3, loo_k=2, est_point=-55.24,
                                    rd_point=-0.023, nnt_copy=-0.023,
                                    nnt_value=1 / 0.023,
                                    extra_rows=[
                                        {"id": "odds-ratio",
                                         "changed": "the summary statistic"},
                                        {"id": "fixed-effect",
                                         "changed": "the model"}])), root)
        good = r["state"] == PASS
        ok = ok and good
        print("  %-14s %-8s a sensitivity list holding 5 analyses of which 3 "
              "are leave-one-out, at k=3"
              % (r["state"], "correct" if good else "WRONG"))

        r = judge_object(write("__control_empty_sensitivity",
                               _obj(k=3, loo_rows=0, loo_k=2, est_point=-55.24,
                                    rd_point=-0.023, nnt_copy=-0.023,
                                    nnt_value=1 / 0.023)), root)
        rules = {f["rule"]: f["state"] for f in r["findings"]}
        good = rules.get("LOO_ARITY") == NA
        ok = ok and good
        print("  %-14s %-8s an EMPTY sensitivity list means no leave-one-out was "
              "performed, not a stale one"
              % (rules.get("LOO_ARITY"), "correct" if good else "WRONG"))

        # Third state: an operand that is absent must not read as a pass.
        noop = _obj(k=6, loo_rows=6, loo_k=5, est_point=-55.24,
                    rd_point=-0.023, nnt_copy=-0.023, nnt_value=1 / 0.023)
        del noop["results"]["by_outcome"]["o1"]["count_panels"]["rd"]["point"]
        r = judge_object(write("__control_nooperand", noop), root)
        good = r["state"] == UNDET
        ok = ok and good
        print("  %-14s %-8s an NNT displayed with no live RD to recompute it from"
              % (r["state"], "correct" if good else "WRONG"))

        # An object with no derived blocks at all is NOT_APPLICABLE, not a pass.
        r = judge_object(write("__control_bare",
                               {"results": {"by_outcome": {"o1": {"k": 3}}}}),
                         root)
        good = r["state"] == NA
        ok = ok and good
        print("  %-14s %-8s an object carrying no declared derivation"
              % (r["state"], "correct" if good else "WRONG"))

        # An internally perfect but externally superseded block MUST fail: this
        # is the exact shape that let the ARNI NNT survive every prior check.
        sneaky = _obj(k=6, loo_rows=6, loo_k=5, est_point=-55.24,
                      rd_point=-0.02305292779417, nnt_copy=-0.044191,
                      nnt_value=1 / 0.044191)
        r = judge_object(write("__control_internally_perfect", sneaky), root)
        good = r["state"] == FAIL
        ok = ok and good
        print("  %-14s %-8s NNT exactly 1/|its own stale copy| -- internally "
              "perfect, externally superseded"
              % (r["state"], "correct" if good else "WRONG"))

        print("\nself-test %s" % ("PASSED" if ok else "FAILED"))
        return 0 if ok else 1
    finally:
        shutil.rmtree(root, ignore_errors=True)


# --------------------------------------------------------------------------

def run_controls():
    """Both controls, before any count is printed.

    THE CONTROLS ARE SYNTHETIC ON PURPOSE. A control anchored to a live corpus
    item retires itself the moment the defect is fixed: it then either fails and
    looks like a regression, or passes for the wrong reason. These are
    constructed, pinned in this file, and cannot drift. The negative side is not
    optional -- over-flagging is this gate's failure mode, and a false finding
    discredits the true ones.
    """
    import shutil
    import tempfile

    from instrument_controls import require_controls

    root = tempfile.mkdtemp(prefix="derivgate_ctl_")
    try:
        def write(name, obj):
            d = os.path.join(root, "ssot", name)
            os.makedirs(d, exist_ok=True)
            p = os.path.join(d, name + ".json")
            with open(p, "w", encoding="utf-8") as fh:
                json.dump(obj, fh)
            return p

        planted = write("__control_stale",
                        _obj(k=6, loo_rows=5, loo_k=4, est_point=-55.4593,
                             rd_point=-0.02305292779417, nnt_copy=-0.044191,
                             nnt_value=22.628984))
        fixed = write("__control_fixed",
                      _obj(k=6, loo_rows=6, loo_k=5, est_point=-55.24,
                           rd_point=-0.02305292779417,
                           nnt_copy=-0.02305292779417,
                           nnt_value=1 / 0.02305292779417))
        require_controls(
            "derived_recompute_gate",
            positive=("a synthetic object whose NNT and leave-one-out block are "
                      "snapshots of superseded operands",
                      judge_object(planted, root)["state"], FAIL),
            negative=("the same object with every derivation refreshed",
                      judge_object(fixed, root)["state"], FAIL))
    finally:
        shutil.rmtree(root, ignore_errors=True)


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("objects", nargs="*")
    ap.add_argument("--selftest", action="store_true")
    ap.add_argument("--diff", metavar="BASE")
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--repo", default=REPO)
    ap.add_argument("--timeout-seconds", type=float, default=300.0)
    ap.add_argument("--json", metavar="PATH")
    a = ap.parse_args(argv)

    if a.selftest:
        return selftest()

    # NOTHING IS PRINTED BEFORE THE CONTROLS HOLD.
    run_controls()

    repo = os.path.abspath(a.repo)
    not_reached = []
    if a.objects:
        objs = [os.path.abspath(p) for p in a.objects]
        scope_note = "object(s) named on the command line"
    elif a.all:
        objs = all_objects(repo)
        scope_note = "canonical object(s) under ssot/"
    else:
        base = a.diff or "origin/main"
        objs, err = diff_objects(base, repo)
        if objs is None:
            print("INVALID: cannot compute the diff against %s: %s" % (base, err))
            return 2
        scope_note = "canonical object(s) changed against %s" % base

    t0, c0 = time.time(), time.process_time()
    deadline = t0 + a.timeout_seconds
    records = []
    for i, p in enumerate(objs):
        if time.time() > deadline:
            not_reached = objs[i:]
            print("TIMED_OUT after %.1fs: %d object(s) were not reached."
                  % (a.timeout_seconds, len(not_reached)))
            break
        records.append(judge_object(p, repo))
    wall, cpu = time.time() - t0, time.process_time() - c0

    rc = report(records, len(objs), scope_note, wall, cpu, not_reached)
    if a.json:
        with open(a.json, "w", encoding="utf-8") as fh:
            json.dump({"records": records, "scope": scope_note,
                       "n_in_scope": len(objs),
                       "not_reached": [os.path.basename(p) for p in not_reached],
                       "wall_seconds": wall, "cpu_seconds": cpu}, fh, indent=1)
    return rc


if __name__ == "__main__":
    raise SystemExit(main())
