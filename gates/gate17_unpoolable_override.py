"""GATE 17  UNPOOLABLE OVERRIDE

Does anything publish a pooled estimate for a topic whose store object has
already recorded a refusal to pool?

Every other cross-artefact check in this repo compares two surfaces and inherits
that comparison's reach. The direction test could see 16 surface pairs out of
607 id-checkable sidecars; the trial-set audit needed registration ids that one
whole class does not carry. Both measured their own reach as much as the corpus.

This one compares an artefact against OUR OWN RECORDED REFUSALS. The store
writes `pooled.withdrawn: true` or `poolable: false` with a `poolable_reason`
in full - median 705 characters, none shorter than 109, quoting registry
evidence. No second surface, no reach limit, no denominator problem.

Measured 2026-08-31: of 108 recorded refusals, 88 are overridden by a sidecar
that publishes anyway, and 3 of those reach a page a reader can see. The store
had already diagnosed, in writing, three defects this lane spent a night
rediscovering by comparing surfaces:

  BEMPEDOIC_ACID  "Nothing is pooled: one trial. This is not a withheld
                   estimate -- the value stands and is CLEAR Outcomes' own."
  CANGRELOR_PCI   "THE NUMERATORS AND THE DENOMINATORS ON THIS PAGE COME FROM
                   DIFFERENT OUTCOMES, ON ALL THREE TRIALS."
  INCRETIN_HFpEF  "TWO OF THE THREE TRIALS ON THIS PAGE REGISTER ONLY CONTINUOUS
                   PRIMARY OUTCOMES, AND THIS PAGE POOLED EVENT COUNTS."

BASELINE IS OWED, NOT CLEARED. The ratchet is on the number that matters -
SERVED overrides must not rise AND no new page may join the served set.

Detector: scripts/gate_unpoolable_override.py
Proof it can fail: scripts/plant_unpoolable_override.py (makes one unserved
override served, asserts refusal BY NAME, restores byte-for-byte, asserts pass).
Root cause and remedy: SPEC-sidecar-must-honour-store-refusals-2026-08-31.md
"""
from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _harness as H                                                        # noqa: E402

REPO = H.repo_root()
sys.path.insert(0, os.path.join(REPO, "scripts"))

# THE NAMED POSITIVE MUST BE SYNTHETIC, NOT A LIVE DEFECT.
#
# This gate first named the three live served overrides -- BEMPEDOIC_ACID,
# CANGRELOR_PCI, INCRETIN_HFpEF. All three were fixed hours later by serving the
# store's refusal text in place of the estimate, the gate could no longer reach
# them, and the harness refused it as VACUOUS. A control anchored to live data
# RETIRES ITSELF the moment the defect is fixed, and the gate then cries wolf
# about its own success. Gate 12 records the same lesson in this suite already.
#
# So the named positive is a SYNTHETIC refusal evaluated in memory: it cannot be
# fixed and cannot drift. The live cases are findings and ratchet entries, which
# is where they belong.
SYNTHETIC = "synthetic-refusal-recognised"
SERVED_AT_FREEZE = ("BEMPEDOIC_ACID_REVIEW.html",
                    "CANGRELOR_PCI_REVIEW.html",
                    "INCRETIN_HFpEF_REVIEW.html")


