r"""Absolute risk difference and NNT for every r_validation sidecar, pooled
DIRECTLY from the 2x2 cells.

WHY DIRECT, AND NOT BY CONVERTING THE POOLED ODDS RATIO
    Converting a pooled OR to an absolute effect needs a baseline risk
    ASSUMED from somewhere. Pooling the risk difference from the cells does
    not: the control arms of the trials supply the baseline themselves. So
    this takes the direct route, and says so on every row. The pooled odds
    ratio already in the sidecar is left untouched and is not used.

WHAT THE BASELINE IS, ON EVERY ROW
    baseline_value   pooled control-arm risk, sum(cE)/sum(cN)
    baseline_source  the control arms of the named trials, with numerator
                     and denominator spelled out
    baseline_spread  the per-trial control risks, because the pooled figure
                     hides them, and the absolute effect at the extremes of
                     that range is a different number from the same pool

    A different baseline gives a different answer. That is the whole point
    of publishing the baseline beside the effect.

ORDER OF CHECKS -- THE STORE'S REFUSAL IS CONSULTED FIRST
    The sidecars overrode the store's refusals 88 times out of 108. So a
    sidecar is never computed on its own authority where the store has
    ruled. Each sidecar resolves to one of:

      REFUSED_BY_STORE        a store object exists, matches on trial
                              identity, and refuses. Verbatim reason
                              carried; nothing is computed.
      NO_STORE_ADJUDICATION   no store object exists for this page. This is
                              SILENCE, NOT PERMISSION, and it is reported as
                              its own state rather than folded in with pages
                              the store has actually allowed.
      store_adjudication=ALLOWED  a store object exists, matches, does not
                              refuse.

    MATCHING IS BY TRIAL IDENTITY, NOT BY NAME. A name match alone is not an
    identity: ARNI_HF.json and ssot/arni-hfref pool DIFFERENT TRIALS --
    PARAGON-HF and PARADISE-MI against parachute-hf, parallel-hf and
    answer-hf. Letting a store refusal or a store polarity attach to a
    sidecar on the strength of a similar name would bind a ruling to
    evidence it was never made about. So a mapped pair must also share NCT
    identifiers, and a name match with no trial overlap is recorded as
    NAME_MATCH_WITHOUT_TRIAL_OVERLAP and treated as unadjudicated.

PROVENANCE EXCLUSIONS, BY PROVENANCE AND NOT BY INSPECTION
    17 sidecars are derived from a published hazard ratio and store a log
    HAZARD ratio in a field named `pooled_logOR`. They carry `hr` on their
    trial rows and no per-arm cells. 21 more are mean differences. Both are
    excluded on the presence of those keys -- never on whether the numbers
    happen to look convertible.

POLARITY
    An NNT counts events. Whether fewer events is better depends on whether
    the event is death or cure, and that is NOT in the sidecar. Where the
    store supplies `favours` for a matched outcome the polarity is recorded;
    otherwise the row carries POLARITY_UNKNOWN and no benefit/harm reading.
    The risk difference and the NNT MAGNITUDE are still reported, because
    those are arithmetic; only the interpretation is withheld.

POOLING
    Random effects, REML tau-squared, Hartung-Knapp-Sidik-Jonkman variance
    with the scaling factor floored at 1, interval on t_{k-1}. Those choices
    are the ones the sidecar generator already made for the odds ratio, and
    the REML routine is IMPORTED from it rather than rewritten, so the two
    cannot drift apart. Zero-cell continuity correction is applied ONLY when
    a cell is actually zero.
"""
from __future__ import annotations
import argparse
import glob
import json
import math
import os
import sys
from collections import OrderedDict, Counter

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)

# SINGLE SOURCE OF TRUTH. build_binary_sidecar.reml_tau2 was corrected on
# 2026-08-31 and is now imported rather than duplicated here, so the two
# cannot drift apart. It is proven against metafor by
# tests/test_metafor_oracle.py.
from build_binary_sidecar import t_quantile_975, reml_tau2  # noqa: E402


