#!/usr/bin/env python3
# sentinel:skip-file — developer tool; hardcoded ROOT is intentional (local Finrenone checkout only)
"""Fix 3 confirmed data-quality issues surfaced by the portfolio audit:

  1. ROMOSOZUMAB_OP_REVIEW: ARCH (NCT01631214) appears TWICE in realData
     with different tE/cE counts. JS evaluates the second one last so the
     wrong counts (81/148) silently override the correct ones (127/243
     from Saag 2017 Table 2). Also has `pmid: '28892457', pmid: '28892457'`
     duplicate key on the first ARCH line. Fix: remove the dead
     second ARCH entry (lines ~2326-2336).

  2. PBC_PPAR_REVIEW: Seladelpar RESPONSE trial stored as NCT04620240
     which returns 404 from CT.gov. Verified correct NCT via CT.gov
     search: NCT04620733. Typo (240 vs 733). Fix: change in 3 places —
     AUTO_INCLUDE_TRIAL_IDS, nctAcronyms, realData key.

  3. 29 apps with placeholder PUBLISHED_META_BENCHMARKS (clone-template
     artifact: all copied the Finerenone FIDELITY 2022 benchmark entry,
     irrelevant to their actual topic). Clear these to `{}` so the UI
     honestly reports "No published benchmark available" instead of
     falsely comparing unrelated drug pools to Finerenone FIDELITY.
"""
import argparse, pathlib, re, sys

ROOT = pathlib.Path(r"C:\Projects\Finrenone")


# -------- Fix 1: ROMOSOZUMAB_OP ARCH duplicate -------------------------------
R_DUP_PATH = ROOT / "ROMOSOZUMAB_OP_REVIEW.html"

R_DUP_OLD_DUPLICATE = (
    "                'NCT01631214': {\n"
    "                    name: 'ARCH', phase: 'III', year: 2017, tE: 81, tN: 2046, cE: 148, cN: 2047, group: 'High-risk postmenopausal osteoporosis, romosozumab 210 mg Q1M for 12 mo then alendronate vs alendronate alone (24-mo new vertebral fracture RR)', publishedHR: 0.52, hrLCI: 0.4, hrUCI: 0.66,\n"
    "                    allOutcomes: [\n"
    "                        { shortLabel: 'MACE', title: 'New vertebral fracture through month 24 (primary, romo-then-alendronate vs alendronate alone, RR; head-to-head, ARCH is the FDA-pivotal for the active-comparator path)', tE: 81, cE: 148, type: 'PRIMARY', matchScore: 95, effect: 0.52, lci: 0.4, uci: 0.66, estimandType: 'RR' }\n"
    "                    ],\n"
    "                    rob: ['low', 'some concerns', 'low', 'low', 'low'],\n"
    "                    snippet: 'Source: Saag KG et al. NEJM 2017;377:1417-1427 (ARCH). Active-comparator head-to-head vs alendronate.',\n"
    "                    sourceUrl: 'https://www.nejm.org/doi/full/10.1056/NEJMoa1708322',\n"
    "                    ctgovUrl: 'https://clinicaltrials.gov/study/NCT01631214',\n"
    "                    evidence: []\n"
    "                }"
)
# We're removing this block plus the preceding comma-newline of the prior entry.
# In context the preceding close is `                },\n` then blank then this block.
# We replace the block and leave the closing of the object literal intact.
R_DUP_REPLACEMENT = ""  # removed entirely

# Also fix the duplicate pmid key on the surviving ARCH entry
R_PMID_OLD = "name: 'ARCH', pmid: '28892457',  pmid: '28892457',"
R_PMID_NEW = "name: 'ARCH', pmid: '28892457',"


# -------- Fix 2: PBC_PPAR NCT typo -------------------------------------------
P_PATH = ROOT / "PBC_PPAR_REVIEW.html"
P_REPLACEMENTS = [
    # 3 call sites: AUTO_INCLUDE_TRIAL_IDS, nctAcronyms, realData key
    ("'NCT04526665', 'NCT04620240'", "'NCT04526665', 'NCT04620733'"),
    ("'NCT04526665': 'ELATIVE', 'NCT04620240': 'RESPONSE'",
     "'NCT04526665': 'ELATIVE', 'NCT04620733': 'RESPONSE'"),
    ("'NCT04620240': {", "'NCT04620733': {"),
    # And any ctgovUrl pointing at the bad NCT
    ("https://clinicaltrials.gov/study/NCT04620240", "https://clinicaltrials.gov/study/NCT04620733"),
]


