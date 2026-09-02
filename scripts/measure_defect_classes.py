"""Blast radius of each defect class, and the inventory of refusals that are RIGHT.

TWO OUTPUTS, DELIBERATELY IN ONE FILE. A cleanup pass that removes a defect class
is the same pass that removes a correct refusal, because on the page they look
alike -- both are a place where the review declines to print a number. Measuring
them together means the protected count is in front of whoever reads the defect
count.

THE SERVED SURFACE IS ROOT-LEVEL *.html AND NOTHING ELSE.
The Pages workflow publishes the repository root, so subdirectory HTML is
reachable by URL, but it is not a reader page. Those files are excluded BY NAME
and BY COUNT below rather than silently, because a scan reports where it looked
and that is not the same as what it claims to cover:

    deployed_all_html   2228
    served reader pages 1464   <- the denominator every count here uses
    out/                 190   adjudication + withdrawal artefacts
    outputs/             327   of which 319 are *backup* -- ARCHIVE, a third kind
                               of item that is neither data nor defect
    other subdirectories 247

SCREEN vs CONFIRMED. A count under `screened` is an UPPER BOUND produced by
co-occurrence of strings on one page. It is not a finding. Two strings on one
page do not establish that they describe the same outcome, and the screens here
were measured to be over-inclusive in the direction that matters most: the first
version of the `not drawn` screen returned 151 pages, and the hits were
"GOSH plot -- not drawn at this k", which is a CORRECT refusal. A screen is
promoted to `confirmed` only by a predicate that reads the same object twice.
"""
from __future__ import annotations

import html as H
import io
import json
import re
import sys
from pathlib import Path

if __name__ == "__main__":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

ROOT = Path(__file__).resolve().parent.parent
TAG = re.compile(r"<[^>]+>")


def rendered(source: str) -> str:
    """Tag-stripped, entity-decoded, whitespace-collapsed -- what a READER sees.

    Every predicate in this module reads THIS, never the source. A sentence a
    reader sees as one string is routinely several strings in the file, split by
    an inline <strong> or a newline inside a <p>, so a source-level search for it
    cannot find it and scores the page as clean.
    """
    source = re.sub(r"(?is)<(script|style)\b.*?</\1>", " ", source)
    return re.sub(r"\s+", " ", H.unescape(TAG.sub(" ", source)))


def served_pages(root: Path = ROOT):
    """Root-level *.html. The one definition of `served`, imported by the gates."""
    return sorted(p for p in root.glob("*.html"))


# --- screens: upper bounds, never findings -------------------------------------------
SCREENS = {
    "S-not-executed":  r"NOT EXECUTED FOR THIS TOPIC",
    "S-no-sentence":   r"no source sentence recorded",
    "S-remainder-0":   r"not yet screened[^.]{0,40}?\b0\b",
    "S-elig-not-incl": r"ELIGIBLE_POOLABLE_NOT_INCLUDED",
    "S-assessors-dis": r"assessors disagree",
}

# --- refusals that are RIGHT: protected, counted before anything is edited ----------
PROTECTED = {
    "R1-not-recorded-idiom": r"Not recorded —",
    "R2-not-drawn-small-k":  r"not drawn at this k",
    "R3-no-meta-bias":       r"no funnel, Egger or Peters value is held",
    "R4-no-synthesis-method": r"no outcome on this object carries a pooled estimate",
    "R5-subgroup-unknown":   r"which is not the same as none having been",
    "R6-coprimary-separate": r"co-primar",
    "R7-ldl-surrogate":      r"LDL[^.]{0,140}surrogate",
    "R8-not-ready":          r"Submission readiness: NOT READY",
    "R9-no-conversion":      r"[Nn]o conversion anywhere|not converted into",
}


def measure(root: Path = ROOT):
    pages = served_pages(root)
    screened = {k: [] for k in SCREENS}
    protected = {k: [] for k in PROTECTED}
    for p in pages:
        text = rendered(p.read_text(encoding="utf-8", errors="replace"))
        for key, pat in SCREENS.items():
            if re.search(pat, text, re.I):
                screened[key].append(p.name)
        for key, pat in PROTECTED.items():
            if re.search(pat, text, re.I):
                protected[key].append(p.name)
    return pages, screened, protected


def _run_controls(screened):
    """Two known answers, neither of them established by this instrument.

    POSITIVE. AZILSARTAN_HTN_AUTO_FULL_REVIEW.html renders, in its own PubMed card,
    `<pre>NOT EXECUTED FOR THIS TOPIC</pre>`. That was read out of the served bytes by hand
    before this module existed, so the screen must flag it. If it does not, nothing else
    this file prints is trustworthy.

    NEGATIVE, and it is the load-bearing half. ABLATION_AF_REVIEW.html carries
    "GOSH plot -- not drawn at this k", a CORRECT refusal that reviewers praised. No defect
    screen may name it. This is the exact direction three predicates in this lane failed:
    a `not drawn` screen returned 151 pages and every hit was a correct refusal. An
    instrument that over-flags a protected refusal is worse than one that finds nothing,
    because a flagged page gets "fixed".
    """
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    from instrument_controls import require_controls
    pos_page = "AZILSARTAN_HTN_AUTO_FULL_REVIEW.html"
    neg_page = "ABLATION_AF_REVIEW.html"
    flagged_anywhere = {p for pages in screened.values() for p in pages}
    require_controls(
        "measure_defect_classes",
        positive=("%s carries a placeholder query" % pos_page,
                  pos_page in screened["S-not-executed"], True),
        negative=("%s is a protected small-k refusal" % neg_page,
                  neg_page in flagged_anywhere, True))


