# -*- coding: utf-8 -*-
"""Protocol schema + validator, built so a protocol CANNOT repeat the failures already in this
corpus. A protocol is a JSON object; validate() refuses one that reproduces a known defect.

THE KNOWN FAILURES THIS GUARDS, each a real one in the repo:

  1. BACKDATED PROSPECTIVENESS. ARNI claims prospective registration in four places while 9 of
     its 9 screening decisions predate its earliest executed query. A protocol authored TODAY
     for a review already screened is a RETROSPECTIVE FORMALISATION. It must say so, carry its
     authoring date, and claim prospectiveness NOWHERE. `prospective: true` is allowed only with
     an explicit `prospective_evidence` (a registration id + date predating screening); without
     it, true is refused. Pre-registration protects the bar, not its height; backdating protects
     nothing.

  2. OUTCOME USED AS ELIGIBILITY. Screening on whether a trial reports the outcome is the
     Cochrane-forbidden mechanism; it wrongly excluded FAIR-HFpEF and moved a pooled estimate
     across significance. So eligibility has exactly population/intervention/comparator/design,
     and OUTCOMES ARE A REPORTING FIELD. A trial meeting P/I/C/D that does not report an outcome
     is eligible-and-unreported. validate() refuses an eligibility criterion that mentions an
     outcome, and refuses a protocol that puts outcomes inside eligibility.

  3. A CRITERION WITH NO CODE BEHIND IT. 167 of 1068 screening rows have no rule id, so their
     decisions are unfalsifiable. Every eligibility criterion here carries a rule_id.

  4. A CRITERION THAT CANNOT BE DIFFED / CANNOT TRACK ITS GUIDELINE. The `ef: le40` rung lived
     outside the repo, so the 2026 ESC change (HFrEF now LVEF <50%) could not be tracked. A
     criterion derived from a guideline records `guideline` + `guideline_version`.
"""
from __future__ import annotations
import io, json, re, sys

ELIG_FIELDS = ("population", "intervention", "comparator", "design")
_PROSPECTIVE_CLAIM = re.compile(
    r"prospective(ly)?\s+(register|registrat)|pre-?register|registered\s+before|"
    r"a\s+priori\s+protocol", re.I)
_OUTCOME_WORDS = re.compile(
    r"\boutcome|\bendpoint|\bmortality|\bMACE\b|\bhospitali[sz]ation|reported\b|primary\s+result",
    re.I)


def template(stem):
    """A blank retrospective protocol, correct by construction."""
    return {
        "protocol_id": "%s_retrospective_v1" % stem,
        "review_stem": stem,
        "authored_utc": None,                      # fill at author time
        "prospective": False,                      # authored after screening
        "provenance": ("RETROSPECTIVE FORMALISATION -- authored after this review's screening "
                       "already occurred. It records the criteria the review appears to have "
                       "applied; it is NOT a pre-registration and claims no prospectiveness."),
        "eligibility": {
            "population":   {"rule_id": "P1", "criterion": None, "threshold": None,
                             "guideline": None, "guideline_version": None},
            "intervention": {"rule_id": "I1", "criterion": None},
            "comparator":   {"rule_id": "C1", "criterion": None},
            "design":       {"rule_id": "D1", "criterion": None},
        },
        "outcomes_reporting": {
            "note": ("Outcomes are a REPORTING field, not an eligibility field. A trial meeting "
                     "P/I/C/D that does not report an outcome is eligible-and-unreported, never "
                     "ineligible."),
            "outcomes": [],
        },
    }


