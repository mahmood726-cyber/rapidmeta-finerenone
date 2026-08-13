import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "scripts"))

from erratum_scope import (  # noqa: E402
    ERRATUM_INERT,
    ERRATUM_LIKELY_NUMERIC,
    ERRATUM_OFF_TARGET,
    ERRATUM_TOUCHES_STORED_CELL,
    build_erratum_scope_artifacts,
    classify_notice_scope,
)


def test_notice_parser_touches_stored_effect_and_ci():
    result = classify_notice_scope(
        "In Table 2, the hazard ratio was reported incorrectly. "
        "It should read 0.79 with a 95% CI of 0.66 to 0.94.",
        populated_cells={"effect", "ci_lo", "ci_hi", "reported_n"},
    )

    assert result.code == ERRATUM_TOUCHES_STORED_CELL
    assert {"effect", "ci_lo", "ci_hi"}.issubset(result.fields_touched)


def test_notice_parser_likely_numeric_when_table_scope_is_unstructured():
    result = classify_notice_scope(
        "Values in Table 1, column 3 were transposed and corrected online.",
        populated_cells={"effect"},
    )

    assert result.code == ERRATUM_LIKELY_NUMERIC
    assert "table or figure" in result.numeric_hints


def test_notice_parser_off_target_for_p_value_only():
    result = classify_notice_scope(
        "The p value in Figure 2 was incorrect and should read P=0.04.",
        populated_cells={"effect", "ci_lo", "ci_hi"},
    )

    assert result.code == ERRATUM_OFF_TARGET
    assert result.fields_touched == ["p_value"]


def test_notice_parser_inert_for_affiliation_and_funding():
    result = classify_notice_scope(
        "The affiliation of the third author and the funding statement were listed incorrectly.",
        populated_cells={"effect"},
    )

    assert result.code == ERRATUM_INERT
    assert {"affiliation", "funding"}.issubset(result.fields_touched)


def test_erratum_scope_artifact_counts_from_local_metaguard_outputs(tmp_path):
    summary = build_erratum_scope_artifacts(
        corpus_path=REPO_ROOT / "outputs" / "metaguard_run" / "rapidmeta_metaguard_corpus.ndjson",
        relations_path=REPO_ROOT / "outputs" / "metaguard_run" / "erratum_relations_from_pubmed_cache.json",
        manifest_path=REPO_ROOT / "outputs" / "metaguard_run" / "rapidmeta_metaguard_manifest.json",
        output_dir=tmp_path,
        batch_size=50,
    )

    assert summary["rows_submitted_for_notice_scope"] == 105
    assert summary["corpus_rows_denominator"] == 3656
    assert summary["unique_original_pmids_with_erratum_relation"] == 83
    assert summary["unique_erratum_notice_pmids_for_efetch"] == 82
    assert summary["relation_rows_missing_notice_pmid"] == 12
    assert summary["efetch_payload_id_counts"] == [50, 32]
    assert (tmp_path / "erratum_scope_inventory.json").is_file()
    assert (tmp_path / "erratum_notice_efetch_payloads.json").is_file()
    assert (tmp_path / "erratum_notice_efetch_payloads.txt").is_file()
