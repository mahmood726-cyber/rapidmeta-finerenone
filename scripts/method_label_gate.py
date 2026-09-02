"""METHOD LABEL GATE -- a label must be earned by the arithmetic it describes.

THE RULE. A method label must be EMITTED BY the code that performs the
computation, never typed by hand into a template. Where a hand-written label
already exists, it has to be checked against what the code actually did. This
gate does the checking, by recomputing the quantity both ways and asking which
answer is on the page.

WHAT WAS FOUND

    ARNI's prediction interval. `panels.prediction` carries
    `convention: 't_{k-1}, Cochrane Handbook v6.5'` beside the numbers 0.6862
    to 1.1070. Recomputed from the object's own pooled estimate, its interval,
    its k and its tau-squared, those two numbers are what a NORMAL quantile
    gives. The t quantile on k-1 = 3 degrees of freedom is 3.1824, and it gives
    0.5911 to 1.2853 -- which is what the object's OTHER prediction-interval
    surface holds, correctly labelled, after a correction the panel never
    received. At k=4 the label was wrong by a factor of 1.62 on the interval
    half-width; at k=2 the same mislabelling is wrong by a factor of 6.5 and
    routinely flips whether the interval spans no difference.

    Bococizumab's protocol table. It reads "the REML random-effects,
    inverse-variance estimator on the log scale" and "Effect scale reported on
    the log scale", for an outcome whose stored `pooled.scale` is `natural` and
    whose measure is a mean difference in percentage points. The label came from
    the review-level `config.scale`, which the outcome overrides. A template read
    a default where the computation had a fact.

THE THREE RULES

    PI_CRITICAL_VALUE
        Recompute the prediction interval under BOTH critical values from the
        object's own pooled point, confidence interval, k and tau-squared, then
        ask which one the stored interval reproduces, and compare THAT with the
        label. Arithmetic decides; the label is the thing on trial.

        A tell that needs no arithmetic and is checked separately: when
        tau-squared is 0 a normal-quantile prediction interval equals the
        confidence interval exactly. A prediction interval identical to its
        confidence interval is always wrong, at any k.

    SCALE_LABEL_VS_COMPUTATION
        A scale asserted ABOVE the outcome -- a review-level `config.scale`, or a
        method sentence on the page -- that disagrees with an outcome's own
        `pooled.scale`. Attribution is exact for the object-level case, so that
        one fails; the page-level case fails only when every outcome contradicts
        the page's claim, and is otherwise reported UNDETERMINABLE rather than
        guessed at.

    ESTIMATOR_LABEL_VS_USED
        `estimator` and `estimator_used` on one outcome naming different
        estimators.

WHAT IT CANNOT SEE -- printed with every verdict

    * A label for a computation this gate does not know how to redo. The list of
      recomputable methods is declared, not inferred.
    * A prediction interval whose inputs are incomplete: no k, no tau-squared,
      or a confidence interval from which no standard error can be recovered.
      That is UNDETERMINABLE, never a pass.
    * A label on the page that names no outcome, when outcomes disagree about
      the answer. Reported, not failed.
    * Whether the computation itself was the right one to do. It only asks
      whether the label matches what was done.
    * It does not FORCE labels to be emitted rather than typed; it detects the
      consequence. Emission is a build change, and this gate is what makes a
      hand-typed label a blocking defect in the meantime.

USAGE

    python scripts/method_label_gate.py --selftest
    python scripts/method_label_gate.py ssot/<app>/<app>.json [--page p.html]
    python scripts/method_label_gate.py --diff origin/main    # DEFAULT SCOPE
    python scripts/method_label_gate.py --all

Exit code: +1 if anything FAILED, +2 if anything could not be judged.
"""
from __future__ import annotations

import argparse
import html as _html
import json
import math
import os
import re
import subprocess
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)
if HERE not in sys.path:
    sys.path.insert(0, HERE)

PASS, FAIL, UNDET, NA = "PASS", "FAIL", "UNDETERMINABLE", "NOT_APPLICABLE"

