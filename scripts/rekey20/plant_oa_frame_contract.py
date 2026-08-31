# -*- coding: utf-8 -*-
"""PLANTS FOR THE OPEN-ACCESS FRAME CONTRACT. Every refusal separately, each with a clean
sibling that must pass through the SAME code path.

⛔ A CONTRACT THAT HAS NEVER REFUSED ANYTHING IS A DOCSTRING. Each check below gets a row
that must be refused and a row that must be accepted, differing in exactly the field the
check keys on -- otherwise "refuse everything" and "accept everything" both pass.

⭐ AND THE LIVE-CORPUS POSITIVE IS THE REAL DEFECT: PMC12183782 and PMC12964950 are the two
protocols that reached the verified set labelled `systematic_review`, taken from
`oa_states_twenty.json` rather than invented. If the contract cannot refuse the rows that
actually got through, it does not close the hole it was written for.
"""
import io, json, os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace",
                              line_buffering=True)
from oa_frame_contract import (check_row, load_frame, comparators, kind_evidence,   # noqa
                               refuse_cross_kind, OAFrameRefused)

STATES = os.path.join(HERE, "../../evidence/2026-08-31-axis/oa_states_twenty.json")

results = []


def check(tag, ok, detail):
    results.append((tag, ok, detail))
    print("   %-56s %-4s %s" % (tag, "PASS" if ok else "FAIL", detail))


def row(**kw):
    r = {"oa_id": "PMC1234567", "source": "europepmc", "title": "A systematic review of X",
         "objectives_verbatim": "We aimed to evaluate X in Y.",
         "objectives_source": "abstract", "record_kind": "systematic_review",
         "is_open_access": "Y", "verification_field_kind": "abstract",
         "provenance": "europepmc REST"}
    r.update(kw)
    return r


def refuses(r, must_mention):
    try:
        check_row(r)
        return False, "ACCEPTED -- no refusal"
    except OAFrameRefused as e:
        return (must_mention in str(e)), str(e).splitlines()[1][:96]


print("=== EVERY REFUSAL PLANTED, EACH WITH A CLEAN SIBLING ===")

ok, d = refuses(row(oa_id="A systematic review of X"), "stable external identifier")
check("C1 plant: a TITLE as the key is refused", ok, d)
check("C1 clean sibling: a PMC id is accepted",
      check_row(row(oa_id="PMC9999999")) == "systematic_review", "accepted")

ok, d = refuses(row(objectives_verbatim=""), "UNOBTAINABLE")
check("C2 plant: empty-string objectives refused (null means unobtainable)", ok, d)
check("C2 clean sibling: NULL objectives accepted as 'unknown' kind",
      check_row(row(objectives_verbatim=None, record_kind="unknown")) == "unknown",
      "null is a real fact; the empty string is a parser saying nothing quietly")

ok, d = refuses(row(verification_field_kind="vibes"), "verification_field_kind")
check("C3 plant: an undeclared verification material is refused", ok, d)
check("C3 clean sibling: 'cochrane_objectives' is accepted",
      check_row(row(verification_field_kind="cochrane_objectives")) == "systematic_review",
      "accepted")

r = row()
del r["provenance"]
ok, d = refuses(r, "missing contract field")
check("C4 plant: a missing contract field is refused", ok, d)
check("C4 clean sibling: all fields present is accepted",
      check_row(row()) == "systematic_review", "accepted")

# ⛔ C5 IS THE ONE THE WHOLE FILE EXISTS FOR.
ok, d = refuses(row(objectives_verbatim="This is a protocol for a Cochrane Review "
                                        "(intervention). The objectives are as follows.",
                    record_kind="systematic_review"), "ASSERTED rather than READ")
check("C5 plant: a PROTOCOL claimed as systematic_review is refused", ok, d)
check("C5 clean sibling: the same row, kind stated HONESTLY, is accepted",
      check_row(row(objectives_verbatim="This is a protocol for a Cochrane Review "
                                        "(intervention).", record_kind="protocol")) == "protocol",
      "the contract objects to the false CLAIM, not to the protocol's existence")
# and the sibling that proves the detector is not just matching the word 'protocol'
check("C5 clean sibling: a review that MENTIONS following a protocol is still a review",
      check_row(row(objectives_verbatim="We followed our registered analysis plan and "
                                        "PRISMA guidance.")) == "systematic_review",
      "the marks are phrases, not the bare word")

try:
    load_frame([row(oa_id="PMC1111111"), row(oa_id="PMC1111111")])
    ok, d = False, "ACCEPTED a duplicate"
except OAFrameRefused as e:
    ok, d = "duplicate oa_id" in str(e), str(e).splitlines()[1][:96]
check("C6 plant: a duplicate oa_id is refused", ok, d)
_, k = load_frame([row(oa_id="PMC1111111"), row(oa_id="PMC2222222")])
check("C6 clean sibling: two distinct ids are accepted", sum(k.values()) == 2, str(dict(k)))

try:
    refuse_cross_kind("cochrane_objectives", "abstract", "MATCHED 6/20 vs 16/20")
    ok, d = False, "ACCEPTED a cross-kind comparison"
except OAFrameRefused as e:
    ok, d = "do not measure the same thing" in str(e), str(e).splitlines()[1][:96]
