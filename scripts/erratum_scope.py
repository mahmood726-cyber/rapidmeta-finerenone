#!/usr/bin/env python
"""Disk-only erratum notice scope tools for MetaGuard D-32.

This module deliberately performs no network calls. It reconstructs the D-32
erratum row set from local MetaGuard artifacts and emits EFetch request payloads
that an operator can run outside the socket-restricted sandbox.
"""

from __future__ import annotations

import argparse
import csv
import dataclasses
import json
import os
import re
import tempfile
from pathlib import Path
from typing import Any, Iterable
from urllib.parse import urlencode


EFETCH_ENDPOINT = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi"

ERRATUM_TOUCHES_STORED_CELL = "ERRATUM_TOUCHES_STORED_CELL"
ERRATUM_LIKELY_NUMERIC = "ERRATUM_LIKELY_NUMERIC"
ERRATUM_OFF_TARGET = "ERRATUM_OFF_TARGET"
ERRATUM_INERT = "ERRATUM_INERT"

STORED_FIELDS = {
    "n_t",
    "n_c",
    "e_t",
    "e_c",
    "mean_t",
    "mean_c",
    "sd_t",
    "sd_c",
    "effect",
    "se",
    "ci_lo",
    "ci_hi",
    "reported_n",
    "trial_true_n",
    "reported_events",
    "weight",
    "outcome",
    "timepoint",
}

INERT_FIELDS = {
    "author",
    "authors",
    "affiliation",
    "affiliations",
    "funding",
    "conflict_of_interest",
    "acknowledgements",
    "orcid",
    "title",
    "spelling",
    "reference_list",
}

OFF_TARGET_FIELDS = {
    "p_value",
    "baseline_characteristics",
    "supplementary_material",
    "axis_label",
    "page_number",
    "unit_label",
}


@dataclasses.dataclass(frozen=True)
class ErratumScopeClassification:
    code: str
    fields_touched: list[str]
    stored_fields: list[str]
    inert_fields: list[str]
    off_target_fields: list[str]
    numeric_hints: list[str]
    evidence_terms: list[str]

    def to_json_dict(self) -> dict[str, Any]:
        return dataclasses.asdict(self)


def _field_patterns() -> list[tuple[re.Pattern[str], set[str], str]]:
    return [
        (
            re.compile(
                r"\b(hazard ratio|odds ratio|risk ratio|relative risk|rate ratio|"
                r"incidence rate ratio|mean difference|standardi[sz]ed mean|"
                r"effect estimate|effect size|estimate)\b",
                re.I,
            ),
            {"effect"},
            "effect estimate",
        ),
        (
            re.compile(r"\b(confidence interval|confidence limits?|95%\s*ci|\bci\b)\b", re.I),
            {"ci_lo", "ci_hi"},
            "confidence interval",
        ),
        (re.compile(r"\b(standard error|standard errors|\bse\b)\b", re.I), {"se"}, "standard error"),
        (
            re.compile(r"\b(standard deviation|standard deviations|\bsd\b)\b", re.I),
            {"sd_t", "sd_c"},
            "standard deviation",
        ),
        (
            re.compile(r"\b(least[- ]squares mean|mean change|change from baseline|mean value|mean)\b", re.I),
            {"mean_t", "mean_c"},
            "mean",
        ),
        (
            re.compile(
                r"\b(sample size|number of patients|number of participants|participants|"
                r"patients|randomi[sz]ed|analysed|analyzed|enrolled|denominator)\b",
                re.I,
            ),
            {"reported_n", "trial_true_n", "n_t", "n_c"},
            "sample size",
        ),
        (
            re.compile(
                r"\b(events?|deaths?|responders?|nonresponders?|cases?|numerator|"
                r"adverse events?|serious adverse events?)\b",
                re.I,
            ),
            {"reported_events", "e_t", "e_c"},
            "event count",
        ),
        (re.compile(r"\b(outcome|endpoint|end point)\b", re.I), {"outcome"}, "outcome"),
        (re.compile(r"\b(time point|timepoint|week\s+\d+|month\s+\d+)\b", re.I), {"timepoint"}, "timepoint"),
        (re.compile(r"\b(weight|inverse variance)\b", re.I), {"weight"}, "weight"),
    ]


