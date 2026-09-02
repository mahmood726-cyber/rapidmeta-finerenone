"""A REFUSAL IS A CLAIM AND ITS REASON IS PART OF THE CLAIM.

This gate audits the REASONS the corpus gives for declining to pool. It does not audit the
refusals. Those are separately protected, counted in PROTECTED-REFUSALS-2026-09-02.md, and
nothing here may turn one into a failure: declining funnel, GOSH, meta-regression or TSA at
small k is right, and so is refusing to pool across estimands.

THE CASE THIS WAS WRITTEN FROM
==============================

ssot/iv-iron-hf declines to pool a hierarchical win ratio. THE REFUSAL IS CORRECT, and so
is one of its four stated grounds. The other three are not. From the object:

    "The resulting ratio counts wins against losses, so values ABOVE one favour treatment
     -- the opposite of every other ratio in this object. It is reported by a single trial,
     at an interval level that is not the level everything else here uses, and it is not
     pooled with anything."

Three of those grounds do not survive contact with the arithmetic:

  COMPARES PAIRS.        The unit of analysis differs, which matters for interpretation and
                         not for poolability. A win ratio is a ratio measure with a
                         log-scale standard error like any other; log(WR) pools by
                         inverse-variance exactly as log(HR) does.
  OPPOSITE DIRECTION.    Direction is a SIGN CONVENTION. Invert the ratio, or negate the log,
                         and it points the same way as everything else. If a direction flip
                         made a measure unpoolable, no review could ever pool a
                         benefit-coded outcome with a harm-coded one, which they do routinely.
  A 99% INTERVAL.        A different confidence level changes the multiplier and nothing
                         else: se = (ln(upper) - ln(lower)) / (2 * 2.5758) at 99% rather
                         than 1.9600 at 95%. Recovering an SE from a 99% interval is the
                         same operation with a different constant.

The ONE ground that holds is in the same sentence and is doing none of the work: it is
reported by a SINGLE TRIAL. k=1 is a complete reason. A pool of one is the trial.

WHY THIS MATTERS MORE THAN A WORDING FIX. A reader who accepts "opposite direction means
unpoolable" carries it to the next review, where it will exclude a poolable outcome. And a
refusal defended by a false reason is indistinguishable, to an auditor, from a refusal with
no reason at all -- which is the state this corpus works hardest to avoid.

WHAT IT FLAGS, AND WHAT IT MUST NOT
===================================

FLAGGED   a non-pooling reason resting ONLY on grounds in INVALID_GROUNDS.
NOT FLAGGED   the same grounds when a VALID ground is present in the same reason. Naming a
          direction flip beside k=1 is useful context for a reader; it is only a defect
          when it is load-bearing. This distinction is the negative control, and without it
          the gate would push authors toward saying less.

The gate reports and ratchets; it does not edit any object. Fixing the wording is an edit
to a topic's stored reason, which changes the object without changing the page it was built
from, so it is listed in the register as outstanding rather than done silently here.
"""
from __future__ import annotations

import io
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

BASELINE = ROOT / "scripts" / "baselines" / "refusal_reason_baseline.json"

#: Grounds that do not, on their own, make an effect unpoolable.
INVALID_GROUNDS = {
    "unit_is_a_pair": (
        r"compares pairs|counts? wins? against losses|unit (?:of analysis )?is a pair|"
        r"pairs? of participants",
        "the unit of analysis differs; log(WR) pools by inverse variance like log(HR)"),
    "direction_is_opposite": (
        r"opposite of every other ratio|opposite direction|above one favours?|"
        r"direction is inverted",
        "direction is a sign convention -- invert the ratio or negate the log"),
    "interval_level_differs": (
        r"99%|interval level that is not|different confidence level|not the level "
        r"everything else",
        "a 99% interval yields an SE with the 2.5758 multiplier instead of 1.9600"),
}

#: Grounds that ARE complete reasons to decline. One of these present clears the reason.
VALID_GROUNDS = (
    r"\bk\s*=\s*1\b|single trial|reported by (?:a|one) single|only one trial|"
    r"one trial reports|no second trial",
    r"different estimand|not the same estimand|crosses an estimand|another estimand",
    r"no variance|no standard error|no interval is reported|carries no interval",
    r"different outcome|measures a different thing|not this review's outcome",
)

_REASON_KEYS = ("reason", "why_not_pooled", "not_pooled_because", "case_definition",
                "refusal_reason", "declined_because")
_NON_POOL = re.compile(r"not pooled|is not pooled|declines? to pool|do(?:es)? not pool|"
                       r"cannot be pooled|not poolable", re.I)


def _walk_dicts(node):
    if isinstance(node, dict):
        yield node
        for v in node.values():
            yield from _walk_dicts(v)
    elif isinstance(node, list):
        for v in node:
            yield from _walk_dicts(v)


def audit_reason(text):
    """-> (invalid_grounds_present, has_a_valid_ground). Neither implies the other."""
    invalid = [name for name, (pat, _why) in sorted(INVALID_GROUNDS.items())
               if re.search(pat, text, re.I)]
    valid = any(re.search(p, text, re.I) for p in VALID_GROUNDS)
    return invalid, valid