def reml_tau2_historic(ys, vs, max_iter=200, tol=1e-10):
    """THE ESTIMATOR THAT PRODUCED THE ARTEFACTS CURRENTLY ON DISK.

        tau2 <- tau2 + sum(w^2 * ((y - mu)^2 - v)) / sum(w^2)

    This is NOT a fallback and must never be called to compute a result. It
    exists for exactly one purpose: to reproduce what the published sidecars
    say, so the corrected values can be compared against them.

    It is kept as an explicit reimplementation rather than an import,
    because build_binary_sidecar.reml_tau2 has since been fixed. After that
    fix, importing it "as shipped" would silently make the comparison
    correct-against-correct and report a blast radius of zero -- a
    regeneration that appears to change nothing, which is indistinguishable
    from one that never ran.

    Two defects, both load-bearing: it is an INCREMENT on the previous value
    rather than a direct assignment, and it omits the `1/sum(w)` term that
    separates REML from ML. Clamped at zero it has a fixed point AT zero.
    """
    k = len(ys)
    if k < 2:
        return 0.0
    tau2 = 0.0
    for _ in range(max_iter):
        w = [1.0 / (v + tau2) for v in vs]
        sw = sum(w)
        mu = sum(wi * y for wi, y in zip(w, ys)) / sw
        num = sum((wi ** 2) * ((y - mu) ** 2 - v)
                  for wi, y, v in zip(w, ys, vs))
        den = sum(wi ** 2 for wi in w)
        new = max(0.0, tau2 + num / den)
        if abs(new - tau2) < tol:
            return new
        tau2 = new
    return tau2


# name kept for callers that predate the correction
reml_tau2_as_shipped = reml_tau2_historic

SIDECARS = os.path.join(ROOT, "outputs", "r_validation", "*.json")
STORE = os.path.join(ROOT, "ssot", "*", "*.json")


# ------------------------------------------------------------ per-trial risk

def rd_and_variance(tE, tN, cE, cN):
    """Risk difference for one trial and its variance.

    Continuity correction ONLY when a cell is zero; applying it
    unconditionally biases the estimate.
    Returns (rd, var) or None if the trial cannot yield either.
    """
    for v in (tE, tN, cE, cN):
        # positive form: what a usable cell IS. bool excluded explicitly,
        # since True is an int in Python and would pass as 1.
        is_a_plain_integer = isinstance(v, int) and isinstance(v, bool) is False
        if is_a_plain_integer is False:
            return None
    if tN <= 0 or cN <= 0 or tE < 0 or cE < 0 or tE > tN or cE > cN:
        return None
    a, b, c, d = tE, tN - tE, cE, cN - cE
    if min(a, b, c, d) == 0:
        a, b, c, d = a + 0.5, b + 0.5, c + 0.5, d + 0.5
    n1, n0 = a + b, c + d
    p1, p0 = a / n1, c / n0
    var = p1 * (1 - p1) / n1 + p0 * (1 - p0) / n0
    if var <= 0 or not math.isfinite(var):
        return None
    return p1 - p0, var


def pool_rd(rows):
    """Random-effects pool of risk differences. rows: [(name, rd, var)].

    REML tau-squared, HKSJ variance with the scaling factor floored at 1
    (below 1 it would narrow the interval below the fixed-effect one), and
    a t_{k-1} interval.
    """
    k = len(rows)
    ys = [r[1] for r in rows]
    vs = [r[2] for r in rows]
    if k == 1:
        se = math.sqrt(vs[0])
        return OrderedDict([
            ("point", ys[0]), ("se", se), ("k", 1), ("tau2", None),
            ("Q", None), ("I2", None), ("hksj_floor_applied", None),
            ("ci_low", ys[0] - 1.959963985 * se),
            ("ci_high", ys[0] + 1.959963985 * se),
            ("interval_basis", "SINGLE TRIAL -- this is not a pooled "
                               "estimate; the interval is that one trial's, "
                               "on a normal quantile"),
        ])
    tau2 = reml_tau2(ys, vs)
    w = [1.0 / (v + tau2) for v in vs]
    sw = sum(w)
    mu = sum(wi * yi for wi, yi in zip(w, ys)) / sw
    # HKSJ scaling, floored at 1 (Wiksten 2016)
    q = sum(wi * (yi - mu) ** 2 for wi, yi in zip(w, ys)) / (k - 1)
    floored = q < 1.0
    q_used = max(q, 1.0)
    se = math.sqrt(q_used / sw)
    tcrit = t_quantile_975(k - 1)
    # heterogeneity on the fixed-effect weights
    wf = [1.0 / v for v in vs]
    swf = sum(wf)
    muf = sum(wi * yi for wi, yi in zip(wf, ys)) / swf
    Q = sum(wi * (yi - muf) ** 2 for wi, yi in zip(wf, ys))
    I2 = max(0.0, (Q - (k - 1)) / Q * 100.0) if Q > 0 else 0.0
    return OrderedDict([
        ("point", mu), ("se", se), ("k", k), ("tau2", tau2),
        ("Q", Q), ("I2", I2), ("hksj_floor_applied", floored),
        ("ci_low", mu - tcrit * se), ("ci_high", mu + tcrit * se),
        ("interval_basis", "REML tau-squared, HKSJ variance floored at 1, "
                           "t_{k-1} interval"),
    ])


