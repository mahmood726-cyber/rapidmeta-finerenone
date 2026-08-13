"""Add the journal's mandatory manuscript elements to the canonical object.

These are defaults for every Nafis paper, not an ARNI special case: the profile
in journal_profile.py states the requirement and this fills the fields the
profile validates. The prose is authored and stored in the object for the same
reason the rest of the manuscript is -- one reviewable place, and quantities as
tokens so the abstract cannot drift from the analysis.

THE ABSTRACT WAS 425 WORDS IN EIGHT SECTIONS. The journal requires four sections
and at most 300. The long form is not deleted; it is kept as `abstract_extended`
because it is the better description of the methods and belongs in the deposit
package, where there is no word limit.
"""
import io
import json
import sys

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
sys.path.insert(0, "ssot")
import journal_profile as jp  # noqa: E402

P = "ssot/arni-hfref/arni-hfref.json"
d = json.load(open(P, encoding="utf-8"))
m = d["manuscript"]

if "abstract_extended" not in m:
    m["abstract_extended"] = dict(m["abstract"])
    m["abstract_extended"]["_why_kept"] = (
        "The eight-section, 425-word abstract written before the journal profile "
        "was applied. It describes the methods better than 300 words allow and is "
        "carried into the deposit package, where there is no limit. Kept rather "
        "than deleted so the shorter one can be checked against it.")

m["abstract"] = {
    "_structure": "Structured, four sections, journal-mandated order.",
    "_limit": "300 words. Counted at build time and the build fails if exceeded.",
    "Background": (
        "Angiotensin receptor-neprilysin inhibition changed the treatment of "
        "heart failure with reduced ejection fraction on the strength of a "
        "single large trial. Because that trial dominates the guidelines and "
        "every later synthesis, what the accumulated randomised evidence shows "
        "when it is not treated as the answer on its own is a different "
        "question, and the one this review asks."),
    "Methods": (
        "PubMed and ClinicalTrials.gov were searched on [[search_date]] with no "
        "language, date or publication-status filter. Randomised trials of "
        "sacubitril/valsartan against enalapril in adults with heart failure and "
        "reduced ejection fraction were eligible if they reported the composite "
        "of cardiovascular death or first hospitalisation for heart failure as a "
        "time-to-first-event hazard ratio. Hazard ratios were pooled on the log "
        "scale by generic inverse variance under a random-effects model with the "
        "[[estimator]] estimator. Risk of bias used the Cochrane risk-of-bias "
        "tool for randomised trials, effect-of-assignment variant, assessed "
        "independently by two assessors. Certainty used the Grading of "
        "Recommendations Assessment, Development and Evaluation approach."),
    "Results": (
        "[[n_records]] records were screened and [[k]] trials contributing "
        "[[n_total]] randomised participants met all eligibility conditions. The "
        "pooled hazard ratio was [[pooled]] ([[ci_low]] to [[ci_high]]), "
        "favouring sacubitril/valsartan. Heterogeneity was low, with I-squared "
        "[[i2]] percent. The result did not survive removal of the largest "
        "trial, which moved the estimate to [[loo_paradigm]], an interval "
        "including no effect. No risk-of-bias domain was rated high by either "
        "assessor. Certainty was [[certainty]]."),
    "Conclusions": (
        "Sacubitril/valsartan reduced the hazard of a first cardiovascular death "
        "or heart failure hospitalisation compared with enalapril, at "
        "[[certainty]] certainty. The estimate rests almost entirely on one "
        "trial and does not survive its removal; the two smaller trials are "
        "individually compatible with no effect. One trial establishes this "
        "benefit rather than three confirming it."),
}

m["keywords"] = [
    "heart failure", "reduced ejection fraction", "sacubitril/valsartan",
    "angiotensin receptor-neprilysin inhibitor", "enalapril",
    "meta-analysis", "systematic review", "hazard ratio",
]

