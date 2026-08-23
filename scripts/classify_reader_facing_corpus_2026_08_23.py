"""Bucket every page a reader can reach from the index. Four counts, and nothing folded to tidy them.

# no-control: the buckets are defined by markers present in the delivered bytes, so the known
# answer is the file itself -- there is no synthetic case to construct. The two confirmed
# instances named by hand, GLP1_CVOT_REVIEW (legacy) and PCSK9_REVIEW (tombstone), are asserted
# at the end of the run and the script exits non-zero if either lands in the wrong bucket.

WHY THIS IS NOT BOOKKEEPING. Every rate this project publishes -- 141 of 141, 28 of 28, 7 of 34
-- is computed over the SSOT-generated set. A reader arriving at the index meets all four
buckets. Until the fraction is known, every figure carries an unstated denominator, which is
the exact criticism this project makes of published meta-analyses.

UNCLASSIFIABLE PAGES ARE REPORTED BY NAME. A page folded into a bucket to make the numbers
tidy is a page nobody looks at again.
"""
import io
import json
import os
import re
import sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
INDEX = os.path.join(REPO, "index.html")

NOT_REVIEWS = {"audit_table.html", "dashboard.html", "portfolio_pools.html",
               "what_changed.html", "EVIDENCE_GAPS.html", "index.html"}

SSOT_MARKS = ("Reproducibility artifact", "Sources for this section",
              "<strong>Refused:</strong>")
LEGACY_MARKS = ("Run Acquisition", "INTERNAL CHECKS PASSED", "AMSTAR 2",
                "Fabrication-risk", "Loading...")
TOMBSTONE_MARKS = ("page-state", "RETIRED", "This review has been retired")


def links():
    h = io.open(INDEX, encoding="utf-8", errors="replace").read()
    out = []
    for m in re.finditer(r'href="([^"#?]+\.html)', h):
        n = os.path.basename(m.group(1))
        if n not in NOT_REVIEWS:
            out.append(n)
    return sorted(set(out))


def classify(text):
    low = text.lower()
    tomb = (("retired" in low and "noindex" in low)
            or "this review has been retired" in low
            or re.search(r'page-state["\s:=]+retired', low) is not None)
    if tomb:
        return "tombstone"
    ssot = sum(1 for m in SSOT_MARKS if m in text)
    legacy = sum(1 for m in LEGACY_MARKS if m in text)
    if ssot >= 2 and legacy == 0:
        return "ssot"
    if legacy >= 2 and ssot == 0:
        return "legacy"
    if ssot >= 2 and legacy >= 1:
        return "ssot"          # a generated page that merely mentions a legacy term
    if legacy >= 1 and ssot == 0:
        return "legacy"
    return "unclassifiable"


def main():
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    names = links()
    buckets = {"ssot": [], "legacy": [], "tombstone": [], "unclassifiable": [], "missing": []}
    legacy_detail = {"pass_banner": [], "unverified_reg": [], "stats_dashes": [],
                     "empty_pico": [], "amstar_registered": []}
    for n in names:
        p = os.path.join(REPO, n)
        if not os.path.isfile(p):
            buckets["missing"].append(n)
            continue
        t = io.open(p, encoding="utf-8", errors="replace").read()
        b = classify(t)
        buckets[b].append(n)
        if b != "legacy":
            continue
        if "INTERNAL CHECKS PASSED" in t:
            legacy_detail["pass_banner"].append(n)
        if re.search(r"(?i)unverified|not found in clinicaltrials", t):
            legacy_detail["unverified_reg"].append(n)
        if len(re.findall(r">\s*--\s*<", t)) >= 4:
            legacy_detail["stats_dashes"].append(n)
        if re.search(r"(?is)<t[dh][^>]*>\s*</t[dh]>", t):
            legacy_detail["empty_pico"].append(n)
        if re.search(r"(?is)protocol registered before commencement.{0,200}?yes", t):
            legacy_detail["amstar_registered"].append(n)

    total = len(names)
    print("")
    print("READER-FACING CORPUS: %d review pages linked from the index" % total)
    print("(index links %d .html files; %d are not reviews and are excluded by name)"
          % (total + len(NOT_REVIEWS) - 1, len(NOT_REVIEWS) - 1))
    print("")
    for k, label in (("ssot", "SSOT-GENERATED"), ("legacy", "LEGACY APP PAGE"),
                     ("tombstone", "RETIRED TOMBSTONE"),
                     ("unclassifiable", "UNCLASSIFIABLE"),
                     ("missing", "LINKED BUT NOT ON DISK")):
        n = len(buckets[k])
        print("   %-24s %4d   %5.1f%%" % (label, n, 100.0 * n / max(1, total)))
    print("")
    if buckets["unclassifiable"]:
        print("UNCLASSIFIABLE, BY NAME -- not folded into a bucket:")
        for n in buckets["unclassifiable"]:
            print("   %s" % n)
        print("")
    if buckets["missing"]:
        print("LINKED FROM THE INDEX AND NOT PRESENT ON DISK:")
        for n in buckets["missing"][:20]:
            print("   %s" % n)
        print("")
    print("ON THE LEGACY SET (%d pages):" % len(buckets["legacy"]))
    for k, label in (("pass_banner", 'carry an "INTERNAL CHECKS PASSED" banner'),
                     ("unverified_reg", "flag an unverified or unresolvable registration"),
                     ("stats_dashes", "render pooled statistics as --"),
                     ("empty_pico", "have empty PICO/table cells"),
                     ("amstar_registered",
                      'assert AMSTAR 2 "Protocol registered before commencement"')):
        print("   %-52s %4d" % (label, len(legacy_detail[k])))

    # the two confirmed-by-hand instances must land where a person put them
    errs = []
    if "GLP1_CVOT_REVIEW.html" in names and "GLP1_CVOT_REVIEW.html" not in buckets["legacy"]:
        errs.append("GLP1_CVOT_REVIEW.html is confirmed legacy by hand and this run did not "
                    "classify it as legacy")
    if "PCSK9_REVIEW.html" in names and "PCSK9_REVIEW.html" not in buckets["tombstone"]:
        errs.append("PCSK9_REVIEW.html is confirmed a tombstone by hand and this run did not "
                    "classify it as one")
    json.dump({k: v for k, v in buckets.items()},
              io.open(os.path.join(REPO, "outputs", "reader_facing_classes_2026_08_23.json"),
                      "w", encoding="utf-8"), indent=1)
    if errs:
        print("")
        sys.exit("REFUSED: the classifier disagrees with a page classified by hand:\n   "
                 + "\n   ".join(errs))
    print("")
    print("FLOOR: the two pages classified by hand -- GLP1_CVOT (legacy), PCSK9 (tombstone) --")
    print("land in the buckets a person put them in, so the markers read what a reader saw.")


if __name__ == "__main__":
    main()
