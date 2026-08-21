"""Pages that must not be rebuilt, and the check that runs BEFORE the build.

A DECISION RECORDED ONLY IN A REPORT IS NOT A CONSTRAINT ON THE NEXT COMMAND.

Twice now a page has been rebuilt that had been explicitly decided against:

    ARNI_HF_REVIEW.html          an authored docmodel manuscript. The projector reproduces
                                 about a quarter of it, so a rebuild replaces written argument
                                 with a projection. Caught by `manuscript_guard`, which is a
                                 SECOND line and fired for its own reason rather than for this
                                 one.
    TIGECYCLINE_CIAI_SSOT.html   built by different code, 36 KB against a tabbed build's
                                 1.6 MB, and NOT in PAGE_MAP. It was recorded, in writing, that
                                 mapping or rebuilding it REPLACES A PAGE A READER ALREADY HAS
                                 and is a publication decision. It was then rebuilt anyway,
                                 in the same session, by the author who wrote that sentence.
                                 Caught by reading the byte count in the build output.

Both times the stop was a person or an unrelated guard. This module is the mechanical one.

WHY IT LIVES HERE AND NOT IN A SCRIPT. The list was duplicated in
`scripts/rollout_figures_2026_08_20.py` and `scripts/rebuild_paper_corpus_2026_08_20.py`, and
`scripts/audit_standing_instructions.py` had already flagged that -- "DO_NOT_REBUILD list lives
in one script, not in a shared module". Two copies means a third caller inherits neither, and
`build_tabbed.py` invoked directly was exactly that third caller: BOTH overwrites went through
it, and it knew nothing about either list.

    THE CHECK NOW SITS IN THE BUILDER, so it fires whatever calls it -- a rollout script, a
    one-off command line, or a loop written at three in the morning.

OVERRIDE, DELIBERATE AND LOUD. `REBUILD_ANYWAY=<page name>` permits exactly that one page and
prints why it was protected. There is no blanket override: a variable that unlocks the whole
list is a variable that gets exported once and forgotten.
"""
import os
import sys

PAGES = {
    "ARNI_HF_REVIEW.html": (
        "AUTHORED DOCMODEL MANUSCRIPT. The projector reproduces roughly 26% of it, so a "
        "rebuild replaces written argument with a projection. Standing instruction from "
        "Mahmood; ssot/manuscript_guard.py is the second line, not the first."),
    "TIGECYCLINE_CIAI_SSOT.html": (
        "BUILT BY DIFFERENT CODE AND NOT IN PAGE_MAP. 36 KB where a tabbed build is 1.6 MB. "
        "Rebuilding it REPLACES A PAGE A READER ALREADY HAS with one produced by another "
        "generator, which is a publication decision and belongs to Mahmood. Recorded as held "
        "on 2026-08-21, then rebuilt the same day by the author who recorded it -- which is "
        "why this list exists in the builder rather than in a report."),
}


def check(out_path):
    """Refuse before the build if `out_path` names a protected page."""
    name = os.path.basename(str(out_path))
    why = PAGES.get(name)
    if not why:
        return
    if os.environ.get("REBUILD_ANYWAY", "").strip() == name:
        sys.stderr.write(
            "[do-not-rebuild] OVERRIDDEN for %s. It is protected because: %s\n" % (name, why))
        return
    sys.exit(
        "REFUSED: %s is on the do-not-rebuild list.\n\n  %s\n\n"
        "  This check runs BEFORE the build, so nothing has been written.\n"
        "  To proceed deliberately for this one page:  REBUILD_ANYWAY=%s <command>\n"
        "  There is no blanket override." % (name, why, name))
