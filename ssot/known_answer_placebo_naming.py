#!/usr/bin/env python3
"""Known-answer test for placebo-naming identity and the two absence states.

EVERY STRING BELOW IS A REAL INTERVENTION-RECORD NAME, taken from ClinicalTrials.gov payloads
cached in this repository, with the registration that carries it named beside it. None was
invented. A fixture an author writes tests the author's belief about the corpus; this file
exists because that lesson is already recorded here under detector 10.

THE QUESTION ASKED IS NOT "is this record a placebo". It is **does the topic drug appear in
this text outside a placebo phrase** -- which is what the caller needs and what a record-level
verdict cannot express, because one record can name an active drug AND a placebo for a
different one. Two live defects came from asking the other question; both are listed below
with the registration that produced them.

Run: python ssot/known_answer_placebo_naming.py
Exit 0 = every known answer reproduced. Exit 1 = at least one did not, and it names which.
"""
import io
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import topic_identity as TI

# (intervention-record name, topic key, is the DRUG PRESENT, registration it was read from)
# `drug present == False` means the record names only a placebo for it.
NAMES_V2 = [
    # The two records that broke a record-level verdict, and the reason this file's question
    # changed. Each names an ACTIVE drug and a placebo in ONE string.
    ("Azilsartan medoxomil/placebo", "azilsartan", True,
     "NCT01456169 -- the arm carrying it is LABELLED 'Azilsartan medoxomil 40 mg'. A slash "
     "joins the two; read as a placebo record, azilsartan vanished from an arm that receives "
     "it and the FDC-vs-monotherapy trial stopped being a background design."),
    ("dapagliflozin 10 mg and matching placebo for balcinrenone/dapagliflozin", "sglt2 inhibitors",
     True,
     "NCT06307652 -- the ACTIVE_COMPARATOR arm genuinely receives dapagliflozin 10 mg. Read as "
     "a placebo record it lost it, and a fixed-dose-combination trial with dapagliflozin in "
     "every arm was promoted out of background."),
    ("balcinrenone/dapagliflozin 15 mg/10 mg and matching placebo for dapagliflozin 10 mg",
     "sglt2 inhibitors", True, "NCT06307652 -- its experimental arm."),
    # Placebo-only records: the drug must NOT be found.
    ("Apixaban-matching placebo", "apixaban", False, "NCT00452530 / NCT00423319"),
    ("Apixaban Placebo", "apixaban", False, "NCT00097357 APROPOS"),
    ("Alirocumab placebo", "alirocumab", False, "NCT03004001"),
    ("Azilsartan medoxomil placebo", "azilsartan", False, "NCT02203916"),
    ("Azilsartan placebo tablets", "azilsartan", False, "NCT02609490"),
    ("Bococizumab 150mg placebo", "bococizumab", False, "NCT02458287"),
    ("One tablet of placebo of dapagliflozin 10 mg", "sglt2 inhibitors", False, "NCT07025629"),
    ("Placebo (for alirocumab)", "alirocumab", False, "ODYSSEY -- the original E1 instance"),
    ("Placebo Matched to Alirocumab", "alirocumab", False,
     "NCT01576484 -- 'matched to', a preposition the phrase patterns do not list; only the "
     "LEADING anchor catches it"),
    ("Placebo for Bococizumab (PF-04950615;RN316)", "bococizumab", False,
     "NCT02135029 -- the development code survives phrase-stripping in the tail and is itself "
     "a declared synonym, so only the LEADING anchor catches it"),
    ("Placebos", "apixaban", False, "cached payload -- plural, which `\\b` cannot match"),
    # Conjunction: BOTH are given, so the drug IS present.
    ("Apixaban + Placebo", "apixaban", True, "NCT00371683 ADVANCE-1"),
    ("empagliflozin plus placebo", "sglt2 inhibitors", True,
     "the case the original anchored pattern was written to protect"),
    # Ordinary drug records.
    ("Apixaban", "apixaban", True, "NCT00643201 AMPLIFY"),
    ("Dapagliflozin 10 MG Oral Tablet [Farxiga]", "sglt2 inhibitors", True, "NCT07025629"),
    ("Enoxaparin", "apixaban", False, "NCT00452530 -- a different drug entirely"),
]

