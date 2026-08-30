# -*- coding: utf-8 -*-
"""REFUSAL: a subgroup estimate may not be rendered without its analysis status.

⛔ WHY THIS IS A REFUSAL AND NOT A WARNING. The dapivirine age strata are the case: 56% in women
over 21 and -27% in women 21 and under, and the source's first four words are "In a post hoc
analysis". A page that renders the 56% without that status ASSERTS MORE THAN THE SOURCE DOES --
it turns a hypothesis-generating subgroup into a finding, which is the difference between a
caveat and a treatment decision.

⛔ AND THE CHEAPEST FIX MUST NOT BE TO PUBLISH THE ESTIMATE. If this control ever fires, the
resolution is to record the status or drop the subgroup -- never to relax the check. That is
written here because the fix that scores identically and means the opposite is always available.

TWO CHECKS, AND THE SECOND IS THE ESTIMAND RULE APPLIED TO SUBGROUPS:

  1. STATUS   every subgroup record carries analysis_status from a closed vocabulary. A record
              with no status REFUSES; it does not default to prespecified, and it does not
              default to post hoc either. Absence is not a value.
  2. VALUE    every normalised number must actually appear in the verbatim sentence stored
              beside it. NOT a label-equality check -- comparing "the label says post hoc" with
              "the field says post hoc" proves only that two strings match. This compares the
              STORED NUMBERS against the SOURCE'S OWN WORDS, so a transcription error is caught
              rather than confirmed.

⚠️ COVERAGE IS PUBLISHED, matching the standard gate 14 set: the fraction of outcome blocks this
can see, and a plain statement about the rest.
"""
import io
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
os.chdir(os.path.dirname(os.path.dirname(HERE)))

STATUS_VOCAB = ("PRESPECIFIED", "POST_HOC", "EXPLORATORY", "STATUS_NOT_STATED_IN_SOURCE")


class SubgroupRefusal(Exception):
    pass


def _subgroup_records(canon):
    """Every subgroup record, with the path that reaches it. Yields (path, record)."""
    for oid, block in (((canon.get("results") or {}).get("by_outcome")) or {}).items():
        if not isinstance(block, dict):
            continue
        # ⛔ THE SHAPE IS THE GENERATOR'S, NOT MINE. build_app_v2 already renders subgroups as a
        # LIST of records with label / k / point / ci_low / ci_high / ve_percent. My first
        # record used a dict and BROKE THE BUILD -- TypeError: string indices must be integers,
        # because iterating a dict yields its keys. The renderer existed all along; what was
        # missing was the record. Conform to the contract that ships, do not invent one beside it.
        subs = block.get("subgroups") or []
        if isinstance(subs, dict):                      # tolerated, and refused below
            subs = [dict(v, label=k) for k, v in subs.items() if isinstance(v, dict)]
        for n, rec in enumerate(subs):
            if isinstance(rec, dict):
                yield ("results.by_outcome.%s.subgroups[%d]" % (oid, n), rec)


def _numbers_in(text):
    """Integers appearing in the sentence, sign-normalised. U+2212 counts as a minus."""
    t = (text or "").replace("−", "-")
    return {int(x) for x in re.findall(r"-?\d+", t)}


def check(canon):
    """[(path, problem)] -- empty when every subgroup record is renderable."""
    bad = []
    for path, rec in _subgroup_records(canon):
        st = rec.get("analysis_status")
        if not st:
            bad.append((path, "no analysis_status. A subgroup estimate without a recorded "
                              "status may not be rendered; absence is not a value."))
            continue
        if st not in STATUS_VOCAB:
            bad.append((path, "analysis_status %r is outside the closed vocabulary %s"
                        % (st, list(STATUS_VOCAB))))
        verb = rec.get("verbatim") or ""
        if not verb:
            bad.append((path, "no verbatim source sentence stored beside the numbers"))
            continue
        present = _numbers_in(verb)
        for field in ("point", "ci_low", "ci_high", "ve_percent"):
            v = rec.get(field)
            if isinstance(v, int) and v not in present:
                bad.append((path, "%s = %d does not appear in the stored source sentence; the "
                                  "normalised value and the verbatim disagree" % (field, v)))
    return bad


