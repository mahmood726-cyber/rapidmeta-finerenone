# -*- coding: utf-8 -*-
"""GATE: I2 at small k must carry its power caveat, never a bare homogeneity claim.

'I2 = 0% with only two trials is not proof of homogeneity; it means detectable between-study variation
was absent with very low power.' Rendering I2 0% as established homogeneity at k=2 is a power statement
dressed as a finding -- the same shape as 'absence of assessment is not a negative assessment'. At small
k the heterogeneity narrative must say so; a bare 'the trials are homogeneous / agree closely' fails.
"""
from __future__ import annotations
import io, os, re, json, glob, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _harness as H  # noqa: E402

SMALL_K = 3
CAVEAT = re.compile(r"power|few (studies|trials)|small k|k\s*=\s*[23]|not (evidence|proof) of homogeneity|"
                    r"detectab|cannot exclude|underpowered|too few", re.I)
HOMO = re.compile(r"homogen|agree closely|no heterogeneity|consistent across", re.I)


def check_outcome(het, het_status, k):
    """FIRES if I2 is present at small k, the narrative claims homogeneity, and no power caveat is given."""
    if not isinstance(het, dict) or het.get("i2") is None:
        return False
    if k is None or k > SMALL_K:
        return False
    text = (json.dumps(het) + " " + (het_status or ""))
    return bool(HOMO.search(text)) and not CAVEAT.search(text)


def scan():
    hits, examined = [], 0
    objs = [p for p in glob.glob(os.path.join(H.repo_root(), "ssot", "*", "*.json"))
            if os.path.basename(p)[:-5] == os.path.basename(os.path.dirname(p))]
    for p in objs:
        try:
            o = json.load(io.open(p, encoding="utf-8"))
        except Exception:
            continue
        for oid, oc in ((o.get("results") or {}).get("by_outcome") or {}).items():
            if not isinstance(oc, dict):
                continue
            het = oc.get("heterogeneity") or {}
            k = het.get("df") + 1 if isinstance(het.get("df"), int) else len(oc.get("per_trial") or []) or (oc.get("pooled") or {}).get("k")
            if het.get("i2") is not None and (k or 99) <= SMALL_K:
                examined += 1
                if check_outcome(het, oc.get("heterogeneity_status"), k):
                    hits.append(("%s/%s" % (os.path.basename(p)[:-5], oid), "I2=%s at k=%s, homogeneity claimed with no power caveat" % (het.get("i2"), k)))
    return hits, examined, len(objs)


def controls():
    pos = check_outcome({"i2": 0.0, "q": 0.28}, "the two trials agree closely; I-squared 0%", 2)          # must FIRE
    neg = check_outcome({"i2": 0.0, "q": 0.28}, "I-squared 0% but with only 2 trials this reflects low power, not proof of homogeneity", 2)  # silent
    neg2 = check_outcome({"i2": 80.0, "q": 40.0}, "high heterogeneity across 12 trials", 12)                # silent (large k)
    return pos, (neg is False and neg2 is False)


def main(argv):
    gate = H.Gate("I2 AT SMALL k NEEDS A POWER CAVEAT", "I2 at small k renders with its power caveat, not as bare homogeneity")
    named = gate.expect_case("__synthetic_i2_homogeneity_no_caveat__", "I2 0% at k=2 claimed homogeneous with no power caveat must fire")
    gate.requires_control()
    pos, neg = controls()
    if pos:
        gate.saw(named)
    gate.control(2, 0 if neg else 2, [] if neg else ["a caveated/large-k case was flagged"], accuses=True)
    if not pos:
        gate.broken("positive control did not fire")
    hits, examined, npop = scan()
    for name, why in hits:
        gate.finding(name, why)
    gate.kinds({"outcomes with I2 at small k": examined, "of those, homogeneity claimed with no caveat": len(hits)})
    gate.coverage(examined, examined, "only small-k outcomes carrying an I2 are in scope")
    return gate.report(denominator="%d small-k outcomes with an I2 (of %d objects)" % (examined, npop))


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