INERT_PATTERNS: list[tuple[re.Pattern[str], set[str], str]] = [
    (re.compile(r"\b(authors?|byline)\b", re.I), {"author", "authors"}, "author"),
    (re.compile(r"\b(affiliations?|departments?|institutions?)\b", re.I), {"affiliation"}, "affiliation"),
    (re.compile(r"\b(funding|grant|funder)\b", re.I), {"funding"}, "funding"),
    (
        re.compile(r"\b(conflicts? of interest|competing interests?|disclosures?)\b", re.I),
        {"conflict_of_interest"},
        "conflict of interest",
    ),
    (re.compile(r"\b(acknowledg?ements?)\b", re.I), {"acknowledgements"}, "acknowledgements"),
    (re.compile(r"\b(orcid)\b", re.I), {"orcid"}, "orcid"),
    (re.compile(r"\b(article title|title)\b", re.I), {"title"}, "title"),
    (re.compile(r"\b(spell(?:ing)?|misspell(?:ed|ing)|typographical)\b", re.I), {"spelling"}, "spelling"),
    (re.compile(r"\b(references?|citation)\b", re.I), {"reference_list"}, "reference list"),
]

OFF_TARGET_PATTERNS: list[tuple[re.Pattern[str], set[str], str]] = [
    (re.compile(r"\b(p[- ]?value|p\s*[<=>])", re.I), {"p_value"}, "p value"),
    (
        re.compile(r"\b(baseline characteristic|baseline characteristics|age|sex|race|body mass index|bmi)\b", re.I),
        {"baseline_characteristics"},
        "baseline characteristics",
    ),
    (
        re.compile(r"\b(supplement|supplementary appendix|appendix|webappendix)\b", re.I),
        {"supplementary_material"},
        "supplementary material",
    ),
    (re.compile(r"\b(axis label|legend|figure legend)\b", re.I), {"axis_label"}, "axis label"),
    (re.compile(r"\b(page number|pagination)\b", re.I), {"page_number"}, "page number"),
    (re.compile(r"\b(unit label|units? of measure)\b", re.I), {"unit_label"}, "unit label"),
]

NUMERIC_HINT_PATTERNS: list[tuple[re.Pattern[str], str]] = [
    (re.compile(r"\b(table|figure|fig\.|panel|column|row)\b", re.I), "table or figure"),
    (re.compile(r"\b(should read|should have read|read as follows|corrected to)\b", re.I), "replacement text"),
    (re.compile(r"\b(incorrect|incorrectly|erroneous|error|miscalculated|recalculated)\b", re.I), "correction word"),
    (re.compile(r"\b(transposed|reversed|decimal|rounded|rounding)\b", re.I), "numeric edit"),
    (re.compile(r"\b\d+(?:\.\d+)?\s*(?:%|percent|percentage)\b", re.I), "percentage"),
    (re.compile(r"\b\d+(?:\.\d+)?\s*(?:-|to)\s*\d+(?:\.\d+)?\b", re.I), "numeric range"),
]


def _clean_pmid(value: Any) -> str | None:
    if value is None:
        return None
    match = re.search(r"\d{5,9}", str(value))
    return match.group(0) if match else None


def _normalize_notice_text(notice_text: str) -> str:
    return " ".join(str(notice_text or "").replace("\x00", " ").split())


def _collect_fields(
    text: str,
    patterns: Iterable[tuple[re.Pattern[str], set[str], str]],
) -> tuple[set[str], set[str]]:
    fields: set[str] = set()
    terms: set[str] = set()
    for pattern, pattern_fields, term in patterns:
        if pattern.search(text):
            fields.update(pattern_fields)
            terms.add(term)
    return fields, terms


def _collect_hints(text: str) -> set[str]:
    return {term for pattern, term in NUMERIC_HINT_PATTERNS if pattern.search(text)}


def classify_notice_scope(
    notice_text: str,
    populated_cells: Iterable[str] | None = None,
) -> ErratumScopeClassification:
    """Classify an erratum notice against the D-32 stored-cell vocabulary.

    When `populated_cells` is omitted, all D-32 stored fields are considered
    present. A row-specific caller should pass only the cells actually populated
    by that corpus row.
    """

    text = _normalize_notice_text(notice_text)
    if not text:
        raise ValueError("notice_text is empty")

    stored_fields, stored_terms = _collect_fields(text, _field_patterns())
    inert_fields, inert_terms = _collect_fields(text, INERT_PATTERNS)
    off_target_fields, off_target_terms = _collect_fields(text, OFF_TARGET_PATTERNS)
    numeric_hints = _collect_hints(text)

    populated = set(populated_cells or STORED_FIELDS)
    fields_touched = stored_fields | inert_fields | off_target_fields
    evidence_terms = stored_terms | inert_terms | off_target_terms | numeric_hints

    if stored_fields:
        code = ERRATUM_TOUCHES_STORED_CELL if stored_fields & populated else ERRATUM_OFF_TARGET
    elif off_target_fields:
        code = ERRATUM_OFF_TARGET
    elif inert_fields:
        code = ERRATUM_INERT
    elif numeric_hints:
        code = ERRATUM_LIKELY_NUMERIC
    else:
        # Fail closed: a correction notice that is not recognisably inert should
        # stay in the review queue even when it lacks field-specific language.
        code = ERRATUM_LIKELY_NUMERIC
        numeric_hints.add("unclassified correction notice")
        evidence_terms.add("unclassified correction notice")

    return ErratumScopeClassification(
        code=code,
        fields_touched=sorted(fields_touched),
        stored_fields=sorted(stored_fields),
        inert_fields=sorted(inert_fields),
        off_target_fields=sorted(off_target_fields),
        numeric_hints=sorted(numeric_hints),
        evidence_terms=sorted(evidence_terms),
    )


