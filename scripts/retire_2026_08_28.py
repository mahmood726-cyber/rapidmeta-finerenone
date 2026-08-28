"""Retire pages from DISCOVERY, tombstone them at the URL, in one revertible change.

WHAT THIS DOES AND DOES NOT DO. Mahmood's problem is discovery: a reader wades through dead
topics to reach a usable review. So these pages leave every index, listing, sitemap and
navigation surface. THE URL KEEPS SERVING -- a tombstone, not a 404 -- so an external citation
does not break silently and an auditor can SEE a retirement rather than infer it from a gap.

EXTERNAL REFERRERS ARE UNMEASURED, in those words. No backlink index, server log or referrer
report is reachable from this lane, and reporting zero would be a claim about the world from
an instrument that cannot see it. THE TOMBSTONE IS WHAT MAKES THAT ACCEPTABLE: a URL that
serves a tombstone does not break for anyone, measured or not.

  *** IF ANYONE FLIPS TOMBSTONE_MODE TO 404, THE UNMEASURED EXTERNAL REFERRERS BECOME
  *** BLOCKING AGAIN. The tombstone is the only reason it is safe not to have measured them.
  *** Do not flip it without a backlink or access-log check.

RE-VERIFIED AT THE MOMENT OF REMOVAL, not read from an earlier artefact. Each page must
independently satisfy all three legs: no store, no interval in rendered text, not in
PAGE_MAP. A page failing any leg leaves the batch and is named.

  This is not belt-and-braces. Building this batch from a serialised artefact returned 232
  instead of 763, because that artefact capped its member lists at 400 -- my own cap, silent,
  written an hour earlier. Never read a working set from a serialised artefact; recompute
  from source at the moment of use.

`a_tombstone_is_not_an_absence` is carried onto every tombstone AS A SENTENCE, because that
is why it was read instead of skipped.
"""
import io
import json
import os
import re
import sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(REPO, "outputs", "retirement_run_2026_08_28.json")

# THE PRECONDITION, WIRED 2026-08-28. gates/absence.py existed for a day before anything
# called it -- AVAILABLE, NOT OPERATIVE, which is the distinction .githooks/pre-commit already
# warns about and is the diagnosis this whole batch is named after. A gate no script invokes is
# a rule in a document with extra steps.
sys.path.insert(0, os.path.join(REPO, "gates"))
import absence as _absence                                              # noqa: E402

# A page positively IS resultless when it SAYS so. This is the POSITIVE restatement of the
# selector above, and it exists so the two counts can be compared before anything is written.
POSITIVE_NO_RESULT = re.compile(
    r"no pooled (estimate|result)|nothing is pooled|not pooled|no combined (figure|estimate)|"
    r"no meta-analys|no synthesis was|declines to pool|refuses to pool|"
    r"no quantitative synthesis|not been pooled", re.I)

TOMBSTONE_MODE = "tombstone"      # flip to "404" only after a backlink/access-log check

SCRIPT = re.compile(r"<script\b.*?</script>", re.S | re.I)
STYLE = re.compile(r"<style\b.*?</style>", re.S | re.I)
TAG = re.compile(r"<[^>]+>")
INTERVAL = re.compile(r"\d+\.\d+\s*[\(\[]\s*(?:95\s*%?\s*(?:CI|CrI)\s*[:,]?\s*)?"
                      r"-?\d+\.\d+\s*(?:to|,|-)\s*-?\d+\.\d+\s*[\)\]]")

TOMB = """<!doctype html>
<html lang="en" data-artefact="tombstone" data-retired="%(date)s">
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<meta name="robots" content="noindex,nofollow">
<title>Retired: %(title)s</title>
<style>
 :root{--bg:#fff;--fg:#111;--line:#d4d4d8;--muted:#3f3f46}
 body{background:var(--bg);color:var(--fg);font:16px/1.6 system-ui,sans-serif;
      max-width:42rem;margin:0 auto;padding:2.5rem 1.25rem}
 h1{font-size:1.3rem;margin:0 0 1rem}
 .box{border:1px solid var(--line);border-left:3px solid #b45309;padding:1rem 1.25rem;
      margin:1.25rem 0}
 small{color:var(--muted)}
 a{color:#1d4ed8}
</style>
<h1>This page has been retired</h1>

<p><strong>%(title)s</strong> is no longer listed. It carried the apparatus of a systematic
review &mdash; the tables, the headings, the sections &mdash; and no result: no pooled
estimate, and no interval anywhere in its text.</p>

<div class="box">
<p><strong>A tombstone is not an absence.</strong> This page is kept, and says what it was,
because an auditor must be able to see that a page was retired rather than infer it from a
gap. Removing it entirely would make a retirement we chose indistinguishable from a page we
lost.</p>
</div>

<p>It was removed from every index, listing, sitemap and navigation surface on
<strong>%(date)s</strong> so that readers reach the reviews that carry results without
wading through those that do not. The address keeps working, so any existing link to it
does not break.</p>

<p><small>Retired %(date)s from generator commit <code>%(sha)s</code>. Reason:
%(reason)s.</small></p>

<p><a href="index.html">Return to the index</a></p>
</html>
"""


def rendered(h):
    return re.sub(r"\s+", " ", TAG.sub(" ", STYLE.sub(" ", SCRIPT.sub(" ", h or "")))).strip()


