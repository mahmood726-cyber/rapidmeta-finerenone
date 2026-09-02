"""A property that cannot refuse is not a check. This test makes that mechanical.

THREE INSTRUMENTS, AND THEY PROVE DIFFERENT THINGS
==================================================

1. `test_each_property_refuses_a_planted_defect` -- plants one defect per property in a
   hand-built object and asserts the property does NOT hold. This LOCKS THE FIX IN. On
   its own it proves nothing about the state before the fix, because it exercises
   ssot/page_properties.py, which did not exist before the fix.

2. `test_no_property_is_emitted_as_a_literal_hold` -- reads ssot/build_to_standard.py as
   TEXT and fails if any `props["P..."] = prop(HELD, ...)` literal remains. THIS ONE
   FIRES AGAINST THE PRE-FIX FILE. Run it against the parent commit and it reports five
   literals: P1, P2, P3 (in its held branch), P4 and P5. That is the negative test the
   fix had to clear, and it calls the real module rather than a copy of it.

       git show origin/main:ssot/build_to_standard.py > "$SCRATCH/build_to_standard.prefix.py"
       python scripts/test_properties_can_refuse.py --source "$SCRATCH/build_to_standard.prefix.py"
       -> FAIL: 5 properties emitted as a literal HELD

3. The production evidence, which is stronger than either and is not synthetic:
   `scripts/property_recompute_gate.py` recomputes every property from the topic object
   the page was built from and compares it with the state the page SERVES. At the time
   this landed: 11 disagreements on 10 of the 18 served pages whose object resolves.
   Those are the old emitter's constants failing against real objects.

WHAT THE PLANTS DELIBERATELY ARE
================================

Each plant is the SMALLEST edit that makes the property's own claim false, and each is a
shape observed on the served corpus, not invented:

  P1  a database entry whose `query_as_executed` reads "NOT EXECUTED FOR THIS TOPIC"
      -- served verbatim on AZILSARTAN_HTN_AUTO_FULL_REVIEW while P1 read HELD.
  P2  a cascade whose included count exceeds the experimental count it descends from.
  P3  `predefined: None` -- served on IV_IRON_HF_REVIEW and SGLT2_HF_REVIEW while P3
      read HELD and printed "predefined=None on its face" in the HELD column.
  P4  a precondition verdict with no cited authority.
  P5  a READ cell with a source path and no verbatim sentence -- served on
      BEMPEDOIC_ACID_REVIEW while P5 read "READ with source path and verbatim text".

A test that only ever passes is the same defect as a property that only ever holds, so
`test_every_property_has_a_reachable_refusal` fails if a property is added to
PROPERTIES without a plant here.
"""
from __future__ import annotations

import io
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "ssot"))

import page_properties as PP  # noqa: E402


def _ok_object():
    """An object that legitimately holds every property. The control."""
    return {
        # A DECLARED STRATEGY, because P1 now requires one. Added 2026-09-03 with the
        # search.strategy arm: without it this CONTROL refuses, and a control that cannot
        # hold proves nothing about the plants below. The control caught the omission on
        # the first run of the new arm, which is exactly what it is there for.
        "search": {"strategy": "registry + bibliographic, protocol section 3.2",
                   "databases": [
                       {"database": "ClinicalTrials.gov API v2",
                        "query_as_executed": 'intervention="x"; study_type=INTERVENTIONAL',
                        "date_executed": "2026-08-18", "records_returned": 21},
                   ]},
        "k_cascade": {"k0_surfaced": 22, "k2_role_located": 21, "k3_experimental": 18,
                      "k4_comparator": 0, "k_included_in_object": 6,
                      "k_unscreened_remainder": 0},
        "screening": {"eligibility_provenance": {"predefined": True, "state": "PROTOCOL"}},
        "precondition_verdict": {"verdicts": {
            "population_stated": {"verdict": "PASS", "reason": "r", "authority": "MECIR R29"},
        }},
        "extraction": {"cells": [
            {"field": "effect", "label": "READ", "source_path": "resultsSection.analyses[0]",
             "verbatim": "HR 0.87, CI 0.79 to 0.96"},
            {"field": "arm_role", "label": "DERIVED", "derived_by": "topic_identity.locate()"},
        ]},
    }


def _plant_p1(o):
    o["search"]["databases"].append(
        {"database": "PubMed (NCBI E-utilities esearch)",
         "query_as_executed": "NOT EXECUTED FOR THIS TOPIC"})
    return o


def _plant_p1_no_strategy(o):
    """The 17-page shape: real queries, no declared strategy, banner already saying so."""
    o["search"].pop("strategy")
    return o


def _plant_p2(o):
    o["k_cascade"]["k_included_in_object"] = 99      # exceeds k3_experimental = 18
    return o


def _plant_p3(o):
    o["screening"]["eligibility_provenance"]["predefined"] = None
    return o


def _plant_p4(o):
    o["precondition_verdict"]["verdicts"]["population_stated"].pop("authority")
    return o


def _plant_p5(o):
    o["extraction"]["cells"][0].pop("verbatim")       # READ cell with a path and no sentence
    return o


