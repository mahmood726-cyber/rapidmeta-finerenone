"""GATE 12 -- an effect estimate must lie inside its own confidence interval.

THE FIRST UNIT OF THE CONVERSION FACTORY, AND THE FIRST DETECTOR HERE THAT WORKS ON CONTENT
WE DID NOT WRITE. It needs no schema, no registry and no model, so the same code runs over our
pages and over a published Cochrane review. That matters twice: a detector that only fires on
our own corpus may be fitting our idioms, and a defect found in somebody else's review is
evidence about the world rather than about us.

FOUR LEGS, and it does not ship without all four:

  1 DETECTOR   `interval_contains_point.findings` -- arithmetic, deterministic, no model call.
  2 PLANT      tier2_plants_d.py, applied to a real page, watched to FAIL, restored, restoration
               asserted by sha256 and byte count.
  3 CONTROL    15 known negatives anchored to FIXTURES, never to the corpus's current belief:
               boundary equality, decimal commas, en-dashes, negative mean differences, a year
               followed by a CI. Plus 4 known positives, so the gate cannot pass by being blind.
  4 PRECISION  measured on that control and printed beside every count.

REACH IS PRINTED SEPARATELY FROM COVERAGE, because the first run of this unit made exactly that
mistake. It found one contradiction across "15 Cochrane reviews" -- which was reach: 8 of the 15
were PROTOCOLS with no results, and of the CI-marked intervals in the 7 completed reviews the
parser examined 30%. On our own corpus it examines 8%. A count over 8% of a population is not a
statement about the population, and this gate says so in its own output rather than leaving a
reader to assume otherwise.

WHY THE WIDE PATTERN IS NOT USED. Dropping the requirement for a measure name beside the point
raises reach and takes the measured false-positive rate from 0% to 19% -- it swallows "In 2019
(95% CI ...)", a participant count, a version number and a 0-100 scale. Against external
content a false accusation costs far more than a miss, so the wide pattern is measured, kept in
the module, and NOT used for reporting.
"""
from __future__ import annotations

import glob
import io
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _harness as H                                                        # noqa: E402
import interval_contains_point as U                                         # noqa: E402

LOOSE = re.compile(r"\(\s*9[05](?:\.\d)?\s*%\s*(?:CI|confidence interval)", re.I)
TAGS = re.compile(r"<(script|style)[^>]*>.*?</\1>", re.S | re.I)


def page_text(path):
    s = io.open(path, encoding="utf-8", errors="replace").read()
    return re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", TAGS.sub(" ", s)))


def main(argv):
    repo = H.repo_root()
    gate = H.Gate("12 INTERVAL CONTAINS POINT",
                  "an effect estimate must lie inside its own confidence interval")
    gate.requires_control()

    # -- leg 3 and 4: the control, and the precision it measures ---------------
    (nn, fp, fpx), (npos, missed, missx) = U.control2()
    gate.control(nn, fp, fpx)
    case = gate.expect_case("positives", "the four known positives are still detected")
    if missed == 0:
        gate.saw(case)
    else:
        for t in missx:
            gate.broken("a KNOWN POSITIVE was not detected: " + t[:80])

    pages = sorted(glob.glob(os.path.join(repo, "*_REVIEW.html")))
    loose = examined = 0
    findings = []
    for p in pages:
        t = page_text(p)
        loose += len(LOOSE.findall(t))
        examined += len(U.PAT2.findall(t))
        findings += U.findings2(t, os.path.basename(p))

    gate.kinds({
        "delivered pages read": len(pages),
        "CI-marked intervals present": loose,
        "  EXAMINED by the strict parser": examined,
        "  NOT examined -- unmeasured, NOT clean": loose - examined,
        "known positives in the control": npos,
        "known negatives in the control": nn,
    })

    for f in findings[:40]:
        gate.finding("POINT-OUTSIDE-ITS-OWN-INTERVAL",
                     "%s: %s %s with CI %s to %s -- the point is outside the interval printed "
                     "with it. Quote: %s" % (f["source"], f["measure"], f["point"], f["lo"],
                                             f["hi"], f["quote"][:160]),
                     numerator=len(findings), denominator=examined)

    pct = (100.0 * examined / loose) if loose else 0.0
    gate.note("REACH, NOT COVERAGE: %d of %d CI-marked intervals were examined (%.0f%%). The "
              "other %d are UNMEASURED and are not claimed clean."
              % (examined, loose, pct, loose - examined))
    gate.note("This unit also runs on external content. Measured 2026-08-29 over 7 completed "
              "Cochrane reviews (8 further fetched were PROTOCOLS and hold no results): one "
              "contradiction found and hand-read as genuine -- CD005470 / PMC13353907, "
              "'OR 0.46 (95% CI 1.29 to 1.65)', held in a single <list-item><p> element, so it "
              "is not an artefact of flattening. 30% of that corpus's intervals were examined.")
    gate.note("PAT2 keeps the measure-name anchor and relaxes only the punctuation between "
              "the point and the CI marker. That anchor is what holds the false-positive rate "
              "at zero: the WIDE variant, which drops it, measures 19% and is NOT used.")
    gate.note("THE FIXTURE CONTROL DID NOT TRANSFER. PAT2 measured 0% on fixtures and then "
              "produced a false accusation against a Cochrane review on its first real run -- "
              "a middle-dot decimal (0·71) read as the integer 0. That shape, and every "
              "other real one that fooled it, is now a permanent known negative. A control "
              "holding only the shapes its author thought of measures the author.")
    return gate.report(denominator="%d estimates examined across %d pages" % (examined, len(pages)))


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