# Two-sided 97.5% quantiles of Student's t, by degrees of freedom. Tabulated
# rather than computed so this gate needs no scipy: a gate that cannot run
# because of a missing optional dependency is a gate that silently does not run.
_T975 = {1: 12.706205, 2: 4.302653, 3: 3.182446, 4: 2.776445, 5: 2.570582,
         6: 2.446912, 7: 2.364624, 8: 2.306004, 9: 2.262157, 10: 2.228139,
         11: 2.200985, 12: 2.178813, 13: 2.160369, 14: 2.144787, 15: 2.131450,
         16: 2.119905, 17: 2.109816, 18: 2.100922, 19: 2.093024, 20: 2.085963,
         21: 2.079614, 22: 2.073873, 23: 2.068658, 24: 2.063899, 25: 2.059539,
         26: 2.055529, 27: 2.051831, 28: 2.048407, 29: 2.045230, 30: 2.042272}
_Z975 = 1.959964

_T_LABEL = re.compile(r"(?i)\bt[\s_-]*(?:distribution|\{?k\s*-\s*1\}?|_\{k-1\})"
                      r"|\bt\s+distribution|student|\bt_?\{?k-1\}?")
_Z_LABEL = re.compile(r"(?i)normal quantile|normal critical|\bz[\s-]*(?:quantile|"
                      r"critical|distribution)|gaussian")

_NATURAL_MEASURES = ("MD", "SMD", "RD", "MEAN DIFFERENCE", "RISK DIFFERENCE")

_INLINE = ("a|abbr|b|bdi|bdo|big|cite|code|del|dfn|em|font|i|ins|kbd|label|mark|"
           "output|q|rp|rt|ruby|s|samp|small|span|strike|strong|sub|sup|time|tt|"
           "u|var|wbr")
_INLINE_RE = re.compile(r"(?i)</?(?:%s)\b[^>]*>" % _INLINE)


def rendered_text(html):
    txt = re.sub(r"(?is)<(script|style)\b.*?</\1>", " ", html)
    txt = _INLINE_RE.sub("", txt)
    txt = re.sub(r"<[^>]+>", " ", txt)
    return re.sub(r"\s+", " ", _html.unescape(txt))


def is_num(v):
    return isinstance(v, (int, float)) and not isinstance(v, bool)


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
    def __init__(self, rule, where, state, detail):
        self.rule, self.where, self.state, self.detail = rule, where, state, detail

    def as_dict(self):
        return {"rule": self.rule, "where": self.where, "state": self.state,
                "detail": self.detail}


# --------------------------------------------------------------------------
# PI recomputation

def _se_from_ci(lo, hi, scale):
    """Standard error of the summary, recovered from its 95% interval."""
    if scale == "log":
        if lo <= 0 or hi <= 0:
            return None
        return (math.log(hi) - math.log(lo)) / (2.0 * _Z975)
    return (hi - lo) / (2.0 * _Z975)


def _pi(point, se, tau2, crit, scale):
    sd = math.sqrt(max(tau2, 0.0) + se * se)
    if scale == "log":
        mu = math.log(point)
        return math.exp(mu - crit * sd), math.exp(mu + crit * sd)
    return point - crit * sd, point + crit * sd


def _pi_blocks(outcome):
    """Every stored prediction interval on an outcome, with its label."""
    out = []
    p = outcome.get("panels")
    if isinstance(p, dict) and isinstance(p.get("prediction"), dict):
        b = p["prediction"]
        out.append(("panels.prediction", b.get("pi_low"), b.get("pi_high"),
                    " ".join(str(b.get(k, "")) for k in
                             ("convention", "method", "label", "note"))))
    b = outcome.get("prediction_interval")
    if isinstance(b, dict):
        out.append(("prediction_interval", b.get("low"), b.get("high"),
                    " ".join(str(b.get(k, "")) for k in
                             ("method", "convention", "label", "note"))))
    return out


