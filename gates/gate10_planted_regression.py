# no-control: this module matches no document text. It calls other modules' predicates against
# literal fixtures and compares verdicts; it reads no corpus prose and emits no text-derived
# count, so a known-negative control would have nothing to be a control over. Stated rather
# than silently exempted, because an unexplained exemption is how a gate stops meaning anything.
"""GATE 10 -- every defect class we have found must still be found.

WHAT THIS ANSWERS. Tonight's defects were found by people reading pages. This gate is the
standing measurement of whether an instrument would find them now, one class at a time, and it
FAILS in both directions: a class that stopped being detected is a regression, and a class
recorded as undetected that has quietly become detected means this registry is lying about our
coverage.

COST. Tier 1 is in-process calls to the real shipped predicates against literal fixtures. No
corpus scan, no file writes, no network, and NO MODEL CALLS. It runs in well under a second,
because a suite that is slow gets switched off and a suite that is switched off is worse than
none. `--tier 2` and `--tier 3` are opt-in and are not run by the pre-push hook.

WHAT TIER 1 CANNOT DO, SAID PLAINLY. It exercises each rule, not each traversal. A predicate
can be correct while the walk that feeds it never reaches a real defect -- measured on
2026-08-28, when gate 1's predicate was right and a swapped name written in PROSE was never
handed to it. Tier 2 plants the real corpus and is the only thing that tests reach. This gate
prints that limitation every run rather than letting a green tier 1 be read as coverage.
"""
from __future__ import annotations

import importlib
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _harness as H                                                        # noqa: E402
import regression_plants as RP                                              # noqa: E402

G1 = importlib.import_module("gate1_trial_identity")
G3 = importlib.import_module("gate3_one_reason_field")
G4 = importlib.import_module("gate4_judgement_reference")
G6 = importlib.import_module("gate6_nct_beside_name")
TM = importlib.import_module("textmatch")
ICP = importlib.import_module("interval_contains_point")


# ---------------------------------------------------------------------------
# probes. Each returns (detected: bool, evidence: str).
# A probe MUST call the shipped function. None of these re-implements a rule.
# ---------------------------------------------------------------------------
def p_gate1_swap():
    rows, _ = G1.check_objects(RP.fx_swapped_label_store())
    return bool(rows), "check_objects returned %d row(s): %s" % (
        len(rows), rows[0].get("names") if rows else "-")


def p_gate1_unpinned():
    """A swap between two trials that are not in PINNED. Out of scope by construction."""
    obj = {"fixture-topic": {"inputs": {"trials": [
        {"nct": "NCT03036124", "label": "DELIVER"}]}}}       # NCT03036124 is DAPA-HF
    rows, _ = G1.check_objects(obj)
    return bool(rows), ("check_objects returned %d row(s); PINNED holds %d registrations"
                        % (len(rows), len(G1.PINNED)))


def p_gate6_swap_clean():
    v, _ = G6.pair_by_nearest(TM.page_text(RP.FX_SWAP_PROSE), "NCT00509106")
    return v == "SWAPPED", "pair_by_nearest -> %s" % v


def p_gate6_swap_mixed():
    v, _ = G6.pair_by_nearest(TM.page_text(RP.FX_SWAP_PROSE_BOTH), "NCT00509106")
    return v == "SWAPPED", "pair_by_nearest -> %s (a true swap is present)" % v


def p_gate3_divergent():
    rows, _ = G3.scan(RP.fx_divergent_reason())
    return bool(rows), "scan returned %d row(s)" % len(rows)


def p_gate3_identical():
    rows, _ = G3.scan(RP.fx_identical_reason())
    return bool(rows), "scan returned %d row(s) on a KNOWN NEGATIVE" % len(rows)


def _kinds_of(obj):
    return [k for _, _, k in G4.judgement_blocks(obj)]


def p_gate4_bare():
    kinds = _kinds_of(RP.fx_bare_judgement())
    return G4.KIND_D in kinds, "judgement_blocks -> %s" % [k.split("--")[0].strip() for k in kinds]


def p_gate4_bare_under_date():
    kinds = _kinds_of(RP.fx_bare_judgement_under_a_date())
    return G4.KIND_D in kinds, ("judgement_blocks -> %s (the SAME judgement, one dated "
                                "ancestor)" % [k.split("--")[0].strip() for k in kinds])


def p_gate4_fake_hash():
    kinds = _kinds_of(RP.fx_fake_full_hash())
    # detected would mean: NOT credited as versioned on the strength of 8 hex characters
    return G4.KIND_A not in kinds, ("judgement_blocks -> %s from an 8-character 'full sha256'"
                                    % [k.split("--")[0].strip() for k in kinds])


