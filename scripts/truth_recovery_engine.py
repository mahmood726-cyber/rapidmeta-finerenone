#!/usr/bin/env python
"""
truth_recovery_engine.py — make the Unified truth-recovery (honest coverage) estimator
AVAILABLE as a selectable pooling engine in the RapidMeta pipeline, and FLAG (never
overwrite) any published headline it would materially change.

The estimator itself is packaged in allmeta (engines/truth_recovery). This script is the
RapidMeta-side adapter:

    # selectable engine on one app's study-level inputs (log effect + SE):
    python scripts/truth_recovery_engine.py estimate --yi 0.58,1.03,3.82 --si 0.30,0.21,1.01

    # FLAG report: re-pool every poolable published app through the engine and diff the
    # headline vs the published number. Writes TRUTH_RECOVERY_FLAGGED.md. Changes NOTHING.
    python scripts/truth_recovery_engine.py repool-flag

TRUTH-FIRST CONTRACT
--------------------
* This script NEVER edits a generated paper, dashboard, findings JSON, or any published
  artifact. Its only output is the flag report (a new file) + stdout.
* The published numbers are pooled on a LOG-ODDS / LOG-RR / LOG-HR scale. The Unified
  engine's NPE component is amortized on a simulation DGP (generic effect scale,
  mu~0.3, tau2~0.05); on the real ratio-measure domain it is OUT OF DISTRIBUTION. So:
    - A unified POINT shift on this domain is a FLAG FOR HUMAN REVIEW, not a verified
      de-biasing — the classical estimate is usually the more trustworthy point here.
    - The honest INTERVAL leans on the Manski partial-identification backstop and is
      wider by design; interval-widening alone is EXPECTED and is reported separately,
      not as "the published result is wrong".
  Mahmood decides what (if anything) to change.
"""

import argparse
import json
import math
import os
import sys

# --- locate the packaged engine (no hardcoded single drive; env override first) -----
_CANDIDATES = [
    os.environ.get("TRUTH_RECOVERY_HOME"),
    r"F:\allmeta\engines",
    r"C:\allmeta\engines",
    os.path.join(os.path.dirname(__file__), "..", "..", "allmeta", "engines"),
]
for _c in _CANDIDATES:
    if _c and os.path.isdir(os.path.join(_c, "truth_recovery")):
        if _c not in sys.path:
            sys.path.insert(0, _c)
        break
try:
    import truth_recovery as TR
except Exception as e:  # fail closed, loudly
    sys.stderr.write(
        "ERROR: cannot import the packaged truth_recovery engine.\n"
        "Set TRUTH_RECOVERY_HOME to the allmeta 'engines' dir (the one containing "
        "truth_recovery/), e.g.\n    set TRUTH_RECOVERY_HOME=F:\\allmeta\\engines\n"
        f"(import error: {e})\n")
    sys.exit(2)

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)
POOLCHECK = os.path.join(REPO, "outputs", "poolcheck_input.json")
FINDINGS = os.path.join(REPO, "findings")
REPORT = os.path.join(REPO, "TRUTH_RECOVERY_FLAGGED.md")
AUDIT_JSON = os.path.join(REPO, "outputs", "truth_recovery_repool.json")

# Material-change thresholds (on the ratio scale unless noted).
POINT_REL = 0.10          # >10% relative change in the headline point estimate
CI_REL = 0.25             # >25% change in a CI bound (interval-shift, secondary)


def _exp(x):
    return math.exp(x) if (x is not None and math.isfinite(x)) else float("nan")


def estimate_logscale(yi, si):
    """Run the unified engine on (log effect, SE). Returns the engine dict + ratio views."""
    vi = [s * s for s in si]
    r = TR.estimate(yi, vi)
    r["ratio_point"] = _exp(r["point"])
    r["ratio_ci_lo"] = _exp(r["ci_lo"])
    r["ratio_ci_hi"] = _exp(r["ci_hi"])
    r["ratio_pid_lo"] = _exp(r["partial_id"]["ci_lo"])
    r["ratio_pid_hi"] = _exp(r["partial_id"]["ci_hi"])
    return r


