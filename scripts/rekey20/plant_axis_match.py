# -*- coding: utf-8 -*-
"""PLANTS FOR THE TWO-AXIS MATCHER. Every arm separately, each with a clean sibling.

⛔⛔ WHY EVERY ARM AND NOT A SAMPLE. A gate with seven arms and one dead one passes review
by eye: the file looks thorough, the run prints PASS, and the dead clause never fires on any
input for the life of the instrument. This repo shipped exactly that. So each state gets its
OWN plant, and each plant gets a CLEAN SIBLING that differs in exactly the one thing the
state is supposed to depend on and must land in a DIFFERENT state. A plant that passes while
its sibling also passes proves the clause fires, not that it DISCRIMINATES.

⭐⭐ AN ARTEFACT CONTROL AND A DETECTOR CONTROL ARE DIFFERENT THINGS AND BOTH ARE HERE.
  * The ARTEFACT control (A10) proves WHICH bytes were read -- path, size, row count and a
    sha256 over the sorted cd_base SET. It says nothing about whether the measure works.
  * The DETECTOR control (A9) proves every state CAN return a positive over the real frame.
    A clause that can never fire has a numerator fixed before a row is read, and its zero is
    not evidence of anything.
A sweep can pass the first perfectly and be measuring nothing.

⚠️ EVERYTHING RUNS THROUGH `axis_match.score()`. A plant that exercises a reimplementation
of the thing under test certifies the reimplementation.
"""
import io, os, sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.chdir(os.path.dirname(os.path.abspath(__file__)))
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace",
                              line_buffering=True)
from axis_match import prepare, score, _cond_need, ref                            # noqa
from axis_states import (ALL_STATES, MATCHED, AMBIGUOUS, PAIR_ABSENT,             # noqa
                         INTERVENTION_MISMATCH, CONDITION_MISMATCH,
                         NO_CANDIDATE_RETRIEVED, REFUSED_NO_TERMS)

FRAME = "F:/claude-temp/pend/cdsr_frame_cardiology.jsonl"
TWENTY = "../../evidence/2026-08-31-rekey/corrected/twenty.json"

# A10 -- THE ARTEFACT CONTROL, PINNED. If the frame is rebuilt these stop matching and the
# plant FAILS. That is correct: the right first question is then "did the world change?",
# not "did the code break?" -- and a control that silently follows its artefact has stopped
# being a control.
PINNED = {"frame_bytes": 2693862, "frame_rows": 1216,
          "frame_base_set_sha256":
          "a0d44914a5ef99e3ac826e9e11da13c4309cbf6549c385114405280e014349a9"}

# Term sets. Every one is real clinical vocabulary; none is a typo standing in for absence.
ERA = ["endothelin receptor antagonist"]          # live: 4 rows
WARF = ["warfarin"]                               # live: 5 rows
MAVA = ["mavacamten"]                             # a real drug, absent from this frame
RIPC = ["remote ischemic preconditioning versu no remote ischemic preconditioning"]
PAH = ["pulmonary", "arterial", "hypertension"]   # live
AF = ["atrial", "fibrillation"]                   # live: 22 rows
RIPC_C = ["endovascular", "vascular"]             # live
OUT = ["keratoconus", "photorefractive"]          # real ophthalmic terms, absent from a
                                                  # CARDIOLOGY frame by construction

rows, reviews = prepare(FRAME)
R = ref(FRAME, TWENTY)

print("=== REF -- printed before any assertion, so every number below is addressed ===")
for k in ("matcher", "rule_fingerprint", "frame_path", "frame_bytes", "frame_rows",
          "frame_base_set_sha256", "twenty_path", "twenty_n", "twenty_app_id_set_sha256"):
    v = R[k]
    print("   REF.%-24s %s" % (k, (v[:16] if isinstance(v, str) and len(v) == 64 else v)))
print("")

results, seen_states = [], set()


def check(tag, ok, detail):
    results.append((tag, ok, detail))
    print("   %-48s %-4s %s" % (tag, "PASS" if ok else "FAIL", detail))


def _n(s, k):
    return (s.get(k) or {}).get("n") if s.get(k) is not None else "-"


def st(iterms, cterms):
    s = score(reviews, iterms, cterms)
    seen_states.add(s["state"])
    return s


def arm(name, plant_i, plant_c, want, siblings):
    """One arm: the plant lands in `want`; each sibling lands somewhere ELSE."""
    p = st(plant_i, plant_c)
    check("%s  plant" % name, p["state"] == want,
          "wanted %s, got %s (I=%s C=%s both=%s ver=%s)"
          % (want, p["state"], _n(p, "axis_intervention"), _n(p, "axis_condition"),
             _n(p, "both"), _n(p, "verified")))
    for si, sc, swant, why in siblings:
        s = st(si, sc)
        check("%s  clean sibling: %s" % (name, why),
              s["state"] == swant and s["state"] != want,
              "wanted %s and not %s, got %s" % (swant, want, s["state"]))


