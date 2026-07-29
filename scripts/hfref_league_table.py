"""Build the HFrEF GDMT league table from the serialised netmeta covariance.

Reads  outputs/hfref_nma_bundle.json   (written by scripts/hfref_league_bundle.R)
Writes outputs/hfref_league_table.json
       outputs/hfref_league_table.md

Every cell carries a REAL point estimate and a REAL interval, both derived from
the basic-parameter covariance the R bundle exports:

    log RR(A vs B) = d_A - d_B
    Var(A - B)     = Cov[A,A] + Cov[B,B] - 2*Cov[A,B]
    95% CI         = exp( (d_A - d_B) -/+ ci_multiplier * sqrt(Var) )

where ci_multiplier is the HKSJ-corrected t critical value the settled fit
applied (sqrt(q) * t_df), not a normal quantile.

The contrast count is COUNTED, never asserted. A contrast is reported as
estimable only if its variance is finite and strictly positive; anything else is
listed as non-estimable with the reason. No padding to a target count.
"""

import io
import json
import math
import os
import sys

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
BUNDLE = os.path.join(ROOT, "outputs", "hfref_nma_bundle.json")
OUT_JSON = os.path.join(ROOT, "outputs", "hfref_league_table.json")
OUT_MD = os.path.join(ROOT, "outputs", "hfref_league_table.md")

# Anchor re-checked here too: stage 2 must not be able to publish a table built
# on a bundle whose anchor did not hold.
ANCHOR = {
    "ACEI+BB+MRA": (0.59333495, 0.348, 1.011),
    "ACEI+BB": (0.64459765, 0.433, 0.959),
}
ANCHOR_TAU2 = 0.02323609


def load_bundle():
    with open(BUNDLE, encoding="utf-8") as fh:
        b = json.load(fh)
    if not b.get("anchor", {}).get("pass"):
        raise SystemExit("REFUSING: bundle anchor did not pass")
    if not b.get("covariance_cross_check", {}).get("pass"):
        raise SystemExit("REFUSING: bundle covariance cross-check did not pass")
    return b


def recheck_anchor(nodes_vs_ref, tau2):
    """Independently re-derive the anchor from the covariance we are about to use."""
    rows, ok = [], True
    for node, (rr, lo, hi) in ANCHOR.items():
        got = nodes_vs_ref[node]
        good = (
            abs(got["rr"] - rr) < 1e-8
            and abs(got["lo"] - lo) < 5e-4
            and abs(got["hi"] - hi) < 5e-4
        )
        ok = ok and good
        rows.append(
            {
                "node": node,
                "expected": [rr, lo, hi],
                "observed": [got["rr"], got["lo"], got["hi"]],
                "pass": good,
            }
        )
    tau_ok = abs(tau2 - ANCHOR_TAU2) < 1e-8
    ok = ok and tau_ok
    rows.append(
        {
            "node": "tau2",
            "expected": [ANCHOR_TAU2],
            "observed": [tau2],
            "pass": tau_ok,
        }
    )
    return ok, rows


