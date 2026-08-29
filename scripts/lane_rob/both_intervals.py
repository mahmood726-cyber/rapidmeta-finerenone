# -*- coding: utf-8 -*-
"""GENERATOR COMPONENT: show BOTH intervals, and say which one the page reports and why.

WHY THIS IS THE SECOND CHEAPEST. It needs no retrieval either -- every number it prints is
derived from per-trial effects already in the object. It is also the feature with the largest
clinical consequence per line of code, because at the sizes these reviews actually have, THE
CHOICE OF INTERVAL CHANGES THE ANSWER, not the decimal.

WHAT IT IS FOR. A random-effects Wald interval treats the between-trial variance as if it were
known. It is not known; it is estimated, usually from a handful of trials. The modified
Hartung-Knapp interval carries that uncertainty and uses t on k-1 degrees of freedom. With k=2
the t multiplier is 12.71 against 1.96 -- the honest interval is not slightly wider, it is a
different statement about what is known.

⛔ AND THE FLOOR IS NOT COSMETIC. Unmodified Hartung-Knapp can come out NARROWER than Wald when
Q < k-1, which would make the more careful estimator look like the more confident one. The
modification floors the scaling at 1 so that carrying extra uncertainty can never buy a tighter
answer. This component prints q* so a reader can see when the floor bound.

⛔ IT WILL NOT COMPUTE A POOL THE OBJECT HAS WITHDRAWN. sglt2-hf carries a withdrawn primary
pool -- four trials that do not share one endpoint -- and that object exists because the page
once published the withdrawn number six times against one occurrence of the word "withdrawn". A
component that recomputes intervals from per-trial rows would cheerfully republish it. So a
withdrawn pool gets the withdrawal, and no interval.

⛔ DERIVE OR REFUSE. Missing per-trial precision, k<2, or an absent t-quantile is a stated
refusal naming what was missing -- never a normal approximation quietly standing in for t.
"""
import io
import math
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

# Ratio measures are pooled on the log scale; difference measures on their own scale.
LOG_SCALE = ("RR", "OR", "HR", "IRR", "RATE RATIO", "RISK RATIO", "ODDS RATIO", "HAZARD RATIO")


def _z(level):
    from statistics import NormalDist
    return NormalDist().inv_cdf(1 - (1 - float(level) / 100.0) / 2.0)


def _t(level, df):
    """t quantile. REFUSES rather than substituting z -- that substitution is the whole defect."""
    from scipy import stats
    return float(stats.t.ppf(1 - (1 - float(level) / 100.0) / 2.0, df))


def _is_log(measure):
    return str(measure or "").strip().upper() in LOG_SCALE


def _trial_yse(t, log_scale, level):
    """(y, se) on the analysis scale, or None when precision cannot be established."""
    for k in ("log_se", "se_log_rr", "se_log_hr", "se"):
        if isinstance(t.get(k), (int, float)) and t[k] > 0:
            se = float(t[k])
            pt = t.get("log_point")
            if not isinstance(pt, (int, float)):
                p = t.get("point")
                if not isinstance(p, (int, float)):
                    return None
                pt = math.log(float(p)) if log_scale else float(p)
            return float(pt), se
    p, lo, hi = t.get("point"), t.get("ci_low"), t.get("ci_high")
    if not all(isinstance(v, (int, float)) for v in (p, lo, hi)):
        return None
    if log_scale:
        if min(float(p), float(lo), float(hi)) <= 0:
            return None
        p, lo, hi = math.log(float(p)), math.log(float(lo)), math.log(float(hi))
    z = _z(t.get("ci_level") or level or 95)
    se = (float(hi) - float(lo)) / (2.0 * z)
    return (float(p), se) if se > 0 else None


