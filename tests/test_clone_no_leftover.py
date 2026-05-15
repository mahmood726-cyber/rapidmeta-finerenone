"""Contract test: a freshly-cloned audit-first dashboard contains ZERO
dupilumab/COPD base-template leftover tokens.

This is the regression gate for the bulk-clone neutralizer. It runs the real
pipeline (bulk_clone_audit_first.build_config -> clone_dashboard.clone) on a
real VIABLE topic into a temp file, then runs the fail-closed scanner and
asserts no violations. Red before the neutralizer fix; green after.
"""
import glob
import importlib.util
import json
import os
import sys

import pytest

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SCRIPTS = os.path.join(HERE, "scripts")
BASE = os.path.join(HERE, "DUPILUMAB_COPD_REVIEW.html")
TOPICS = os.path.join(HERE, "outputs", "new_topics")


def _load(name):
    spec = importlib.util.spec_from_file_location(name, os.path.join(SCRIPTS, name + ".py"))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _all_viable():
    out = []
    for p in sorted(glob.glob(os.path.join(TOPICS, "*.json"))):
        try:
            doc = json.loads(open(p, encoding="utf-8", errors="replace").read())
        except Exception:
            continue
        if doc.get("verdict") == "VIABLE":
            out.append(p)
    return out


def _pilot_topics(limit=5):
    """Adversarial pilot: apostrophe-condition topics + a COPD topic (soft-token
    guard) + first N VIABLE. These are the historically dangerous shapes."""
    allv = _all_viable()
    picked, seen = [], set()

    def add(pred, n):
        c = 0
        for p in allv:
            if p in seen:
                continue
            b = os.path.basename(p).upper()
            if pred(b):
                picked.append(p); seen.add(p); c += 1
                if c >= n:
                    break

    add(lambda b: "CROHNS" in b or "ALZHEIMER" in b, 3)   # apostrophe conditions
    add(lambda b: "COPD" in b, 1)                          # COPD soft-token guard
    add(lambda b: b.startswith("DUPILUMAB"), 1)            # dupilumab-drug soft-token guard
    add(lambda b: True, max(0, limit - len(picked)))       # fill with first VIABLE
    return picked or allv[:1]


def _viable_topics(limit=5):
    return _pilot_topics(limit)


@pytest.mark.skipif(not os.path.isfile(BASE), reason="base template missing")
@pytest.mark.skipif(not _viable_topics(1), reason="no VIABLE topics on disk")
@pytest.mark.parametrize("topic_json", _viable_topics(5))
def test_clone_has_zero_leftover(topic_json, tmp_path):
    bulk = _load("bulk_clone_audit_first")
    clone = _load("clone_dashboard")
    scanner = _load("scan_narrative_leftover")
    jscheck = _load("jscheck")

    doc = json.loads(open(topic_json, encoding="utf-8", errors="replace").read())
    cfg = bulk.build_config(doc)
    assert cfg, f"build_config returned None for {os.path.basename(topic_json)}"

    out = tmp_path / "clone.html"
    cfg["out"] = str(out)
    clone.clone(cfg, dry=False)
    assert out.is_file() and out.stat().st_size > 200_000, "clone did not produce a full dashboard"

    violations = scanner.scan(str(out), topic_json)
    if violations:
        summary = {}
        for tok, _off, _ctx in violations:
            summary[tok] = summary.get(tok, 0) + 1
        pytest.fail(
            f"{os.path.basename(topic_json)}: {len(violations)} leftover tokens "
            f"-> {summary}; first: {violations[0][2][:140]}"
        )

    # Gate 2: the clone must still PARSE as JS (apostrophe-injection guard).
    js_problems = jscheck.check(str(out))
    if js_problems:
        pytest.fail(
            f"{os.path.basename(topic_json)}: {len(js_problems)} broken script "
            f"block(s); first: block#{js_problems[0][0]} {js_problems[0][1]}"
        )


if __name__ == "__main__":
    sys.exit(pytest.main([__file__, "-q"]))