def collect(root: Path = ROOT):
    page_map = json.loads((root / "ssot" / "PAGE_MAP.json").read_text(encoding="utf-8"))
    findings, carried, reasons_read, objects_read = [], [], 0, 0
    for rel in sorted(set(page_map.values())):
        path = root / rel
        resolves = path.exists()
        if resolves:
            objects_read += 1
            obj = json.loads(path.read_text(encoding="utf-8"))
            topic = rel.split("/")[1] if "/" in rel else rel
            for block in _walk_dicts(obj):
                for key in _REASON_KEYS:
                    text = block.get(key)
                    is_a_refusal = isinstance(text, str) and _NON_POOL.search(text)
                    if is_a_refusal:
                        reasons_read += 1
                        invalid, valid = audit_reason(text)
                        if invalid and not valid:
                            findings.append({
                                "topic": topic, "key": key,
                                "invalid_grounds": invalid,
                                "reason": text[:260],
                                "why": [INVALID_GROUNDS[g][1] for g in invalid],
                            })
                        elif invalid and valid:
                            # REPORTED, NEVER FAILED. The refusal rests on a complete
                            # ground, so it is sound and is protected. But a reader who
                            # takes "opposite direction" or "a 99% interval" away as a rule
                            # will apply it to an outcome that IS poolable, so the sentence
                            # still costs something. Failing on it would push authors to
                            # give thinner reasons, which is worse.
                            carried.append({
                                "topic": topic, "key": key,
                                "invalid_grounds": invalid,
                                "reason": text[:260],
                                "why": [INVALID_GROUNDS[g][1] for g in invalid],
                            })
    return {"objects_read": objects_read, "refusal_reasons_read": reasons_read,
            "findings": findings, "carried": carried}


def _run_controls(res):
    """Known answers, both directions, established outside this gate.

    POSITIVE and NEGATIVE are the SAME SENTENCE under two edits, which is the only way to
    show the gate is reading the grounds rather than the topic. The real iv-iron sentence
    carries all three invalid grounds AND `reported by a single trial`, so it must NOT be
    flagged -- the false grounds are context beside a complete reason. Strip the valid
    ground and the identical sentence must be flagged.
    """
    from instrument_controls import require_controls
    real = ("The resulting ratio counts wins against losses, so values ABOVE one favour "
            "treatment -- the opposite of every other ratio in this object. It is reported "
            "by a single trial, at an interval level that is not the level everything else "
            "here uses, and it is not pooled with anything.")
    stripped = real.replace("It is reported by a single trial, ", "")
    inv_real, val_real = audit_reason(real)
    inv_strip, val_strip = audit_reason(stripped)
    require_controls(
        "refusal_reason_gate",
        positive=("the iv-iron sentence WITHOUT its k=1 ground is flagged",
                  bool(inv_strip) and not val_strip, True),
        negative=("the real iv-iron sentence, which names k=1, is flagged",
                  bool(inv_real) and not val_real, True))


def main(argv):
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    res = collect()
    _run_controls(res)
    findings = res["findings"]

    print("topic objects read            : %d" % res["objects_read"])
    print("non-pooling reasons read      : %d" % res["refusal_reasons_read"])
    print("reasons resting ONLY on grounds that do not hold: %d  (FAILS)" % len(findings))
    print("reasons that state such a ground BESIDE a valid one: %d  (reported, never fails)"
          % len(res["carried"]))
    for c in res["carried"][:6]:
        print("  %-30s carries %s" % (c["topic"], ", ".join(c["invalid_grounds"])))
        for w in c["why"]:
            print("      - %s" % w)
    for f in findings[:12]:
        print("  %-34s %s" % (f["topic"], ", ".join(f["invalid_grounds"])))
        print("      %s" % f["reason"][:150])
    if res["refusal_reasons_read"] == 0:
        print("\nNOT_FOUND, not ABSENT: no non-pooling reason matched the key list, so this "
              "gate read nothing and its zero is a statement about its reach.")

    summary = {"objects_read": res["objects_read"],
               "refusal_reasons_read": res["refusal_reasons_read"],
               "finding_total": len(findings),
               "topics": sorted({f["topic"] for f in findings})}
    if "--write-baseline" in argv:
        BASELINE.write_text(json.dumps({"summary": summary, "findings": findings}, indent=2),
                            encoding="utf-8")
        print("\nbaseline written -> %s" % BASELINE)
        return 0
    if not BASELINE.exists():
        print("\nNO BASELINE. Run with --write-baseline once, then commit it.")
        return 1
    base = json.loads(BASELINE.read_text(encoding="utf-8"))["summary"]
    failures = []
    if len(findings) > base["finding_total"]:
        failures.append("reasons resting only on invalid grounds rose from %d to %d"
                        % (base["finding_total"], len(findings)))
    new = set(summary["topics"]) - set(base["topics"])
    if new:
        failures.append("topics newly affected: %s" % ", ".join(sorted(new)))
    if res["refusal_reasons_read"] < base["refusal_reasons_read"]:
        failures.append("reach fell: %d reasons read against a baseline of %d"
                        % (res["refusal_reasons_read"], base["refusal_reasons_read"]))
    if failures:
        print("\nFAIL")
        for f in failures:
            print("  - %s" % f)
        return 1
    print("\nPASS (at or below baseline)")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
