"""GATE 10 -- a non-inferiority trial pooled and presented as superiority.

THE CLASS, AND WHY IT OUTRANKS LARGER ONES. A non-inferiority trial is designed to show a
treatment is not MEANINGFULLY WORSE than its comparator, within a pre-specified margin. Pool
such trials, present the result as an ordinary effect estimate, and the reader is invited to
read "not meaningfully worse" as "better" -- the margin is chosen to make exactly that reading
available. It is one of the few classes that make a reader act in the WRONG DIRECTION rather
than merely act on a weak number.

WHAT THE CORPUS LOOKS LIKE TODAY, measured by the detector this gate exercises:

  pooled topics containing >=1 registered non-inferiority trial   35
  topics where EVERY contributing trial is a registered NI design  9
  topics whose PAGE states a margin                                0

Nine topics pool nothing but non-inferiority designs, so the ratio a reader sees is built
entirely from trials that were never asked whether the treatment is better. Two pages carry an
explicit DENIAL the registry contradicts -- and a denial is worse than silence, because silence
is an omission while a denial is a false statement a reader may rely on.

WHY A WRAPPER RATHER THAN A REIMPLEMENTATION, following gate 9. A gate that re-implements what
it checks is a tautology: it can only agree with itself. This gate EXERCISES the real detector
as a subprocess -- `scripts/lane_rob/chk_noninferiority_pooled_as_superiority.py` -- and
ratchets its findings so the class cannot grow.

⚠️ THE DETECTOR IS NOT ON THIS BRANCH YET. It was built on `lane/rob-retrieval-2026-08-26` and
lands with the merge. Until then this gate reports BROKEN and says so by name -- which is the
correct state for a gate whose subject is absent, and is exactly the available-not-operative
shape these gates exist to make visible. BROKEN is not PASS.

TWO NUMBERS IN THIS GATE ARE FLOORS, NOT COUNTS, and are labelled so wherever they appear. The
detector reads only locally cached registry records when looking for a stated margin, and its
denial pattern is narrower than the phrasing seen in the corpus. Both under-find. A brief
reported 17 topics where the detector measures 35; the 35 supersedes it, because one came from
a report and the other from the data.
"""
from __future__ import annotations

import io
import json
import os
import subprocess
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _harness as H  # noqa: E402

DETECTOR = "scripts/lane_rob/chk_noninferiority_pooled_as_superiority.py"
RESULT = r"F:\claude-temp\pend\out\noninferiority_detector.json"
BACKLOG = "GATE10_KNOWN_NI_TOPICS.json"

# The cases this gate was built to find. Never reaching one is VACUOUS, never a pass.
NAMED = {
    "ceftaroline": "ceftaroline -- 3 of 3 contributing trials are registered NI designs",
    "gepotidacin": "gepotidacin -- 2 of 2, and the page DENIES what the registry states",
    "lefamulin": "lefamulin -- 2 of 2, and the page DENIES what the registry states",
}


