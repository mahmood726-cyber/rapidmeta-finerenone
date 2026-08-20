"""Score every topic that publishes a pooled estimate against P46, from the objects.

P46 (PAGE-STANDARD.md): a topic is complete when its OBJECT holds -- or states a reason
for the absence of -- a risk-of-bias assessment PER RESULT, a GRADE rating PER POOLED
OUTCOME, a published comparison CARRYING A DENOMINATOR, and the model output QUOTED
VERBATIM.

A DISCHARGED REFUSAL SCORES AS COMPLETE, and that is not leniency. A held-only counter
reports a correctly-refusing topic as incomplete forever, and somebody eventually
"fixes" it by writing into the slot -- which is how a refusal becomes a fabrication.

THE COUNTER ASSERTS IT COUNTED SOMETHING. If it visits no objects, finds no pooled
estimate anywhere, or scores every single topic identically, it exits non-zero: a
scorer that cannot distinguish between topics is not measuring them.

Run: python scripts/p46_queue.py [topic ...]
"""
import io
import json
import os
import sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SSOT = os.path.join(REPO, "ssot")

# A refusal is discharged when it says what was REACHED and what was found insufficient.
# These are the keys the corpus already uses for that; a slot holding only `None` with no
# such sibling is a BLANK, and a blank is not a refusal.
REFUSAL_KEYS = ("refusal_discharges_P46_because", "_why_absent", "why_not_manufactured",
                "denominator_reason", "what_would_change_it", "what_stands_instead",
                "what_would_hold_P6", "state")


def has_refusal(node):
    if not isinstance(node, dict):
        return False
    return any(node.get(k) not in (None, "", [], {}) for k in REFUSAL_KEYS)


def pooled_outcomes(obj):
    out = []
    for oid, blk in (((obj.get("results") or {}).get("by_outcome")) or {}).items():
        if isinstance(blk, dict) and isinstance(blk.get("pooled"), dict) \
                and blk["pooled"].get("point") is not None:
            out.append((oid, blk))
    return out


def score(obj):
    """Return {limb: (state, detail)} where state is HELD, REFUSED or ABSENT."""
    pools = pooled_outcomes(obj)
    oids = [oid for oid, _ in pools]
    res = {}

    # 1. RISK OF BIAS, PER RESULT.
    rob = obj.get("risk_of_bias")
    byo = (rob or {}).get("by_outcome") if isinstance(rob, dict) else None
    if isinstance(byo, dict) and all(isinstance(byo.get(o), dict) and byo[o] for o in oids):
        n = sum(len(byo[o]) for o in oids)
        res["rob_per_result"] = ("HELD", "%d result-level assessments over %d outcome(s)"
                                 % (n, len(oids)))
    elif isinstance(rob, dict) and has_refusal(rob):
        res["rob_per_result"] = ("REFUSED", "risk_of_bias states its own absence")
    elif isinstance(obj.get("absent_from_source"), dict) and \
            obj["absent_from_source"].get("rob2"):
        res["rob_per_result"] = ("REFUSED", str(obj["absent_from_source"]["rob2"])[:70])
    else:
        missing = [o for o in oids if not (isinstance(byo, dict) and byo.get(o))]
        res["rob_per_result"] = ("ABSENT", "no assessment and no stated reason for %s"
                                 % (", ".join(missing) or "the topic"))

    # 2. GRADE, PER POOLED OUTCOME.
    g = obj.get("grade")
    gb = (g or {}).get("by_outcome") if isinstance(g, dict) else None
    held, refused, absent = [], [], []
    for oid, blk in pools:
        entry = gb.get(oid) if isinstance(gb, dict) else None
        if isinstance(entry, dict) and entry.get("certainty"):
            held.append(oid)
        elif isinstance(blk.get("grade"), dict) and blk["grade"].get("certainty"):
            held.append(oid)
        elif has_refusal(entry) or has_refusal(blk.get("grade")):
            refused.append(oid)
        elif isinstance(obj.get("absent_from_source"), dict) and \
                obj["absent_from_source"].get("grade"):
            refused.append(oid)
        else:
            absent.append(oid)
    if absent:
        res["grade_per_pool"] = ("ABSENT", "no rating and no stated reason for %s"
                                 % ", ".join(absent))
    elif held and not refused:
        res["grade_per_pool"] = ("HELD", "%d of %d pooled outcome(s)" % (len(held), len(pools)))
    else:
        res["grade_per_pool"] = ("REFUSED" if not held else "HELD",
                                 "held %s, refused %s" % (len(held), len(refused)))

    # 3. PUBLISHED COMPARISON, CARRYING A DENOMINATOR.
    pc = obj.get("published_comparison")
    if isinstance(pc, dict) and pc.get("denominator") not in (None, "", [], {}):
        res["comparison_denominator"] = ("HELD", "denominator = %r" % (pc["denominator"],))
    elif isinstance(pc, dict) and has_refusal(pc):
        res["comparison_denominator"] = ("REFUSED", str(pc.get("denominator_reason")
                                                        or "stated")[:70])
    else:
        res["comparison_denominator"] = ("ABSENT", "no denominator and no stated reason")

    # 4. MODEL OUTPUT, QUOTED VERBATIM, per pooled outcome.
    held, refused, absent = [], [], []
    for oid, blk in pools:
        ro = blk.get("r_output")
        if isinstance(ro, dict) and ro.get("verbatim"):
            held.append(oid)
        elif has_refusal(ro) or has_refusal(blk.get("r_output_refused")):
            refused.append(oid)
        else:
            absent.append(oid)
    if absent:
        res["model_output_verbatim"] = ("ABSENT", "no quoted output and no stated reason "
                                        "for %s" % ", ".join(absent))
    elif held and not refused:
        res["model_output_verbatim"] = ("HELD", "%d of %d pooled outcome(s)"
                                        % (len(held), len(pools)))
    else:
        res["model_output_verbatim"] = ("REFUSED" if not held else "HELD",
                                        "held %s, refused %s" % (len(held), len(refused)))
    return res


