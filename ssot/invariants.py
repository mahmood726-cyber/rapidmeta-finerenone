"""General pipeline invariants. Not owned by the assessor harness.

IDENTICAL OUTPUT FROM DIFFERENT INPUTS IS A GENERAL LAW, NOT AN ASSESSOR RULE.

It was written as detector 4 in the assessor registry, where it caught `subject_role` --
one check registered under two names. It then caught something the registry could never
have seen: a two-hop resolution cache keyed on BATCH POSITION rather than content, where
three articles carrying 26, 53 and 86 references returned byte-identical results.

Any pipeline in this repo can call it. If two runs over different inputs agree exactly,
either the inputs are not different or the pipeline is not reading them.
"""
import collections
import hashlib


def identical_output_alarm(results, min_inputs=2):
    """results = {label: any-hashable-or-reprable}. Returns alarm strings, possibly empty."""
    if len(results) < min_inputs:
        return []
    groups = collections.defaultdict(list)
    for label, value in results.items():
        groups[repr(value)].append(label)
    return [f"identical output from different inputs: {sorted(labels)} -- either the inputs "
            f"are not different or the pipeline is not reading them"
            for labels in groups.values() if len(labels) > 1]


def content_cache_key(*parts):
    """THE CACHE KEY IS DERIVED FROM CONTENT. Three cache defects in one night, one root:

        keyed on EXISTENCE  -> a 0-byte file cached forever, and every later run reported
                               a transport failure as unparseable DATA.
        keyed on POSITION   -> `hop2_{batch_index}` with index always 0, so every input
                               after the first read the first one's file.
        keyed on NEITHER    -> no key at all; the first answer became every answer.

    A cache is invisible when it works and indistinguishable from a finding when it does
    not. All three produced results that looked like data.
    """
    return hashlib.sha1("\x00".join(str(p) for p in parts).encode()).hexdigest()[:16]


def cache_is_valid(path):
    """Zero bytes is a MISS, not a hit. Existence is not content."""
    import os
    return os.path.exists(path) and os.path.getsize(path) > 0
