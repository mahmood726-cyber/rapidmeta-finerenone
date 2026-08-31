# -*- coding: utf-8 -*-
"""Fetch the SERVED page and check what a reader actually gets. Not the build, not the preview.

⛔ EVERY NUMBER THIS LANE REPORTED TODAY DESCRIBED A WORKTREE. This is the only script that
speaks about the public URL, and it says so in every line it prints.

THE FOUR FORMAT QUESTIONS ARE REPORTED SEPARATELY FROM THE CONTENT CHECKS, and that separation
is the point. The standing requirement is ONE DOWNLOADABLE HTML FILE with tabs -- Protocol,
Search, Screening WITH EVERY RECORD AND ITS DECISION, Extraction WITH EVERY DATUM LINKED TO ITS
SOURCE, Analysis, Paper Studio, HTA, Guideline.

⚠️ THE TABBED SHELL IS NOT IN THE SSOT GENERATOR. So a generated page can lose the format
silently, and the regeneration suite can score 13 of 13 while the artefact has stopped being the
thing worth reading. ***THAT IS A DIFFERENT DENOMINATOR, NOT A CAVEAT ON A NUMBER*** -- a
feature count measured on a page without tabs is measuring the wrong object, and this script
therefore refuses to fold the format result into the content result.

⛔ A COUNT WHERE A LIST BELONGS IS THE OPPOSITE OF THIS FORMAT. "1,247 records screened" with no
records is not a weaker version of Screening; it is the thing Screening exists to prevent. Same
for Extraction: a number with no link to its source is the defect, not a missing nicety.

⛔ AND OFFLINE IS PART OF THE FORMAT, NOT A NICETY. A reader in Uganda gets what the file
CONTAINS, not what it can reach. Any external fetch -- CDN script, remote font, XHR on load --
is a format failure even when every tab renders perfectly on a machine with network.
"""
import hashlib
import html as _html
import io
import json
import os
import re
import sys
import urllib.request

URL = "https://mahmood726-cyber.github.io/rapidmeta-finerenone/AGYW_HIV_PREP_REVIEW.html"

TABS = ("Protocol", "Search", "Screening", "Extraction", "Analysis",
        "Paper Studio", "HTA", "Guideline")

# ⛔ A LINK A READER CLICKS IS NOT A RESOURCE THE PAGE LOADS, AND THE FIRST VERSION OF THIS
# PATTERN COULD NOT TELL THEM APART. It matched `href=` generically, so two ordinary
# <a href="https://clinicaltrials.gov/..."> hyperlinks -- exactly the outbound citations this
# review is SUPPOSED to carry -- were reported as "⛔ 2 EXTERNAL REFERENCES: a reader without
# network gets less than the file claims". That is false, and it is false in the direction that
# looks like a finding.
#
# ⚠️ THE OFFLINE REQUIREMENT IS ABOUT WHAT THE FILE NEEDS, NOT WHAT IT POINTS AT. A page full of
# outbound citations is the goal; a page that FETCHES a stylesheet at load is the defect. Only
# load-time dependencies count: script src, stylesheet link, @import, fetch, XHR, and remote
# images.
EXTERNAL = re.compile(
    r"""(?ix)
      <script[^>]+\bsrc\s*=\s*["']\s*(?:https?:)?//(?!mahmood726-cyber\.github\.io)
    | <link[^>]+\bhref\s*=\s*["']\s*(?:https?:)?//(?!mahmood726-cyber\.github\.io)
    | <img[^>]+\bsrc\s*=\s*["']\s*(?:https?:)?//(?!mahmood726-cyber\.github\.io)
    | @import\s+(?:url\()?\s*["']?\s*(?:https?:)?//
    | \bfetch\s*\(\s*["']\s*(?:https?:)?//
    | new\s+XMLHttpRequest
    """)


def rendered(b):
    s = b.decode("utf-8", errors="replace")
    t = re.sub(r"(?is)<(script|style).*?</\1>", " ", s)
    t = re.sub(r"(?i)</t[dh]>", " | ", t)
    t = re.sub(r"(?i)</(tr|p|h1|h2|h3|li|div)>", "\n", t)
    t = re.sub(r"<[^>]+>", "", t)
    return re.sub(r"[ \t]+", " ", _html.unescape(t)), s


def fetch(url=URL, out=None):
    r = urllib.request.urlopen(url, timeout=120)
    b = r.read()
    if out:
        io.open(out, "wb").write(b)
    return r.status, b


