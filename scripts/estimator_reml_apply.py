"""APPLY THE ESTIMATOR DECISION -- one rule corpus-wide, with the change announced.

DECIDED against Cochrane Handbook 6.5 (2024), section 10.10.4.4, verified live on
2026-08-18:

    "In RevMan, the default option for estimating the between-study variance is REML,
     while the DerSimonian and Laird moment-based method remains an available option."

    "Several simulation studies have concluded that an approach proposed by Paule and
     Mandel should be recommended; whereas a comprehensive recent simulation study
     recommended the REML approach, although noted that no single approach is
     universally preferable."

WHY ONE RULE AND NOT TWO. The corpus was ALREADY MIXED -- ARNI publishes the REML
value (0.8715; its DL value is 0.8835) while other objects publish DL. So the choice
was never between changing and not changing. It was between one estimator and two.

EVERY MOVED VALUE IS ANNOUNCED. `display_change_announced` is UNENFORCEABLE by
construction -- no artefact can show that a change was announced to a reader -- so it
is a rule with a named owner. This script writes the announcement INTO the object so
the obligation is at least recorded where the value lives.

  --report   measure only, change nothing
  --apply    write REML values and the announcement
"""
from __future__ import annotations
import glob
import io
import json
import math
import os
import sys

if __name__ == "__main__":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
HANDBOOK_SECTION = "Cochrane Handbook 6.5 (2024) section 10.10.4.4"


def dl_tau2(y, v):
    w = [1.0 / x for x in v]
    sw = sum(w)
    mu = sum(wi * yi for wi, yi in zip(w, y)) / sw
    q = sum(wi * (yi - mu) ** 2 for wi, yi in zip(w, y))
    k = len(y)
    c = sw - sum(wi * wi for wi in w) / sw
    if c <= 0:
        return 0.0, q
    return max(0.0, (q - (k - 1)) / c), q


def reml_tau2(y, v, iters=200, tol=1e-12):
    """Iterative REML for the random-effects between-study variance.

    Standard fixed-point iteration (Viechtbauer 2005). Starts from DL, which is the
    usual choice, and is clamped at zero -- a negative variance is not a variance.
    """
    t2, _ = dl_tau2(y, v)
    k = len(y)
    if k < 2:
        return 0.0
    for _ in range(iters):
        w = [1.0 / (vi + t2) for vi in v]
        sw = sum(w)
        mu = sum(wi * yi for wi, yi in zip(w, y)) / sw
        num = sum((wi ** 2) * ((yi - mu) ** 2 - vi) for wi, yi, vi in zip(w, y, v))
        num += sum(wi * wi for wi in w) / sw          # REML correction term
        den = sum(wi ** 2 for wi in w)
        new = max(0.0, num / den) if den > 0 else 0.0
        if abs(new - t2) < tol:
            t2 = new
            break
        t2 = new
    return t2


def pool(y, v, t2):
    w = [1.0 / (vi + t2) for vi in v]
    sw = sum(w)
    mu = sum(wi * yi for wi, yi in zip(w, y)) / sw
    se = math.sqrt(1.0 / sw)
    return mu, se


def per_trial_data(blk):
    """(log estimates, variances) from the object's own stored per-trial values."""
    y, v = [], []
    for r in blk.get("per_trial") or []:
        if not isinstance(r, dict):
            continue
        lp, ls = r.get("log_point"), r.get("log_se")
        if lp is None or ls is None or ls == 0:
            return None, None
        y.append(float(lp))
        v.append(float(ls) ** 2)
    if len(y) < 2:
        return None, None
    return y, v


def objects():
    for p in sorted(glob.glob(os.path.join(REPO, "ssot", "*", "*.json"))):
        if os.path.basename(p)[:-5] != os.path.basename(os.path.dirname(p)):
            continue
        yield p


def survey():
    rows = []
    for path in objects():
        try:
            obj = json.load(io.open(path, encoding="utf-8"))
        except Exception:
            continue
        for oid, blk in ((obj.get("results") or {}).get("by_outcome") or {}).items():
            if not isinstance(blk, dict):
                continue
            pooled = blk.get("pooled")
            if not isinstance(pooled, dict) or pooled.get("point") is None:
                continue
            y, v = per_trial_data(blk)
            if y is None:
                rows.append((path, oid, blk, None))
                continue
            rows.append((path, oid, blk, (y, v)))
    return rows


