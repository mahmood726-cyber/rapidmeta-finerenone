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
        "Mahmood; ssot/manuscript_guard.py is the second line, not the first. "
        "  WHAT WOULD BE LOST, stated because a do-not-rebuild flag with no named cost is "
        "an instruction someone eventually overrules: roughly three quarters of this page "
        "is written argument that exists NOWHERE ELSE -- not on the object, not in any "
        "other page. It is the corpus's ONLY authored manuscript, and authorship is the "
        "property the whole programme is trying to acquire. A rebuild trades that for a "
        "projection. "
        "  AND IT IS NOT PURELY AUTHORED. Its F1000 prose carries [[certainty]] "
        "substitution tokens, already resolved and baked in -- a hand-written surface with "
        "generated holes. So a defect here can appear in prose as well as in a rendered "
        "cell, and a fix that only corrects the generated-looking surfaces leaves the "
        "prose asserting what the rest of the page withholds. On 2026-08-27 that was five "
        "published certainty levels, not the three a gate reading rendered cells found. "
        "  HOW TO MAINTAIN IT: edit it BY HAND. That is not the edited-not-rebuilt defect "
        "-- that defect is hand-editing a GENERATED artefact, where the next build "
        "silently reverts you. Hand-editing a hand-written surface is simply maintenance."),
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


# ---------------------------------------------------------------------------------------
# GENERATOR-PIN PRECONDITION. In the path, not in the notes.
# ---------------------------------------------------------------------------------------
#
# A REBUILD CAN REVERT A SERVED FIX, AND ON 2026-08-27 ONE NEARLY DID. IV_IRON_HF was rebuilt
# from a worktree whose renderer predated 7f18a5da2 ("derive the direction-of-benefit label,
# never default it"), which rewrote ssot/build_app_v2.py. That commit was already on main and
# already serving eight render-layer corrections -- one inverted KCCQ label and seven
# manufactured direction claims. The rebuild did not revert them, but only because none of
# the eight happened to be on the two pages it touched. Exposure is not damage, and a
# near-miss explainable only by luck is a finding about the system.
#
# THE FIX IS A PRECONDITION, NOT A HABIT. The rule "check the pin before rebuilding" was
# already known and was not applied, because a rule that lives in prose gets violated -- this
# project has paid for that twice in one night with the exit-status-through-a-pipe rule. So
# the check runs where the build cannot avoid it, beside the do-not-rebuild refusal, before
# anything is written.
#
# ADMISSION CRITERION -- AN ENTRY MAY ONLY REGISTER A COMMIT THAT CHANGED THE GENERATOR.
# A hand-edit to served HTML cannot be guaranteed by an ancestry check BY CONSTRUCTION: the
# rebuild regenerates the file from the object and overwrites it, so the commit stays an
# ancestor forever while the fix is gone. On 2026-08-27 three such commits were registered
# here and then removed -- 463c6d625, 048cf178b and 424e8aa0d changed nine served .html files
# and zero .py and zero .json between them. Checked by rebuilding, one of the nine came back
# with the pre-edit text.
#
# A LEDGER ENTRY THAT CANNOT BE KEPT IS WORSE THAN A MISSING ONE. A missing entry prompts a
# question; a false one closes it.
#
# Before adding a commit, run:  git show --name-only --format= <sha> | grep -E '\.(py)$'
# If that is empty, the commit changed no generator and DOES NOT BELONG HERE. Record it in
# the handover instead, where a claim does not carry a guarantee.
#
# And the description is never the evidence. 7f18a5da2's entry says it "carries eight served
# render corrections"; it landed 23:43 and those corrections landed 23:55, 00:24 and 00:30,
# none of them its ancestor. Ancestry is the evidence. Prose is a label.
#
# HOW TO EXTEND IT: add a commit here when a renderer fix must not be reverted by a rebuild.
# The entry is a promise that the built page will carry that fix.
# THE ENTRY IS ADDED IN A SEPARATE COMMIT FROM THE FIX IT NAMES, AND THAT IS DELIBERATE.
# A commit cannot contain its own SHA, so registering a fix in the same commit would mean
# either a placeholder or a rewritten hash -- and the entry would then be an assertion about
# itself rather than a checkable fact. Two commits keeps the ledger VERIFIABLE: every SHA
# here names a commit that already exists and can be resolved. Do not "simplify" this into
# one commit; it quietly breaks that property.
REQUIRED_GENERATOR_COMMITS = {
    "a441e41870bf1befc68b0854a4c1f48487862339": (
        "read arm counts THROUGH to as_posted instead of copying them into arms -- a trial "
        "storing no arms now derives the cell from the one authoritative location and states "
        "its provenance, its read date, that the counts are UNCORRECTED, and whether a "
        "continuity correction applies. Without it those pages say 'not recorded on this "
        "object' while the object holds the counts a field away"),
    "7f18a5da2": ("derive the direction-of-benefit label, never default it -- rewrote "
                  "ssot/build_app_v2.py and carries eight served render corrections"),
    "561ebb9dd": ("derive or refuse the effect scale, the subgroup heading and the "
                  "estimator name -- without it a rebuilt page can state 'on the natural "
                  "scale' for a ratio measure, which is a log-scale quantity"),
    # FULL sha deliberately. The two above are nine characters, which git resolves today;
    # this repository carries several thousand branches and an abbreviation that is unique
    # now need not stay unique, and an ambiguous rev makes this gate fail in the direction
    # of refusing a build it cannot name a reason for.
    "c5409eaa1f32461e4ab1bfb57855bac5fb63f1e4": (
        "absence handling in build_app_v2 -- a direct subscript on a field that may be "
        "absent crashed the build on 57 of 141 objects at four keys, one of which is the "
        "literal sentence an object stores AS a source id. The generator failed SAFE but "
        "it failed at BUILD time, so the honest sentence was never written and affected "
        "pages stayed frozen at whatever they last said, including four whose fix was "
        "already on main and could not reach a reader"),
    # FULL sha, per the note above: this repository carries several thousand branches.
    "95bddba58a75b06793c0655f60091244c941cc6e": (
        "emit the store path in the served bytes -- <html data-store=\"ssot/<id>/<id>.json\">. "
        "Without it a rebuilt page states the generator that made it and not the object it "
        "is about: measured 2026-08-27, 31 of 144 pages declared their object and 138 "
        "declared their generator, which is why attribution was forensic rather than a "
        "lookup. The same commit stops lane_rob/provenance.py counting untracked build "
        "output as dirt, which had pinned git_dirty true on every record that lane wrote"),
    "767a8de9affbc091ecd6c1c8c2649d65fe5b09ac": (
        "declare what the page IS and which pool each number came from -- "
        "<html data-artefact=\"review|tool\"> and <tr data-pool=\"<outcome_id>\"> on the "
        "summary-of-findings row. Without it, establishing that 744 of 1,463 served pages "
        "are unpopulated shells wearing the full apparatus of a review takes a census and 58 "
        "pages opened by hand, and three checks stay unbuildable because no page links a "
        "stated number to the pool it came from"),

    # ADDED 2026-08-27 AFTER CHECKING RATHER THAN ASSUMING. Asked to prove a rebuild could
    # not revert the five served fixes of 08-26, I found the ledger did not guard four of
    # them at all. They are ancestors of THIS head, so a rebuild from here keeps them -- but
    # that is a property of my base, not of the ledger, and the ledger is what the next lane
    # relies on. The fifth (b2afcce50, 47 orphan stubs) is a file-deletion fix a page
    # rebuild cannot reintroduce: 47 removed, 0 present in this tree.
    "36ae41332611a33a37ff041d158683f6dd8698a3": (
        "per-outcome participant counts, the withdrawn-state fallthrough, and a gate that was passing an empty set. Without it a rebuilt page restates a review-level denominator against an outcome that did not use it"),

    "509dde275afa81c877332ad930d783b954de3fde": (
        "the risk-of-bias traffic-light legend, after 948cec5ef made an out-of-scale domain draw as an open square. Without it a rebuilt page labels nine squares as circles and contradicts itself; reverting the glyph instead would return No information as a fourth RoB 2 judgement, which is the defect 948cec5ef removed"),
}


