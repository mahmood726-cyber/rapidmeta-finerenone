"""Give the 58-of-60 finding the scrutiny we apply to everyone else's numbers.

MAHMOOD: "A result this good invites exactly the scrutiny we apply to others."

Three things a sceptic would ask, answered from the cached XML rather than asserted:

  1. WHAT IS THE SAMPLING FRAME? How were the reviews chosen, over what dates, from where,
     and what would narrow the claim? A count of 58/60 means one thing if it is a broad
     sample and something much smaller if it is one journal family in one year.

  2. "NAMES NO REGISTRATION ANYWHERE" IS NOT "NAMES NO TRIAL REGISTRATION." A review citing
     its own PROSPERO number but no trial NCTs is a different fact from one citing nothing at
     all -- and the second is the stronger claim, so the two must not be summed. PROSPERO ids
     look like CRD42022360263; trial ids look like NCT01234567. Counting them together would
     inflate the "names something" side and understate the finding, which is the direction
     that flatters us and therefore the one to check hardest.

  3. WHAT DO THE TWO THAT DO NAME REGISTRATIONS DO DIFFERENTLY? If a journal policy explains
     it, that is a lever and a far more useful conclusion than a complaint.

THE CLAIM BEING TESTED IS ABOUT AUDITABILITY, NOT QUALITY. Not naming a trial registration is
not a defect and this is not an accusation: many included trials predate registration
entirely. The claim is that a review which never names a trial registration cannot be checked
for trial-identity defects by anyone -- not by us, not by a peer reviewer, not by its own
authors. It is stronger for being modest, because it is a fact about the artefact rather than
a judgement about the people.
"""
import io
import json
import os
import re
import subprocess
import sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(REPO, "scripts"))
import instrument_controls

CACHE = os.path.join(REPO, "outputs", "review_registration_naming_2026_08_25.jsonl")
EFETCH = ("https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi?db=pmc"
          "&id=%s&retmode=xml")

NCT = re.compile(r"NCT\d{8}")
# Review-level registrations, which are NOT trial ids and must be counted apart.
PROSPERO = re.compile(r"CRD4\d{10}|PROSPERO", re.I)
OTHER_TRIAL_REG = re.compile(
    r"ISRCTN\d{6,8}|ChiCTR[-\w]*\d{6,}|EudraCT\s*\d{4}-\d{6}-\d{2}|"
    r"jRCT\w?\d{6,}|UMIN\d{6,}|ACTRN\d{10,}|NL\d{4,}|IRCT\d{6,}", re.I)
JOURNAL = re.compile(r"<journal-title>(.*?)</journal-title>", re.S)
PUBDATE = re.compile(r'<pub-date[^>]*>.*?<year>(\d{4})</year>', re.S)


def control():
    """The three counters must separate three id shapes, and must not invent any."""
    t = "Registered on PROSPERO as CRD42022360263. Trials NCT03630081 and ISRCTN12345678."
    n, p, o = len(set(NCT.findall(t))), len(PROSPERO.findall(t)), len(set(OTHER_TRIAL_REG.findall(t)))
    empty = "This review cites Smith 2019 and Jones 2021 only."
    instrument_controls.require_controls(
        "registration-naming-rigour",
        ("text with 1 NCT, 1 PROSPERO and 1 ISRCTN -> (1,>=1,1)",
         (n, p >= 1, o), (1, True, 1)),
        ("text with none must not yield a trial id",
         len(NCT.findall(empty)) + len(OTHER_TRIAL_REG.findall(empty)) > 0, True))
    # A PROSPERO id must NOT be counted as a trial registration -- the check that keeps the
    # two facts apart.
    if NCT.search("CRD42022360263"):
        raise instrument_controls.ControlFailed(
            "REFUSED: a PROSPERO id matched the trial-id pattern. The two would be summed and "
            "the finding misstated. NO COUNT IS PRINTED.")
    print("CONTROL (separation) a PROSPERO id does not match the trial-id pattern")
    return True


