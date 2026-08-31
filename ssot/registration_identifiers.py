#!/usr/bin/env python3
r"""THE ONE PLACE THAT KNOWS WHAT A TRIAL REGISTRATION IDENTIFIER LOOKS LIKE.

    THIS MODULE EXISTS BECAUSE A DOCUMENTED RULE FAILED AT A RANGE OF TWELVE INCHES.

On 2026-08-26 `gate_screening_row_has_registration_id` was written matching only `NCT\d{8}`.
It accused 663 screening rows of being unauditable; the rows were fine and the matcher was
narrow. It was widened to cover ISRCTN, EudraCT, NTR, ACTRN and ChiCTR.

Hours later, the same author wrote `measure_topic_trial_retrievability` with
`if not NCT.match(n): continue` -- the narrow version again, in the next file along, on the
same night, with the corrected pattern already open in the editor. A third gate caught it.

    Knowledge recorded and connected to nothing. Not a rule in a document, not a memory from
    last week -- the correct code, twelve inches away, written by the same hand the same day.
    If a rule can fail at that range, no amount of documentation closes it. Only a shared
    constant does.

So: one pattern, one module, imported. A future widening happens here and reaches every
caller, and a caller that wants a narrower rule has to say so out loud by not importing this.

MEASURED, so the scope of the current risk is bounded rather than feared. Across
`inputs.trials` on 2026-08-27: 403 identifiers, ALL of them NCT, 0 other-registry,
0 unrecognised, 4 trials carrying no identifier field at all. The non-NCT branch is therefore
DEAD CODE ON THIS CORPUS TODAY and is kept because the first non-NCT trial admitted would
otherwise vanish from every denominator without a message.
"""
import re

NCT = re.compile(r"NCT\d{8}")

# Every non-ClinicalTrials.gov register this corpus cites or plausibly will. Widen HERE.
OTHER_REGISTRY = re.compile(
    r"\b(ISRCTN\d{6,8}"
    r"|EudraCT\s*\d{4}-\d{6}-\d{2}"
    r"|NTR\d{3,5}"
    r"|ACTRN\d{14}"
    r"|ChiCTR[-\w]*\d{6,}"
    r"|CTRI/\d{4}/\d{2,3}/\d{6}"
    r"|JPRN-[\w\d]+"
    r"|IRCT\d{11,}"
    r"|PACTR\d{12,})\b", re.I)

ANY = re.compile("(%s|%s)" % (NCT.pattern, OTHER_REGISTRY.pattern), re.I)


def is_registration_id(s):
    """True if `s` IS a registration identifier -- the POSITIVE property.

    Named positively on purpose. `audit_exclusion_by_absence` exists because
    `absence of X` gets used where `is a Y` was meant, and a helper called
    `is_registration_id` is harder to misuse in that direction than a bare regex.
    """
    return bool(s) and bool(ANY.fullmatch(str(s).strip()))


def find_registration_ids(blob):
    """Every registration identifier appearing anywhere in a string."""
    return sorted({m.group(0) for m in ANY.finditer(str(blob))})