# Registration-level answers: (nct, topic key, expected role, why we know it)
SCR = ("F:/claude-temp/claude/F--rapidmeta-ssot-shell/"
       "c02222d6-792e-4344-bcf5-fd4ff659cdd6/scratchpad/apx_raw_q2.json")
CACHE = os.environ.get(
    "RM_CTGOV_CACHE",
    "F:/claude-temp/claude/F--rapidmeta-ssot-shell/"
    "eb4d84e5-8a24-4c3b-afe2-34bd91c20bc7/scratchpad/.ctgov-raw-cache")
ROLES = [
    ("NCT00452530", "apixaban", TI.EXPERIMENTAL,
     "ADVANCE-2: apixaban vs enoxaparin, double-dummy. The randomised contrast IS apixaban."),
    # THE EXPECTED ANSWER HERE WAS WRITTEN WRONG FIRST, AND THE CORRECTION IS THE ENTRY.
    #
    # I asserted EXPERIMENTAL because ADVANCE-3 is the same design as ADVANCE-2 by the same
    # sponsor, months apart: apixaban 2.5 mg BID vs enoxaparin 40 mg QD, double-dummy. That was
    # MY expectation, not the registry's record -- the exact substitution detector 10 exists to
    # forbid ("the known answer must come from the data, never from a fixture the author
    # invented"), committed inside the file written to enforce it.
    #
    # WHAT THE REGISTRY ACTUALLY RECORDS, and it is the more useful finding:
    #     ADVANCE-2  EXPERIMENTAL      'Apixaban, 2.5 mg BID + Placebo'
    #     ADVANCE-3  ACTIVE_COMPARATOR 'Apixaban, 2.5 mg BID plus placebo'   <- INVERTED
    # One programme, one design, opposite arm typing. So the cascade puts two identical trials
    # in two different cells -- k3 for one, k4 for the other -- and NOTHING about the trials
    # differs. It is a registrant's habit.
    #
    # No promotion rule is invented here. Separating "the topic drug is the new agent" from
    # "the topic drug is the established comparator" in a head-to-head needs knowledge locate()
    # does not have and cannot get from the payload; the placebo discriminator works precisely
    # because a placebo arm is inert and says so. The consequence is carried into screening
    # instead, where k3 and k4 are screened TOGETHER against the review's criteria and the
    # decision is argued rather than inherited.
    ("NCT00423319", "apixaban", TI.COMPARATOR,
     "ADVANCE-3: apixaban vs enoxaparin, and the registration types the APIXABAN arm "
     "ACTIVE_COMPARATOR and the ENOXAPARIN arm EXPERIMENTAL -- the reverse of ADVANCE-2's "
     "typing for the same design. Recorded as the registry has it; the inconsistency is a "
     "finding about arm typing, not about either trial."),
    ("NCT00097357", "apixaban", TI.EXPERIMENTAL,
     "APROPOS: six apixaban dose arms vs enoxaparin vs warfarin, double-dummy."),
    ("NCT00371683", "apixaban", TI.EXPERIMENTAL,
     "ADVANCE-1: `Apixaban + Placebo` vs `Enoxaparin + Placebo`. THE CONTROL CASE for the "
     "conjunction rule -- if `+ Placebo` were read as a placebo-only record this still has to "
     "come out experimental, and if the trailing rule over-fired it would not."),
    ("NCT03988842", "apixaban", TI.BACKGROUND,
     "SAFE-LYSE: apixaban under its own name in BOTH arms; the randomised contrast is "
     "alteplase. THE BOTH-ARMS RULE MUST SURVIVE THE FIX."),
    ("NCT02946944", "apixaban", TI.BACKGROUND,
     "PSCAT: sildenafil/apixaban vs apixaban. Contrast is sildenafil."),
    ("NCT04128254", "apixaban", TI.NOT_ASSESSABLE,
     "the placebo-typed arm's ONLY intervention record is `Apixaban Oral Tablet`, with no "
     "placebo record -- the registration contradicts itself."),
    ("NCT00252005", "apixaban", TI.NOT_ASSESSABLE,
     "Botticelli DVT: randomised, parallel, double-blind, n=520, and NO armGroups in the "
     "payload at all. Absent field, not background use."),
    ("NCT00643201", "apixaban", TI.EXPERIMENTAL,
     "AMPLIFY: apixaban vs enoxaparin/warfarin with placebos for each. Unmoved by the fix."),
    # THE TWO THE REFACTOR BROKE, both in the withholding direction, both restored by putting
    # the original leading anchor back. They are here so a future generalisation cannot quietly
    # drop the special case that already worked.
    ("NCT01576484", "alirocumab", TI.EXPERIMENTAL,
     "alirocumab open-label extension: `Placebo Matched to Alirocumab` vs `Alirocumab 150 mg`. "
     "'matched to' is not one of the prepositions the forward phrase pattern lists, so phrase "
     "stripping alone leaves `alirocumab` standing in the placebo arm."),
    ("NCT02135029", "bococizumab", TI.EXPERIMENTAL,
     "bococizumab vs atorvastatin vs placebo. The placebo record is `Placebo for Bococizumab "
     "(PF-04950615;RN316)` -- the phrase is stripped and the DEVELOPMENT CODE survives in the "
     "tail, and `pf-04950615` is itself a declared bococizumab synonym, so the drug reappears "
     "out of its own placebo's name."),
    ("NCT05171049", "apixaban", TI.COMPARATOR,
     "ASTER: abelacimab is the experimental agent and apixaban is genuinely the comparator. "
     "The placebo-discriminator must NOT promote it -- the other arm is an active drug."),
]


