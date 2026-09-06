# -*- coding: utf-8 -*-
"""Gate 37 -- the EXTRACTION twin of the screen-every-outcome-rank fix.

The screening fix admits a trial if ANY report provides the prespecified outcome. Its twin, one
layer down: once admitted, EXTRACT every outcome rank, and where trials report a SHARED endpoint
alongside their differing primaries, PREFER the shared one. Taking each trial's registered primary
and stopping pools incommensurable composites.

Fixture (rosuvastatin, 11th external review): the page pooled JUPITER's FIVE-component primary
against HOPE-3's THREE-component co-primary -- incoherent. But JUPITER also reports the SAME
three-component endpoint (CV death + nonfatal MI + nonfatal stroke), 83/8901 vs 157/8901,
HR 0.53 -- exactly HOPE-3's co-primary. Extract-every-rank finds it and the pool becomes coherent.

The rule must FAIL pre-fix (primary-only extraction leaves the composites mismatched) and PASS
post-fix (the shared 3-component endpoint is found and preferred).
"""
from __future__ import annotations
import io, sys

# each trial's available endpoints, by rank. 'components' lets the rule detect a shared endpoint.
JUPITER = {
    "primary":   {"name": "5-component CV composite", "components": 5, "rank": "primary"},
    "reported":  [{"name": "3-component (CVd+nonfatal MI+nonfatal stroke)", "components": 3,
                   "rank": "secondary", "counts": (83, 8901, 157, 8901), "hr": 0.53}],
}
HOPE3 = {
    "primary":   {"name": "3-component co-primary", "components": 3, "rank": "primary",
                  "counts": (235, 6361, 304, 6344)},
    "reported":  [],
}


def extract_old(trial):
    """Defect: take the registered primary, stop."""
    return trial["primary"]


def extract_new(trials):
    """Fix: gather every rank across trials; if a component-count is shared by all, prefer it."""
    per_trial_available = []
    for t in trials:
        ranks = [t["primary"]] + t.get("reported", [])
        per_trial_available.append({e["components"]: e for e in ranks})
    shared = set.intersection(*[set(a) for a in per_trial_available]) if per_trial_available else set()
    if shared:
        pick = min(shared)  # the shared endpoint (here the 3-component one)
        return [a[pick] for a in per_trial_available], pick
    return [t["primary"] for t in trials], None


def coherent(endpoints):
    """A pool is coherent only if every contributed endpoint has the same component count."""
    return len({e["components"] for e in endpoints}) == 1


if __name__ == "__main__":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    trials = [JUPITER, HOPE3]
    old = [extract_old(t) for t in trials]
    new, shared_k = extract_new(trials)
    print("GATE 37 -- extract every outcome rank, prefer the shared endpoint (rosuvastatin fixture)")
    print("  PRE-FIX  (primary-only): JUPITER=%s (%dc) vs HOPE-3=%s (%dc) -> coherent=%s"
          % (old[0]["name"], old[0]["components"], old[1]["name"], old[1]["components"], coherent(old)))
    print("  POST-FIX (every rank):   both -> %d-component shared endpoint -> coherent=%s"
          % (shared_k or 0, coherent(new)))
    jupiter_3c_found = any(e.get("components") == 3 and e["rank"] != "primary" for e in JUPITER["reported"])
    ok = (not coherent(old)) and coherent(new) and jupiter_3c_found and shared_k == 3
    print("\n  PROVEN: pre-fix pool is INCOHERENT (mixed 5c vs 3c); post-fix finds JUPITER's shared"
          " 3-component endpoint and the pool is coherent." if ok else "\n  *** rule wrong ***")
    raise SystemExit(0 if ok else 1)
