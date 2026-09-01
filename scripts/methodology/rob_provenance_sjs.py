# -*- coding: utf-8 -*-
"""GAP 1, SECOND INDEPENDENT SCORING -- RoBBR SJS (Support Judgment Selection).

WHY A SECOND SCORING
  SSR scored the lexicon at coverage@3 = 0.398 by RETRIEVING sentences from a paper. SJS is
  a different task on a different split: given candidate STATEMENTS, pick the one that
  supports the judgement. Same lexicon, different format, different records -- so agreement
  between the two is evidence about the lexicon rather than about one task's quirks.

NO FITTING. The lexicon is fixed, written from the Cochrane Handbook's domain definitions
before either split was scored. Neither split is training material; both are known-answer
controls. Nothing here is tuned after seeing a score.

CONTROLS, all of which must pass or the number is not reported:
  RANDOM      chance is 1/len(options) and varies per record -- it is computed, not assumed.
  MUST-FIRE   an unmistakable option must win against distractors.
  PLANT       destroy the lexicon; accuracy must fall to chance. Restore; assert recovery.
"""
import io, json, os, random, sys, collections

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import rob_provenance as RP  # noqa: E402  (its stdout reassignment is guarded)

if __name__ == "__main__":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace",
                                  line_buffering=True)

SJS = os.path.join(RP.ROBBR_DIR, "SJS_Cochrane_test.json")


def pick(options, key, cues=None):
    """Argmax over options using the SAME scorer SSR used. Deterministic tie-break on index."""
    sc = RP.score_sentences(options, key, cues)
    sc.sort(key=lambda t: (-t[1], t[0]))
    return sc[0][0] if sc else None


def evaluate(records, cues=None, seed=None):
    rnd = random.Random(seed)
    n = hit = 0
    chance = 0.0
    unmapped = 0
    per_domain = collections.defaultdict(lambda: [0, 0])
    for r in records:
        opts = r.get("options") or []
        lab = r.get("label")
        if not opts or not isinstance(lab, int) or not (0 <= lab < len(opts)):
            continue
        key = RP.domain_key(r.get("bias"))
        if key is None:
            unmapped += 1
            continue
        got = pick(opts, key, cues)
        n += 1
        ok = (got == lab)
        hit += ok
        chance += 1.0 / len(opts)
        per_domain[key][0] += ok
        per_domain[key][1] += 1
    return {"n": n, "accuracy": hit / float(n) if n else 0.0,
            "chance": chance / float(n) if n else 0.0,
            "unmapped": unmapped,
            "per_domain": {k: (v[0], v[1], v[0] / float(v[1])) for k, v in per_domain.items()}}


def main():
    if not os.path.exists(SJS):
        raise SystemExit("MISSING INPUT: %s\nSet ROBBR_DIR to the RoBBR data directory.\n"
                         "Fetch: https://huggingface.co/datasets/RoBBR-Benchmark/RoBBR "
                         "(CC-BY-NC-4.0)" % SJS)
    recs = list(json.load(io.open(SJS, encoding="utf-8")).values())
    opt_sizes = [len(r.get("options") or []) for r in recs if r.get("options")]
    print("MEASURED  SJS_Cochrane_test records: %d" % len(recs))
    print("          options per record: min %d, median %d, max %d"
          % (min(opt_sizes), sorted(opt_sizes)[len(opt_sizes) // 2], max(opt_sizes)))
    print("          cmd: python rob_provenance_sjs.py")
    print("")

    # ---------- CONTROL: MUST-FIRE ----------
    probe = ["The study was funded by a national research council.",
             "Mean baseline age was 58 years in both arms.",
             "Allocation was concealed in sequentially numbered sealed opaque envelopes.",
             "Follow-up continued for 24 months."]
    got = pick(probe, "allocation_concealment")
    ok1 = got == 2
    print("CONTROL   MUST-FIRE: unmistakable option wins -- picked %s, expected 2 -- %s"
          % (got, "PASS" if ok1 else "FAIL"))

    # ---------- the measurement ----------
    res = evaluate(recs, seed=20260902)
    print("")
    print("MEASURED  scored %d records (%d unmapped domains, named not zeroed)"
          % (res["n"], res["unmapped"]))
    print("          ACCURACY : %.3f" % res["accuracy"])
    print("          chance   : %.3f   (mean 1/len(options), computed per record)"
          % res["chance"])
    print("          LIFT     : %+.3f" % (res["accuracy"] - res["chance"]))
    print("")
    print("          per domain (correct / n / accuracy):")
    for k, (c, t, a) in sorted(res["per_domain"].items(), key=lambda x: -x[1][1]):
        print("            %-24s %3d / %3d  %.3f" % (k, c, t, a))

    # ---------- CONTROL: PLANT THE DEFECT ----------
    import re as _re
    broken = {k: _re.compile(r"(?!x)x") for k in RP.COMPILED}
    b = evaluate(recs, cues=broken, seed=20260902)
    print("")
    print("CONTROL   PLANT: lexicon destroyed -> accuracy %.3f (was %.3f), chance %.3f"
          % (b["accuracy"], res["accuracy"], b["chance"]))
    collapsed = b["accuracy"] < res["accuracy"] - 0.03
    print("          collapse observed: %s" % ("YES" if collapsed else "NO -- CHECK IS INERT"))
    r2 = evaluate(recs, seed=20260902)
    restored = abs(r2["accuracy"] - res["accuracy"]) < 1e-12
    print("          RESTORE -> %.3f -- %s" % (r2["accuracy"], "PASS" if restored else "FAIL"))

    # ---------- the cross-task comparison ----------
    print("")
    ssr = None
    if os.path.exists("rob_provenance_result.json"):
        ssr = json.load(io.open("rob_provenance_result.json", encoding="utf-8"))
    print("=== TWO INDEPENDENT SCORINGS OF THE SAME FIXED LEXICON ===")
    if ssr:
        s = ssr["k3"]
        print("  SSR retrieval  coverage@3 %.3f vs chance %.3f  (lift %+.3f, %d records)"
              % (s["coverage_at_k"], s["random_baseline"],
                 s["coverage_at_k"] - s["random_baseline"], s["n"]))
    print("  SJS selection  accuracy   %.3f vs chance %.3f  (lift %+.3f, %d records)"
          % (res["accuracy"], res["chance"], res["accuracy"] - res["chance"], res["n"]))

    allok = ok1 and collapsed and restored
    print("")
    print("VERDICT   controls %s" % ("ALL PASS" if allok else "FAILED -- number not reportable"))
    json.dump({"sjs": res, "planted": b, "controls_pass": bool(allok)},
              io.open("rob_provenance_sjs_result.json", "w", encoding="utf-8"), indent=1)
    return 0 if allok else 1


if __name__ == "__main__":
    raise SystemExit(main())
