"""How far does the risk-of-bias summary understate the stored judgements?

THE DEFECT. `_fit_to_budget` summarises the risk-of-bias section by regex-matching the
RENDERED PROSE of that section for the phrases "high risk of bias", "some concerns", "low
risk of bias" and "no information", then reporting the tally as the review's finding. It
never reads a stored judgement. Two consequences, both live:

  1. IT COUNTS PROSE THAT IS NOT A JUDGEMENT. The object's own methodological rule says
     "A rating of SOME CONCERNS with no explanation reads as a judgement against the
     trial" -- and the summariser counts that sentence as a verdict of SOME CONCERNS.

  2. IT MISSES THE STORED TOKEN ENTIRELY. Judgements are stored as `HIGH`, not as the
     phrase "high risk of bias", so a result at high risk contributes nothing to the tally
     unless some sentence happens to spell it out.

On sotagliflozin-hf the four per-result overall judgements are SOME_CONCERNS, HIGH, HIGH,
HIGH. The published page says "8 at some concerns, 7 at no information, 1 at low risk of
bias" and reports NO result at high risk of bias. A reader is told the opposite of what the
review found.

This is the string-match-instead-of-property failure class, and it is the one that matters
most, because the direction of the error is always the same: understatement. Prose about
method mentions "some concerns" and "no information" freely; nothing writes "high risk of
bias" in passing.

This script measures, per topic, the stored distribution against what the summariser would
report, and counts how many pages understate.
"""
import collections
import glob
import io
import json
import os
import re

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# The regex the summariser uses, reproduced exactly so this measures the real behaviour.
_VERDICT_RE = re.compile(
    r"\b(high risk of bias|some concerns|low risk of bias|no information)\b", re.I)


def stored_overalls(obj):
    """Every per-RESULT overall judgement the object holds."""
    rob = obj.get("risk_of_bias")
    if not isinstance(rob, dict):
        return []
    out = []
    for _oid, per in (rob.get("by_outcome") or {}).items():
        if not isinstance(per, dict):
            continue
        for _rid, rec in per.items():
            if not isinstance(rec, dict):
                continue
            v = rec.get("overall") or rec.get("rating")
            if v:
                out.append(str(v).upper().replace(" ", "_"))
    return out


def stored_domains(obj):
    """Every per-DOMAIN judgement the object holds."""
    rob = obj.get("risk_of_bias")
    if not isinstance(rob, dict):
        return []
    out = []
    for _oid, per in (rob.get("by_outcome") or {}).items():
        if not isinstance(per, dict):
            continue
        for _rid, rec in per.items():
            if not isinstance(rec, dict):
                continue
            for _dn, d in (rec.get("domains") or {}).items():
                if isinstance(d, dict) and d.get("judgement"):
                    out.append(str(d["judgement"]).upper().replace(" ", "_"))
    return out


def prose_of(obj):
    """Everything the risk-of-bias section would draw its prose from.

    Approximated by the whole risk_of_bias block serialised, which is what the section is
    composed from. The point is not to reproduce the projector byte for byte; it is to show
    that the phrases the summariser counts occur in method text, not only in judgements.
    """
    return json.dumps(obj.get("risk_of_bias") or {}, ensure_ascii=False)


def main():
    L = []

    def w(s):
        L.append(str(s))

    understating = []
    n_with_rob = 0
    for p in sorted(glob.glob(os.path.join(REPO, "ssot", "*", "*.json"))):
        slug = os.path.basename(os.path.dirname(p))
        if os.path.basename(p) != slug + ".json":
            continue
        try:
            with io.open(p, encoding="utf-8") as fh:
                obj = json.load(fh)
        except Exception:
            continue
        overalls = stored_overalls(obj)
        domains = stored_domains(obj)
        if not overalls and not domains:
            continue
        n_with_rob += 1
        stored_high = sum(1 for v in overalls if v == "HIGH")
        stored_high_dom = sum(1 for v in domains if v == "HIGH")
        counted = collections.Counter(m.lower() for m in _VERDICT_RE.findall(prose_of(obj)))
        reported_high = counted.get("high risk of bias", 0)
        if (stored_high or stored_high_dom) and not reported_high:
            understating.append((slug, stored_high, len(overalls),
                                 stored_high_dom, len(domains), dict(counted)))

    w("Topics carrying any risk-of-bias judgement: %d" % n_with_rob)
    w("")
    w("TOPICS WHERE A HIGH JUDGEMENT IS STORED AND THE PHRASE-COUNT REPORTS NONE: %d"
      % len(understating))
    w("")
    for slug, sh, no, shd, nd, counted in understating:
        w("  %s" % slug)
        w("     stored: %d of %d results HIGH; %d of %d domain judgements HIGH"
          % (sh, no, shd, nd))
        w("     phrase-count would report: %s"
          % (", ".join("%d at %s" % (n, k) for k, n in sorted(counted.items())) or "nothing"))
    w("")
    w("DIRECTION OF THE ERROR. Method prose says 'some concerns' and 'no information'")
    w("freely -- both appear in rules ABOUT judging, not only in judgements. Nothing writes")
    w("'high risk of bias' in passing. So a phrase count inflates the reassuring categories")
    w("and drops the alarming one, every time, on every page it touches.")

    out = os.path.join(REPO, "outputs", "rob_summary_defect_2026_08_24.txt")
    io.open(out, "w", encoding="utf-8").write("\n".join(L))
    print("\n".join(L))


main()
