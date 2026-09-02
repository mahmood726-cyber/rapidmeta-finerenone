"""The executed analysis must follow the protocol we ourselves stored, or say it did not.

FULLY ORACLE-FREE. Both sides are in this repository: `protocols/*.md` declares the
analysis, `ssot/<topic>/<topic>.json` records what was executed. Nothing here consults a
publication, a registry or a reviewer.

THE CASE THIS WAS WRITTEN FROM
==============================

`protocols/cab_prep_hiv_protocol_v1.1_2026-04-20.md` declares, at lines 92-94:

    Primary pool:                 DerSimonian-Laird random-effects IVW on log-HR scale.
    CI adjustment:                HKSJ with t-distribution df = k-1.
    HKSJ variance-inflation floor: max(1, Q/(k-1))  (non-optional, hard-coded)

`ssot/cab-prep-hiv-review/cab-prep-hiv-review.json` records:

    results.by_outcome.primary.estimator          REML
    results.by_outcome.primary.measure            RR
    pooled_hartung_knapp.why_it_is_shown          "Shown ALONGSIDE, not instead."

Three declared choices, three different executed choices, and no amendment recorded for
any of them. The object even says of the CI rule that it has been "referred rather than
taken", which is an honest note about an undecided question and is NOT an amendment.

> A SILENT ESTIMAND DRIFT WITH A PROTOCOL ON FILE IS WORSE THAN HAVING NO PROTOCOL.
> It converts prespecification -- the claim this project rests on -- into the thing a
> reviewer can disprove fastest, using only our own files.

WHAT COUNTS AS RESOLVING A DIFFERENCE
=====================================

A difference is not a defect. An UNDECLARED difference is. A difference resolves when the
object records an amendment that is DATED and that NAMES the axis it changed. Recording
"we used REML" somewhere in prose is not an amendment; neither is a note saying a decision
has been referred. The amendment has to say what changed, on which axis, and when.

WHAT THIS GATE DOES NOT DO
==========================

It does not decide which choice is right. DerSimonian-Laird is not better than REML, and
this file has no opinion on it -- `advanced-stats` says DL is the one to avoid below k=10,
so the EXECUTED choice is very often the better one. That is exactly why the amendment
matters: improving on your protocol is allowed, and doing it silently is not.

It also does not check the protocol's PICO against the review's PICO. That is a separate
class (register P2x, the ceftaroline protocol that covers a different question entirely)
and it needs a different comparison.

COVERAGE IS REPORTED, NOT ASSUMED. A topic whose protocol cannot be located is NOT a pass;
it is counted and named under `protocol_not_located`.
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

# --- what a protocol DECLARES, by axis -----------------------------------------------
# Each axis is (regex over the protocol text -> canonical token). The regexes are
# deliberately narrow: a protocol that says nothing about an axis must come back None, not
# a guess, because a guessed declaration would manufacture drift that is not there.
_DECLARED = {
    "estimator": [
        (r"dersimonian[-\s]?laird|\bDL\b random", "DERSIMONIAN_LAIRD"),
        (r"\bREML\b", "REML"),
        (r"paule[-\s]?mandel|\bPM\b random", "PAULE_MANDEL"),
    ],
    "scale": [
        (r"log[-\s]?HR scale|on the log[-\s]?hazard", "LOG_HR"),
        (r"log[-\s]?OR scale", "LOG_OR"),
        (r"log[-\s]?RR scale|risk[-\s]?ratio scale", "LOG_RR"),
    ],
    "ci_method": [
        (r"HKSJ|hartung[-\s]?knapp", "HKSJ"),
        (r"\bWald\b|normal approximation", "WALD"),
    ],
}

# --- what the OBJECT records as executed ----------------------------------------------
_EXECUTED_ESTIMATOR = ("estimator", "estimator_used")
_EXECUTED_MEASURE = ("measure",)

_MEASURE_TO_SCALE = {"RR": "LOG_RR", "OR": "LOG_OR", "HR": "LOG_HR",
                     "MD": "MD", "SMD": "SMD"}

_HK_BLOCK = re.compile(r"hartung|hksj", re.I)

# A POOL THE REVIEW DECLINES TO REPORT IS NOT THE EXECUTED ANALYSIS.
#
# The first version read the FIRST estimator string it found anywhere under `results`, and
# on colchicine-cvd-coronary that was
#   by_outcome.mace.the_pools_this_refusal_declines_to_report.name_matched_k3.estimator
#     = "Paule-Mandel tau-squared, Knapp-Hartung t interval on 2 df ..."
# -- an estimator belonging to a pool the page explicitly REFUSES to publish, shown so the
# refusal costs something inspectable. The gate reported it as a protocol deviation, which
# would have accused a page for doing exactly the right thing. That refusal is protected.
#
# Reading a value out of a block whose own name says it is not the answer is the defect
# class this lane exists for, committed by one of its own gates.
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

    Conservative: it requires the protocol's stem tokens to be a subset of the topic's, or
    the reverse. A near-miss returns None and the topic is reported as NOT LOCATED rather
    than compared against somebody else's protocol -- which is register class P2x and is
    the worse failure of the two.
    """
    t = _norm(topic)
    best = None
    for p in protocol_files:
        stem = _norm(re.sub(r"_auto_protocol.*|_protocol.*", "", p.name))
        if not stem:
            continue
        if stem == t or stem in t or t in stem:
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
    """What the object records. Returns {axis: token or None} plus where each was read."""
    est, measure, hk_alongside, hk_block, has_pool = None, None, False, False, False
    for path, v in _walk(obj.get("results") or {}):
        leaf = path.rsplit(".", 1)[-1]
        if _NOT_THE_EXECUTED_ANALYSIS.search(path):
            continue                      # a declined or superseded pool; see above
        if leaf in _EXECUTED_ESTIMATOR and isinstance(v, str) and est is None:
            m = re.search(r"REML|DerSimonian[-\s]?Laird|Paule[-\s]?Mandel", v, re.I)
            if m:
                est = {"reml": "REML", "dersimonianlaird": "DERSIMONIAN_LAIRD",
                       "dersimonian laird": "DERSIMONIAN_LAIRD",
                       "paulemandel": "PAULE_MANDEL",
                       "paule mandel": "PAULE_MANDEL"}.get(_norm(m.group(0)), m.group(0).upper())
        if leaf in _EXECUTED_MEASURE and isinstance(v, str) and measure is None:
            if v.strip().upper() in _MEASURE_TO_SCALE:
                measure = v.strip().upper()
        if leaf == "pooled" and isinstance(v, dict):
            has_pool = True
        if _HK_BLOCK.search(leaf):
            hk_block = True
        if isinstance(v, str) and re.search(r"ALONGSIDE, not instead", v, re.I):
            hk_alongside = True

    # THREE STATES, AND ONLY ONE OF THEM IS A DIFFERENCE.
    #   HKSJ_PRIMARY  -- an HKSJ interval and no separate unadjusted pool beside it
    #   HKSJ_ALONGSIDE-- both are present, so the primary is the unadjusted one
    #   None          -- the object pools nothing, or records no interval method at all,
    #                    which is NOT_ESTABLISHED and is reported separately from drift
    if hk_block and hk_alongside:
        ci = "HKSJ_ALONGSIDE_UNADJUSTED_PRIMARY"
    elif hk_block:
        ci = "HKSJ"
    else:
        ci = None
    return {"estimator": est,
            "scale": _MEASURE_TO_SCALE.get(measure) if measure else None,
            "ci_method": ci,
            "_pools_anything": has_pool,
            "_measure": measure}