def _components_once(yi, si):
    """Single-pass unified estimate for the bulk re-pool.

    Identical math to truth_recovery.estimate()/unified.unified() (mode=gated,
    npe_scale=1.15) but calls NPE and PartialID exactly ONCE each (the bulk diff over
    ~1158 apps would otherwise pay for them twice). Returns the headline interval, the
    component intervals, and the gate flag.
    """
    import numpy as np
    unified, sbi, rs, methods = TR._load_vendor()
    y = np.asarray(yi, float)
    v = np.asarray([s * s for s in si], float)
    a = sbi.npe(y, v)          # NPE component
    b = rs.partial_id(y, v)    # PartialID component
    scale = TR.UNIFIED_NPE_SCALE_DEFAULT
    a_ok = a.get("ok", False) and np.isfinite(a.get("mu", np.nan))
    b_ok = b.get("ok", False) and np.isfinite(b.get("mu", np.nan))
    gate_fired = False
    if a_ok and b_ok:
        a_lo, a_hi = unified._scale_iv(a["mu"], a["ci_lo"], a["ci_hi"], scale)
        gate_fired = bool((b["mu"] < a_lo) or (b["mu"] > a_hi))
        if gate_fired:
            lo, hi = min(a_lo, b["ci_lo"]), max(a_hi, b["ci_hi"])
        else:
            lo, hi = a_lo, a_hi
        mu = float(min(max(a["mu"], lo), hi))
        tau2 = a.get("tau2", b.get("tau2", np.nan))
    elif a_ok:
        lo, hi, mu, tau2 = a["ci_lo"], a["ci_hi"], a["mu"], a.get("tau2", np.nan)
    elif b_ok:
        lo, hi, mu, tau2 = b["ci_lo"], b["ci_hi"], b["mu"], b.get("tau2", np.nan)
    else:
        re = methods.reml(y, v)
        lo, hi, mu, tau2 = re["ci_lo"], re["ci_hi"], re["mu"], re.get("tau2", np.nan)
    return {
        "point": float(mu), "ci_lo": float(lo), "ci_hi": float(hi),
        "tau2": float(tau2), "gate_fired": gate_fired,
        "npe": {"mu": float(a.get("mu", np.nan)), "ci_lo": float(a.get("ci_lo", np.nan)),
                "ci_hi": float(a.get("ci_hi", np.nan)), "ok": bool(a_ok)},
        "partial_id": {"ci_lo": float(b.get("ci_lo", np.nan)),
                       "ci_hi": float(b.get("ci_hi", np.nan)), "ok": bool(b_ok)},
        "ratio_point": _exp(mu), "ratio_ci_lo": _exp(lo), "ratio_ci_hi": _exp(hi),
    }


def _classical_hksj(yi, si):
    """Classical comparator from allmeta's audited kernel (DL-HKSJ, t_{k-1}, Q-floor).

    This is the 'old engine' baseline computed from the SAME inputs, so a diff isolates
    the effect of the engine choice. Uses the vendored methods.hksj.
    """
    unified, sbi, rs, methods = TR._load_vendor()
    import numpy as np
    h = methods.hksj(np.asarray(yi, float), np.asarray([s * s for s in si], float))
    return {
        "point": float(h.get("mu", float("nan"))),
        "ci_lo": float(h.get("ci_lo", float("nan"))),
        "ci_hi": float(h.get("ci_hi", float("nan"))),
        "ok": bool(h.get("ok", False)),
    }


def _crosses_null_log(ci_lo, ci_hi):
    """On the log scale the null effect is 0 (ratio 1)."""
    return (ci_lo is not None and ci_hi is not None
            and math.isfinite(ci_lo) and math.isfinite(ci_hi)
            and ci_lo <= 0.0 <= ci_hi)


def _published_or(app):
    fj = os.path.join(FINDINGS, app.replace(".html", ".json"))
    if not os.path.exists(fj):
        return None
    try:
        st = json.load(open(fj, encoding="utf-8")).get("state") or {}
    except Exception:
        return None
    o = st.get("or")
    try:
        return float(o)
    except (TypeError, ValueError):
        return None