def main(argv):
    gate = H.Gate("10 NON-INFERIORITY POOLED AS SUPERIORITY",
                  "a pooled ratio built from trials never asked whether the treatment is better")
    for cid, desc in NAMED.items():
        gate.expect_case(cid, desc)
    gate.requires_control()

    repo = H.repo_root()
    path = os.path.join(repo, DETECTOR)
    if not os.path.exists(path):
        gate.broken(
            "%s is absent on this branch; this gate exists to RUN it and will not substitute "
            "a copy. It lands with the merge of lane/rob-retrieval-2026-08-26. A gate whose "
            "subject is absent is BROKEN, not passing." % DETECTOR)
        gate.kinds({"detector present": 0, "detector absent": 1})
        return gate.report(denominator="0 topics -- the detector could not run")

    # THE CONTROL IS THE DETECTOR'S OWN PLANT, exercised rather than asserted. It checks four
    # things: a planted NI topic is flagged, a topic with no NI trial is NOT, the fixture is
    # removed, and a missing registration list makes it REFUSE instead of pass.
    plant = subprocess.run([sys.executable, path, "--plant"], cwd=repo, capture_output=True)
    pout = plant.stdout.decode("utf-8", "replace")
    held = plant.returncode == 0 and pout.count("[PASS]") == 4
    if held:
        gate.control(4, 0, [], accuses=True)
    else:
        gate.control(4, 4, ["the detector's own plant did not hold"], accuses=True)
        gate.broken("the detector's plant did not pass 4/4; its findings are not usable. "
                    "stdout: %s" % pout[-300:].replace("\n", " "))

    proc = subprocess.run([sys.executable, path], cwd=repo, capture_output=True)
    if proc.returncode == 2:
        gate.broken("the detector REFUSED: %s"
                    % proc.stdout.decode("utf-8", "replace")[-300:].replace("\n", " "))
        gate.kinds({"topics reached": 0})
        return gate.report(denominator="the detector refused rather than reporting a pass")

    try:
        rows = json.load(io.open(RESULT, encoding="utf-8"))
    except Exception as e:
        gate.broken("the detector ran but its result file could not be read: %s" % e)
        gate.kinds({"result file readable": 0})
        return gate.report(denominator="no result to ratchet")

    for r in rows:
        for cid in NAMED:
            if r["topic"].startswith(cid):
                gate.saw(cid)

    undisclosed = [r for r in rows if r["verdict"] != "DISCLOSED"]
    denials = [r for r in rows if r["verdict"] == "DENIAL_CONTRADICTED_BY_REGISTRY"]
    allni = [r for r in rows if r["all_contributing_are_ni"]]

    found = ["%s|%s" % (r["topic"], r["verdict"]) for r in undisclosed]
    if "--plant" in argv:
        found.append("__planted_topic|UNDISCLOSED_NI_DESIGN")
        gate.note("PLANTED: a new topic pooling a non-inferiority trial without disclosure")

    new = H.ratchet(gate, BACKLOG, found,
                    "pooled topics containing a registered non-inferiority trial whose page "
                    "does not disclose the design or state its margin.")

    gate.kinds({
        "pooled topics with >=1 registered NI trial": len(rows),
        "of those, EVERY contributing trial is NI": len(allni),
        "pages carrying a denial the registry contradicts": len(denials),
        "pages stating any margin": sum(1 for r in rows if r["page_states_margin"]),
        "undisclosed, of which NEW since the freeze": len(new),
    })
    gate.note("the registry-margin count and the denial count are FLOORS: the detector reads "
              "only locally cached registry records, and its denial pattern is narrower than "
              "the phrasing seen in the corpus. Both under-find.")
    gate.note("nine topics pool NOTHING BUT non-inferiority trials, so the ratio a reader sees "
              "is built entirely from designs never asked whether the treatment is better.")

    for f in new:
        topic, _, verdict = f.partition("|")
        gate.finding("NI-POOLED-WITHOUT-DISCLOSURE",
                     "%s pools a registered non-inferiority trial and its page is %s. State "
                     "the design and the margin, or refuse the pooled claim." % (topic, verdict),
                     numerator=len(new), denominator=len(rows))

    # COVERAGE. The detector reads LOCALLY CACHED registry records only. A pooled topic
    # whose trials are not cached cannot be assessed for a non-inferiority design at all,
    # and its absence from the findings means nothing was read, not that nothing is there.
    # H.topic_objects returns (objects, kinds). len() on the TUPLE is 2, which made this
    # print "35 of 35" -- 100%% coverage -- from a type error. A wrong instrument reports
    # good news; that is the whole reason this fraction exists.
    _objs, _ = H.topic_objects(repo)
    _pooled = len(_objs)
    gate.coverage(len(rows), max(_pooled, len(rows)),
                  "pooled topics with no locally cached registry record for their trials, "
                  "where a non-inferiority design would be invisible to this detector")
    return gate.report(denominator="%d topics with an NI trial, %d frozen"
                       % (len(rows), len(found) - len(new)))


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
