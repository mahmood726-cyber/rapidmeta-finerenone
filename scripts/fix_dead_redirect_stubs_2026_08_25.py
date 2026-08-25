"""A stub must not promise a page that does not exist, nor bounce a reader to a 404.

WHAT THESE PAGES DO. `X_AUTO_REVIEW.html` is a redirect stub. It tells the reader

    "This page is now the full RapidMeta dashboard (all tabs + Paper Studio)."
    "If it does not open automatically, open the full ... RapidMeta here."

and runs `location.replace('X_AUTO_FULL_REVIEW.html')`.

For 47 of them the target does not exist. So the sentence is false, the automatic redirect
lands on a 404, and the manual link a reader clicks when the redirect "does not work" lands
on the same 404. Found by an overnight hunt briefed to attack the gates: the link gate
visited seven hub pages and never looked at these.

THE TARGETS CANNOT SIMPLY BE BUILT. None of the 101 missing targets is in PAGE_MAP and none
has an ssot object, so there is no source to generate them from. This is not a build that was
skipped; those full reviews do not exist.

SO THE STUB IS MADE TRUTHFUL RATHER THAN MADE TO WORK. The redirect is disabled, the claim is
replaced with what is actually the case, and the dead link is removed. The page is NOT
deleted: it is linked from galleries and audit tables, and a 404 at a path someone else links
to is a worse outcome than a page that explains itself.

CONSERVATIVE BY CONSTRUCTION. Only stubs whose target is genuinely absent are touched;
anything else is left alone, and every edit is verified by re-reading the file.
"""
import io
import os
import re
import sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REDIRECT = re.compile(r"location\.replace\(\s*'([^']+\.html)'\s*\)\s*;?")
META_REFRESH = re.compile(r'<meta http-equiv="refresh"[^>]*url=([A-Za-z0-9_\-]+\.html)', re.I)
ORPHAN_MARK = re.compile(r'<meta name="rm-orphan-redirect" content="([A-Za-z0-9_\-]+\.html)"', re.I)


def main():
    apply = "--apply" in sys.argv
    here = {f for f in os.listdir(REPO) if f.endswith(".html")}
    touched, skipped = [], 0
    for page in sorted(here):
        path = os.path.join(REPO, page)
        try:
            h = io.open(path, encoding="utf-8", errors="replace").read()
        except OSError:
            continue
        # FOUND BY ANY OF ITS THREE REDIRECT MECHANISMS, not just the JavaScript one.
        #
        # The first pass keyed on `location.replace`, removed it, and thereby made the same
        # pages invisible to a second pass -- while their <meta http-equiv="refresh"> was
        # still bouncing readers to the 404. A repair that destroys its own search key can
        # only ever be run once, and cannot be verified by re-running it.
        m = (REDIRECT.search(h) or META_REFRESH.search(h) or ORPHAN_MARK.search(h))
        if not m:
            continue
        target = m.group(1)
        if target in here:
            skipped += 1
            continue                     # the redirect works; leave it entirely alone

        new = h
        # 1. Disable EVERY automatic bounce to the 404, and there are two.
        #
        # Disabling only the JavaScript `location.replace` left the page still redirecting,
        # because the real mechanism is a <meta http-equiv="refresh"> in the head -- which
        # fires with JavaScript disabled and fires FIRST. Caught by re-reading the page
        # after the first pass instead of trusting the diff: the prose was honest and the
        # reader was still being thrown to a 404.
        #
        # The canonical link goes too. A <link rel="canonical"> naming a page that does not
        # exist tells every indexer that the real address of this content is a 404.
        new = REDIRECT.sub("/* redirect disabled: the target does not exist */", new)
        new = re.sub(r'<meta http-equiv="refresh"[^>]*%s[^>]*>\s*' % re.escape(target),
                     "", new, flags=re.I)
        new = re.sub(r'<link rel="canonical" href="%s"[^>]*>\s*' % re.escape(target),
                     "", new, flags=re.I)
        # 2. Replace the claim with what is true.
        new = new.replace(
            "This page is now the full RapidMeta dashboard (all tabs + Paper Studio).",
            "The full RapidMeta dashboard for this topic has not been published. "
            "This page is a pointer that was left behind when it was not built, and it is "
            "kept rather than deleted because other pages link to this address.")
        # 3. Remove the link that goes to the same missing file, keeping the sentence
        #    readable rather than leaving a dangling "here".
        new = re.sub(
            r"<p>If it does not open automatically,\s*<a href=\"%s\">[^<]*</a>\s*\.?</p>"
            % re.escape(target),
            "<p>There is nothing further to open.</p>", new)
        new = re.sub(r'<a href="%s">([^<]*)</a>' % re.escape(target), r"\1", new)

        if new == h:
            continue
        touched.append((page, target))
        if apply:
            io.open(path, "w", encoding="utf-8").write(new)
            back = io.open(path, encoding="utf-8", errors="replace").read()
            # The only surviving mention may be <meta name="rm-orphan-redirect">, which is a
            # RECORD of where this stub used to point and is not a redirect. Anything that
            # would still move a reader must be gone.
            assert 'http-equiv="refresh"' not in back, page
            assert "location.replace" not in back, page
            assert 'rel="canonical" href="%s"' % target not in back, page

    print("redirect stubs whose target EXISTS (untouched) : %d" % skipped)
    print("stubs pointing at a MISSING target             : %d" % len(touched))
    for page, target in touched[:8]:
        print("   %-46s -> %s" % (page, target))
    if not apply:
        print("\nDRY RUN. Re-run with --apply to write.")
    return 0


sys.exit(main())
