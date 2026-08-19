"""BLIND ADJUDICATION PACKET for the 352 the rhythm-control screener could not settle.

THE CORRECTED QUESTION FORM, CARRIED OVER DELIBERATELY (P27). The first adjudication of this
project's history asked what an arm CONTAINS and produced 47.7% agreement that was largely a
measurement of the question's ambiguity. This asks WHAT DIFFERS BETWEEN THE ARMS, and it adds
the two codes THIS topic needs that the sibling's did not:

    RHYTHM_BOTH_ARMS      every arm gets some rhythm-control treatment and what differs is
                          WHICH KIND -- the head-to-head shape, 97 trials by the screener's
                          own count, and the cell that needs a criteria judgement rather than
                          a rule
    CONTRAST_RATE_OR_NODAL  what differs is RATE control, including AV-node ablation, which is
                          rate control delivered by ablation

Neither is expressible in the sibling's vocabulary, and asking this topic's trials in the
sibling's terms is the contamination route recorded this session as route 7.

The packet contains ONLY registry arm structures: no verdict, no disposition vocabulary, no
criteria, not the word "excluded", and no hint these 352 are the residue of anything.
"""
import io
import json
import os
import sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(REPO, "ssot"))
os.environ.setdefault(
    "RM_CTGOV_CACHE",
    "F:/claude-temp/claude/F--rapidmeta-ssot-shell/"
    "eb4d84e5-8a24-4c3b-afe2-34bd91c20bc7/scratchpad/.ctgov-raw-cache")

import ctgov_transport as X          # noqa: E402

SCREEN = os.path.join(REPO, "evidence", "2026-08-19-batch1", "rhythm_control_screening.json")
OUT_DIR = ("F:/claude-temp/claude/F--rapidmeta-ssot-shell/"
           "6b629e1e-cc8c-4565-af03-e40341ee43f3/scratchpad")

TASK = """You are reading registered clinical trial arm structures from ClinicalTrials.gov.
All are trials in atrial fibrillation.

For EACH trial, answer ONE question: WHAT DIFFERS BETWEEN THE ARMS?

Do not ask what any arm contains. Ask what the randomisation actually varies. A treatment
present in EVERY arm is background and is NOT what differs, however prominent it is.

Background you need: RHYTHM CONTROL means trying to restore or maintain normal sinus rhythm --
by antiarrhythmic drugs (amiodarone, flecainide, propafenone, dronedarone, sotalol,
dofetilide), by electrical cardioversion, or by catheter ablation of the atria (pulmonary vein
isolation, radiofrequency, cryoballoon, pulsed-field). RATE CONTROL means leaving the
fibrillation and slowing the ventricle -- beta blockers, diltiazem, verapamil, digoxin, or
ablation of the AV node / AV junction with a pacemaker.

Choose exactly one code per trial:

  CONTRAST_RHYTHM       A rhythm-control treatment is what differs: at least one arm receives
                        one and at least one arm does not.
  RHYTHM_BOTH_ARMS      Every arm receives some rhythm-control treatment, and what differs is
                        WHICH KIND (for example ablation against antiarrhythmic drugs, or one
                        ablation technique against another).
  RHYTHM_IN_ALL_ADJUNCT Every arm receives the SAME rhythm-control treatment and something
                        ELSE is what differs -- sedation, imaging, a device used during the
                        procedure, monitoring, follow-up care, an added drug.
  CONTRAST_RATE         What differs is RATE control, including AV-node or AV-junction
                        ablation with a pacemaker.
  CONTRAST_OTHER        No arm receives any rhythm-control treatment; something else entirely
                        is what differs.
  UNCLEAR               The arm data genuinely does not say.

Then, only if you chose CONTRAST_RHYTHM, answer what it is compared AGAINST:
  CONTROL= RATE (rate-control drugs or AV-node ablation), USUAL (usual/standard/conventional
           care or no treatment), OTHER (some other procedure or device), or UNCLEAR.
  Otherwise write CONTROL=NA.

Output EXACTLY one line per trial, no commentary:
NCTxxxxxxxx | CODE | CONTROL=...

UNCLEAR is a correct and expected answer. Do not guess to avoid it.
"""


def main():
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    rows = json.load(io.open(SCREEN, encoding="utf-8"))["trials"]
    todo = [r["nct"] for r in rows if r["verdict"] == "NEEDS_ADJUDICATION"]
    print("to adjudicate: %d" % len(todo))

    blocks = []
    for nct in todo:
        st, study, det = X.fetch_raw(nct, fields="protocolSection,hasResults")
        if st != X.OK:
            continue
        p = X.require_raw_v2(study, nct)["protocolSection"]
        arms = (p.get("armsInterventionsModule") or {}).get("armGroups") or []
        lines = [nct]
        for a in arms:
            names = "; ".join(str(n) for n in (a.get("interventionNames") or [])) or "(none)"
            lines.append("    [%s] %s -- %s"
                         % (a.get("type") or "?", a.get("label") or "?", names))
        blocks.append("\n".join(lines))

    os.makedirs(OUT_DIR, exist_ok=True)
    CHUNK = 44
    n = 0
    for i in range(0, len(blocks), CHUNK):
        part = blocks[i:i + CHUNK]
        text = TASK + "\n" + "\n\n".join(part) + "\n"
        path = os.path.join(OUT_DIR, "rhythm_packet_%02d.txt" % (i // CHUNK + 1))
        with io.open(path, "w", encoding="utf-8") as fh:
            fh.write(text)
        n += 1
        print("   wrote rhythm_packet_%02d.txt (%d trials, %d chars)"
              % (i // CHUNK + 1, len(part), len(text)))
    with io.open(os.path.join(OUT_DIR, "rhythm_ids.json"), "w", encoding="utf-8") as fh:
        fh.write(json.dumps(todo, indent=1))
    print("\n%d chunks, identical to both seats." % n)
    return 0


if __name__ == "__main__":
    sys.exit(main())
