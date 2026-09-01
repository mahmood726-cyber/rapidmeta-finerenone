# no-control: this module matches no document text. Its only `in` test is a substring check
# against the --only argument to select which gates to run, which reports nothing and decides
# no finding. Stated rather than silently exempted, because an unexplained exemption is how a
# gate stops meaning anything.
"""Run every gate. Print the numerator and the denominator. Never summarise to a tick.

EXIT CODE IS THE WORST OF THE GATES, and VACUOUS is worse than FAIL on purpose: a gate that
could not see is more dangerous than one that saw and objected, because it reads as a pass.

  0 PASS     every gate saw its named cases and found nothing
  1 FAIL     at least one gate found something
  2 VACUOUS  at least one gate never reached a case it was built to find
  3 BROKEN   at least one gate could not run

`--fast` skips the gates that read all 1,426 delivered pages (5 and 6), for use where a
sub-minute check is wanted. It prints WHICH gates it skipped, because a scoped pass that does
not name its scope is how "53 apps" turned out to be 1,522.
"""
from __future__ import annotations

import importlib
import os
import subprocess
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _harness as H                                                        # noqa: E402

GATES = [
    ("gate1_trial_identity", "trial identity: a name beside a registration", "fast"),
    ("gate2_textmatch_control", "text matching carries a measured precision", "slow"),
    ("gate3_one_reason_field", "one authoritative reason for not pooling", "fast"),
    ("gate4_judgement_reference", "a judgement references what it judged", "fast"),
    ("gate5_absence_defined_set", "no irreversible action on an absence", "slow"),
    ("gate6_nct_beside_name", "NCT beside every trial name", "slow"),
    ("gate7_blast_radius", "blast radius counted before a class-wide edit", "fast"),
    ("gate8_caller_and_wiring", "every gate has a caller; every removal a precondition", "fast"),
    ("gate9_shared_scratch", "the shared-scratch lint actually runs", "fast"),
    # ADDED 2026-08-29. The class was undefended: 35 pooled topics contain a registered
    # non-inferiority trial, 9 pool nothing else, and ZERO pages state a margin. Registering it
    # here is what makes the detector operative -- a detector nothing calls is the
    # available-not-operative shape these gates exist to expose, and this suite was itself
    # sitting unmerged when the class was found.
    ("gate10_noninferiority_pooled_as_superiority",
     "non-inferiority pooled as superiority", "fast"),
    # ADDED 2026-08-29, and registered in the same commit that created it. An external
    # reviewer found Q printed twice on one page with different values; the sweep that
    # traced it to a dozen independent poolers was itself caught by gate 8 as a check
    # nothing called. Registering it here is what makes it operative.
    ("gate11_one_statistic_one_value",
     "a displayed statistic matches the R output stored beside it", "fast"),
    # ADDED 2026-08-29 alongside gate 11, and for the same reason: the sweep behind it was
    # written for a reported defect and would otherwise sit inert. Its named case is the
    # page that handles this CORRECTLY, because a gate whose only named case is a defect
    # goes vacuous the moment the defect is fixed.
    ("gate12_planned_shown_as_observed",
     "a planned duration displayed where a reader reads an observed one", "fast"),
    # ADDED 2026-08-29. Four word boundaries arrived as control characters in one
    # evening and three of the four had silenced a live check. The sweep behind this
    # was, predictably, caught by gate 8 as a check nothing called.
    ("gate13_nonraw_regex_escape",
     # SLOW: it parses every .py in the tree, twice (plant, then real). 9 minutes on
     # this machine. The pre-push hook runs --fast and will SKIP it, and says so by
     # name; CI runs the full set. A gate that makes every push nine minutes longer
     # is a gate people start bypassing.
     "a regex escape in a non-raw literal makes a check inert", "slow"),
    # ADDED 2026-08-30. An unsourced claim drifts to its strongest form; this is the
    # DISPLAYED-bytes leg, complementary to another lane's detector rather than a
    # duplicate of it. Slow: it renders 932,327 blocks across every delivered page.
    ("gate14_unanchored_authority",
     "an authority named as the source of a claim with nothing to follow", "slow"),
    # ADDED 2026-08-30. Ten components are now wired onto the write path and nothing checked
    # that a wired component carries controls at all. Registering it here is what makes it
    # operative -- a gate nothing calls is the available-not-operative shape gate 8 exists to
    # expose, and this suite has produced four such files already.
    #
    # ⛔ IT RATCHETS. Four components predate the contract; refusing on them would block every
    # lane's push (this suite runs in pre-push, which has no override) for a backlog none of
    # those lanes introduced. The backlog is recorded in gates/COMPONENT_CONTRACT_BACKLOG.json
    # with what each one lacks and why, printed on every run, and the gate refuses only a NEW
    # non-conformance or a REGRESSION. Proven both ways: with the backlog file absent it
    # REFUSES 4; with it present it passes and says the backlog has not risen.
    # ADDED 2026-08-31, and registered in the same commit that created it. The moat this
    # project claims is a READER-LEVEL one -- take a trial from the page, find its
    # registration beside the name, click through and confirm it -- and until now it had
    # been demonstrated exactly once, by hand, on one page. A demonstration does not apply
    # to the next topic. Registering it here is what makes it operative; a check that runs
    # in CI after the push cannot block the push.
    ("gate16_reader_can_check",
     "a reader can take a trial from the page and confirm it in the registry", "slow"),
    ("gate15_component_contract",
     "a wired generator component carries no controls", "fast"),
    # ADDED 2026-08-31. Three served surfaces disagreed about the same review and no
    # single-file gate could see it: the landing page served ARNI as HR 0.8715 k=4 while
    # the dashboard served 0.85 k=3, and each file is internally consistent. Six reviews
    # disagree on the DIRECTION of effect, one of them an HIV-prevention estimate that
    # reads protective on one page and harmful on two others.
    #
    # IT RATCHETS, for the same reason gate 15 does. 67 divergences (48 unique code+page
    # pairs) predate this gate; refusing on them would block every lane's push for a
    # backlog no lane introduced. Frozen in gates/GATE16_CROSS_SURFACE_BASELINE.json marked
    # OWED - NOT CLEARED, with the 6 DIRECTION_FLIPs named rather than buried in a total.
    # Refuses on a NEW (code, page) pair OR a rise in unique pairs -- both arms are needed,
    # and the count arm was UNFIREABLE on first writing because it compared a set size
    # against a raw finding count (48 can never exceed 67). Fixed before registering.
    ("gate16_cross_surface",
     "three served surfaces must not disagree about one review", "fast"),
    # ADDED 2026-08-31, and it is the better instrument. Every other cross-artefact check
    # here compares two surfaces and inherits that comparison's reach; this one compares an
    # artefact against OUR OWN RECORDED REFUSALS, so it has no reach limit. The store writes
    # `poolable: false` with a reason in full -- median 705 characters, none under 109 -- and
    # 88 of its 108 refusals are overridden by a sidecar that publishes anyway. It would have
    # caught all three served cases on day one, from the store alone.
    #
    # IT RATCHETS on the number that matters: SERVED overrides must not rise AND no new page
    # may join the served set. Baseline outputs/override_gate_baseline.json, OWED - NOT
    # CLEARED. Root cause is one point, not 88: build_binary_sidecar.py is never told the
    # store refuses. Remedy specified, not applied, in
    # SPEC-sidecar-must-honour-store-refusals-2026-08-31.md -- that script is another lane's.
    ("gate17_unpoolable_override",
     "nothing may publish a pool the store has recorded a refusal for", "fast"),
]