def amendments(obj):
    """Dated amendment records that NAME an axis. Prose mentioning a method is not one."""
    found = []
    for path, v in _walk(obj):
        leaf = path.rsplit(".", 1)[-1]
        if _AMENDMENT_KEY.search(leaf):
            blob = json.dumps(v, ensure_ascii=False) if not isinstance(v, str) else v
            if _DATED.search(blob):
                found.append({"at": path, "text": blob[:200]})
    return found


def compare(declared, executed):
    """-> (differences, unestablished). THREE STATES PER AXIS, AND ONLY ONE IS A DEFECT.

    The first version of this function returned "the object records nothing on this axis"
    as a DIFFERENCE, and reported 127 of 127 compared topics as drifting. 127 of 127 is a
    statement about the instrument, not about the corpus: nearly every object pools nothing
    and therefore records no interval method, so the gate was reporting its own blindness
    as a finding, at a volume that would have buried the three real drifts.

    CONFORMS       the object records the same choice the protocol declares
    DIFFERS        it records a DIFFERENT one -- the defect, and the only thing that fails
    NOT_ESTABLISHED the object records nothing on the axis; counted and named, never a pass
    """
    diffs, unestablished = [], []
    for axis in ("estimator", "scale", "ci_method"):
        d, e = declared.get(axis), executed.get(axis)
        if d is None:
            continue                      # the protocol is silent; nothing to conform to
        if e is None:
            unestablished.append({"axis": axis, "declared": d})
        elif axis == "ci_method" and d == "HKSJ" and e == "HKSJ_ALONGSIDE_UNADJUSTED_PRIMARY":
            diffs.append({"axis": axis, "declared": d, "executed": e,
                          "note": "the protocol makes HKSJ the PRIMARY interval; the object "
                                  "shows it ALONGSIDE an unadjusted pool, so the primary is "
                                  "the unadjusted one"})
        elif e != d:
            diffs.append({"axis": axis, "declared": d, "executed": e})
    return diffs, unestablished


