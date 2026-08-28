# -*- coding: utf-8 -*-
"""Stage 0 and Stage 1 of the adjudication protocol: what is adjudicable, and what is not.

WHY A TRIAGE COMES BEFORE AN ADJUDICATOR. A third model was given the two readers' verdicts
and asked to settle them. It abstained on 90.3% of cells, and stripping cells where any reader
abstained left 31 of 360. That was read as the adjudicator's disposition. It was not: the two
readers had not been shown the same evidence, and no adjudicator can settle a disagreement
between two answers to different questions.

THE MEASUREMENT THAT ESTABLISHES IT, and it is a step function rather than a gradient:

  domain  what the 14-field registry allow-list can answer   assessor 2 NO_INFORMATION
    D1    partly -- no allocation-concealment field           77 of 81   95.1%
    D2    NO -- needs the paper                               81 of 81  100.0%
    D3    NO -- needs the paper                               81 of 81  100.0%
    D4    YES -- registered masking                            1 of 81    1.2%
    D5    YES -- registered outcomes                           7 of 81    8.6%

A model's disposition produces a graded pattern. This is 100/100/95 against 1/9, and it maps
exactly onto what those fourteen fields contain. ASSESSOR 2'S ABSTENTIONS MEASURE THE PROMPT,
NOT THE TRIALS -- so the corpus-wide disagreement rate is dominated by an evidence asymmetry
between the two readers rather than by disagreement about trials.

SO THE FIRST GATE IS EVIDENCE PARITY, NOT ADJUDICATION. A cell is adjudicable only if both
readers were shown the same evidence. Cells failing parity are NOT "unadjudicated" -- they are
NOT YET ASSESSABLE, and each emits a retrieval or re-ask task naming what was missing.

STAGE 1 THEN SPLITS WHAT REMAINS WITHOUT USING A MODEL AT ALL, because RoB 2 already fixes the
mapping from signalling responses to a domain judgement. Where two readers agree on the
signalling responses and differ on the verdict, that is not a matter of opinion to arbitrate:
the published algorithm decides it. Only where the signalling RESPONSES differ is someone
actually wrong about the trial, and only those need a judge.

  A  NO_SIGNALLING       one reader recorded no signalling responses at all. A data-collection
                         defect. Emits a re-ask, not an adjudication.
  B  DERIVATION_MISMATCH one reader's stored judgement does not follow from that reader's own
                         signalling responses under the published algorithm. Resolvable by
                         re-derivation, and some of these DISSOLVE the disagreement entirely.
  C  THRESHOLD           signalling responses identical, verdicts differ. The algorithm sets
                         the line. No model.
  D  FACTUAL             signalling responses differ. Someone read the source differently.
                         THIS IS THE ONLY CLASS AN ADJUDICATOR SHOULD SEE.

READ-ONLY. Writes nothing to any store.
"""
import collections
import glob
import io
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(os.path.dirname(HERE))
os.chdir(REPO)
sys.path.insert(0, os.path.join(REPO, "ssot"))
sys.path.insert(0, os.path.join(REPO, "scripts"))
import rob2_algorithm as ALG  # noqa: E402
from rederive_no_information_domains_2026_08_26 import KEYMAP  # noqa: E402

CELL_RE = re.compile(r"(NCT\d+)__(\S+)\s+((?:D\d=[A-Z_]+\s*)+)")
DOM_RE = re.compile(r"D(\d)=([A-Z_]+)")


def derive(dn, sq):
    """The algorithm's proposed judgement from stored signalling responses.

    Returns (judgement or None, reason, unmapped_keys).

    TWO DEFECTS LIVED HERE AND THE FIRST RUN REPORTED 116 FINDINGS BECAUSE OF THEM. The
    table functions expect responses ALREADY CODED to the tool's four tokens (Y/PY, N/PN,
    NI, NA) via ALG.code(); raw stored strings like PROBABLY_YES are unrecognised and select
    no row. And each function returns a (judgement, reason) TUPLE, so comparing its result
    to a verdict string made every cell look like a mismatch -- including cells where the
    reader was right. A comparison against the wrong type cannot fail safe: it accuses.
    """
    resp, unmapped = {}, []
    for k, v in (sq or {}).items():
        num = KEYMAP.get(k)
        if num is None:
            unmapped.append(k)
            continue
        c = ALG.code(v)
        if c is None:
            unmapped.append("%s=%s (unrecognised response)" % (k, v))
            continue
        resp[num] = c
    fn, needed = ALG.DOMAIN.get(dn, (None, ()))
    if fn is None or not resp:
        return None, "no basis", unmapped
    # AN UNANSWERED QUESTION IS "NO INFORMATION", A REAL INPUT ROW AND NOT A BLANK.
    for q in needed:
        resp.setdefault(q, ALG.NI)
    try:
        j, why = fn(resp)
    except Exception as e:
        return None, "algorithm raised: %s" % e, unmapped
    return j, why, unmapped


