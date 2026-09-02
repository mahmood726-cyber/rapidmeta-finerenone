"""Re-run every page-standard property against the SERVED BYTES, and report the flips.

THE CLAIM THIS GATE EXISTS TO TEST
==================================

A page-standard property is rendered onto the page as a state and a reason. Before
this lane, five of those states were CONSTANTS -- `prop(HELD, "...")` with no branch
that could report anything else. A marker satisfiable by assertion is a password,
and a password tells you nothing about the thing it guards.

This gate does not read the marker. For every served page that carries the property
table it:

  1. reads the STATE THE PAGE SERVES, out of the page's own rendered bytes;
  2. recomputes the same property from the topic object the page was built from,
     using ssot/page_properties.py, which is a predicate and can refuse;
  3. reports every disagreement as a FLIP, with both reasons.

A flip is not automatically a page defect. It is a place where the page's marker and
the object disagree, which is precisely the situation the old emitter could not
produce and therefore could not report.

WHY IT READS RENDERED TEXT, NOT SOURCE
======================================

Both surfaces are compared after tag-stripping and whitespace collapse. A sentence a
reader sees as one string is routinely several strings in the file, split by an inline
<strong> or a newline inside a <p>. A source-level comparison misses those and scores
the page as agreeing.

WHAT IT DOES NOT DO
===================

It does not rebuild any page. Regeneration would erase retractions already applied to
the served corpus, so blast radius here is decided by RENDERING, never by re-publishing.

BASELINE AND RATCHET
====================

The measured flip count at the time this landed is stored in
scripts/baselines/property_recompute_baseline.json. The gate FAILS (exit 1) when the
count RISES above the baseline, or when a page not in the baseline acquires a flip.
It does not fail on the existing flips, because those pages are not being regenerated
in this lane and a gate that fails on a state nobody is allowed to change is a gate
that gets bypassed. Lowering the baseline requires the flips to actually be gone.
"""
from __future__ import annotations

import html as H
import io
import json
import os
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "ssot"))

import page_properties as PP  # noqa: E402  (path set above)

BASELINE = ROOT / "scripts" / "baselines" / "property_recompute_baseline.json"
PAGE_MAP = ROOT / "ssot" / "PAGE_MAP.json"

TAG = re.compile(r"<[^>]+>")
ROW = re.compile(
    r"<tr[^>]*>\s*<td>(P\d+_[a-z0-9_]+)</td>\s*<td><strong>([A-Z\- ]+)</strong></td>"
    r"\s*<td>(.*?)</td>\s*</tr>", re.S)


def rendered(source: str) -> str:
    source = re.sub(r"(?is)<(script|style)\b.*?</\1>", " ", source)
    return re.sub(r"\s+", " ", H.unescape(TAG.sub(" ", source))).strip()


def served_property_states(html: str):
    """What the page SERVES: {property: (state, reason)} from its own rendered bytes."""
    return {m[0]: (m[1].strip(), rendered(m[2])) for m in ROW.findall(html)}


def recompute(obj, expected_preconditions=()):
    """What the OBJECT supports, via the predicates. Never reads the marker."""
    out = {}
    for name, fn in PP.PROPERTIES.items():
        try:
            if name == "P4_preconditions":
                state, reason = fn(obj, expected_names=expected_preconditions)
            else:
                state, reason = fn(obj)
        except Exception as exc:                       # a predicate that crashes is a refusal
            state, reason = PP.REFUSING, "predicate raised %s: %s" % (type(exc).__name__, exc)
        out[name] = (state, reason)
    return out


def collect(root: Path = ROOT):
    page_map = json.loads(PAGE_MAP.read_text(encoding="utf-8"))
    pages = sorted(p for p in root.glob("*.html"))
    flips, checked, unmapped, no_table = [], 0, [], 0
    for page in pages:
        html = page.read_text(encoding="utf-8", errors="replace")
        served = served_property_states(html)
        # POSITIVE PROPERTIES ONLY, and each branch is taken on the thing that must be TRUE.
        # `if not X: continue` inside a corpus loop is how a page leaves a denominator
        # without anyone deciding that it should: the absence stands in for a property
        # nobody stated. The three states are kept apart and each is counted --
        # carries a table / resolves to an object / neither.
        carries_a_property_table = bool(served)
        rel = page_map.get(page.name)
        resolves_to_an_object = bool(rel) and (root / rel).exists()

        if carries_a_property_table and resolves_to_an_object:
            obj = json.loads((root / rel).read_text(encoding="utf-8"))
            checked += 1
            computed = recompute(obj)
            for name, (served_state, served_reason) in sorted(served.items()):
                comparable = name in computed
                if comparable and computed[name][0] != served_state:
                    new_state, new_reason = computed[name]
                    flips.append({
                        "page": page.name, "object": rel, "property": name,
                        "served_state": served_state, "recomputed_state": new_state,
                        "served_reason": served_reason[:300],
                        "recomputed_reason": new_reason[:300],
                    })
        elif carries_a_property_table:
            # NOT a page that passed. Named in the report so the coverage figure cannot be
            # mistaken for the population it claims to cover.
            unmapped.append(page.name)
        else:
            no_table += 1
    return {"served_reader_pages": len(pages), "pages_with_table": len(pages) - no_table,
            "pages_checked": checked, "unmapped_pages": unmapped, "flips": flips}


