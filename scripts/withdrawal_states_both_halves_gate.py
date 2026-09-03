"""A withdrawal is a claim about OUR DERIVATION, not about the world.

THE RULE, as a gate rather than an intention, because this lane issues withdrawals at
scale:

    EVERY WITHDRAWAL STATES TWO THINGS.
      1. WHAT IS INVALIDATED -- the derivation, the row, the pool. Always present.
      2. WHAT IS NOT, and specifically whether the CLINICAL CLAIM survives.
         Absent unless someone remembers.

    "The estimate is withdrawn" and "the effect is unsupported" are different sentences
    and usually only one of them is true. If the clinical claim was not separately
    refuted, the withdrawal has to say so in words.

WHY IT MATTERS MORE THAN IT SOUNDS. On cangrelor the stored 2x2 carried MORTALITY
numerators over COMPOSITE denominators on all three trials -- a real catch, and the
withdrawal was RIGHT. The page then said "the correction reverses the conclusion" and "the
page reported a significant benefit where the trials' own primary outcomes do not establish
one". But `OR 0.81 (0.71-0.91)` reproduces Steg et al. 2013, a PRESPECIFIED pooled analysis
of PATIENT-LEVEL data from all three CHAMPION trials, n=24,910. Our provenance had
collapsed; the clinical claim had not.

**A FALSE WARNING DISCREDITS THE TRUE ONES.**

WHAT THE MEASUREMENT SHOWS, AND IT CORRECTS THE BRIEF THIS GATE WAS WRITTEN FROM.
The cangrelor OBJECT already carries the balanced half: a `withdrawn_note` headed "WHAT IS
CONFIRMED, STATED AS PROMINENTLY AS WHAT IS WRONG", plus a findings block recording the
Steg reproduction, and the served page carries that reproduction too. What the page does
NOT carry is the "WHAT IS CONFIRMED" framing, and what it does carry -- early and
unqualified -- is "the correction reverses the conclusion".

So the defect there is a missing QUALIFICATION on the strongest sentence, not a missing
fact, and it lives in the projector's SELECTION rather than in the object. This gate checks
the OBJECT, which is what a generator can be held to. The projector half is recorded in the
register as still open rather than folded into a gate that cannot reach it.

WHAT THIS GATE DOES NOT DO. It does not judge whether the clinical claim actually survives
-- that is a reading of the evidence. It checks only that the withdrawal SAYS which of the
two it is, because a withdrawal that does not say is one the reader completes for
themselves, in the more alarming direction.
"""
from __future__ import annotations

import io
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

BASELINE = ROOT / "scripts" / "baselines" / "withdrawal_both_halves_baseline.json"

#: Keys carrying a withdrawal's reason -- the "what is invalidated" half. Measured over the
#: corpus: withdrawn_reason 121, withdrawn_note 23, withdrawn_because 7 = 151.
_WITHDRAWAL_REASON = re.compile(r"^withdrawn_reason$|^withdrawn_note$|^withdrawn_because$",
                                re.I)

#: Language stating what SURVIVES. Deliberately broad: the point is that the author said
#: SOMETHING about survival, not that they used a house phrase. A narrow pattern here would
#: report absence of a wording convention as absence of the thought.
_STATES_WHAT_SURVIVES = re.compile(
    r"what is confirmed|what is not invalidated|what (?:this|the withdrawal) does not|"
    r"remains? (?:correct|valid|true|unaffected)|is (?:independently|separately) correct|"
    r"the (?:clinical )?claim (?:survives|stands|is unaffected)|"
    r"not a statement about the (?:effect|world)|still (?:holds|stands|correct)|"
    r"unaffected by this withdrawal|reproduces? (?:the|a) published|"
    r"matches a published", re.I)