# -------- Fix 3: placeholder benchmark cleanup (exact-match safe) ------------
# Remove only the exact Finerenone-FIDELITY placeholder content between the
# { ... } of PUBLISHED_META_BENCHMARKS. The braces themselves stay intact so
# the object remains syntactically `= {}`.
BENCH_OLD_CONTENT = (
    "\n            MACE: [\n"
    "                { label: 'FIDELITY pooled analysis', citation: 'Agarwal 2022', year: 2022, measure: 'HR', estimate: 0.86, lci: 0.78, uci: 0.95, k: 2, n: 13026, scope: 'FIDELIO + FIGARO, CKD/T2D' }\n"
    "            ]\n        "
)


def fix_romosozumab(dry_run: bool) -> str:
    text = R_DUP_PATH.read_text(encoding="utf-8", newline="")
    crlf = "\r\n" in text
    work = text.replace("\r\n", "\n") if crlf else text
    notes = []

    # Duplicate ARCH removal
    if R_DUP_OLD_DUPLICATE in work:
        # Also remove the preceding comma + newline so we don't leave a dangling ,\n
        # Find the preceding `                }` block and adjust
        dup_pos = work.find(R_DUP_OLD_DUPLICATE)
        # Walk backwards to find the `,\n                '` that separates from previous entry
        pre = work[:dup_pos]
        sep_m = re.search(r",\n\s*$", pre)
        if sep_m:
            work = pre[:sep_m.start()] + "\n" + work[dup_pos + len(R_DUP_OLD_DUPLICATE):]
            notes.append("arch-dup:OK")
        else:
            work = work.replace(R_DUP_OLD_DUPLICATE, "", 1)
            notes.append("arch-dup:OK(no-comma-cleanup)")
    else:
        notes.append("arch-dup:skip(not-present)")

    # Duplicate pmid key
    if R_PMID_OLD in work:
        work = work.replace(R_PMID_OLD, R_PMID_NEW, 1)
        notes.append("arch-pmid-dup:OK")
    else:
        notes.append("arch-pmid-dup:skip")

    if not dry_run and (work != text.replace("\r\n", "\n") if crlf else work != text):
        out = work.replace("\n", "\r\n") if crlf else work
        R_DUP_PATH.write_text(out, encoding="utf-8", newline="")
    return f"ROMOSOZUMAB_OP: {'; '.join(notes)}"


def fix_pbc_ppar(dry_run: bool) -> str:
    text = P_PATH.read_text(encoding="utf-8", newline="")
    changes = 0
    for old, new in P_REPLACEMENTS:
        count = text.count(old)
        if count > 0:
            text = text.replace(old, new)
            changes += count
    if not dry_run and changes > 0:
        P_PATH.write_text(text, encoding="utf-8", newline="")
    return f"PBC_PPAR NCT04620240 -> NCT04620733: {changes} occurrence(s) {'would be' if dry_run else ''} replaced"


def _find_balanced_close(text: str, open_pos: int) -> int:
    """Given index of '{' in text, return index of matching '}' by brace counting."""
    depth = 0
    i = open_pos
    while i < len(text):
        ch = text[i]
        if ch == '{':
            depth += 1
        elif ch == '}':
            depth -= 1
            if depth == 0:
                return i
        i += 1
    return -1


def fix_placeholder_benchmarks(dry_run: bool) -> str:
    touched = []
    for p in sorted(ROOT.glob("*_REVIEW.html")):
        text = p.read_text(encoding="utf-8", newline="")
        if "'FIDELITY pooled analysis'" not in text:
            continue
        if p.name == "FINERENONE_REVIEW.html":
            continue  # legitimate use
        marker = "const PUBLISHED_META_BENCHMARKS = {"
        m_pos = text.find(marker)
        if m_pos < 0:
            continue
        open_pos = m_pos + len(marker) - 1  # position of the '{'
        close_pos = _find_balanced_close(text, open_pos)
        if close_pos < 0:
            continue
        # Confirm the placeholder is inside this {...}
        if "'FIDELITY pooled analysis'" not in text[open_pos:close_pos]:
            continue
        new_text = text[:open_pos] + "{}" + text[close_pos + 1:]
        if not dry_run:
            p.write_text(new_text, encoding="utf-8", newline="")
        touched.append(p.name)
    return f"Placeholder benchmarks cleared: {len(touched)} apps"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--apply", action="store_true")
    args = ap.parse_args()
    if not (args.dry_run or args.apply): ap.error("pass --dry-run or --apply")
    print(fix_romosozumab(dry_run=args.dry_run))
    print(fix_pbc_ppar(dry_run=args.dry_run))
    print(fix_placeholder_benchmarks(dry_run=args.dry_run))


if __name__ == "__main__":
    main()
