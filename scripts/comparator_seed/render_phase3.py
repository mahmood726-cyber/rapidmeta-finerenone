"""Render the PHASE 3 report as markdown: the comparator table and the named missing trials."""
import argparse
import json
import io
import os
import sys

if __name__ == "__main__":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")


def esc(s):
    return (s or "").replace("|", "\\|").replace("\n", " ").strip()


def name_of(s):
    bits = [b for b in (s.get("first_author"), s.get("year")) if b]
    label = " ".join(bits) if bits else "(no author/year in the citation)"
    if s.get("acronym"):
        label += " [%s]" % s["acronym"]
    ids = []
    if s.get("resolved_ncts"):
        ids.append("/".join(s["resolved_ncts"]))
    if s.get("pmid"):
        ids.append("PMID %s" % s["pmid"])
    return label + (" (%s)" % "; ".join(ids) if ids else "")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--report", default=r"C:/claude-temp/comparator-seed/work/phase3_report.json")
    ap.add_argument("--out", default=r"C:/claude-temp/comparator-seed/stage/outputs/comparator_seed_phase3.md")
    args = ap.parse_args()
    with open(args.report, encoding="utf-8") as fh:
        d = json.load(fh)
    cs = sorted(d["comparators"], key=lambda c: (c["field"], -c["k_extracted"]))
    L = []

    L.append("## The 40 comparators\n")
    L.append("`k_ext` is MEASURED (references cited from the study-characteristics table). "
             "`k_dec` is INFERRED from the abstract and is **not reliable** — see the "
             "agreement figure in the finding. `close` is the declared search close date, "
             "INFERRED from the methods section, with the sentence quoted in the JSON.\n")
    L.append("| # | field | PMCID | journal | yr | close | k_ext | k_dec | held | not held | out of scope | unresolvable |")
    L.append("|---|---|---|---|---|---|---|---|---|---|---|---|")
    for i, c in enumerate(cs, 1):
        n = c["counts"]
        unres = n.get("UNRESOLVABLE_NO_REGISTRY_ID", 0) + n.get("UNRESOLVABLE_NO_PMID", 0)
        L.append("| %d | %s | [PMC%s](https://pmc.ncbi.nlm.nih.gov/articles/PMC%s/) | %s | %s | %s | %d | %s | %d | %d | %d | %d |" % (
            i, "cardio" if c["field"] == "cardiology" else "ID", c["pmcid"], c["pmcid"],
            esc((c["journal"] or "")[:34]), c["year"] or "?",
            c["search_close_date"]["value"] or "—",
            c["k_extracted"], c["declared_k"]["value"] if c["declared_k"]["value"] else "—",
            n.get("HELD", 0), n.get("NOT_HELD", 0), n.get("OUT_OF_SCOPE_DESIGN", 0), unres))

    L.append("\n### Titles\n")
    for i, c in enumerate(cs, 1):
        L.append("%d. **PMC%s** — %s *(%s)*  \n   DOI `%s` · topic terms: %s" % (
            i, c["pmcid"], esc((c["title"] or "")[:190]), esc(c["journal"] or "?"),
            c["doi"], ", ".join(c["terms"][:4])))

    L.append("\n---\n\n## Named missing trials — the deliverable\n")
    L.append("A trial is listed here only when it resolved to a ClinicalTrials.gov "
             "accession **and** that accession is absent from our holdings. Studies the "
             "comparator's own characteristics row calls observational are listed "
             "separately with the reason quoted. Studies that resolve to no registry id "
             "are not listed as missing, because an NCT-keyed store cannot answer them.\n")
    for c in cs:
        miss = [s for s in c["included_studies"] if s["status"] == "NOT_HELD"]
        if not miss:
            continue
        L.append("\n### PMC%s — %s" % (c["pmcid"], esc((c["title"] or "")[:130])))
        L.append("*%s · their k (measured) %d · search closed %s · we hold %d*\n" % (
            "cardiology" if c["field"] == "cardiology" else "infectious disease",
            c["k_extracted"], c["search_close_date"]["value"] or "not stated",
            c["counts"].get("HELD", 0)))
        for s in miss:
            L.append("- %s" % name_of(s))

    L.append("\n---\n\n## Excluded by a declared scope reason, with the reason quoted\n")
    shown = 0
    for c in cs:
        oos = [s for s in c["included_studies"] if s["status"] == "OUT_OF_SCOPE_DESIGN"]
        if not oos:
            continue
        L.append("\n**PMC%s** (%d of %d studies):" % (c["pmcid"], len(oos), c["k_extracted"]))
        for s in oos[:6]:
            L.append("- %s — comparator's row: `%s`" % (
                name_of(s), esc((s["design"]["quote"] or "")[:130])))
            shown += 1
        if len(oos) > 6:
            L.append("- …and %d more, all listed in the JSON" % (len(oos) - 6))
    L.append("\n*%d of %d out-of-scope studies shown; every one is in the JSON.*" % (
        shown, d["totals"]["OUT_OF_SCOPE_DESIGN"]))

    os.makedirs(os.path.dirname(args.out), exist_ok=True)
    with open(args.out, "w", encoding="utf-8") as fh:
        fh.write("\n".join(L) + "\n")
    print("wrote", args.out, len("\n".join(L)), "chars")


if __name__ == "__main__":
    main()