def main(argv):
    fast = "--fast" in argv
    only = None
    if "--only" in argv:
        only = argv[argv.index("--only") + 1].split(",")

    results, skipped = [], []
    for mod, what, speed in GATES:
        if only and not any(o in mod for o in only):
            continue
        if fast and speed == "slow":
            skipped.append(mod)
            continue
        t0 = time.time()
        m = importlib.import_module(mod)
        try:
            rc = m.main([a for a in argv if a not in ("--fast",)])
        except Exception as exc:            # a gate that crashes is BROKEN, never a pass
            print("GATE %s CRASHED: %r" % (mod, exc))
            rc = H.BROKEN
        results.append((mod, what, rc, time.time() - t0))

    print("")
    print("#" * 78)
    print("GATE SUMMARY")
    for mod, what, rc, dt in results:
        print("  %-9s %-32s %-28s %5.1fs" % (H.VERDICT_NAME[rc], mod.split("_", 1)[0], what, dt))
    if skipped:
        print("  SKIPPED (--fast): " + ", ".join(skipped))
        print("  A scoped pass names its scope. These gates read all delivered pages and were")
        print("  NOT run; this run says nothing about what they check.")
    worst = max([r for _, _, r, _ in results] or [H.BROKEN],
                key=lambda r: {H.PASS: 0, H.FAIL: 1, H.VACUOUS: 2, H.BROKEN: 3}[r])
    print("  OVERALL: %s" % H.VERDICT_NAME[worst])
    print("#" * 78)
    return worst


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
