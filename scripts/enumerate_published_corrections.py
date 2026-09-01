# -*- coding: utf-8 -*-
"""Which delivered pages carry a PUBLISHED CORRECTION, and what must survive a rebuild?

⛔ WHY THIS MUST EXIST BEFORE ANY CORPUS-WIDE REBUILD.

Corrections live in HISTORY and in the page bytes. A generator that reads only
current store state can rebuild a page WITHOUT its correction, which silently
un-publishes a retraction -- and the run looks clean, because nothing errors and
the tree count does not change.

    A REBUILD THAT DROPS A CORRECTION IS INDISTINGUISHABLE FROM A SUCCESSFUL
    REBUILD, FROM THE OUTSIDE.

So each page that carries one gets a `must_render` string -- the shortest
distinctive substring that EXISTS in the page today and would be absent if the
correction were dropped -- and the builder refuses to write a page that has an
entry here and does not contain it.

⚠️ THE VOCABULARY OVER-MATCHES ON PURPOSE, AND THE CLASSES SAY SO. "withdrawn"
describes a pooled estimate withheld TODAY, which is a legitimate current state
and not a correction of a past error. Three classes, counted separately:

    PUBLISHED_CORRECTION  the page tells a reader a PREVIOUS PUBLISHED VERSION
                          said something different
    STATE_ONLY            the word describes current state, no claim about a past
                          version
    HISTORY_ONLY          only a commit message suggests a correction; the page
                          says nothing to a reader -- which is itself a finding,
                          because the reader was never told

    python scripts/enumerate_published_corrections.py            # report
    python scripts/enumerate_published_corrections.py --write     # write the json
"""
import io
import json
import os
import re
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
# ⛔ NOT outputs/. THAT DIRECTORY IS GITIGNORED, so a list written there exists
# only on the machine that generated it -- and the builder guard that reads it
# REFUSES when it is absent, correctly, which would have refused every build for
# every other lane and in every fresh clone. A guard whose input cannot travel is
# a guard that fails closed for everyone except its author.
OUT = os.path.join(ROOT, "scripts", "baselines", "published_corrections.json")

# Phrases that claim a PREVIOUS PUBLISHED VERSION differed. These are the ones
# that make a page a correction rather than a statement of current state.
# ⛔ `correction[: ]` WAS IN THIS PATTERN AND IT MATCHED "continuity correction
# 0.5". That one token classified 824 of 1,427 pages as carrying a published
# correction -- 58% of the corpus, with ZERO of them pinnable to a must_render
# string, which is what gave it away. "Correction" is a STATISTICS word here
# (continuity correction, Bonferroni correction, correction for multiple
# testing) far more often than it is an editorial one.
#
#     AN IMPLAUSIBLE PROPORTION IS A STATEMENT ABOUT THE INSTRUMENT.
#     58% would have meant this project retracts more often than it publishes.
#
# So every phrase below must reference A PREVIOUS PUBLISHED VERSION explicitly.
# "Correction" survives only when bound to publication language, never alone.
PAST_VERSION = re.compile(
    r"(this page (?:previously|earlier)|an earlier version|a previous version"
    r"|we (?:previously )?reported|previously (?:said|stated|reported|showed)"
    r"|now reads|has been corrected|(?:published|issued) a correction"
    r"|correction notice|erratum"
    r"|retract(?:ed|ion) (?:of|notice)|superseded by|amended on)", re.I)

# Weaker signals: present, but they describe today unless PAST_VERSION also fires.
STATE_WORDS = re.compile(r"\b(withdrawn|withheld|not established|superseded)\b", re.I)

COMMIT_WORDS = re.compile(
    r"\b(correct(?:ion|ed)?|retract(?:ed|ion)|erratum|amend(?:ed|ment)|"
    r"was wrong|is wrong|misreported|overstated|understated)\b", re.I)


def sh(args, timeout=240):
    try:
        r = subprocess.run(args, cwd=ROOT, capture_output=True, timeout=timeout)
        return r.stdout.decode("utf-8", "replace")
    except Exception:
        return ""


def pages():
    return [f for f in sorted(os.listdir(ROOT))
            if f.endswith(".html") and "_REVIEW" in f]