# ------------------------------------------------------------------ the NNT

def nnt_from_rd(point, lo, hi):
    """NNT and its interval. Altman BMJ 1998 for an interval spanning zero."""
    out = OrderedDict()
    out["risk_difference"] = point
    out["risk_difference_per_1000"] = point * 1000.0
    out["direction"] = ("FEWER_EVENTS" if point < 0 else
                        "MORE_EVENTS" if point > 0 else "NO_DIFFERENCE")
    out["nnt_magnitude"] = (1.0 / abs(point)) if point else None
    if lo is None or hi is None:
        out["nnt_ci_kind"] = "NO_INTERVAL"
        return out
    if lo < 0 < hi:
        out["nnt_ci_kind"] = "SPANS_NO_DIFFERENCE"
        out["nnt_ci"] = OrderedDict([
            ("nnt_fewer_events_bound", 1.0 / abs(lo)),
            ("to", "infinity"),
            ("nnt_more_events_bound", 1.0 / abs(hi)),
            ("reading", "Altman 1998: the risk-difference interval includes "
                        "zero, so the NNT interval is not a finite range."),
        ])
    elif lo == 0 or hi == 0:
        out["nnt_ci_kind"] = "BOUND_AT_NO_DIFFERENCE"
    else:
        out["nnt_ci_kind"] = "FINITE"
        a, b = abs(lo), abs(hi)
        out["nnt_ci"] = OrderedDict([("low", 1.0 / max(a, b)),
                                     ("high", 1.0 / min(a, b))])
    return out


# ------------------------------------------------------- store adjudication

def _store_file_kind(path):
    """Name what a store file IS. Returns (kind, obj_or_None).

    Positive form, and it counts. A store object dropped here is not a
    cosmetic loss: it is a HOLE IN THE REFUSAL RECORD. If an object that
    refuses a pool fails to load, the sidecar of the same name stops
    resolving to REFUSED_BY_STORE and silently becomes
    NO_STORE_ADJUDICATION -- and then gets computed. The drop would move a
    row in the UNSAFE direction, so it is counted and surfaced rather than
    swallowed by a bare `continue`.
    """
    try:
        obj = json.load(open(path, encoding="utf-8"))
    except Exception:
        return "unparseable", None
    if isinstance(obj, dict):
        if "THE_OBJECT_AS_IT_STOOD_AT_RETIREMENT" in obj:
            return "tombstone", obj
        res = obj.get("results")
        if isinstance(res, dict):
            bo = res.get("by_outcome")
            if isinstance(bo, dict):
                return "usable", obj
            return "no_by_outcome", obj
        return "no_results", obj
    return "root_not_dict", None


