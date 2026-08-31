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

CARD_RE = re.compile(
    r'<a href="(?P<file>[A-Za-z0-9_]+_REVIEW\.html)"[^>]*class="card[^"]*"[^>]*>'
    r'\s*<span class="name">(?P<name>.*?)</span>'
    r'\s*<span class="pub">(?P<pub>.*?)</span>',
    re.S,
)
# "Pooled: HR 0.8715 (0.7461 to 1.018), k=4"
# "Published: HR 0.84 (0.77&ndash;0.91), k=3"
EST_RE = re.compile(
    r'(?:Pooled|Published)\s*:\s*'
    r'(?P<measure>HR|OR|RR|MD|SMD)\s*'
    r'(?P<est>-?\d+(?:\.\d+)?)\s*'
    r'\(\s*(?P<lo>-?\d+(?:\.\d+)?)\s*'
    r'(?:to|&ndash;|&mdash;|–|—)\s*'
    r'(?P<hi>-?\d+(?:\.\d+)?)\s*\)'
    r'[^k]*?k\s*=\s*(?P<k>\d+)',
    re.S,
)


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


def check(index_spec, portfolio_spec, ci_ratio_max=1e4):
    fail = []
    doc, prows = parse_portfolio(read_surface(portfolio_spec))
    idx = parse_index(read_surface(index_spec))
    rows = doc.get("rows", [])

    def bad(code, subject, detail):
        fail.append((code, subject, detail))

    # ---- A. Cross-surface: every review present on BOTH surfaces ----------
    both = sorted(set(idx) & set(prows))
    for f in both:
        i, p = idx[f], prows[f]
        pooled = p.get("pooled_OR")
        if pooled is None:
            continue

        # A1. The measure must agree.  This is the check that catches ARNI.
        if i["measure"] != PORTFOLIO_MEASURE:
            bad("MEASURE_MISMATCH", f,
                "index.html declares {} {} ({}-{}) k={}; portfolio serves an {} "
                "{:.4g} ({}-{}) k={}. Different estimands rendered under one "
                "column header.".format(
                    i["measure"], i["est"], i["lo"], i["hi"], i["k"],
                    PORTFOLIO_MEASURE, pooled, p.get("ci_low"), p.get("ci_high"),
                    p.get("k")))
            continue

        # A2. Same measure -> the trial set must agree before values can.
        if i["k"] != p.get("k"):
            bad("K_MISMATCH", f,
                "index.html k={}, portfolio k={} - same measure over different "
                "trial sets.".format(i["k"], p.get("k")))
            continue

        # A3. Same measure, same k -> estimate and interval must agree.
        if not close(i["est"], pooled):
            bad("ESTIMATE_MISMATCH", f,
                "index.html {} vs portfolio {:.6g}".format(i["est"], pooled))
        if not (close(i["lo"], p.get("ci_low")) and close(i["hi"], p.get("ci_high"))):
            bad("INTERVAL_MISMATCH", f,
                "index.html [{}-{}] vs portfolio [{}-{}]".format(
                    i["lo"], i["hi"], p.get("ci_low"), p.get("ci_high")))

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

    return fail, len(both), len(rows)


def main(argv=None):
    ap = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--index", default="index.html",
                    help="path or gitref:path to the landing page")
    ap.add_argument("--portfolio", default="outputs/portfolio_index.json",
                    help="path or gitref:path to the dashboard's data")
    ap.add_argument("--ci-ratio-max", type=float, default=1e4)
    ap.add_argument("--quiet", action="store_true", help="summary only")
    a = ap.parse_args(argv)

    fail, n_both, n_rows = check(a.index, a.portfolio, a.ci_ratio_max)

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