def p_k_vs_rows():
    """No shipped instrument. Prove the fixture is genuinely defective, then report the zero."""
    outcome = {"k": 5, "per_trial": [{"nct": "NCT03036124"}, {"nct": "NCT03619213"}]}
    really_broken = outcome["k"] != len(outcome["per_trial"])
    if not really_broken:                       # a fixture that is not defective measures nothing
        raise AssertionError("Q4 fixture is not actually defective")
    return False, "k=5 over 2 rows; no shipped module joins k to its rows"


def p_falsy_served():
    text = TM.page_text("<p>Pooled efficacy: None (95% CI None to None).</p>")
    if "None" not in text:                      # the fixture must really reach the reader
        raise AssertionError("AS6 fixture does not render None into page text")
    return False, "page_text carries 'None'; no shipped module refuses a falsy in served prose"


def p_interval_outside():
    f = ICP.findings("The pooled effect was RR 1.20 (95% CI 0.60 to 1.10).", "fixture")
    return bool(f), "findings -> %d" % len(f)


def p_interval_inside():
    f = ICP.findings("The pooled effect was RR 0.79 (95% CI 0.71 to 0.88).", "fixture")
    return bool(f), "findings on a VALID interval -> %d" % len(f)


def p_none():
    """No instrument exists for this class. Recorded, not inferred."""
    return False, "no shipped instrument reads for this class"


PROBES = {k: v for k, v in list(globals().items()) if k.startswith("p_")}


# ---------------------------------------------------------------------------
def main(argv):
    tier = 1
    if "--tier" in argv:
        tier = int(argv[argv.index("--tier") + 1])

    gate = H.Gate("10 PLANTED REGRESSION",
                  "every defect class we have found is still found, or still is not")

    plants = [p for p in RP.PLANTS if p["tier"] <= tier]
    for p in plants:
        gate.expect_case(p["id"], "%s [%s]" % (p["cls"], p["layer"]))

    kinds = {"class-instances checked": 0,
             "  expecting DETECTED (a detector exists)": 0,
             "  expecting ZERO (measured absence of any detector)": 0,
             "distinct defect classes covered": len({p["cls"] for p in plants}),
             "instances SKIPPED -- tier above the requested one":
                 len(RP.PLANTS) - len(plants)}

    for p in plants:
        probe = PROBES.get(p["probe"])
        if probe is None:
            gate.broken("no probe named %s for %s" % (p["probe"], p["id"]))
            continue
        try:
            detected, evidence = probe()
        except Exception as exc:
            gate.broken("probe %s raised %r" % (p["probe"], exc))
            continue
        gate.saw(p["id"])                       # the probe RAN and reached its fixture
        kinds["class-instances checked"] += 1
        kinds["  expecting DETECTED (a detector exists)"] += p["expect"] == "DETECTED"
        kinds["  expecting ZERO (measured absence of any detector)"] += p["expect"] == "ZERO"

        got = "DETECTED" if detected else "ZERO"
        if got != p["expect"]:
            if p["expect"] == "DETECTED":
                gate.finding("REGRESSION-CLASS-NO-LONGER-DETECTED",
                             "%s: %s. Instrument: %s. Evidence: %s"
                             % (p["id"], p["cls"], p["instrument"], evidence),
                             numerator=1, denominator=len(plants))
            else:
                gate.finding("REGISTRY-STALE-CLASS-NOW-DETECTED",
                             "%s: %s is recorded as undetected and something now reports it. "
                             "Update the registry -- a known-zero that has become a known-one "
                             "is a false statement about our coverage. Evidence: %s"
                             % (p["id"], p["cls"], evidence),
                             numerator=1, denominator=len(plants))

    gate.kinds(kinds)

    det = [p for p in plants if p["expect"] == "DETECTED"]
    zero = sorted({p["cls"] for p in plants if p["expect"] == "ZERO"}
                  - {p["cls"] for p in det})
    gate.note("MEASURED RECALL, tier %d: %d of %d class-instances have any instrument at all."
              % (tier, len(det), len(plants)))
    gate.note("CLASSES AT ZERO -- nothing we own reports these (%d):" % len(zero))
    for c in zero:
        gate.note("    " + c)
    gate.note("REACH IS NOT COVERAGE: tier 1 exercises each RULE, not each TRAVERSAL. A "
              "predicate can be correct while the walk never reaches a real defect. Only "
              "tier 2 (--tier 2, plants the real corpus) tests reach.")
    if tier < 2:
        gate.note("TIER 2 NOT RUN: " + "; ".join(RP.TIER2_SOURCES))
    return gate.report(denominator="%d class-instances over %d distinct classes"
                                   % (len(plants), len({p["cls"] for p in plants})))


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
