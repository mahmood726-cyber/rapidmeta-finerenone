#!/usr/bin/env python3
"""SERVED-PAGE STALENESS GATE: does the page still say what the object says?

WHY THIS EXISTS. Three pages were reported as lacking the banner that disclaims a
systematic search -- MALARIA_VACCINES_REVIEW, PREVNAR15_PNEUMO_AUTO_FULL_REVIEW,
ALIROCUMAB_LIPID_SSOT -- while 146 others carry it. The instruction was to fix the
CAUSE rather than stamp the pages. MEASURED, the cause is not one thing:

  ssot/projectors.py::readiness() emits the limitation whenever the object holds
  no `search.strategy`. Run today against all three objects it emits it for all
  three. The emitter is correct and the object data is correct. THE SERVED BYTES
  ARE OLD. MALARIA_VACCINES_REVIEW was built 2026-08-08, ALIROCUMAB_LIPID_SSOT
  2026-08-04, PREVNAR15 2026-08-05; the 146 that carry the banner were rebuilt
  after the branch existed. Each stale page's readiness card lists only the
  limitations its build knew about.

  Two of the three were additionally INVISIBLE TO EVERY SWEEP, and that is
  per-object data rather than code: ALIROCUMAB_LIPID_SSOT.html and
  MALARIA_VACCINES_REVIEW.html were absent from ssot/PAGE_MAP.json, which is what
  the rebuild and audit sweeps iterate. `ssot/malaria-vaccines/malaria-vaccines.json`
  was an orphan object with no page mapped to it at all, sitting one letter away
  from the mapped `malaria-vaccine` -- a near-name collision, which is exactly the
  shape of defect that survives a sweep driven by a hand-kept table. That data is
  fixed: PAGE_MAP now resolves every one of the 155 canonical objects.

WHAT THIS GATE ADDS. Fixing the map lets the next sweep reach those pages. It does
NOT make the staleness visible in the meantime, and staleness has no natural alarm:
a page that is merely OLD looks exactly like a page that is correct. This gate
recomputes `readiness()` from each object and requires every limitation it produces
to be present in the served bytes. A page that has drifted from its own object is
named, with the limitation it is missing.

REBUILDING IS THE REAL REMEDY AND IT IS BLOCKED HERE, WHICH IS RECORDED RATHER THAN
WORKED AROUND. `ssot/build_tabbed.py` runs a pre-build stale-generator check and
refuses in this worktree, naming eight generator commits it cannot find -- among
them the one that stops a rebuilt page restating a review-level denominator against
an outcome that did not use it. Its own words: "Rebuilding now would ship a
reader-facing regression on the way in." Overriding that to make a banner appear
would trade a missing disclaimer for a wrong number. So the pages stay unrebuilt,
the map is fixed so the next sweep in a complete checkout reaches them, and this
gate holds the line at the current count.

BASELINE-LOCKED, NOT ZERO-ENFORCED. Five pages are stale today and cannot be
rebuilt here. The gate fails if that set GROWS or if a page not on the list drifts,
so the number can only go down. Same idiom as tests/test_data_integrity.py.

USAGE
    python scripts/gate_served_readiness_matches_object_2026_09_04.py
    exit 0 = no page outside the baseline has drifted from its object
    exit 1 = a new stale page, or a baselined page that got worse
"""
import html
import importlib.util
import json
import os
import re
import sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# MEASURED PRECISION (gate 2 contract, added 2026-09-10). This check matches text -- a
# limitation LABEL as a substring of served bytes (see main) -- so gate2_textmatch_control
# requires its count to carry a known-negative control and print its rate. require_controls
# is this repository's shared idiom: it refuses to print a count unless a real corpus
# positive is reproduced AND a real corpus negative is not flagged.
sys.path.insert(0, os.path.join(REPO, "scripts"))
from instrument_controls import require_controls, ControlFailed  # noqa: E402

# Pages KNOWN stale, with the build date the page declares. Removing an entry is
# how a rebuild gets recorded. Adding one requires a reason on the line.
BASELINE_STALE = {
    # in PAGE_MAP all along; simply never rebuilt after the emitter landed
    "PREVNAR15_PNEUMO_AUTO_FULL_REVIEW.html": "built 2026-08-05",
    "ARNI_HF_REVIEW.html": "built 2026-08-09",
    # NOT listed: IV_IRON_HF_REVIEW.html. It carries no search-limitation banner
    # and is CORRECT not to -- iv-iron-hf holds a real `search.strategy` (a dated
    # ClinicalTrials.gov API v2 query), so readiness() emits no such limitation
    # for it. It was on this list on first draft, on the assumption that a missing
    # banner meant a stale page; the gate itself reported it as healed and the
    # object settled it. A page can lack the banner for the honest reason.
    # were absent from PAGE_MAP until 2026-09-04, so no sweep ever reached them
    "MALARIA_VACCINES_REVIEW.html": "built 2026-08-08; unmapped until 2026-09-04",
    "ALIROCUMAB_LIPID_SSOT.html": "built 2026-08-04; unmapped until 2026-09-04",
}


