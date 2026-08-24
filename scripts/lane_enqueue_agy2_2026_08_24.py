"""A second family of agy work, queued because agy went idle with an empty queue.

TWO IDLE SLOTS AND NOTHING BEHIND THEM IS THE FAILURE. The daemon was healthy, codex was
full at 4, and agy sat at 0 of 2 for want of tasks -- not for want of capacity. The first
agy family (one lane per withdrawal text) had drained. So this queues the judgement-shaped
questions that are actually open tonight, and the two are deliberately different in kind:

    FAMILY A -- fields the corpus HOLDS and no page SHOWS. The audit can say a field is held
        by 155 objects and rendered on 0 pages. It cannot say whether that silence is a
        defect. `withheld_display` reaching no reader may be correct; a recorded objection
        reaching no reader probably is not. That is a judgement about what a reader is owed,
        which is exactly what a cold reader is for and exactly what an audit is not.

    FAMILY B -- pools carrying a GRADE certainty in BOTH locations. The brief owes a
        supervised read on these: `grade.by_outcome.<oid>.certainty` and
        `results.by_outcome.<oid>.grade.certainty` may agree as strings and still disagree
        about what was rated. Consolidating to one location without reading them is how a
        rating gets manufactured by a merge.

Both prompts carry the completeness assertion and both carry the WHOLE object, for the
reason PACKET-COMPLETENESS-2026-08-23.md records: a fixed field list plus a completeness
assertion is a false assurance, and it manufactured six confident fabrication accusations.
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
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(REPO, "ssot"))
from instrument_controls import require_controls  # noqa: E402
import qualification_fields as qf  # noqa: E402

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


def objects():
    for p in sorted(glob.glob(os.path.join(REPO, "ssot", "*", "*.json"))):
        t = os.path.basename(os.path.dirname(p))
        if os.path.basename(p) != t + ".json":
            continue
        try:
            yield t, json.load(io.open(p, encoding="utf-8"))
        except ValueError:
            continue


def find_value(obj, key):
    """First stored value for `key` at any depth, with the path that reached it."""
    stack = [(obj, "")]
    while stack:
        cur, path = stack.pop(0)
        if isinstance(cur, dict):
            for k, v in cur.items():
                sub = path + "." + str(k) if path else str(k)
                if k == key and isinstance(v, str):
                    return sub, v
                stack.append((v, sub))
        elif isinstance(cur, list):
            for i, v in enumerate(cur):
                stack.append((v, "%s[%d]" % (path, i)))
    return None, None


def family_a(rows, cache):
    """One lane per qualifying field the corpus holds and no page shows."""
    n = 0
    for r in rows:
        if r["pages"] or r["objects"] < 1:
            continue
        holders = []
        for t, o in cache:
            path, val = find_value(o, r["field"])
            if val:
                holders.append({"topic": t, "path_in_object": path, "stored_value": val})
            if len(holders) >= 3:
                break
        if not holders:
            continue
        whole = next((o for t, o in cache if t == holders[0]["topic"]), {})
        body = (PACKET + """A field is RECORDED on %d object(s) in this corpus and appears on
ZERO delivered pages. The audit that found it can measure that silence and cannot judge it.
You are being asked for the judgement, and only the judgement.

THE FIELD: %s
HELD BY: %d object(s).  SHOWN ON: 0 pages.

The question is NOT whether the field is well written. It is:

1. IS A READER OWED THIS? Answer OWED / NOT OWED / COULD NOT DETERMINE, and say why in one
   sentence. Some silence is correct -- a field recording an internal decision, a duplicate
   of text already shown under another name, or a machine flag -- and saying NOT OWED where
   that is true is as valuable as saying OWED where it is not.
2. IF OWED: WHERE. Which reader, at what moment, needs it. A qualification shown in a place
   nobody reads has not reached anyone.
3. IS IT A DUPLICATE? Search the complete object below. If this text is already on a page
   under a different field name, say so and name the other field -- that would make the
   silence harmless and the finding a false positive.
4. WHAT WOULD BE LOST if this were simply deleted rather than shown?

Under 350 words. If the stored value is boilerplate that says nothing, say so plainly.

