"""Count, across the whole delivered corpus, how many pages carry each reader-facing defect.

BEFORE AND AFTER, FROM THE SAME INSTRUMENT. `outputs/reads_terribly_backup_2026_08_24/`
holds the bytes each page had before today's rebuild. This counts both directories with one
code path, so the two numbers are comparable; counting "before" from memory or from an
earlier report is how a corpus-wide claim goes wrong.

WHAT THIS DOES NOT ESTABLISH, WRITTEN BEFORE THE NUMBERS ARE READ. A zero here means the
enumerated markers are gone. It does NOT mean the pages read well. Four blind readers were
shown four of these pages after the markers were cleared and all four called them a debug
dump. This instrument cannot see that and must not be quoted as if it could.
"""
import io
import json
import os
import re
import sys
import glob
import html as htmllib

if __name__ == "__main__":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BACKUP = os.path.join(REPO, "outputs", "reads_terribly_backup_2026_08_24")

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import gate_paper_reads_terribly_2026_08_24 as GATE


def count_dir(pages, root):
    """Count over EXACTLY the pages given. The caller establishes that they all exist.

    THE POSITIVE PROPERTY, AND THE PRE-COMMIT GATE WAS RIGHT TO INSIST ON IT. This began
    as `if not os.path.exists(path): continue` inside the loop, and
    `audit_exclusion_by_absence.py` refused the commit. That refusal was worth more than
    the convenience: a BEFORE count that silently skips pages missing from the backup
    directory under-counts the baseline, and the improvement then looks larger than it is.
    On a number I am about to report corpus-wide, that is the difference between evidence
    and flattery. The caller now intersects the two directories first and prints both
    denominators, so any page counted in one and not the other is visible rather than
    dropped.
    """
    per_class, blocked = {}, 0
    for page in pages:
        path = os.path.join(root, page)
        html = open(path, encoding="utf-8", errors="replace").read()
        f = GATE.findings_for(path, html, GATE.slugs_of(page))
        if f:
            blocked += 1
            for cls, _ in f:
                per_class[cls] = per_class.get(cls, 0) + 1
    return len(pages), blocked, per_class


def main():
    if not GATE.run_controls():
        sys.exit("REFUSED: the gate's own controls failed; nothing it counts is evidence.")
    page_map = json.load(open(os.path.join(REPO, "ssot", "PAGE_MAP.json"), encoding="utf-8"))
    pages = sorted(page_map)

    # BOTH DENOMINATORS, STATED. The comparison runs over the INTERSECTION, and every page
    # that is in one set and not the other is printed rather than skipped -- see count_dir.
    in_backup = [p for p in pages if os.path.exists(os.path.join(BACKUP, p))]
    in_repo = [p for p in pages if os.path.exists(os.path.join(REPO, p))]
    both = sorted(set(in_backup) & set(in_repo))
    print("\nPAGES IN PAGE_MAP: %d" % len(pages))
    print("  present in backup (before): %d" % len(in_backup))
    print("  present in repo   (after) : %d" % len(in_repo))
    print("  COMPARED (in both)        : %d" % len(both))
    only_after = sorted(set(in_repo) - set(in_backup))
    if only_after:
        print("  in repo but never backed up, so NOT in the before/after (%d): %s"
              % (len(only_after), ", ".join(only_after[:6])))

    b_checked, b_blocked, b_cls = count_dir(both, BACKUP)
    a_checked, a_blocked, a_cls = count_dir(both, REPO)

    print("\n  before: %d carrying a defect of %d compared" % (b_blocked, b_checked))
    print("  after : %d carrying a defect of %d compared" % (a_blocked, a_checked))
    print("\n  %-22s %8s %8s" % ("class", "before", "after"))
    for cls in sorted(set(b_cls) | set(a_cls)):
        print("  %-22s %8d %8d" % (cls, b_cls.get(cls, 0), a_cls.get(cls, 0)))

    # Also count every delivered page on disk, not only the mapped ones, so a defect that
    # lives outside PAGE_MAP cannot hide behind the mapped denominator.
    allp = sorted(os.path.basename(p) for p in glob.glob(os.path.join(REPO, "*_REVIEW.html")))
    a2_checked, a2_blocked, a2_cls = count_dir(allp, REPO)   # all exist, they were globbed
    print("\nEVERY DELIVERED PAGE ON DISK: %d checked, %d carrying a defect"
          % (a2_checked, a2_blocked))
    for cls in sorted(a2_cls):
        print("  %-22s %8d" % (cls, a2_cls[cls]))

    with io.open(os.path.join(REPO, "outputs", "corpus_marker_count_2026_08_24.json"),
                 "w", encoding="utf-8") as fh:
        json.dump({"mapped_pages": len(pages),
                   "before": {"checked": b_checked, "blocked": b_blocked, "by_class": b_cls},
                   "after": {"checked": a_checked, "blocked": a_blocked, "by_class": a_cls},
                   "all_delivered": {"checked": a2_checked, "blocked": a2_blocked,
                                     "by_class": a2_cls}}, fh, indent=2)
    return 0


if __name__ == "__main__":
    sys.exit(main())