def main():
    want = set(sys.argv[1:])
    rows = []
    visited = 0
    with_pool = 0
    for name in sorted(os.listdir(SSOT)):
        d = os.path.join(SSOT, name)
        if not os.path.isdir(d):
            continue
        fp = os.path.join(d, name + ".json")
        if not os.path.exists(fp):
            js = [f for f in os.listdir(d) if f.endswith(".json")]
            if len(js) != 1:
                continue
            fp = os.path.join(d, js[0])
        try:
            obj = json.load(io.open(fp, encoding="utf-8"))
        except Exception:
            continue
        visited += 1
        if not pooled_outcomes(obj):
            continue
        with_pool += 1
        if want and name not in want:
            continue
        rows.append((name, score(obj)))

    if visited == 0:
        sys.exit("REFUSED: visited zero objects.")
    if with_pool == 0:
        sys.exit("REFUSED: no object publishes a pooled estimate; the walk is wrong.")

    limbs = ["rob_per_result", "grade_per_pool", "comparison_denominator",
             "model_output_verbatim"]
    print("topics that publish a pooled estimate: %d (of %d objects read)"
          % (with_pool, visited))
    print()
    hdr = "%-44s %-4s %s" % ("topic", "n/4", "  ".join("%-22s" % l for l in limbs))
    print(hdr)
    print("-" * len(hdr))
    complete = 0
    per_limb = {l: 0 for l in limbs}
    shapes = set()
    for name, s in rows:
        n = sum(1 for l in limbs if s[l][0] in ("HELD", "REFUSED"))
        for l in limbs:
            if s[l][0] in ("HELD", "REFUSED"):
                per_limb[l] += 1
        if n == 4:
            complete += 1
        shapes.add(tuple(s[l][0] for l in limbs))
        print("%-44s %-4s %s" % (name[:44], "%d/4" % n,
                                 "  ".join("%-22s" % s[l][0] for l in limbs)))
    print()
    if len(rows) > 1 and len(shapes) == 1:
        sys.exit("REFUSED: all %d topics scored identically (%s). A scorer that cannot "
                 "distinguish between topics is not measuring them."
                 % (len(rows), shapes.pop()))
    print("COMPLETE by P46 (held OR discharged on all four): %d of %d" % (complete, len(rows)))
    for l in limbs:
        print("  %-24s %d of %d  (%.0f%%)" % (l, per_limb[l], len(rows),
                                              100.0 * per_limb[l] / max(1, len(rows))))
    if want:
        print()
        for name, s in rows:
            print("=" * 96)
            print(name)
            for l in limbs:
                st, detail = s[l]
                print("  [%-8s] %-24s %s" % (st, l, detail))


if __name__ == "__main__":
    main()