def sentence_around(text, idx, span=260):
    a = max(0, idx - span // 2)
    b = min(len(text), idx + span // 2)
    return re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", text[a:b])).strip()


def main():
    write = "--write" in sys.argv
    all_pages = pages()

    # ONE git call for the whole corpus, not one per page: 1,427 subprocesses is
    # how a checker becomes something nobody runs.
    # THE SEPARATORS ARE BUILT WITH chr(), NOT WRITTEN AS ESCAPES. A literal NUL
    # or SOH in a source pattern is the same hazard class as a backslash-b that
    # arrives as 0x08 -- lint_escape_hazards refused this file for it and was
    # right: a control character written as an escape survives one transport and
    # not the next, and the failure is silent because the pattern still compiles.
    _NUL, _SOH = chr(0), chr(1)
    log = sh(["git", "log", "--since=90 days ago", "--name-only",
              "--pretty=format:%x00%H%x01%s"], timeout=550)
    touched = {}
    for block in log.split(_NUL):
        if not block.strip():
            continue
        head, _, files = block.partition("\n")
        sha, _, subject = head.partition(_SOH)
        if not COMMIT_WORDS.search(subject):
            continue
        for f in files.splitlines():
            f = f.strip()
            if f.endswith(".html") and "_REVIEW" in f:
                touched.setdefault(os.path.basename(f), []).append(
                    {"where": "commit", "match": COMMIT_WORDS.search(subject).group(0),
                     "context": subject[:200], "commit": sha[:12]})

    counts = {"PUBLISHED_CORRECTION": 0, "STATE_ONLY": 0, "HISTORY_ONLY": 0}
    out_pages = {}
    skipped = {}
    examined = 0

    for page in all_pages:
        p = os.path.join(ROOT, page)
        try:
            with io.open(p, encoding="utf-8", errors="replace") as fh:
                html = fh.read()
        except Exception as exc:
            skipped["unreadable: %s" % type(exc).__name__] = \
                skipped.get("unreadable: %s" % type(exc).__name__, 0) + 1
            continue
        examined += 1
        body = re.sub(r"<script\b.*?</script>", " ",
                      html.split("</style>", 1)[-1], flags=re.S)

        sigs = []
        for m in PAST_VERSION.finditer(body):
            sigs.append({"where": "page", "match": m.group(0)[:60],
                         "context": sentence_around(body, m.start()), "commit": None})
            if len(sigs) >= 4:
                break
        state_hits = len(STATE_WORDS.findall(body))
        hist = touched.get(page, [])

        if sigs:
            klass = "PUBLISHED_CORRECTION"
        elif hist:
            klass = "HISTORY_ONLY"
        elif state_hits:
            klass = "STATE_ONLY"
        else:
            continue

        counts[klass] += 1
        must = None
        if klass == "PUBLISHED_CORRECTION":
            # The shortest distinctive substring that EXISTS today. Verified by
            # reading it back out of the file, not assumed.
            for s in sigs:
                cand = s["context"]
                if len(cand) >= 40:
                    plain = re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", body))
                    if cand in plain:
                        must = cand[:180]
                        break
        out_pages[page] = {"class": klass,
                           "signals": (sigs + hist)[:6],
                           "state_word_hits": state_hits,
                           "must_render": must}

    report = {
        "written_utc": None,
        "method": ("Page bytes searched for phrases CLAIMING A PREVIOUS PUBLISHED "
                   "VERSION differed (not for words like 'withdrawn', which describe "
                   "today). Commit subjects from the last 90 days searched for "
                   "correction language and joined to the pages they touched. NOT "
                   "searched: commit DIFFS (too slow to be run), pages older than the "
                   "90-day window, and any correction phrased in words outside the "
                   "vocabulary -- all three are gaps, named here rather than implied."),
        "denominator": {"top_level_review_html": len(all_pages),
                        "pages_examined": examined,
                        "pages_skipped_and_why": skipped},
        "counts": counts,
        "must_render_present": sum(1 for v in out_pages.values()
                                   if v["class"] == "PUBLISHED_CORRECTION"
                                   and v["must_render"]),
        "pages": out_pages,
    }

    print("PUBLISHED CORRECTIONS -- enumerated before any rebuild")
    print("  delivered review pages      : %d" % len(all_pages))
    print("  examined                    : %d" % examined)
    if skipped:
        print("  skipped                     : %s" % skipped)
    print("  commits with correction language touching a page: %d" % len(touched))
    print()
    for k in ("PUBLISHED_CORRECTION", "HISTORY_ONLY", "STATE_ONLY"):
        print("  %-22s %4d" % (k, counts[k]))
    print()
    pc = [p for p, v in out_pages.items() if v["class"] == "PUBLISHED_CORRECTION"]
    print("  PUBLISHED_CORRECTION pages (%d), and whether a must_render was pinned:"
          % len(pc))
    for p in sorted(pc):
        v = out_pages[p]
        print("    %-46s %s" % (p[:46],
                                "pinned" if v["must_render"] else "*** NOT PINNED ***"))
        if v["must_render"]:
            print("        %s" % v["must_render"][:110])
    ho = [p for p, v in out_pages.items() if v["class"] == "HISTORY_ONLY"]
    if ho:
        print()
        print("  ⚠️ HISTORY_ONLY (%d): a commit says a correction was made and the PAGE "
              "SAYS NOTHING" % len(ho))
        for p in sorted(ho)[:12]:
            print("    %-46s %s" % (p[:46], out_pages[p]["signals"][0]["context"][:70]))

    if write:
        os.makedirs(os.path.dirname(OUT), exist_ok=True)
        with io.open(OUT, "w", encoding="utf-8", newline="\n") as fh:
            fh.write(json.dumps(report, ensure_ascii=False, indent=1) + "\n")
        print()
        print("  written %s" % os.path.relpath(OUT, ROOT))
    return 0


if __name__ == "__main__":
    # A UTF-8 wrapper IS correct here: this module imports nothing that installs
    # one. Without it the run died on a tau while writing its own output --
    # CORR_EXIT=1, no JSON, after examining all 1,427 pages.
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8",
                                  errors="replace", line_buffering=True)
    sys.exit(main())
