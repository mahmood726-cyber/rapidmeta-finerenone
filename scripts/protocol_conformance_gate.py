"""The executed analysis must follow the protocol we ourselves stored, or record an amendment.

FULLY ORACLE-FREE. Both sides are in this repository: `protocols/*.md` declares the
analysis, `ssot/<topic>/<topic>.json` records what was executed. Nothing here consults a
publication, a registry, or a reviewer.

WHY THIS IS THE HIGHEST-VALUE GATE IN THE LANE. Prespecification is the claim this project
rests on. A silent estimand drift with a protocol ON FILE is worse than having no protocol
at all: it converts the central claim into the thing a reviewer can disprove fastest, using
only our own files.

WHAT COUNTS AS RESOLVING A DIFFERENCE
=====================================

A difference is not a defect. An UNDECLARED difference is. It resolves when the object
records an amendment that is DATED and NAMES the axis it changed. Prose that merely
mentions a method is not an amendment, and neither is a note saying a decision has been
referred to someone.

THREE STATES PER AXIS, AND ONLY ONE OF THEM FAILS
=================================================

    CONFORMS         the object records the choice the protocol declares
    DIFFERS          it records a DIFFERENT one -- the defect
    NOT_ESTABLISHED  the object records nothing on that axis

NOT_ESTABLISHED is counted and reported separately and is NEVER a pass. Most objects in
this corpus pool nothing and so record no interval method; folding those into DIFFERS would
report the gate's own blindness as a finding, at a volume that buries the real ones.

WHAT THIS GATE DOES NOT DO
==========================

It has NO OPINION ON WHICH CHOICE IS RIGHT. `advanced-stats` says DerSimonian-Laird is the
one to avoid below k=10, so the EXECUTED choice is frequently the better one. That is
exactly why the amendment matters: improving on your protocol is allowed, and doing it
silently is not.

It does not compare the protocol's PICO with the review's PICO. A protocol that covers a
different question entirely is a separate class and needs a different comparison.

A POOL THE REVIEW DECLINES TO REPORT IS NOT THE EXECUTED ANALYSIS. Reading a value out of a
block whose own name says it is not the answer is the defect class this lane exists for, so
subtrees naming a refusal, a decline, a sensitivity analysis or a superseded result are
skipped and the negative control pins that behaviour.

COVERAGE IS REPORTED, NOT ASSUMED. A topic whose protocol cannot be located, or whose
protocol declares no axis this gate parses, is NOT a pass -- it is counted and named.
"""
from __future__ import annotations

import io
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

BASELINE = ROOT / "scripts" / "baselines" / "protocol_conformance_baseline.json"
PROTOCOLS = ROOT / "protocols"

# --- what a protocol DECLARES, per axis ------------------------------------------------
# Narrow on purpose. A protocol silent on an axis must return None rather than a guess: a
# guessed declaration manufactures drift that is not there.
_DECLARED = {
    "estimator": [
        (r"dersimonian[-\s]?laird", "DERSIMONIAN_LAIRD"),
        (r"\bREML\b", "REML"),
        (r"paule[-\s]?mandel", "PAULE_MANDEL"),
    ],
    "scale": [
        (r"log[-\s]?HR scale|on the log[-\s]?hazard", "LOG_HR"),
        (r"log[-\s]?OR scale", "LOG_OR"),
        (r"log[-\s]?RR scale|risk[-\s]?ratio scale", "LOG_RR"),
    ],
    "ci_method": [
        (r"HKSJ|hartung[-\s]?knapp|knapp[-\s]?hartung", "HKSJ"),
        (r"\bWald\b|normal approximation", "WALD"),
    ],
}

_EXECUTED_ESTIMATOR = ("estimator", "estimator_used")
_EXECUTED_MEASURE = ("measure",)
_MEASURE_TO_SCALE = {"RR": "LOG_RR", "OR": "LOG_OR", "HR": "LOG_HR"}

_HK_BLOCK = re.compile(r"hartung|hksj", re.I)
_ALONGSIDE = re.compile(r"ALONGSIDE, not instead", re.I)

# See the module docstring: a declined pool is not the executed analysis.
_NOT_THE_EXECUTED_ANALYSIS = re.compile(
    r"declines_to_report|refus|declined|sensitivity|not_reported|superseded|withdrawn", re.I)

_AMENDMENT_KEY = re.compile(r"amendment|protocol_deviation|deviation_from_protocol", re.I)
_DATED = re.compile(r"\b20\d\d-\d\d-\d\d\b")


def _walk(node, path=""):
    if isinstance(node, dict):
        for k, v in node.items():
            yield path + "." + str(k), v
            yield from _walk(v, path + "." + str(k))
    elif isinstance(node, list):
        for i, v in enumerate(node):
            yield from _walk(v, "%s[%d]" % (path, i))