check("C7 plant: comparing objectives-verified with abstract-verified is refused", ok, d)
check("C7 clean sibling: same kind on both sides is allowed",
      refuse_cross_kind("abstract", "abstract", "x") == "abstract", "allowed")

print("")
print("=== KIND PARTITION -- a protocol is a THIRD kind, not data and not a defect ===")
rows = [row(oa_id="PMC3000001"), row(oa_id="PMC3000002"),
        row(oa_id="PMC3000003", record_kind="protocol",
            objectives_verbatim="This is a protocol for a Cochrane Review."),
        row(oa_id="PMC3000004", record_kind="unknown", objectives_verbatim=None)]
keep, meta = comparators(rows)
check("C8 comparators() excludes non-reviews and NAMES what it excluded",
      meta == {"n_rows": 4, "n_comparators": 2,
               "excluded_by_kind": {"protocol": 1, "unknown": 1}}, str(meta))

print("")
print("=== ⭐ THE TWO REAL PROTOCOLS, PINNED AS FIXTURES ===")
# ⛔⛔ THIS BLOCK USED TO READ THEM OUT OF `oa_states_twenty.json`, AND IT RETIRED ITSELF THE
# MOMENT THE CONTRACT WORKED. The contract excludes protocols upstream, so the two records
# vanished from the verified set and the plant went 19/19 -> 17/19 -- reported as a
# REGRESSION when it was the fix landing.
#
# ⇒ A CONTROL ANCHORED TO LIVE DATA STOPS BEING A CONTROL WHEN THE DEFECT IS FIXED. It then
# either fails and looks like a break, or passes for the wrong reason. So the two records
# are pinned here as immutable fixtures -- their own words, quoted -- and the live corpus is
# used only for the separate, opposite assertion in the next block.
PINNED_PROTOCOLS = {
    "PMC12183782": {
        "title": "Myosin inhibitors for treatment of hypertrophic cardiomyopathy.",
        "objectives_verbatim": "<h4>Objectives</h4>This is a protocol for a Cochrane Review "
                               "(intervention). The objectives are as follows: Primary "
                               "objective To assess the effects of myosin inhibitors."},
    "PMC12964950": {
        "title": "Direct oral anticoagulants versus vitamin K antagonists for "
                 "postoperative anticoagulation.",
        "objectives_verbatim": "This study protocol describes a systematic review and "
                               "meta-analysis that will compare the two strategies."},
}
PINNED_REVIEW = {
    "oa_id": "PMC13315990",
    "title": "Efficacy and safety of sotatercept in pulmonary arterial hypertension: A "
             "systematic review and meta-analysis of randomized controlled trials.",
    "objectives_verbatim": "We conducted a meta-analysis of randomized controlled trials "
                           "(RCTs) to quantify its efficacy and safety. We followed our "
                           "registered analysis plan throughout."}

for oid, rec in sorted(PINNED_PROTOCOLS.items()):
    derived, marks = kind_evidence(rec)
    check("FIXTURE %s is READ as a protocol" % oid, derived == "protocol",
          "derived %r, marks %s" % (derived, marks))
# ⭐ THE SIBLING, AND IT IS THE ONE THAT MATTERS: a real review that MENTIONS a registered
# plan must not be swept up. Without it, "call everything a protocol" passes both plants.
derived, _ = kind_evidence(PINNED_REVIEW)
check("FIXTURE PMC13315990 (a real review naming a plan) is NOT a protocol",
      derived == "systematic_review", "derived %r" % derived)
# ⭐ And the two fixtures must fire DIFFERENT marks, or one branch is carrying the rule.
m1 = set(kind_evidence(PINNED_PROTOCOLS["PMC12183782"])[1])
m2 = set(kind_evidence(PINNED_PROTOCOLS["PMC12964950"])[1])
check("FIXTURE the two protocols fire DIFFERENT marks",
      bool(m1) and bool(m2) and m1 != m2,
      "%s vs %s -- two branches proven, not one branch twice" % (sorted(m1), sorted(m2)))

print("")
print("=== ⭐ THE FIX REACHED THE CORPUS -- the opposite assertion, on live data ===")
# This is the only thing the live artefact is asked, and it is a POSITIVE property of the
# fix rather than a case that the fix deletes.
if os.path.exists(STATES):
    d = json.load(io.open(STATES, encoding="utf-8"))
    verified_ids = {r["oa_id"] for t in d["topics"]
                    for r in ((t.get("verified") or {}).get("rows") or [])}
    leaked = sorted(set(PINNED_PROTOCOLS) & verified_ids)
    check("no pinned protocol survives in the live verified set", not leaked,
          "leaked: %s" % (leaked or "none"))
    excluded = sum((t.get("kinds") or {}).get("excluded_by_kind", {}).get("protocol", 0)
                   for t in d["topics"])
    check("the contract actually removed protocols from the live run", excluded > 0,
          "%d protocol rows excluded across the twenty -- a fix that excludes NOTHING is "
          "indistinguishable from a fix that never ran" % excluded)
else:
    check("live-corpus assertions", False, "%s missing" % STATES)

print("")
n = sum(1 for _, ok, _ in results if ok)
print("PLANTS: %d/%d" % (n, len(results)))
if n != len(results):
    print("FAILED: %s" % ", ".join(t for t, ok, _ in results if not ok))
    sys.exit(1)
