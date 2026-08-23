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
import io
import os
import sys

PAGES = {
    "ARNI_HF_REVIEW.html": (
        "AUTHORED DOCMODEL MANUSCRIPT. The projector reproduces roughly 26% of it, so a "
        "rebuild replaces written argument with a projection. Standing instruction from "
        "Mahmood; ssot/manuscript_guard.py is the second line, not the first."),
}

# RELEASED 2026-08-21, DECIDED BY MAHMOOD, RECORDED HERE RATHER THAN IN A REPORT.
#
#     TIGECYCLINE_CIAI_SSOT.html   was protected because it is built by different code -- 36 KB
#                                  where a tabbed build is 1.6 MB -- and was NOT in PAGE_MAP, so
#                                  rebuilding it REPLACED A PAGE A READER ALREADY HAD with one
#                                  from another generator. That is a publication decision and it
#                                  was not the author's to take; it was taken anyway, the same
#                                  day it was recorded, which is why this list moved into the
#                                  builder.
#
# BEFORE RELEASING IT THE OLD PAGE WAS READ, not assumed reproducible. 142 visible blocks,
# 29,372 characters. Four blocks contain wording not present in the object; three are table
# headers (`Source of this cell`, `Sources`, `Layer Source How it was obtained`). The fourth is
# a Paule-Mandel sensitivity row, `PM ordinary (Wald) 0.9348 (0.8864 to 0.9859) 0.000178` -- and
# every number in it IS on the object, under an estimator-comparison block keyed
# `between_study_variance_estimator: "PM"`. Only the expansion of the abbreviation was display
# sugar. Nothing a reader currently has is lost by the rebuild.


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


def _topic_to_page():
    """topic dir name -> delivered page name, from PAGE_MAP."""
    import json
    m = os.path.join(os.path.dirname(os.path.abspath(__file__)), "PAGE_MAP.json")
    try:
        pm = json.load(io.open(m, encoding="utf-8"))
    except Exception:
        return {}
    out = {}
    if isinstance(pm, dict):
        for page, obj in pm.items():
            out[os.path.basename(os.path.dirname(str(obj)))] = page
    return out


def check_object(path_or_topic):
    """Refuse before a WRITE if this object backs a protected page.

    THE GAP THIS CLOSES, FOUND 2026-08-23 AND IT WOULD HAVE DESTROYED AUTHORED WORK.

    `check()` above takes an OUT_PATH -- a page -- so it guards the BUILDER. It does not guard
    the WRITERS, which take an object path and never see a page name.
    `scripts/build_paper_bookkeeping_2026_08_21.py` writes `manuscript.references`
    UNCONDITIONALLY (`man["references"] = refs`, no guard) while guarding `introduction` two
    lines later -- so one field in one function is careful and the other is not.

    Run with `--all`, it would have replaced ARNI's five authored references with a
    projection. `do_not_rebuild` did not stop it BECAUSE THAT LIST GUARDED THE BUILDER AND THE
    WRITE CAME THROUGH A DIFFERENT DOOR. That is the same class as the de-indexing that
    updated index.html and sitemap.xml and not audit_table.html: a protection applied to the
    surfaces its author was thinking about.

    A guard that depends on the operator remembering to pass the right arguments is not a
    guard, so this refuses on its own.
    """
    t = str(path_or_topic)
    topic = t
    if os.path.sep in t or "/" in t:
        topic = os.path.basename(os.path.dirname(t.replace("/", os.path.sep)))
    page = _topic_to_page().get(topic)
    why = PAGES.get(page) if page else None
    if not why:
        return False
    if os.environ.get("REBUILD_ANYWAY", "").strip() == page:
        sys.stderr.write(
            "[do-not-rebuild] OVERRIDDEN for object %s (page %s). Protected because: %s\n"
            % (topic, page, why))
        return False
    sys.exit(
        "REFUSED: the object `%s` backs %s, which is on the do-not-rebuild list.\n\n  %s\n\n"
        "  This check runs BEFORE the write, so nothing has been changed.\n"
        "  To proceed deliberately:  REBUILD_ANYWAY=%s <command>\n"
        "  There is no blanket override." % (topic, page, why, page))