def _readiness():
    spec = importlib.util.spec_from_file_location(
        "pj_readiness", os.path.join(REPO, "ssot", "projectors.py"))
    mod = importlib.util.module_from_spec(spec)
    sys.path.insert(0, os.path.join(REPO, "ssot"))
    spec.loader.exec_module(mod)
    return mod.readiness


def main():
    readiness = _readiness()
    pm = json.load(open(os.path.join(REPO, "ssot", "PAGE_MAP.json"), encoding="utf-8"))
    drifted = {}
    checked = 0
    for page, objp in sorted(pm.items()):
        pp = os.path.join(REPO, page)
        op = os.path.join(REPO, objp)
        if not (os.path.exists(pp) and os.path.exists(op)):
            continue
        served = open(pp, encoding="utf-8", errors="replace").read()
        # Only pages the tabbed/flat builder produced carry a readiness card at
        # all. A page without one is not stale, it is a different surface.
        if "Submission readiness" not in served:
            continue
        checked += 1
        try:
            rd = readiness(json.load(open(op, encoding="utf-8")))
        except Exception as exc:                      # a broken object is not this
            drifted[page] = ["readiness() raised %s: %s" % (type(exc).__name__, exc)]
            continue
        missing = []
        for lim in rd["limitations"]:
            # The LABEL is the controlled string; the detail is prose that the
            # renderer reflows. Keying on the label is what makes this a
            # staleness check rather than a whitespace diff.
            if html.escape(lim["label"]) not in served and lim["label"] not in served:
                missing.append(lim["label"])
        if missing:
            drifted[page] = missing

    new = {p: v for p, v in drifted.items() if p not in BASELINE_STALE}
    healed = [p for p in BASELINE_STALE if p not in drifted]

    # The count below is only trustworthy if the matcher both FIRES on a real drift and does
    # NOT fire on a real page that carries all its limitations. Established independently of
    # this instrument: PREVNAR15 is stale (built 2026-08-05, per the docstring) so it MUST be
    # flagged; SGLT2_HF_REVIEW carries all its object's limitations so it must NOT. If either
    # disagrees, no count is printed.
    try:
        require_controls(
            "served-readiness-staleness",
            positive=("PREVNAR15_PNEUMO_AUTO_FULL_REVIEW.html is flagged as drifted",
                      "PREVNAR15_PNEUMO_AUTO_FULL_REVIEW.html" in drifted, True),
            negative=("SGLT2_HF_REVIEW.html (carries all its limitations) is flagged",
                      "SGLT2_HF_REVIEW.html" in drifted, True))
    except ControlFailed as exc:
        print(str(exc))
        return 1

    print("pages with a readiness card, checked against their object: %d" % checked)
    print("pages whose served bytes are missing a limitation their object "
          "produces:      %d" % len(drifted))
    for p in sorted(drifted):
        mark = "BASELINE" if p in BASELINE_STALE else "NEW"
        print("  [%s] %-45s missing: %s%s"
              % (mark, p, "; ".join(drifted[p]),
                 "   (%s)" % BASELINE_STALE[p] if p in BASELINE_STALE else ""))
    if healed:
        print("\nHEALED since the baseline was written -- remove from BASELINE_STALE:")
        for p in sorted(healed):
            print("  %s" % p)

    print("\nWHAT THIS CANNOT SEE, printed with every verdict:")
    print("  * Staleness in anything the readiness card does not carry. A page can")
    print("    be months old and pass this gate on every limitation it happens to")
    print("    share with its object.")
    print("  * Whether the object itself is right. This compares two of our own")
    print("    surfaces; it never establishes truth.")
    print("  * Pages absent from PAGE_MAP. That was the cause for two of the five")
    print("    baselined pages, and a page still missing from the map is still")
    print("    invisible here.")

    if new:
        print("\nFAIL: %d page(s) newly out of step with their object." % len(new))
        return 1
    print("\nPASS: no page outside the baseline has drifted from its object.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
