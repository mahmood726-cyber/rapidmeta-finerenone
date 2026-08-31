#!/usr/bin/env python
"""BLOCKING GATE: does anything publish where the store recorded a refusal?

Every other check in this repo compares two surfaces and inherits that
comparison's reach. The direction test could see 16 surface pairs out of 607
id-checkable sidecars. The trial-set audit needed registration ids that the
curated-HR class does not carry. Both measured their own reach as much as the
corpus.

This one does not compare surfaces. The store records its OWN refusals to pool -
`pooled.withdrawn: true`, `poolable: false`, with a `poolable_reason` written
out in full - and the only question is whether another artefact published a
number anyway, and whether a reader can see it. No second surface, no reach
limit, no denominator problem.

Measured 2026-08-31 against 98196b574: of 108 recorded refusals, 88 were
overridden by a sidecar and 3 of those reach a served page.

The baseline is OWED, NOT CLEARED. It exists so the gate can refuse a
REGRESSION today while the 88 are worked off; it is not a statement that the 88
are acceptable. The ratchet is on the number that matters:

  * served overrides must not RISE above the baseline count, AND
  * no NEW page may appear among the served overrides.

Both conditions are needed. A ratchet on the count alone would let a new served
override in while an old one was deleted, and the total would look unchanged.

Exit 0 = no regression. Exit 1 = refused.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BASELINE = os.path.join(HERE, "gates", "GATE17_OVERRIDE_BASELINE.json")


def read(spec):
    """Read from a worktree path or a `gitref:path` spec."""
    if ":" in spec and not re.match(r"^[A-Za-z]:[\\/]", spec):
        ref, _, path = spec.partition(":")
        r = subprocess.run(["git", "-C", HERE, "show", "%s:%s" % (ref, path)],
                           capture_output=True, timeout=300)
        return r.stdout.decode("utf-8", "replace") if r.returncode == 0 else None
    p = os.path.join(HERE, spec)
    if not os.path.exists(p):
        return None
    with open(p, encoding="utf-8", errors="replace") as fh:
        return fh.read()


POOLS_ROW = re.compile(r"<tr[^>]*data-stem=\"([^\"]+)\"", re.S)


def served_pages(pools_spec, portfolio_spec):
    """Pages a reader can actually see a pooled number on."""
    out = set()
    html = read(pools_spec)
    if html:
        for stem in POOLS_ROW.findall(html):
            out.add(stem.upper() + "_REVIEW.html")
    raw = read(portfolio_spec)
    if raw:
        try:
            for r in json.loads(raw).get("rows", []):
                if r.get("pooled_OR") is not None and r.get("file"):
                    out.add(r["file"])
        except Exception:
            pass
    return out


def find_overrides(page_map_spec, pools_spec, portfolio_spec, sidecar_dir):
    served = served_pages(pools_spec, portfolio_spec)
    pm = json.loads(read(page_map_spec) or "{}")
    refusals, overrides = 0, []
    for page, path in sorted(pm.items()):
        raw = read(path)
        if raw is None:
            continue
        try:
            d = json.loads(raw)
        except Exception:
            continue
        bo = ((d.get("results") or {}).get("by_outcome") or {}).get("primary") or {}
        if not bo:
            continue
        p = bo.get("pooled") or {}
        if not (p.get("withdrawn") or bo.get("poolable") is False):
            continue
        refusals += 1
        topic = page[: -len("_REVIEW.html")]
        sc = read(os.path.join(sidecar_dir, topic + ".json").replace("\\", "/"))
        if sc is None:
            continue
        try:
            s = json.loads(sc)
        except Exception:
            continue
        if s.get("pooled_OR") is None:
            continue
        overrides.append({
            "page": page, "topic": topic,
            "reason": (bo.get("poolable_reason") or p.get("withdrawn_reason")
                       or p.get("withdrawn_because") or "(no reason text)"),
            "sidecar_pooled_OR": s.get("pooled_OR"), "sidecar_k": s.get("k"),
            "store_path": path, "served": page in served,
        })
    return refusals, overrides


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--page-map", default="ssot/PAGE_MAP.json")
    ap.add_argument("--pools", default="portfolio_pools.html")
    ap.add_argument("--portfolio", default="outputs/portfolio_index.json")
    ap.add_argument("--sidecars", default="outputs/r_validation")
    ap.add_argument("--baseline", default=BASELINE)
    ap.add_argument("--write-baseline", action="store_true",
                    help="record today's counts as the OWED baseline")
    a = ap.parse_args(argv)

    refusals, overrides = find_overrides(a.page_map, a.pools, a.portfolio, a.sidecars)
    served = sorted(o["page"] for o in overrides if o["served"])

    if a.write_baseline:
        json.dump({
            "recorded": "2026-08-31",
            "recorded_against_ref": subprocess.run(
                ["git", "-C", HERE, "rev-parse", "origin/main"],
                capture_output=True, timeout=120).stdout.decode().strip(),
            "status": "OWED - NOT CLEARED",
            "means": ("These overrides exist and are owed. The baseline lets the gate "
                      "refuse a REGRESSION while they are worked off. It is not a "
                      "statement that any of them is acceptable."),
            "n_store_refusals": refusals,
            "n_overridden": len(overrides),
            "n_served": len(served),
            "served_pages": served,
        }, open(a.baseline, "w", encoding="utf-8"), indent=2)
        print("baseline written: %s" % a.baseline)
        print("  %d refusals, %d overridden, %d SERVED (OWED, not cleared)"
              % (refusals, len(overrides), len(served)))
        return 0

    if not os.path.exists(a.baseline):
        print("REFUSED: no baseline at %s. Run --write-baseline first." % a.baseline)
        return 1
    base = json.load(open(a.baseline, encoding="utf-8"))

    print("unpoolable-override gate")
    print("  baseline recorded %s (%s)" % (base.get("recorded"), base.get("status")))
    print("  store refusals    %d   (baseline %d)" % (refusals, base.get("n_store_refusals", -1)))
    print("  overridden        %d   (baseline %d)" % (len(overrides), base.get("n_overridden", -1)))
    print("  SERVED            %d   (baseline %d)" % (len(served), base.get("n_served", -1)))

    base_served = set(base.get("served_pages", []))
    new_served = [p for p in served if p not in base_served]
    risen = len(served) > base.get("n_served", 0)

    if not new_served and not risen:
        print("\nPASS - no new override reaches a served page, and the served count has "
              "not risen.\n       %d overrides remain OWED." % len(overrides))
        return 0

    by_page = {o["page"]: o for o in overrides}
    print("\nREFUSED")
    if risen:
        print("  served overrides ROSE from %d to %d" % (base.get("n_served", 0), len(served)))
    for p in new_served:
        o = by_page[p]
        print("\n  %s" % p)
        print("      the store refused to pool this, and says why:")
        for line in str(o["reason"]).splitlines() or [""]:
            print("        %s" % line[:160])
        print("      published anyway: OR %s over k=%s" % (o["sidecar_pooled_OR"], o["sidecar_k"]))
        print("      found by: scripts/gate_unpoolable_override.py "
              "(store %s)" % o["store_path"])
    return 1


if __name__ == "__main__":
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    sys.exit(main())