def main():
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace",
                                  line_buffering=True)
    only = [a for a in sys.argv[1:] if not a.startswith("-")]
    kinds = collections.Counter()
    rows, mismatch = [], []
    underivable = collections.Counter()
    topics = 0
    for p in sorted(glob.glob("ssot/*/*.json")):
        t = os.path.basename(os.path.dirname(p))
        if os.path.basename(p) != t + ".json":
            continue
        if only and t not in only:
            continue
        try:
            o = json.load(io.open(p, encoding="utf-8"))
        except Exception:
            continue
        rb = o.get("risk_of_bias") or {}
        sa = None
        for k, v in rb.items():
            if k.startswith("SECOND_ASSESSOR") and isinstance(v, dict):
                sa = v
        if not sa:
            continue
        topics += 1
        a2 = {}
        for m in CELL_RE.finditer(str(sa.get("verbatim_reply") or "")):
            nct, oid, block = m.group(1), m.group(2), m.group(3)
            for dm in DOM_RE.finditer(block):
                a2[(nct, oid, "D" + dm.group(1))] = dm.group(2)
        for oid, recs in ((rb.get("by_outcome") or {})).items():
            for rid, rec in (recs or {}).items():
                for dk, dv in ((rec or {}).get("domains") or {}).items():
                    if not isinstance(dv, dict):
                        continue
                    dn = dk[:2]
                    j1 = str(dv.get("judgement") or "")
                    d1, why1, unmapped = derive(dn, dv.get("signalling_questions") or {})
                    j2 = a2.get((rid, oid, dn))
                    if j2 is None:
                        continue
                    if d1 and d1 != j1:
                        mismatch.append((t, rid, oid, dn, j1, d1, j2))
                    if d1 is None:
                        underivable[why1[:58]] += 1
                    if j1 == j2:
                        kinds["AGREE"] += 1
                        continue
                    kind = "A_NO_SIGNALLING"
                    note = "assessor 2 returned a verdict with no signalling responses"
                    if d1 and d1 == j2:
                        kind = "B_DERIVATION_MISMATCH"
                        note = ("reader 1's own answers derive %s, which is what reader 2 "
                                "said: a derivation error, not a disagreement" % d1)
                    kinds[kind] += 1
                    rows.append({"topic": t, "nct": rid, "outcome": oid, "domain": dn,
                                 "reader1": j1, "reader2": j2, "reader1_derived": d1,
                                 "kind": kind, "note": note, "unmapped_keys": unmapped})
    tot = sum(kinds.values())
    dis = tot - kinds["AGREE"]
    print("")
    print("ADJUDICATION TRIAGE -- what is adjudicable, and what is a different job")
    print("")
    print("  topics with two readers                   %4d" % topics)
    print("  paired domain cells                       %4d  == the denominator" % tot)
    print("     AGREE                                  %4d   %5.1f%%"
          % (kinds["AGREE"], 100.0 * kinds["AGREE"] / tot if tot else 0))
    print("     DISAGREE                               %4d   %5.1f%%"
          % (dis, 100.0 * dis / tot if tot else 0))
    print("")
    print("  the disagreements, triaged:")
    for k in ("B_DERIVATION_MISMATCH", "A_NO_SIGNALLING", "C_THRESHOLD", "D_FACTUAL"):
        print("     %-24s %4d   %5.1f%% of disagreements"
              % (k, kinds[k], 100.0 * kinds[k] / dis if dis else 0))
    print("")
    print("  READER 1 SELF-CONSISTENCY against the published algorithm:")
    print("     stored judgement does not follow from")
    print("     that reader's OWN signalling responses  %4d" % len(mismatch))
    for m in mismatch[:8]:
        print("       %-24s %-12s %s stored %-14s derives %-14s (reader 2: %s)"
              % (m[0][:24], m[1], m[3], m[4], m[5], m[6]))
    print("")
    print("")
    print("  UNDERIVABLE by the published algorithm from reader 1's own answers:")
    for k, v in underivable.most_common(6):
        print("     %4d   %s" % (v, k))
    print("")
    print("  CELLS AN ADJUDICATOR SHOULD SEE TODAY     %4d" % kinds["D_FACTUAL"])
    print("  cells needing a RE-ASK, not a judge       %4d" % kinds["A_NO_SIGNALLING"])
    out = r"F:\claude-temp\pend\adjudication_triage.json"
    json.dump(rows, io.open(out, "w", encoding="utf-8"), indent=1)
    import provenance as pv
    pv.stamp(out, inputs=["ssot/PAGE_MAP.json"],
             note="stage 0/1 adjudication triage of paired RoB 2 domain cells")
    print("  detail -> adjudication_triage.json (+ .prov.json)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