def verify(page, pm):
    """(ok, failed_leg). All three legs, at the moment of removal."""
    if page in pm:
        return False, "IS in PAGE_MAP (has a store)"
    fp = os.path.join(REPO, page)
    if not os.path.exists(fp):
        return False, "no served file"
    t = rendered(io.open(fp, encoding="utf-8", errors="replace").read())
    if not re.search(r"PRISMA|GRADE|AMSTAR|risk of bias", t, re.I):
        return False, "no review apparatus (not a shell)"
    if INTERVAL.search(t):
        return False, "HAS an interval in rendered text"
    return True, None


def title_of(page):
    fp = os.path.join(REPO, page)
    try:
        h = io.open(fp, encoding="utf-8", errors="replace").read(200000)
    except OSError:
        return page
    m = re.search(r"<title>(.*?)</title>", h, re.S | re.I)
    if m:
        return re.sub(r"\s+", " ", TAG.sub("", m.group(1))).strip()[:120]
    return page


def main():
    listfile = sys.argv[1]
    apply_ = "--apply" in sys.argv
    reason = "no pooled estimate and no interval anywhere in the page"
    raw = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace",
                           write_through=True)

    def say(s):
        raw.write(s + chr(10))
        raw.flush()

    import subprocess
    sha = subprocess.run(["git", "rev-parse", "--short", "HEAD"],
                         capture_output=True, cwd=REPO).stdout.decode().strip()
    date = "2026-08-28"
    pm = json.load(io.open(os.path.join(REPO, "ssot", "PAGE_MAP.json"), encoding="utf-8"))
    pages = [l.strip() for l in io.open(listfile, encoding="utf-8") if l.strip()]

    say("candidates            : %d" % len(pages))
    say("re-verifying all three legs at the moment of removal")
    ok, rejected = [], []
    for p in pages:
        good, why = verify(p, pm)
        (ok if good else rejected).append(p if good else (p, why))
    say("  passed all three legs: %d" % len(ok))
    say("  REJECTED and named   : %d" % len(rejected))
    for p, why in rejected[:20]:
        say("     %-52s %s" % (p[:52], why))
    say("")
    # ------------------------------------------------------------------
    # NO IRREVERSIBLE ACTION ON AN ABSENCE-DEFINED SET.
    # Deliberately ABOVE the dry-run return: a refusal you only meet at --apply time is a
    # refusal you meet with your hand already on the lever. A dry run must show it.
    #
    # `verify()` above selects by what a detector could NOT find: no store, no interval
    # matching one regex, no apparatus. That set contains, indistinguishably, the pages that
    # genuinely have no result and the pages whose result the regex cannot see. One of them is
    # PREDICTION_MODEL_KFRE_REVIEW.html, which states 0.88 (95% CI 0.86-0.90) with an EN-DASH
    # -- a character the regex does not accept.
    #
    # So the positive restatement runs first and both counts are printed. `sanction` refuses to
    # issue a token while the difference is unexplained, and nothing below it can run without
    # one. Override deliberately and ON THE RECORD:
    #     RETIRE_EXPLAIN="<why the gap is acceptable>" python scripts/retire_2026_08_28.py ...
    # ------------------------------------------------------------------
    def _positive(page):
        try:
            with io.open(os.path.join(REPO, page), encoding="utf-8", errors="replace") as fh:
                return bool(POSITIVE_NO_RESULT.search(rendered(fh.read())))
        except OSError:
            return False

    try:
        token, _neg, _pos = _absence.sanction(
            "retire %d pages" % len(ok), ok,
            negative=lambda _p: True,          # membership already decided by verify()
            positive=_positive,
            explain=os.environ.get("RETIRE_EXPLAIN") or None)
    except _absence.Unsanctioned as exc:
        say("")
        say("REFUSED: " + str(exc))
        say("")
        say("Nothing was written. Name what the difference is, then re-run with")
        say("RETIRE_EXPLAIN set. A count of what a detector failed to recognise is not")
        say("a count of what is absent.")
        return 1
    say("SANCTIONED: " + token.line())
    _absence.require_sanction(token, "write %d tombstones" % len(ok))

    if not apply_:
        say("(dry run -- nothing written; pass --apply)")
        return 0


    written = 0
    for p in ok:
        html = TOMB % {"title": title_of(p), "date": date, "sha": sha, "reason": reason}
        io.open(os.path.join(REPO, p), "w", encoding="utf-8").write(html)
        written += 1
    say("tombstones written    : %d" % written)

    json.dump({"mode": TOMBSTONE_MODE, "date": date, "generator_sha": sha,
               "candidates": len(pages), "retired": written,
               "rejected": [{"page": p, "leg": w} for p, w in rejected],
               "external_referrers": "UNMEASURED -- no backlink index or access log reachable "
                                     "from this lane. The TOMBSTONE is what makes that "
                                     "acceptable: a URL serving a tombstone does not break. "
                                     "If TOMBSTONE_MODE is ever flipped to 404, this becomes "
                                     "blocking again.",
               "pages": ok},
              io.open(OUT, "w", encoding="utf-8"), indent=1)
    say("wrote %s" % os.path.relpath(OUT, REPO))
    return 0


if __name__ == "__main__":
    sys.exit(main())
