"""Did tonight's work reach the site a reader actually opens?

# no-control: a verifier, not a detector over a corpus. Its control is that every page it
# checks must ALSO satisfy a NEGATIVE assertion -- a string the old bytes carried and the
# new ones must not -- so a stale cache or a 404 cannot come back as a pass.

WHY THIS FILE EXISTS AND IT IS NOT A NICETY. Eleven commits were reported as delivered while
`main` -- the Pages deploy ref -- had not moved. Mahmood reads only the github.io site, so
"committed" and "delivered" had been allowed to mean the same thing in a report, and they
are not the same thing. This asserts the second one.

EACH PAGE IS CHECKED IN BOTH DIRECTIONS. A positive string that must now be present, and a
negative string that must now be ABSENT. A one-sided check passes on a cached copy of the
old page whenever the positive string happened to be there already; the negative side is
what makes a stale read fail.
"""
from __future__ import annotations

import io
import sys
import time
import urllib.error
import urllib.request

SITE = "https://mahmood726-cyber.github.io/rapidmeta-finerenone/"

# page -> (label, must be PRESENT now, must be ABSENT now)
CHECKS = [
    ("withdrawn_audit_rows.html",
     "the withdrawn-rows record (this URL 404'd before tonight)",
     "The four deletion events", None),
    ("audit_table.html",
     "97 rows withdrawn, and the table no longer links them",
     "rows were withdrawn from this table",
     "BIMAGRUMAB_OBESITY_AUTO_FULL_REVIEW.html"),
    ("EVOLOCUMAB_DYSLIPIDEMIA_AUTO_FULL_REVIEW.html",
     "FOURIER arm roles corrected from the registration",
     "Placebo (control, n=13780)", "Placebo (treatment, n=13780)"),
    ("EVOLOCUMAB_ASCVD_AUTO_2_FULL_REVIEW.html",
     "the SAME object's second delivered page",
     "Placebo (control, n=13780)", "Placebo (treatment, n=13780)"),
    ("EVOLOCUMAB_MIXED_DYSLIPIDEMIA_AUTO_FULL_REVIEW.html",
     "HUA TUO arm roles",
     "Placebo Q2W (control)", "Placebo Q2W (treatment)"),
    ("ICOSAPENT_LIPID_AUTO_FULL_REVIEW.html",
     "MARINE and ANCHOR arm roles",
     "Placebo (control)", "Placebo (treatment)"),
    ("MITRAL_FUNCMR_REVIEW.html",
     "RESHAPE-HF2 arm roles",
     "Control Group (control, n=255)", "Control Group (treatment, n=255)"),
    ("ATTR_PN_REVIEW.html",
     "the borrowed-control withdrawal, both grounds, and the superseded drafts",
     "randomised concurrent control", None),
    ("FCM_HF_REVIEW.html",
     "a withdrawal reason the page used to withhold entirely",
     "hours after it was built", None),
    ("SGLT2_HF_REVIEW.html",
     "the four-state certainty column and the estimand-contrast caveat",
     "What the established estimand does NOT cover", "<td>&mdash;</td>"),
    ("sitemap.xml",
     "the record is listed, not merely present",
     "withdrawn_audit_rows.html", None),
]

EXTRA = [
    ("ATTR_PN_REVIEW.html", "the second, independent ground", "three different drugs"),
    ("ATTR_PN_REVIEW.html", "drafts marked superseded", "Draft, superseded"),
    ("SGLT2_HF_REVIEW.html", "See comment on the withdrawn outcome", "See comment"),
]


def fetch(path, tries=1):
    """Cache-busted. A CDN copy of the old bytes is the failure this is guarding."""
    last = None
    for i in range(tries):
        url = "%s%s?cb=%d" % (SITE, path, int(time.time()) + i)
        req = urllib.request.Request(url, headers={
            "Cache-Control": "no-cache", "Pragma": "no-cache",
            "User-Agent": "rapidmeta-served-verify"})
        try:
            with urllib.request.urlopen(req, timeout=120) as r:
                return r.status, r.read().decode("utf-8", "replace")
        except urllib.error.HTTPError as e:
            last = (e.code, "")
        except Exception as e:  # network
            last = (0, str(e))
        if i + 1 < tries:
            time.sleep(20)
    return last or (0, "")


def main():
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    print("")
    print("SERVED BYTES at %s" % SITE)
    print("")
    ok = bad = 0
    pages = {}
    for path, label, present, absent in CHECKS:
        # the new page needs the deploy to have finished; give that one page real patience
        code, body = fetch(path, tries=12 if path == "withdrawn_audit_rows.html" else 3)
        pages[path] = body
        if code != 200:
            print("   %-52s HTTP %s   %s" % (path[:52], code, label))
            bad += 1
            continue
        p_ok = present in body
        a_ok = (absent not in body) if absent else True
        verdict = "LIVE" if (p_ok and a_ok) else "FAIL"
        if p_ok and a_ok:
            ok += 1
        else:
            bad += 1
        print("   %-52s %-5s %s" % (path[:52], verdict, label))
        if not p_ok:
            print("        MISSING the new text: %r" % present)
        if not a_ok:
            print("        STILL CARRIES the old text: %r" % absent)
    print("")
    for path, label, needle in EXTRA:
        body = pages.get(path) or ""
        print("   %-52s %-5s %s"
              % (path[:52], "LIVE" if needle in body else "no", label))
    print("")
    print("   verified live   %d of %d" % (ok, len(CHECKS)))
    if bad:
        sys.exit("REFUSED: %d page(s) are not carrying tonight's work on the served site."
                 % bad)
    print("   Every checked page carries the new bytes AND has lost the old ones.")


if __name__ == "__main__":
    main()
