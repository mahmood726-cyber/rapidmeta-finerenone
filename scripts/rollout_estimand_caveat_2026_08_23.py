"""Rebuild every page whose object holds the estimand-contrast caveat.

# no-control: a rollout, not a detector. Its control is that the caveat must be ABSENT from
# each page before the rebuild and PRESENT after it; a page that already carried it is
# counted separately rather than as a success, and a page that does not carry it afterwards
# is a FAILURE reported by name.

WHY. `estimand_established_does_not_cover_the_contrast_2026_08_20` is held on 125 objects,
157 occurrences, and reached ZERO delivered pages. The projector now renders it. A
projector change delivers nothing until the pages are rebuilt, and a caveat that reaches
1 page of 131 is still a caveat nobody reads.

WHAT IT SAYS: the flag records that every contributing trial measures the SAME QUANTITY and
records NOTHING about what that quantity was measured AGAINST -- whether the comparators
are of one kind, whether each comparison was randomised, whether it was concurrent. That is
the distinction that made the attr-pn withdrawal necessary.

REFUSALS ARE EXPECTED AND ARE NOT FAILURES. Some objects legitimately refuse to build --
the empty shells with no title and no results, and ARNI, which is on `do_not_rebuild`. Each
is skipped by name with its reason, and the run reports them separately from pages that
built but did not come out carrying the caveat, which is a different and worse thing.
"""
from __future__ import annotations

import io
import json
import os
import subprocess
import sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
KEY = "estimand_established_does_not_cover_the_contrast_2026_08_20"
# CASE-INSENSITIVE, BECAUSE THE PROJECTOR SENTENCE-CASES STORED PROSE.
# The object holds "records NOTHING ... AGAINST"; most pages render it as
# "records nothing ... against", and one -- SGLT2, through a path that does not tidy --
# keeps the shouted form. A case-sensitive cue matched the one page and missed the
# other 130, so this rollout was about to refuse with 128 false "BUILT BUT STILL
# MISSING IT" failures over pages that were carrying the caveat correctly. A selector
# keyed to the casing of the SOURCE rather than of the RENDER.
CUE = "records nothing about what that quantity was measured against"
BUILD = [sys.executable, os.path.join(REPO, "ssot", "build_tabbed.py")]


def targets():
    pm = json.load(io.open(os.path.join(REPO, "ssot", "PAGE_MAP.json"), encoding="utf-8"))
    try:
        sys.path.insert(0, os.path.join(REPO, "ssot"))
        import do_not_rebuild as dnr
        frozen = set(getattr(dnr, "DO_NOT_REBUILD", ()) or getattr(dnr, "PAGES", ()) or ())
    except Exception:
        frozen = set()
    out = []
    for page, rel in sorted(pm.items()):
        rel = rel.replace("\\", "/")
        obj = os.path.join(REPO, rel)
        if not os.path.isfile(obj):
            continue
        if KEY not in io.open(obj, encoding="utf-8", errors="replace").read():
            continue
        out.append((page, obj, page in frozen or os.path.basename(rel).startswith("arni")))
    return out


# THE GENERATOR FILES THIS RUN'S OUTPUT DEPENDS ON. Kept in step with
# build_tabbed._generator_stamp, which stamps each page with the last commit to touch
# any of them.
GENERATOR = ("ssot/projectors.py", "ssot/projectors2.py", "ssot/build_tabbed.py",
             "ssot/build_app_v2.py", "ssot/wysiwyg.py", "ssot/paper.py",
             "ssot/qualification_fields.py", "ssot/grade_authority.py")