def main():
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    bad = 0
    print("intervention-record names (%d), every one read from a cached registration" % len(NAMES_V2))
    print("  question: does the TOPIC DRUG appear outside a placebo phrase?")
    for name, topic, want, src in NAMES_V2:
        syns = TI.synonyms_for(topic)
        stripped = "" if TI._name_is_placebo_record(name) else TI._strip_placebo_phrases(name)
        got = any(s in stripped for s in syns)
        if got != want:
            bad += 1
            print("  [FAIL] %-70r" % name)
            print("         topic %-18s drug present? got %s want %s" % (topic, got, want))
            print("         after stripping: %r" % stripped)
            print("         %s" % src)
    print("  %d checked, %d wrong" % (len(NAMES_V2), bad))

    print()
    if not os.path.exists(SCR):
        print("  [SKIP] registration-level answers: payload %s absent." % SCR)
        print("         A SKIP IS NOT A PASS. Re-run the apixaban query to restore it.")
        return 1 if bad else 2
    import json
    studies = {}
    if os.path.isdir(CACHE):
        for fn in os.listdir(CACHE):
            if not fn.endswith(".json"):
                continue
            try:
                rec = json.load(io.open(os.path.join(CACHE, fn), encoding="utf-8"))
            except (ValueError, OSError):
                continue
            for st in (rec.get("studies") if "studies" in rec else [rec]):
                nct_ = (((st.get("protocolSection") or {}).get("identificationModule") or {})
                        .get("nctId"))
                if nct_:
                    studies[nct_] = st
    with io.open(SCR, encoding="utf-8") as fh:
        for st in (json.load(fh).get("studies") or []):
            studies[st["protocolSection"]["identificationModule"]["nctId"]] = st
    print("registration-level answers (%d), roles read from the raw v2 payload" % len(ROLES))
    missing = 0
    for nct, topic, want, why in ROLES:
        syns = TI.synonyms_for(topic)
        s = studies.get(nct)
        if s is None:
            missing += 1
            print("  [ABSENT] %s not in the payload -- NOT a pass." % nct)
            continue
        got, ev = TI.locate(s, syns)
        if got != want:
            bad += 1
            print("  [FAIL] %s got %r want %r" % (nct, got, want))
            print("         why we know: %s" % why)
            print("         evidence   : %s" % ev[:150])
    print("  %d checked, %d absent, %d wrong" % (len(ROLES), missing, bad))

    print()
    if bad or missing:
        print("REFUSED: %d known answer(s) not reproduced, %d payload record(s) absent."
              % (bad, missing))
        return 1
    print("every known answer reproduced.")
    print("NOT CHECKED, and named: `Iloprost or placebo` and `Azilsartan medoxomil/placebo`.")
    print("A record joined by 'or' or by '/' covers both arms in one string and this file does")
    print("not claim to resolve it -- 'or' is treated as a conjunction (drug present), which")
    print("errs toward BACKGROUND, the withholding direction. Stated, not silently decided.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
