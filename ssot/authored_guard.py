"""Refuse to overwrite AUTHORED manuscript prose. The one thing in this corpus that cannot be regenerated.

WHY THIS IS NARROWER THAN THE DO-NOT-REBUILD LIST, AND DELIBERATELY SO. An audit on 2026-08-23
found 70 scripts that mutate `ssot/**/*.json` and 2 that import a do-not-rebuild check. Guarding
all 70 is a large change nobody asked for. But `manuscript.*` is different in kind from every
other field: everything else is PROJECTED FROM DATA and can be rebuilt from the object, and the
authored prose cannot. If it is overwritten it is gone, and the only copy is in git history
that nobody will think to look at because the write will have looked successful.

THE NEAR-MISS. `build_paper_bookkeeping_2026_08_21.py` writes

    man["references"] = refs                                     <- UNCONDITIONAL
    if intro and not str(man.get("introduction") or "").strip():  <- GUARDED, two lines later

One field in one function is careful and the other is not, which means somebody already knew
the guard was needed and applied it to one field and not the next. Run with `--all` it would
have replaced ARNI's five authored references with a projection, and `do_not_rebuild` did not
stop it because THAT LIST GUARDS THE BUILDER AND THE WRITE CAME THROUGH A DIFFERENT DOOR.

THE MARKER IS THE OBJECT'S OWN. `manuscript._provenance` on an authored object begins "The
interpretive prose below is AUTHORED by the review team and stored in the canonical object so
that it is reviewable and identical across every surface." So the guard asks the object rather
than consulting a list of names -- a list has to be maintained and a marker travels with the
data.

THIS DOES NOT FREEZE THE FIELD. A projected manuscript has no such marker and is rewritten
normally, which is right: references must track the trials. Only prose a person wrote is
protected, and the override is per-field and loud.
"""
import os
import sys

MARKER = "AUTHORED"
PROV = "_provenance"


def is_authored(manuscript):
    """True when the object itself says a person wrote this prose."""
    if not isinstance(manuscript, dict):
        return False
    p = manuscript.get(PROV)
    return isinstance(p, str) and MARKER in p


def refuse_if_authored(manuscript, field, topic, where):
    """Refuse a write to `manuscript[field]` when the manuscript is marked authored.

    Returns False when the write may proceed. Exits otherwise -- BEFORE the write, so nothing
    has been changed. `OVERWRITE_AUTHORED=<topic>.<field>` permits exactly one field on one
    topic and says what it is destroying; there is no blanket override, for the same reason
    `do_not_rebuild` has none: a variable that unlocks everything gets exported once and
    forgotten.
    """
    if not is_authored(manuscript):
        return False
    existing = manuscript.get(field)
    if existing in (None, "", {}, []):
        return False                     # nothing there to destroy
    token = "%s.%s" % (topic, field)
    if os.environ.get("OVERWRITE_AUTHORED", "").strip() == token:
        sys.stderr.write(
            "[authored-guard] OVERRIDDEN for %s. Replacing prose a person wrote, from %s.\n"
            % (token, where))
        return False
    sys.exit(
        "REFUSED: %s would overwrite manuscript.%s on `%s`, and that manuscript is marked "
        "AUTHORED by the review team.\n\n"
        "  Authored prose is the only content in this corpus that cannot be regenerated from "
        "the object.\n"
        "  This check runs BEFORE the write, so nothing has been changed.\n"
        "  To proceed deliberately for this one field:  OVERWRITE_AUTHORED=%s <command>\n"
        % (where, field, topic, token))