def load_store():
    """topic -> {ncts, outcomes:{name:(refused, reason, favours)}}.

    Returns (store, dropped) where dropped counts every file NOT loaded, by
    kind. The caller must report it: an unreported drop here weakens the
    refusal check without any visible symptom.
    """
    out = {}
    dropped = Counter()
    for path in sorted(glob.glob(STORE)):
        kind, obj = _store_file_kind(path)
        if kind != "usable":
            dropped[kind] += 1
            continue
        res = obj.get("results")
        bo = res.get("by_outcome")
        topic = os.path.basename(os.path.dirname(path))
        ncts = set()
        inp = obj.get("inputs")
        for t in ((inp.get("trials") if isinstance(inp, dict) else None) or []):
            if isinstance(t, dict) and t.get("nct"):
                ncts.add(str(t["nct"]).upper())
        outcomes = {}
        for name, o in bo.items():
            if isinstance(o, dict):
                p = o.get("pooled") if isinstance(o.get("pooled"), dict) else {}
                refused, reason = False, None
                if p.get("withdrawn"):
                    refused = True
                    reason = (p.get("withdrawn_reason")
                              or p.get("withdrawn_because")
                              or "pooled.withdrawn set with no reason recorded")
                elif o.get("poolable") is False:
                    refused = True
                    reason = (o.get("poolable_reason")
                              or "poolable false with no reason recorded")
                outcomes[name] = (refused, reason, o.get("favours"))
            else:
                # A malformed outcome cannot be read for a refusal. Recording
                # it as refused-with-no-reason would invent a ruling; dropping
                # it silently would lose one. It is named instead.
                dropped["outcome_not_a_dict"] += 1
        out[topic] = {"ncts": ncts, "outcomes": outcomes}
    return out, dropped


def candidate_topics(stem):
    b = stem.lower().replace("_", "-")
    return [b, b + "-review"]


def adjudicate(stem, sidecar_ncts, store):
    """Return (state, detail). Name match is not enough; trials must overlap."""
    for cand in candidate_topics(stem):
        if cand not in store:
            continue
        entry = store[cand]
        overlap = sidecar_ncts & entry["ncts"]
        identity_proven = bool(overlap)
        identity_disproven = bool(sidecar_ncts and entry["ncts"] and not overlap)
        # ASYMMETRY, ON PURPOSE. Identity can be proven, disproven, or simply
        # unverifiable (one side records no NCT at all). The two directions of
        # error are NOT equally bad:
        #   inheriting a REFUSAL without proof  -> we withhold a number we
        #       might have been entitled to publish. Costs coverage.
        #   inheriting an ALLOWANCE or a POLARITY without proof -> we publish
        #       a number, or a benefit/harm reading, on the authority of an
        #       object that may describe different trials. Costs correctness.
        # So a refusal binds on DOUBT, while permission and polarity require
        # PROOF. Without this, 4 of 38 refusals here were being inherited with
        # no overlap at all, purely because one side listed no NCTs.
        if identity_disproven:
            return ("NAME_MATCH_WITHOUT_TRIAL_OVERLAP", OrderedDict([
                ("topic", cand),
                ("sidecar_ncts", sorted(sidecar_ncts)[:8]),
                ("store_ncts", sorted(entry["ncts"])[:8]),
                ("note", "the store object of this name pools DIFFERENT "
                         "trials, so its ruling was not made about this "
                         "evidence and is not applied here"),
            ]))
        refusals = [(n, r) for n, (ref, r, _f) in entry["outcomes"].items() if ref]
        favours = [f for (_ref, _r, f) in entry["outcomes"].values() if f]
        if refusals and len(refusals) == len(entry["outcomes"]):
            return ("REFUSED_BY_STORE", OrderedDict([
                ("topic", cand),
                ("outcomes_refused", len(refusals)),
                ("outcomes_total", len(entry["outcomes"])),
                ("store_reason_verbatim", refusals[0][1]),
                ("trial_overlap", sorted(overlap)[:8]),
                ("identity", "PROVEN by shared trial registration"
                 if identity_proven else
                 "UNVERIFIABLE -- one side records no trial registration, so "
                 "this refusal is inherited on DOUBT. That is the safe "
                 "direction: it withholds a number rather than publishing "
                 "one on an object that may describe other trials."),
            ]))
        if identity_proven:
            return ("ALLOWED", OrderedDict([
                ("topic", cand),
                ("outcomes_refused", len(refusals)),
                ("outcomes_total", len(entry["outcomes"])),
                ("favours", favours[0] if favours else None),
                ("trial_overlap", sorted(overlap)[:8]),
                ("identity", "PROVEN by shared trial registration"),
            ]))
        # Reached only when identity is NOT proven. Permission and polarity
        # require proof; only a refusal is inherited on doubt.
        return ("IDENTITY_UNVERIFIABLE", OrderedDict([
            ("topic", cand),
            ("sidecar_ncts", sorted(sidecar_ncts)[:8]),
            ("store_ncts", sorted(entry["ncts"])[:8]),
            ("note", "a store object of this name does not refuse, but no "
                     "shared trial registration proves it describes this "
                     "evidence. Its permission is NOT inherited and its "
                     "`favours` is NOT used for polarity."),
        ]))
    return ("NO_STORE_ADJUDICATION", OrderedDict([
        ("note", "no store object exists for this page. The store has never "
                 "ruled on this pool. Silence is not permission; this row is "
                 "reported in its own bucket and never counted with pages "
                 "the store has allowed."),
    ]))


