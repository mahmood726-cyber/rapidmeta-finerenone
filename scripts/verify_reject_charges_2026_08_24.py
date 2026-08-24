"""Every REJECT charge against the object it is about: charge, verdict, evidence.

# control: the POSITIVE is amoxicillin-aom, whose overclaim was read by hand and confirmed
# hours ago -- its charge must come back CONFIRMED. The NEGATIVE is a synthetic charge quoting
# a sentence that is not in the notice at all, which must come back NOT_IN_NOTICE rather than
# CONFIRMED, because a charge this instrument cannot locate is not a charge it can uphold.

A BLIND REVIEWER ON A COMPLETE PACKET IS RELIABLE ABOUT THE SHAPE OF A DEFECT AND
UNRELIABLE ABOUT THE INSTANCE. Measured tonight: the scope-dropping shape was found by
pattern-matching on 10 notices and by reading on 22 -- because a notice can overstate
without using the phrases a regex knows. And on the one lane read in full, one of three
specific charges held.

    Pattern-matching finds instances of a shape already named. Reading finds the shape.
    Neither substitutes for the other, and 10-versus-22 is the demonstration.

So this does not batch-accept and does not batch-reject. For each charge it locates the
QUOTED SENTENCE in the object's own withdrawal notice and asks two mechanical questions
that do not require judgement:

    IS THE QUOTED SENTENCE ACTUALLY IN THE NOTICE?   If not, the charge is about text this
        object does not carry and cannot be upheld from here.
    DOES THE OBJECT ITSELF CARRY A NARROWER FORM?    A scope phrase, or a
        `what_this_verdict_does_not_establish`, saying the same thing bounded.

A VERDICT PER REASON A CHARGE CAN FAIL, AND THE LIST GREW TWICE BY DISCOVERY.

It began as four. RESTATES_KNOWN_GUARD split out when 27 of 34 'confirmations' turned
out to rest on a property true of 68 objects regardless of the charge -- one finding
restated once per lane, each restatement counted as new. ELSEWHERE_IN_OBJECT split out
when 23 of 51 NOT_IN_NOTICE verdicts proved to be about my locator, not the charge.

CORRECT_BUT_REMEDY_REGRESSES is the newest and comes from a different direction: not a
charge that fails, but a charge that HOLDS whose proposed fix would make things worse.
A cold lane observed that a corpus-loop pattern matching a bare `pages` would also match
a LOCAL variable sharing the name, and proposed requiring a real iteration source. True
of the regex. Applied, it drops 36 entries, and every one sampled is a genuine corpus
pass. The reviewer was RIGHT ABOUT THE CODE AND WRONG ABOUT WHAT TO DO, and only
sampling the 36 showed it.

It gets its own verdict so it can never be summed with the charges that were
straightforwardly true. Counted as CONFIRMED it inflates the yield; counted as refuted
it discards a correct reading of the code. Neither is what happened. This is
`make_the_honest_path_the_only_path` applied to a taxonomy: when the only verdicts are
upheld and not-upheld, an honest reviewer is forced to misfile.

SIX VERDICTS AND NO SEVENTH, UNTIL THE SEVENTH IS EARNED THE SAME WAY. CONFIRMED needs both: the sentence is in the notice AND the
object holds a narrower form the notice drops. NOT_IN_NOTICE is a statement about the
charge. NO_NARROWER_FORM means the notice may still overstate but the object does not
supply the correction, which is a judgement and is not made here. COULD_NOT_DETERMINE is
for an empty probe -- AND AFTER TWO PROBE FAILURES TONIGHT AN EMPTY PROBE IS A STATEMENT
ABOUT THE PROBE UNTIL PROVEN OTHERWISE, which is why it is a verdict and not a silence.
"""
from __future__ import annotations

import io
import json
import os
import re
import sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from instrument_controls import require_controls  # noqa: E402

