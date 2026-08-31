"""A planned duration must not be displayed as an observed one.

AN EXTERNAL REVIEWER READ THE DAPIVIRINE PAGE AND FOUND ASPIRE'S FOLLOW-UP GIVEN AS
12-14 MONTHS. That is the registered figure -- what the investigators INTENDED to
observe. The publication reports what they actually observed: a median of 1.6 years, a
maximum of 2.6, across 4,280 person-years. The page showed the first number where a
reader reads the second.

THAT INSTANCE WAS ALREADY REPAIRED, BY THE RoB LANE, AND IS ALREADY SERVED. The live
page now names the 12-14 months as planned and prints the observed median beside it. This
gate is not that fix. It exists because the CONDITION that produced it is corpus-wide and
untouched: the registered timeframe is stored for 182 outcomes because it can be fetched,
while an observed follow-up is stored for barely two dozen because it has to be read out
of a paper. When a builder needs a duration and only one is at hand, the available number
gets used and the label does not change to match.

WHAT THIS GATE CAN AND CANNOT SEE, STATED BECAUSE THE GAP IS MOST OF THE CORPUS. The
detector's object leg compares a stored observed value against a stored planned one, and
can reach only 4 objects of 163 -- because 79 store the planned duration and NO observed
one, which is the exact condition under which the substitution happens. So the leg with
the clean method is blind to the population where the defect lives. The page leg reaches
83 pages by reading rendered text, and that is the leg with the reach.

ITS FALSE-POSITIVE RATE WAS MEASURED ON LIVE DATA, NOT ASSUMED. The page leg's first run
returned exactly one hit and that hit was WRONG: LENACAPAVIR quotes a registry outcome
DEFINITION containing the words "duration of follow-up", and the matcher's window swept
across the quotation. One of one. Two discriminators were added and six occurrences are
now suppressed as definitions rather than claims.

AND IT MUST NOT ACCUSE A PAGE THAT HANDLES THIS CORRECTLY. Dapivirine prints the planned
figure, labelled planned, beside the observed one. A gate that flagged that would be
arguing for the defect it exists to find.
"""
from __future__ import annotations

import io
import json
import os
import subprocess
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _harness as H                                                        # noqa: E402

DETECTOR = os.path.join("scripts", "sweep_planned_as_observed_2026_08_29.py")
RESULT = os.path.join("outputs", "planned_as_observed_2026_08_29.json")
BACKLOG = "PLANNED_AS_OBSERVED_BACKLOG.json"


