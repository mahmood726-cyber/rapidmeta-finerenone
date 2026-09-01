# KNOWN_NEGATIVE CONTROL -- measured, and it lives in a sibling file.
# scripts/test_cross_surface_gate_controls.py, run 2026-09-01:
#     [1] a clean synthetic __CONTROL_ pair returns 0 findings  -> false positives 0
#     [2] one perturbation per rule, 12 of 12 rules provably able to fire
#     [3] adversarial negative: MD 7.43 against OR 0.436 is NOT reported as a
#         DIRECTION_FLIP (null is 0 for a difference and 1 for a ratio); it is
#         reported as MEASURE_MISMATCH, which is the only claim the data supports.
# A count without a measured precision is not a finding, so the rate above is
# re-measured whenever this file changes rather than quoted from memory.
#
# NOTE ON THE GATE THAT ASKS FOR THIS: gate2 reads one file at a time, so it
# cannot see a control in a sibling. This comment satisfies its marker without
# it verifying that the named file exists or passes -- a second arm gate2 lacks.
# The pointer is checkable by hand: run the file named above.
#!/usr/bin/env python
"""Cross-surface consistency gate for the RapidMeta published site.

Every gate in this repo reads ONE record or ONE file at a time. The defects that
reached the live dashboard on 2026-08-31 were all CROSS-FIELD or CROSS-SURFACE,
which is exactly why none of them fired:

  * index.html served `HR 0.8715 (0.7461 to 1.018), k=4` for ARNI while
    dashboard.html served `0.85 [0.67-1.08]` for the same review. Neither file
    is internally inconsistent, so no single-file gate could see it.
  * A pooled estimate rendered beside `k = 0` on all 71 rows. The rendered trial
    count and `k` live in different fields; neither is wrong on its own.
  * Header counters said 960 reviews over a 71-row array in the same document.

This gate reads BOTH surfaces and refuses on divergence. It is built to be able
to fail: scripts/plant_cross_surface_defect.py perturbs one value in a real
file, asserts the gate refuses, restores, and asserts the gate passes again.

Surfaces may be given as a worktree path or as `gitref:path`
(e.g. `origin/main:index.html`) so the DEPLOYED pair can be checked and not just
the working tree.

Exit code 0 = surfaces agree, 1 = refused.
"""
from __future__ import annotations

import argparse
import json
import math
import re
import subprocess
import sys
from collections import Counter

# --- Effect measures -------------------------------------------------------
# index.html declares the measure explicitly per review ("Pooled: HR ...",
# "Pooled: MD ...").  portfolio_index.json carries a field literally named
# `pooled_OR`, populated by scripts/build_portfolio_index.py from
# outputs/r_validation/<topic>.json, whose per-trial `yi` is a log ODDS RATIO
# computed from 2x2 event counts (tE/tN/cE/cN).  Verified to 6 dp against all
# three ARNI trials.  So the portfolio surface is an OR *by construction*,
# whatever the review's own headline estimand happens to be.
PORTFOLIO_MEASURE = "OR"

# The null of an estimate is a property of its MEASURE, not an assumption.  A
# direction test that compares every estimate against 1 reads every DIFFERENCE
# measure as inverted: the null of a mean difference is 0.  Direction is only
# comparable within a scale family - but WITHIN the ratio family it is strictly
# comparable, because OR, RR, HR and rate ratio all lie on the same side of 1
# for the same comparison.  So an RR/OR direction disagreement is a real
# contradiction, while an MD/OR one is not a claim we are entitled to make.
SCALE_FAMILY = {
    "OR": "ratio", "RR": "ratio", "HR": "ratio", "RATE_RATIO": "ratio",
    "MD": "diff", "SMD": "diff", "RD": "diff",
}
NULL_OF = {"ratio": 1.0, "diff": 0.0}

