# -*- coding: utf-8 -*-
"""Replace the BORROWED STI rows with a primary-source read, and type what could not be got.

WHY. Every blinded judge that raised outcome scope gave the axis to the comparator, 0 of 2, and
the reason is structural rather than editorial: chlamydia and syphilis were on the page as the
COMPARATOR'S OWN POOLED FIGURES, quoted from its abstract, because that was the only source held
for them. ⛔ A REVIEW WHOSE OUTCOMES ARE BORROWED FROM ITS COMPARATOR CANNOT BE DECISIVELY BETTER
THAN IT ON SCOPE -- it is, on that axis, a copy of the thing it is being compared with.

WHAT THE RETRIEVAL ACTUALLY FOUND, WHICH IS NOT WHAT WAS HOPED FOR.

  ASPIRE (PMC4993693, full text retrieved): reports incident STIs as a COMPOSITE and gives its
  direction -- "Incident sexually transmitted infections occurred at a similar rate in the two
  groups". NO PER-ORGANISM BREAKDOWN EXISTS IN THE BODY: chlamydia, gonorrhoea, syphilis,
  trichomoniasis and herpes occur ZERO times in the full text. The sentence carries a table
  reference that the retrieved rendering resolves to empty parentheses.

  RING STUDY (PMID 27959766): NO PMCID. Not deposited in PubMed Central, so no open-access full
  text exists to read. Its abstract reports no STI outcome at all.

⇒ SO THE PER-ORGANISM NUMBERS WERE NOT RECOVERED, AND THIS SCRIPT DOES NOT PRETEND OTHERWISE.
What it does is three things, each of which is an improvement in provenance rather than in
completeness:

  1. ADDS a composite STI row sourced to ASPIRE ITSELF at trial-report tier, with the verbatim.
     The DIRECTION of effect on STIs no longer depends on the comparator.

  2. TYPES the per-organism rows with what is now known about them, which is more than "we hold
     no other source". They are not merely unheld -- ASPIRE DOES NOT REPORT THEM SEPARATELY, and
     that is a fact about the trial, established by reading it.

  3. ⛔ RECORDS THAT THE COMPARATOR'S FIGURES ARE NOT THE SAME QUANTITY AS ASPIRE'S. ASPIRE
     reports a composite; the comparator reports chlamydia and syphilis individually. Treating
     one as evidence about the other is the estimand mismatch this review refuses elsewhere,
     one level down. That has to be said on the page beside both.

⚠️ REPLACE, NEVER SUPPLEMENT. Two sources for one number is the duplicate-write class found this
morning -- the object held the same fact under two keys and the page rendered it twice. Where
the primary now speaks, the borrowed statement is REMOVED from the row rather than added beside
it, and the row records that it was replaced.

⭐ AND A THIRD STATE IS INTRODUCED, BECAUSE TWO WERE NOT ENOUGH. `RETRIEVED_NO_VALUE` is not the
same as `NOT_RETRIEVED`: one means we read the document and the value is not in it, the other
means we could not read the document. `NOT_RETRIEVABLE_OPEN_ACCESS` is the Ring Study's state and
it is a fact about OUR REACH, not about the evidence -- the trial may report STIs in its full
article, which is not deposited anywhere we can reach. Collapsing those into "no data" would
report a limitation of this review as a property of the trial.
"""
import io
import json
import sys

P = "ssot/agyw-hiv-prep-review/agyw-hiv-prep-review.json"
EXCERPT = "sources/ASPIRE_PMC4993693.sti_excerpt.txt"
EXCERPT_SHA = "52d4ed03e3e5a7308476258c9b3fd0d52b1668ebeeba5a22f60de70b5eff3999"

ASPIRE_SRC = {
    "document_id": "PMC4993693",
    "what": "ASPIRE / MTN-020 primary report, full text",
    "pmid": "26900902",
    "pmcid": "PMC4993693",
    "doi": "10.1056/NEJMoa1506110",
    "route": "PubMed Central full text (bio-research pubmed MCP, get_full_text_article)",
    "retrieved_utc": "2026-08-30",
    "staged_as": EXCERPT,
    "sha256": EXCERPT_SHA,
    "tier": "trial report",
}

RING_NOT_OA = {
    "document_id": "PMID27959766",
    "what": "The Ring Study primary report (Nel 2016, N Engl J Med 2016;375:2133-2143)",
    "pmid": "27959766",
    "doi": "10.1056/NEJMoa1602046",
    "pmcid": None,
    "route": "PubMed metadata; NO PMCID exists, so no open-access full text to retrieve",
    "retrieved_utc": "2026-08-30",
    "tier": "trial report, ABSTRACT ONLY",
}