#: Language asserting the EFFECT is gone. Only harmful when unaccompanied by the above.
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

    Scoped to the parent deliberately: a survival statement about a DIFFERENT outcome,
    elsewhere in the same file, does not qualify THIS withdrawal. Widening it to the whole
    object would let one careful paragraph excuse every careless one in the file.
    """
    parent = path.rsplit(".", 1)[0]
    return " ".join(v for p, v in _walk(obj)
                    if p.startswith(parent) and isinstance(v, str))


def audit_object(obj):
    """-> withdrawals that say nothing about what survives."""
    out = []
    for path, v in _walk(obj):
        leaf = path.rsplit(".", 1)[-1]
        is_a_reason = bool(_WITHDRAWAL_REASON.match(leaf)) and isinstance(v, str)
        if is_a_reason:
            blob = _sibling_blob(obj, path)
            if not _STATES_WHAT_SURVIVES.search(blob):
                out.append({"at": path,
                            "asserts_the_effect_is_gone":
                                bool(_ASSERTS_THE_EFFECT_IS_GONE.search(blob)),
                            "reason_head": v[:120]})
    return out


def collect(root: Path = ROOT):
    page_map = json.loads((root / "ssot" / "PAGE_MAP.json").read_text(encoding="utf-8"))
    topics = sorted({rel.split("/")[1] for rel in page_map.values() if "/" in rel})
    read, no_object, findings, reasons = [], [], [], 0
    for topic in topics:
        obj_path = root / "ssot" / topic / ("%s.json" % topic)
        object_is_on_disk = obj_path.exists()
        if object_is_on_disk is False:
            no_object.append(topic)
            continue
        obj = json.loads(obj_path.read_text(encoding="utf-8"))
        read.append(topic)
        reasons += sum(1 for p, v in _walk(obj)
                       if _WITHDRAWAL_REASON.match(p.rsplit(".", 1)[-1])
                       and isinstance(v, str))
        bad = audit_object(obj)
        if bad:
            findings.append({"topic": topic, "count": len(bad), "items": bad[:4]})
    return {"topics_read": read, "no_object": no_object,
            "withdrawal_reasons_read": reasons, "findings": findings}


def _run_controls(res):
    """Known answers, both directions, and BOTH SYNTHETIC.

    Synthetic on purpose. The corpus population is what this gate measures, so a control
    pinned to a corpus topic retires itself the moment somebody fixes that topic -- and it
    would then either fail and look like a regression, or pass for the wrong reason.

    POSITIVE: a withdrawal whose surrounding block says nothing about survival is found.
    NEGATIVE: the SAME withdrawal, with one sentence added saying what is confirmed, is
    not. The pair differs by exactly the thing the gate is about, which is the only way to
    show it reads that and not something correlated with it.
    """
    from instrument_controls import require_controls
    base = {"withdrawn": True,
            "withdrawn_reason": "The stored 2x2 was corrupt and the pool is withdrawn."}
    planted = {"results": {"o": {"pooled": dict(base)}}}
    clean = {"results": {"o": {"pooled": dict(
        base, withdrawn_note="WHAT IS CONFIRMED: the headline reproduces a published "
                             "patient-level analysis and is unaffected by this withdrawal.")}}}
    require_controls(
        "withdrawal_states_both_halves_gate",
        positive=("a withdrawal saying nothing about what survives",
                  bool(audit_object(planted)), True),
        negative=("the same withdrawal with one sentence stating what is confirmed",
                  bool(audit_object(clean)), True))


def main(argv):
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    res = collect()
    _run_controls(res)
    findings = res["findings"]
    total = sum(f["count"] for f in findings)
    harmful = [(f["topic"], i["reason_head"]) for f in findings for i in f["items"]
               if i["asserts_the_effect_is_gone"]]

    print("topics read                                : %d" % len(res["topics_read"]))
    if res["no_object"]:
        print("NOT ASSESSED, canonical object absent      : %d" % len(res["no_object"]))
    print("withdrawal reasons read                    : %d" % res["withdrawal_reasons_read"])
    print("withdrawals that do NOT state what survives: %d on %d topic(s)"
          % (total, len(findings)))
    print("  of those, ones that ALSO assert the effect is gone: %d" % len(harmful))
    print("  that subset is the harmful shape: an unqualified claim about the WORLD made")
    print("  on the strength of a defect in OUR derivation")
    for t, head in harmful:
        print("      %-42s %s" % (t, head[:70]))

    # NAMED OBSERVATION, not a control: the case this class was written from. Reported so a
    # future reader can see whether the object that gets it right still gets it right,
    # without pinning a control to live data.
    cangrelor_flagged = any(f["topic"] == "cangrelor-pci-review" for f in findings)
    print("  cangrelor-pci-review flagged: %s  (its OBJECT states both halves; the "
          "projector is the open half)" % ("YES -- investigate" if cangrelor_flagged
                                           else "no, as expected"))

    summary = {"topics_read": len(res["topics_read"]),
               "withdrawal_reasons_read": res["withdrawal_reasons_read"],
               "finding_total": total,
               "harmful_total": len(harmful),
               "topics": sorted(f["topic"] for f in findings)}

    if "--write-baseline" in argv:
        prior = (json.loads(BASELINE.read_text(encoding="utf-8"))["summary"]
                 if BASELINE.exists() else None)
        reason = argv[argv.index("--reason") + 1] if "--reason" in argv else None
        if prior and total > prior["finding_total"] and not reason:
            print("\nREFUSED: the baseline would RISE from %d to %d with no --reason. A "
                  "baseline that rises silently is indistinguishable from a defect landing."
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
    if len(harmful) > base.get("harmful_total", 0):
        failures.append("withdrawals asserting the effect is gone rose from %d to %d"
                        % (base.get("harmful_total", 0), len(harmful)))
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