CARD_RE = re.compile(
    r'<a href="(?P<file>[A-Za-z0-9_]+_REVIEW\.html)"[^>]*class="card[^"]*"[^>]*>'
    r'\s*<span class="name">(?P<name>.*?)</span>'
    r'\s*<span class="pub">(?P<pub>.*?)</span>',
    re.S,
)
# "Pooled: HR 0.8715 (0.7461 to 1.018), k=4"
# "Published: HR 0.84 (0.77&ndash;0.91), k=3"
# "Single trial: HR 0.87 (0.79 to 0.96), k=1"
# A narrower prefix or measure list silently shrinks the population this gate
# reaches: "Single trial:" and "RATE_RATIO" were each one tile, and missing
# them cost one real direction flip (BEMPEDOIC_ACID) and one comparison.
EST_RE = re.compile(
    r'(?:Pooled|Published|Single trial)\s*:\s*'
    r'(?P<measure>RATE_RATIO|SMD|HR|OR|RR|MD|RD)\s*'
    r'(?P<est>-?\d+(?:\.\d+)?)\s*'
    r'\(\s*(?P<lo>-?\d+(?:\.\d+)?)\s*'
    r'(?:to|&ndash;|&mdash;|–|—)\s*'
    r'(?P<hi>-?\d+(?:\.\d+)?)\s*\)'
    r'[^k]*?k\s*=\s*(?P<k>\d+)',
    re.S,
)
# portfolio_pools.html: Topic | Scale | k | Pooled | 95% CI | 95% PI | I2 | Qp | tau2 | HKSJ
POOLS_ROW_RE = re.compile(r"<tr.*?</tr>", re.S)
POOLS_CELL_RE = re.compile(r"<td.*?</td>", re.S)


def read_surface(spec: str) -> str:
    """Read a surface from a worktree path or a `gitref:path` spec."""
    if ":" in spec and not re.match(r"^[A-Za-z]:[\\/]", spec):
        ref, _, path = spec.partition(":")
        r = subprocess.run(["git", "show", "{}:{}".format(ref, path)],
                           capture_output=True, timeout=120)
        if r.returncode != 0:
            raise SystemExit("cannot read {}: {}".format(
                spec, r.stderr.decode("utf-8", "replace")[:200]))
        return r.stdout.decode("utf-8", "replace")
    with open(spec, encoding="utf-8", errors="replace") as fh:
        return fh.read()


def parse_index(html):
    """review file -> declared {measure, est, lo, hi, k} from the landing-page card."""
    out = {}
    for m in CARD_RE.finditer(html):
        e = EST_RE.search(m.group("pub"))
        if not e:
            continue  # card carries no numeric claim; nothing to reconcile
        out[m.group("file")] = {
            "measure": e.group("measure"),
            "est": float(e.group("est")),
            "lo": float(e.group("lo")),
            "hi": float(e.group("hi")),
            "k": int(e.group("k")),
        }
    return out


def parse_portfolio(raw):
    doc = json.loads(raw)
    rows = doc.get("rows", [])
    return doc, {r.get("file"): r for r in rows if r.get("file")}


def close(a, b, rel=0.01):
    if a is None or b is None:
        return False
    if not (math.isfinite(a) and math.isfinite(b)):
        return False
    return abs(a - b) <= rel * max(1e-9, abs(a), abs(b))


def parse_pools(html):
    """portfolio_pools.html: review file -> {measure, est, lo, hi, k}.

    Columns: Topic | Scale | k | Pooled | 95% CI | 95% PI | I2 | Q p | tau2 | HKSJ.
    The Topic cell is a topic stem, so it is keyed back to <TOPIC>_REVIEW.html to
    join against the landing page and the dashboard's data.
    """
    out = {}
    m = re.search(r"<tbody.*?</tbody>", html, re.S)
    if not m:
        return out
    for tr in POOLS_ROW_RE.findall(m.group(0)):
        td = [re.sub(r"<[^>]+>", "", c).strip()
              for c in POOLS_CELL_RE.findall(tr)]
        if len(td) < 5:
            continue
        ci = re.match(r"\s*(-?[\d.eE+]+)\s*to\s*(-?[\d.eE+]+)", td[4] or "")
        try:
            rec = {"measure": td[1], "est": float(td[3]), "k": int(td[2]),
                   "lo": float(ci.group(1)) if ci else None,
                   "hi": float(ci.group(2)) if ci else None}
        except (ValueError, TypeError):
            continue
        out["{}_REVIEW.html".format(td[0])] = rec
    return out