# Minimum k at which the classical DL-HKSJ comparator is non-degenerate enough to
# trust a significance verdict: at k=2 the t_{k-1}=t_1 critical value (~12.7) plus the
# HKSJ inflation produces astronomically wide CIs that trivially include the null, so a
# "gains significance" verdict there reflects the COMPARATOR blowing up, not the
# published result. We only assert a significance FLIP at k>=K_SIG_MIN.
K_SIG_MIN = 5
# A classical CI whose log-width exceeds this is treated as degenerate (no usable
# significance verdict regardless of k).
CLASSICAL_LOGWIDTH_MAX = 8.0   # ratio-scale factor e^8 ~ 3000x; beyond this is unusable


def repool_flag(limit=None):
    inp = json.load(open(POOLCHECK, encoding="utf-8"))
    apps = list(inp.items())
    if limit:
        apps = apps[:limit]

    total = len(apps)
    processed = skipped = 0
    records = []          # every re-pooled app (for the JSON audit dump)
    failed = []

    for app, v in apps:
        yi, si, k = v.get("yi"), v.get("si"), v.get("k", 0)
        py_est = v.get("py_est")
        if not yi or not si or k < 2 or len(yi) != len(si):
            skipped += 1
            continue
        if not all(math.isfinite(y) for y in yi) or not all(s > 0 for s in si):
            skipped += 1
            continue
        try:
            u = _components_once(yi, si)
            c = _classical_hksj(yi, si)
        except Exception as e:
            failed.append((app, str(e)))
            continue
        processed += 1
        if processed % 100 == 0:
            sys.stderr.write(f"  ...re-pooled {processed}/{total}\n"); sys.stderr.flush()

        # Published headline point = the actual published OR/RR/HR if present, else
        # poolcheck's own pooled point (py_est) which reproduces it closely.
        pub_or = _published_or(app)
        pub_point = pub_or if (pub_or is not None) else (py_est if isinstance(py_est, (int, float)) else None)

        # POINT change vs the PUBLISHED number (this is "would it change the headline").
        dlog_pub = (abs(u["point"] - math.log(pub_point))
                    if (pub_point is not None and pub_point > 0) else float("nan"))
        point_shift = math.isfinite(dlog_pub) and dlog_pub > math.log(1 + POINT_REL)

        # SIGNIFICANCE flip — only trusted where the classical comparator is non-degenerate.
        c_logwidth = (c["ci_hi"] - c["ci_lo"]) if (math.isfinite(c["ci_lo"]) and math.isfinite(c["ci_hi"])) else float("inf")
        classical_usable = (k >= K_SIG_MIN) and (c_logwidth <= CLASSICAL_LOGWIDTH_MAX)
        c_sig = not _crosses_null_log(c["ci_lo"], c["ci_hi"])
        u_sig = not _crosses_null_log(u["ci_lo"], u["ci_hi"])
        sig_flip = bool(classical_usable and (c_sig != u_sig))

        # Tiering. Tier A = actionable: published number present, k>=K_SIG_MIN, and a real
        # divergence. Tier B = flagged but driven by small-k / point-only (lower priority,
        # NPE OOD-dominated). widened-only is neither (expected interval widening).
        flagged_any = point_shift or sig_flip
        tier = None
        if flagged_any:
            tier = "A" if (pub_point is not None and k >= K_SIG_MIN) else "B"

        rec = {
            "app": app, "k": k,
            "published_point": pub_point, "published_or_source": "findings" if pub_or is not None else "py_est",
            "classical_point": _exp(c["point"]), "classical_ci": [_exp(c["ci_lo"]), _exp(c["ci_hi"])],
            "classical_usable_sig": classical_usable,
            "unified_point": u["ratio_point"], "unified_ci": [u["ratio_ci_lo"], u["ratio_ci_hi"]],
            "unified_sig": u_sig, "classical_sig": c_sig if classical_usable else None,
            "gate_fired": u["gate_fired"], "npe_ok": u["npe"]["ok"],
            "point_shift_vs_published": point_shift, "sig_flip": sig_flip,
            "dlog_vs_published": dlog_pub if math.isfinite(dlog_pub) else None,
            "tier": tier,
        }
        records.append(rec)

    tierA = [r for r in records if r["tier"] == "A"]
    tierB = [r for r in records if r["tier"] == "B"]
    widened = sum(1 for r in records if r["tier"] is None
                  and math.isfinite(r["classical_ci"][0] or float("nan")))
    # order each tier: sig-flips first, then largest point divergence
    keyf = lambda r: (not r["sig_flip"], -(r["dlog_vs_published"] or 0))
    tierA.sort(key=keyf); tierB.sort(key=keyf)

    # full per-app audit dump (reproducible, machine-readable)
    dump = AUDIT_JSON
    try:
        with open(dump, "w", encoding="utf-8") as fh:
            json.dump({"counts": {"total": total, "processed": processed, "tierA": len(tierA),
                                  "tierB": len(tierB)}, "records": records}, fh, indent=1)
    except Exception:
        dump = None

    _write_report(total, processed, skipped, failed, tierA, tierB, dump)
    return {"total": total, "processed": processed, "skipped": skipped,
            "failed": len(failed), "tierA_actionable": len(tierA), "tierB_lowpriority": len(tierB),
            "report": REPORT, "audit_json": dump}


