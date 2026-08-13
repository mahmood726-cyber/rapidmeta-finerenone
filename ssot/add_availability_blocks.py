"""Data and software availability, in the journal's required shape.

THE LICENCE SPLIT IS THE POINT. The code is MIT; the deposited data is CC0. They
are different objects and conflating them is a common error with real
consequences: MIT carries an attribution and licence-retention condition, CC0
waives everything. A reader told "MIT licensed" about a dataset would think they
owe attribution they do not owe; a reader told "CC0" about the code would think
they may strip the copyright notice, which MIT forbids. Both statements name
their object explicitly and neither inherits from the other.

Structured as defaults for every Nafis paper, not as ARNI fields.
"""
import io
import json
import sys

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

P = "ssot/arni-hfref/arni-hfref.json"
d = json.load(open(P, encoding="utf-8"))
m = d["manuscript"]

m["licences"] = {
    "_why_two": (
        "The software and the data are different objects and carry different "
        "licences. Stating one and letting a reader infer the other is the "
        "common error here."),
    "code": {
        "spdx": "MIT",
        "applies_to": "All source code: the generator, the projectors, the "
                      "detectors, the guards and the build scripts.",
        "verified": ("Confirmed at the GitHub API, not assumed: "
                     "repos/mahmood726-cyber/rapidmeta-finerenone reports "
                     "license.spdx_id MIT with path LICENSE at the repository "
                     "root, which is the detection Zenodo reads."),
        "obligation": "Attribution and retention of the licence notice.",
    },
    "data": {
        "spdx": "CC0-1.0",
        "applies_to": "The deposited extended data: the screening log, the search "
                      "capture, the extraction tables, the canonical object, and "
                      "the PRISMA materials.",
        "obligation": "None. All rights waived.",
        "why_cc0_not_mit": (
            "MIT is a software licence and its terms do not fit a dataset. The "
            "journal requires extended data under CC0 or CC-BY; CC0 is chosen so "
            "reuse carries no condition at all."),
    },
}

m["data_availability_statement"] = {
    "_format": "The journal's required structure for a Data Availability Statement.",
    "_mandatory": "Required even when there is no data.",
    "underlying_data": (
        "No new participant-level data were generated. All data underlying this "
        "review are derived from published randomised trials and from public "
        "registry records, and every record is identified in the extended data."),
    "extended_data": {
        "repository": "Zenodo",
        "title": "Extended data for: sacubitril/valsartan versus enalapril in "
                 "heart failure with reduced ejection fraction",
        "persistent_identifier": None,
        "identifier_status": (
            "NOT YET MINTED. Recorded as absent rather than filled with a "
            "plausible string: a wrong identifier in a Data Availability "
            "Statement points a reader at someone else's data, which is worse "
            "than no identifier at all."),
        "files": [
            ("canonical_object.json",
             "The single object every number in this article is projected from."),
            ("screening_log.csv",
             "All [[n_records]] records the search returned, with the stage, the "
             "decision, the eligibility axis that failed, and what each excluded "
             "record reported instead."),
            ("search_capture.csv",
             "Each database with the query string exactly as executed, the "
             "endpoint, parameters, filters and the hit count returned."),
            ("PRISMA_flow.md",
             "Flow counted from the screening log at build time."),
            ("PRISMA_checklist.md",
             "PRISMA 2020, item by item; items not reported are answered No."),
            ("extended_data_tables.docx",
             "Extraction with per-cell provenance, all sensitivity and estimator "
             "analyses, secondary pooled outcomes, the full GRADE profile, "
             "risk-of-bias judgements from both assessors with the unresolved "
             "disagreements, the reconciliation record, the attestation record, "
             "and the executed code."),
            ("README.md",
             "Written for a reader holding only the identifier and none of the "
             "article's context."),
            ("MANIFEST.sha256",
             "Checksums for every file above."),
        ],
        "licence": "CC0 1.0 Universal (CC0 1.0) Public Domain Dedication",
    },
    "blocks_submission_until_minted": True,
}

m["software_availability"] = {
    "_format": "The journal's required four-line software availability block.",
    "source_code_available_from": "https://github.com/mahmood726-cyber/rapidmeta-finerenone",
    "version_control": "https://github.com/mahmood726-cyber/rapidmeta-finerenone",
    "archived_source_code_at_time_of_publication": None,
    "archive_status": (
        "NOT YET DEPOSITED. Zenodo must be authorised against the repository and "
        "a tagged release cut; Zenodo then mints a version-specific identifier "
        "for that tag and a concept identifier that always resolves to the "
        "latest. The VERSION-SPECIFIC one belongs in this article, because that "
        "is the code that produced these results; the concept one belongs in the "
        "repository README."),
    "licence": "MIT",
    "licence_verified": (
        "Verified at the GitHub API rather than assumed: license.spdx_id is MIT "
        "and the file is LICENSE at the repository root, which is what Zenodo "
        "reads."),
    "blocks_submission_until_archived": True,
}

json.dump(d, open(P, "w", encoding="utf-8"), indent=1, ensure_ascii=False)
das = m["data_availability_statement"]
print("data availability : repository %s, %d files, licence %s"
      % (das["extended_data"]["repository"], len(das["extended_data"]["files"]),
         das["extended_data"]["licence"]))
print("                    identifier: %s"
      % (das["extended_data"]["persistent_identifier"] or "NOT YET MINTED (blocks)"))
print("software          : licence %s (verified at the API), archive %s"
      % (m["software_availability"]["licence"],
         m["software_availability"]["archived_source_code_at_time_of_publication"]
         or "NOT YET DEPOSITED (blocks)"))
print("licences          : code %s / data %s -- stated separately"
      % (m["licences"]["code"]["spdx"], m["licences"]["data"]["spdx"]))