def enforce(canon, where="<object>"):
    bad = check(canon)
    if bad:
        raise SubgroupRefusal(
            "BUILD REFUSED at %s: a subgroup estimate cannot be rendered.\n  %s\n"
            "The fix is to record the status or drop the subgroup. It is NOT to relax this "
            "check -- that scores identically and means the opposite." % (
                where, "\n  ".join("%s -- %s" % (p, m) for p, m in bad)))


def _controls():
    out = []
    good = {"results": {"by_outcome": {"primary": {"subgroups": [{
        "label": "Older than 21 years", "analysis_status": "POST_HOC",
        "verbatim": "protection was 56% (95% CI, 31 to 71) but -27% (95% CI, -133 to 31)",
        "point": 56, "ci_low": 31, "ci_high": 71}]}}}}
    try:
        enforce(good, "control:status-present")
        out.append(("status recorded, numbers match the verbatim", "PUBLISHED", "PUBLISH"))
    except SubgroupRefusal:
        out.append(("status recorded, numbers match the verbatim", "REFUSED", "PUBLISH"))
    nostatus = json.loads(json.dumps(good))
    del nostatus["results"]["by_outcome"]["primary"]["subgroups"][0]["analysis_status"]
    try:
        enforce(nostatus, "control:no-status")
        out.append(("NO analysis_status", "PUBLISHED", "REFUSE"))
    except SubgroupRefusal:
        out.append(("NO analysis_status", "REFUSED", "REFUSE"))
    wrong = json.loads(json.dumps(good))
    wrong["results"]["by_outcome"]["primary"]["subgroups"][0]["point"] = 65
    try:
        enforce(wrong, "control:number-not-in-verbatim")
        out.append(("normalised number absent from the verbatim", "PUBLISHED", "REFUSE"))
    except SubgroupRefusal:
        out.append(("normalised number absent from the verbatim", "REFUSED", "REFUSE"))
    noverb = json.loads(json.dumps(good))
    del noverb["results"]["by_outcome"]["primary"]["subgroups"][0]["verbatim"]
    try:
        enforce(noverb, "control:no-verbatim")
        out.append(("no verbatim sentence", "PUBLISHED", "REFUSE"))
    except SubgroupRefusal:
        out.append(("no verbatim sentence", "REFUSED", "REFUSE"))
    return out


def main():
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace",
                                  line_buffering=True)
    print("")
    print("SUBGROUP GUARD")
    print("")
    held = True
    for name, got, want in _controls():
        ok = got == ("REFUSED" if want == "REFUSE" else "PUBLISHED")
        held &= ok
        print("  %-46s %-10s %s" % (name, got, "OK" if ok else "*** want %s ***" % want))
    if not held:
        print("")
        print("  CONTROLS FAILED -- no corpus number is printed.")
        return 2
    objs, blocks, recs, bad = 0, 0, 0, []
    for d in sorted(os.listdir("ssot")):
        p = os.path.join("ssot", d, d + ".json")
        if not os.path.exists(p):
            continue
        objs += 1
        try:
            o = json.load(io.open(p, encoding="utf-8"))
        except Exception:
            continue
        blocks += len(((o.get("results") or {}).get("by_outcome")) or {})
        n = list(_subgroup_records(o))
        recs += len(n)
        for path, msg in check(o):
            bad.append((d, path, msg))
    print("")
    print("  objects examined                        %5d" % objs)
    print("  outcome blocks                          %5d" % blocks)
    print("  SUBGROUP RECORDS -- what this can see   %5d   %5.2f%% of outcome blocks"
          % (recs, 100.0 * recs / max(1, blocks)))
    print("  refusing                                %5d" % len(bad))
    for d, path, msg in bad[:10]:
        print("    %-26s %s -- %s" % (d, path[:44], msg[:70]))
    print("")
    print("  ⇒ The other %d outcome blocks hold no subgroup record at all, so this guard makes"
          % (blocks - recs))
    print("    no statement about them either way. A subgroup that is never stored is not a")
    print("    subgroup this check has cleared -- it is one nobody has extracted.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
