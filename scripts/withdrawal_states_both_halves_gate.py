"""A withdrawal is a claim about OUR DERIVATION, not about the world.

THE RULE, and it is now a template rather than an intention:

    EVERY WITHDRAWAL STATES TWO THINGS.
      1. WHAT IS INVALIDATED -- the derivation, the row, the pool. Always present today.
      2. WHAT IS NOT         -- and specifically whether the CLINICAL CLAIM survives.
         Absent unless someone remembers.

    If the clinical claim was not separately refuted, the withdrawal must say so in
    words. "The estimate is withdrawn" and "the effect is unsupported" are different
    sentences and only one of them is usually true.

WHY IT MATTERS MORE THAN IT SOUNDS. On cangrelor the stored 2x2 carried MORTALITY
numerators over COMPOSITE denominators on all three trials -- a genuine, important catch,
and the withdrawal was RIGHT. The page then said "the correction reverses the conclusion"
and "the page reported a significant benefit where the trials' own primary outcomes do not
establish one". But `OR 0.81 (0.71-0.91)` reproduces Steg et al. 2013, a PRESPECIFIED
pooled analysis of PATIENT-LEVEL data from all three CHAMPION trials, n=24,910. Our
provenance had collapsed; the clinical claim had not.

A FALSE WARNING DISCREDITS THE TRUE ONES, and this lane is about to issue many.

WHAT THE MEASUREMENT FOUND, AND IT CORRECTS THE BRIEF THIS GATE WAS WRITTEN FROM.
The cangrelor OBJECT already carries the balanced half: a `withdrawn_note` headed "WHAT IS
CONFIRMED, STATED AS PROMINENTLY AS WHAT IS WRONG", and a findings block recording that
0.81 matches the published patient-level analysis. The served page carries the Steg
reproduction too. What the page does NOT carry is the "WHAT IS CONFIRMED" framing, and
what it does carry, unqualified and early, is "the correction reverses the conclusion".

So the defect is not a missing fact. It is a missing QUALIFICATION on the strongest
sentence, and that lives in the projector's selection rather than in the object. This gate
therefore checks the OBJECT -- which is what a generator can be held to -- and the register
records the projector half separately as still open.

WHAT THIS GATE DOES NOT DO. It does not judge whether the clinical claim actually
survives. That is a reading of the evidence. It checks only that the withdrawal SAYS which
of the two it is, because a withdrawal that does not say is one a reader will complete for
themselves, in the more alarming direction.
"""
from __future__ import annotations

import io
import json
import os
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

BASELINE = ROOT / "scripts" / "baselines" / "withdrawal_both_halves_baseline.json"

#: Keys that carry a withdrawal's reason -- the "what is invalidated" half.
_WITHDRAWAL_REASON = re.compile(r"^withdrawn_reason$|^withdrawn_note$|^withdrawn_because$",
                                re.I)
_WITHDRAWN_FLAG = re.compile(r"^withdrawn$", re.I)

#: Language that states what SURVIVES. Deliberately broad, because the point is that the
#: reviewer said SOMETHING about survival, not that they used a house phrase.
_STATES_WHAT_SURVIVES = re.compile(
    r"what is confirmed|what is not invalidated|what (?:this|the withdrawal) does not|"
    r"remains? (?:correct|valid|true|unaffected)|is (?:independently|separately) correct|"
    r"the (?:clinical )?claim (?:survives|stands|is unaffected)|"
    r"not a statement about the (?:effect|world)|"
    r"still (?:holds|stands|correct)|unaffected by this withdrawal|"
    r"reproduces? (?:the|a) published|matches a published", re.I)

#: Language that asserts the EFFECT is gone. Only a problem when unaccompanied.
_ASSERTS_THE_EFFECT_IS_GONE = re.compile(
    r"reverses the conclusion|no longer supports?|does not establish|"
    r"the benefit (?:disappears|is not)|unsupported", re.I)


def _walk(node, path=""):
    if isinstance(node, dict):
        for k, v in node.items():
            yield path + "." + str(k), v
            yield from _walk(v, path + "." + str(k))
    elif isinstance(node, list):
        for i, v in enumerate(node):
            yield from _walk(v, "%s[%d]" % (path, i))


def _sibling_blob(obj, path):
    """Every string under the withdrawal's PARENT, joined.

    Scoped to the parent rather than the whole object on purpose: a survival statement
    about a different outcome, elsewhere in the file, does not qualify THIS withdrawal.
    """
    parent = path.rsplit(".", 1)[0]
    parts = []
    for p, v in _walk(obj):
        if p.startswith(parent) and isinstance(v, str):
            parts.append(v)
    return " ".join(parts)


def audit_object(obj):
    """-> list of withdrawals that do not state what survives."""
    out = []
    for path, v in _walk(obj):
        leaf = path.rsplit(".", 1)[-1]
        is_a_withdrawal_reason = bool(_WITHDRAWAL_REASON.match(leaf)) and isinstance(v, str)
        if not is_a_withdrawal_reason:
            continue
        blob = _sibling_blob(obj, path)
        states_survival = bool(_STATES_WHAT_SURVIVES.search(blob))
        asserts_gone = bool(_ASSERTS_THE_EFFECT_IS_GONE.search(blob))
        if not states_survival:
            out.append({"at": path,
                        "asserts_the_effect_is_gone": asserts_gone,
                        "reason_head": v[:120]})
    return out