--- THE STORED VALUES, AND ONE COMPLETE OBJECT THAT HOLDS THE FIELD ---
""" % (r["objects"], r["field"], r["objects"])
                + json.dumps({"field": r["field"], "holders": holders,
                              "THE_COMPLETE_OBJECT": whole}, indent=1,
                             ensure_ascii=False))
        write("agy_silent_field__" + r["field"][:60], body)
        n += 1
    return n


def double_rated(cache):
    """Pools carrying a certainty in BOTH the structured block and the results table."""
    out = []
    for t, o in cache:
        g = ((o.get("grade") or {}).get("by_outcome") or {})
        r = ((o.get("results") or {}).get("by_outcome") or {})
        if not isinstance(g, dict) or not isinstance(r, dict):
            continue
        for oid, blk in g.items():
            if not isinstance(blk, dict):
                continue
            a = blk.get("certainty")
            rb = r.get(oid) if isinstance(r.get(oid), dict) else {}
            gb = rb.get("grade") if isinstance(rb.get("grade"), dict) else {}
            b = gb.get("certainty")
            if a and b:
                out.append((t, oid, a, b, o))
    return out


def family_b(pairs):
    n = 0
    for t, oid, a, b, o in pairs:
        body = (PACKET + """ONE pooled outcome carries a GRADE certainty rating in TWO
places in the same object. The corpus is being consolidated to one authoritative location,
and the standing instruction is that consolidation MUST NOT MANUFACTURE A RATING. Two
strings that read the same can still have been arrived at for different reasons, or be about
different quantities.

  structured block   grade.by_outcome.%s.certainty          = %r
  results table      results.by_outcome.%s.grade.certainty  = %r

Answer, in under 400 words:

1. DO THESE RATE THE SAME QUANTITY? Read the surrounding blocks in the complete object
   below. If one is about the pooled effect and the other about something narrower or
   broader, the strings agreeing is a coincidence, not a confirmation.
2. IS EITHER RATING SUPPORTED BY RECORDED GROUNDS? Name the fields carrying the domain
   judgements (risk of bias, inconsistency, indirectness, imprecision, publication bias) for
   each location. If one location has grounds and the other has only a level, say so -- a
   level with no grounds behind it is the thing most likely to survive a merge unnoticed.
3. IF THEY DISAGREE, is the disagreement substantive or a wording difference?
4. WHICH LOCATION SHOULD SURVIVE, and what would be LOST by dropping the other? Answer
   NEITHER-WITHOUT-A-HUMAN-READ if the grounds do not settle it. That answer is available
   and is not a failure to answer.

DO NOT propose a rating. If the object does not settle the question, the correct output is
the naming of what is missing.

--- THE COMPLETE OBJECT ---
""" % (oid, a, oid, b) + json.dumps(o, indent=1, ensure_ascii=False))
        write("agy_double_rated__%s__%s" % (t.replace("-", "_"), oid), body)
        n += 1
    return n


def main():
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    cache = list(objects())

    # CONTROLS. The positive keys to a FIXTURE PROPERTY that this run does not move: the
    # corpus holds qualifying fields at all, so the enqueuer's own reader works. The negative
    # asserts family A cannot pick a field that IS rendered -- if it could, agy would be
    # asked to judge silence that does not exist, and every answer would be about a fiction.
    rows = json.load(io.open(os.path.join(
        REPO, "outputs", "qualifications_reach_a_reader_2026_08_24.json"),
        encoding="utf-8"))["rows"]
    probe = qf.qualifying_items(cache[0][1]) if cache else {}
    loud = [r for r in rows if r["pages"] > 0]
    picked_loud = [r for r in loud if not r["pages"]]
    require_controls(
        "lane_enqueue_agy2",
        ("the shared qualification predicate reads a real object: %d field(s) found on %s"
         % (len(probe), cache[0][0] if cache else "-"), bool(probe), True),
        ("family A must never queue a field that IS rendered; %d of %d rendered fields "
         "selected" % (len(picked_loud), len(loud)), bool(picked_loud), True))

    a = family_a(rows, cache)
    pairs = double_rated(cache)
    b = family_b(pairs)
    q = len([f for f in os.listdir(QUEUE) if f.endswith(".task")])
    print("")
    print("   FAMILY A  silent qualifying fields, one lane each   %4d" % a)
    print("   FAMILY B  pools rated in both locations             %4d" % b)
    print("   total queued now (all engines)                      %4d" % q)


if __name__ == "__main__":
    main()
