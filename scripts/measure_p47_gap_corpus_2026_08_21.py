"""The 37-claim P47 frame, run across every topic. One topic gave a bound; this gives the spread.

`measure_p47_gap_iv_iron_2026_08_21.py` measured ONE topic, chosen to be a floor, and reported
59.5% derivable. A floor is a bound, not a rate, and THE NUMBER THAT MATTERS FOR PLANNING IS THE
WORST TOPIC, NOT THE BEST. If some topics derive 20% where iv-iron-hf derives 60%, tier 3 is two
jobs and not one.

THE FRAME IS UNCHANGED AND IS IMPORTED, NOT COPIED. Same 37 claims, same PRISMA 2020 anchors,
same resolver. Copying the list would let the two measurements drift and the second would
silently stop being comparable with the first.

HOW A CLAIM IS COUNTED, PER TOPIC:

    DERIVABLE   classed derivable in the frame AND its field resolves on THIS object
    FETCHABLE   classed fetchable in the frame, OR classed derivable and the field does NOT
                resolve here -- because a fact the schema can hold and this object does not is
                work, not judgement
    ARGUMENT    classed argument in the frame. Invariant across topics: whether an effect is
                clinically meaningful is not a thing an object can come to hold.

SO `ARGUMENT` IS A CONSTANT 12 OF 37 AND ONLY THE DERIVABLE/FETCHABLE SPLIT MOVES. That is not a
limitation of the measurement; it is the finding restated -- the irreducible writing is the same
on every topic, and what varies is how much bookkeeping is already in hand.
"""
import glob
import importlib.util
import io
import json
import os
import sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_spec = importlib.util.spec_from_file_location(
    "p47frame", os.path.join(REPO, "scripts", "measure_p47_gap_iv_iron_2026_08_21.py"))
frame = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(frame)

_q = importlib.util.spec_from_file_location(
    "p46_queue", os.path.join(REPO, "scripts", "p46_queue.py"))
p46 = importlib.util.module_from_spec(_q)
_q.loader.exec_module(p46)

D, F, A = frame.D, frame.F, frame.A


def score_topic(obj):
    d = f = a = 0
    missing = []
    for item, section, claim, kind, path in frame.CLAIMS:
        if kind == A:
            a += 1
        elif kind == F:
            f += 1
        else:
            ok, _ = frame.resolve(obj, path)
            if ok:
                d += 1
            else:
                f += 1
                missing.append((item, claim))
    return d, f, a, missing


def main():
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    total = len(frame.CLAIMS)
    rows = []
    for p in sorted(glob.glob(os.path.join(REPO, "ssot", "*", "*.json"))):
        topic = os.path.basename(os.path.dirname(p))
        if os.path.basename(p) != topic + ".json":
            continue
        try:
            obj = json.load(io.open(p, encoding="utf-8"))
        except ValueError:
            continue
        if not p46.pooled_outcomes(obj):
            continue
        d, f, a, missing = score_topic(obj)
        rows.append((d, topic, f, a, missing))
    rows.sort()

    print("")
    print("THE 37-CLAIM PRISMA FRAME ACROSS %d TOPICS -- every topic carrying a pooled outcome."
          % len(rows))
    print("`argument` is a constant %d of %d: whether an effect is clinically meaningful is not"
          % (sum(1 for c in frame.CLAIMS if c[3] == A), total))
    print("a thing an object can come to hold. Only the derivable/fetchable split moves.")
    print("")
    print("%-44s %-11s %-11s %s" % ("topic", "derivable", "fetchable", "argument"))
    for d, topic, f, a, _ in rows:
        print("%-44s %2d  %4.1f%%  %2d  %4.1f%%  %2d  %4.1f%%"
              % (topic[:44], d, 100.0 * d / total, f, 100.0 * f / total,
                 a, 100.0 * a / total))

    ds = [r[0] for r in rows]
    n = len(ds)
    mean = sum(ds) / float(n)
    srt = sorted(ds)
    med = srt[n // 2] if n % 2 else (srt[n // 2 - 1] + srt[n // 2]) / 2.0
    print("")
    print("DISTRIBUTION OF DERIVABLE CLAIMS, out of %d" % total)
    print("   worst   %2d  (%4.1f%%)   %s" % (srt[0], 100.0 * srt[0] / total, rows[0][1]))
    print("   median  %4.1f  (%4.1f%%)" % (med, 100.0 * med / total))
    print("   mean    %4.1f  (%4.1f%%)" % (mean, 100.0 * mean / total))
    print("   best    %2d  (%4.1f%%)   %s" % (srt[-1], 100.0 * srt[-1] / total, rows[-1][1]))
    print("   spread  %2d claims, %.1f percentage points" % (srt[-1] - srt[0],
                                                             100.0 * (srt[-1] - srt[0]) / total))
    iv = [r for r in rows if r[1] == "iv-iron-hf"]
    if iv:
        d = iv[0][0]
        better = sum(1 for x in ds if x > d)
        print("")
        print("   iv-iron-hf, the topic chosen as a FLOOR, derives %d (%.1f%%)."
              % (d, 100.0 * d / total))
        print("   %d of %d topics derive MORE; %d derive the same or less."
              % (better, n, n - better - 1))
        print("   THE FLOOR %s." % ("HELD -- it is not the worst topic, but nothing derives far below it"
                                    if srt[0] >= d - 4 else
                                    "DID NOT HOLD: the worst topic is %d claims below it"
                                    % (d - srt[0])))

    print("")
    print("WHICH DERIVABLE CLAIMS FAIL MOST OFTEN ACROSS THE CORPUS:")
    tally = {}
    for _, _, _, _, missing in rows:
        for item, claim in missing:
            tally[(item, claim)] = tally.get((item, claim), 0) + 1
    for (item, claim), c in sorted(tally.items(), key=lambda kv: -kv[1])[:10]:
        print("   %-5s %-62s missing on %2d of %d" % (item, claim[:62], c, n))
    print("")
    print("EVERY ONE OF THOSE IS FETCHABLE, NOT ARGUMENT -- a field the schema can hold that")
    print("this object does not. It is work, and it is the work that would move the number.")


if __name__ == "__main__":
    main()