def collect(root: Path = ROOT):
    page_map = json.loads((root / "ssot" / "PAGE_MAP.json").read_text(encoding="utf-8"))
    topics = sorted({rel.split("/")[1] for rel in page_map.values() if "/" in rel})
    read, no_object, findings, withdrawals = [], [], [], 0
    for topic in topics:
        obj_path = root / "ssot" / topic / ("%s.json" % topic)
        object_is_on_disk = obj_path.exists()
        if object_is_on_disk is False:
            no_object.append(topic)
            continue
        obj = json.loads(obj_path.read_text(encoding="utf-8"))
        read.append(topic)
        withdrawals += sum(1 for p, v in _walk(obj)
                           if _WITHDRAWAL_REASON.match(p.rsplit(".", 1)[-1])
                           and isinstance(v, str))
        bad = audit_object(obj)
        if bad:
            findings.append({"topic": topic, "count": len(bad), "items": bad[:4]})
    return {"topics_read": read, "no_object": no_object,
            "withdrawal_reasons_read": withdrawals, "findings": findings}


def _run_controls(res):
    """Known answers read out of the objects by hand, before this gate existed.

    POSITIVE. A withdrawal whose surrounding block says nothing about survival must be
    found. Established synthetically below rather than by naming a topic, because the
    corpus population is what this gate is measuring and pinning a control to it would
    make the control retire itself the moment somebody fixed that topic.

    NEGATIVE. cangrelor-pci-review must NOT be flagged. Its withdrawal block carries
    "WHAT IS CONFIRMED, STATED AS PROMINENTLY AS WHAT IS WRONG" and records that the
    withdrawn 0.81 reproduces Steg et al.'s patient-level analysis. It is the case this
    gate was written from, and the OBJECT gets it right -- accusing it would be accusing
    the one page that already does the thing.
    """
    from instrument_controls import require_controls
    planted = {"results": {"o": {"pooled": {
        "withdrawn": True,
        "withdrawn_reason": "The stored 2x2 was corrupt and the pool is withdrawn.",
    }}}}
    clean = {"results": {"o": {"pooled": {
        "withdrawn": True,
        "withdrawn_reason": "The stored 2x2 was corrupt and the pool is withdrawn.",
        "withdrawn_note": "WHAT IS CONFIRMED: the headline reproduces a published "
                          "patient-level analysis and is unaffected by this withdrawal.",
    }}}}
    require_controls(
        "withdrawal_states_both_halves_gate",
        positive=("a withdrawal saying nothing about what survives", bool(audit_object(planted)), True),
        negative=("a withdrawal that states what is confirmed", bool(audit_object(clean)), True))


def main(argv):
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    res = collect()
    _run_controls(res)
    findings = res["findings"]
    total = sum(f["count"] for f in findings)
    loud = sum(1 for f in findings for i in f["items"] if i["asserts_the_effect_is_gone"])

    print("topics read                              : %d" % len(res["topics_read"]))
    if res["no_object"]:
        print("NOT ASSESSED, canonical object absent    : %d" % len(res["no_object"]))
    print("withdrawal reasons read                  : %d" % res["withdrawal_reasons_read"])
    print("withdrawals that do NOT state what survives: %d on %d topic(s)"
          % (total, len(findings)))
    print("  of those, ones that also assert the effect is gone: %d" % loud)
    print("  (that subset is the harmful shape: an unqualified claim about the WORLD made")
    print("   on the strength of a defect in OUR derivation)")
    for f in findings[:10]:
        print("    %-38s %d" % (f["topic"], f["count"]))

    summary = {"topics_read": len(res["topics_read"]),
               "withdrawal_reasons_read": res["withdrawal_reasons_read"],
               "finding_total": total,
               "topics": sorted(f["topic"] for f in findings)}
    if "--write-baseline" in argv:
        prior = (json.loads(BASELINE.read_text(encoding="utf-8"))["summary"]
                 if BASELINE.exists() else None)
        reason = argv[argv.index("--reason") + 1] if "--reason" in argv else None
        if prior and total > prior["finding_total"] and not reason:
            print("\nREFUSED: the baseline would RISE from %d to %d with no --reason."
                  % (prior["finding_total"], total))
            return 1
        rec = {"summary": summary, "findings": findings}
        if reason:
            rec["baseline_moved_because"] = reason
        BASELINE.write_text(json.dumps(rec, indent=2), encoding="utf-8")
        print("\nbaseline written -> %s" % BASELINE)
        return 0
    if not BASELINE.exists():
        print("\nNO BASELINE. Run with --write-baseline once, then commit it.")
        return 1
    base = json.loads(BASELINE.read_text(encoding="utf-8"))["summary"]
    failures = []
    if total > base["finding_total"]:
        failures.append("unqualified withdrawals rose from %d to %d"
                        % (base["finding_total"], total))
    new = set(summary["topics"]) - set(base["topics"])
    if new:
        failures.append("newly affected: %s" % ", ".join(sorted(new)))
    if summary["topics_read"] < base["topics_read"]:
        failures.append("coverage fell: %d topics read against a baseline of %d"
                        % (summary["topics_read"], base["topics_read"]))
    if failures:
        print("\nFAIL")
        for f in failures:
            print("  - %s" % f)
        return 1
    print("\nPASS (at or below baseline)")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