def _fmt(x, d=3):
    return f"{x:.{d}f}" if (x is not None and isinstance(x, (int, float)) and math.isfinite(x)) else "—"


def _flag_label(r):
    flag = []
    if r["sig_flip"]:
        flag.append("**SIG-FLIP** " + ("(loses sig)" if r["classical_sig"] and not r["unified_sig"]
                                       else "(gains sig)"))
    if r["point_shift_vs_published"] and r["dlog_vs_published"]:
        flag.append("point %+.0f%% vs published" % ((math.exp(r["dlog_vs_published"]) - 1) * 100))
    return "; ".join(flag) or "—"


def _row(r):
    uci = f"[{_fmt(r['unified_ci'][0])}, {_fmt(r['unified_ci'][1])}]"
    return (f"| {r['app'].replace('.html','')} | {r['k']} | {_fmt(r['published_point'],2)} "
            f"| {_fmt(r['unified_point'])} {uci} | {_flag_label(r)} "
            f"| {'yes' if r['gate_fired'] else '·'} | {'ok' if r['npe_ok'] else 'fallback'} |\n")


def _write_report(total, processed, skipped, failed, tierA, tierB, dump):
    L = []
    L.append("# Unified truth-recovery — flagged published numbers (for Mahmood's decision)\n")
    L.append("> **Nothing here has been changed.** Read-only diff: each poolable published app's\n"
             "> *own* study-level inputs were re-pooled through the Unified truth-recovery engine\n"
             "> and compared to the **published** OR/RR/HR. Listed = where the engine WOULD\n"
             "> change the headline. Mahmood decides what, if anything, to change.\n")
    L.append("\n## Read this first — why the engine diverges so often here, and what to trust\n")
    L.append("- **This corpus is the engine's out-of-distribution regime.** Published pooling is on\n"
             "  a **log-OR / log-RR / log-HR** scale with often-large effects; the engine's NPE\n"
             "  component is amortized on a simulation DGP (generic effect scale, mu~0.3, tau2~0.05).\n"
             "  So the NPE **point** is systematically pulled toward its training prior here -- a\n"
             "  *flag for review*, **NOT** a verified de-biasing. On this domain the **published /\n"
             "  classical point is the more trustworthy one**; the engine's trustworthy output is\n"
             "  the honest **interval** (which leans on the Manski partial-ID backstop), not the point.\n")
    L.append("- **Do not read the raw flag count as 'N published results are wrong.'** It mostly\n"
             "  reflects the expected NPE OOD point pull, plus small-k instability in any classical\n"
             "  comparator (at k=2 the DL-HKSJ t1 CI explodes to e.g. [0, 1e12], so a 'gains\n"
             "  significance' there is the comparator blowing up, not a real change). Significance\n"
             f"  flips are therefore only asserted at **k>={K_SIG_MIN}** with a non-degenerate comparator.\n")
    L.append("- `gate_fired` = the partial-ID backstop actively widened the interval (genuine\n"
             "  selection/ambiguity signal -- most worth a look). `NPE=fallback` = the NPE could\n"
             "  not run and the engine fell back (treat with extra care).\n")
    L.append("\n## Counts\n")
    L.append(f"- Poolable apps re-pooled: **{processed}** / {total} considered "
             f"(skipped {skipped}, engine failures {len(failed)}).\n")
    nA_flip = sum(1 for r in tierA if r["sig_flip"])
    L.append(f"- **Tier A -- actionable (k>={K_SIG_MIN}, published number present, real divergence): "
             f"{len(tierA)}**, of which significance flips: **{nA_flip}**.\n")
    L.append(f"- Tier B -- lower-priority (small-k and/or point-only, NPE-OOD-dominated): **{len(tierB)}**.\n")
    rest = processed - len(tierA) - len(tierB)
    L.append(f"- The remaining ~{rest} apps agree within {int(POINT_REL*100)}% of the published point "
             f"(interval may still widen by design).\n")
    if dump:
        L.append(f"- Full per-app audit (all {processed} apps, machine-readable): "
                 f"`outputs/{os.path.basename(dump)}`.\n")

    L.append(f"\n## Tier A -- actionable, review these first ({len(tierA)})\n")
    L.append("| App | k | Published | Unified [honest 95%] | Flag | gate | NPE |\n")
    L.append("|---|---|---|---|---|---|---|\n")
    for r in tierA:
        L.append(_row(r))

    L.append(f"\n## Tier B -- lower priority ({len(tierB)} total; top 40 by divergence shown)\n")
    L.append("_Small-k and/or point-only divergences, dominated by the NPE OOD pull described above. "
             "The published/classical point is usually the more reliable one here._\n\n")
    L.append("| App | k | Published | Unified [honest 95%] | Flag | gate | NPE |\n")
    L.append("|---|---|---|---|---|---|---|\n")
    for r in tierB[:40]:
        L.append(_row(r))

    if failed:
        L.append("\n## Engine failures\n")
        for app, err in failed[:50]:
            L.append(f"- {app}: {err}\n")
    L.append(f"\n_Engine: truth_recovery v{TR.__version__}, config "
             f"{TR.info()['config']}. Comparator: published OR/RR/HR (fallback: poolcheck py_est). "
             f"Generated read-only; no published artifact modified._\n")
    with open(REPORT, "w", encoding="utf-8") as fh:
        fh.write("".join(L))


def _cmd_estimate(args):
    yi = [float(x) for x in args.yi.split(",")]
    si = [float(x) for x in args.si.split(",")]
    r = estimate_logscale(yi, si)
    print(json.dumps(r, indent=2))


def _cmd_repool(args):
    res = repool_flag(limit=args.limit)
    print(json.dumps(res, indent=2))
    print(f"\nReport written to {res['report']}  (nothing else was modified)", file=sys.stderr)


def main(argv=None):
    p = argparse.ArgumentParser(description="Unified truth-recovery engine adapter for RapidMeta")
    sub = p.add_subparsers(dest="cmd", required=True)
    pe = sub.add_parser("estimate", help="run the engine on one app's (yi, si)")
    pe.add_argument("--yi", required=True, help="comma-separated log effects")
    pe.add_argument("--si", required=True, help="comma-separated standard errors")
    pe.set_defaults(func=_cmd_estimate)
    pr = sub.add_parser("repool-flag", help="re-pool all poolable published apps and flag diffs")
    pr.add_argument("--limit", type=int, default=None, help="cap apps (debug)")
    pr.set_defaults(func=_cmd_repool)
    args = p.parse_args(argv)
    args.func(args)


if __name__ == "__main__":
    main()
