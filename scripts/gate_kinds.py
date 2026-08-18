"""GATE KINDS -- how many INDEPENDENT kinds of evidence does the gate set have?

WHY THIS EXISTS
    Two pages were edited with a five-check suite in front of them -- div balance,
    script-tag count, numerals-lost, byte growth, anchor-matched-once. All five
    passed. All five were THE SAME CHECK: each asks about CONTENT, and the damage
    was to ENCODING, which content checks are blind to by construction. The edit
    rewrote 12,031 line endings and only `git commit`'s own line count noticed.

    FIVE CONTENT CHECKS ARE NOT REDUNDANCY AGAINST AN ENCODING FAULT. They are one
    check run five times.

    So the coverage question this repository has been asking -- how many checks does
    a page pass -- is the wrong one. The honest question is HOW MANY INDEPENDENT
    KINDS, and which kinds nothing is looking at.

    This file names the kinds, assigns every gate to one, and reports the kinds with
    NO gate at all. The assignment is a judgement and is written down so it can be
    argued with; the LIST of gates is derived from disk so the count cannot decay.

A TRAP WORTH KEEPING
    `ls scripts/*gate*.py` returns 52 files. Twenty-one of them are `propagate_*`
    scripts -- the glob matches "propa-GATE". Anyone quoting "52 gates" from that
    glob is wrong by two thirds. The filter below is explicit for that reason.

USAGE
    python scripts/gate_kinds.py
"""
from __future__ import annotations
import glob
import io
import os
import sys

if __name__ == "__main__":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# NOT gates: propagate_*/aggregate_* are matched only by the "gate" substring, and
# fix_*/regenerate_*/add_*/extend_* are one-off repair scripts, not checks.
NOT_A_GATE = ("propagate_", "aggregate_", "fix_", "regenerate_", "add_", "extend_",
              "gate_kinds")

KINDS = {
    "INTERNAL AGREEMENT": (
        "two of OUR OWN surfaces compared with each other",
        ["alignment_gate", "card_alignment_gate", "extraction_table_gate",
         "k_consistency_gate", "pooled_value_gate", "prose_claim_gate",
         "section_manifest_gate"]),
    "EXTERNAL AGREEMENT": (
        "ours against a source OUTSIDE the repository -- a registry, an article",
        ["absence_reason_gate", "arm_identity_gate", "citation_year_gate",
         "count_provenance_gate", "declared_contrast_gate",
         "estimand_definition_gate", "identity_by_registration_gate",
         "identity_gate", "registration_identity_gate", "search_recall_gate",
         "withdrawal_reason_gate"]),
    "ARITHMETIC": (
        "do the numbers reconcile with each other",
        ["headline_reproducible_gate", "precision_sample_gate"]),
    "MARKUP / STRUCTURE": (
        "is the artefact well formed as a document",
        ["_js_parse_gate", "double_escape_gate", "index_markup_gate"]),
    "PRESENCE / DURABILITY": (
        "does the thing exist, is it tracked, is it current",
        ["build_stamp_gate", "clone_contamination_gate", "durable_artefact_gate",
         "staleness_gate"]),
    "TOPICALITY": (
        "is this about the right subject at all",
        ["subject_match_gate", "protocol_subject_gate"]),
    "SELF-CHECK": (
        "can the checks themselves fail, and did they run",
        ["gate_integrity", "harness_gate"]),
}

# Kinds with NO gate. Each has already produced a real defect, which is the point:
# these are not hypothetical gaps.
UNCOVERED = [
    ("ENCODING / BYTE INTEGRITY",
     "line endings, BOM, charset -- anything true of the FILE rather than of its text",
     "2026-08-18: a text-mode round-trip converted 12,031 CRLF endings to LF on two "
     "live pages. Five content checks passed it. Caught by git's line count alone."),
    ("DELIVERY / LIVENESS",
     "does the far side actually SERVE the bytes that were pushed",
     "2026-08-18: ssot/ had returned 404 for weeks while every page promised the "
     "reader a canonical object. 'Verify live' is a manual protocol step, and for an "
     "object-only change it had nothing to check, so it passed vacuously every time."),
    ("DELTA / IDEMPOTENCY",
     "did this patch change what it was meant to change, and only that",
     "the ledger's own entry: an append-instead-of-set produced a well-formed object "
     "that every gate passed. Only a diff against the EXPECTED change reveals it, and "
     "no gate computes one."),
]


def main() -> int:
    found = set()
    for f in sorted(glob.glob(os.path.join(REPO, "scripts", "*gate*.py"))):
        b = os.path.basename(f)[:-3]
        if any(b.startswith(p) for p in NOT_A_GATE):
            continue
        found.add(b)

    print("gate files on disk (after removing propagate_/fix_/... ): %d" % len(found))
    print("raw `scripts/*gate*.py` glob would report: %d"
          % len(glob.glob(os.path.join(REPO, "scripts", "*gate*.py"))))
    print()
    print("%-24s %-4s %s" % ("KIND", "n", "what it actually inspects"))
    print("-" * 100)
    assigned = set()
    for kind, (what, members) in KINDS.items():
        live = [m for m in members if m in found]
        assigned |= set(members)
        print("%-24s %-4d %s" % (kind, len(live), what))
        for m in sorted(live):
            print("%-29s %s" % ("", m))
        missing = [m for m in members if m not in found]
        for m in missing:
            print("%-29s %s   (CLASSIFIED BUT NOT ON DISK)" % ("", m))
    print()
    unclassified = sorted(found - assigned)
    print("gates on disk with no kind assigned: %d" % len(unclassified))
    for u in unclassified:
        print("   %s" % u)

    print()
    print("=" * 100)
    print("KINDS WITH NO GATE AT ALL -- and each has already cost us something")
    print("=" * 100)
    for name, what, cost in UNCOVERED:
        print()
        print("  %s" % name)
        print("      inspects : %s" % what)
        print("      real cost: %s" % cost)

    print()
    print("THE MEASUREMENT: %d gates across %d kinds, and %d kinds with zero coverage."
          % (len(found), len([k for k, (_, m) in KINDS.items()
                              if any(x in found for x in m)]), len(UNCOVERED)))
    print("A page passing every gate in this set is unchecked in all three.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
