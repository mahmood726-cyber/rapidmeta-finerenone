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
    for page in sorted(pmap):
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