def _atomic_write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(
        "w",
        encoding="utf-8",
        newline="\n",
        delete=False,
        dir=str(path.parent),
    ) as handle:
        handle.write(text)
        temp_name = handle.name
    os.replace(temp_name, path)


def _atomic_write_json(path: Path, payload: dict[str, Any]) -> None:
    _atomic_write_text(path, json.dumps(payload, indent=2, sort_keys=True) + "\n")


def _populated_stored_cells(row: dict[str, Any]) -> list[str]:
    return sorted(field for field in STORED_FIELDS if row.get(field) is not None)


def _load_erratum_rows(corpus_path: Path) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    with corpus_path.open("r", encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, start=1):
            line = line.strip()
            if not line:
                continue
            pool = json.loads(line)
            lane = ((pool.get("external") or {}).get("erratum_lane") or {})
            for row in pool.get("rows") or []:
                citation_id = str(row.get("citation_id") or row.get("row_id") or "")
                rec = lane.get(citation_id)
                if not rec or not rec.get("has_erratum"):
                    continue
                notice_pmids = [
                    pmid
                    for pmid in (_clean_pmid(value) for value in rec.get("erratum_pmids") or [])
                    if pmid
                ]
                primary_notice_pmid = _clean_pmid(rec.get("erratum_pmid"))
                if primary_notice_pmid and primary_notice_pmid not in notice_pmids:
                    notice_pmids.insert(0, primary_notice_pmid)
                out.append(
                    {
                        "pool_id": pool.get("pool_id"),
                        "source_file": pool.get("source_file"),
                        "row_id": row.get("row_id"),
                        "trial_key": row.get("trial_key"),
                        "citation_id": citation_id,
                        "original_pmid": _clean_pmid(citation_id),
                        "erratum_pmids": notice_pmids,
                        "erratum_text_from_relation": rec.get("erratum_text") or "",
                        "populated_cells": _populated_stored_cells(row),
                        "corpus_line": line_number,
                    }
                )
    return out


def _batched(values: list[str], batch_size: int) -> list[list[str]]:
    return [values[index : index + batch_size] for index in range(0, len(values), batch_size)]


def _numeric_sort(values: Iterable[str]) -> list[str]:
    return sorted(set(values), key=lambda value: int(value))


def _build_efetch_payloads(notice_pmids: list[str], batch_size: int) -> list[dict[str, Any]]:
    payloads: list[dict[str, Any]] = []
    for batch_index, batch in enumerate(_batched(notice_pmids, batch_size), start=1):
        params = {
            "db": "pubmed",
            "id": ",".join(batch),
            "retmode": "xml",
        }
        body = urlencode(params, safe=",")
        payloads.append(
            {
                "batch_index": batch_index,
                "method": "POST",
                "endpoint": EFETCH_ENDPOINT,
                "headers": {"Content-Type": "application/x-www-form-urlencoded"},
                "params": params,
                "payload": body,
                "id_count": len(batch),
                "pmids": batch,
                "equivalent_get_url": f"{EFETCH_ENDPOINT}?{body}",
            }
        )
    return payloads


def _payload_text(payloads: list[dict[str, Any]]) -> str:
    chunks: list[str] = []
    for payload in payloads:
        chunks.append(
            "\n".join(
                [
                    f"# batch {payload['batch_index']} ({payload['id_count']} PMIDs)",
                    f"POST {payload['endpoint']}",
                    "Content-Type: application/x-www-form-urlencoded",
                    "",
                    str(payload["payload"]),
                ]
            )
        )
    return "\n\n".join(chunks) + "\n"


def _write_rows_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = [
        "pool_id",
        "source_file",
        "row_id",
        "trial_key",
        "citation_id",
        "original_pmid",
        "erratum_pmids",
        "populated_cells",
    ]
    with tempfile.NamedTemporaryFile(
        "w",
        encoding="utf-8",
        newline="",
        delete=False,
        dir=str(path.parent),
    ) as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow(
                {
                    **{field: row.get(field) for field in fieldnames},
                    "erratum_pmids": ";".join(row.get("erratum_pmids") or []),
                    "populated_cells": ";".join(row.get("populated_cells") or []),
                }
            )
        temp_name = handle.name
    os.replace(temp_name, path)


