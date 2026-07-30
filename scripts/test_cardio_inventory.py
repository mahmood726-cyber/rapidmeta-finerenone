#!/usr/bin/env python
"""Regression tests for the cardio inventory scanner.

The two cases at the top are the ones that actually shipped a wrong answer:
an NCT-shaped key regex silently returned 0 trials for quoted keys
(`"NCT01507831":`) and suffixed keys (`NCT01206062_SENIOR:`), which the
inventory then reported as "EMPTY / template" for apps that carry real data.
"""
from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from cardio_inventory import balanced_slice, depth1_keys  # noqa: E402

KEY_CASES = [
    # (name, source, expected depth-1 keys)
    ("quoted keys (regression)", '{"NCT01507831":{a:1},"NCT00239681":{b:2}}',
     ["NCT01507831", "NCT00239681"]),
    ("suffixed keys (regression)", "{NCT01206062_SENIOR:{a:1},NCT01206062_YOUNG:{b:2}}",
     ["NCT01206062_SENIOR", "NCT01206062_YOUNG"]),
    ("bare keys", "{NCT01860976:{a:1},NCT00534313:{b:2}}",
     ["NCT01860976", "NCT00534313"]),
    ("genuinely empty", "{}", []),
    ("nested objects are not keys", "{A:{name:'x',inner:{deep:{q:1}}},B:{n:2}}", ["A", "B"]),
    ("colon inside a string", '{A:{url:"https://x.org/y",note:"a: b"},B:{n:1}}', ["A", "B"]),
    ("brace inside a string", '{A:{s:"a{b}c"},B:{n:1}}', ["A", "B"]),
    ("escaped quote inside a string", '{A:{s:"he said \\"hi\\""},B:{n:1}}', ["A", "B"]),
    ("array values", '{A:{rob:["low","high"],o:[{x:1}]},B:{n:1}}', ["A", "B"]),
    ("mixed quoted and bare", '{"NCT1":{a:1},NCT2_SUB:{b:2},\'NCT3\':{c:3}}',
     ["NCT1", "NCT2_SUB", "NCT3"]),
]

SLICE_CASES = [
    ("balanced", "x={a:{b:1}} tail", "{a:{b:1}}"),
    ("brace in string not counted", 'x={a:"}{"} tail', '{a:"}{"}'),
    ("unbalanced returns empty", "x={a:{b:1}", ""),
]


def test_depth1_keys() -> int:
    bad = 0
    for name, src, exp in KEY_CASES:
        got = depth1_keys(src)
        ok = got == exp
        bad += 0 if ok else 1
        print(f"{'PASS' if ok else 'FAIL'}  depth1_keys: {name}")
        if not ok:
            print(f"        got={got!r}\n        expected={exp!r}")
    return bad


def test_balanced_slice() -> int:
    bad = 0
    for name, src, exp in SLICE_CASES:
        got = balanced_slice(src, 0)
        ok = got == exp
        bad += 0 if ok else 1
        print(f"{'PASS' if ok else 'FAIL'}  balanced_slice: {name}")
        if not ok:
            print(f"        got={got!r}\n        expected={exp!r}")
    return bad


# --------------------------------------------------------------------------
# Gate must be ABLE TO PASS as well as fail. A gate that only ever reports
# findings is verification theatre (rules/lessons.md).
# --------------------------------------------------------------------------
import tempfile  # noqa: E402

import cardio_integrity_gates as gates  # noqa: E402

CLEAN_APP = """<html><head><title>t</title></head><body><script>
var RapidMeta={realData:{NCT11111111:{name:"CleanTrial",pmid:"12345678",phase:"III",
year:2020,tE:50,tN:500,cE:60,cN:500,pubHR:null,allOutcomes:[]}}};
</script></body></html>"""

DIRTY_APP = CLEAN_APP.replace("tE:50,tN:500", "tE:600,tN:500")  # e > N


def test_gate_can_pass_and_fail() -> int:
    bad = 0
    for name, src, want_clean in (("clean ledger", CLEAN_APP, True),
                                  ("e>N ledger", DIRTY_APP, False)):
        with tempfile.NamedTemporaryFile("w", suffix="_REVIEW.html", delete=False,
                                         encoding="utf-8") as fh:
            fh.write(src)
            p = fh.name
        try:
            # --no-net: offline gates only, so the test never depends on the network.
            res = gates.run(p, use_net=False)
            c = res["counts"]
            blocking = c["CRITICAL"] + c["HIGH"]
            ok = (blocking == 0) if want_clean else (blocking > 0)
            bad += 0 if ok else 1
            print(f"{'PASS' if ok else 'FAIL'}  gate on {name}: k={res['k_trials']} "
                  f"blocking={blocking} (wanted {'0' if want_clean else '>0'})")
        finally:
            os.unlink(p)
    return bad


def main() -> int:
    bad = test_depth1_keys() + test_balanced_slice() + test_gate_can_pass_and_fail()
    total = len(KEY_CASES) + len(SLICE_CASES) + 2
    print(f"\n{total - bad}/{total} passed")
    return 1 if bad else 0


if __name__ == "__main__":
    raise SystemExit(main())
