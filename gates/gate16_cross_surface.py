"""GATE 16  CROSS SURFACE

Every other gate in this suite reads one artefact. This one reads THREE and
refuses when they disagree about the same review: index.html's card, the
dashboard's outputs/portfolio_index.json, and portfolio_pools.html.

It exists because the defects it finds are invisible to any single-file check.
On 2026-08-31 the landing page served ARNI as `HR 0.8715 (0.7461 to 1.018) k=4`
while the dashboard served `0.85 [0.67-1.08]` for the same review; neither file
is internally inconsistent, so nothing fired. Six reviews disagree on the
DIRECTION of effect, including an HIV-prevention estimate that reads protective
on one page and harmful on two others.

BASELINE IS OWED, NOT CLEARED. The corpus carries 67 divergences today. The
baseline exists so this gate can refuse a REGRESSION while they are worked off;
it is not a statement that any of them is acceptable. The ratchet refuses on a
RISE in the total AND on any NEW (code, page) pair, because either alone is
bypassable: a new divergence could enter while an old one is deleted and the
total would look unchanged.

Detector: scripts/check_cross_surface_consistency.py
Proof it can fail: scripts/plant_cross_surface_defect.py (perturbs one value in
the real portfolio_index.json, asserts exactly one new finding, restores
byte-for-byte, asserts the verdict returns to baseline).
Controls: scripts/test_cross_surface_gate_controls.py
"""
from __future__ import annotations

import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _harness as H                                                        # noqa: E402

REPO = H.repo_root()
sys.path.insert(0, os.path.join(REPO, "scripts"))

BASELINE = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                        "GATE16_CROSS_SURFACE_BASELINE.json")

# The cases this gate was built to find. Never reaching one is VACUOUS, not a pass.
FLIPS = ("AGYW_HIV_PREP_REVIEW.html",
         "BEMPEDOIC_ACID_REVIEW.html",
         "CEFTAROLINE_AUTO_FULL_REVIEW.html")