def build_erratum_scope_artifacts(
    corpus_path: Path,
    relations_path: Path,
    manifest_path: Path,
    output_dir: Path,
    batch_size: int = 50,
) -> dict[str, Any]:
    if batch_size <= 0:
        raise ValueError("batch_size must be positive")
    rows = _load_erratum_rows(corpus_path)
    relations = json.loads(relations_path.read_text(encoding="utf-8"))
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))

    original_pmids_from_rows = _numeric_sort(
        pmid for pmid in (row.get("original_pmid") for row in rows) if pmid
    )
    notice_pmids_from_rows = _numeric_sort(
        pmid for row in rows for pmid in (row.get("erratum_pmids") or [])
    )
    relation_notice_pmids = _numeric_sort(
        pmid for pmid in (_clean_pmid(rel.get("erratum_pmid")) for rel in relations) if pmid
    )
    relation_rows_missing_notice_pmid = [
        {
            "original_pmid": rel.get("original_pmid"),
            "refsource": rel.get("refsource"),
        }
        for rel in relations
        if not _clean_pmid(rel.get("erratum_pmid"))
    ]

    payloads = _build_efetch_payloads(notice_pmids_from_rows, batch_size=batch_size)

    inventory_path = output_dir / "erratum_scope_inventory.json"
    payload_json_path = output_dir / "erratum_notice_efetch_payloads.json"
    payload_text_path = output_dir / "erratum_notice_efetch_payloads.txt"
    rows_csv_path = output_dir / "erratum_scope_rows.csv"

    summary = {
        "source_artifacts": {
            "corpus_path": str(corpus_path),
            "relations_path": str(relations_path),
            "manifest_path": str(manifest_path),
        },
        "rows_submitted_for_notice_scope": len(rows),
        "corpus_rows_denominator": int(manifest["rows"]),
        "unique_original_pmids_with_erratum_relation": len(original_pmids_from_rows),
        "original_pmids": original_pmids_from_rows,
        "erratum_relation_rows": len(relations),
        "unique_erratum_notice_pmids_for_efetch": len(notice_pmids_from_rows),
        "relation_notice_pmids_for_efetch": len(relation_notice_pmids),
        "efetch_batch_size": batch_size,
        "efetch_batch_count": len(payloads),
        "efetch_payload_id_counts": [payload["id_count"] for payload in payloads],
        "relation_rows_missing_notice_pmid": len(relation_rows_missing_notice_pmid),
        "rows_without_notice_pmid": sum(1 for row in rows if not row.get("erratum_pmids")),
        "output_paths": {
            "inventory": str(inventory_path),
            "rows_csv": str(rows_csv_path),
            "payloads_json": str(payload_json_path),
            "payloads_text": str(payload_text_path),
        },
        "notes": [
            "No network calls were attempted.",
            "EFetch payloads target erratum notice PMIDs only; relation rows without a target PMID need PMID resolution from refsource before efetch-by-ID.",
        ],
    }

    _atomic_write_json(
        inventory_path,
        {
            **summary,
            "relation_rows_missing_notice_pmid_detail": relation_rows_missing_notice_pmid,
            "rows": rows,
        },
    )
    _write_rows_csv(rows_csv_path, rows)
    _atomic_write_json(
        payload_json_path,
        {
            "endpoint": EFETCH_ENDPOINT,
            "purpose": "Fetch PubMed XML for erratum notice records so D-32 scope parser can inspect notice text.",
            "no_network_attempted": True,
            "payloads": payloads,
            "missing_notice_pmid_relation_rows": relation_rows_missing_notice_pmid,
        },
    )
    _atomic_write_text(payload_text_path, _payload_text(payloads))
    return summary


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Prepare offline erratum D-32 notice-scope jobs.")
    parser.add_argument(
        "--corpus-path",
        default=str(Path("outputs") / "metaguard_run" / "rapidmeta_metaguard_corpus.ndjson"),
    )
    parser.add_argument(
        "--relations-path",
        default=str(Path("outputs") / "metaguard_run" / "erratum_relations_from_pubmed_cache.json"),
    )
    parser.add_argument(
        "--manifest-path",
        default=str(Path("outputs") / "metaguard_run" / "rapidmeta_metaguard_manifest.json"),
    )
    parser.add_argument("--output-dir", default=str(Path("outputs") / "metaguard_run"))
    parser.add_argument("--batch-size", type=int, default=50)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_arg_parser().parse_args(argv)
    summary = build_erratum_scope_artifacts(
        corpus_path=Path(args.corpus_path),
        relations_path=Path(args.relations_path),
        manifest_path=Path(args.manifest_path),
        output_dir=Path(args.output_dir),
        batch_size=args.batch_size,
    )
    print(json.dumps(summary, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
