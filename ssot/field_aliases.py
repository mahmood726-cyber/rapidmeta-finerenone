"""One concept, several spellings. ONE map, read by every surface.

WHY THIS EXISTS AND WHY IT IS NOT A DATA CHANGE. A sweep on 2026-08-23 found seven key pairs
and one value pair where the corpus stores one concept under two names, never co-occurring:

    screening.dual_screening        /  screening.duplicate_screening      ARNI vs SGLT2
    results.*.pooled.withdrawn_reason / absent_reason / withdrawn_because  86 / 10 / 3 objects
    inputs.trials[].id              /  trial_id                           111 / 20
    inputs.trials[].read_utc        /  registration_read_utc              74 / 26
    outcomes[].comparator_type      /  comparator / comparator_kind       127 / 127 / 1
    handbook_authority              /  methodological_authority           68 / 44
    state                           /  topic_state                        14 / 89
    model VALUE "random-effects"    /  "random"                           110 / 8

THE CONSEQUENCE IS ALWAYS SILENT. A surface reading only `withdrawn_reason` reports NO REASON
on the ten objects that record one under `absent_reason` -- so a page withholds the reason an
estimate was withdrawn, which is the single thing this project exists to not do. It was found
this way: a projection read only `duplicate_screening` and reported "no screening record" for
the ONE object in the corpus that holds a named adjudicator.

UNIFYING THE DATA IS NOT THIS FILE'S DECISION. That is 155 objects and it is Mahmood's. This
makes every READER tolerant, today, which decides nothing and stops the false absences.

READ FROM HERE, NEVER FROM PER-SITE ALTERNATES. Two call sites listing their own spellings is
the same defect one level up: they drift, and the one that drifts is the one nobody re-reads.
"""

# concept -> the spellings, most common first. Order matters only for reporting.
KEY_ALIASES = {
    "screening_record": ("duplicate_screening", "dual_screening"),
    "withdrawal_reason": ("withdrawn_reason", "absent_reason", "withdrawn_because"),
    "trial_identifier": ("id", "trial_id", "registry_id"),
    "registration_read": ("registration_read_utc", "read_utc"),
    "comparator": ("comparator_type", "comparator", "comparator_kind"),
    "authority": ("handbook_authority", "methodological_authority"),
    "topic_state": ("topic_state", "state"),
}

# value spellings, per field
VALUE_ALIASES = {
    "model": {"random-effects": ("random-effects", "random"),
              "fixed-effect": ("fixed-effect", "fixed", "common-effect")},
}


def get(d, concept, default=None):
    """The first spelling of `concept` this mapping actually holds."""
    if not isinstance(d, dict):
        return default
    for k in KEY_ALIASES.get(concept, ()):
        if k in d and d[k] not in (None, "", {}, []):
            return d[k]
    return default


def which_spelling(mapping, concept):
    """Which spelling was found -- for reporting that an alias did the work.

    NAMED `which_spelling` RATHER THAN `which`: `lint_string_where_collection_expected`
    knows a helper called `which(d=...)` whose `d` is membership-tested, and an unrelated
    function sharing the name tripped it. A name that collides with a linted signature is a
    name that will be misread by a person too.
    """
    if not isinstance(mapping, dict):
        return None
    for k in KEY_ALIASES.get(concept, ()):
        if k in mapping and mapping[k] not in (None, "", {}, []):
            return k
    return None


def canonical_value(field, value):
    """A value under its canonical spelling, so `random` and `random-effects` are one thing."""
    if value is None:
        return None
    v = str(value).strip().lower()
    for canon, spellings in (VALUE_ALIASES.get(field) or {}).items():
        if v in spellings:
            return canon
    return v


def all_key_spellings():
    out = set()
    for v in KEY_ALIASES.values():
        out.update(v)
    return out