def _norm(name):
    return re.sub(r"[^a-z0-9]+", "", name.lower())


def locate_protocol(topic, protocol_files):
    """Match a topic directory to a protocol file, or return None.

    Conservative by design: a near-miss returns None and the topic is reported as NOT
    LOCATED rather than compared against somebody else's protocol -- which is the worse
    failure of the two, and a separate register class.
    """
    t = _norm(topic)
    best = None
    for p in protocol_files:
        stem = _norm(re.sub(r"_auto_protocol.*|_protocol.*", "", p.name))
        if stem and (stem == t or stem in t or t in stem):
            if best is None or len(stem) > len(_norm(best.name)):
                best = p
    return best


def declared_axes(text):
    out = {}
    for axis, rules in _DECLARED.items():
        out[axis] = None
        for pattern, token in rules:
            if re.search(pattern, text, re.I):
                out[axis] = token
                break
    return out


def executed_axes(obj):
    """What the OBJECT records as actually run."""
    est = measure = None
    hk_block = alongside = False
    for path, v in _walk(obj.get("results") or {}):
        if _NOT_THE_EXECUTED_ANALYSIS.search(path):
            continue
        leaf = path.rsplit(".", 1)[-1]
        if leaf in _EXECUTED_ESTIMATOR and isinstance(v, str) and est is None:
            m = re.search(r"REML|DerSimonian[-\s]?Laird|Paule[-\s]?Mandel", v, re.I)
            if m:
                est = {"reml": "REML",
                       "dersimonianlaird": "DERSIMONIAN_LAIRD",
                       "paulemandel": "PAULE_MANDEL"}.get(_norm(m.group(0)))
        if leaf in _EXECUTED_MEASURE and isinstance(v, str) and measure is None:
            if v.strip().upper() in _MEASURE_TO_SCALE:
                measure = v.strip().upper()
        if _HK_BLOCK.search(leaf):
            hk_block = True
        if isinstance(v, str) and _ALONGSIDE.search(v):
            alongside = True

    if hk_block and alongside:
        ci = "HKSJ_ALONGSIDE_UNADJUSTED_PRIMARY"
    elif hk_block:
        ci = "HKSJ"
    else:
        ci = None
    return {"estimator": est,
            "scale": _MEASURE_TO_SCALE.get(measure) if measure else None,
            "ci_method": ci}


def amendments(obj):
    """Dated amendment records naming an axis. Prose mentioning a method is not one."""
    out = []
    for path, v in _walk(obj):
        if _AMENDMENT_KEY.search(path.rsplit(".", 1)[-1]):
            blob = v if isinstance(v, str) else json.dumps(v, ensure_ascii=False)
            if _DATED.search(blob):
                out.append(path)
    return out


def compare(declared, executed):
    """-> (differences, unestablished)."""
    diffs, unest = [], []
    for axis in ("estimator", "scale", "ci_method"):
        d, e = declared.get(axis), executed.get(axis)
        if d is None:
            continue                       # the protocol is silent; nothing to conform to
        if e is None:
            unest.append({"axis": axis, "declared": d})
        elif axis == "ci_method" and d == "HKSJ" and e == "HKSJ_ALONGSIDE_UNADJUSTED_PRIMARY":
            diffs.append({"axis": axis, "declared": d, "executed": e,
                          "note": "the protocol makes HKSJ the PRIMARY interval; the object "
                                  "shows it alongside an unadjusted pool, so the primary is "
                                  "the unadjusted one"})
        elif e != d:
            diffs.append({"axis": axis, "declared": d, "executed": e})
    return diffs, unest


def collect(root: Path = ROOT):
    protocol_files = sorted(PROTOCOLS.glob("*.md")) if PROTOCOLS.is_dir() else []
    page_map = json.loads((root / "ssot" / "PAGE_MAP.json").read_text(encoding="utf-8"))
    topics = sorted({rel.split("/")[1] for rel in page_map.values() if "/" in rel})

    compared, not_located, no_object, findings, unestablished = [], [], [], [], []
    for topic in topics:
        obj_path = root / "ssot" / topic / ("%s.json" % topic)
        object_is_on_disk = obj_path.exists()
        if object_is_on_disk is False:
            no_object.append(topic)
            continue
        proto = locate_protocol(topic, protocol_files)
        if proto is None:
            not_located.append(topic)
            continue
        decl = declared_axes(proto.read_text(encoding="utf-8", errors="replace"))
        if not any(decl.values()):
            not_located.append(topic)
            continue
        obj = json.loads(obj_path.read_text(encoding="utf-8"))
        compared.append(topic)
        diffs, unest = compare(decl, executed_axes(obj))
        if unest:
            unestablished.append({"topic": topic, "axes": unest})
        if diffs:
            findings.append({"topic": topic, "protocol": proto.name, "declared": decl,
                             "differences": diffs,
                             "amendments_recorded": len(amendments(obj))})
    return {"topics": topics, "compared": compared, "protocol_not_located": not_located,
            "no_object": no_object, "findings": findings, "unestablished": unestablished}


