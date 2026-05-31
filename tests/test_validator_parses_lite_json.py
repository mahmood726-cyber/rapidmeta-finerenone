"""Regression: the portfolio validator must parse BOTH realData formats.

Bug (fixed 2026-05-31): extract_real_data only understood the flagship
single-quoted JS-object format (`'NCT…': { tE: 313 }`) with an 8-12-space
closing indent. The lite *_AUTO_REVIEW apps emit realData as standard JSON
(`"NCT…": { "tE": 313 }`, 2-space indent), so the parser extracted ZERO
trials from all 794 of them -- they were all counted "non-poolable" despite
carrying real 2x2 event tables. The fix added a JSON-first path (brace-match +
json.loads) with the regex parser as fallback. Net effect: 584 apps moved out
of non-poolable, with the 18 flagship benchmark pools byte-for-byte unchanged.
"""
import importlib.util
from pathlib import Path

_spec = importlib.util.spec_from_file_location(
    "vv", Path(__file__).resolve().parent.parent / "validate_living_ma_portfolio.py")
vv = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(vv)


LITE_JSON = '''<script>
window.cfg = { realData: {
  "NCT01860976": {
    "name": "ASTRAEA",
    "tE": 54, "tN": 213, "cE": 22, "cN": 211,
    "estimandType": "OR", "publishedHR": null, "hrLCI": null, "hrUCI": null
  },
  "NCT01350804": {
    "name": "NURTURE 1",
    "tE": 30, "tN": 138, "cE": 5, "cN": 137,
    "estimandType": "OR", "publishedHR": null
  }
} };
</script>'''

FLAGSHIP_JS = """<script>
realData: {
        'NCT2807': {
            name: 'FIDELIO',
            tE: 100, tN: 1000, cE: 130, cN: 1000,
            publishedHR: 0.86, hrLCI: 0.79, hrUCI: 0.92
        },
},
</script>"""


def test_lite_json_format_is_parsed():
    trials = vv.extract_real_data(LITE_JSON)
    assert set(trials) == {"NCT01860976", "NCT01350804"}, trials
    assert trials["NCT01860976"]["tE"] == 54
    assert trials["NCT01860976"]["cN"] == 211
    # null publishedHR must not block the event-count path
    res = vv.pool_dl(trials)
    assert res and res.get("k") == 2, res


def test_flagship_single_quoted_still_parsed_via_fallback():
    # invalid JSON (single quotes, unquoted keys) -> must hit the regex parser
    assert vv._trials_from_json(FLAGSHIP_JS) is None
    trials = vv.extract_real_data(FLAGSHIP_JS)
    assert "NCT2807" in trials
    assert trials["NCT2807"]["publishedHR"] == 0.86
    assert trials["NCT2807"]["hrLCI"] == 0.79


def test_brace_extract_balances_nested_objects():
    blk = vv._brace_extract('x realData: { "a": {"b": 1}, "c": 2 } trailing', "realData:")
    assert blk == '{ "a": {"b": 1}, "c": 2 }'