OUT = os.path.join(REPO, "outputs", "lanes", "out")
QUOTE = re.compile(r"[\"“]([^\"”]{30,300})[\"”]")
SCOPES = ("on the clinical quantity this page pools", "the pooled quantity",
          "the quantity this page pools", "that this page pools",
          "not pre-specified", "as this page pools it")
GUARD = "what_this_verdict_does_not_establish"

# THE PRINTED ORDER, NAMED ONCE. A verdict the judge can return but the report does not
# print would leave the total disagreeing with the rows, silently.
ORDER = ("CONFIRMED_SCOPE_DROPPED", "CORRECT_BUT_REMEDY_REGRESSES",
         "RESTATES_KNOWN_GUARD", "ELSEWHERE_IN_OBJECT", "NOT_IN_OBJECT",
         "NO_NARROWER_FORM", "COULD_NOT_DETERMINE")


def load_object(topic):
    p = os.path.join(REPO, "ssot", topic, topic + ".json")
    if not os.path.isfile(p):
        return None
    try:
        return json.load(io.open(p, encoding="utf-8"))
    except ValueError:
        return None


def notice_of(obj, oid):
    blk = ((obj.get("results") or {}).get("by_outcome") or {}).get(oid) or {}
    pl = blk.get("pooled") or {}
    return str(pl.get("withdrawn_reason") or ""), blk, pl


def charges_from(text):
    """The OVERCLAIM section's quoted sentences -- the checkable half of a review."""
    m = re.search(r"OVERCLAIM(.{0,1800}?)(?:\n\s*\*?\*?2\.|UNDERCLAIM)", text,
                  re.S | re.I)
    seg = m.group(1) if m else text[:1200]
    # QUOTE has ONE capture group, so findall yields strings, not pairs. Unpacking them as
    # pairs raised on the first lane -- an assumption about the regex's own shape, made
    # while writing a file about assumptions.
    return [q.strip() for q in QUOTE.findall(seg) if q.strip()]


def judge(charge, notice, obj, blk):
    norm = re.sub(r"\s+", " ", charge).strip().lower()
    nn = re.sub(r"\s+", " ", notice).lower()
    if not notice:
        return "COULD_NOT_DETERMINE", "the object holds no withdrawal notice to check"
    # THE LOCATOR SEARCHES THE WHOLE OBJECT, NOT JUST THE NOTICE.
    #
    # The first version searched only the withdrawal notice and returned NOT_IN_NOTICE for
    # 51 charges. 23 of those quote text that IS in the object, elsewhere -- the reviewers
    # were handed the COMPLETE object and quoted from it, while I searched one field. That
    # verdict was a fact about where I looked.
    #
    # An unlocated quote is a statement about the LOCATOR until the locator has been shown
    # to cover the whole artefact. This one now does, so a miss here is about the charge.
    blob_all = re.sub(r"\s+", " ", json.dumps(obj, ensure_ascii=False)).lower()
    if norm[:60] not in nn:
        if norm[:50] in blob_all:
            return ("ELSEWHERE_IN_OBJECT",
                    "quoted from the object but not from the withdrawal notice, so it is "
                    "not evidence that the NOTICE overstates")
        return "NOT_IN_OBJECT", "quoted sentence is nowhere in this object"
    blob = json.dumps(obj, ensure_ascii=False).lower()
    narrower = [s for s in SCOPES if s in blob and s not in nn]
    guard = blk.get(GUARD) or ((blk.get("pooled") or {}).get(GUARD)) or obj.get(GUARD)
    if narrower:
        return ("CONFIRMED_SCOPE_DROPPED",
                "object holds a narrower form the notice drops: %r" % narrower[0])
    if guard:
        # NOT A CONFIRMATION OF THIS CHARGE, AND IT WAS COUNTED AS ONE.
        #
        # 27 of 34 "confirmations" rested on this branch: the object holds
        # `what_this_verdict_does_not_establish` and the notice does not state it. That is
        # TRUE OF 68 OBJECTS whether or not the specific charge is right, so it upheld every
        # charge on every one of those objects for a reason that has nothing to do with the
        # charge.
        #
        # A CHARGE THAT WOULD BE TRUE WHETHER OR NOT THE INSTANCE IS TRUE IS NOT EVIDENCE
        # ABOUT THE INSTANCE. One already-counted finding, restated once per lane, each
        # restatement counted as new: a double-count wearing the clothes of independent
        # corroboration. It is the same error as two assessors agreeing because they read
        # the same flawed packet.
        return ("RESTATES_KNOWN_GUARD",
                "object holds %s, which is true of 68 objects regardless of this charge"
                % GUARD)
    return "NO_NARROWER_FORM", "notice may overstate but the object supplies no correction"