def format_report(raw, text):
    """THE FOUR QUESTIONS. Returned as their own dict; never merged with content results."""
    tabs_present = {t: (t.lower() in raw.lower()) for t in TABS}

    # Screening: a LIST of records, or a COUNT standing in for one?
    scr_counts = re.findall(r"(?i)([\d,]{2,})\s+(?:records?|citations?|titles?|abstracts?)\s+"
                            r"(?:were\s+)?(?:screened|identified|retrieved|assessed)", text)
    # a record-with-decision looks like an identifier next to an include/exclude verdict
    scr_rows = re.findall(r"(?i)\b(?:NCT\d{8}|PMID\s*\d{6,9}|doi\s*10\.\d{4,})\b[^\n]{0,120}?"
                          r"\b(includ|exclud|not eligible|eligible|screened out)", text)
    # Extraction: data points carrying a resolvable source
    linked = len(re.findall(r"(?i)(?:PMC\d{6,}|NCT\d{8}|10\.\d{4,}/\S+)", text))
    sha = re.findall(r"\b[0-9a-f]{16,64}\b", text)

    ext = EXTERNAL.findall(raw)
    return {
        "tabs_present": tabs_present,
        "tabs_found": sum(1 for v in tabs_present.values() if v),
        "tabs_expected": len(TABS),
        "screening_counts_quoted": scr_counts[:6],
        "screening_record_rows": len(scr_rows),
        "screening_verdict": (
            "LIST -- records shown with decisions" if len(scr_rows) >= 5 else
            "⛔ COUNT WHERE A LIST BELONGS" if scr_counts else
            "NEITHER a list nor a count found -- Screening may be absent entirely"),
        "extraction_source_links": linked,
        "content_hashes_on_page": len(set(sha)),
        "external_references": len(ext),
        "offline_verdict": ("SELF-CONTAINED -- no external reference found" if not ext
                            else "⛔ %d EXTERNAL REFERENCE(S): a reader without network gets "
                                 "less than the file claims" % len(ext)),
        "external_examples": [e if isinstance(e, str) else str(e) for e in ext[:4]],
    }


def main():
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace",
                                  line_buffering=True)
    # ⛔ SAME DEFECT AS THE INDEX AUDIT, WRITTEN IN THE SAME HOUR. `%TEMP%/served_page.html` is
    # a generic name in a shared root: every lane fetching the served page picks it, and one
    # lane then checks bytes another lane fetched. The worktree is unique BY CONSTRUCTION --
    # each lane has its own and no coordination is needed to keep it that way.
    out = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(
        os.path.abspath(__file__)))), "out", "fetched", "served_page.html")
    os.makedirs(os.path.dirname(out), exist_ok=True)
    try:
        status, b = fetch(out=out)
    except Exception as exc:
        print("FETCH FAILED: %s: %s" % (type(exc).__name__, exc))
        print("⚠️ This says nothing about the page. It says the fetch did not happen.")
        return 2
    text, raw = rendered(b)
    print("SERVED PAGE -- %s" % URL)
    print("  HTTP %s   %d bytes   %d rendered chars" % (status, len(b), len(text)))
    print("  sha256 %s" % hashlib.sha256(b).hexdigest())
    print("  saved to %s (open it with the network off)" % out)

    print("")
    print("=" * 74)
    print("FORMAT -- reported SEPARATELY, because a page without tabs is a different artefact")
    print("=" * 74)
    f = format_report(raw, text)
    print("  tabs found %d of %d" % (f["tabs_found"], f["tabs_expected"]))
    for t, ok in f["tabs_present"].items():
        print("     %-14s %s" % (t, "present" if ok else "*** ABSENT ***"))
    print("  Screening   %s" % f["screening_verdict"])
    print("     record rows with a decision : %d" % f["screening_record_rows"])
    print("     bare counts quoted          : %s" % (f["screening_counts_quoted"] or "none"))
    print("  Extraction  source links on the page : %d" % f["extraction_source_links"])
    print("              content hashes           : %d" % f["content_hashes_on_page"])
    print("  Offline     %s" % f["offline_verdict"])
    for e in f["external_examples"]:
        print("     %s" % e[:100])
    json.dump(f, io.open(os.path.join(os.path.dirname(out), "served_format.json"),
                         "w", encoding="utf-8"), indent=1)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