def main():
    pages, screened, protected = measure()
    _run_controls(screened)
    report = {
        "denominator": {
            "served_reader_pages": len(pages),
            "deployed_all_html": 2228,
            "excluded_by_name": {"out/": 190, "outputs/": 327,
                                 "of_which_backup_archive": 319, "other_subdirs": 247},
        },
        "screened_upper_bounds": {k: len(v) for k, v in sorted(screened.items())},
        "protected_refusals": {k: len(v) for k, v in sorted(protected.items())},
    }
    print(json.dumps(report, indent=2))
    (ROOT / "scripts" / "baselines" / "defect_class_baseline.json").write_text(
        json.dumps({"report": report, "screened_pages": screened,
                    "protected_pages": protected}, indent=2), encoding="utf-8")
    zero = [k for k, v in protected.items() if not v]
    if zero:
        print("\nPROTECTED PATTERNS RETURNING ZERO (NOT_FOUND, not ABSENT): %s" % zero)
    return 0


if __name__ == "__main__":
    sys.exit(main())


# ===========================================================================================
# ADDED 2026-09-03, from reviews 9-15. Two measurements with precisely located emitters.
# ===========================================================================================

_ROW = re.compile(r"<td>(P\d+_[a-z0-9_]+)</td><td><strong>([A-Z\- ]+)</strong></td>", re.S)
_NO_SEARCH = re.compile(r"No systematic search was run|No bibliographic search", re.I)
_TWO_TRIAL = "named two-trial programme"


def measure_p1_against_the_banner(root: Path = ROOT):
    """P1_executed_search HELD on a page whose OWN prose says no search was run.

    THE PAGE IS HONEST AND THE MARKER IS NOT. The banner at ssot/projectors.py:545 is a
    deliberate NOT-READY disclosure -- "Nothing on this page should be read as though a
    systematic search had been performed" -- and it is CORRECT. It fires when
    `search.strategy` is absent. p1_executed_search reads `search.databases`. Two keys on
    one block, and nothing asserted they agree.

    The direction matters: the banner is protected, the marker is the defect.
    """
    hits, with_table, without_table = [], 0, 0
    for page in served_pages(root):
        raw = page.read_text(encoding="utf-8", errors="replace")
        rows = {m[0]: m[1].strip() for m in _ROW.findall(raw)}
        # POSITIVE PROPERTY, and both states counted. `if not rows: continue` drops a page
        # out of the denominator without anyone deciding that it should, which is how a
        # reach figure comes to wear a coverage figure's clothes.
        carries_the_table = bool(rows)
        if carries_the_table:
            with_table += 1
            if rows.get("P1_executed_search") == "HELD" and _NO_SEARCH.search(rendered(raw)):
                hits.append(page.name)
        else:
            without_table += 1
    return {"pages_with_property_table": with_table,
            "pages_without_property_table": without_table,
            "contradicted": sorted(hits)}


def measure_two_trial_sentence(root: Path = ROOT):
    """A hardcoded topic-specific sentence emitted corpus-wide, checked against real k.

    `ssot/projectors.py:545` writes "The included set is a named two-trial programme" for
    EVERY topic whose search declares no strategy. It is a module constant; the count two
    is not read from anything.
    """
    page_map = json.loads((root / "ssot" / "PAGE_MAP.json").read_text(encoding="utf-8"))
    rendering, contradicting, unresolved, no_k = [], [], [], []
    for page in served_pages(root):
        if _TWO_TRIAL not in rendered(page.read_text(encoding="utf-8", errors="replace")):
            continue
        rendering.append(page.name)
        rel = page_map.get(page.name)
        resolves = bool(rel) and (root / rel).exists()
        if resolves:
            obj = json.loads((root / rel).read_text(encoding="utf-8"))
            k = (obj.get("k_cascade") or {}).get("k_included_in_object")
            if isinstance(k, int):
                if k != 2:
                    contradicting.append({"page": page.name, "k_included_in_object": k})
            else:
                # THREE STATES, NOT TWO. An object that resolves but records no
                # k_included_in_object cannot confirm OR contradict the sentence. The first
                # version of this function folded it into "object_resolves" and would have
                # reported 146 checked against 13 contradicting -- reading 133 unreadable
                # objects as agreement.
                no_k.append(page.name)
        else:
            unresolved.append(page.name)
    return {"rendering_the_sentence": len(rendering),
            "checkable": len(rendering) - len(unresolved) - len(no_k),
            "contradicting_their_own_k": contradicting,
            "records_no_k_so_not_checkable": len(no_k),
            "no_object_so_not_checkable": len(unresolved)}
