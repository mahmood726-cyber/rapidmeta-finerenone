"""COMPARE THE TWO BLIND READINGS of the 130, and reduce them to the cases a human must read.

TWO INDEPENDENT FAMILIES, NEITHER SHOWN THE OTHER'S ANSWER OR MINE:
    Codex  (openai, GPT-5)
    agy    (google, Gemini 3.1 Pro)
Claude wrote the screener and is the instrument under test, so Claude is not a third vote here.

WHERE THEY AGREE the answer is taken and SPOT-CHECKED against a coded field rather than
re-read. WHERE THEY DIFFER the trial is listed for hand adjudication. That is the whole point
of the method: it turns 130 readings into the much smaller set where two independent instruments
actually disagree, and a disagreement is evidence about the instruments as well as the trial.

CODEX EMITTED EVERY ANSWER TWICE. Verified self-consistent -- 33 distinct NCTs, 0 answered
differently in the two copies -- so the duplicates are deduplicated rather than treated as two
votes. Counting one model's repeated answer as two votes would manufacture agreement out of
verbosity.
"""
import io
import json
import os
import re
import sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
S = ("F:/claude-temp/claude/F--rapidmeta-ssot-shell/"
     "6b629e1e-cc8c-4565-af03-e40341ee43f3/scratchpad")
SCREEN = os.path.join(REPO, "evidence", "2026-08-19-batch1", "ablation_medical_screening.json")
DEST = os.path.join(REPO, "evidence", "2026-08-19-batch1", "ablation_adjudication.json")
ANS = re.compile(r"^(NCT\d{8})\s*\|\s*A=(YES|NO|UNCLEAR)\s*\|\s*B=(YES|NO|UNCLEAR)", re.I)


def read(prefix):
    out = {}
    inconsistent = {}
    for i in ("01", "02", "03", "04"):
        p = os.path.join(S, "%s_adj_%s.txt" % (prefix, i))
        if not os.path.exists(p):
            continue
        for line in io.open(p, encoding="utf-8", errors="replace"):
            m = ANS.match(line.strip())
            if not m:
                continue
            nct, a, b = m.group(1), m.group(2).upper(), m.group(3).upper()
            if nct in out and out[nct] != (a, b):
                inconsistent[nct] = (out[nct], (a, b))
            out[nct] = (a, b)
    return out, inconsistent


def disposition(a, b):
    """(A ablation arm, B non-ablation control) -> what the pair implies for eligibility."""
    if a == "NO":
        return "EXCLUDED", "INTERVENTION", "no arm delivers atrial ablation"
    if a == "YES" and b == "NO":
        return "EXCLUDED", "COMPARATOR", ("an ablation arm, and no non-ablation control -- an "
                                          "ablation-against-ablation or single-arm design")
    if a == "YES" and b == "YES":
        return "ELIGIBLE", "P/I/C", ("an ablation arm against a non-ablation control; status "
                                     "and estimand still decide the disposition")
    return "HAND", "UNCLEAR", "at least one limb the reader could not settle"


def main():
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    codex, cx_bad = read("codex")
    agy, ag_bad = read("agy")
    todo = [r["nct"] for r in json.load(io.open(SCREEN, encoding="utf-8"))["trials"]
            if r["verdict"] == "NEEDS_ADJUDICATION"]

    print("to adjudicate            %4d" % len(todo))
    print("codex answered           %4d   (self-inconsistent: %d)" % (len(codex), len(cx_bad)))
    print("agy answered             %4d   (self-inconsistent: %d)" % (len(agy), len(ag_bad)))
    missing = [n for n in todo if n not in codex or n not in agy]
    if missing:
        print("NOT ANSWERED BY BOTH     %4d   <- NOT adjudicated; a trial no instrument read "
              "is not\n%s" % (len(missing), " " * 30 + "a trial that was decided"))

    agree, differ, hand = [], [], []
    for n in todo:
        if n not in codex or n not in agy:
            continue
        c, a = codex[n], agy[n]
        if c == a:
            d, limb, why = disposition(*c)
            (hand if d == "HAND" else agree).append((n, c, d, limb, why))
        else:
            differ.append((n, c, a))

    print()
    print("BOTH AGREE, and the pair settles it   %4d" % len(agree))
    print("BOTH AGREE, and both say UNCLEAR      %4d   <- still a hand reading" % len(hand))
    print("THEY DIFFER                           %4d   <- hand reading, and evidence about "
          "the instruments" % len(differ))

    from collections import Counter
    print("\nAGREED DISPOSITIONS")
    for k, v in Counter("%s / %s" % (d, limb) for _n, _c, d, limb, _w in agree).most_common():
        print("   %-34s %4d" % (k, v))

    print("\nDISAGREEMENTS -- codex vs agy")
    for n, c, a in differ:
        print("   %s  codex A=%s B=%s   agy A=%s B=%s" % (n, c[0], c[1], a[0], a[1]))

    out = {"adjudicated_utc": "2026-08-19",
           "method": ("two independent families read the same blind arm structures and were "
                      "asked to CLASSIFY, not to confirm. Claude wrote the screener and is the "
                      "instrument under test, so it is not a vote here."),
           "seats": {"codex": "openai GPT-5, probed live",
                     "agy": "google Gemini 3.1 Pro, probed live"},
           "n_to_adjudicate": len(todo), "n_agree": len(agree),
           "n_both_unclear": len(hand), "n_differ": len(differ),
           "n_not_answered_by_both": len(missing),
           "agreed": [{"nct": n, "codex_agy": list(c), "implies": d, "limb": limb,
                       "why": why} for n, c, d, limb, why in agree],
           "both_unclear": [{"nct": n, "answer": list(c)} for n, c, _d, _l, _w in hand],
           "disagreements": [{"nct": n, "codex": list(c), "agy": list(a)}
                             for n, c, a in differ],
           "not_answered_by_both": missing}
    with io.open(DEST, "w", encoding="utf-8") as fh:
        fh.write(json.dumps(out, indent=1))
    print("\nwrote %s" % DEST)
    print("\nHAND READINGS REQUIRED: %d  (%d disagreements + %d both-unclear)"
          % (len(differ) + len(hand), len(differ), len(hand)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
