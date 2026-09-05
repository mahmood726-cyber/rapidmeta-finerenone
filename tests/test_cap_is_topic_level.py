"""Two-way proof that the per-topic candidate cap is a SETTING, not a positional
default that binds every topic to 20 -- which is why Galli 2025 (GLP-1, JACC,
k=21) was unreachable by arithmetic rather than by search.

We do not import add_topic_autodiscover: that module executes the whole AACT
discovery pipeline at import time. Instead we AST-extract the REAL bytes of
`_apply_cap` from the source and exec just that pure function, so the proof runs
against the shipped code path, not a paraphrase of it.

Proven here:
  A. a topic that MUST truncate still truncates and SAYS SO (records + prints);
  B. a topic UNDER the cap is untouched and records NOTHING;
  C. a cap silently EQUAL to the eligible count is a no-op (== no cap), so it is
     not manufactured into a phantom truncation;
  D. cap=None means no cap: the full eligible set is returned, nothing recorded;
  E. the binding itself: with cap=20 a 21-eligible set yields 20 (Galli
     unreachable); lifting the topic's cap yields all 21.
"""
import ast
import io
import os
from contextlib import redirect_stdout

SRC = os.path.join(os.path.dirname(__file__), "..", "scripts",
                   "add_topic_autodiscover.py")


def _load_apply_cap():
    """Return the live `_apply_cap` object, compiled from the real source file."""
    tree = ast.parse(open(SRC, encoding="utf-8").read(), filename=SRC)
    fn = next((n for n in tree.body
               if isinstance(n, ast.FunctionDef) and n.name == "_apply_cap"), None)
    assert fn is not None, "_apply_cap not found in source -- refactor drifted"
    mod = ast.Module(body=[fn], type_ignores=[])
    ns = {}
    exec(compile(mod, SRC, "exec"), ns)
    return ns["_apply_cap"]


APPLY_CAP = _load_apply_cap()


def _run(matches, cap):
    """Call the real _apply_cap with a fresh record; capture stdout so we can
    assert on both the return value AND whether it announced a truncation."""
    record = []
    buf = io.StringIO()
    with redirect_stdout(buf):
        kept = APPLY_CAP(list(matches), cap, record)
    return kept, record, buf.getvalue()


def test_A_must_truncate_still_truncates_and_says_so():
    elig = [f"NCT{i:08d}" for i in range(23)]  # 23 eligible, cap 20 -> bites
    kept, record, out = _run(elig, 20)
    assert kept == elig[:20]
    assert len(record) == 1, "a real truncation must leave exactly one record"
    r = record[0]
    assert r["eligible"] == 23 and r["kept"] == 20 and r["dropped"] == 3
    assert r["dropped_ncts"] == elig[20:], "the dropped tail must be named, not just counted"
    # eligible count AND kept count both surfaced -- the visible half of the fix.
    assert "23 eligible" in out and "kept 20" in out and "DROPPED 3" in out


def test_B_under_cap_is_untouched_and_records_nothing():
    elig = [f"NCT{i:08d}" for i in range(12)]  # 12 eligible, cap 20 -> no bite
    kept, record, out = _run(elig, 20)
    assert kept == elig, "a topic under the cap must be returned whole"
    assert record == [], "no truncation happened, so nothing may be recorded"
    assert out == "", "silence when nothing was dropped"


def test_C_cap_equal_to_eligible_is_a_noop_not_a_phantom_truncation():
    # The user's exact point: a cap silently equal to the eligible count is
    # indistinguishable from no cap and must NOT be logged as a truncation.
    elig = [f"NCT{i:08d}" for i in range(20)]
    kept, record, out = _run(elig, 20)
    assert kept == elig
    assert record == [], "cap == eligible dropped nothing; recording it would lie"
    assert out == ""


def test_D_none_means_no_cap():
    elig = [f"NCT{i:08d}" for i in range(63)]
    kept, record, out = _run(elig, None)
    assert kept == elig, "cap=None must write the full eligible set"
    assert record == [] and out == ""


def test_E_galli_k21_was_unreachable_at_20_and_is_reachable_when_lifted():
    # 21 eligible trials, exactly Galli's k.
    elig = [f"NCT{i:08d}" for i in range(21)]

    # Old behaviour, reproduced: the positional default of 20 caps a 21-eligible
    # set at 20 -- k=21 can never surface, no matter how large the eligible set.
    kept20, rec20, _ = _run(elig, 20)
    assert len(kept20) == 20, "at cap 20 a 21-eligible topic is bound below k=21"
    assert rec20[0]["dropped"] == 1, "and the one lost trial is recorded, not silent"

    # The fix: as a topic-level setting the cap can be raised (or set None), and
    # the same eligible set now surfaces all 21.
    kept_lift, rec_lift, _ = _run(elig, 25)
    assert kept_lift == elig and rec_lift == [], "lifting the cap reaches k=21 cleanly"
    kept_none, rec_none, _ = _run(elig, None)
    assert kept_none == elig and rec_none == []


if __name__ == "__main__":
    import sys
    fns = [v for k, v in sorted(globals().items()) if k.startswith("test_")]
    for fn in fns:
        fn()
        print(f"PASS  {fn.__name__}")
    print(f"\n{len(fns)}/{len(fns)} passed", file=sys.stderr)
