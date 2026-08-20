"""Arm roles that the object's OWN other fields contradict. No registration needed.

`attr-pn-review` records inotersen as NEURO-TTRansform's treatment arm and eplontersen as
its control, which the registration reverses. Establishing THAT required reading
NCT04136184, and reading a registration per trial does not scale to a corpus.

THIS FILE ASKS ONLY WHAT THE OBJECT CAN ANSWER ABOUT ITSELF. Every finding here is provable
from two fields of the same object disagreeing, which is why none of them is a judgement
call and none of them needs a source outside the repository.

    A  A TREATMENT ARM WHOSE LABEL IS A PLACEBO.
       `evolocumab-mixed-dyslipidemia-auto-full-review`, HUA TUO (NCT03433755):
           treatment  "Placebo Q2W"
           control    "Evolocumab 420 mg QM"
       A placebo is not an intervention. The roles are inverted, and if the effect was
       stored in the direction the roles imply, ITS SIGN IS INVERTED TOO.

    B  A TRIAL NAME THAT NAMES A COMPARATOR THE ARMS DO NOT.
       `rosuvastatin-auto-full-review`, HOPE-3 (NCT00468923):
           name       "HOPE-3 (rosuvastatin 10 mg vs placebo)"
           control    "Candesartan/HCT"
       HOPE-3 was 2x2 factorial and the arm recorded is the ANTIHYPERTENSIVE factor, not
       the lipid one. The object's own name says which comparison it meant.
       `hepatitis-b-taf-tdf-review`, both trials:
           name       "GS-US-320-0108 (TAF vs TDF, HBeAg-negative)"
           control    "Open-label TAF"
       TDF appears nowhere in either row. A pool described as TAF against TDF is recorded
       as TAF against TAF.

    C  BOTH ARMS NAMING THE SAME AGENT WITH NO PLACEBO ANYWHERE.
       `netarsudil-ocular-hypertension-auto-full-review`, ROCKET-2 (NCT02207621):
           treatment  "AR-13324 Ophthalmic Solution 0.02% & pla"
           control    "AR-13324 Ophthalmic Solution 0.02% BID"
       A dose-or-schedule contrast sitting beside two netarsudil-against-timolol rows. The
       treatment label is also truncated mid-word, which is its own defect.

WHAT THIS FILE DOES NOT DO. It does not correct anything. A role swap changes what the
object says a trial DID, and on two of these topics the stored effect's sign depends on the
roles. Correcting from inference is the error `attr-pn` was written up to avoid: there the
labels looked obvious from the drug names and the registration turned out to say something
sharper still -- that the stored value was not the randomised contrast at all.

IT ALSO REPORTS THREE STATES, NOT TWO. A trial with no arms is UNREAD, not clean; 241
contributing trials across the corpus carry none.
"""
import io
import json
import os
import re
import sys
import glob

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# C ROUTES THROUGH THE SAME DRUG RECOGNISER AS audit_mixed_contrast_pools RATHER THAN
# THROUGH BARE WORD OVERLAP. Word overlap flagged three `intensive-bp-review` rows on the
# shared token "BP" -- "Intensive BP control" against "Standard BP control" is a STRATEGY
# contrast, correctly labelled, and calling it a mislabelled drug row is an accusation in
# the wrong direction. A shared token has to be a DRUG for C to mean anything.
from audit_mixed_contrast_pools import real_tokens as drug_tokens
from audit_mixed_contrast_pools import CARE

PLACEBO = re.compile(r"placebo|saline|sham|vehicle|alum-only|dummy", re.I)
# "X vs Y" or "X versus Y" inside a trial name.
VS = re.compile(r"\b(?:vs\.?|versus)\s+([a-z0-9][a-z0-9 /+-]{2,40})", re.I)
WORD = re.compile(r"[a-z][a-z0-9-]{1,}", re.I)

STOP = set(["placebo", "control", "comparator", "group", "arm", "arms", "dose", "daily",
            "twice", "once", "with", "plus", "alone", "usual", "care", "standard", "open",
            "label", "solution", "ophthalmic", "week", "weeks", "month", "months",
            "matching", "treatment", "therapy", "intensive", "mg", "g", "of", "the", "and",
            "or", "in", "vs", "versus", "bid", "qd", "qm", "q2w", "ow", "sc", "iv", "po",
            "study", "trial", "phase", "high", "low", "target"])


def words(text):
    return set(w.lower() for w in WORD.findall(text or "") if w.lower() not in STOP)