def rule_pi_critical_value(oid, outcome):
    blocks = _pi_blocks(outcome)
    if not blocks:
        return [Finding("PI_CRITICAL_VALUE", oid, NA,
                        "no prediction interval stored on this outcome")]
    k = outcome.get("k")
    pooled = outcome.get("pooled") or {}
    het = outcome.get("heterogeneity") or {}
    point, lo, hi = pooled.get("point"), pooled.get("ci_low"), pooled.get("ci_high")
    scale = str(pooled.get("scale") or "natural").lower()
    tau2 = het.get("tau2")

    missing = [n for n, v in (("k", k), ("pooled.point", point),
                              ("pooled.ci_low", lo), ("pooled.ci_high", hi),
                              ("heterogeneity.tau2", tau2)) if not is_num(v)]
    if missing:
        return [Finding("PI_CRITICAL_VALUE", oid, UNDET,
                        "a prediction interval is displayed but %s %s absent, "
                        "so which critical value produced it cannot be "
                        "established" % (", ".join(missing),
                                         "is" if len(missing) == 1 else "are"))]
    if k < 2:
        return [Finding("PI_CRITICAL_VALUE", oid, UNDET,
                        "a prediction interval is displayed at k=%s; it is "
                        "undefined below k=2" % k)]
    df = int(k) - 1
    if df not in _T975:
        return [Finding("PI_CRITICAL_VALUE", oid, UNDET,
                        "no tabulated t quantile for %d degrees of freedom" % df)]
    se = _se_from_ci(lo, hi, scale)
    if se is None or se <= 0:
        return [Finding("PI_CRITICAL_VALUE", oid, UNDET,
                        "no standard error can be recovered from the stored "
                        "interval (%s to %s on the %s scale)" % (lo, hi, scale))]

    t_lo, t_hi = _pi(point, se, tau2, _T975[df], scale)
    z_lo, z_hi = _pi(point, se, tau2, _Z975, scale)
    out = []
    for where, plo, phi, label in blocks:
        if not (is_num(plo) and is_num(phi)):
            out.append(Finding("PI_CRITICAL_VALUE", "%s/%s" % (oid, where), UNDET,
                               "the block carries no numeric interval"))
            continue

        def near(a, b):
            return abs(a - b) <= max(abs(b) * 0.01, 1e-6)

        is_t = near(plo, t_lo) and near(phi, t_hi)
        is_z = near(plo, z_lo) and near(phi, z_hi)
        says_t = bool(_T_LABEL.search(label))
        says_z = bool(_Z_LABEL.search(label))

        # the arithmetic-free tell: a PI equal to its own CI
        if near(plo, lo) and near(phi, hi):
            out.append(Finding(
                "PI_CRITICAL_VALUE", "%s/%s" % (oid, where), FAIL,
                "the prediction interval (%.4f to %.4f) is identical to the "
                "confidence interval. A prediction interval equal to its own "
                "confidence interval is always wrong, at any k."
                % (plo, phi)))
            continue
        if not is_t and not is_z:
            out.append(Finding(
                "PI_CRITICAL_VALUE", "%s/%s" % (oid, where), UNDET,
                "the stored interval %.4f to %.4f reproduces neither the t "
                "(%.4f to %.4f) nor the normal (%.4f to %.4f) recomputation, so "
                "this gate cannot say what produced it"
                % (plo, phi, t_lo, t_hi, z_lo, z_hi)))
            continue
        if is_z and says_t and not says_z:
            out.append(Finding(
                "PI_CRITICAL_VALUE", "%s/%s" % (oid, where), FAIL,
                "the label says %r, and the numbers %.4f to %.4f are what a "
                "NORMAL quantile (%.4f) gives. The t quantile on %d degrees of "
                "freedom is %.4f and gives %.4f to %.4f. The label describes a "
                "computation that was not performed."
                % (label.strip()[:80], plo, phi, _Z975, df, _T975[df],
                   t_lo, t_hi)))
            continue
        if is_t and says_z and not says_t:
            out.append(Finding(
                "PI_CRITICAL_VALUE", "%s/%s" % (oid, where), FAIL,
                "the label says %r, and the numbers %.4f to %.4f are the t "
                "recomputation on %d degrees of freedom, not the normal one "
                "(%.4f to %.4f)." % (label.strip()[:80], plo, phi, df,
                                     z_lo, z_hi)))
            continue
        if not says_t and not says_z:
            out.append(Finding(
                "PI_CRITICAL_VALUE", "%s/%s" % (oid, where), UNDET,
                "the interval is %s-based by recomputation but carries no label "
                "naming a critical value, so there is nothing to check it "
                "against" % ("t" if is_t else "normal")))
            continue
        out.append(Finding("PI_CRITICAL_VALUE", "%s/%s" % (oid, where), PASS,
                           "labelled %s and reproduces the %s recomputation "
                           "(%.4f to %.4f)"
                           % ("t" if says_t else "normal",
                              "t" if is_t else "normal", plo, phi)))
    return out


