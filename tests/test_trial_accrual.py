"""Fail-closed trial-status baseline tests, fully offline and deterministic."""
import importlib.util
import json
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch

SCRIPT = Path(__file__).resolve().parents[1] / "scripts/workflow/check_trial_status.py"
spec = importlib.util.spec_from_file_location("trial_accrual", SCRIPT)
monitor = importlib.util.module_from_spec(spec)
spec.loader.exec_module(monitor)


def record(status="RECRUITING", last="2026-10-15", result=None):
    return {"status": status, "lastUpdatePost": last, "resultsPost": result,
            "studyPost": "2025-01-01", "completion": None}


class TrialAccrualTests(unittest.TestCase):
    def test_nct_extraction_canonical_and_alias_parent(self):
        html = ('NCT01234567 NCT1234567 NCT012345678 "NCT87654321B" '
                'NCT98765432_TDF NCT1234567x and wordNCT99999999')
        self.assertEqual(set(monitor.NCT_RE.findall(html)),
                         {"NCT01234567", "NCT87654321", "NCT98765432"})

    def test_empty_snapshot_rejected(self):
        with self.assertRaises(ValueError): monitor.validate_snapshot({})

    def test_network_error_record_rejected(self):
        with self.assertRaisesRegex(ValueError, "failed"):
            monitor.validate_record("NCT01234567", {"error": "timeout"})

    def test_missing_status_rejected(self):
        with self.assertRaisesRegex(ValueError, "overallStatus"):
            monitor.validate_record("NCT01234567", record(status=None))

    def test_noncanonical_key_rejected(self):
        with self.assertRaisesRegex(ValueError, "noncanonical"):
            monitor.validate_record("NCT01234567a", record())

    def test_absent_date_is_legal(self):
        self.assertEqual(monitor.validate_record("NCT01234567", record()), record())

    def test_unexpected_schema_rejected(self):
        with self.assertRaisesRegex(ValueError, "unexpected"):
            monitor.validate_record("NCT01234567", dict(record(), unexpected="x"))

    def test_first_successful_poll_is_not_a_change(self):
        current = {"NCT01234567": record(), "NCT87654321": record()}
        self.assertEqual(monitor.diff_snapshots(None, current), [])

    def test_actual_date_change_is_reported(self):
        old = {"NCT01234567": record(last="2026-10-14")}
        new = {"NCT01234567": record(last="2026-10-15")}
        self.assertEqual(len(monitor.diff_snapshots(old, new)), 1)

    def test_identical_polls_no_alert(self):
        old = {"NCT01234567": record()}
        self.assertEqual(monitor.diff_snapshots(old, old), [])

    def test_newly_tracked_is_explicitly_different(self):
        old = {"NCT01234567": record()}
        new = dict(old, NCT87654321=record())
        changes = monitor.diff_snapshots(old, new)
        self.assertEqual(changes[0][0], "NCT87654321")
        self.assertIsNone(changes[0][1])
        rep = monitor.format_report(changes, {})
        self.assertIn("not evidence of registry status change", rep)
        self.assertIn("Newly tracked NCT IDs", rep)

    def test_missing_majority_of_previous_ids_fails_closed(self):
        before = {f"NCT{x:08d}": record() for x in range(100)}
        after = {f"NCT{x:08d}": record() for x in range(70)}
        with self.assertRaisesRegex(ValueError, "census collapsed"):
            monitor.diff_snapshots(before, after)

    def test_inconsistent_study_payload_aborts(self):
        fake = {"protocolSection": {"identificationModule": {"nctId": "NCT00000001"},
                                    "statusModule": {"overallStatus": "COMPLETED"}}}
        class Response:
            def __enter__(self): return self
            def __exit__(self, *args): return None
            def read(self): return json.dumps(fake).encode()
        with patch.object(monitor.urllib.request, "urlopen", return_value=Response()):
            with self.assertRaisesRegex(RuntimeError, "NCT ID missing"):
                monitor.fetch_status("NCT00000002")

    def test_api_status_decoded(self):
        fake = {"protocolSection": {"identificationModule": {"nctId": "NCT00000001"},
              "statusModule": {"overallStatus": "COMPLETED", "resultsFirstPostDateStruct": {"date":"2026-10-01"}}}}
        class Response:
            def __enter__(self): return self
            def __exit__(self, *args): return None
            def read(self): return json.dumps(fake).encode()
        with patch.object(monitor.urllib.request, "urlopen", return_value=Response()):
            self.assertEqual(monitor.fetch_status("NCT00000001")["resultsPost"], "2026-10-01")

    def test_first_full_run_persists_baseline_without_report(self):
        with TemporaryDirectory() as dir:
            root = Path(dir)
            by_nct = {"NCT01234567": ["a_REVIEW.html"]}
            with patch.object(monitor, "ROOT", root), patch.object(monitor, "extract_ncts", return_value=by_nct), patch.object(monitor, "fetch_status", return_value=record()):
                self.assertEqual(monitor.main(["--snapshot", "state/snap.json", "--report", "state/report.md"]), 0)
            self.assertTrue((root/"state/snap.json").exists())
            self.assertFalse((root/"state/report.md").exists())

    def test_failed_poll_preserves_previous_baseline(self):
        with TemporaryDirectory() as dir:
            root = Path(dir)
            state = root/"state/snap.json"
            state.parent.mkdir()
            original = json.dumps({"NCT01234567": record()})
            state.write_text(original)
            with patch.object(monitor, "ROOT", root), patch.object(monitor, "extract_ncts", return_value={"NCT01234567": ["a_REVIEW.html"]}), patch.object(monitor, "fetch_status", side_effect=RuntimeError("CT.gov timeout")):
                with self.assertRaisesRegex(RuntimeError,"CT.gov timeout"):
                    monitor.main(["--snapshot", "state/snap.json", "--report", "state/report.md"])
            self.assertEqual(state.read_text(), original)
            self.assertFalse((root/"state/report.md").exists())

    def test_corrupt_previous_snapshot_not_reset_to_blank(self):
        with TemporaryDirectory() as dir:
            root = Path(dir)
            state = root/"state/snap.json"
            state.parent.mkdir()
            state.write_text('not json')
            with patch.object(monitor,"ROOT",root), patch.object(monitor,"extract_ncts", return_value={"NCT01234567": []}):
                with self.assertRaises(json.JSONDecodeError):
                    monitor.main(["--snapshot", "state/snap.json", "--report", "state/report.md"])
            self.assertEqual(state.read_text(), 'not json')


if __name__ == "__main__":
    unittest.main()