def main():
    verbose = "--verbose" in sys.argv
    a_hits, b_hits, c_hits = [], [], []
    trials_seen = 0
    trials_unread = 0
    topics = 0

    for path in sorted(glob.glob(os.path.join(REPO, "ssot", "*", "*.json"))):
        topic = os.path.basename(os.path.dirname(path))
        if os.path.basename(path) != topic + ".json":
            continue
        try:
            obj = json.load(io.open(path, encoding="utf-8"))
        except Exception:
            continue
        trials = (obj.get("inputs") or {}).get("trials")
        if not isinstance(trials, list):
            continue
        topics += 1
        for t in trials:
            nct = t.get("nct") or t.get("trial_id") or t.get("id") or "?"
            name = str(t.get("name") or "")
            arms = t.get("arms") or []
            if not arms:
                trials_unread += 1
                continue
            trials_seen += 1
            treats = [str(a.get("label") or "") for a in arms
                      if a.get("role") == "treatment"]
            ctrls = [str(a.get("label") or "") for a in arms if a.get("role") == "control"]
            if not treats or not ctrls:
                trials_unread += 1
                continue

            # A -- a treatment arm that is a placebo, and a control arm that is not.
            for lab in treats:
                if PLACEBO.search(lab) and not any(PLACEBO.search(c) for c in ctrls):
                    a_hits.append((topic, nct, lab, " / ".join(ctrls)))

            # B -- the name names a comparator the control arm does not carry.
            for m in VS.finditer(name):
                have = set()
                for c in ctrls:
                    have |= words(c)
                if PLACEBO.search(m.group(1)):
                    # The name says the comparator was a placebo.
                    if any(PLACEBO.search(c) for c in ctrls):
                        continue
                    b_hits.append((topic, nct, name, " / ".join(ctrls),
                                   "a placebo, and no control arm is one"))
                    break
                named = words(m.group(1))
                if not named:
                    continue
                if not (named & have):
                    b_hits.append((topic, nct, name, " / ".join(ctrls),
                                   ", ".join(sorted(named))))
                    break

            # C -- both arms name the same agent and nothing is a placebo.
            if any(PLACEBO.search(x) for x in treats + ctrls):
                continue
            # A DECLARED STRATEGY CONTRAST IS NOT A MISLABELLING. cryptococcal-meningitis's
            # COAT row gives both arms antiretroviral therapy and says so in the label --
            # "started four weeks after randomisation ... the trial's control strategy".
            # The shared drug is the POINT of that comparison, not evidence against it.
            if any(CARE.search(c) for c in ctrls):
                continue
            shared = set()
            for c in ctrls:
                for tr in treats:
                    shared |= (drug_tokens(c)[0] & drug_tokens(tr)[0])
            if shared:
                cs = set()
                for c in ctrls:
                    cs |= drug_tokens(c)[0]
                if cs and cs <= shared:
                    c_hits.append((topic, nct, " / ".join(treats), " / ".join(ctrls),
                                   ", ".join(sorted(shared))))

    print("ARM ROLES CONTRADICTED BY THE OBJECT'S OWN FIELDS")
    print("%d topics, %d trials with both roles readable, %d UNREAD (no arms or one role "
          "only)" % (topics, trials_seen, trials_unread))
    print("UNREAD IS NOT CLEAN. Nothing below was asked of those %d." % trials_unread)

    print("")
    print("A -- A TREATMENT ARM WHOSE LABEL IS A PLACEBO (%d)" % len(a_hits))
    print("    A placebo is not an intervention. If the effect was stored in the direction")
    print("    these roles imply, its SIGN IS INVERTED.")
    for topic, nct, lab, ctrl in a_hits:
        print("    %s  %s" % (topic, nct))
        print("        treatment %r  control %r" % (lab, ctrl))

    print("")
    print("B -- THE TRIAL NAME NAMES A COMPARATOR THE CONTROL ARM DOES NOT (%d)"
          % len(b_hits))
    for topic, nct, name, ctrl, named in b_hits:
        print("    %s  %s" % (topic, nct))
        print("        name    %r" % name)
        print("        control %r  -- the name says %s" % (ctrl, named))

    print("")
    print("C -- BOTH ARMS NAME THE SAME AGENT AND NEITHER IS A PLACEBO (%d)" % len(c_hits))
    print("    A dose, schedule or duration contrast -- or a mislabelling. Either way it is")
    print("    not a drug-against-comparator row and must not be pooled with ones that are.")
    for topic, nct, tr, ctrl, shared in c_hits:
        print("    %s  %s   [%s in both]" % (topic, nct, shared))
        print("        treatment %r" % tr)
        print("        control   %r" % ctrl)

    total = len(a_hits) + len(b_hits) + len(c_hits)
    print("")
    print("%d contradictions across %d readable trials. NOTHING IS CORRECTED HERE -- a role "
          "swap" % (total, trials_seen))
    print("changes what the object says a trial did, and on the sign-bearing ones that is a")
    print("published-number decision.")


if __name__ == "__main__":
    main()