def validate(proto):
    """Return (ok, errors). Refuses a protocol that reproduces a known defect."""
    e = []
    if not isinstance(proto, dict):
        return False, ["not an object"]
    # 1. retrospective honesty
    if proto.get("authored_utc") in (None, ""):
        e.append("authored_utc missing -- a retrospective protocol must date its authoring")
    if proto.get("prospective") is True and not proto.get("prospective_evidence"):
        e.append("prospective:true without prospective_evidence (a registration id + date "
                 "predating screening) -- backdated prospectiveness is refused")
    # a false/absent-prospective protocol must not claim prospectiveness in prose anywhere
    if not proto.get("prospective"):
        blob = json.dumps({k: v for k, v in proto.items() if k != "provenance"})
        m = _PROSPECTIVE_CLAIM.search(blob)
        if m:
            e.append("claims prospectiveness (%r) while prospective is not true" % m.group(0)[:40])
    # 2. eligibility is exactly P/I/C/D; outcomes not among them
    elig = proto.get("eligibility") or {}
    for f in ELIG_FIELDS:
        if f not in elig:
            e.append("eligibility.%s missing (P/I/C/D are first-class)" % f)
    for extra in set(elig) - set(ELIG_FIELDS):
        e.append("eligibility has a non-P/I/C/D field %r -- outcomes/other are not eligibility" % extra)
    # 3 + 2b: each eligibility criterion has a rule id, a criterion, and does not screen on outcome
    for f in ELIG_FIELDS:
        c = elig.get(f) or {}
        if not c.get("rule_id"):
            e.append("eligibility.%s has no rule_id -- an unfalsifiable criterion" % f)
        if not c.get("criterion"):
            e.append("eligibility.%s has no criterion text" % f)
        if c.get("criterion") and _OUTCOME_WORDS.search(str(c["criterion"])):
            e.append("eligibility.%s screens on an OUTCOME (%r) -- forbidden; outcomes are a "
                     "reporting field" % (f, _OUTCOME_WORDS.search(str(c['criterion'])).group(0)))
    # 4. guideline-derived criteria carry the version
    for f in ELIG_FIELDS:
        c = elig.get(f) or {}
        if c.get("guideline") and not c.get("guideline_version"):
            e.append("eligibility.%s cites guideline %r without a version -- cannot track a "
                     "guideline change" % (f, c["guideline"]))
    # outcomes must live only in outcomes_reporting
    if "outcomes" in proto:
        e.append("top-level 'outcomes' -- outcomes belong under outcomes_reporting")
    return (not e), e


def _selftest():
    out, ok = [], True

    def check(name, cond):
        nonlocal ok
        ok &= bool(cond); out.append((name, "OK" if cond else "*** FAIL ***"))

    good = template("demo")
    good["authored_utc"] = "2026-09-06T09:00:00+00:00"
    for f, txt in (("population", "Adults with HFrEF, LVEF <50%"),
                   ("intervention", "an SGLT2 inhibitor"),
                   ("comparator", "placebo"), ("design", "randomised controlled trial")):
        good["eligibility"][f]["criterion"] = txt
    good["eligibility"]["population"]["guideline"] = "ESC HF"
    good["eligibility"]["population"]["guideline_version"] = "2026"
    okg, eg = validate(good)
    check("a correct retrospective protocol validates", okg and not eg)

    # each known failure must be REFUSED (prove the validator can fail)
    b1 = json.loads(json.dumps(good)); b1["authored_utc"] = None
    check("missing authoring date refused", not validate(b1)[0])
    b2 = json.loads(json.dumps(good)); b2["prospective"] = True
    check("prospective:true without evidence refused", not validate(b2)[0])
    b3 = json.loads(json.dumps(good)); b3["provenance"] = good["provenance"]
    b3["eligibility"]["population"]["criterion"] = "adults, pre-registered before screening"
    check("prospectiveness prose while not prospective refused", not validate(b3)[0])
    b4 = json.loads(json.dumps(good)); b4["eligibility"]["comparator"]["criterion"] = "reports all-cause mortality"
    check("outcome used as eligibility refused", not validate(b4)[0])
    b5 = json.loads(json.dumps(good)); b5["eligibility"]["design"]["rule_id"] = None
    check("criterion with no rule_id refused", not validate(b5)[0])
    b6 = json.loads(json.dumps(good)); b6["eligibility"]["population"]["guideline_version"] = None
    check("guideline without version refused", not validate(b6)[0])
    b7 = json.loads(json.dumps(good)); b7["eligibility"]["outcomes"] = {"rule_id": "O1", "criterion": "x"}
    check("outcomes inside eligibility refused", not validate(b7)[0])
    return ok, out


if __name__ == "__main__":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    if "--selftest" in sys.argv:
        good, rows = _selftest()
        print("protocol_schema selftest")
        for n, v in rows:
            print("  %-56s %s" % (n, v))
        print("\n%s" % ("ALL PASS" if good else "FAILURES ABOVE"))
        raise SystemExit(0 if good else 1)
    print(json.dumps(template("example"), indent=1))