print("=== A1-A7  EVERY STATE PLANTED SEPARATELY, EACH WITH A CLEAN SIBLING ===")

arm("A1 MATCHED", ERA, PAH, MATCHED,
    [(ERA, AF, PAIR_ABSENT, "condition swapped for a live but unpaired one")])

arm("A2 AMBIGUOUS", RIPC, RIPC_C, AMBIGUOUS,
    [(ERA, PAH, MATCHED, "same shape, but the matched row HAS objectives")])

arm("A3 PAIR_ABSENT", ERA, AF, PAIR_ABSENT,
    [(ERA, PAH, MATCHED, "condition swapped for the paired one")])

arm("A4 INTERVENTION_MISMATCH", MAVA, AF, INTERVENTION_MISMATCH,
    [(WARF, AF, AMBIGUOUS, "intervention swapped for a live one")])

arm("A5 CONDITION_MISMATCH", WARF, OUT, CONDITION_MISMATCH,
    [(WARF, AF, AMBIGUOUS, "condition swapped for a live one")])

# ⛔ A6 IS THE ASSERTION THE BRIEF NAMES AS NON-NEGOTIABLE. Collapsing
# NO_CANDIDATE_RETRIEVED into INTERVENTION_MISMATCH is the error that produced
# "84 of 105 killed" and read as a threshold problem when it was an absence. The two
# siblings differ from the plant on ONE AXIS EACH and must separate.
arm("A6 NO_CANDIDATE_RETRIEVED", MAVA, OUT, NO_CANDIDATE_RETRIEVED,
    [(MAVA, AF, INTERVENTION_MISMATCH, "condition axis made live -- MUST separate"),
     (WARF, OUT, CONDITION_MISMATCH, "intervention axis made live -- MUST separate")])

for label, i_t, c_t, want_axes in (("condition empty", ERA, [], ["condition"]),
                                   ("intervention empty", [], PAH, ["intervention"]),
                                   ("both empty", [], [], ["intervention", "condition"])):
    s = st(i_t, c_t)
    check("A7 REFUSED_NO_TERMS  plant: %s" % label,
          s["state"] == REFUSED_NO_TERMS and s["vacuous_axes"] == want_axes
          and s["axis_intervention"] is None and s["axis_condition"] is None,
          "got %s vacuous_axes=%s; axis counts are None, NOT 0"
          % (s["state"], s["vacuous_axes"]))
s = st(ERA, PAH)
check("A7 REFUSED_NO_TERMS  clean sibling: terms restored",
      s["state"] == MATCHED, "wanted MATCHED, got %s" % s["state"])

print("")
print("=== A8  THE VACUOUS SET, DETONATED AND SIZED ===")
# `all([])` is True. Here it wears numbers: with cond == [] the natural test
# `len(hits) >= min(2, len(cond))` is `0 >= 0` -- true for EVERY row. An unguarded empty
# condition list does not return zero, it returns THE ENTIRE FRAME.
try:
    _cond_need([])
    raised = False
except ValueError:
    raised = True
check("A8a guard raises on an empty condition list", raised,
      "_cond_need([]) refuses instead of returning 0")
unguarded = sum(1 for r in reviews
                if len([c for c in [] if c in r["_all"]]) >= min(2, 0))
check("A8b the vacuous set is SIZED, not merely refused", unguarded == len(reviews),
      "WITHOUT the guard an empty condition list matches %d of %d reviews -- not 0. A "
      "vacuous clause fails TOWARD a full match here, which would have read as a "
      "universally satisfied condition" % (unguarded, len(reviews)))

print("")
print("=== A9  DETECTOR CONTROL -- can every clause return a positive at all? ===")
for state in ALL_STATES:
    check("A9 %s observed" % state, state in seen_states,
          "a state never observed has a numerator that was fixed before a row was read")

print("")
print("=== A10 ARTEFACT CONTROL -- WHICH bytes were read ===")
for k, want in sorted(PINNED.items()):
    got = R[k]
    check("A10 %s" % k, got == want,
          "pinned %s / read %s%s"
          % (str(want)[:24], str(got)[:24],
             "" if got == want else
             "   <-- ask 'did the world change?' before 'did the code break?': this "
             "control is pinned to a frame outside the repo"))

print("")
n_ok = sum(1 for _, ok, _ in results if ok)
print("PLANTS: %d/%d" % (n_ok, len(results)))
if n_ok != len(results):
    print("FAILED: %s" % ", ".join(t for t, ok, _ in results if not ok))
    sys.exit(1)