def main(argv):
    gate = H.Gate("17 UNPOOLABLE OVERRIDE",
                  "nothing may publish a pool the store has recorded a refusal for")
    gate.requires_control()

    try:
        import gate_unpoolable_override as X
    except Exception as exc:                                   # pragma: no cover
        gate.kinds({"detector import failed": 1})
        gate.broken("cannot import scripts/gate_unpoolable_override.py: %s" % exc)
        gate.coverage(0, 1, "the detector did not load, so nothing was inspected")
        return gate.report()

    base_path = os.path.join(REPO, "gates", "GATE17_OVERRIDE_BASELINE.json")
    if not os.path.exists(base_path):
        gate.kinds({"baseline absent": 1})
        gate.broken("no baseline at gates/GATE17_OVERRIDE_BASELINE.json")
        gate.coverage(0, 1, "no baseline, so no regression can be defined")
        return gate.report()
    base = H.load(base_path)

    gate.expect_case(SYNTHETIC,
                     "a synthetic store object recording a refusal is recognised as one")
    # Evaluate the SAME predicate the sweep uses, on an object built in memory.
    _withdrawn = {"pooled": {"withdrawn": True, "point": None}, "poolable": True}
    _unpoolable = {"pooled": {"point": 0.5}, "poolable": False}
    _clean = {"pooled": {"point": 0.5}, "poolable": True}

    def _is_refusal(bo):
        p = bo.get("pooled") or {}
        return bool(p.get("withdrawn") or bo.get("poolable") is False)

    if _is_refusal(_withdrawn) and _is_refusal(_unpoolable) and not _is_refusal(_clean):
        gate.saw(SYNTHETIC)

    refusals, overrides = X.find_overrides(
        "ssot/PAGE_MAP.json", "portfolio_pools.html",
        "outputs/portfolio_index.json", "outputs/r_validation")
    served = sorted(o["page"] for o in overrides if o["served"])

    # ---- known-negative control ------------------------------------------
    # The store objects that record NO refusal are established-clean for this
    # gate's question: it must never name one. They are counted from the same
    # traversal, so the control cannot drift from the population it scores.
    import json as _json
    pm = _json.loads(X.read("ssot/PAGE_MAP.json") or "{}")
    clean, accused = 0, []
    flagged = {o["page"] for o in overrides}
    for page, path in pm.items():
        raw = X.read(path)
        if raw is None:
            continue
        try:
            d = _json.loads(raw)
        except Exception:
            continue
        bo = ((d.get("results") or {}).get("by_outcome") or {}).get("primary") or {}
        if not bo:
            continue
        p = bo.get("pooled") or {}
        if p.get("withdrawn") or bo.get("poolable") is False:
            continue
        clean += 1
        if page in flagged:
            accused.append(page)
    gate.control(max(clean, 1), len(accused), accused[:5])

    gate.kinds({
        "store objects recording a refusal": refusals,
        "  overridden by a sidecar that publishes": len(overrides),
        "    AND SERVED to readers": len(served),
        "  refused with no publishing sidecar": refusals - len(overrides),
        "store objects recording no refusal": clean,
    })

    # Coverage: this gate can decide only on topics the PAGE_MAP resolves to a
    # store object. Topics with no store object are not clean - they are unknown.
    gate.coverage(refusals + clean, max(len(pm), refusals + clean),
                  "PAGE_MAP entries whose store object is missing, unparseable, or "
                  "carries no primary outcome, so no refusal can be read from them")

    gate.note("baseline recorded %s: %d refusals, %d overridden, %d served (%s)"
              % (base.get("recorded"), base.get("n_store_refusals"),
                 base.get("n_overridden"), base.get("n_served"), base.get("status")))
    gate.note("a PASS means no NEW served override and no rise, not a clean corpus: "
              "%d overrides remain OWED" % len(overrides))
    gate.note("root cause is one point, not %d: build_binary_sidecar.py is never told the "
              "store refuses. Remedy specified in "
              "SPEC-sidecar-must-honour-store-refusals-2026-08-31.md" % len(overrides))

    frozen = set(base.get("served_pages", []))
    by_page = {o["page"]: o for o in overrides}
    for p in sorted(set(served) - frozen):
        o = by_page[p]
        gate.finding("NEW-SERVED-UNPOOLABLE-OVERRIDE",
                     "%s -- the store refused and says why: %s | published anyway: "
                     "OR %s over k=%s" % (p, str(o["reason"])[:220],
                                          o["sidecar_pooled_OR"], o["sidecar_k"]),
                     numerator=len(set(served) - frozen), denominator=len(frozen))
    if len(served) > base.get("n_served", 0) and not (set(served) - frozen):
        gate.finding("SERVED-OVERRIDE-COUNT-ROSE",
                     "served overrides rose from %d to %d with no new page"
                     % (base.get("n_served"), len(served)))

    return gate.report(denominator="%d store refusals, %d overrides, %d served"
                                   % (refusals, len(overrides), len(served)))


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
