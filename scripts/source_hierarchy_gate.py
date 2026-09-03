"""FIX ALPHA, enforced: the source hierarchy, and the two errors it dissolves.

    PRIMARY PUBLICATION -> SUPPLEMENT / SAP / PROTOCOL -> REGISTRY

The registry was privileged so hard that a fully published RCT could be dropped because
its registry entry had no results section. `ssot/provenance_tier.py` now ranks sources by
the QUESTION being asked -- the registry keeps precedence on pre-specification, where its
deposited-under-duty argument holds, and loses it on what the effect IS. This gate reads
the corpus for the two consequences of the old order.

  A1  REGISTRY SILENCE READ AS ABSENCE.  `hasResults=false` is a fact about
      ClinicalTrials.gov. A disposition that turns it into "there is nothing to extract"
      without naming a non-registry source it checked has decided a trial's fate on the
      registry alone.

  A2  AN EFFECT WITH NO ANALYSIS VARIANT.  Matching an endpoint TITLE does not establish
      that the same analysis was used. The ORION-11 record holds three values for one
      endpoint -- -53.5 observed-case, -47.8 after washout, -49.9 the published imputation.
      Pooling one trial's observed-case value with another's imputed value manufactured
      I2 = 74% on inclisiran; harmonised to one variant the same trials give tau2 = 0.
      Heterogeneity is a property of the extraction as much as of the trials, so every
      effect must carry the variant it is, and a pool may not mix variants.

WHAT THIS GATE DOES NOT DO
  It does not decide which variant is right, and it does not choose sources. It reports
  where the object cannot answer the question, which is the state the old ranking made
  invisible.

RATCHET. Both counts are baselined in scripts/baselines/source_hierarchy_baseline.json.
The gate fails when either RISES, or when a topic not in the baseline acquires one. It
does not fail on the existing population: no page is being rebuilt in this lane, and a
gate that fails on a state nobody is allowed to change is a gate that gets bypassed.
"""
from __future__ import annotations

import io
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "ssot"))
sys.path.insert(0, str(ROOT / "scripts"))

import provenance_tier as PT  # noqa: E402

BASELINE = ROOT / "scripts" / "baselines" / "source_hierarchy_baseline.json"

#: The variants a stored effect may declare. An effect that declares none is the finding.
KNOWN_VARIANTS = ("observed_case", "observed", "imputed", "multiple_imputation", "washout",
                  "adjusted", "unadjusted", "itt", "per_protocol", "mitt", "as_treated",
                  "last_observation_carried_forward", "mixed_model")

_VARIANT_KEYS = ("analysis_variant", "analysis_population", "estimand_variant",
                 "analysis_set", "population_analysed")


def topic_objects(root: Path = ROOT):
    """Every topic object, via PAGE_MAP so the population is the SERVED one."""
    page_map = json.loads((root / "ssot" / "PAGE_MAP.json").read_text(encoding="utf-8"))
    seen = {}
    for page, rel in sorted(page_map.items()):
        path = root / rel
        resolves = path.exists()
        if resolves and rel not in seen:
            seen[rel] = json.loads(path.read_text(encoding="utf-8"))
    return seen


def _walk_dicts(node):
    if isinstance(node, dict):
        yield node
        for v in node.values():
            yield from _walk_dicts(v)
    elif isinstance(node, list):
        for v in node:
            yield from _walk_dicts(v)


def find_registry_silence(obj):
    """Dispositions that convert `hasResults=false` into an absence of results."""
    out = []
    for block in _walk_dicts(obj):
        has_a_reason = isinstance(block.get("reason"), str)
        if has_a_reason:
            for problem in PT.registry_silence_problems(block):
                out.append({"reason": block["reason"][:200],
                            "nct": block.get("nct") or block.get("nct_id"),
                            "problem": problem})
    return out


def find_variantless_effects(obj):
    """Stored per-trial effects that carry a point and declare no analysis variant."""
    out = []
    for block in _walk_dicts(obj):
        carries_a_point = block.get("point") is not None
        if carries_a_point:
            declared = next((str(block[k]) for k in _VARIANT_KEYS if block.get(k)), None)
            if declared is None:
                out.append({"nct": block.get("nct") or block.get("nct_id"),
                            "outcome": str(block.get("outcome") or block.get("name") or "")[:80],
                            "point": block.get("point")})
    return out


def pools_mixing_variants(obj):
    """Outcomes whose contributing effects declare MORE THAN ONE analysis variant."""
    out = []
    for oc in (obj.get("outcomes") or []):
        variants = set()
        for block in _walk_dicts(oc):
            if block.get("point") is not None:
                declared = next((str(block[k]) for k in _VARIANT_KEYS if block.get(k)), None)
                if declared:
                    variants.add(declared.strip().lower())
        if len(variants) > 1:
            out.append({"outcome": str(oc.get("name") or oc.get("id") or "")[:80],
                        "variants": sorted(variants)})
    return out


def _declared_variant_count(res):
    """How many stored points DO declare a variant. The denominator for the mixing check."""
    return res.get("declared_variants", 0)


def collect(root: Path = ROOT):
    objs = topic_objects(root)
    silence, variantless, mixed = {}, {}, {}
    declared = 0
    for rel, obj in objs.items():
        topic = rel.split("/")[1] if "/" in rel else rel
        s = find_registry_silence(obj)
        v = find_variantless_effects(obj)
        m = pools_mixing_variants(obj)
        for block in _walk_dicts(obj):
            if block.get("point") is not None and any(block.get(k) for k in _VARIANT_KEYS):
                declared += 1
        if s:
            silence[topic] = s
        if v:
            variantless[topic] = len(v)
        if m:
            mixed[topic] = m
    return {"objects_read": len(objs), "registry_silence": silence,
            "variantless_effects": variantless, "pools_mixing_variants": mixed,
            "declared_variants": declared}