PLANTS = {
    "P1_executed_search": _plant_p1,
    "P2_k_cascade": _plant_p2,
    "P3_inclusion_criteria": _plant_p3,
    "P4_preconditions": _plant_p4,
    "P5_extraction_table": _plant_p5,
}

#: Extra plants that share a property with one above. PLANTS is keyed by property, so a
#: second shape for the same property lives here and is run alongside it.
EXTRA_PLANTS = [("P1_executed_search", "no declared search strategy", _plant_p1_no_strategy)]

_EXPECTED_PRECONDITIONS = ("population_stated",)


def _call(name, obj):
    fn = PP.PROPERTIES[name]
    if name == "P4_preconditions":
        return fn(obj, expected_names=_EXPECTED_PRECONDITIONS)
    return fn(obj)


def test_control_object_holds_every_property():
    """If the control does not hold, the plants below prove nothing."""
    bad = []
    for name in PP.PROPERTIES:
        state, reason = _call(name, _ok_object())
        if state != PP.HELD:
            bad.append("%s returned %s on the CONTROL object: %s" % (name, state, reason))
    return bad


def test_each_property_refuses_a_planted_defect():
    bad = []
    for name, plant in PLANTS.items():
        state, reason = _call(name, plant(_ok_object()))
        if state == PP.HELD:
            bad.append("%s still HELD with its defect planted -- it is a password, not a "
                       "check. Reason it gave: %s" % (name, reason))
    for name, label, plant in EXTRA_PLANTS:
        state, reason = _call(name, plant(_ok_object()))
        if state == PP.HELD:
            bad.append("%s still HELD with %s planted. This is the shape served on 17 of "
                       "the 19 pages carrying the property table. Reason it gave: %s"
                       % (name, label, reason))
    return bad


def test_every_property_has_a_reachable_refusal():
    missing = sorted(set(PP.PROPERTIES) - set(PLANTS))
    return ["%s is in PROPERTIES with no plant in this file, so nothing establishes that "
            "it can refuse" % n for n in missing]


_PROP_KEY = re.compile(r"^P\d+_[a-z0-9_]+$")


def _emitted_states(tree):
    """{property name: set of state constants it is EVER assigned in this module}.

    AST, not regex. The first version of this check was a regex for
    `props["Pn"] = prop(HELD` and flagged P6, P7 and P8 -- all three of which sit inside
    an if/else that assigns REFUSING on the other branch. A regex cannot see the
    enclosing branch, so it reported three correct emitters as passwords. That was the
    THIRD over-inclusive predicate written in this lane, all three failing the same way:
    flagging correct code. Collecting the states a property is ever assigned answers the
    actual question -- can this property report anything other than HELD? -- and needs no
    knowledge of control flow at all.

    A dynamic state (`prop(*PP.p1_executed_search(obj))`) is recorded as COMPUTED: what it
    returns is established by the planted-defect tests above, not by reading this file.
    """
    import ast
    states = {}
    for node in ast.walk(tree):
        if not isinstance(node, ast.Assign):
            continue
        for target in node.targets:
            if not (isinstance(target, ast.Subscript)
                    and isinstance(target.slice, ast.Constant)
                    and isinstance(target.slice.value, str)
                    and _PROP_KEY.match(target.slice.value)):
                continue
            name = target.slice.value
            val = node.value
            if not (isinstance(val, ast.Call) and getattr(val.func, "id", None) == "prop"):
                continue
            if val.args and isinstance(val.args[0], ast.Name):
                states.setdefault(name, set()).add(val.args[0].id)
            elif val.args and isinstance(val.args[0], ast.Starred):
                states.setdefault(name, set()).add("COMPUTED")
            else:
                states.setdefault(name, set()).add("COMPUTED")
    return states


def test_no_property_is_emitted_as_a_literal_hold(source_path=None):
    """THE ONE THAT FIRES AGAINST THE PRE-FIX FILE. Parses the builder."""
    import ast
    path = Path(source_path) if source_path else (ROOT / "ssot" / "build_to_standard.py")
    tree = ast.parse(path.read_text(encoding="utf-8", errors="replace"))
    problems = []
    for name, states in sorted(_emitted_states(tree).items()):
        if states == {"HELD"}:
            problems.append(
                "%s is only ever assigned HELD in %s -- no object could make it report "
                "anything else, so it is a password, not a check" % (name, path.name))
    return problems


def main(argv):
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    source = None
    if "--source" in argv:
        source = argv[argv.index("--source") + 1]

    checks = [
        ("control object holds every property", test_control_object_holds_every_property()),
        ("each property refuses its planted defect", test_each_property_refuses_a_planted_defect()),
        ("every property has a plant", test_every_property_has_a_reachable_refusal()),
        ("no property emitted as a literal HELD",
         test_no_property_is_emitted_as_a_literal_hold(source)),
    ]
    failed = 0
    for label, problems in checks:
        if problems:
            failed += len(problems)
            print("FAIL  %s" % label)
            for p in problems:
                print("        - %s" % p)
        else:
            print("PASS  %s" % label)
    if failed:
        print("\n%d problem(s)." % failed)
        return 1
    print("\nAll property checks pass.")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