def main() -> int:
    apply_it = "--apply" in sys.argv
    rows = survey()
    print("live pools found: %d" % len(rows))
    print()
    moved, same, unreadable = [], [], []
    for path, oid, blk, data in rows:
        name = os.path.basename(path)[:-5]
        if data is None:
            unreadable.append((name, oid))
            continue
        y, v = data
        t2_dl, _ = dl_tau2(y, v)
        t2_re = reml_tau2(y, v)
        mu_dl, se_dl = pool(y, v, t2_dl)
        mu_re, se_re = pool(y, v, t2_re)
        cur = float(blk["pooled"]["point"])
        p_dl, p_re = math.exp(mu_dl), math.exp(mu_re)
        lo_re, hi_re = math.exp(mu_re - 1.96 * se_re), math.exp(mu_re + 1.96 * se_re)
        shift = abs(p_re - cur) / cur * 100 if cur else 0.0
        rec = dict(name=name, oid=oid, k=len(y), cur=cur, dl=p_dl, reml=p_re,
                   lo=lo_re, hi=hi_re, t2_dl=t2_dl, t2_re=t2_re, shift=shift,
                   blk=blk, path=path, tau2_differs=abs(t2_re - t2_dl) > 1e-9)
        # A DIFFERENCE IS ONLY AN ESTIMATOR DIFFERENCE IF TAU-SQUARED MOVED.
        # Four pools showed a shift of 0.005-0.019% with tau2 = 0 under BOTH
        # estimators. With tau2 identical the two estimators give the SAME pooled
        # value by construction, so that shift is recomputation noise from stored,
        # rounded log_point/log_se -- not an effect of the estimator. Overwriting a
        # published number with recomputation noise would be a worse error than
        # leaving it, and it would be announced as an estimator change it is not.
        if shift > 0.005 and rec["tau2_differs"]:
            moved.append(rec)
        else:
            same.append(rec)

    print("%-34s %-26s %2s %-11s %-11s %7s" %
          ("object", "outcome", "k", "published", "REML", "shift%"))
    print("-" * 100)
    for r in sorted(moved, key=lambda x: -x["shift"]):
        print("%-34s %-26s %2d %-11.6g %-11.6g %6.3f%%  tau2 %.5f -> %.5f"
              % (r["name"][:33], r["oid"][:25], r["k"], r["cur"], r["reml"],
                 r["shift"], r["t2_dl"], r["t2_re"]))
    noise = [r for r in same if r["shift"] > 0.005 and not r["tau2_differs"]]
    if noise:
        print()
        print("NOT APPLIED -- tau-squared is IDENTICAL under both estimators (zero), so")
        print("the estimator changes nothing and the small difference is recomputation")
        print("noise from stored rounded inputs. The published value stands:")
        for r in noise:
            print("    %-34s %-24s k=%d  %.6g vs %.6g  (%.3f%%)"
                  % (r["name"][:33], r["oid"][:23], r["k"], r["cur"], r["reml"], r["shift"]))
    print()
    print("pools whose published value MOVES BECAUSE OF THE ESTIMATOR : %d" % len(moved))
    print("pools unchanged                   : %d" % len(same))
    print("pools whose per-trial data cannot be read (no log_point/log_se): %d"
          % len(unreadable))
    for n, o in unreadable:
        print("    %-34s %s" % (n, o))

    crossers = [r for r in moved
                if (r["lo"] - 1) * (r["hi"] - 1) < 0 != ((r["cur"] - 1) < 0)]
    print()
    print("CONCLUSION CHANGES (an interval that crossed 1 stops crossing, or starts): "
          "checked per pool below")
    flipped = 0
    for r in moved:
        pooled = r["blk"]["pooled"]
        old_lo, old_hi = pooled.get("ci_low"), pooled.get("ci_high")
        if old_lo is None or old_hi is None:
            continue
        was = (float(old_lo) - 1) * (float(old_hi) - 1) < 0
        now = (r["lo"] - 1) * (r["hi"] - 1) < 0
        if was != now:
            flipped += 1
            print("    !!! %s %s: crossed-one %s -> %s" % (r["name"], r["oid"], was, now))
    print("    conclusion changes: %d" % flipped)

    if not apply_it:
        print()
        print("REPORT ONLY. Re-run with --apply to write.")
        return 0

    if flipped:
        raise SystemExit("REFUSING to apply: %d pool(s) change conclusion. That is a "
                         "finding and needs a human, not a sweep." % flipped)

    by_path = {}
    for r in moved:
        by_path.setdefault(r["path"], []).append(r)
    for path, recs in by_path.items():
        obj = json.load(io.open(path, encoding="utf-8"))
        for r in recs:
            blk = obj["results"]["by_outcome"][r["oid"]]
            p = blk["pooled"]
            before = {"point": p.get("point"), "ci_low": p.get("ci_low"),
                      "ci_high": p.get("ci_high"),
                      "estimator": blk.get("estimator") or blk.get("estimator_used")}
            p["point"], p["ci_low"], p["ci_high"] = r["reml"], r["lo"], r["hi"]
            blk["estimator"] = "REML (restricted maximum likelihood)"
            blk["estimator_used"] = "REML (restricted maximum likelihood)"
            blk["display_change_announced"] = {
                "changed_utc": "2026-08-18",
                "what_changed": (
                    "The between-study variance estimator moved from DerSimonian-Laird "
                    "to REML, so the pooled point estimate and its interval both move."),
                "from": before,
                "to": {"point": r["reml"], "ci_low": r["lo"], "ci_high": r["hi"],
                       "estimator": "REML (restricted maximum likelihood)"},
                "shift_percent": round(r["shift"], 4),
                "tau2": {"dersimonian_laird": r["t2_dl"], "reml": r["t2_re"]},
                "conclusion_unchanged": True,
                "authority": HANDBOOK_SECTION,
                "why": (
                    "REML is Cochrane's own current default and the Handbook states that "
                    "'no single approach is universally preferable'. THE CORPUS WAS "
                    "ALREADY MIXED -- ARNI published the REML value while others published "
                    "DL -- so this was never a choice between changing and not changing, "
                    "it was a choice between one estimator and two."),
                "a_reader_who_wrote_down_the_old_value": (
                    "The previous value is recorded above in full. A reader who noted the "
                    "old number can see exactly what it was, what it is now, and why -- "
                    "which is the whole point of announcing a display change rather than "
                    "letting a refinement look like a retraction."),
            }
        io.open(path, "w", encoding="utf-8").write(
            json.dumps(obj, ensure_ascii=False, indent=1))
        print("wrote %d pool(s) into %s" % (len(recs), os.path.basename(path)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
