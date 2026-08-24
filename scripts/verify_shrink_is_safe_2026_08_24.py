"""Is a manuscript that got SHORTER still saying everything it said before?

WHY THIS EXISTS. Tonight's projector changes made 45 of 162 pages shrink past the -5% the
build guard refuses at. Every one of them has a plausible innocent explanation -- a false
39-character placeholder ("title not recorded in the registry read") replaced by a real and
shorter trial name, or a fifty-word title stated once instead of seven times. Plausible is
not measured, and "I know why it shrank" is exactly the reasoning that ships a regression.

SO THE CLAIM IS TESTED AS A PROPERTY, not as a story about intent:

    a shrink is safe if the new text loses NO REGISTRATION and NO REPORTED NUMBER.

Both are extractable from either version without knowing anything about what changed. A
page may lose words freely -- repetition, placeholders, apparatus -- but the moment it loses
an NCT id or an estimate, it has stopped reporting something it used to report, whatever the
diff looks like and however good the reason sounded.

Numbers are compared as the SET of numeric tokens, which is deliberately strict in one
direction: a formatting change from 0.7171 to 0.72 registers as a loss. That is wanted here.
Rounding a pooled estimate IS a change to what the page reports, and it should have to be
declared rather than absorbed into a percentage.
"""
import io
import json
import os
import re
import subprocess
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__))), "ssot"))

import paper_projector as P          # noqa: E402
import statement as S                # noqa: E402

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_NCT = re.compile(r"NCT\d{8}")
# A number as a reader meets it: 0.72, 10584, 95, 1.05. Not the digits inside an NCT id,
# which are stripped first, and not a bare year attached to a word.
_NUM = re.compile(r"(?<![\w.])\d+(?:\.\d+)?(?![\w])")


def delivered_paper_text(path):
    """The paper tab of a built page, as text, or None."""
    if not os.path.exists(path):
        return None
    h = io.open(path, encoding="utf-8", errors="replace").read()
    m = re.search(r'id="pn-paper"(.*?)(?:id="pn-[a-z]|<!--\s*end-paper)', h, re.S)
    if not m:
        return None
    seg = re.sub(r"<(script|style)\b.*?</\1>", " ", m.group(1), flags=re.S)
    return re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", seg))


def rebuilt_paper_text(src, page):
    """Build this page to a SCRATCH path and read the same tab back out of it.

    THE FIRST VERSION OF THIS COMPARED THE DELIVERED PAGE AGAINST `P.render(...)`, AND THAT
    IS NOT A COMPARISON. The delivered paper tab contains figures, extended data and
    references; the projector's text render does not. So the check reported 141 of 148 pages
    "losing" numbers, and the lost numbers were figure axis ticks -- 0.5, 0.6, 0.7 -- and
    DOI prefixes like 10.1136. Nothing had been lost at all; the two sides were different
    documents.

    That is the same mistake as reading a manuscript out of a CLI debug render earlier
    tonight and concluding a software exception was reaching readers. A property check is
    only as sound as the two things it puts side by side, and when a check reports that
    almost everything is broken, the instrument is the first suspect.

    So: same builder, same extraction, both sides. Slow -- a build per page -- but the
    raster cache makes it a few seconds each, and it is the only version that measures what
    it claims to.
    """
    scratch = os.path.join(REPO, "outputs", "_shrink_check", page)
    os.makedirs(os.path.dirname(scratch), exist_ok=True)
    # DELETE LAST RUN'S COPY FIRST, or this check silently measures its own history.
    #
    # `build_tabbed` refuses to overwrite a delivered manuscript that would shrink past 5%.
    # On the SECOND run of this check the scratch file left by the FIRST run IS that
    # "delivered manuscript", so the build refuses, the stale file survives, and the
    # comparison reports the previous build's content as though it were the new one. It made
    # a budget fix look like it had changed nothing on 51 pages when it had in fact restored
    # whole sections on all of them.
    #
    # Fourth time tonight an instrument measured something adjacent to what it claimed to
    # measure and reported it with full confidence.
    if os.path.exists(scratch):
        try:
            os.remove(scratch)
        except OSError:
            return None
    r = subprocess.run([sys.executable, os.path.join(REPO, "ssot", "build_tabbed.py"),
                        src, scratch],
                       cwd=REPO, capture_output=True, timeout=900)
    if r.returncode != 0:
        return None
    return delivered_paper_text(scratch)


def tokens(text):
    ncts = set(_NCT.findall(text or ""))
    stripped = _NCT.sub(" ", text or "")
    return ncts, set(_NUM.findall(stripped))


def main():
    pmap = json.load(io.open(os.path.join(REPO, "ssot", "PAGE_MAP.json"), encoding="utf-8"))
    L = []

    def w(s):
        L.append(str(s))

    checked = skipped = safe = 0
    unsafe = []
    # SCOPED TO THE PAGES THE REBUILD REFUSED, when that list exists. Comparing a page the
    # rebuild already REWROTE means comparing the new build against itself: guaranteed
    # identical, informative about nothing, and it costs a full build to learn it. The
    # refused pages are the only ones where the delivered copy is still the OLD one, so
    # they are the only ones where this comparison has two different things to compare.
    only = None
    _list = os.path.join(REPO, "outputs", "_refused_pages.txt")
    if os.path.exists(_list):
        only = {x.strip() for x in io.open(_list, encoding="utf-8") if x.strip()}
        print("scoped to %d refused pages" % len(only))
    for page in sorted(pmap):
        if only is not None and page not in only:
            continue
        src = os.path.join(REPO, pmap[page].replace("/", os.sep))
        dst = os.path.join(REPO, page)
        old = delivered_paper_text(dst)
        if old is None:
            skipped += 1
            continue
        try:
            new = rebuilt_paper_text(src, page)
        except Exception:
            new = None
        if new is None:
            skipped += 1
            continue
        checked += 1
        o_nct, o_num = tokens(old)
        n_nct, n_num = tokens(new)
        lost_nct = sorted(o_nct - n_nct)
        lost_num = sorted(o_num - n_num)
        if lost_nct or lost_num:
            unsafe.append((page, lost_nct, lost_num))
        else:
            safe += 1

    w("pages compared                : %d" % checked)
    w("skipped (not built / no paper): %d" % skipped)
    w("")
    w("LOSE NOTHING -- no registration and no number dropped : %d" % safe)
    w("LOSE SOMETHING                                        : %d" % len(unsafe))
    w("")
    for page, ln, lnum in unsafe:
        w("  %s" % page)
        if ln:
            w("     registrations no longer on the page: %s" % ", ".join(ln[:8]))
        if lnum:
            w("     numbers no longer on the page (%d): %s"
              % (len(lnum), ", ".join(lnum[:14])))
    out = os.path.join(REPO, "outputs", "shrink_safety_2026_08_24.txt")
    io.open(out, "w", encoding="utf-8").write("\n".join(L))
    print("\n".join(L[:80]))
    return 1 if unsafe else 0


sys.exit(main())
