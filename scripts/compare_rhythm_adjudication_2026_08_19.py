"""COMPARE the two blind readings of the 352, at BOTH rates.

TWO RATES BECAUSE THEY ANSWER TWO QUESTIONS.

    CODE rate         how consistently two instruments DESCRIBE a design
    DISPOSITION rate  how consistently they SCREEN it

The sibling's run showed the gap matters: 66.7% on codes and 80.0% on dispositions, because
ABLATION_IN_ALL and ABLATION_VS_ABLATION are two readings of WHY a trial is out and both mean
EXCLUDED. A disagreement about the reason is not a disagreement about the verdict, and
conflating them understates agreement exactly where P15 says reason and verdict are separate
outputs.

THIS TOPIC ADDS A CODE THAT IS NOT A RESIDUAL CATEGORY. `RHYTHM_BOTH_ARMS` names the 97
head-to-head trials the screener found -- every arm gets some rhythm control and what differs
is which kind. It maps to NEEDS_CRITERIA rather than to EXCLUDED, because CABANA is one of
them and CABANA IS IN THE INCLUDED SET. Naming the cell is what stops those trials being
silently excluded on a limb they do not actually fail.
"""
import io
import json
import os
import re
import sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
S = ("F:/claude-temp/claude/F--rapidmeta-ssot-shell/"
     "6b629e1e-cc8c-4565-af03-e40341ee43f3/scratchpad")
DEST = os.path.join(REPO, "evidence", "2026-08-19-batch1", "rhythm_adjudication.json")

CODES = ("CONTRAST_RHYTHM", "RHYTHM_BOTH_ARMS", "RHYTHM_IN_ALL_ADJUNCT", "CONTRAST_RATE",
         "CONTRAST_OTHER", "UNCLEAR")
LINE = re.compile(r"^(NCT\d{8})\s*\|?\s*([A-Z_]+)\s*\|?\s*CONTROL\s*=\s*([A-Z]+)", re.I)

IMPLIES = {
    "CONTRAST_RHYTHM": ("ELIGIBLE", "rhythm control is what the randomisation varies"),
    "RHYTHM_BOTH_ARMS": ("NEEDS_CRITERIA",
                         "head-to-head: every arm gets rhythm control and what differs is "
                         "which kind. CABANA is this shape and IS included, so the cell is a "
                         "criteria judgement and NOT an exclusion"),
    "RHYTHM_IN_ALL_ADJUNCT": ("EXCLUDED",
                              "every arm gets the same rhythm-control treatment; the contrast "
                              "is the adjunct"),
    "CONTRAST_RATE": ("EXCLUDED", "what differs is rate control, incl. AV-node ablation"),
    "CONTRAST_OTHER": ("EXCLUDED", "no arm receives rhythm-control treatment"),
    "UNCLEAR": ("HAND", "the arm data does not say"),
}


def read(prefix, n_chunks=8):
    out = {}
    for i in range(1, n_chunks + 1):
        p = os.path.join(S, "%s_rhythm_%02d.txt" % (prefix, i))
        if not os.path.exists(p):
            continue
        for line in io.open(p, encoding="utf-8", errors="replace"):
            m = LINE.match(line.strip())
            if not m:
                continue
            code = m.group(2).upper()
            if code in CODES:
                out[m.group(1)] = (code, m.group(3).upper())
    return out


def main():
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    todo = json.load(io.open(os.path.join(S, "rhythm_ids.json"), encoding="utf-8"))
    codex, agy = read("codex"), read("agy")
    print("to adjudicate   %4d" % len(todo))
    print("codex answered  %4d" % len(codex))
    print("agy answered    %4d" % len(agy))
    missing = [n for n in todo if n not in codex or n not in agy]
    if missing:
        print("NOT ANSWERED BY BOTH %d -- NOT adjudicated. A trial no instrument read is not a"
              "\n   trial that was decided." % len(missing))

    agree, differ = [], []
    for n in todo:
        if n not in codex or n not in agy:
            continue
        if codex[n][0] == agy[n][0]:
            agree.append((n, codex[n]))
        else:
            differ.append((n, codex[n], agy[n]))
    n_cmp = len(agree) + len(differ)
    if not n_cmp:
        print("\nNOT_ASSESSABLE: no trial was answered by both seats.")
        return 1

    code_rate = 100.0 * len(agree) / n_cmp
    same_disp, real_diff = [], []
    for n, c, a in differ:
        if IMPLIES[c[0]][0] == IMPLIES[a[0]][0]:
            same_disp.append((n, c, a))
        else:
            real_diff.append((n, c, a))
    disp_rate = 100.0 * (len(agree) + len(same_disp)) / n_cmp

    print("\nAGREE ON THE CODE          %4d / %d   (%.1f%%)" % (len(agree), n_cmp, code_rate))
    print("AGREE ON THE DISPOSITION   %4d / %d   (%.1f%%)"
          % (len(agree) + len(same_disp), n_cmp, disp_rate))
    print("   of which same verdict, different reason: %d" % len(same_disp))
    print("DISPOSITION ACTUALLY DIFFERS %4d   <- the real judgements" % len(real_diff))

    from collections import Counter
    print("\nAGREED CODES")
    for k, v in Counter(c[0] for _n, c in agree).most_common():
        d, why = IMPLIES[k]
        print("   %-24s %4d  -> %s" % (k, v, d))

    resolved = [(n, c) for n, c in agree if IMPLIES[c[0]][0] not in ("HAND", "NEEDS_CRITERIA")]
    criteria = [(n, c) for n, c in agree if IMPLIES[c[0]][0] == "NEEDS_CRITERIA"]
    hand = [(n, c) for n, c in agree if IMPLIES[c[0]][0] == "HAND"]
    print("\nRESOLVED BY AGREEMENT        %4d" % len(resolved))
    print("HEAD-TO-HEAD, needs criteria %4d   <- NOT an exclusion; CABANA is this shape"
          % len(criteria))
    print("BOTH UNCLEAR                 %4d   <- hand reading" % len(hand))
    print("DISPOSITION DIFFERS          %4d   <- hand reading" % len(real_diff))

    out = {"adjudicated_utc": "2026-08-19", "topic": "early-rhythm-control-af",
           "n": n_cmp, "n_agree_code": len(agree),
           "code_agreement_rate_pct": round(code_rate, 1),
           "n_agree_disposition": len(agree) + len(same_disp),
           "disposition_agreement_rate_pct": round(disp_rate, 1),
           "same_verdict_different_reason": len(same_disp),
           "not_answered_by_both": missing,
           "code_meanings": {k: {"disposition": v[0], "why": v[1]}
                             for k, v in IMPLIES.items()},
           "resolved": [{"nct": n, "code": c[0], "control": c[1]} for n, c in resolved],
           "head_to_head_needs_criteria": [{"nct": n, "code": c[0]} for n, c in criteria],
           "both_unclear": [n for n, _c in hand],
           "disposition_differs": [{"nct": n, "codex": list(c), "agy": list(a)}
                                   for n, c, a in real_diff],
           "same_verdict_different_reason_rows": [
               {"nct": n, "codex": list(c), "agy": list(a)} for n, c, a in same_disp]}
    with io.open(DEST, "w", encoding="utf-8") as fh:
        fh.write(json.dumps(out, indent=1))
    print("\nwrote %s" % DEST)
    return 0


if __name__ == "__main__":
    sys.exit(main())