# --------------------------------------------------------------------------

def rule_scale_label(obj, page_text=None):
    by_outcome = ((obj.get("results") or {}).get("by_outcome") or {})
    scales = {}
    for oid, o in by_outcome.items():
        if isinstance(o, dict):
            po = o.get("pooled") or {}
            s = str(po.get("scale") or "").lower()
            m = str(po.get("measure") or "").upper()
            if not s and m in _NATURAL_MEASURES:
                s = "natural"
            if s:
                scales[oid] = s
    if not scales:
        return [Finding("SCALE_LABEL_VS_COMPUTATION", "results", NA,
                        "no outcome records the scale it was pooled on")]

    out = []
    cfg = str(((obj.get("config") or {}).get("scale")) or "").lower()
    if cfg:
        off = sorted(o for o, s in scales.items() if s != cfg)
        if off:
            out.append(Finding(
                "SCALE_LABEL_VS_COMPUTATION", "config.scale", FAIL,
                "config.scale is %r, and %d of %d outcome(s) were pooled on a "
                "different scale: %s. A review-level default rendered as a "
                "method label states, for those outcomes, a computation that "
                "was not performed."
                % (cfg, len(off), len(scales),
                   ", ".join("%s=%s" % (o, scales[o]) for o in off))))
        else:
            out.append(Finding("SCALE_LABEL_VS_COMPUTATION", "config.scale", PASS,
                               "config.scale %r agrees with all %d outcome(s)"
                               % (cfg, len(scales))))

    if page_text:
        claims = set(m.group(1).lower() for m in
                     re.finditer(r"(?i)on the (log|natural|ratio) scale",
                                 page_text))
        for claim in sorted(claims):
            agree = [o for o, s in scales.items() if s == claim]
            if agree:
                out.append(Finding(
                    "SCALE_LABEL_VS_COMPUTATION", "the page", PASS,
                    "the page says %r and %d outcome(s) were pooled that way"
                    % ("on the %s scale" % claim, len(agree))))
            elif len(scales) == 1:
                oid, s = list(scales.items())[0]
                out.append(Finding(
                    "SCALE_LABEL_VS_COMPUTATION", "the page", FAIL,
                    "the page says %r while the only outcome on this object "
                    "(%s) was pooled on the %s scale."
                    % ("on the %s scale" % claim, oid, s)))
            else:
                out.append(Finding(
                    "SCALE_LABEL_VS_COMPUTATION", "the page", UNDET,
                    "the page says %r and NO outcome was pooled that way (%s), "
                    "but the sentence names no outcome, so this gate will not "
                    "attribute it."
                    % ("on the %s scale" % claim,
                       ", ".join("%s=%s" % kv for kv in sorted(scales.items())))))
    return out


# NEITHER OF THESE NAMES AN ESTIMATOR. "not pooled -- the estimate is withdrawn"
# and "none" are the same statement in different words, and comparing them as
# strings produced FOURTEEN false accusations on the first corpus run of this
# gate -- inside the very gate written to stop a label being trusted over the
# arithmetic. Where nothing was pooled there is no estimator to label, and the
# rule does not apply.
_NO_ESTIMATOR = re.compile(
    r"(?i)^\s*(none\b.*|n/?a\b.*|not applicable\b.*|-+|not pooled\b.*|"
    r"withdrawn\b.*|no estimator\b.*|no estimate\b.*|nothing pooled\b.*)\s*$")