def pin_or_refuse():
    """Pin the commit this run builds from, or refuse to start.

    A CONTINUOUSLY-RUNNING ROLLOUT AND A GENERATOR UNDER EDIT PRODUCE PAGES STAMPED WITH
    UNCOMMITTED CODE. That happened tonight: the rollout rebuilt IV_IRON_HF_REVIEW.html
    while generator changes were still in the working tree, the stamp gate refused the
    next commit, and the page had to be restored and the sequence redone by hand.

    Two ways to stop it, and only one is the right way round. FENCING EDITS stops the
    writing to protect the rollout; PINNING stops the rollout, and the rollout is the
    cheap thing to restart. So: one check at launch. If any generator file is dirty this
    refuses by name; otherwise it records the SHA every page in the run will carry.

    WHAT THIS BUYS BEYOND TIDINESS: every page produced by a run becomes reproducible
    from ONE commit. That is the claim the reproducibility artefact on each page has
    been making all along without being able to support it -- a run spanning three
    generator states stamps three different commits and no single checkout rebuilds it.
    """
    dirty = subprocess.run(["git", "-C", REPO, "status", "--porcelain", "--",
                            *GENERATOR], capture_output=True).stdout.decode(
        "utf-8", "replace").strip()
    if dirty:
        sys.exit(
            "REFUSED: the generator is dirty, so every page this run builds would carry\n"
            "a stamp naming a commit that does not contain the code that built it.\n\n"
            "%s\n\n"
            "Commit the generator, then start the rollout. The rollout is the cheap thing\n"
            "to restart; a page stamped with uncommitted code is not reproducible by\n"
            "anyone, including us." % dirty)
    sha = subprocess.run(["git", "-C", REPO, "log", "-1", "--format=%h", "--",
                          *GENERATOR], capture_output=True).stdout.decode(
        "utf-8", "replace").strip()
    if not sha:
        sys.exit("REFUSED: could not read a generator commit to pin to.")
    return sha


def main():
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    limit = None
    for a in sys.argv[1:]:
        if a.startswith("--limit="):
            limit = int(a.split("=", 1)[1])
    pinned = pin_or_refuse()
    tg = targets()
    if limit:
        tg = tg[:limit]
    print("")
    print("ROLLOUT: pages whose object holds the estimand-contrast caveat = %d" % len(tg))
    print("   pinned to generator commit %s -- every page in this run carries it"
          % pinned)
    print("")
    already = built = frozen_n = refused = missing = 0
    fails, refusals = [], []
    for page, obj, is_frozen in tg:
        path = os.path.join(REPO, page)
        before = io.open(path, encoding="utf-8", errors="replace").read() \
            if os.path.isfile(path) else ""
        if CUE in before.lower():
            already += 1
            continue
        if is_frozen:
            frozen_n += 1
            refusals.append((page, "on do_not_rebuild -- not rebuilt by instruction"))
            continue
        r = subprocess.run(BUILD + [obj, path], cwd=REPO, capture_output=True)
        if r.returncode != 0:
            tail = r.stdout.decode("utf-8", "replace").strip().split("\n")[-1][:150]
            refused += 1
            refusals.append((page, tail or "build refused"))
            continue
        after = io.open(path, encoding="utf-8", errors="replace").read()
        if CUE in after.lower():
            built += 1
            sys.stdout.write(".")
            sys.stdout.flush()
        else:
            missing += 1
            fails.append(page)
    print("")
    print("")
    print("   already carried it                %4d" % already)
    print("   rebuilt and now carry it          %4d" % built)
    print("   frozen (do_not_rebuild)           %4d" % frozen_n)
    print("   build refused, by the object      %4d" % refused)
    print("   BUILT BUT STILL MISSING IT        %4d   <- the only failure state" % missing)
    print("   %-33s %4d   == the population" % ("sum",
          already + built + frozen_n + refused + missing))
    print("")
    for page, why in refusals[:30]:
        print("   skipped %-46s %s" % (page[:46], why[:90]))
    if fails:
        print("")
        for p in fails:
            print("   FAILED  %s" % p)
        sys.exit("REFUSED: %d page(s) rebuilt without the caveat their object holds."
                 % len(fails))


if __name__ == "__main__":
    main()