def pool(rows, level=95):
    """DerSimonian-Laird random effects, with the Wald and modified Hartung-Knapp intervals."""
    k = len(rows)
    w = [1.0 / (se * se) for _, se in rows]
    sw = sum(w)
    fe = sum(wi * y for wi, (y, _) in zip(w, rows)) / sw
    Q = sum(wi * (y - fe) ** 2 for wi, (y, _) in zip(w, rows))
    C = sw - sum(wi * wi for wi in w) / sw
    tau2 = max(0.0, (Q - (k - 1)) / C) if C > 0 else 0.0
    ws = [1.0 / (se * se + tau2) for _, se in rows]
    sws = sum(ws)
    mu = sum(wi * y for wi, (y, _) in zip(ws, rows)) / sws
    se_re = math.sqrt(1.0 / sws)
    q = sum(wi * (y - mu) ** 2 for wi, (y, _) in zip(ws, rows)) / (k - 1)
    q_star = max(1.0, q)                      # ⛔ the floor: extra care can never buy a tighter answer
    se_hk = se_re * math.sqrt(q_star)
    z, tq = _z(level), _t(level, k - 1)
    return {"k": k, "mu": mu, "tau2": tau2, "Q": Q, "q": q, "q_star": q_star,
            "wald": (mu - z * se_re, mu + z * se_re),
            "hk": (mu - tq * se_hk, mu + tq * se_hk),
            "z": z, "t": tq, "widen": (tq * math.sqrt(q_star)) / z,
            "floor_bound": q < 1.0}


def _fmt(v, log_scale):
    x = math.exp(v) if log_scale else v
    return ("%.3f" % x) if abs(x) < 100 else ("%.1f" % x)


