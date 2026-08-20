"""How many pages the reading-order rollout skipped are CURRENT-generator pages?

THE SKIP CRITERION DOES NOT MEAN WHAT IT WAS TAKEN TO MEAN.

scripts/rollout_reading_order_2026_08_20.py skips any page with zero `paper-*` h3 sections,
on the reasoning that such a page "was not built by this generator, and rebuilding it is a
replacement rather than a re-ordering". That reasoning is sound for a genuinely old page.

IT IS NOT SOUND FOR A CURRENT PAGE THAT SIMPLY HAS NO PAPER TAB. Found by accident while
sampling the skipped set for something else: BOCOCIZUMAB_LIPID_AUTO_FULL_REVIEW.html
carries this generator's own headings -- "Pooled result", "Contributing trials", "Endpoint
definitions, read from the registry", "Leave-one-out sensitivity" -- and was skipped only
for lacking a paper tab. AND ITS OBJECT HOLDS A POOLED POINT OF -55.24 THAT THE PAGE SHOWS
NOWHERE.

So a criterion meant to protect old pages from replacement instead EXCLUDED LIVE PAGES FROM
A CORPUS-WIDE FIX, and at least one of them is stale against its own object.

This separates the skipped set on a marker of THIS generator rather than on the absence of
one feature of it, and reports the stale ones. It decides nothing.
"""
import io
import json
import os
import re
import sys

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LOG = (r"F:/claude-temp/claude/F--rapidmeta-ssot-shell/"
       r"1b81ef60-0aa7-48a6-b23e-0c385cde4482/scratchpad/rollout.log")

# Markers this generator emits and the old PRISMA/AMSTAR template does not.
CURRENT = ("Endpoint definitions, read from the registry",
           "The methods rule governing this decision",
           "What this pool holds constant",
           "Does the answer depend on the pooling method?")
OLD = ("RapidMeta Precision v", "AMSTAR 2 Critical Domains")


def visible(t):
    b = re.sub(r"<script.*?</script>", " ", t, flags=re.S | re.I)
    return re.sub(r"<style.*?</style>", " ", b, flags=re.S | re.I)


def main():
    if not os.path.exists(LOG):
        print("NOT_ASSESSABLE: no rollout log at %s" % LOG)
        return 2
    log = io.open(LOG, encoding="utf-8", errors="replace").read()
    pages = [a for a, _ in re.findall(
        r"\s*\d+/\d+ (\S+)\s+SKIPPED, not a current-generator page \((\d+) words", log)]
    if not pages:
        print("NOT_ASSESSABLE: the log names no skipped page.")
        return 2

    pm = json.load(io.open(os.path.join(REPO, "ssot", "PAGE_MAP.json"), encoding="utf-8"))
    current, old, unclear = [], [], []
    for p in pages:
        fp = os.path.join(REPO, p)
        if not os.path.exists(fp):
            continue
        b = visible(io.open(fp, encoding="utf-8", errors="replace").read())
        n_cur = sum(1 for m in CURRENT if m in b)
        n_old = sum(1 for m in OLD if m in b)
        (current if n_cur and not n_old else old if n_old else unclear).append((p, n_cur, n_old))

    print("skipped pages examined            %d" % (len(current) + len(old) + len(unclear)))
    print("  CURRENT generator, no paper tab %d   <- WRONGLY EXCLUDED FROM THE ROLLOUT"
          % len(current))
    print("  old PRISMA/AMSTAR template      %d   <- correctly skipped" % len(old))
    print("  neither marker                  %d   <- UNCLASSIFIED, not 'old'" % len(unclear))
    print()

    stale = []
    for p, _c, _o in current:
        objp = pm.get(p)
        if not objp:
            continue
        fo = os.path.join(REPO, objp)
        if not os.path.exists(fo):
            continue
        o = json.load(io.open(fo, encoding="utf-8"))
        txt = re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ",
                                         visible(io.open(os.path.join(REPO, p),
                                                         encoding="utf-8",
                                                         errors="replace").read())))
        for oid, blk in ((o.get("results") or {}).get("by_outcome") or {}).items():
            pt = ((blk or {}).get("pooled") or {}).get("point")
            if pt is None:
                continue
            if not any(f in txt for f in {("%g" % pt), ("%.2f" % pt), ("%.3f" % pt)}):
                stale.append((p, oid, pt))

    if current:
        print("CURRENT-GENERATOR PAGES THE ROLLOUT SKIPPED:")
        for p, c, _o in sorted(current):
            print("    %-52s %d current marker(s)" % (p, c))
        print()
    if stale:
        print("AND THESE SERVE NOTHING FOR A POOLED POINT THEIR OBJECT HOLDS:")
        for p, oid, pt in stale:
            print("    %-52s %-28s object holds %s, page shows it nowhere" % (p, oid, pt))
        print()
        print("REFUSED: %d skipped page(s) are current-generator pages, %d of which do not "
              "serve a pooled point their object holds." % (len(current), len(stale)))
        return 1
    if unclear:
        print("UNCLASSIFIED pages -- NOT evidence they are old:")
        for p, _c, _o in sorted(unclear)[:20]:
            print("    %s" % p)
    print("REPORTED. %d current-generator page(s) were skipped; none is stale against its "
          "object on the pooled point." % len(current))
    return 0


if __name__ == "__main__":
    sys.exit(main())
