"""ONE predicate for "is this field a qualification", shared by the audit and the renderer.

WHY THIS IS A MODULE AND NOT TWO COPIES. `dual_screening` and `duplicate_screening` are in
this corpus because one concept was given two names by two authors who each needed it. Two
PREDICATES for one concept fails the same way and is harder to see: the audit would report a
number the renderer does not act on, and both would be defensible in isolation. The measure
of whether the rendering work succeeded is the audit's own count moving, and that is only
meaningful if the two agree by construction rather than by review.

WHAT A QUALIFICATION IS, HERE. A field whose job is to qualify, caveat, scope, bound or
guard a claim -- judged by its NAME against vocabulary this corpus actually uses, plus any
sentence-shaped key, which in this corpus is nearly always a finding written where a name
should be.

WHY SHAPE AND NOT A WHITELIST. Measured over the corpus: qualifications held on 50+ objects
reach a reader 73% of the time; those held on exactly ONE object, 30%. 261 of 338 distinct
qualifying fields exist on a single object, and 182 of those reach nobody.

    THE CORPUS PROJECTS ITS SCHEMA AND DOES NOT PROJECT ITS ONE-OFFS. Projection is
    schema-driven while findings are written ad hoc, so the moment an author invents a field
    name to hold something important, they have written it where no page looks.

A whitelist would fight the thing that makes this corpus good -- an author noticing
something specific and naming it in words that fit. The asymmetry decides it: AN UNRENDERED
QUALIFICATION IS INVISIBLE; A GENERICALLY RENDERED ONE IS MERELY UNTIDY. The cost is real
and is stated rather than hidden: some internal bookkeeping will surface that was never
meant for a reader. That is a tuning problem, and it is a better problem than the one it
replaces.
"""
from __future__ import annotations

import re

# Vocabulary read off this corpus, not invented.
QUAL = ("does_not", "doesnt", "not_claimed", "not_established", "not_cover",
        "limitation", "caveat", "qualification", "qualif", "scope", "bound",
        "what_is_not", "cannot", "must_not", "does_not_establish", "not_poolable_because",
        "absent", "withheld", "refus", "unless", "only_if", "does_not_apply",
        "not_shown", "not_verified", "uncertain", "assumption")

# Names that match the vocabulary but are NOT qualifications: the scope of a search, an
# absent-state machine field, a reason already rendered in its own place. Excluded by name,
# and the exclusion is printed by the audit so a reader can disagree and recount.
NOT_QUAL = ("scope_decisions", "absent_from_source", "absent_reason", "scope_of_this_rule",
            "withdrawn_reason", "withdrawn_because", "boundary_scope")

# A key with six or more underscore-separated words is a sentence, and a sentence used as a
# key is a finding written where a name should be.
SENTENCE = re.compile(r"^[a-zA-Z][a-zA-Z0-9]*(_[a-zA-Z0-9]+){5,}$")

MIN_VALUE_CHARS = 60


def is_qualification(key):
    """True when this field NAME is doing qualification work."""
    kl = str(key).lower()
    if kl in NOT_QUAL:
        return False
    if any(q in kl for q in QUAL):
        return True
    return bool(SENTENCE.match(str(key))) and len(str(key)) > 34


def qualifying_items(obj, skip=()):
    """(key, value) for every qualification held anywhere in this object.

    `skip` names keys the caller renders in a bespoke place already, so the generic block
    does not repeat them. Nothing is dropped silently: the caller decides, and the audit
    counts the field either way.
    """
    out = []
    seen = set()

    def walk(x):
        if isinstance(x, dict):
            for k, v in x.items():
                if (isinstance(v, str) and len(v) >= MIN_VALUE_CHARS
                        and is_qualification(k) and k not in skip):
                    sig = (k, v[:120])
                    if sig not in seen:
                        seen.add(sig)
                        out.append((k, v))
                walk(v)
        elif isinstance(x, list):
            for v in x:
                walk(v)

    walk(obj)
    return out


def human(key):
    """A field name as a heading, without inventing words it does not contain."""
    s = re.sub(r"_20\d\d_\d\d_\d\d$", "", str(key))
    s = s.replace("_", " ").strip()
    return (s[:1].upper() + s[1:]) if s else str(key)