def _run_controls(res):
    """Known answers established outside this gate.

    POSITIVE. ssot/ablation-af-heart-failure carries four dispositions that say, in the
    object's own words, "CHECKED LIVE AGAINST THE REGISTRY: hasResults=false and no
    resultsSection. There is nothing to extract." That was read by hand from the object
    before this gate existed, so it must be found.

    NEGATIVE. The same file's `eligible_poolable_not_included_is_zero_because` states the
    identical registry fact and does NOT convert it into an absence claim about the trial;
    it records what four lookups returned. A gate that flags the careful phrasing along
    with the careless one would push authors toward saying less, which is the opposite of
    what the corpus wants. That distinction is tested by the plant in
    scripts/test_source_hierarchy_refuses.py.
    """
    from instrument_controls import require_controls
    pos = "ablation-af-heart-failure"
    require_controls(
        "source_hierarchy_gate",
        positive=("%s converts registry silence into 'nothing to extract'" % pos,
                  pos in res["registry_silence"], True),
        negative=("a topic with no stored points is not reported as variantless",
                  any(n == 0 for n in res["variantless_effects"].values()), True))


def main(argv):
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    res = collect()
    _run_controls(res)

    n_silence = sum(len(v) for v in res["registry_silence"].values())
    n_variantless = sum(res["variantless_effects"].values())
    n_mixed = sum(len(v) for v in res["pools_mixing_variants"].values())
    print("topic objects read                        : %d" % res["objects_read"])
    print("A1 registry silence read as absence       : %d disposition(s) on %d topic(s)"
          % (n_silence, len(res["registry_silence"])))
    print("A2 effects with no analysis variant       : %d on %d topic(s)"
          % (n_variantless, len(res["variantless_effects"])))
    # A ZERO FROM AN UNPROVEN POPULATION IS NOT_FOUND, NEVER ABSENT.
    # Mixing can only be seen among effects that DECLARE a variant. With 610 of them
    # declaring none, this count is bounded by how few can be read, not by how few mix --
    # and the inclisiran case (three values for one ORION-11 endpoint, mixed variants
    # manufacturing I2 = 74%) is exactly the shape that would be invisible here.
    declared_total = _declared_variant_count(res)
    if n_mixed == 0 and declared_total < n_variantless:
        print("A2 pools mixing analysis variants         : NOT_FOUND, not ABSENT -- only %d "
              "effect(s) declare a variant against %d that do not, so this check has almost "
              "nothing to compare" % (declared_total, n_variantless))
    else:
        print("A2 pools mixing analysis variants         : %d on %d topic(s)"
              % (n_mixed, len(res["pools_mixing_variants"])))

    summary = {"objects_read": res["objects_read"],
               "registry_silence_topics": sorted(res["registry_silence"]),
               "registry_silence_total": n_silence,
               "variantless_total": n_variantless,
               "mixed_variant_topics": sorted(res["pools_mixing_variants"])}

    if "--write-baseline" in argv:
        # A BASELINE MAY FALL FREELY AND MAY ONLY RISE WITH A RECORDED REASON.
        #
        # This gate predated the mechanism and wrote silently. On 2026-09-03 its A2 count
        # rose 610 -> 623 from trunk content; a --reason WAS supplied on the command line
        # and this block DROPPED IT ON THE FLOOR, leaving a baseline that could not say why
        # it moved. That is the rule this lane wrote hours earlier after doing the same
        # thing to a different baseline -- second instance, same mechanism -- so it stops
        # being a habit of the operator and becomes a property of the write.
        prior = (json.loads(BASELINE.read_text(encoding="utf-8"))["summary"]
                 if BASELINE.exists() else None)
        reason = argv[argv.index("--reason") + 1] if "--reason" in argv else None
        rose = prior is not None and (
            n_silence > prior.get("registry_silence_total", 0)
            or n_variantless > prior.get("variantless_total", 0))
        if rose and not reason:
            print("\nREFUSED: the baseline would RISE and no --reason was given. A baseline "
                  "that rises silently is indistinguishable from a defect landing.")
            return 1
        record = {"summary": summary, "detail": res}
        if reason:
            record["baseline_moved_because"] = reason
            record["moved_from"] = ({"registry_silence_total": prior.get("registry_silence_total"),
                                     "variantless_total": prior.get("variantless_total")}
                                    if prior else None)
        BASELINE.write_text(json.dumps(record, indent=2), encoding="utf-8")
        print("\nbaseline written -> %s" % BASELINE)
        if reason:
            print("reason recorded: %s" % reason[:110])
        return 0
    if not BASELINE.exists():
        print("\nNO BASELINE. Run with --write-baseline once, then commit it.")
        return 1

    base = json.loads(BASELINE.read_text(encoding="utf-8"))["summary"]
    failures = []
    if n_silence > base["registry_silence_total"]:
        failures.append("registry-silence dispositions rose from %d to %d"
                        % (base["registry_silence_total"], n_silence))
    if n_variantless > base["variantless_total"]:
        failures.append("variantless effects rose from %d to %d"
                        % (base["variantless_total"], n_variantless))
    new_mixed = set(summary["mixed_variant_topics"]) - set(base["mixed_variant_topics"])
    if new_mixed:
        failures.append("topics newly mixing analysis variants in one pool: %s"
                        % ", ".join(sorted(new_mixed)))
    if failures:
        print("\nFAIL")
        for f in failures:
            print("  - %s" % f)
        return 1
    print("\nPASS (at or below baseline)")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