# ---------------------------------------------------------------- the sweep

def evaluate_sidecar(path, store):
    stem = os.path.basename(path)[:-5]
    row = OrderedDict(sidecar=stem, source_file=os.path.relpath(path, ROOT))
    try:
        d = json.load(open(path, encoding="utf-8"))
    except Exception as exc:
        row["state"] = "NNT_NOT_COMPUTABLE"
        row["reason"] = "SIDECAR_UNPARSEABLE: %s" % str(exc)[:90]
        return row
    if isinstance(d, dict) is False:
        row["state"] = "NNT_NOT_COMPUTABLE"
        row["reason"] = "SIDECAR_ROOT_NOT_DICT"
        return row
    trials = d.get("trials")
    trials = trials if isinstance(trials, list) else []

    # provenance exclusions, decided on keys and not on the numbers
    if any(isinstance(t, dict) and "hr" in t for t in trials):
        row["state"] = "NNT_NOT_COMPUTABLE"
        row["reason"] = ("PROVENANCE_HAZARD_RATIO: the trial rows carry `hr`, "
                         "so this sidecar was derived from published hazard "
                         "ratios and stores a log HAZARD ratio in a field "
                         "named pooled_logOR. It has no per-arm cells. "
                         "Excluded by provenance, not by inspection.")
        return row
    if any(isinstance(t, dict) and "md" in t for t in trials):
        row["state"] = "NNT_NOT_COMPUTABLE"
        row["reason"] = ("PROVENANCE_MEAN_DIFFERENCE: the trial rows carry "
                         "`md`. A mean difference is not a risk and an NNT "
                         "would need a responder threshold nothing states.")
        return row

    cells = [t for t in trials
             if isinstance(t, dict) and all(k in t for k in ("tE", "tN", "cE", "cN"))]
    if len(cells) == 0:
        row["state"] = "NNT_NOT_COMPUTABLE"
        row["reason"] = ("NO_2X2_CELLS: no trial row carries tE/tN/cE/cN, so "
                         "there is no control-arm risk and no baseline. None "
                         "is substituted from any other source.")
        return row

    ncts = {str(t.get("nct")).upper() for t in cells if t.get("nct")}
    state, detail = adjudicate(stem, ncts, store)
    row["store_adjudication"] = state
    row["store_adjudication_detail"] = detail
    if state == "REFUSED_BY_STORE":
        row["state"] = "REFUSED_BY_STORE"
        row["store_reason_verbatim"] = detail.get("store_reason_verbatim")
        return row

    usable, dropped = [], []
    for t in cells:
        got = rd_and_variance(t.get("tE"), t.get("tN"), t.get("cE"), t.get("cN"))
        if got is None:
            dropped.append(t.get("name") or t.get("nct") or "?")
            continue
        usable.append((t.get("name") or t.get("nct") or "?", got[0], got[1]))
    if dropped:
        row["trials_dropped"] = dropped
    if len(usable) == 0:
        row["state"] = "NNT_NOT_COMPUTABLE"
        row["reason"] = ("NO_USABLE_TRIAL: every trial row was refused by the "
                         "cell check (impossible or empty arms). Dropped: %s"
                         % dropped)
        return row

    cE = sum(t["cE"] for t in cells if isinstance(t.get("cE"), int))
    cN = sum(t["cN"] for t in cells if isinstance(t.get("cN"), int))
    if cN <= 0:
        row["state"] = "NNT_NOT_COMPUTABLE"
        row["reason"] = "BASELINE_DENOMINATOR_ZERO: control arms total %d" % cN
        return row
    baseline = cE / cN

    pooled = pool_rd(usable)
    row["state"] = "COMPUTABLE"
    row["k_used"] = len(usable)
    row["route"] = ("DIRECT FROM THE 2x2 CELLS: the risk difference is pooled "
                    "from the trials' own arms. The pooled odds ratio in this "
                    "sidecar is NOT used and no baseline is assumed.")
    row["baseline_value"] = baseline
    row["baseline_source"] = (
        "CONTROL ARMS OF THE TRIALS IN THIS SIDECAR: %d events in %d "
        "control-arm participants across %d trial(s)." % (cE, cN, len(cells)))
    row["baseline_note"] = (
        "THIS ANSWER IS A FUNCTION OF THIS BASELINE. The same relative effect "
        "at a different baseline gives a different absolute effect -- in this "
        "corpus the dapivirine ring spans roughly 75 woman-years per "
        "infection prevented at trial incidence against roughly 3,370 in a "
        "lower-incidence setting, unchanged risk ratio. The reader supplies "
        "the baseline for their own setting.")
    per_trial = [OrderedDict([("trial", t.get("name") or t.get("nct")),
                              ("control_events", t.get("cE")),
                              ("control_n", t.get("cN")),
                              ("control_risk", t["cE"] / t["cN"]
                               if t.get("cN") else None)])
                 for t in cells if isinstance(t.get("cN"), int) and t["cN"] > 0]
    row["baseline_per_trial"] = per_trial
    risks = [p["control_risk"] for p in per_trial if p["control_risk"] is not None]
    if risks:
        row["baseline_spread"] = OrderedDict([
            ("min", min(risks)), ("max", max(risks)),
            ("fold", (max(risks) / min(risks)) if min(risks) > 0 else None),
            ("note", "the spread the pooled baseline hides")])
    row["pooled_rd"] = pooled
    row.update(nnt_from_rd(pooled["point"], pooled.get("ci_low"),
                           pooled.get("ci_high")))

    fav = (row["store_adjudication_detail"].get("favours")
           if state == "ALLOWED" else None)
    if fav:
        # DERIVING POLARITY, and naming the inference rather than asserting it.
        # `favours` names the arm the store judged better. Combined with the
        # SIGN of the risk difference that fixes whether an event of this
        # outcome is a bad thing or a good one:
        #   favours treatment and FEWER events on treatment -> events are bad
        #   favours treatment and MORE  events on treatment -> events are good
        # The NNT is then readable, and only then.
        f = str(fav).strip().lower()
        rd = pooled["point"]
        side = ("treatment" if "treat" in f or "intervention" in f
                else "control" if "control" in f or "comparator" in f
                or "placebo" in f else None)
        if side is None or rd == 0:
            row["event_polarity"] = "UNKNOWN"
            row["nnt_interpretation"] = (
                "POLARITY_UNKNOWN: the store records favours=%r, which does "
                "not resolve to an arm, so an event cannot be called good or "
                "bad here." % (fav,))
        else:
            favoured_has_fewer = (rd < 0) if side == "treatment" else (rd > 0)
            row["event_polarity"] = "KNOWN"
            row["event_is"] = "HARMFUL" if favoured_has_fewer else "BENEFICIAL"
            row["event_polarity_source"] = (
                "DERIVED, not read: the store records favours=%r for a "
                "matched outcome, and the risk difference computed here is "
                "%+.6f. The favoured arm therefore has %s events, so an "
                "event of this outcome is %s."
                % (fav, rd, "fewer" if favoured_has_fewer else "more",
                   "harmful" if favoured_has_fewer else "beneficial"))
            row["event_polarity_assumption"] = (
                "This assumes the store's `favours` was recorded about the "
                "same outcome as the pool computed here. The trial sets "
                "overlap but are not necessarily identical, so this is an "
                "inference and is labelled as one.")
            row["nnt_interpretation"] = (
                "number needed to treat for one fewer harmful event"
                if favoured_has_fewer else
                "number needed to treat for one additional beneficial event")
    else:
        row["event_polarity"] = "UNKNOWN"
        row["nnt_interpretation"] = (
            "POLARITY_UNKNOWN: nothing available here establishes whether an "
            "event of this outcome is good or bad, so this NNT must not be "
            "read as benefit or as harm. The magnitude and the arithmetic "
            "direction stand; the clinical reading does not.")
    return row