def _run_controls(res):
    """Known answers, both directions.

    POSITIVE is synthetic and self-contained: an object declaring REML against a protocol
    declaring DerSimonian-Laird must be found, and on more than one axis when more than one
    differs. It is NOT pinned to a corpus topic, because a control anchored to live data
    retires itself the moment somebody fixes that topic.

    NEGATIVE, and it is the load-bearing half: an estimator that appears ONLY inside a
    block the review declines to report must NOT be read as the executed analysis. A page
    that shows what it refused, so the refusal costs something inspectable, is doing the
    right thing and must not be accused for it.
    """
    from instrument_controls import require_controls

    drifting = {"results": {"by_outcome": {"primary": {
        "estimator": "REML", "measure": "RR"}}}}
    declined_only = {"results": {"by_outcome": {"primary": {
        "estimator": "not pooled -- no shared estimand",
        "the_pools_this_refusal_declines_to_report": {
            "k3": {"estimator": "Paule-Mandel tau-squared, Knapp-Hartung t interval"}}}}}}
    proto = {"estimator": "DERSIMONIAN_LAIRD", "scale": "LOG_HR", "ci_method": None}

    pos_diffs, _ = compare(proto, executed_axes(drifting))
    neg_diffs, _ = compare(proto, executed_axes(declined_only))
    require_controls(
        "protocol_conformance_gate",
        positive=("an object recording REML/RR against a protocol declaring DL/log-HR",
                  len(pos_diffs) >= 2, True),
        negative=("an estimator found ONLY inside a declined-pool block",
                  any(d["axis"] == "estimator" for d in neg_diffs), True))


def main(argv):
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    res = collect()
    _run_controls(res)
    findings = res["findings"]

    print("topics named by PAGE_MAP                 : %d" % len(res["topics"]))
    if res["no_object"]:
        print("NOT ASSESSED, canonical object absent    : %d" % len(res["no_object"]))
    print("protocol located and comparable          : %d" % len(res["compared"]))
    print("NOT COMPARED (no protocol, or it declares no parsed axis): %d"
          % len(res["protocol_not_located"]))
    print("    these are NOT passes -- a topic this gate cannot read is unassessed")
    print("axes NOT ESTABLISHED (object records nothing): %d topic(s), counted not passed"
          % len(res["unestablished"]))
    print("topics whose executed analysis DIFFERS from their protocol: %d" % len(findings))
    for f in findings:
        print("\n  %s   (%s)" % (f["topic"], f["protocol"]))
        for d in f["differences"]:
            print("      %-10s protocol says %-22s object records %s"
                  % (d["axis"], d["declared"], d["executed"]))
            if d.get("note"):
                print("                 %s" % d["note"])
        print("      dated amendments naming an axis: %d" % f["amendments_recorded"])

    summary = {"compared": sorted(res["compared"]),
               "not_located": sorted(res["protocol_not_located"]),
               "finding_topics": sorted(f["topic"] for f in findings),
               "finding_total": len(findings)}

    if "--write-baseline" in argv:
        prior = (json.loads(BASELINE.read_text(encoding="utf-8"))["summary"]
                 if BASELINE.exists() else None)
        reason = argv[argv.index("--reason") + 1] if "--reason" in argv else None
        if prior and len(findings) > prior["finding_total"] and not reason:
            print("\nREFUSED: the baseline would RISE from %d to %d with no --reason. A "
                  "baseline that rises silently is indistinguishable from a defect landing."
                  % (prior["finding_total"], len(findings)))
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
    if len(findings) > base["finding_total"]:
        failures.append("topics drifting from their protocol rose from %d to %d"
                        % (base["finding_total"], len(findings)))
    new = set(summary["finding_topics"]) - set(base["finding_topics"])
    if new:
        failures.append("newly drifting: %s" % ", ".join(sorted(new)))
    if len(res["compared"]) < len(base["compared"]):
        failures.append("coverage fell: %d compared against a baseline of %d"
                        % (len(res["compared"]), len(base["compared"])))
    if failures:
        print("\nFAIL")
        for f in failures:
            print("  - %s" % f)
        return 1
    print("\nPASS (at or below baseline)")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
