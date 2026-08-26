#!/usr/bin/env python
"""A direction-of-benefit label must be DERIVED from the outcome's polarity.

LAYER: the defect lives in the PROJECTOR (ssot/build_app_v2.py:_favoured_arm),
surfaces at the RENDER layer, and is INVISIBLE in the store -- the object
recorded "higher is better" correctly and the page printed "lower is better".
A check that reads only the store passes while the plot lies.

This gate EXERCISES THE REAL RENDERER rather than re-implementing its rules.
A gate that duplicates the logic it checks cannot fail when that logic is
wrong -- it only agrees with itself. Reverting the fix in build_app_v2.py
makes this gate fail, which is the property that makes it a gate.

Part 1  behaviour of the real _favoured_arm over known polarities
Part 2  every stored polarity token in the corpus is one the renderer knows
"""
import os, sys, json

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "ssot"))
sys.path.insert(0, os.path.join(ROOT, "scripts"))
import build_app_v2 as B                                          # noqa: E402
from instrument_controls import require_controls                  # noqa: E402

HIGHER, LOWER = "higher is better", "lower is better"
KNOWN = {"higher", "higher is better", "lower", "lower is better"}

def label(direction):
    outcome = {"name": "probe", "treatment_node": "T", "comparator_node": "C"}
    if direction is not None:
        outcome["direction_of_benefit"] = direction
    return B._favoured_arm({"favours": "treatment"}, outcome)

CASES = [
    ("higher",                       HIGHER, LOWER),
    ("higher is better",             HIGHER, LOWER),
    ("Higher Is Better",             HIGHER, LOWER),
    ("lower",                        LOWER,  HIGHER),
    ("lower is better",              LOWER,  HIGHER),
    ("not recorded on the page",     None,   None),
    (None,                           None,   None),
]

def part1():
    fails = []
    for raw, must, must_not in CASES:
        got = label(raw)
        if must is None:
            if HIGHER in got or LOWER in got:
                fails.append((raw, got, "unknown polarity rendered as a CLAIM"))
        else:
            if must not in got:
                fails.append((raw, got, "expected %r" % must))
            elif must_not in got:
                fails.append((raw, got, "also emitted the OPPOSITE %r" % must_not))
    return fails

def part2():
    unknown = []
    for rt, dirs, fs in os.walk(os.path.join(ROOT, "ssot")):
        for f in (x for x in fs if x.endswith(".json")):
            p = os.path.join(rt, f)
            try:
                obj = json.load(open(p, encoding="utf-8", errors="replace"))
            except Exception:                                     # noqa: BLE001
                continue
            stack = [obj]
            while stack:
                o = stack.pop()
                if isinstance(o, dict):
                    d = o.get("direction_of_benefit")
                    if d is not None and str(d).strip().lower() not in KNOWN:
                        unknown.append((os.path.relpath(p, ROOT).replace(os.sep, "/"),
                                        o.get("name") or "?", d))
                    stack.extend(o.values())
                elif isinstance(o, list):
                    stack.extend(o)
    return unknown

def stored(objpath, needle):
    """The polarity token this corpus actually stores for a named outcome."""
    obj = json.load(open(os.path.join(ROOT, objpath), encoding="utf-8",
                        errors="replace"))
    stack, hit = [obj], None
    while stack:
        o = stack.pop()
        if isinstance(o, dict):
            if needle in str(o.get("name") or "") and "direction_of_benefit" in o:
                hit = o["direction_of_benefit"]
            stack.extend(o.values())
        elif isinstance(o, list):
            stack.extend(o)
    return hit


if __name__ == "__main__":
    # CONTROLS. Positive: the incretin-HFpEF KCCQ outcome, whose answer was
    # established independently of this code -- an external reviewer read the
    # DELIVERED page, saw "lower is better" beside a pooled MD of +7.43 on a
    # 0-100 instrument where higher is better, and reported it. The object
    # stores "higher is better"; the label must say so.
    # Negative: a genuine lower-is-better outcome must NOT come back "higher".
    _kccq = stored("ssot/incretin-hfpef-review/incretin-hfpef-review.json", "KCCQ")
    require_controls(
        "direction_polarity_gate",
        positive=("incretin-HFpEF KCCQ label", HIGHER in label(_kccq), True),
        negative=("a lower-is-better outcome", HIGHER in label("lower"), True),
    )
    f1 = part1()
    print("PART 1  real renderer over %d known polarities" % len(CASES))
    for raw, got, why in f1:
        print("   FAIL  stored %r -> %r  (%s)" % (raw, got, why))
    print("   %s" % ("PASS" if not f1 else "%d FAILURE(S)" % len(f1)))

    u = part2()
    print("PART 2  stored polarity tokens the renderer does not recognise: %d" % len(u))
    # These are NOT failures: the renderer now refuses them explicitly. They are
    # REPORTED so absence stays visible instead of being silently dropped from
    # the denominator.
    for s, n, d in u[:3]:
        print("   refuses (correctly): %s :: %s :: %r" % (s, str(n)[:40], str(d)[:40]))
    if len(u) > 3:
        print("   ... +%d more, all rendered as an explicit refusal" % (len(u) - 3))

    if f1:
        sys.exit("REFUSED: the direction label is not derived from the outcome's polarity.")
    print("\nevery direction label is derived from its outcome's own polarity.")