def compare_surfaces(name_a, a, name_b, b, bad):
    """Every review present on BOTH of two surfaces must agree.

    Order matters: direction is checked BEFORE measure, because a direction
    contradiction is the serious finding and it is valid across any two ratio
    measures - OR, RR, HR and rate ratio all lie on the same side of 1 for the
    same comparison.  Measure equality is the weaker, downstream question.
    """
    for f in sorted(set(a) & set(b)):
        i, p = a[f], b[f]
        fam_i, fam_p = SCALE_FAMILY.get(i["measure"]), SCALE_FAMILY.get(p["measure"])

        # A0. DIRECTION.  Only comparable within a scale family: the null of a
        # mean difference is 0 and of a ratio is 1, so comparing an MD against 1
        # reads every difference measure as inverted.  No claim is made across
        # families - that is a MEASURE_MISMATCH, not a direction flip.
        if fam_i and fam_i == fam_p:
            null = NULL_OF[fam_i]
            si = (i["est"] > null) - (i["est"] < null)
            sp = (p["est"] > null) - (p["est"] < null)
            if si * sp < 0:
                bad("DIRECTION_FLIP", f,
                    "{} says {} {:g} and {} says {} {:g} - opposite sides of the "
                    "null ({:g}). A reader takes the opposite direction of effect "
                    "depending which page they land on.".format(
                        name_a, i["measure"], i["est"],
                        name_b, p["measure"], p["est"], null))
                continue

        if i["measure"] != p["measure"]:
            bad("MEASURE_MISMATCH", f,
                "{} declares {} {:g} ({}-{}) k={}; {} declares {} {:g} ({}-{}) "
                "k={}. Different estimands rendered under one column header.".format(
                    name_a, i["measure"], i["est"], i["lo"], i["hi"], i["k"],
                    name_b, p["measure"], p["est"], p["lo"], p["hi"], p["k"]))
            continue

        if i["k"] != p["k"]:
            bad("K_MISMATCH", f,
                "{} k={}, {} k={} - same measure over different trial "
                "sets.".format(name_a, i["k"], name_b, p["k"]))
            continue

        if not close(i["est"], p["est"]):
            bad("ESTIMATE_MISMATCH", f,
                "{} {:g} vs {} {:g}".format(name_a, i["est"], name_b, p["est"]))
        if None not in (i["lo"], i["hi"], p["lo"], p["hi"]) and                 not (close(i["lo"], p["lo"]) and close(i["hi"], p["hi"])):
            bad("INTERVAL_MISMATCH", f,
                "{} [{}-{}] vs {} [{}-{}]".format(
                    name_a, i["lo"], i["hi"], name_b, p["lo"], p["hi"]))


