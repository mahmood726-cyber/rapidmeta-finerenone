# -*- coding: utf-8 -*-
"""Did the page a reader opens actually change, and does it match MY build?

⛔ WHAT THIS REFUSES TO ACCEPT AS PROOF. A 200. A green workflow. A commit sha.
A push that reported success. None of those is evidence that the bytes a reader
receives are the bytes that were built -- eleven commits were once reported as
delivered while `main`, the Pages deploy ref, had not moved.

⭐ THE STANDARD IS A HASH COMPARISON. sha256 of the fetched page against sha256
of the local build. Equal or it did not ship. Anything softer than that is a
claim about intent rather than about what a reader gets.

AND THE TABS ARE COUNTED FROM THE NAV OF THE FETCHED BYTES, against
`ssot/page_format_v1.json` -- the DECLARED list -- rather than against whichever
eight a lane remembers. Two lanes scored the same page "6 of 8" and "6 of 10"
on 2026-08-30 and neither was wrong about the page; they were counting different
required lists. A count whose denominator is unstated stops meaning anything.

    python scripts/verify_served_page.py AGYW_HIV_PREP_REVIEW.html

Exit 0 only if the served sha equals the built sha.
"""
import hashlib
import io
import json
import os
import re
import sys
import urllib.error
import urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
SITE = "https://mahmood726-cyber.github.io/rapidmeta-finerenone/"
UA = "rapidmeta-served-check/1.0 (mailto:mahmood726@gmail.com)"


def sha(b):
    return hashlib.sha256(b).hexdigest()


def fetch(url):
    req = urllib.request.Request(url, headers={
        "User-Agent": UA,
        # ⚠️ A CACHED COPY WOULD PASS A ONE-SIDED CHECK. Ask for the origin.
        "Cache-Control": "no-cache", "Pragma": "no-cache"})
    with urllib.request.urlopen(req, timeout=60) as r:
        return r.read(), dict(r.headers), r.status


def tabs_in(html):
    body = html.split("</style>", 1)[-1]
    return re.findall(r'<label for="rt-([a-z0-9_-]+)">([^<]+)</label>', body)


# KNOWN_NEGATIVE FOR THE ONE TEXT-MATCHING PART OF THIS TOOL -- AND WHAT IT IS NOT.
#
# `tabs_in` is the only thing here that matches text and reports a count. Its false-positive
# risk is counting something that LOOKS like a tab label but is not, which is why it strips
# everything up to the first `</style>` before matching.
#
# NO CORPUS KNOWN-NEGATIVE IS AVAILABLE, AND THAT WAS MEASURED RATHER THAN ASSUMED: 120
# delivered *_REVIEW.html pages were scanned for a `<label for="rt-...">` outside the tab nav
# -- inside the style block, or after it in a code sample -- and ZERO carry one. A
# "known-negative" drawn from this corpus would therefore be a page with nothing hard in it:
#
#     A KNOWN-NEGATIVE DRAWN FROM THE EASY MAJORITY MEASURES NOTHING.
#
# So it is PROVEN BY PLANT, following the precedent gate16 sets for its clause 4 -- "proven
# by plant, not by a corpus positive, and that is recorded rather than implied". The plant is
# PAIRED: a decoy that must NOT be counted and a real nav that MUST be, so the matcher is
# shown to DISCRIMINATE rather than merely to return zero.
#
# THE HONEST LIMIT, STATED SO A GREEN IS NOT OVERREAD: this controls the MATCHER, not the
# corpus, and says nothing about the sha comparison -- which is the point of this tool and
# cannot be controlled offline at all, because it needs the network and a deployed page.
# A PASS FROM --selftest IS NOT A VERIFIED SERVED PAGE.
KNOWN_NEGATIVE = "planted decoy: <label for='rt-x'> inside <style> must not be counted"