def _run_controls(flips):
    """Two known answers, established outside this gate.

    POSITIVE. AZILSARTAN_CLD_VS_OLM_HCTZ_REVIEW.html serves P1_executed_search as HELD
    while its own PubMed card renders `NOT EXECUTED FOR THIS TOPIC`. Both halves were read
    out of the served bytes by hand before this gate existed, so P1 must flip there.

    NEGATIVE. ABLATION_AF_HEART_FAILURE_REVIEW.html must NOT flip. It is the page whose
    DERIVED standard-error cell names its method as
    `se = (ln(upper) - ln(lower)) / (2 x 1.959964)` rather than through a `derived_by` key,
    and an earlier version of p5_extraction_table refused it for that -- one of three
    over-strict predicates in this lane, all failing in the direction of accusing a correct
    page. This control is the one that would have caught all three.
    """
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    from instrument_controls import require_controls
    flipped = {(f["page"], f["property"]) for f in flips}
    pos = ("AZILSARTAN_CLD_VS_OLM_HCTZ_REVIEW.html", "P1_executed_search")
    neg_page = "ABLATION_AF_HEART_FAILURE_REVIEW.html"
    require_controls(
        "property_recompute_gate",
        positive=("%s serves P1 HELD over a placeholder query" % pos[0], pos in flipped, True),
        negative=("%s names its derivation without a derived_by key" % neg_page,
                  any(p == neg_page for p, _ in flipped), True))


def main(argv):
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    write_baseline = "--write-baseline" in argv
    res = collect()
    flips = res["flips"]
    _run_controls(flips)
    by_prop = {}
    for f in flips:
        by_prop.setdefault(f["property"], []).append(f["page"])

    print("served reader pages      : %d" % res["served_reader_pages"])
    print("carrying property table  : %d" % res["pages_with_table"])
    print("checked (object resolved): %d" % res["pages_checked"])
    if res["unmapped_pages"]:
        # A page whose object cannot be resolved is NOT a page that passed. Named, so the
        # coverage figure cannot be mistaken for the population.
        print("NOT CHECKED, object unresolved: %d -- %s"
              % (len(res["unmapped_pages"]), ", ".join(res["unmapped_pages"][:8])))
    print("FLIPS                    : %d on %d page(s)"
          % (len(flips), len({f["page"] for f in flips})))
    for prop_name in sorted(by_prop):
        print("  %-28s %d" % (prop_name, len(by_prop[prop_name])))

    summary = {"pages_checked": res["pages_checked"],
               "unmapped_pages": sorted(res["unmapped_pages"]),
               "flip_total": len(flips),
               "flips_by_property": {k: sorted(v) for k, v in sorted(by_prop.items())}}

    if write_baseline:
        BASELINE.write_text(json.dumps({"summary": summary, "flips": flips}, indent=2),
                            encoding="utf-8")
        print("\nbaseline written -> %s" % BASELINE)
        return 0

    if not BASELINE.exists():
        print("\nNO BASELINE. Run with --write-baseline once, then commit it.")
        return 1

    base = json.loads(BASELINE.read_text(encoding="utf-8"))["summary"]
    failures = []
    if len(flips) > base["flip_total"]:
        failures.append("flip count rose from %d to %d" % (base["flip_total"], len(flips)))
    base_pairs = {(p, page) for p, pages in base["flips_by_property"].items() for page in pages}
    new_pairs = {(f["property"], f["page"]) for f in flips} - base_pairs
    if new_pairs:
        failures.append("new flips not in the baseline: %s"
                        % ", ".join("%s on %s" % (p, pg) for p, pg in sorted(new_pairs)[:8]))
    if res["pages_checked"] < base["pages_checked"]:
        failures.append("coverage fell: %d pages checked against a baseline of %d"
                        % (res["pages_checked"], base["pages_checked"]))

    if failures:
        print("\nFAIL")
        for f in failures:
            print("  - %s" % f)
        return 1
    print("\nPASS (at or below baseline of %d flips over %d pages)"
          % (base["flip_total"], base["pages_checked"]))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
