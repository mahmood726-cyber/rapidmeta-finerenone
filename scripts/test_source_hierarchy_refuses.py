"""Fix alpha's negative tests. Two of them fire against the module as it was.

HOW THE PRE-FIX RUN IS DONE, so the claim is checkable rather than asserted:

    git show origin/main:ssot/provenance_tier.py > pre_tier.py
    python scripts/test_source_hierarchy_refuses.py --module pre_tier.py
    -> FAIL: the registry outranks the primary publication for an effect value
       FAIL: the module cannot say a disposition reads registry silence as absence

    python scripts/test_source_hierarchy_refuses.py          -> PASS

TEST 1 IS THE ONE THAT MATTERS, AND IT DOES NOT CHEAT BY LOOKING FOR NEW NAMES.
It asks the module for its ordering the way a caller would: use the question-scoped
order if the module has one, otherwise fall back to the only ordering the module
publishes, `TIERS[t]["rank"]`. Against the pre-fix module that fallback is the whole
answer, and it says REGISTRY_POSTED_RESULT (rank 1) outranks JOURNAL_FULL_TEXT
(rank 2) -- which is the inversion that dropped a published RCT because its registry
entry carried hasResults=false, and that took the registry's -53.5 for an ORION-11
endpoint whose published imputation is -49.9.

WHAT IS NOT CLAIMED. Reversing an order does not re-extract anything. No stored value
changes here. What changes is that a caller asking "which source wins for a VALUE" now
gets the publication, and a disposition rested on registry silence is reportable.
"""
from __future__ import annotations

import importlib.util
import io
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def load_module(path=None):
    if path is None:
        sys.path.insert(0, str(ROOT / "ssot"))
        import provenance_tier
        return provenance_tier
    spec = importlib.util.spec_from_file_location("tier_under_test", path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def effective_effect_order(mod, tier_a, tier_b):
    """Does tier_a beat tier_b for an EFFECT VALUE, per whatever ordering this module has?

    A caller with no question-scoped order has exactly one thing to go on: `rank`. So that
    is the fallback, and using it is what makes this test meaningful against the old module
    rather than a test that a new name exists.
    """
    if hasattr(mod, "outranks") and hasattr(mod, "EFFECT_VALUE_ORDER"):
        return mod.outranks(tier_a, tier_b, "effect_value")
    return mod.TIERS[tier_a]["rank"] < mod.TIERS[tier_b]["rank"]


def test_publication_outranks_registry_for_a_value(mod):
    if effective_effect_order(mod, "JOURNAL_FULL_TEXT", "REGISTRY_POSTED_RESULT"):
        return []
    return ["For an EFFECT VALUE the registry outranks the primary publication. That is the "
            "ordering that drops a published RCT whose registry entry carries "
            "hasResults=false, and that takes a registry value over the published one when "
            "a record holds several for one endpoint."]


def test_registry_keeps_precedence_on_prespecification(mod):
    """The other half. Flipping the order everywhere would be its own defect."""
    if not (hasattr(mod, "outranks") and hasattr(mod, "PRESPECIFICATION_ORDER")):
        return ["the module publishes no ordering for pre-specification, so the registry's "
                "deposited-under-duty argument has nowhere to hold"]
    if mod.outranks("REGISTRY_POSTED_RESULT", "JOURNAL_FULL_TEXT", "prespecification"):
        return []
    return ["The registry lost precedence on PRE-SPECIFICATION too. Its deposit-under-duty "
            "argument is correct for that question and reversing it there would trade one "
            "conflation for another."]


_SILENCE_AS_ABSENCE = {
    "field_read": "hasResults / resultsSection",
    "reason": ("ELIGIBLE. CHECKED LIVE AGAINST THE REGISTRY: hasResults=false and no "
               "resultsSection. There is nothing to extract. n=330."),
}
#: The CAREFUL phrasing, which must NOT be flagged. It states the same registry fact and
#: stops there instead of converting it into a claim about the trial. Flagging it would
#: push authors toward saying less, which is the opposite of what the corpus wants.
_SILENCE_STATED_ONLY = {
    "field_read": "hasResults / resultsSection",
    "reason": ("All four candidates were checked live against the registry and none has "
               "posted results (hasResults=false, no resultsSection). The zero is what four "
               "lookups returned, not a cell nobody filled."),
}
#: Silence converted into absence, but with the publication actually checked. Also fine.
_SILENCE_WITH_PUBLICATION_CHECKED = dict(_SILENCE_AS_ABSENCE, pmid="31562798")


def test_module_can_report_silence_as_absence(mod):
    if not hasattr(mod, "registry_silence_problems"):
        return ["the module cannot say whether a disposition reads registry silence as an "
                "absence of results; there is no predicate for it"]
    problems = []
    if not mod.registry_silence_problems(_SILENCE_AS_ABSENCE):
        problems.append("a disposition reading `hasResults=false` as 'there is nothing to "
                        "extract', with no non-registry source named, was NOT reported")
    if mod.registry_silence_problems(_SILENCE_STATED_ONLY):
        problems.append("the CAREFUL phrasing was flagged. It states the registry fact and "
                        "does not convert it into an absence; flagging it would penalise "
                        "the wording the corpus wants")
    if mod.registry_silence_problems(_SILENCE_WITH_PUBLICATION_CHECKED):
        problems.append("a disposition that DID name a checked publication was still flagged")
    return problems


def main(argv):
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    path = None
    if "--module" in argv:
        path = argv[argv.index("--module") + 1]
    mod = load_module(path)
    label = path or "ssot/provenance_tier.py"

    checks = [
        ("publication outranks registry for a VALUE",
         test_publication_outranks_registry_for_a_value(mod)),
        ("registry keeps precedence on PRE-SPECIFICATION",
         test_registry_keeps_precedence_on_prespecification(mod)),
        ("registry silence as absence is reportable, and careful phrasing is not",
         test_module_can_report_silence_as_absence(mod)),
    ]
    failed = 0
    print("module under test: %s\n" % label)
    for name, problems in checks:
        if problems:
            failed += len(problems)
            print("FAIL  %s" % name)
            for p in problems:
                print("        - %s" % p)
        else:
            print("PASS  %s" % name)
    if failed:
        print("\n%d problem(s)." % failed)
        return 1
    print("\nAll source-hierarchy checks pass.")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