m["data_availability_statement"] = {
    "_mandatory": "Required by the journal even when there is no data.",
    "statement": (
        "Underlying data. All data underlying this review are derived from "
        "published randomised trials and public registry records, and every "
        "record is identified in the extended data below. No new participant-"
        "level data were generated.\n\n"
        "Extended data. The complete screening log of [[n_records]] records with "
        "each decision and the eligibility axis it failed, the search capture "
        "with the query strings exactly as executed and their hit counts, the "
        "extraction tables with per-cell provenance, all sensitivity and "
        "estimator analyses, the risk-of-bias judgements from both assessors "
        "with the unresolved disagreements, the full certainty profile, the "
        "reconciliation record, the attestation record, the canonical data "
        "object from which every number in this article is projected, and the "
        "PRISMA checklist and flow diagram, are deposited in an approved "
        "repository under a CC0 waiver.\n\n"
        "REPOSITORY DOI: not yet minted. This statement carries a placeholder "
        "for the deposit identifier and the build FAILS submission conformance "
        "until it is replaced with the real DOI. It is recorded as absent rather "
        "than filled with a plausible-looking string, because a wrong DOI in a "
        "data availability statement points a reader at someone else's data."),
    "deposit_doi": None,
    "deposit_licence": "CC0 1.0 Universal",
    "blocks_submission_until_minted": True,
}

m["software_availability"] = {
    "statement": (
        "Source code available from: the project repository on GitHub.\n"
        "Archived source code at time of publication: NOT YET DEPOSITED -- a "
        "Zenodo archive with a DOI is required and has not been minted.\n"
        "Licence: an OSI-approved licence is required and is not yet declared "
        "in the repository."),
    "github": "https://github.com/mahmood726-cyber/rapidmeta-finerenone",
    "zenodo_doi": None,
    "licence": None,
    "blocks_submission_until_complete": True,
}

m["prisma"] = {
    "_mandatory": "Checklist and flow diagram are both required.",
    "flow_diagram": "Generated in the deposit package, counted from the screening log.",
    "checklist": "Generated in the deposit package, item by item.",
    "route": jp.F1000RESEARCH["prisma_route"],
    "deposit_doi": None,
}

m["registration_note_for_editor"] = (
    "This review's protocol was registered as a timestamped, SHA-pinned public "
    "commit rather than in PROSPERO. The commit precedes the first executed "
    "query by a recorded margin and the ordering is machine-checkable at every "
    "build, which is stronger evidence of prospective registration than a "
    "registry entry provides. It is NOT, however, the token the journal asks "
    "for, and the difference is stated here rather than presented as "
    "equivalent. Mahmood should decide whether to also register in PROSPERO.")

sections = {k: v for k, v in m["abstract"].items() if not k.startswith("_")}
import paper as pp
_res = d["results"]["by_outcome"][next(iter(d["results"]["by_outcome"]))]
_tok = pp.build_tokens(d, _res, next(iter(d["results"]["by_outcome"])))
n, problems = jp.check_abstract(sections, tokens=_tok)
problems += jp.check_keywords(m["keywords"])
print("abstract: %d words (limit %d), %d sections"
      % (n, jp.F1000RESEARCH["abstract_max_words"], len(sections)))
for k, v in sections.items():
    _f = __import__("re").sub(r"\[\[([a-z0-9_]+)\]\]",
                              lambda mm: str(_tok.get(mm.group(1), mm.group(0))), v)
    print("   %-12s %3d words (filled)" % (k, len(_f.split())))
print("keywords: %d (max %d)" % (len(m["keywords"]), jp.F1000RESEARCH["keywords_max"]))
print("validator problems:", problems or "NONE")
if problems:
    raise SystemExit("refusing to write an object that fails the profile")
json.dump(d, open(P, "w", encoding="utf-8"), indent=1, ensure_ascii=False)
print("\nwritten. abstract_extended preserved:", "abstract_extended" in m)