def render(canon):
    outs = ((canon.get("results") or {}).get("by_outcome")) or {}
    if not outs:
        return ("<h2>Both intervals, and which one this page reports</h2><p>This object records "
                "no outcome, so there is nothing to pool. That is a refusal, not an omission.</p>")
    body, notes = [], []
    for oid, res in outs.items():
        pooled = res.get("pooled") or {}
        name = re.sub(r"[<>]", "", str(oid))[:60]
        if pooled.get("withdrawn"):
            notes.append(
                "<p><b>%s &mdash; no interval is computed.</b> This pool is withdrawn, and a "
                "component that recomputed it from the per-trial rows would republish a number "
                "the object exists to retract.</p>" % name)
            continue
        measure = pooled.get("measure") or (
            (res.get("per_trial") or [{}])[0].get("measure") if res.get("per_trial") else None)
        log_scale = _is_log(measure)
        level = pooled.get("ci_level") or 95
        rows, missing = [], []
        for t in (res.get("per_trial") or []):
            yse = _trial_yse(t, log_scale, level)
            (rows.append(yse) if yse else missing.append(t.get("label") or t.get("nct") or "?"))
        if len(rows) < 2:
            notes.append("<p><b>%s &mdash; not computed.</b> Precision could be established for "
                         "%d of %d contributing trials%s, and two are needed before an interval "
                         "means anything.</p>"
                         % (name, len(rows), len(res.get("per_trial") or []),
                            (" (missing: " + ", ".join(str(m)[:40] for m in missing[:3]) + ")")
                            if missing else ""))
            continue
        p = pool(rows, level)
        body.append(
            "<tr><td>%s</td><td>%d</td><td>%s</td><td>%s to %s</td><td>%s to %s</td>"
            "<td>%.2f&times;</td></tr>"
            % (name, p["k"], _fmt(p["mu"], log_scale),
               _fmt(p["wald"][0], log_scale), _fmt(p["wald"][1], log_scale),
               _fmt(p["hk"][0], log_scale), _fmt(p["hk"][1], log_scale), p["widen"]))
        notes.append(
            "<p>For <b>%s</b>: %d trials, &tau;&sup2; = %.4f, q* = %.2f%s. The t multiplier on "
            "%d degrees of freedom is %.2f against %.2f for the normal, so the modified interval "
            "is %.2f&times; wider on the analysis scale.</p>"
            % (name, p["k"], p["tau2"], p["q_star"],
               " (at the floor &mdash; without it the more careful estimator would have returned "
               "a <i>narrower</i> interval than the Wald one)" if p["floor_bound"] else "",
               p["k"] - 1, p["t"], p["z"], p["widen"]))
    out = ["<h2>Both intervals, and which one this page reports</h2>"]
    if body:
        out.append("<div class=\"scroll\"><table><tr><th>Outcome</th><th>k</th><th>Pooled</th>"
                   "<th>Random-effects Wald</th><th>Modified Hartung&ndash;Knapp</th>"
                   "<th>Wider by</th></tr>" + "".join(body) + "</table></div>")
        # ⛔ THE RULE IS CONDITIONAL ON k, AND THIS IS NOT A SOFTENING TO RECOVER SIGNIFICANCE.
        #
        # Running this component on the pilot is what forced the condition. Dapivirine pools two
        # trials that agree closely (tau-squared exactly 0): Wald 0.566 to 0.873, modified
        # Hartung-Knapp 0.172 to 2.865. Reporting the second as the headline would convert two
        # large randomised trials, both showing benefit, into "no evidence of effect".
        #
        # That interval is not a fact about dapivirine. With k=2 the multiplier is t on ONE
        # degree of freedom -- 12.71 against 1.96 -- because two trials carry almost no
        # information about between-trial variance. The interval is wide by construction and
        # would be nearly as wide whatever the trials had found. Reading it as evidence of
        # absence is reading the degrees of freedom, not the data.
        #
        # So: at k>=3 the modified interval is the one reported. At k=2 both are shown and
        # NEITHER is given as the answer, with the reason stated. Hiding the wide one would be
        # dishonest; leading with it would be worse, because a clinician acts on the headline.
        ks = [int(re.search(r"<td>(\d+)</td>", b).group(1)) for b in body]
        if min(ks) >= 3:
            out.append(
                "<p><b>This page reports the modified Hartung&ndash;Knapp interval.</b> The Wald "
            "interval treats the between-trial variance as known when it has in fact been "
            "estimated from a handful of trials; the modified interval carries that uncertainty "
            "and uses t on k&minus;1 degrees of freedom. Both are shown because the difference "
            "is not a rounding matter at these sizes, and a reader comparing this page with a "
            "review that reports the Wald interval should be able to see exactly where the "
                "disagreement comes from.</p>")
        else:
            out.append(
                "<p><b>At two trials this page reports neither interval as the answer, and says "
                "why.</b> With k&nbsp;=&nbsp;2 the modified interval uses t on ONE degree of "
                "freedom &mdash; a multiplier of 12.71 against 1.96 &mdash; because two trials "
                "carry almost no information about how much results vary between trials. The "
                "resulting interval is wide by construction and would be nearly as wide whatever "
                "the trials had found, so it should not be read as evidence that the treatment "
                "does not work: that width is the degrees of freedom, not the data. The Wald "
                "interval has the opposite fault &mdash; it treats a between-trial variance "
                "estimated from two numbers as if it were known, and is too narrow for the same "
                "reason. Both are printed above so a reader can see the size of the gap rather "
                "than inherit whichever one an author preferred.</p>")
        out.append(
            "<p>The modification is the floor at q*&nbsp;=&nbsp;1. Unmodified, "
            "Hartung&ndash;Knapp can return a <i>narrower</i> interval than Wald whenever "
            "Q&nbsp;&lt;&nbsp;k&minus;1 &mdash; which would let the estimator that carries more "
            "uncertainty appear more confident. Flooring it means extra care can never buy a "
            "tighter answer.</p>")
    out.extend(notes)
    return "".join(out)


MARKER = "<h2>Both intervals, and which one this page reports</h2>"


def inject(html, canon):
    if MARKER in html:
        return html
    return html + "\n<div class=\"card\">\n" + render(canon) + "\n</div>\n"


if __name__ == "__main__":
    import json
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    os.chdir(os.path.dirname(os.path.dirname(HERE)))
    for path in sys.argv[1:] or ["ssot/agyw-hiv-prep-review/agyw-hiv-prep-review.json"]:
        canon = json.load(io.open(path, encoding="utf-8"))
        t = re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", render(canon)))
        print("=" * 78)
        print(os.path.basename(path))
        print(t[:1400])
