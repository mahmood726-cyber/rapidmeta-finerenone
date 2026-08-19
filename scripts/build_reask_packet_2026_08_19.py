"""RE-ASK the 45 unresolved trials with the CORRECTED question.

WHAT CHANGED, AND WHY THE OLD ANSWERS ARE NOT REUSED.

The first packet asked, of each trial, "does any arm DELIVER catheter ablation" -- the
discarded form of a question this project reframed hours earlier. For a trial of sedation
during an ablation, or metformin after one, the honest answer to that is YES: every arm
delivers an ablation. Which is exactly what makes the ablation BACKGROUND and the adjunct the
contrast.

    THE QUESTION NOW ASKED IS "WHAT DIFFERS BETWEEN THE ARMS" -- the same reframing that
    dissolved two defects in topic_identity.locate(). P27.

Because the old question was ambiguous, the 45 unresolved answers to it are DISCARDED rather
than reconciled. Reconciling answers to an ambiguous question preserves the ambiguity inside a
number that then looks settled.

THE 45 ARE: 43 where the two seats gave different answers with at least one UNCLEAR, and 2
where both said UNCLEAR. The 25 hard contradictions are NOT re-asked -- they were hand-read
from armGroups and all 25 are excluded, and a hand reading of the arms does not depend on how
the question to a model was phrased.
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

ADJ = os.path.join(REPO, "evidence", "2026-08-19-batch1", "ablation_adjudication.json")
HARD = os.path.join(REPO, "evidence", "2026-08-19-batch1", "ablation_hard_adjudication.json")
OUT_DIR = ("F:/claude-temp/claude/F--rapidmeta-ssot-shell/"
           "6b629e1e-cc8c-4565-af03-e40341ee43f3/scratchpad")

TASK = """You are reading registered clinical trial arm structures from ClinicalTrials.gov.

For EACH trial, answer ONE question: WHAT DIFFERS BETWEEN THE ARMS?

Do not ask what any arm contains. Ask what the randomisation actually varies. A treatment
present in EVERY arm is background and is NOT what differs, however prominent it is.

Choose exactly one code per trial:

  CONTRAST_ABLATION   Catheter ablation of atrial fibrillation (pulmonary vein isolation,
                      radiofrequency, cryoballoon, pulsed-field, laser) is what differs: at
                      least one arm receives it and at least one arm does not.
  ABLATION_IN_ALL     Every arm receives an atrial ablation, and something ELSE is what
                      differs -- sedation, imaging, a drug, a device used during the
                      procedure, monitoring, follow-up care, anything.
  ABLATION_VS_ABLATION  Every arm receives an atrial ablation and what differs is the
                      ablation TECHNIQUE, technology or lesion set.
  CONTRAST_NODAL      What differs is ablation of the AV node / AV junction / His bundle
                      (rate control by ablating the conduction system, usually with a
                      pacemaker), not atrial ablation.
  CONTRAST_SURGICAL   What differs is a SURGICAL or thoracoscopic ablation performed during
                      cardiac surgery.
  CONTRAST_OTHER      No arm receives an atrial catheter ablation at all; something else
                      entirely is what differs.
  UNCLEAR             The arm data genuinely does not say.

Then answer one more thing, only if you chose CONTRAST_ABLATION:
  CONTROL= the kind of arm the ablation is compared AGAINST -- DRUG (any medication, rate or
           rhythm control), USUAL (usual/standard/conventional care or no treatment),
           OTHER (some other procedure or device), or UNCLEAR.
  If you did not choose CONTRAST_ABLATION, write CONTROL=NA.

Output EXACTLY one line per trial, no commentary:
NCTxxxxxxxx | CODE | CONTROL=...

UNCLEAR is a correct and expected answer. Do not guess to avoid it.
"""


def main():
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    adj = json.load(io.open(ADJ, encoding="utf-8"))
    hard_done = {r["nct"] for r in json.load(io.open(HARD, encoding="utf-8"))["trials"]}
    todo = [r["nct"] for r in adj["disagreements"] if r["nct"] not in hard_done]
    todo += [r["nct"] for r in adj["both_unclear"]]
    todo = sorted(set(todo))
    print("re-asking %d trials (43 soft disagreements + 2 both-unclear)" % len(todo))
    print("NOT re-asked: %d hard contradictions, hand-read from armGroups" % len(hard_done))

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
    CHUNK = 23
    for i in range(0, len(blocks), CHUNK):
        part = blocks[i:i + CHUNK]
        text = TASK + "\n" + "\n\n".join(part) + "\n"
        path = os.path.join(OUT_DIR, "reask_packet_%02d.txt" % (i // CHUNK + 1))
        with io.open(path, "w", encoding="utf-8") as fh:
            fh.write(text)
        print("   wrote %s (%d trials, %d chars)" % (path, len(part), len(text)))
    with io.open(os.path.join(OUT_DIR, "reask_ids.json"), "w", encoding="utf-8") as fh:
        fh.write(json.dumps(todo, indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main())