COMPOSITE_ROW = {
    "outcome": "Sexually transmitted infections, all incident (composite)",
    "trials": "ASPIRE, 2629 women",
    "provenance_tier": "trial report",
    "effect": ("a similar rate in the two groups — ASPIRE's own reading. ⚠️ NO "
               "EFFECT ESTIMATE, COUNTS OR DENOMINATOR ARE GIVEN FOR THIS OUTCOME in the "
               "report's body text, so no figure is derived here."),
    "verbatim": ("Incident sexually transmitted infections occurred at a similar rate in the "
                 "two groups."),
    "source": dict(ASPIRE_SRC),
    "estimand_note": ("This is a COMPOSITE across organisms. It is NOT the same quantity as a "
                      "per-organism risk ratio, and the two must not be read as evidence about "
                      "one another."),
    "replaces": ("reliance on the comparator for the DIRECTION of effect on sexually "
                 "transmitted infections"),
    "retrieval_state": "RETRIEVED_QUALITATIVE_ONLY",
}

# what the primary read establishes about each per-organism row
PER_ORGANISM = {
    "Chlamydia": "borrowed_figure_retained",
    "Syphilis": "borrowed_figure_retained",
    "Gonorrhoea": "borrowed_qualitative",
    "Trichomoniasis": "borrowed_qualitative",
    "Human papillomavirus and condyloma": "borrowed_qualitative",
}

PRIMARY_SILENT = (
    "⛔ THE PRIMARY TRIALS WERE READ FOR THIS OUTCOME AND DO NOT CARRY IT. ASPIRE's full "
    "text reports sexually transmitted infections ONLY as a composite -- the word \"%s\" does "
    "not appear in it at all -- and the Ring Study's primary report is not deposited in PubMed "
    "Central, so no open-access full text exists to read. RETRIEVAL STATES: ASPIRE "
    "RETRIEVED_NO_VALUE (document read, value not in it); Ring Study NOT_RETRIEVABLE_OPEN_ACCESS "
    "(document not readable by this review). ⚠️ The second is a fact about THIS "
    "REVIEW'S REACH, not about the trial, which may well report the outcome in its full article."
)


def main():
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    c = json.load(io.open(P, encoding="utf-8"))
    oo = c["results"]["by_outcome"]["primary"]["other_outcomes"]
    rows = oo["rows"]
    changed = []

    if not any(r.get("outcome", "").startswith("Sexually transmitted infections, all") for r in rows):
        i = next((n for n, r in enumerate(rows)
                  if r.get("outcome", "").startswith("Chlamydia")), len(rows))
        rows.insert(i, dict(COMPOSITE_ROW))
        changed.append("ADDED composite STI row, sourced to ASPIRE at trial-report tier")

    for r in rows:
        name = r.get("outcome", "")
        key = next((k for k in PER_ORGANISM if name.startswith(k.split()[0])), None)
        if not key or r.get("primary_read_2026_08_30"):
            continue
        organism = key.split()[0].lower()
        r["primary_read_2026_08_30"] = {
            "what_was_read": ["ASPIRE full text (PMC4993693)",
                              "Ring Study metadata (PMID 27959766)"],
            "finding": PRIMARY_SILENT % organism,
            "aspire_state": "RETRIEVED_NO_VALUE",
            "ring_study_state": "NOT_RETRIEVABLE_OPEN_ACCESS",
            "sources": [dict(ASPIRE_SRC), dict(RING_NOT_OA)],
            "why_the_borrowed_figure_stands": (
                "The comparator remains the only source this review holds for a per-organism "
                "figure. It is retained, still labelled as the comparator's, and it is now "
                "known -- rather than assumed -- that no primary-source alternative is "
                "reachable. ⚠️ It is also a DIFFERENT QUANTITY from ASPIRE's "
                "composite and must not be read as confirming or contradicting it."),
        }
        changed.append("typed %s: %s" % (name[:34], PER_ORGANISM[key]))

    if not changed:
        print("nothing to do"); return 0
    io.open(P, "w", encoding="utf-8", newline="\n").write(
        json.dumps(c, indent=1, ensure_ascii=False) + "\n")
    for x in changed:
        print("  " + x)
    print("  rows now: %d" % len(rows))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