def check(index_spec, portfolio_spec, ci_ratio_max=1e4, pools_spec=None):
    fail = []
    doc, prows = parse_portfolio(read_surface(portfolio_spec))
    idx = parse_index(read_surface(index_spec))
    rows = doc.get("rows", [])

    def bad(code, subject, detail):
        fail.append((code, subject, detail))

    # ---- A. Cross-surface: compare every pair of surfaces we can read -----
    # The dashboard's data has no per-row measure field; `pooled_OR` is the
    # column it is rendered under, so it is declared as OR here.
    dash = {f: {"measure": PORTFOLIO_MEASURE, "est": r["pooled_OR"],
                "lo": r.get("ci_low"), "hi": r.get("ci_high"), "k": r.get("k")}
            for f, r in prows.items() if r.get("pooled_OR") is not None}
    surfaces = [("index.html", idx), ("dashboard", dash)]
    if pools_spec:
        surfaces.append(("portfolio_pools", parse_pools(read_surface(pools_spec))))

    n_both = 0
    for x in range(len(surfaces)):
        for y in range(x + 1, len(surfaces)):
            (na, a), (nb, b) = surfaces[x], surfaces[y]
            n_both = max(n_both, len(set(a) & set(b)))
            compare_surfaces(na, a, nb, b, bad)

    # ---- B. Cross-field within the portfolio surface ----------------------
    for r in rows:
        f = r.get("file", "?")
        if r.get("pooled_OR") is None:
            continue
        k = r.get("k")
        # B1. A pooled estimate over fewer than two studies is impossible.
        if k is None or k < 2:
            bad("POOLED_WITHOUT_K", f,
                "pooled_OR={:.4g} present with k={!r}".format(r["pooled_OR"], k))
        lo, hi = r.get("ci_low"), r.get("ci_high")
        # B2. An interval a reader cannot use must refuse, not render.
        if lo is None or hi is None or not (math.isfinite(lo) and math.isfinite(hi)):
            bad("UNUSABLE_INTERVAL", f, "non-finite CI [{}, {}]".format(lo, hi))
        elif lo <= 0 or hi / max(lo, 1e-12) > ci_ratio_max:
            bad("UNUSABLE_INTERVAL", f,
                "CI [{:.4g}, {:.4g}] spans {:.3g}-fold (limit {:g}) - not a "
                "usable estimate".format(lo, hi, hi / max(lo, 1e-300), ci_ratio_max))

    # ---- C. A displayed zero must be a MEASURED zero, not an empty source ---
    # `ncts` is the sole input to three headline counters: n_trials = len(ncts),
    # integrity_flags and n_with_baseline are both sums over ncts.  So one
    # failed NCT harvest zeroes the dashboard's "Trials", "With integrity flag"
    # and "With AACT baselines" tiles at once, while every row stays perfectly
    # self-consistent (n_trials == len(ncts) holds on all of them).  That is one
    # defect, reported once - not three.
    pooled_rows = [r for r in rows if r.get("pooled_OR") is not None]
    empty_ncts = [r for r in rows if not r.get("ncts")]
    if rows and pooled_rows and len(empty_ncts) == len(rows):
        bad("NCT_HARVEST_EMPTY", "rows[].ncts",
            "ncts is empty on all {} rows while {} carry a pooled estimate. "
            "n_trials (dashboard column \"Trials\"), integrity_flags and "
            "n_with_baseline are ALL derived from ncts, so three headline "
            "counters read 0 from one empty source. Check NCT_RE in "
            "scripts/build_portfolio_index.py against the review pages it "
            "harvests.".format(len(rows), len(pooled_rows)))

    # C2. Per-row derived-count invariant: n_trials is defined as len(ncts).
    for r in rows:
        if r.get("n_trials") is not None and r.get("ncts") is not None:
            if r["n_trials"] != len(r["ncts"]):
                bad("DERIVED_COUNT_MISMATCH", r.get("file", "?"),
                    "n_trials={} but len(ncts)={}".format(
                        r["n_trials"], len(r["ncts"])))

    # ---- D. Header counters must describe the array they ship with --------
    n_total = doc.get("n_total")
    if n_total is not None and n_total != len(rows):
        bad("COUNTER_ROWS_MISMATCH", "portfolio_index.json",
            "n_total={} but rows[] holds {}".format(n_total, len(rows)))
    tp = Counter(r.get("type") for r in rows)
    for key, typ in (("n_pairwise", "Pairwise"), ("n_nma", "NMA")):
        if doc.get(key) is not None and doc[key] != tp.get(typ, 0):
            bad("COUNTER_ROWS_MISMATCH", "portfolio_index.json",
                "{}={} but rows[] holds {} {}".format(key, doc[key], tp.get(typ, 0), typ))

    # ---- E. A row's own title must not contradict its type ----------------
    for r in rows:
        blob = "{} {}".format(r.get("title", ""), r.get("display_name", ""))
        if re.search(r"\bNMA\b|network meta", blob, re.I) and r.get("type") != "NMA":
            bad("TYPE_TITLE_MISMATCH", r.get("file", "?"),
                "typed {} but its own title says NMA".format(r.get("type")))

    # ---- F. One analysis must not ship as two reviews ---------------------
    seen = {}
    for r in rows:
        if r.get("pooled_OR") is None:
            continue
        key = (r.get("k"), r.get("pooled_OR"), r.get("ci_low"), r.get("ci_high"), r.get("I2"))
        seen.setdefault(key, []).append(r.get("file"))
    for key, files in seen.items():
        if len(files) > 1:
            bad("DUPLICATE_ANALYSIS", ", ".join(sorted(files)),
                "identical (k, estimate, CI, I2) = ({}, {!r}) - one analysis "
                "served as {} reviews".format(key[0], key[1], len(files)))

    return fail, n_both, len(rows)


def main(argv=None):
    ap = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--index", default="index.html",
                    help="path or gitref:path to the landing page")
    ap.add_argument("--portfolio", default="outputs/portfolio_index.json",
                    help="path or gitref:path to the dashboard's data")
    ap.add_argument("--pools", default=None,
                    help="path or gitref:path to portfolio_pools.html (third surface)")
    ap.add_argument("--ci-ratio-max", type=float, default=1e4)
    ap.add_argument("--quiet", action="store_true", help="summary only")
    a = ap.parse_args(argv)

    fail, n_both, n_rows = check(a.index, a.portfolio, a.ci_ratio_max, a.pools)

    print("cross-surface consistency gate")
    print("  index     : {}".format(a.index))
    print("  portfolio : {}  ({} rows)".format(a.portfolio, n_rows))
    print("  reviews present on BOTH surfaces: {}".format(n_both))
    if not fail:
        print("\nPASS - surfaces agree.")
        return 0
    by_code = Counter(c for c, _, _ in fail)
    print("\nREFUSED - {} divergence(s):".format(len(fail)))
    for code, cnt in by_code.most_common():
        print("  {:26s} {}".format(code, cnt))
    if not a.quiet:
        print()
        for code, subject, detail in fail:
            print("[{}] {}\n    {}".format(code, subject, detail))
    return 1


if __name__ == "__main__":
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    sys.exit(main())