def rule_estimator_label(oid, outcome):
    a = outcome.get("estimator")
    b = outcome.get("estimator_used")
    if a is None or b is None:
        return [Finding("ESTIMATOR_LABEL_VS_USED", oid, NA,
                        "this outcome does not record both a declared and a "
                        "used estimator")]
    sa, sb = str(a).strip(), str(b).strip()
    na, nb = bool(_NO_ESTIMATOR.match(sa)), bool(_NO_ESTIMATOR.match(sb))
    if na and nb:
        return [Finding("ESTIMATOR_LABEL_VS_USED", oid, NA,
                        "nothing was pooled on this outcome (%r / %r), so there "
                        "is no estimator label to check" % (sa, sb))]
    if na != nb:
        return [Finding("ESTIMATOR_LABEL_VS_USED", oid, FAIL,
                        "one side says no estimator was used and the other "
                        "names one: estimator %r, estimator_used %r." % (sa, sb))]
    if sa.lower() == sb.lower():
        return [Finding("ESTIMATOR_LABEL_VS_USED", oid, PASS,
                        "declared and used estimator agree: %r" % sa)]
    # one may be a phrase containing the other -- that is agreement, not drift
    if re.search(r"(?i)\b%s\b" % re.escape(sa), sb) or \
       re.search(r"(?i)\b%s\b" % re.escape(sb), sa):
        return [Finding("ESTIMATOR_LABEL_VS_USED", oid, PASS,
                        "declared %r and used %r name the same estimator"
                        % (sa, sb))]
    return [Finding("ESTIMATOR_LABEL_VS_USED", oid, FAIL,
                    "the outcome declares estimator %r and records "
                    "estimator_used %r." % (sa, sb))]


# --------------------------------------------------------------------------

def judge_object(path, repo, page_path=None):
    rec = {"object": os.path.relpath(path, repo).replace(os.sep, "/"),
           "page": None, "state": None, "detail": "", "findings": []}
    try:
        with open(path, "rb") as fh:
            obj = json.loads(fh.read().decode("utf-8", "replace"))
    except Exception as exc:
        rec["state"] = "NO_RECORD"
        rec["detail"] = "object unreadable: %s" % exc
        return rec

    page_text = None
    if page_path and os.path.exists(page_path):
        with open(page_path, "rb") as fh:
            page_text = rendered_text(fh.read().decode("utf-8", "replace"))
        rec["page"] = os.path.relpath(page_path, repo).replace(os.sep, "/")

    fs = []
    by_outcome = ((obj.get("results") or {}).get("by_outcome") or {})
    for oid, o in by_outcome.items():
        if not isinstance(o, dict):
            continue
        fs += rule_pi_critical_value(oid, o)
        fs += rule_estimator_label(oid, o)
    fs += rule_scale_label(obj, page_text)
    if not fs:
        fs = [Finding("*", "results", NA, "no outcome block on this object")]
    rec["findings"] = [f.as_dict() for f in fs]

    states = {f["state"] for f in rec["findings"]}
    rec["state"] = (FAIL if FAIL in states else
                    UNDET if UNDET in states else
                    PASS if PASS in states else NA)
    return rec


# --------------------------------------------------------------------------
# scope / reporting -- identical contract to the other gates in this suite

def _is_canonical(rel):
    p = rel.split("/")
    return len(p) == 3 and p[0] == "ssot" and p[2] == p[1] + ".json"


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
        if n and _is_canonical(n) and os.path.exists(p):
            out.append(p)
    return out, None


def all_objects(repo):
    root = os.path.join(repo, "ssot")
    if not os.path.isdir(root):
        return []
    return [os.path.join(root, n, n + ".json") for n in sorted(os.listdir(root))
            if os.path.exists(os.path.join(root, n, n + ".json"))]


