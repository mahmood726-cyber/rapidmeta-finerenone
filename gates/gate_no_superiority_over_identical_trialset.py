# -*- coding: utf-8 -*-
"""GATE: no page may claim superiority over a published synthesis on an IDENTICAL trial set.

An identical point estimate from an identical trial set is arithmetic, not corroboration -- and it is
certainly not superiority. Without IPD, longer follow-up, unpublished regulatory data, or new eligible
trials we are not a stronger evidence base and must not say we are. The defensible claim is
reconstruction + traceability + a living process; 'stronger/better/superior/beats the published meta' on
an identical trial set is refused. FIRES when a superiority phrase sits near a published-synthesis
reference whose trial set overlaps ours.
"""
from __future__ import annotations
import io, os, re, json, glob, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _harness as H  # noqa: E402

SUPERIOR = re.compile(r"\b(stronger|superior|better than|beats|outperforms|improves on|more (?:robust|reliable) than|"
                      r"stronger evidence base|higher quality than)\b", re.I)
PUBLISHED = re.compile(r"published (meta|synthes|pooled|review)|EMPEROR-Pooled|the literature pools", re.I)
IDENTICAL = re.compile(r"same (two )?trials|identical trial set|exactly these two|same-trials", re.I)


def check_text(text):
    """FIRES if a superiority phrase co-occurs (within ~200 chars) with a published-synthesis reference
    AND the trial-set overlap is asserted (or nearby)."""
    for m in SUPERIOR.finditer(text):
        window = text[max(0, m.start() - 200):m.end() + 200]
        if PUBLISHED.search(window) and (IDENTICAL.search(window) or PUBLISHED.search(window)):
            # require the identical/overlap signal somewhere in the window to avoid flagging a genuine
            # superiority claim backed by MORE trials
            if IDENTICAL.search(text[max(0, m.start() - 400):m.end() + 400]):
                return m.group(0)
    return None


def scan():
    hits = []
    objs = [p for p in glob.glob(os.path.join(H.repo_root(), "ssot", "*", "*.json"))
            if os.path.basename(p)[:-5] == os.path.basename(os.path.dirname(p))]
    for p in objs:
        try:
            o = json.load(io.open(p, encoding="utf-8"))
        except Exception:
            continue
        # scan the rendered free-text fields where such a claim would live
        text = json.dumps(o)
        hit = check_text(text)
        if hit:
            hits.append((os.path.basename(p)[:-5], "superiority phrase %r near a published synthesis on an identical trial set" % hit))
    return hits, len(objs)


def controls():
    pos = bool(check_text("This review provides STRONGER evidence than the published EMPEROR-Pooled meta-analysis of the same two trials."))
    neg1 = check_text("This review reconstructs the published EMPEROR-Pooled estimate from the same two trials with fully traceable inputs.") is None
    neg2 = check_text("This review is stronger because it adds four new trials the published meta did not include.") is None
    return pos, (neg1 and neg2)


def main(argv):
    gate = H.Gate("NO SUPERIORITY OVER AN IDENTICAL TRIAL SET",
                  "no page claims to beat a published synthesis on the same trials (arithmetic is not corroboration)")
    named = gate.expect_case("__synthetic_superiority_same_trials__", "a 'stronger than the published meta of the same trials' claim must fire")
    gate.requires_control()
    pos, neg = controls()
    if pos:
        gate.saw(named)
    gate.control(2, 0 if neg else 2, [] if neg else ["a reconstruction/more-trials claim was flagged"], accuses=True)
    if not pos:
        gate.broken("positive control did not fire")
    hits, npop = scan()
    for name, why in hits:
        gate.finding(name, why)
    gate.kinds({"objects scanned": npop, "superiority-on-identical-set claims": len(hits)})
    gate.coverage(npop, npop, "every object's text scanned for the claim")
    return gate.report(denominator="%d objects" % npop)


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