def main(argv):
    gate = H.Gate("16 CROSS SURFACE",
                  "three served surfaces must not disagree about one review")
    gate.requires_control()

    try:
        import check_cross_surface_consistency as X
    except Exception as exc:                                   # pragma: no cover
        gate.kinds({"detector import failed": 1})
        gate.broken("cannot import scripts/check_cross_surface_consistency.py: %s" % exc)
        gate.coverage(0, 1, "the detector did not load, so nothing was inspected")
        return gate.report()

    for f in FLIPS:
        gate.expect_case("flip:" + f.split("_REVIEW")[0].lower(),
                         "%s disagrees on the DIRECTION of effect across surfaces" % f)

    # ---- known-negative control ------------------------------------------
    # The synthetic clean pair from the shipped control suite. It is designed to
    # satisfy every rule, so any finding on it is this gate accusing a clean case.
    # Reusing the tested builder rather than rewriting one is deliberate: a fresh
    # rewrite would pass for reasons the real detector does not share.
    try:
        import test_cross_surface_gate_controls as C
        import tempfile
        html, doc = C.clean_pair()
        with tempfile.TemporaryDirectory() as tmp:
            fp = C.run(html, doc, tmp)
        gate.control(len(doc["rows"]), len(fp),
                     [("%s %s" % (c, s)) for c, s, _ in fp][:5])
    except Exception as exc:
        gate.broken("the known-negative control did not run: %s" % exc)
        gate.control(1, 1, ["control harness failed to execute"])

    # ---- the sweep --------------------------------------------------------
    fail, n_both, n_rows = X.check("index.html", "outputs/portfolio_index.json",
                                   pools_spec="portfolio_pools.html")
    now = {(c, s) for c, s, _ in fail}
    detail = {(c, s): d for c, s, d in fail}

    for c, s, _d in fail:
        if c == "DIRECTION_FLIP" and s in FLIPS:
            gate.saw("flip:" + s.split("_REVIEW")[0].lower())

    by_code = {}
    for c, _s, _d in fail:
        by_code[c] = by_code.get(c, 0) + 1
    gate.kinds(dict(sorted(by_code.items(), key=lambda kv: -kv[1])))

    # ---- coverage ---------------------------------------------------------
    # What this gate can DECIDE on is a review present with an estimate on at
    # least two surfaces. The population it claims to police is every review the
    # dashboard ships. The gap is not "some items" - it is named.
    gate.coverage(
        n_both, max(n_rows, n_both),
        "dashboard rows carrying no estimate on a second surface, so no "
        "cross-surface comparison is possible for them at all")

    if not os.path.exists(BASELINE):
        gate.broken("no baseline at %s -- run with --write-baseline" % BASELINE)
        return gate.report()
    base = H.load(BASELINE)
    frozen = {(k[0], k[1]) for k in base.get("keys", [])}

    gate.note("baseline %s recorded %s: %d divergences, %s"
              % (os.path.basename(BASELINE), base.get("recorded"),
                 base.get("count"), base.get("status")))
    gate.note("ratchet compares UNIQUE (code, page) pairs: %d frozen, %d now"
              % (base.get("n_unique_keys", 0), len(now)))
    gate.note("a PASS means no NEW divergence and no rise, not a clean corpus. "
              "%d of the frozen set are DIRECTION_FLIP -- the worst cases are "
              "named, not buried in a total." % base.get("n_direction_flip", 0))
    retired = frozen - now
    if retired:
        gate.note("retired since the freeze (lower the baseline): %d" % len(retired))

    for key in sorted(now - frozen):
        gate.finding("NEW-CROSS-SURFACE-DIVERGENCE", "%s: %s" % (key[0], detail[key]),
                     numerator=len(now - frozen), denominator=len(frozen))
    # COMPARE LIKE WITH LIKE. `now` is a SET of (code, page) pairs; the baseline
    # also stores the raw finding count, which is larger because one page can
    # carry the same code against two surfaces. Comparing the set size against
    # the raw count made this arm unfireable: 48 can never exceed 67.
    if len(now) > base.get("n_unique_keys", 0) and not (now - frozen):
        gate.finding("CROSS-SURFACE-COUNT-ROSE",
                     "unique (code, page) pairs rose from %d to %d with no pair "
                     "absent from the freeze -- the set ratchet did not catch it"
                     % (base.get("n_unique_keys"), len(now)))

    return gate.report(denominator="%d divergences over %d comparable reviews"
                                   % (len(now), n_both))


def write_baseline():
    sys.path.insert(0, os.path.join(REPO, "scripts"))
    import check_cross_surface_consistency as X
    fail, n_both, n_rows = X.check("index.html", "outputs/portfolio_index.json",
                                   pools_spec="portfolio_pools.html")
    keys = sorted([c, s] for c, s, _ in fail)
    nflip = sum(1 for c, _s, _d in fail if c == "DIRECTION_FLIP")
    payload = {
        "recorded": "2026-08-31",
        "status": "OWED - NOT CLEARED",
        "means": ("These divergences exist and are owed. The baseline lets gate 16 refuse a "
                  "REGRESSION while they are worked off. It is not a statement that any of "
                  "them is acceptable, and it must be lowered as they are fixed, never raised."),
        "count": len(keys),
        "n_unique_keys": len(set(tuple(k) for k in keys)),
        "n_direction_flip": nflip,
        "comparable_reviews": n_both,
        "what": ("(code, page) pairs where two served surfaces disagree about one review"),
        "keys": keys,
    }
    with open(BASELINE, "w", encoding="utf-8") as fh:
        json.dump(payload, fh, indent=2)
    print("baseline written: %s" % BASELINE)
    print("  %d divergences (%d unique code+page pairs) over %d comparable reviews, "
          "%d of them DIRECTION_FLIP"
          % (len(keys), len(set(tuple(k) for k in keys)), n_both, nflip))
    print("  status: OWED - NOT CLEARED")
    return 0


if __name__ == "__main__":
    if "--write-baseline" in sys.argv:
        sys.exit(write_baseline())
    sys.exit(main(sys.argv[1:]))
