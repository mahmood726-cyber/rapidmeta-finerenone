"""Remove donor-app residue the post-clone contamination gate does not cover.

The gate (scripts/clone_contamination_gate.py) reports 0 hard findings on
HFREF_NMA_AUTO_FULL_REVIEW.html, and that is correct for the slots it inspects.
Two claim-bearing slots outside its blocklist still carried the donor app's
identity after the clone:

  1. JSON-LD "url" resolved this page to the DONOR artifact,
     .../SACUBITRIL_VALSARTAN_HF_AUTO_FULL_REVIEW.html. Structured metadata is
     what citation tools and search engines read, so the page was machine-
     readably claiming to be a different review.

  2. The benchmark footnote -- present twice, once in the DOM and once as the
     JavaScript fallback string -- read "Benchmarks use a locked local
     comparator database of published sacubitril pooled analyses." The
     BENCHMARKS object in this app is EMPTY ({}), so the caption described a
     comparator database that (a) is not loaded and (b) belongs to another
     drug. No false number was rendered, but the caption asserted a provenance
     the page does not have.

Idempotent: re-running after a successful pass is a no-op and exits 0.
"""

import io
import os
import sys

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
APP = os.path.join(ROOT, "HFREF_NMA_AUTO_FULL_REVIEW.html")

FIXES = [
    (
        "JSON-LD canonical url pointed at the donor app",
        "rapidmeta-finerenone/SACUBITRIL_VALSARTAN_HF_AUTO_FULL_REVIEW.html",
        "rapidmeta-finerenone/HFREF_NMA_AUTO_FULL_REVIEW.html",
        1,
    ),
    (
        "benchmark footnote claimed a sacubitril comparator database",
        "Benchmarks use a locked local comparator database of published "
        "sacubitril pooled analyses.",
        "No external benchmark comparator database is loaded for this network. "
        "The estimates on this page come from our own R/netmeta fit and are "
        "not benchmarked here against any published pooled analysis.",
        2,
    ),
]


def main():
    with open(APP, encoding="utf-8") as fh:
        html = fh.read()

    changed = 0
    for label, old, new, expect in FIXES:
        n = html.count(old)
        if n == 0:
            if html.count(new) >= 1:
                print(f"  already fixed: {label}")
                continue
            raise SystemExit(f"REFUSING: neither old nor new text present for: {label}")
        if n != expect:
            raise SystemExit(
                f"REFUSING: expected {expect} occurrence(s) of the donor string "
                f"for '{label}', found {n}. Not editing blind.")
        html = html.replace(old, new)
        changed += n
        print(f"  fixed ({n}x): {label}")

    if not changed:
        print("no changes needed")
        return

    with open(APP, "w", encoding="utf-8") as fh:
        fh.write(html)
    print(f"WROTE {APP} ({changed} replacement(s))")

    # fail closed: the donor strings must be gone
    with open(APP, encoding="utf-8") as fh:
        after = fh.read()
    for label, old, _new, _e in FIXES:
        if old in after:
            raise SystemExit(f"REFUSING: donor string survived the fix: {label}")
    print("post-check: no donor string survives")


if __name__ == "__main__":
    main()