def run(pattern=SIDECARS):
    store, store_dropped = load_store()
    if store_dropped:
        # Surfaced, never swallowed: each of these is a store object whose
        # refusal could not be read, and an unread refusal moves a row toward
        # being computed.
        print("STORE FILES NOT LOADED (each is a hole in the refusal record):")
        for k, v in sorted(store_dropped.items()):
            print("  %-22s %d" % (k, v))
        print("")
    rows = []
    for path in sorted(glob.glob(pattern)):
        if os.path.basename(path).startswith("_"):
            continue
        rows.append(evaluate_sidecar(path, store))
    return rows


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--pattern", default=SIDECARS)
    ap.add_argument("--json-out", default=None)
    ap.add_argument("--limit", type=int, default=12)
    args = ap.parse_args()
    rows = run(args.pattern)

    n = len(rows)
    comp = [r for r in rows if r["state"] == "COMPUTABLE"]
    ref = [r for r in rows if r["state"] == "REFUSED_BY_STORE"]
    notc = [r for r in rows if r["state"] == "NNT_NOT_COMPUTABLE"]
    print("CANDIDATES (sidecar files, excluding leading-underscore): %d" % n)
    print("  COMPUTABLE          %d" % len(comp))
    print("  REFUSED_BY_STORE    %d" % len(ref))
    print("  NNT_NOT_COMPUTABLE  %d" % len(notc))
    ok = len(comp) + len(ref) + len(notc) == n
    print("  identity computable + refused_by_store + not_computable == "
          "candidates : %s (%d + %d + %d == %d)"
          % ("HOLDS" if ok else "FAILS", len(comp), len(ref), len(notc), n))
    print("")
    print("COVERAGE: %d of %d sidecars yield an absolute effect (%.1f%%)."
          % (len(comp), n, 100.0 * len(comp) / n if n else 0.0))
    print("  Denominator NAMED: files matching %s. NOT the topic count and "
          "NOT the store's object count." % args.pattern)
    print("")
    print("STORE ADJUDICATION of the computable rows -- silence is not "
          "permission")
    for k, v in Counter(r.get("store_adjudication") for r in comp).most_common():
        print("  %-34s %d" % (k, v))
    print("")
    print("WHY NOT COMPUTABLE")
    for k, v in Counter(r["reason"].split(":")[0] for r in notc).most_common():
        print("  %-34s %d" % (k, v))
    print("")
    print("POLARITY of the computable rows")
    for k, v in Counter(r.get("event_polarity") for r in comp).most_common():
        print("  %-34s %d" % (k, v))
    print("")
    print("NNT INTERVAL KIND")
    for k, v in Counter(r.get("nnt_ci_kind") for r in comp).most_common():
        print("  %-34s %d" % (k, v))
    print("")
    print("FIRST %d COMPUTED ROWS" % args.limit)
    for r in comp[:args.limit]:
        print("  %-38s k=%-3s baseline %.4f  RD %+.5f  NNT %8.1f  [%s] %s"
              % (r["sidecar"][:38], r["k_used"], r["baseline_value"],
                 r["risk_difference"], r["nnt_magnitude"] or float("nan"),
                 r["nnt_ci_kind"], r["event_polarity"]))
    if args.json_out:
        json.dump(rows, open(args.json_out, "w", encoding="utf-8"),
                  indent=1, ensure_ascii=False)
        print("\nwrote %s" % args.json_out)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