def check_generator_pin(repo=None):
    """Refuse before the build if the working generator lacks a required renderer fix."""
    import subprocess
    root = repo or os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    missing = []
    for sha, why in sorted(REQUIRED_GENERATOR_COMMITS.items()):
        r = subprocess.run(["git", "merge-base", "--is-ancestor", sha, "HEAD"],
                           cwd=root, capture_output=True)
        if r.returncode == 128:
            # THE COMMIT IS NOT IN THIS REPOSITORY AT ALL. That is not a pass. A check that
            # treats "cannot evaluate" as "satisfied" is the silent-success failure this
            # project has now hit in five tools.
            missing.append((sha, why, "not present in this repository"))
        elif r.returncode != 0:
            missing.append((sha, why, "not an ancestor of HEAD"))
    if not missing:
        return
    if os.environ.get("REBUILD_STALE_GENERATOR_ANYWAY", "").strip() == "1":
        sys.stderr.write(
            "[generator-pin] OVERRIDDEN. Building against a generator missing: %s\n"
            % ", ".join(s for s, _, _ in missing))
        return
    sys.exit(
        "REFUSED: this generator is missing a renderer fix that is already SERVED, so the "
        "rebuilt page would revert it.\n\n"
        + "".join("  %s  %s\n     %s\n" % (s, st, why) for s, why, st in missing)
        + "\n  Rebuilding now would ship a reader-facing regression on the way in.\n"
          "  Merge or rebase onto a commit containing it, then rebuild.\n"
          "  This check runs BEFORE the build, so nothing has been written.\n"
          "  Deliberate override for one run:  REBUILD_STALE_GENERATOR_ANYWAY=1 <command>")


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
