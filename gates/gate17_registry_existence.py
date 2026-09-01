"""GATE 17 -- a trial id that resolves to nothing may not contribute a pooled row.

THE CHECK EXISTED AND NOTHING RAN IT. `scripts/gate_registry_existence.py` was
written in this lane, planted, and proved to refuse -- and gate8 immediately named
it: "named like a gate, can fail, and nothing runs it. A gate written and left
inert." That is the fourth instance of the shape this repo keeps finding, and the
sharpest kind: a check whose own author left it uncalled in the same session he
wrote it to close someone else's uncalled check.

WHY A WRAPPER RATHER THAN AN EDIT. The script is the instrument; this gate
EXERCISES it as a subprocess -- the real script, not a copy -- and ratchets its
findings so the class cannot grow. 43 ids that already contribute rows are frozen
by name in REGISTRY_EXISTENCE_BACKLOG.json; a NEW one fails.

WHAT IT DEFENDS. Nothing between a typed id and a pooled estimate asked whether
the trial exists: build_auto_include_ids_js is a string join, the page's
autoscreener pre-proposes INCLUDE from that set, and the row enters realData. The
audit that looked like a guard -- check_10_nct_in_auto_include_vs_realdata --
compares AUTO_INCLUDE to realData keys, both emitted from the same unverified
source, so it passes with fabricated ids in BOTH. A control can be green because
it compared a thing to its own reflection.

THE INSTRUMENT CARRIES BOTH CONTROLS and prints whether they held: it plants a
fabricated id and requires a refusal, and plants a REAL id and requires no
accusation. This gate reads that line rather than assuming an exit code means what
it hopes.

COVERAGE, STATED. It reads AUTO_INCLUDE_TRIAL_IDS out of served pages. An id that
reaches a pool by some other route -- written directly into realData with no
AUTO_INCLUDE entry -- is invisible to it. That is not hypothetical: the 43 known
ids are in no generator config at all, so this gate catches them at the page and
would not catch them at their source.
"""
from __future__ import annotations

import json
import os
import re
import subprocess
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _harness as H                                                        # noqa: E402

SCRIPT = "scripts/gate_registry_existence.py"
BACKLOG = "REGISTRY_EXISTENCE_BACKLOG.json"
CONTROLS_HELD = "both controls held"
REJECT = re.compile(r"^\s+(NCT\d{8})\s+on\s+(\d+)\s+page", re.M)
SEEN = re.compile(r"ids seen in those sets\s*:\s*(\d+)")
ACCEPTED = re.compile(r"accepted, in snapshot\s*:\s*(\d+)")


def main(argv):
    repo = H.repo_root()
    gate = H.Gate("17 REGISTRY EXISTENCE",
                  "no trial id that resolves to nothing may contribute a row to a "
                  "pooled estimate")
    gate.requires_control()

    path = os.path.join(repo, SCRIPT)
    if not os.path.exists(path):
        gate.broken("%s is absent; this gate exists to run it and will not "
                    "substitute a copy." % SCRIPT)
        gate.kinds({"instrument absent": 1})
        return gate.report()

    gate.expect_case("instrument-runs",
                     "the shipped check executes and reports its own controls")

    # THE INSTRUMENT'S OWN CONTROLS, READ RATHER THAN ASSUMED.
    st = subprocess.run([sys.executable, path, "--selftest"], cwd=repo,
                        capture_output=True)
    st_out = st.stdout.decode("utf-8", "replace")
    if CONTROLS_HELD in st_out:
        gate.saw("instrument-runs")
        gate.control(1, 0, [])
    else:
        gate.control(1, 1, ["the check did not report that its own controls held"])
        gate.broken("%s did not print %r. Its verdict is not usable."
                    % (SCRIPT, CONTROLS_HELD))
        return gate.report()

    proc = subprocess.run([sys.executable, path], cwd=repo, capture_output=True)
    out = proc.stdout.decode("utf-8", "replace")
    found = {m.group(1) for m in REJECT.finditer(out)}

    bpath = os.path.join(os.path.dirname(os.path.abspath(__file__)), BACKLOG)
    frozen = set()
    if os.path.exists(bpath):
        frozen = set(json.load(open(bpath, encoding="utf-8")).get("frozen", []))
    new = sorted(found - frozen)
    retired = sorted(frozen - found)

    gate.note("ratchet: %d frozen, %d now, %d retired, %d NEW. A PASS means no new "
              "instances, not a clean corpus."
              % (len(frozen), len(found), len(retired), len(new)))
    if retired:
        gate.note("  retired since the freeze (remove them from %s): %s"
                  % (BACKLOG, " ".join(retired)))

    for n in new:
        gate.finding("NEW-UNRESOLVABLE-ID-IN-A-POOL",
                     "%s appears in AUTO_INCLUDE_TRIAL_IDS and does not exist in the "
                     "registry. A reader cannot check which trial the row came from."
                     % n, numerator=len(new), denominator=len(found))

    m_seen, m_acc = SEEN.search(out), ACCEPTED.search(out)
    seen = int(m_seen.group(1)) if m_seen else 0
    acc = int(m_acc.group(1)) if m_acc else 0
    m_live = re.search(r"accepted, known live\s*:\s*(\d+)", out)
    live = int(m_live.group(1)) if m_live else 0

    # ⭐ KINDS BEFORE COUNTS. An id in an AUTO_INCLUDE set is one of three things,
    # and a population reported as a single number hides which. The third kind is
    # the one that matters: an id absent from the SNAPSHOT is not thereby absent
    # from the REGISTRY -- NCT01445665 is live on ClinicalTrials.gov and missing
    # from the 2026-08-27 export -- so collapsing it into "rejected" would accuse
    # a real trial.
    gate.kinds({
        "accepted: present in the AACT snapshot": acc,
        "accepted: absent from the snapshot, proven live by a dated probe": live,
        "rejected: resolves to nothing in either": len(found),
    })
    gate.coverage(seen, max(seen, 1),
                  "ids reaching a pool by a route other than AUTO_INCLUDE_TRIAL_IDS "
                  "-- written straight into realData -- are not visible here; the 43 "
                  "known ids are in no generator config, so this catches them at the "
                  "page and not at their source")
    return gate.report(denominator="%d ids in AUTO_INCLUDE sets, %d accepted against "
                                   "the registry" % (seen, acc))


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