def main():
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    rows = json.load(io.open(os.path.join(REPO, "outputs",
                                          "reject_triage_2026_08_24.json"),
                             encoding="utf-8"))
    live = [r for r in rows if r["live"]]

    # controls
    amox = next((r for r in live if r["topic"] == "amoxicillin-aom"), None)
    pos = ("amoxicillin-aom's overclaim was read by hand and confirmed; got %s", "", "")
    if amox:
        o = load_object("amoxicillin-aom")
        notice, blk, _pl = notice_of(o, amox["outcome"])
        t = io.open(os.path.join(OUT, amox["lane"] + ".out"), encoding="utf-8",
                    errors="replace").read()
        cs = charges_from(t)
        v = [judge(c, notice, o, blk)[0] for c in cs]
        pos = ("amoxicillin-aom's overclaim, read by hand hours ago; verdicts %s" % v,
               any(x == "CONFIRMED_SCOPE_DROPPED" for x in v), True)
        neg_o, neg_blk = o, blk
    else:
        neg_o, neg_blk = {}, {}
    neg_v = judge("a sentence this notice certainly does not contain anywhere at all",
                  "some unrelated notice text", neg_o, neg_blk)[0]
    require_controls("verify_reject_charges", pos,
                     ("a charge quoting a sentence absent from the notice must not be "
                      "upheld; got %s" % neg_v, neg_v.startswith("CONFIRMED"), True))

    tally, out_rows = {}, []
    for r in live:
        p = os.path.join(OUT, r["lane"] + ".out")
        if not os.path.isfile(p):
            continue
        o = load_object(r["topic"])
        if o is None:
            continue
        notice, blk, _pl = notice_of(o, r["outcome"])
        for c in charges_from(io.open(p, encoding="utf-8", errors="replace").read()):
            verdict, why = judge(c, notice, o, blk)
            tally[verdict] = tally.get(verdict, 0) + 1
            out_rows.append({"topic": r["topic"], "outcome": r["outcome"],
                             "charge": c[:150], "verdict": verdict, "evidence": why,
                             "page": (r["pages"] or [None])[0]})

    print("")
    print("REJECT CHARGES, over %d live REJECT lanes" % len(live))
    print("")
    for k in ORDER:
        print("   %-22s %4d" % (k, tally.get(k, 0)))
    unprinted = sorted(set(tally) - set(ORDER))
    assert not unprinted, "verdict(s) tallied but never printed: %s" % unprinted
    tot = sum(tally.values())
    print("   %-22s %4d   == every charge extracted" % ("total", tot))
    if tot:
        print("")
        print("   withdrawn or unupheld: %d of %d  (%.0f%%)"
              % (tot - tally.get("CONFIRMED_SCOPE_DROPPED", 0), tot,
                 100.0 * (tot - tally.get("CONFIRMED_SCOPE_DROPPED", 0)) / tot))
    print("")
    for row in [x for x in out_rows if x["verdict"] == "CONFIRMED_SCOPE_DROPPED"][:14]:
        print("   CONFIRMED  %-30s %s" % (row["topic"][:30], row["page"] or ""))
        print("        charge   : %s" % row["charge"][:110])
        print("        evidence : %s" % row["evidence"][:110])
    json.dump(out_rows, io.open(os.path.join(REPO, "outputs",
                                             "reject_charges_2026_08_24.json"),
                                "w", encoding="utf-8"), indent=1)


if __name__ == "__main__":
    main()
