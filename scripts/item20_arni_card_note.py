"""ARNI card note: the index must carry the endpoint-registration finding too.

The card announced the RESOLVED measure question and nothing else, which was
right on 2026-08-18 and is incomplete on 2026-08-18 after the registry read. A
reader who meets this topic on the index should learn, before opening it, that
one of the four pooled trials registers no such endpoint. The numbers on the
card do not change; they are projected from the object and the object's numbers
did not move.

USAGE  python scripts/item20_arni_card_note.py
"""
from __future__ import annotations
import io
import json
import os
import sys

if __name__ == "__main__":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
OBJ = os.path.join(ROOT, "ssot", "arni-hfref", "arni-hfref.json")

NOTE = (
    "Measure question RESOLVED 2026-08-18: ANSWER-HF’s 1.83 (0.72–4.67) "
    "IS a hazard ratio — JACC Table 2 is headed “Effect HR (95% CI)” "
    "and the Methods name Cox proportional hazard models. The trial stays in, k "
    "remains 4, no displayed value changed, and the k=3 alternative HR 0.8333 "
    "(0.7473–0.9292) is on the page as a sensitivity. ENDPOINT DEFINITIONS "
    "NOW READ FROM THE REGISTRY FOR ALL FOUR TRIALS, and three of the four agree "
    "exactly — PARADIGM-HF and PARALLEL-HF register this composite as their "
    "primary, PARACHUTE-HF as its first secondary. ANSWER-HF REGISTERS NO SUCH "
    "ENDPOINT AT ANY RANK: NCT04853758 declares two primary and eighteen "
    "secondary outcome measures and none is this composite, so a quarter of the "
    "pool rests on a quantity that appears only in a publication. It is disclosed "
    "and NOT removed — removing it would turn a null into a positive result, "
    "and a withdrawal needs the same evidence as a claim."
)


def main():
    with io.open(OBJ, encoding="utf-8") as fh:
        obj = json.load(fh)
    pooled = obj["results"]["by_outcome"]["cvdeath_or_hfh_first"]["pooled"]
    if pooled.get("card_note") == NOTE:
        print("card_note already current -- nothing written")
        return 0
    pooled["card_note_superseded_2026_08_18"] = pooled.get("card_note")
    pooled["card_note"] = NOTE
    with io.open(OBJ, "w", encoding="utf-8") as fh:
        json.dump(obj, fh, ensure_ascii=False, indent=1)
        fh.write("\n")
    print("card_note rewritten (%d chars); previous note kept as "
          "card_note_superseded_2026_08_18" % len(NOTE))
    return 0


if __name__ == "__main__":
    sys.exit(main())
