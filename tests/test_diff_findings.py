# sentinel:skip-file
"""Regression coverage for harvest schemas, comparison semantics and publication safety."""
import contextlib
import io
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from scripts.workflow import diff_findings as diff


def record(app="A_REVIEW.html", concerns=("existing",), decision="Minor revision"):
    return {"app": app, "timestamp": "2026-10-14T00:00:00Z", "findings": {
        "editor": {"decision": decision},
        "reviewers": [{"role": "Methodologist", "concerns": list(concerns)}],
    }}


class DiffFindingsTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.findings = self.root / "findings"
        self.findings.mkdir()
        self.report = self.root / "diff.md"
        self.status = self.root / "status.md"
        self.outputs = self.root / "outputs"

    def tearDown(self):
        self.temp.cleanup()

    def write(self, directory, data, name="records.json"):
        directory.mkdir(exist_ok=True)
        (directory / name).write_text(json.dumps(data), encoding="utf-8")

    def snapshot(self, name, values, start="2026-10-14T01:00:00Z", end="2026-10-14T02:00:00Z", scope="full", pending=()):
        directory = self.findings / name
        directory.mkdir()
        pages = []
        for value in values:
            self.write(directory, value, value["app"].replace(".html", ".json"))
            normalized = diff.normalize_record(value, "test")
            pages.append({"app": value["app"], "status": normalized["status"]})
        pages.extend({"app": app, "status": "pending"} for app in pending)
        manifest = {"schemaVersion": 1, "startedAt": start, "finishedAt": end, "scope": scope,
                    "pages": pages, "total": len(pages),
                    **{s: sum(p["status"] == s for p in pages) for s in diff.STATUSES}}
        manifest["complete"] = bool(pages) and manifest["ok"] == len(pages) and scope == "full" and end is not None
        self.write(directory, manifest, diff.MANIFEST)
        return directory

    def run_diff(self, current):
        self.outputs.unlink(missing_ok=True)
        with patch.object(diff, "ROOT", self.root), patch.dict("os.environ", {"GITHUB_OUTPUT": str(self.outputs)}), contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
            code = diff.main(["--current", str(current), "--report", str(self.report), "--status-report", str(self.status)])
        outputs = dict(line.split("=", 1) for line in self.outputs.read_text().splitlines())
        return code, outputs

    def test_dictionary_record(self):
        self.write(self.findings, record())
        loaded = diff.load_dir(self.findings)
        self.assertEqual(loaded["A_REVIEW"]["findings"], record()["findings"])
        self.assertEqual(loaded["A_REVIEW"]["status"], "ok")

    def test_array_of_records_preserves_all_findings(self):
        self.write(self.findings, [record(), record("B_REVIEW.html", ("second",))])
        loaded = diff.load_dir(self.findings)
        self.assertEqual(set(loaded), {"A_REVIEW", "B_REVIEW"})
        self.assertEqual(loaded["B_REVIEW"]["findings"]["reviewers"][0]["concerns"], ["second"])

    def test_unrelated_arrays_and_scalars_rejected_with_location(self):
        for value in [[], ["12345678"], [{"path": "A_REVIEW.html", "ok": False}], 1, None, "text"]:
            with self.subTest(value=value):
                self.write(self.findings, value)
                with self.assertRaisesRegex(diff.HarvestError, "records.json"):
                    diff.load_dir(self.findings)

    def test_duplicate_identity_rejected(self):
        self.write(self.findings, [record(), record()])
        with self.assertRaisesRegex(diff.HarvestError, "duplicate app"):
            diff.load_dir(self.findings)

    def test_invalid_json_is_not_silently_skipped(self):
        (self.findings / "bad.json").write_text("{")
        with self.assertRaisesRegex(diff.HarvestError, "bad.json: cannot read JSON"):
            diff.load_dir(self.findings)

    def test_missing_and_null_findings_are_unobserved(self):
        for value in [{"app": "A_REVIEW.html", "timestamp": "2026-10-14T00:00:00Z"}, {"app": "A_REVIEW.html", "findings": None}]:
            normalized = diff.normalize_record(value, "test")
            self.assertEqual(normalized["status"], "skipped")
            self.assertEqual(diff.compare_records({"A": normalized}, {"A": diff.normalize_record(record(), "test")}), [])

    def test_legacy_skip_and_errors_are_not_successful_reviews(self):
        for finding, expected in [({"skipped": True, "reason": "no-state.results"}, "skipped"), ({"error": "review failed"}, "failed")]:
            value = record()
            value["findings"] = finding
            self.assertEqual(diff.normalize_record(value, "test")["status"], expected)
        self.assertEqual(diff.normalize_record({"app": "A_REVIEW.html", "error": "navigation timeout"}, "test")["status"], "failed")

    def test_malformed_findings_rejected(self):
        for finding in [[], {"editor": {}}, {"editor": {"decision": "Accept"}},
                        {"editor": {"decision": "Accept"}, "reviewers": [{"role": "M"}]},
                        {"editor": {"decision": "Accept"}, "reviewers": [{"role": "M", "concerns": [42]}]}]:
            value = record()
            value["findings"] = finding
            with self.subTest(finding=finding), self.assertRaises(diff.HarvestError):
                diff.normalize_record(value, "test")

    def test_unexpected_metadata_and_conflicting_status_are_rejected(self):
        values = [{"app": "A_REVIEW.html", "pmid": "123", "title": "audit"},
                  {**record(), "status": []}, {**record(), "error": "failure"},
                  {"app": "A_REVIEW.html", "error": 42}]
        for value in values:
            with self.subTest(value=value), self.assertRaises(diff.HarvestError):
                diff.normalize_record(value, "test")

    def test_success_status_cannot_mask_missing_findings(self):
        with self.assertRaisesRegex(diff.HarvestError, "contradicts"):
            diff.normalize_record({"app": "A_REVIEW.html", "status": "ok"}, "test")

    def test_new_resolved_and_changed_editor(self):
        old = diff.normalize_record(record(concerns=("existing", "resolved")), "old")
        new = diff.normalize_record(record(concerns=("new", "existing"), decision="Major revision"), "new")
        change = diff.compare_records({"A": new}, {"A": old})[0]
        self.assertTrue(change["editor_changed"])
        self.assertEqual(change["new"], [("Methodologist", "new")])
        self.assertEqual(change["resolved"], [("Methodologist", "resolved")])

    def test_editor_only_change(self):
        old = diff.normalize_record(record(), "old")
        new = diff.normalize_record(record(decision="Reject"), "new")
        change = diff.compare_records({"A": new}, {"A": old})[0]
        self.assertTrue(change["editor_changed"])
        self.assertEqual(change["new"], [])
        self.assertEqual(change["resolved"], [])

    def test_duplicate_reviewer_roles_do_not_overwrite_concerns(self):
        value = record()
        value["findings"]["reviewers"].append({"role": "Methodologist", "concerns": ["another"]})
        roles = diff.concerns_by_role(diff.normalize_record(value, "test")["findings"])
        self.assertEqual(roles["Methodologist"], {"existing", "another"})

    def test_absent_or_failed_page_never_resolves_old_concerns(self):
        old = {"A": diff.normalize_record(record(), "test")}
        self.assertEqual(diff.compare_records({}, old), [])
        failed = diff.normalize_record({"app": "A_REVIEW.html", "error": "timeout"}, "test")
        self.assertEqual(diff.compare_records({"A": failed}, old), [])
        self.assertEqual(diff.compare_records(old, {"A": failed}), [])

    def test_partial_current_blocks_comparison_and_removes_stale_report(self):
        self.snapshot("prior", [record()])
        current = self.snapshot("current", [{"app": "A_REVIEW.html", "error": "timeout"}], start="2026-10-14T03:00:00Z", end="2026-10-14T04:00:00Z")
        self.report.write_text("old resolutions")
        code, outputs = self.run_diff(current)
        self.assertEqual(code, 0)
        self.assertEqual(outputs, {"complete": "false", "publish": "false"})
        self.assertFalse(self.report.exists())
        self.assertIn("0 successful / 0 skipped / 1 failed", self.status.read_text())
        self.assertIn("Comparison blocked", self.status.read_text())

    def test_partial_with_one_success_and_missing_pending_page_is_blocked(self):
        current = self.snapshot("current", [record()], pending=("B_REVIEW.html",), end=None)
        self.assertEqual(self.run_diff(current)[1]["complete"], "false")
        self.assertIn("pending 1", self.status.read_text())

    def test_manifest_cannot_claim_complete_with_skip_or_wrong_counts(self):
        current = self.snapshot("current", [{"app": "A_REVIEW.html", "findings": None}])
        path = current / diff.MANIFEST
        for key, value in [("complete", True), ("total", 99), ("ok", 1)]:
            original = json.loads(path.read_text())
            self.write(current, {**original, key: value}, diff.MANIFEST)
            self.assertEqual(self.run_diff(current)[0], 2)
            self.write(current, original, diff.MANIFEST)

    def test_manifest_cannot_omit_or_misclassify_record(self):
        current = self.snapshot("current", [record()])
        self.write(current, record("B_REVIEW.html"), "B_REVIEW.json")
        self.assertEqual(self.run_diff(current)[0], 2)
        self.assertIn("manifest scope disagrees", self.status.read_text())

    def test_prior_selection_skips_incomplete_and_future_uses_timestamps(self):
        prior = self.snapshot("z-older-name", [record()])
        current = self.snapshot("current", [record(concerns=("new",))], start="2026-10-14T05:00:00Z", end="2026-10-14T06:00:00Z")
        self.snapshot("a-newer-but-partial", [{"app": "A_REVIEW.html", "error": "timeout"}], start="2026-10-14T03:00:00Z", end="2026-10-14T04:00:00Z")
        self.snapshot("future", [record()], start="2026-10-15T03:00:00Z", end="2026-10-15T04:00:00Z")
        self.assertEqual(diff.find_prior_dir(current), prior)
        self.assertEqual(self.run_diff(current)[1], {"complete": "true", "publish": "true"})
        self.assertIn("New concerns", self.report.read_text())
        self.assertIn("Resolved concerns (no longer emitted)", self.report.read_text())

    def test_newly_observed_page_labelled_not_editor_change(self):
        self.snapshot("prior", [record()])
        current = self.snapshot("current", [record(), record("B_REVIEW.html", ("new page concern",))], start="2026-10-14T03:00:00Z", end="2026-10-14T04:00:00Z")
        self.assertEqual(self.run_diff(current)[1]["publish"], "true")
        self.assertIn("Newly observed page", self.report.read_text())
        self.assertNotIn("Editor decision:", self.report.read_text())

    def test_first_complete_run_establishes_baseline_without_new_concerns_issue(self):
        current = self.snapshot("current", [record()])
        self.assertEqual(self.run_diff(current)[1], {"complete": "true", "publish": "false"})
        self.assertFalse(self.report.exists())

    def test_identical_complete_run_removes_stale_report(self):
        self.snapshot("prior", [record()])
        current = self.snapshot("current", [record()], start="2026-10-14T03:00:00Z", end="2026-10-14T04:00:00Z")
        self.report.write_text("stale")
        self.assertEqual(self.run_diff(current)[1]["publish"], "false")
        self.assertFalse(self.report.exists())

    def test_removed_page_is_unassessed_not_resolved(self):
        self.snapshot("prior", [record(), record("B_REVIEW.html")])
        current = self.snapshot("current", [record()], start="2026-10-14T03:00:00Z", end="2026-10-14T04:00:00Z")
        self.assertEqual(self.run_diff(current)[1]["publish"], "false")
        self.assertIn("NOT been classified as resolved", self.status.read_text())
        self.assertIn("B_REVIEW", self.status.read_text())

    def test_missing_manifest_subset_and_empty_harvest_are_unverified(self):
        legacy = self.findings / "legacy"
        self.write(legacy, record())
        self.assertEqual(self.run_diff(legacy)[1]["complete"], "false")
        subset = self.snapshot("subset", [record()], scope="subset")
        self.assertEqual(self.run_diff(subset)[1]["complete"], "false")
        empty = self.snapshot("empty", [])
        self.assertEqual(self.run_diff(empty)[1]["complete"], "false")

    def test_bad_data_returns_validation_error_not_comparison(self):
        current = self.snapshot("current", [record()])
        self.write(current, ["unrelated audit array"], "audit.json")
        self.report.write_text("stale")
        code, outputs = self.run_diff(current)
        self.assertEqual(code, 2)
        self.assertEqual(outputs["publish"], "false")
        self.assertFalse(self.report.exists())
        self.assertIn("audit.json[0]", self.status.read_text())


if __name__ == "__main__":
    unittest.main()
