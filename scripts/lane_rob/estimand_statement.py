# -*- coding: utf-8 -*-
"""GENERATOR COMPONENT: state what quantity is pooled, and whether the trials analysed it.

WHY THIS IS FIRST. It needs no retrieval, no new data and no judgement -- everything it says is
already in the object and in registry records we hold. It is the cheapest of the thirteen
features that vanish on regeneration, so it is the first one to make survive a rebuild.

WHAT IT SAYS, AND WHY IT MATTERS CLINICALLY RATHER THAN METHODOLOGICALLY. A risk ratio over
binary counts and a hazard ratio over time to event are DIFFERENT QUANTITIES. Where trials
analysed time to event with censoring and unequal follow-up and a page pools counts, the pooled
number is not the trials' own answer -- and a reader who does not know that will read it as if
it were. The dapivirine pool is exactly this case: 4,280 person-years, median 1.6 years, pooled
as a risk ratio.

⛔ DERIVE OR REFUSE. Where the trials' own analysis cannot be established from what we hold, the
component SAYS SO rather than assuming they match. "We could not determine what the trials
analysed" is a true sentence; "the estimand matches" asserted from nothing is not.

⚠️ AND IT IS RUN ON A SECOND TOPIC BEFORE IT IS BELIEVED. A component that works on the page it
was written against is a lookup table. The split classifier proved that tonight: perfect on its
own page, clinically backwards on a generated one.
"""
import io
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

# WARNING: THE SECOND VERSION OF THESE PATTERNS MATCHED NOTHING WHILE LOOKING CORRECT.
# Written through a shell heredoc, every intended word-boundary escape became a literal
# BACKSPACE character (0x08). The compiled pattern PRINTED as 'hazard|cox|rate ratio|HR|IRR'
# -- visually perfect -- and search('HR') returned False, because the real pattern was
# 'hazard|cox|rate ratio|HR'. An invisible control character produced a
# check that appears installed and is inert: the available-not-operative family, at character
# level. Caught only because the classifier suddenly called HR, RR and MD unrecognised.
TIME_TO_EVENT = re.compile(r"hazard|\bcox\b|rate ratio|incidence rate|\bHR\b|\bIRR\b", re.I)
BINARY = re.compile(r"risk ratio|relative risk|odds ratio|risk difference|\bRR\b|\bOR\b|\bRD\b", re.I)
CONTINUOUS = re.compile(r"mean difference|median difference|least square|\bLS mean\b|difference in percentage|adjusted difference|\bMD\b|\bSMD\b", re.I)


def _kind(measure):
    m = str(measure or "")
    if not m.strip():
        return None
    # order matters: "hazard" before the generic ratio patterns
    if TIME_TO_EVENT.search(m):
        return "time to event"
    if BINARY.search(m):
        return "binary counts"
    if CONTINUOUS.search(m):
        return "a continuous measure"
    return None


def _registry_params(canon):
    """What the registry says each contributing trial ANALYSED, via the sanctioned finder."""
    try:
        import data_finder as DF
    except Exception:
        return {}
    out = {}
    for oid, res in (((canon.get("results") or {}).get("by_outcome")) or {}).items():
        for r in (res.get("per_trial") or []):
            nct = r.get("nct")
            if not nct or nct in out:
                continue
            rec = DF.find(nct, "effect_estimate")
            if rec.get("state") == DF.OBTAINED:
                out[nct] = (rec["value"] or {}).get("param")
    return out


def render(canon):
    """The estimand statement, or a refusal naming what could not be established."""
    rows = []
    for oid, res in (((canon.get("results") or {}).get("by_outcome")) or {}).items():
        pooled = res.get("pooled") or {}
        measure = pooled.get("measure") or (
            (res.get("per_trial") or [{}])[0].get("measure") if res.get("per_trial") else None)
        if not measure:
            continue
        rows.append((oid, measure, _kind(measure), len(res.get("per_trial") or [])))
    if not rows:
        return ("<h2>What is being estimated</h2><p>This object records no pooled measure, so "
                "there is no estimand to state. That is a refusal, not an omission.</p>")

    params = _registry_params(canon)
    declared = sorted({str(v).upper() for v in params.values() if v})
    out = ["<h2>What is being estimated</h2>"]
    out.append("<div class=\"scroll\"><table><tr><th>Outcome</th><th>Pooled as</th>"
               "<th>Which is</th><th>Trials</th></tr>")
    for oid, measure, kind, k in rows:
        out.append("<tr><td>%s</td><td><b>%s</b></td><td>%s</td><td>%d</td></tr>"
                   % (re.sub(r"[<>]", "", str(oid))[:60], re.sub(r"[<>]", "", str(measure)),
                      kind or "an unrecognised measure", k))
    out.append("</table></div>")

    if not params:
        out.append(
            "<p><b>What the trials themselves analysed could not be established</b> from the "
            "records held, so this page does not claim that the pooled quantity matches the "
            "trials' own analysis. That is a gap in what we hold, not a statement that they "
            "agree.</p>")
        return "".join(out)

    ours = {k for _, _, k, _ in rows if k}
    theirs = {_kind(p) for p in declared if _kind(p)}
    out.append("<p>The registry records an analysis of <b>%s</b> for %d of the contributing "
               "trials.</p>" % (", ".join(sorted(theirs)) or "an unrecognised type", len(params)))
    if theirs and ours and not (theirs & ours):
        out.append(
            "<p><b>These are different quantities.</b> The pooled figure above is %s; the "
            "trials analysed %s, with censoring and unequal follow-up. A reader should not "
            "read the pooled number as the trials' own answer.</p>"
            % (" and ".join(sorted(ours)), " and ".join(sorted(theirs))))
    elif theirs & ours:
        out.append("<p>The pooled quantity and the trials' recorded analysis are of the same "
                   "kind.</p>")
    return "".join(out)


MARKER = "<h2>What is being estimated</h2>"


def inject(html, canon):
    if MARKER in html:
        return html
    return html + "\n<div class=\"card\">\n" + render(canon) + "\n</div>\n"


if __name__ == "__main__":
    import json
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    os.chdir(os.path.dirname(os.path.dirname(HERE)))
    for path in sys.argv[1:] or ["ssot/agyw-hiv-prep-review/agyw-hiv-prep-review.json"]:
        canon = json.load(io.open(path, encoding="utf-8"))
        t = re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", render(canon)))
        print("=" * 78)
        print(os.path.basename(path))
        print(t[:700])