def selftest():
    nav = '<label for="rt-paper">Paper</label><label for="rt-screen">Screen</label>'
    decoy = ('<style>#rt-x{} label[for="rt-x"]{} '
             '<label for="rt-x">Decoy</label></style>')
    cases = [
        ("must count a real nav", decoy + nav, ["paper", "screen"]),
        ("must NOT count a label inside <style>", decoy, []),
        ("must not be fooled by CSS alone",
         '<style>label[for="rt-ghost"]{color:red}</style>', []),
    ]
    ok = True
    for label, doc, want in cases:
        got = [t for t, _ in tabs_in(doc)]
        good = got == want
        ok &= good
        print("  selftest %-40s got=%-20s want=%-20s %s"
              % (label, got, want, "OK" if good else "*** FAIL ***"))
    if not ok:
        print("SELFTEST FAILED -- tabs_in cannot tell a tab from a decoy, so its count is "
              "not a measurement.")
        return 1
    print("  known-negative control: 0/1 planted decoys counted "
          "(measured false-positive rate 0.0%)")
    print("  CORPUS INSTANCES OF THIS HAZARD: 0 of 120 pages scanned -- the control is a "
          "PLANT because the corpus offers no hard case, stated rather than implied.")
    print("  THIS CONTROLS THE MATCHER, NOT THE SERVED-BYTES COMPARISON.")
    return 0


def main():
    if "--selftest" in sys.argv:
        return selftest()
    page = sys.argv[1] if len(sys.argv) > 1 else "AGYW_HIV_PREP_REVIEW.html"
    local_path = os.path.join(ROOT, page)
    if not os.path.exists(local_path):
        print("REFUSED: no local build at %s -- nothing to compare against, and "
              "a served check with no local side is just a fetch." % local_path)
        return 2
    local = open(local_path, "rb").read()
    lsha = sha(local)

    url = SITE + page
    try:
        served, headers, status = fetch(url)
    except urllib.error.HTTPError as e:
        print("SERVED FETCH FAILED: HTTP %s for %s" % (e.code, url))
        print("  ⇒ the page is NOT served. A local build is not a delivery.")
        return 1
    except Exception as exc:
        print("SERVED FETCH FAILED: %s" % exc)
        return 1

    ssha = sha(served)
    match = (lsha == ssha)

    print("SERVED-BYTES CHECK  %s" % page)
    print("  url            %s" % url)
    print("  http status    %s" % status)
    print("  local  bytes   %d  sha256 %s" % (len(local), lsha))
    print("  served bytes   %d  sha256 %s" % (len(served), ssha))
    print("  MATCH          %s" % ("YES -- the reader gets exactly this build"
                                   if match else
                                   "NO -- the served page is NOT this build"))
    if not match:
        print("  ⇒ Do NOT report this as delivered. A push that lands a commit "
              "is not a deploy, and a deploy is not a served byte.")

    # Tabs, from the SERVED bytes, against the DECLARED list.
    decl_path = os.path.join(ROOT, "ssot", "page_format_v1.json")
    text = served.decode("utf-8", "replace")
    found = dict(tabs_in(text))
    print()
    if not os.path.exists(decl_path):
        print("  ⚠️ ssot/page_format_v1.json is NOT PRESENT LOCALLY, so the tab "
              "count has no declared denominator and is not reported. The "
              "served page carries %d tabs: %s"
              % (len(found), ", ".join(sorted(found))))
    else:
        decl = json.load(open(decl_path, encoding="utf-8"))
        req = decl.get("required_tabs") or []
        have = 0
        print("  TABS ON THE SERVED PAGE, against ssot/page_format_v1.json (%s):"
              % decl.get("version"))
        for t in req:
            pid = str(t.get("panel_id_hint") or "").replace("pn-", "")
            ok = pid in found
            if ok:
                have += 1
            print("    %-14s %s" % (t.get("id"),
                                    "present" if ok else "*** ABSENT ***"))
        print("    SCORE %d of %d" % (have, len(req)))
        extra = sorted(set(found) - {str(t.get("panel_id_hint") or "").replace("pn-", "")
                                     for t in req})
        if extra:
            print("    (also present, not on the required list: %s)"
                  % ", ".join(extra))

    # What a reader can actually check, from the served bytes.
    rows = len(re.findall(r"<tr", text))
    links = len(re.findall(r"""href=['"]https?://""", text))
    m = re.search(r'<section class="panel" id="pn-screen">(.*?)</section>',
                  text, re.S)
    sc = m.group(1) if m else ""
    print()
    print("  SERVED CONTENT")
    print("    total <tr> rows        %d" % rows)
    print("    outbound links         %d" % links)
    print("    screening tab rows     %d" % len(re.findall(r"<tr", sc)))
    print("    screening tab links    %d" % len(re.findall(r"""href=['"]https?://""", sc)))
    print("    <details> groups       %d" % len(re.findall(r'<details class="screen-group"', sc)))
    print("    ...carrying `open`     %d" % len(re.findall(r'<details class="screen-group" open', sc)))
    return 0 if match else 1


if __name__ == "__main__":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8",
                                  errors="replace")
    sys.exit(main())