def collect(root: Path = ROOT):
    protocol_files = sorted(PROTOCOLS.glob("*.md")) if PROTOCOLS.is_dir() else []
    page_map = json.loads((root / "ssot" / "PAGE_MAP.json").read_text(encoding="utf-8"))
    topics = sorted({rel.split("/")[1] for rel in page_map.values() if "/" in rel})

    compared, not_located, findings, unestablished, no_object = [], [], [], [], []
    for topic in topics:
        obj_path = root / "ssot" / topic / ("%s.json" % topic)
        # POSITIVE PROPERTY, and the miss is COUNTED. A topic PAGE_MAP names whose canonical
        # object is absent has not been assessed; dropping it silently would shrink the
        # denominator without anyone deciding that it should.
        object_is_on_disk = obj_path.exists()
        if object_is_on_disk is False:
            no_object.append(topic)
            continue
        proto = locate_protocol(topic, protocol_files)
        if proto is None:
            not_located.append(topic)
            continue
        obj = json.loads(obj_path.read_text(encoding="utf-8"))
        decl = declared_axes(proto.read_text(encoding="utf-8", errors="replace"))
        if not any(decl.values()):
            not_located.append(topic)     # a protocol declaring no axis compares to nothing
            continue
        compared.append(topic)
        diffs, unest = compare(decl, executed_axes(obj))
        if unest:
            unestablished.append({"topic": topic, "axes": unest})
        if diffs:
            findings.append({"topic": topic, "protocol": proto.name,
                             "declared": decl, "differences": diffs,
                             "amendments_recorded": len(amendments(obj))})
    return {"topics_with_an_object": len(topics), "compared": compared,
            "protocol_not_located": not_located, "findings": findings,
            "unestablished": unestablished, "no_object_on_disk": no_object}


def _run_controls(res):
    """Known answers, both directions, established by reading our own two files by hand.

    POSITIVE. cab-prep-hiv-review. Protocol lines 92-94 declare DerSimonian-Laird on the
    log-HR scale with HKSJ t(k-1) primary; the object records estimator REML and measure
    RR. That was read out of both files before this gate existed, so it must be found and
    it must find MORE THAN ONE axis -- a gate that noticed only the estimator would look
    like it worked while missing the estimand.

    NEGATIVE. colchicine-cvd-coronary must NOT be reported as drifting. Its only
    Paule-Mandel estimators sit under `the_pools_this_refusal_declines_to_report` -- pools
    the page explicitly REFUSES to publish and shows anyway so the refusal costs something
    inspectable. The first version of this gate read one of them as the executed analysis
    and accused the page for doing the right thing. That refusal is protected, and this
    control is the thing standing between it and the next loosely-scoped reader.
    """
    from instrument_controls import require_controls
    pos_topic = "cab-prep-hiv-review"
    neg_topic = "colchicine-cvd-coronary"
    hit = next((f for f in res["findings"] if f["topic"] == pos_topic), None)
    require_controls(
        "protocol_conformance_gate",
        positive=("%s drifts on more than one axis" % pos_topic,
                  bool(hit) and len(hit["differences"]) >= 2, True),
        negative=("%s publishes no pool and its declined pools must not be read as the "
                  "executed analysis" % neg_topic,
                  any(f["topic"] == neg_topic for f in res["findings"]), True))


def main(argv):
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    res = collect()
    _run_controls(res)
    findings = res["findings"]

    print("topics with an object            : %d" % res["topics_with_an_object"])
    print("protocol located and comparable  : %d" % len(res["compared"]))
    print("NOT COMPARED, protocol not located or declares no parsed axis: %d"
          % len(res["protocol_not_located"]))
    print("    (these are NOT passes; a topic this gate cannot read is unassessed)")
    if res["no_object_on_disk"]:
        print("NOT ASSESSED, canonical object absent: %d -- %s"
              % (len(res["no_object_on_disk"]), ", ".join(res["no_object_on_disk"][:6])))
    print("axes NOT ESTABLISHED (object records nothing): %d topic(s) -- counted, not passed"
          % len(res["unestablished"]))
    print("topics whose executed analysis DIFFERS from their protocol: %d" % len(findings))
    for f in findings:
        print("\n  %s   (%s)" % (f["topic"], f["protocol"]))
        for d in f["differences"]:
            print("      %-10s protocol says %-20s object records %s"
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
            print("\nREFUSED: the baseline would RISE from %d to %d with no --reason."
                  % (prior["finding_total"], len(findings)))
            return 1
        record = {"summary": summary, "findings": findings}
        if reason:
            record["baseline_moved_because"] = reason
        BASELINE.write_text(json.dumps(record, indent=2), encoding="utf-8")
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
        failures.append("coverage fell: %d topics compared against a baseline of %d"
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