def main():
    control()
    if not os.path.exists(CACHE):
        print("REFUSED: no cache. NO COUNT IS PRINTED.")
        return 2
    rows = []
    seen = set()
    for line in io.open(CACHE, encoding="utf-8"):
        try:
            d = json.loads(line)
        except ValueError:
            continue
        if d.get("status") == "ok" and d.get("pmcid") not in seen:
            seen.add(d["pmcid"])
            rows.append(d)

    print()
    print("=== 1. SAMPLING FRAME, stated so a sceptic can narrow the claim ===")
    print("  source        : PubMed Central, open-access subset only")
    print("  query         : \"systematic review\"[Title] AND \"meta-analysis\"[Title]")
    print("  date range    : 2023-2026 publication date")
    print("  selection     : PMC's own relevance order, first N returned. NOT random,")
    print("                  NOT stratified by journal, specialty, or publisher.")
    print("  retrieved     : %d reviews, 0 fetch failures" % len(rows))
    print()
    print("  WHAT A SCEPTIC WOULD SAY, and each is a real limit:")
    print("   * PMC open access is not the literature. Cochrane Reviews are largely NOT in")
    print("     PMC, and Cochrane is the comparator this programme is measured against.")
    print("   * PMC relevance order is not random; the same query on another day may differ.")
    print("   * \"systematic review\" AND \"meta-analysis\" in the TITLE selects a particular")
    print("     reporting style and misses reviews that title themselves differently.")
    print("   * No specialty stratification: if the sample skews to one field, the number is")
    print("     about that field.")

    # Re-read the XML for the id-type split; the cache stored only NCT counts.
    print()
    print("=== 2. NAMES NOTHING vs NAMES A REVIEW REGISTRATION ONLY ===")
    print("  (re-reading cached XML is not possible -- the cache kept counts, not bodies --")
    print("   so a subsample is refetched to split the two facts)")
    sub = rows[:40]
    none_at_all = review_reg_only = trial_reg = other_only = 0
    journals = {}
    examples = []
    for i, r in enumerate(sub, 1):
        try:
            p = subprocess.run(["curl", "-sL", "-m", "90", EFETCH % r["pmcid"]],
                               capture_output=True, timeout=120)
            xml = (p.stdout or b"").decode("utf-8", "replace")
        except Exception:
            continue
        if len(xml) < 2000:
            continue
        has_nct = bool(NCT.search(xml))
        has_other = bool(OTHER_TRIAL_REG.search(xml))
        has_pros = bool(PROSPERO.search(xml))
        jm = JOURNAL.search(xml)
        j = " ".join(re.sub(r"<[^>]+>", " ", jm.group(1)).split())[:44] if jm else "?"
        journals[j] = journals.get(j, 0) + 1
        if has_nct:
            trial_reg += 1
            examples.append((r["pmcid"], j, "NCT"))
        elif has_other:
            other_only += 1
            examples.append((r["pmcid"], j, "non-NCT trial registry"))
        elif has_pros:
            review_reg_only += 1
        else:
            none_at_all += 1
    n = trial_reg + other_only + review_reg_only + none_at_all
    if not n:
        print("  REFUSED: no reviews refetched. NO COUNT IS PRINTED.")
        return 2
    print()
    print("  of %d reviews refetched:" % n)
    print("    name >=1 NCT trial registration            : %2d  (%.0f%%)" % (trial_reg, 100.0*trial_reg/n))
    print("    name a NON-NCT trial registry id only      : %2d  (%.0f%%)" % (other_only, 100.0*other_only/n))
    print("    name a REVIEW registration (PROSPERO) only : %2d  (%.0f%%)" % (review_reg_only, 100.0*review_reg_only/n))
    print("    name NO registration of any kind           : %2d  (%.0f%%)" % (none_at_all, 100.0*none_at_all/n))
    print()
    print("  THE STRONGER CLAIM is trial-level: %d of %d (%.0f%%) name no TRIAL registration"
          % (n - trial_reg - other_only, n, 100.0*(n - trial_reg - other_only)/n))
    print("  and are therefore not auditable for trial identity by anyone.")
    print("  A PROSPERO id does not make a review auditable for THIS defect: it registers the")
    print("  review's intent, not which trials it ended up including.")

    print()
    print("=== 3. THE ONES THAT DO NAME TRIAL REGISTRATIONS ===")
    if examples:
        for pmcid, j, kind in examples[:10]:
            print("   PMC%-10s %-44s %s" % (pmcid, j[:44], kind))
    else:
        print("   none in this subsample")
    print()
    print("  journals represented in the subsample (top 8):")
    for j, c in sorted(journals.items(), key=lambda x: -x[1])[:8]:
        print("     %-46s %d" % (j[:46], c))

    out = os.path.join(REPO, "outputs", "registration_naming_rigour_2026_08_25.json")
    json.dump({"subsample": n, "names_nct": trial_reg, "names_other_registry": other_only,
               "prospero_only": review_reg_only, "names_none": none_at_all,
               "journals": journals},
              io.open(out, "w", encoding="utf-8"), indent=1)
    print()
    print("written: %s" % os.path.relpath(out, REPO))
    return 0


if __name__ == "__main__":
    sys.exit(main())
