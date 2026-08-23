"""Queue the judgement-shaped work for agy, with packet completeness asserted each time.

WHY THE ASSERTION IS IN EVERY PROMPT. A blinded read of a PARTIAL packet returned six
confident accusations of fabrication in one night, and all six named facts that were on the
object and missing from what I sent. The reviewer was not careless; the packet was
incomplete, and an incomplete packet manufactures false defect classes in the most
convincing possible form. So each prompt below states what it contains, states that nothing
is withheld, and instructs the reviewer to answer COULD NOT DETERMINE and NAME the gap
rather than call anything invented.
"""
from __future__ import annotations

import glob
import io
import json
import os
import sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
QUEUE = os.path.join(REPO, "outputs", "lanes", "queue")
PROMPTS = os.path.join(REPO, "outputs", "lanes", "prompts")

PACKET = """PACKET COMPLETENESS, ASSERTED. Everything you need is in this message. The
material below is reproduced IN FULL and unabridged; nothing is withheld or summarised. You
have no file access and should not ask for any.

If something you need is genuinely not here, answer COULD NOT DETERMINE and NAME what is
missing. Do NOT say anything is fabricated, invented, or absent from the record: an earlier
blinded read of a partial packet returned six confident accusations of fabrication, and all
six named facts that were present in the record and missing only from the packet. A false
accusation costs as much here as a missed defect.

"""


def write(name, body):
    os.makedirs(QUEUE, exist_ok=True)
    os.makedirs(PROMPTS, exist_ok=True)
    pp = os.path.join(PROMPTS, name + ".txt")
    io.open(pp, "w", encoding="utf-8", newline="\n").write(body)
    json.dump({"engine": "agy", "prompt": os.path.relpath(pp, REPO)},
              io.open(os.path.join(QUEUE, name + ".task"), "w", encoding="utf-8"))


def wording_lanes():
    """Every withdrawal and correction text written tonight, one lane each, read cold."""
    n = 0
    for p in sorted(glob.glob(os.path.join(REPO, "ssot", "*", "*.json"))):
        t = os.path.basename(os.path.dirname(p))
        if os.path.basename(p) != t + ".json":
            continue
        try:
            o = json.load(io.open(p, encoding="utf-8"))
        except ValueError:
            continue
        for oid, blk in ((o.get("results") or {}).get("by_outcome") or {}).items():
            if not isinstance(blk, dict):
                continue
            pl = blk.get("pooled") or {}
            if not isinstance(pl, dict) or not pl.get("withdrawn"):
                continue
            reason = pl.get("withdrawn_reason")
            if not reason or len(str(reason)) < 200:
                continue
            # THE WHOLE OBJECT, BECAUSE THE ASSERTION HAS TO BE EARNED.
            #
            # This built a packet from a FIXED LIST of fields and then told the reviewer
            # nothing was withheld. That is worse than not asserting completeness at all: it
            # is a false assurance, and the reviewer acted on it exactly as instructed. 11 of
            # the first agy wording lanes returned REJECT on reasoning of the form "the
            # provided evidence contains none of these registry strings" -- and the strings
            # were on the object, outside my field list. The write-up in
            # PACKET-COMPLETENESS-2026-08-23.md says to name every field the text relies on
            # and assert each is present; the first implementation of it did not do that step.
            #
            # Naming the fields a free-prose withdrawal relies on is not mechanisable -- it
            # quotes whatever it needs. So the packet is the OBJECT, entire. stdin carries it;
            # there is no size limit to trade against honesty here.
            packet = {
                "topic": t, "outcome_under_review": oid,
                "THE_WITHDRAWAL_TEXT_TO_REVIEW": reason,
                "THE_NOTE": pl.get("withdrawn_note"),
                "OTHER_GROUNDS_RECORDED": pl.get("and_a_second_independent_ground"),
                "THE_COMPLETE_OBJECT_THIS_TEXT_WAS_WRITTEN_FROM": o,
            }
            body = (PACKET + """You are reviewing ONE withdrawal text, cold. The house rule
it must satisfy: a stated reason asserts exactly what the evidence supports -- NO MORE, and
no less. Overclaiming is the failure being hunted; understating in the corpus's own favour
is the same failure pointing the other way.

Answer these, briefly, in under 400 words total:

1. OVERCLAIM. Quote any sentence asserting more than the packet supports, and say what the
   extra claim is. If none, say NONE.
2. UNDERCLAIM. Does the packet show a ground for withdrawal that the text does not state?
   Name it. This is the more likely failure on a text written by the person who withdrew it.
3. FACT vs JUDGEMENT. Any place an interpretive judgement is written in the grammar of a
   fact, or attributed to the evidence rather than owned.
4. IS THE STATED REASON THE ACTUAL REASON? Given the contributing trials and their declared
   contrasts, does the reason follow? Could the same packet support a DIFFERENT reason that
   has not been given?
5. VERDICT: ACCEPT / ACCEPT WITH CHANGES (list them) / REJECT (say why).

NOTE ON THE PACKET: it contains the ENTIRE canonical object this text was written from,
under THE_COMPLETE_OBJECT_THIS_TEXT_WAS_WRITTEN_FROM -- every field at every depth, not a
selection. So "the packet does not contain X" is now a strong statement: if a value is not
in there, it is not on the object either. Search it before saying anything is missing.

--- THE PACKET, AS JSON ---
""" + json.dumps(packet, indent=1, ensure_ascii=False))
            write("agy_wording_%s__%s" % (t.replace("-", "_"), oid), body)
            n += 1
    return n


def topology_lane():
    ev = {}
    for t in ("antimalarial-act", "cryptococcal-meningitis"):
        p = os.path.join(REPO, "ssot", t, t + ".json")
        if os.path.isfile(p):
            o = json.load(io.open(p, encoding="utf-8"))
            ev[t] = {"network": o.get("network")}
    body = (PACKET + """A corpus contains network meta-analyses. Most are STARS: every
treatment compared only against one common comparator, no closed loop. All present a
RANKING. The decision taken is: emit the computed topology, do NOT remove rankings, and
where a ranking sits on a star, state what it can and cannot support.

THE TRAP: qualifying a ranking can slide from a STATEMENT OF WHAT THE NETWORK IS -- a fact
about the graph -- into a JUDGEMENT ABOUT HOW MUCH TO DISCOUNT IT, which is an opinion. The
first is owed to the reader; the second is not ours to make.

A candidate single sentence has been proposed:

  "This network is a star with no closed loops: every non-comparator treatment is evaluated
   purely via indirect comparison through the common comparator, and statistical consistency
   cannot be assessed."

Answer in under 400 words:
1. Is every clause of that sentence a FACT about the graph? Name any clause that is not.
2. Is anything the topology determines LEFT OUT of it? Add only what is fact.
3. What would a well-meaning author be tempted to append that would cross into judgement?
4. Check it against the two real networks below: is it TRUE of each? Where a network is not
   a star, what should the sentence say instead?

--- THE NETWORKS, AS JSON ---
""" + json.dumps(ev, indent=1, ensure_ascii=False)[:9000])
    write("agy_topology_sentence", body)
    return 1


def main():
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    w = wording_lanes()
    t = topology_lane()
    q = len([f for f in os.listdir(QUEUE) if f.endswith(".task")])
    print("   agy wording lanes (one per withdrawal) %4d" % w)
    print("   agy topology lane                      %4d" % t)
    print("   total queued now                       %4d" % q)


if __name__ == "__main__":
    main()