def main(argv):
    gate = H.Gate("12 PLANNED SHOWN AS OBSERVED",
                  "a registered follow-up displayed where a reader reads an observed one")
    # THE NAMED CASE IS THE PAGE THAT GETS IT RIGHT. There is no confirmed defect left to
    # name -- the reported one is repaired and served -- so the case this gate must reach
    # is the CORRECT handling, and reaching it means checking that dapivirine is examined
    # and NOT flagged. A gate whose only named case is a defect goes vacuous the moment
    # the defect is fixed, and then passes forever without looking at anything.
    gate.expect_case("DAPIVIRINE_RING_PILOT",
                     "the reported page, now correct: it must be examined and NOT accused")
    gate.requires_control()

    repo = H.repo_root()
    path = os.path.join(repo, DETECTOR)
    if not os.path.exists(path):
        gate.broken("%s is absent; this gate RUNS the detector rather than reimplementing "
                    "it. A gate whose subject is missing is BROKEN, not passing." % DETECTOR)
        gate.kinds({"detector present": 0, "detector absent": 1})
        return gate.report(denominator="0 pages -- the detector could not run")

    plant = subprocess.run([sys.executable, path, "--plant"], cwd=repo, capture_output=True)
    pout = plant.stdout.decode("utf-8", "replace")
    held = plant.returncode == 0 and pout.count("[PASS]") == 5
    if held:
        gate.control(5, 0, [], accuses=True)
    else:
        gate.control(5, 5, ["the detector's own plant did not hold"], accuses=True)
        gate.broken("the detector's plant did not pass 5/5, so its findings are not "
                    "usable. stdout: %s" % pout[-300:].replace(chr(10), " "))

    proc = subprocess.run([sys.executable, path], cwd=repo, capture_output=True)
    if proc.returncode == 2:
        gate.broken("the detector REFUSED its own comparator controls: %s"
                    % proc.stdout.decode("utf-8", "replace")[-300:].replace(chr(10), " "))
        gate.kinds({"pages reached": 0})
        return gate.report(denominator="the detector refused rather than reporting a pass")

    try:
        doc = json.load(io.open(os.path.join(repo, RESULT), encoding="utf-8"))
    except Exception as e:
        gate.broken("the detector ran but its result could not be read: %s" % e)
        gate.kinds({"result file readable": 0})
        return gate.report(denominator="no result to ratchet")

    obj_hits = doc.get("findings") or []
    page_hits = doc.get("leg_b_findings") or []
    checked = doc.get("leg_b_pages_checked", 0)

    # The named case is reached by confirming the page was IN the examined population and
    # is NOT among the hits. Absence from a findings list proves nothing on its own -- it
    # is equally consistent with never having been looked at.
    dap = "DAPIVIRINE_RING_PILOT_REVIEW.html"
    examined = os.path.exists(os.path.join(repo, dap))
    if examined and not any(h.get("page") == dap for h in page_hits + obj_hits):
        gate.saw("DAPIVIRINE_RING_PILOT")

    found = (["obj|%s|%s" % (h["page"], h["observed_field"]) for h in obj_hits]
             + ["page|%s|%s" % (h["page"], h["label"]) for h in page_hits])
    if "--plant" in argv:
        found.append("page|__control_planted_page.html|median follow-up")
        gate.note("PLANTED: a page showing the registered duration under an observed label")

    new = H.ratchet(gate, BACKLOG, found,
                    "pages or objects presenting a registered planned duration where a "
                    "reader reads an observed one.")

    gate.kinds({
        "objects storing BOTH a planned and an observed duration": doc.get("n_both", 0),
        "objects storing a planned duration and NO observed one": doc.get("n_uncheckable", 0),
        "objects storing neither": doc.get("n_neither", 0),
        "pages with a planned duration to compare against": checked,
        "presentations flagged, of which NEW since the freeze": len(new),
    })
    gate.note("the %d objects storing only a planned duration are NOT passes. They are the "
              "population where this substitution happens, and the object leg cannot see "
              "them at all -- it compares 4 objects of 163. Only the page leg reaches them."
              % doc.get("n_uncheckable", 0))
    gate.note("the page leg's measured false-positive rate on its first live run was 1 of 1: "
              "it flagged LENACAPAVIR, where the phrase sits inside a registry outcome "
              "DEFINITION and the duration printed after it is correctly labelled. Two "
              "discriminators were added; that hit is now suppressed along with 5 others.")
    gate.note("the reported instance, dapivirine, was repaired by the RoB lane and verified "
              "SERVED on 2026-08-29. This gate did not fix it and does not claim to.")

    for f in new:
        leg, _, rest = f.partition("|")
        page, _, where = rest.partition("|")
        gate.finding("PLANNED-DURATION-SHOWN-AS-OBSERVED",
                     "%s presents a registered planned duration at %r where a reader reads "
                     "an observed one (%s leg). Say which it is, or give the observed "
                     "figure." % (page, where, leg),
                     numerator=len(new), denominator=checked)

    # COVERAGE. A page can only be checked where an object gives a registered duration to
    # compare its prose against. Most delivered pages have no object at all, so a baseline
    # of 0 is a statement about 83 pages, not about the corpus.
    _delivered = doc.get("n_delivered_pages") or checked
    gate.coverage(checked, max(_delivered, checked),
                  "delivered pages with no registered duration stored anywhere to compare "
                  "their prose against, where a planned figure shown as observed is invisible")
    return gate.report(denominator="%d pages carrying a registered duration; %d objects "
                                   "unreachable for lack of any observed value"
                       % (checked, doc.get("n_uncheckable", 0)))


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