def report(records, n_in_scope, scope_note, wall, cpu, not_reached):
    fails = [r for r in records if r["state"] == FAIL]
    undet = [r for r in records if r["state"] in (UNDET, "NO_RECORD", "TIMED_OUT")]
    passes = [r for r in records if r["state"] == PASS]
    na = [r for r in records if r["state"] == NA]

    for r in fails:
        print("\nFAIL  %s%s" % (r["object"],
                                "  (page %s)" % r["page"] if r["page"] else ""))
        for f in [x for x in r["findings"] if x["state"] == FAIL]:
            print("      [%s] %s" % (f["rule"], f["where"]))
            print("      %s" % f["detail"])
    for r in undet:
        print("\n%-14s %s -- %s" % (r["state"], r["object"], r["detail"][:120]))
        for f in [x for x in r["findings"] if x["state"] == UNDET][:4]:
            print("      [%s] %s -- %s" % (f["rule"], f["where"], f["detail"]))

    reach = {}
    for r in records:
        for f in r["findings"]:
            d = reach.setdefault(f["rule"], {PASS: 0, FAIL: 0, UNDET: 0, NA: 0})
            d[f["state"]] += 1

    print("\n" + "-" * 74)
    print("COVERAGE   %d of %d %s" % (len(records), n_in_scope, scope_note))
    print("           %d PASS, %d FAIL, %d could not be judged, %d not "
          "applicable" % (len(passes), len(fails), len(undet), len(na)))
    print("PER RULE   (a rule that judged nothing reads NOT OBSERVED, not SAFE)")
    for rule in sorted(reach):
        d = reach[rule]
        judged = d[PASS] + d[FAIL] + d[UNDET]
        print("           %-30s %s"
              % (rule,
                 "NOT OBSERVED -- 0 judged, %d not applicable" % d[NA]
                 if judged == 0 else
                 "%d judged: %d pass, %d fail, %d undeterminable (%d n/a)"
                 % (judged, d[PASS], d[FAIL], d[UNDET], d[NA])))
    print("BLIND TO   methods this gate cannot redo; a PI with incomplete "
          "inputs; a page label")
    print("           that names no outcome when outcomes disagree. It detects "
          "a hand-typed")
    print("           label; it does not make the build emit one.")
    if not_reached:
        print("           NOT REACHED: %d object(s)" % len(not_reached))
    print("COST       %.2fs wall, %.2fs CPU" % (wall, cpu))
    if not records:
        print("VERDICT    NOT OBSERVED -- nothing in scope carried an object.")
    return (1 if fails else 0) + (2 if (undet or not_reached) else 0)


# --------------------------------------------------------------------------
# self-test

def _outcome(k=4, tau2=0.0085970258403, crit="z", label="t_{k-1}, Cochrane "
                                                        "Handbook v6.5"):
    point, lo, hi = 0.87153524291, 0.74608292776, 1.0180821077
    se = _se_from_ci(lo, hi, "log")
    c = _Z975 if crit == "z" else _T975[k - 1]
    plo, phi = _pi(point, se, tau2, c, "log")
    return {"k": k, "estimator": "REML", "estimator_used": "REML",
            "pooled": {"measure": "HR", "point": point, "ci_low": lo,
                       "ci_high": hi, "scale": "log"},
            "heterogeneity": {"tau2": tau2},
            "panels": {"prediction": {"pi_low": plo, "pi_high": phi,
                                      "convention": label}}}


def _md_outcome():
    """A natural-scale mean-difference outcome with NO prediction interval.

    Deliberately separate from the HR fixture: mixing a log-scale PI into a
    natural-scale outcome makes the PI rule fire for its own reason and the
    scale case stops testing what it says it tests.
    """
    return {"k": 6, "estimator": "REML", "estimator_used": "REML",
            "pooled": {"measure": "MD", "point": -55.24, "ci_low": -57.92,
                       "ci_high": -52.56, "scale": "natural"},
            "heterogeneity": {"tau2": 9.3148}}


def _obj(outcome, config_scale=None):
    o = {"results": {"by_outcome": {"o1": outcome}}}
    if config_scale:
        o["config"] = {"scale": config_scale}
    return o