def main():
    b = load_bundle()
    bp = b["basic_parameters"]
    order = bp["order"]
    d = {t: v for t, v in zip(order, bp["log_rr"])}
    cov = {a: {c: bp["cov"][i][j] for j, c in enumerate(order)} for i, a in enumerate(order)}
    ref = bp["reference"]
    mult = b["model"]["ci_multiplier"]

    # reference node is the zero of the scale, with zero variance by construction
    nodes = list(order) + [ref]
    d[ref] = 0.0
    for a in nodes:
        cov.setdefault(a, {})
        for c in nodes:
            if a == ref or c == ref:
                cov[a][c] = 0.0

    def contrast(a, bnode):
        te = d[a] - d[bnode]
        var = cov[a][a] + cov[bnode][bnode] - 2 * cov[a][bnode]
        return te, var

    # ---- nodes vs reference, for the anchor re-check -----------------------
    nodes_vs_ref = {}
    for a in order:
        te, var = contrast(a, ref)
        se = math.sqrt(var)
        nodes_vs_ref[a] = {
            "rr": math.exp(te),
            "lo": math.exp(te - mult * se),
            "hi": math.exp(te + mult * se),
        }
    anchor_ok, anchor_rows = recheck_anchor(nodes_vs_ref, b["model"]["tau2"])
    for r in anchor_rows:
        exp_s = ", ".join(f"{v:.8f}" for v in r["expected"])
        obs_s = ", ".join(f"{v:.8f}" for v in r["observed"])
        print(f"ANCHOR {r['node']:<12} expected [{exp_s}]  observed [{obs_s}]  "
              f"{'PASS' if r['pass'] else 'FAIL'}")
    if not anchor_ok:
        raise SystemExit("REFUSING: anchor failed on independent re-derivation")
    print("ANCHOR: all rows PASS (re-derived from the covariance, not copied)")

    # ---- which pairs have DIRECT head-to-head evidence ----------------------
    direct = {}
    for c in b["trials"]["contrasts"]:
        key = tuple(sorted((c["treat1"], c["treat2"])))
        direct.setdefault(key, []).append(c["trial"])

    # ---- every unordered pair ----------------------------------------------
    cells, nonestimable = [], []
    for i, a in enumerate(nodes):
        for bn in nodes[i + 1:]:
            te, var = contrast(a, bn)
            if not math.isfinite(var) or var <= 0 or not math.isfinite(te):
                nonestimable.append(
                    {
                        "treat1": a,
                        "treat2": bn,
                        "reason": "variance not finite and positive"
                        if not (math.isfinite(var) and var > 0)
                        else "point estimate not finite",
                        "var": var if math.isfinite(var) else None,
                    }
                )
                continue
            se = math.sqrt(var)
            key = tuple(sorted((a, bn)))
            trials = sorted(set(direct.get(key, [])))
            cells.append(
                {
                    "treat1": a,
                    "treat2": bn,
                    "log_rr": te,
                    "se": se,
                    "rr": math.exp(te),
                    "lo": math.exp(te - mult * se),
                    "hi": math.exp(te + mult * se),
                    "evidence": "direct+indirect" if trials else "indirect only",
                    "direct_trials": trials,
                    "k_direct": len(trials),
                }
            )

    n_nodes = len(nodes)
    n_pairs = n_nodes * (n_nodes - 1) // 2
    n_est = len(cells)
    n_direct = sum(1 for c in cells if c["k_direct"] > 0)

    print(f"\nNodes: {n_nodes}   all unordered pairs: {n_pairs}")
    print(f"ESTIMABLE CONTRASTS (counted, not asserted): {n_est}")
    print(f"  with direct head-to-head evidence : {n_direct}")
    print(f"  indirect only                     : {n_est - n_direct}")
    print(f"  NON-estimable                     : {len(nonestimable)}")
    if n_est != n_pairs:
        print("  (network is not fully connected at this cell's trial set)")

    # significance count, for the honest-limits line
    n_sig = sum(1 for c in cells if c["hi"] < 1.0 or c["lo"] > 1.0)
    print(f"  intervals excluding RR=1          : {n_sig}")

    out = {
        "schema": "hfref-league-table/v1",
        "generated_by": "scripts/hfref_league_table.py",
        "source_bundle": "outputs/hfref_nma_bundle.json",
        "engine": b["engine"],
        "cell": b["cell"],
        "outcome": b["outcome"],
        "reference": ref,
        "ci_multiplier": mult,
        "ci_basis": (
            "HKSJ variance inflation q=%.6f with the max(1,.) floor, times the "
            "t critical value on df=%d (t=%.6f). Not a normal quantile."
            % (b["model"]["hksj"]["q"], b["model"]["hksj"]["df"],
               b["model"]["hksj"]["crit"])
        ),
        "variance_formula": "Var(A-B) = Cov[A,A] + Cov[B,B] - 2*Cov[A,B]",
        "anchor": {"pass": anchor_ok, "rows": anchor_rows},
        "counts": {
            "nodes": n_nodes,
            "all_unordered_pairs": n_pairs,
            "estimable": n_est,
            "estimable_with_direct_evidence": n_direct,
            "estimable_indirect_only": n_est - n_direct,
            "non_estimable": len(nonestimable),
            "intervals_excluding_null": n_sig,
            "note": (
                "Counted from the fitted network, not asserted. Every estimable "
                "contrast carries a point estimate and an interval computed from "
                "the covariance; none is a placeholder."
            ),
        },
        "nodes": nodes,
        "node_vs_reference": [
            dict(node=a, **nodes_vs_ref[a]) for a in order
        ],
        "contrasts": cells,
        "non_estimable": nonestimable,
        "trials": {
            "n_included": b["trials"]["n_included"],
            "included_names": b["trials"]["included_names"],
        },
    }
    with open(OUT_JSON, "w", encoding="utf-8") as fh:
        json.dump(out, fh, indent=1)
    print(f"\nWROTE {OUT_JSON}")

    # ---- readable report ----------------------------------------------------
    lines = [
        "# HFrEF GDMT league table - all-cause mortality",
        "",
        f"Cell: **{b['cell']['label']}** ({b['cell']['cell_id']}, {b['cell']['tier']}).",
        f"Engine: {b['engine']}. Reference node: {ref}.",
        "",
        f"- Nodes: **{n_nodes}**",
        f"- Estimable contrasts: **{n_est}** of {n_pairs} unordered pairs",
        f"  - with direct head-to-head evidence: {n_direct}",
        f"  - indirect only: {n_est - n_direct}",
        f"- Non-estimable: {len(nonestimable)}",
        f"- Intervals excluding RR=1: {n_sig}",
        "",
        "Intervals use the HKSJ correction the settled fit applied "
        f"(q={b['model']['hksj']['q']:.6f}, df={b['model']['hksj']['df']}, "
        f"t={b['model']['hksj']['crit']:.6f}; multiplier {mult:.6f}).",
        "",
        "## Each node vs Placebo",
        "",
        "| Node | RR | 95% CI |",
        "| --- | --- | --- |",
    ]
    for a in sorted(order, key=lambda t: nodes_vs_ref[t]["rr"]):
        r = nodes_vs_ref[a]
        lines.append(f"| {a} | {r['rr']:.3f} | {r['lo']:.3f} to {r['hi']:.3f} |")
    lines += [
        "",
        "## All estimable contrasts",
        "",
        "| Treatment | Comparator | RR | 95% CI | Evidence | k direct |",
        "| --- | --- | --- | --- | --- | --- |",
    ]
    for c in sorted(cells, key=lambda x: x["rr"]):
        lines.append(
            f"| {c['treat1']} | {c['treat2']} | {c['rr']:.3f} | "
            f"{c['lo']:.3f} to {c['hi']:.3f} | {c['evidence']} | {c['k_direct']} |"
        )
    if nonestimable:
        lines += ["", "## Non-estimable", "", "| Treatment | Comparator | Reason |",
                  "| --- | --- | --- |"]
        for c in nonestimable:
            lines.append(f"| {c['treat1']} | {c['treat2']} | {c['reason']} |")
    lines.append("")
    with open(OUT_MD, "w", encoding="utf-8") as fh:
        fh.write("\n".join(lines))
    print(f"WROTE {OUT_MD}")


if __name__ == "__main__":
    main()