def selftest():
    import copy
    import shutil
    import tempfile

    root = tempfile.mkdtemp(prefix="methodlabel_")
    try:
        seq = [0]

        def run(label, obj, want, rule=None, page=None):
            seq[0] += 1
            d = os.path.join(root, "ssot", "__control_%02d" % seq[0])
            os.makedirs(d, exist_ok=True)
            p = os.path.join(d, "__control_%02d.json" % seq[0])
            with open(p, "w", encoding="utf-8") as fh:
                json.dump(obj, fh)
            pg = None
            if page is not None:
                pg = os.path.join(root, "p%02d.html" % seq[0])
                with open(pg, "w", encoding="utf-8") as fh:
                    fh.write(page)
            r = judge_object(p, root, pg)
            fired = {f["rule"] for f in r["findings"] if f["state"] == FAIL}
            good = r["state"] == want and (rule is None or rule in fired)
            print("  %-14s expected %-14s %-8s %s"
                  % (r["state"], want, "correct" if good else "WRONG", label))
            return good

        ok = True
        print("=== each plant must fire before its fix is allowed to pass ===")

        ok &= run("PLANT: normal-quantile numbers under a t_{k-1} label "
                  "(ARNI, exactly)", _obj(_outcome(crit="z")), FAIL,
                  "PI_CRITICAL_VALUE")
        ok &= run("FIX of that plant: the same label over t-quantile numbers",
                  _obj(_outcome(crit="t")), PASS)
        ok &= run("PLANT: t numbers under a 'normal quantile' label",
                  _obj(_outcome(crit="t", label="built with a normal quantile")),
                  FAIL, "PI_CRITICAL_VALUE")

        # tau2 = 0: the normal PI collapses onto the CI, and that is always wrong
        o = _outcome(crit="z", tau2=0.0)
        ok &= run("PLANT: tau-squared 0, so the normal PI equals the CI exactly",
                  _obj(o), FAIL, "PI_CRITICAL_VALUE")

        o = _outcome(crit="z")
        o["panels"]["prediction"]["convention"] = "random-effects"
        ok &= run("a PI with no critical value named: UNDETERMINABLE, not a pass",
                  _obj(o), UNDET)

        o = _outcome(crit="z")
        del o["heterogeneity"]["tau2"]
        ok &= run("a PI displayed with no tau-squared to recompute it from",
                  _obj(o), UNDET)

        ok &= run("PLANT: config.scale 'log' over an outcome pooled natural "
                  "(bococizumab, exactly)",
                  _obj(_md_outcome(), "log"),
                  FAIL, "SCALE_LABEL_VS_COMPUTATION")
        ok &= run("FIX of that plant: config.scale matches the outcome",
                  _obj(_md_outcome(), "natural"), PASS)

        ok &= run("PLANT: a page saying 'on the log scale' for a "
                  "natural-scale-only object",
                  _obj(_md_outcome()),
                  FAIL, "SCALE_LABEL_VS_COMPUTATION",
                  page="<html><body><p>Pooled with inverse variance on the "
                       "l<em>og</em> scale.</p></body></html>")

        o = copy.deepcopy(_outcome(crit="t"))
        o["estimator_used"] = "DL"
        ok &= run("PLANT: estimator declared REML, estimator_used DL",
                  _obj(o), FAIL, "ESTIMATOR_LABEL_VS_USED")

        # THE FALSE POSITIVE THIS GATE COMMITTED ON ITS OWN FIRST CORPUS RUN.
        # Fourteen accusations, every one of them a withdrawn outcome saying so
        # twice in different words. Kept as a permanent negative control.
        o = copy.deepcopy(_outcome(crit="t"))
        o["estimator"] = "not pooled -- the estimate is withdrawn"
        o["estimator_used"] = "none"
        ok &= run("a withdrawn outcome saying so twice in different words is "
                  "NOT a label contradiction", _obj(o), PASS)

        o = copy.deepcopy(_outcome(crit="t"))
        o["estimator"] = "not pooled -- the estimate is withdrawn"
        o["estimator_used"] = "REML"
        ok &= run("PLANT: one side says nothing was pooled, the other names an "
                  "estimator", _obj(o), FAIL, "ESTIMATOR_LABEL_VS_USED")

        ok &= run("an object with no outcome at all is NOT_APPLICABLE",
                  {"results": {"by_outcome": {}}}, NA)

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

    root = tempfile.mkdtemp(prefix="methodlabel_ctl_")
    try:
        def write(name, obj):
            d = os.path.join(root, "ssot", name)
            os.makedirs(d, exist_ok=True)
            p = os.path.join(d, name + ".json")
            with open(p, "w", encoding="utf-8") as fh:
                json.dump(obj, fh)
            return p

        p1 = write("__control_mislabelled", _obj(_outcome(crit="z")))
        p2 = write("__control_labelled_right", _obj(_outcome(crit="t")))
        require_controls(
            "method_label_gate",
            positive=("a synthetic prediction interval computed with a normal "
                      "quantile and labelled as t on k-1 degrees of freedom",
                      judge_object(p1, root)["state"], FAIL),
            negative=("the same label over t-quantile numbers",
                      judge_object(p2, root)["state"], FAIL))
    finally:
        shutil.rmtree(root, ignore_errors=True)


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("objects", nargs="*")
    ap.add_argument("--selftest", action="store_true")
    ap.add_argument("--page")
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
        records.append(judge_object(p, repo, a.page if len(objs) == 1 else None))
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
