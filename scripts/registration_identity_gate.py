"""REGISTRATION IDENTITY -- does the registration actually name THIS trial?

WHY THIS EXISTS
    `identity_by_registration_gate` checks that every pooled trial carries a
    registration and that no two rows share one. It PASSED DOAC_CANCER_VTE's row
    `NCT02583191 = 'SELECT-D'`. That registration is CONKO-011 / AIO-SUP-0115,
    sponsored by AIO-Studien-gGmbH in Germany, enrolment 246, whose registered
    primary outcome is patient-reported treatment satisfaction measured to four
    weeks. It is not SELECT-D; SELECT-D is ISRCTN86712308 and is not on
    ClinicalTrials.gov at all.

    The existing gate closes the LABEL -> IDENTITY direction, which is the
    PARACHUTE-HF/ANSWER-HF defect. It leaves REGISTRATION -> IDENTITY wide open,
    and that direction fails toward COMFORT: a wrong key looks exactly like a
    right one to any check that only asks whether a key is present and unique.

WHAT IT COMPARES, AND WHY THAT SIGNAL
    The obvious check -- does the trial's NAME appear in the registration's
    title? -- DOES NOT WORK, and it is worth recording why rather than letting
    someone rediscover it. Hokusai VTE-Cancer's registration has no acronym and
    its brief title is "Cancer Venous Thromboembolism (VTE)". The name appears
    nowhere in its own record. A name-match check would flag a correct row.

    What DOES discriminate is arithmetic the registry states and the object
    states independently: THE NUMBER OF PARTICIPANTS ANALYSED against the
    ENROLMENT the registration records.

        Hokusai      522 + 524 = 1046   registered 1046    exact
        CARAVAGGIO   576 + 579 = 1155   registered 1170    1.3% below, analysed < randomised
        SELECT-D row 101 + 102 =  203   registered  246   17.5% below   <-- the wrong key

    A row keyed to the wrong registration is a row whose two halves were sized by
    different trials, so this fires on exactly the defect it is named for.

WHAT THIS DOES NOT ESTABLISH -- written in advance, because that is the rule here
    - NOT that a row inside the tolerance is correctly keyed. Two trials of
      similar size would pass. This is a screen, not a proof.
    - NOT that a row outside it is wrongly keyed. Analysed is legitimately below
      randomised, sometimes far below: a per-protocol population, an
      efficacy-cutoff population, a trial reporting one of three arms. THAT IS
      WHY THE VERDICT IS `REVIEW`, NOT `FAIL` -- this gate hands a human a short
      list and refuses to convict on arithmetic alone.
    - NOTHING AT ALL without a stored enrolment. A row with no
      `registration_enrolment` is UNMEASURED and says so; it is never a pass.
      An absent field must not read as a clean one.

    The tolerance is deliberately loose. A tight one would convict every
    per-protocol analysis in the corpus and be switched off within a week, which
    is how a check that fails toward alarm dies -- and this file would rather be
    quiet and trusted than loud and ignored.

USAGE
    python scripts/registration_identity_gate.py <object.json> [...]
    python scripts/registration_identity_gate.py --selftest
    python scripts/registration_identity_gate.py --fetch <object.json>
        --fetch fills registration_enrolment from ClinicalTrials.gov and writes
        it back, so every later run is offline.
"""
from __future__ import annotations
import io
import json
import os
import sys

if __name__ == "__main__":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

# Below this ratio of analysed-to-registered, the row is listed for a human.
# 0.75 keeps CARAVAGGIO (0.987) and every ordinary per-protocol shortfall quiet
# while listing the SELECT-D row (0.825)... which it does NOT. See _THRESHOLD_NOTE.
_THRESHOLD_NOTE = """
    THE FIRST THRESHOLD I PICKED WAS WRONG AND THE SELFTEST CAUGHT IT.
    0.75 was chosen to "keep per-protocol analyses quiet". The SELECT-D row sits
    at 0.825, ABOVE it, so the one real defect this gate was built for would have
    passed silently -- a gate that cannot catch its own founding case. Raised to
    0.90, which lists SELECT-D (0.825) and keeps CARAVAGGIO (0.987) and Hokusai
    (1.000) quiet. Recorded rather than quietly corrected, because picking a
    threshold that excludes your own fixture is the exact shape of a check built
    to pass.
"""
MIN_ANALYSED_RATIO = 0.90


def _analysed(trial, oid):
    """Participants analysed on this trial, from arms or from the outcome cell."""
    bo = (trial.get("by_outcome") or {}).get(oid) or {}
    an = bo.get("analysed") or {}
    # BOTH VOCABULARIES. The v1 objects say {"treatment", "control"}; the
    # extractor schema says {"intervention", "control"}. The first cut of this
    # read only the second pair, so on a v1 object it summed the control arm
    # alone and returned HALF THE TRIAL -- and thirteen correctly-keyed rows came
    # back at 46-50%, which would have made this gate noise on its first run.
    # arm_identity_gate carries a comment about hitting exactly this, which I had
    # read. Knowing a rule does not apply it; only a check does, so the selftest
    # below now carries a treatment/control row.
    tot = 0.0
    for key in ("intervention", "treatment", "control", "comparator"):
        v = an.get(key)
        if isinstance(v, (int, float)):
            tot += float(v)
    if tot > 0:
        return tot
    for a in trial.get("arms") or []:
        v = a.get("participants")
        if isinstance(v, (int, float)):
            tot += float(v)
    return tot or None


def check(obj):
    trials = ((obj.get("inputs") or {}).get("trials")) or []
    results = ((obj.get("results") or {}).get("by_outcome")) or {}
    if not trials or not results:
        return "UNCHECKABLE", ["object carries no trials or no pooled outcome"]
    oid = sorted(results)[0]

    notes, listed, unmeasured, checked = [], [], [], 0
    for t in trials:
        name = t.get("name") or t.get("nct") or "?"
        reg = t.get("nct") or ""
        # A conflict already RECORDED on the object is the property met by
        # declaration: the object is not hiding it, and a second alarm about a
        # documented fact is noise. It is still reported, distinctly.
        if t.get("identity_conflict"):
            notes.append("  %-22s %-13s DECLARED   an identity conflict is recorded "
                         "on this row" % (name[:22], reg))
            continue
        enrolled = t.get("registration_enrolment")
        analysed = _analysed(t, oid)
        if not isinstance(enrolled, (int, float)) or not enrolled:
            unmeasured.append(name)
            notes.append("  %-22s %-13s UNMEASURED no registration_enrolment stored "
                         "-- run --fetch. This is not a pass" % (name[:22], reg))
            continue
        if not analysed:
            unmeasured.append(name)
            notes.append("  %-22s %-13s UNMEASURED no analysed count on this row"
                         % (name[:22], reg))
            continue
        checked += 1
        ratio = analysed / float(enrolled)
        # A MULTI-ARM TRIAL POOLED TWO ARMS AT A TIME IS NOT A SHORTFALL.
        # RE-LY registers three arms and this corpus pools dabigatran 150 against
        # warfarin; ENGAGE registers three and it pools high-dose edoxaban against
        # warfarin. Both land near two thirds and both are correct. The arm count
        # is STATED rather than used to adjust the denominator: scaling by it would
        # be guessing which arms were pooled and how big they were.
        arms_registered = t.get("registration_arm_count")
        arms_pooled = len([a for a in (t.get("arms") or [])
                           if a.get("role") in ("treatment", "intervention", "control",
                                                "comparator")])
        multiarm = (isinstance(arms_registered, int) and arms_pooled
                    and arms_registered > arms_pooled)
        if ratio < MIN_ANALYSED_RATIO:
            why = ("" if not multiarm else
                   "  -- but the registration has %d arms and this pool takes %d, "
                   "which accounts for a shortfall of about this size"
                   % (arms_registered, arms_pooled))
            listed.append((name, reg, analysed, enrolled, ratio))
            notes.append("  %-22s %-13s REVIEW     analysed %d against registered %d "
                         "= %.1f%%%s" % (name[:22], reg, analysed, enrolled,
                                         100 * ratio, why))
        else:
            notes.append("  %-22s %-13s ok         analysed %d against registered %d "
                         "= %.1f%%" % (name[:22], reg, analysed, enrolled, 100 * ratio))

    if not checked and not listed:
        notes.append("-> UNMEASURED. No row could be compared, so nothing is "
                     "established. This is NOT a pass.")
        return "UNCHECKABLE", notes
    if listed:
        notes.append("-> REVIEW: %d row(s) analyse far fewer participants than their "
                     "registration records. That is legitimate for a per-protocol or "
                     "efficacy-cutoff population and it is also what a WRONG "
                     "REGISTRATION looks like. A human decides; this gate does not "
                     "convict on arithmetic." % len(listed))
        return "REVIEW", notes
    notes.append("-> PASS: every checked row's analysed count is consistent with its "
                 "registration's enrolment. This screens the key, not the trial.")
    return "PASS", notes


# ------------------------------------------------------------------ selftest
def selftest() -> int:
    ok = True

    def obj(rows):
        return {"inputs": {"trials": rows},
                "results": {"by_outcome": {"primary": {"k": len(rows)}}}}

    def row(name, nct, tn, cn, enrolled, conflict=None):
        r = {"name": name, "nct": nct,
             "arms": [{"role": "treatment", "participants": tn},
                      {"role": "control", "participants": cn}],
             "by_outcome": {"primary": {}}}
        if enrolled is not None:
            r["registration_enrolment"] = enrolled
        if conflict:
            r["identity_conflict"] = conflict
        return r

    def row_v1(name, nct, tn, cn, enrolled):
        """A v1-shaped row: analysed keyed treatment/control, arms unpopulated.

        This is the shape that broke the first cut. alirocumab's rows carry
        participants: None on the arms and the real numbers only under analysed,
        so a reader that misses this key has nothing to fall back on.
        """
        return {"name": name, "nct": nct,
                "arms": [{"role": "treatment", "participants": None},
                         {"role": "control", "participants": None}],
                "by_outcome": {"primary": {"analysed": {"treatment": tn,
                                                        "control": cn}}},
                "registration_enrolment": enrolled}

    HOKUSAI = row("HOKUSAI VTE-Cancer", "NCT02073682", 522, 524, 1046)
    CARAVAGGIO = row("CARAVAGGIO", "NCT03045406", 576, 579, 1170)
    SELECTD = row("SELECT-D", "NCT02583191", 101, 102, 246)

    cases = [
        ("POSITIVE the founding case: SELECT-D's data under CONKO-011's key",
         obj([HOKUSAI, CARAVAGGIO, SELECTD]), "REVIEW"),
        ("NEGATIVE the same object with only the correctly-keyed rows",
         obj([HOKUSAI, CARAVAGGIO]), "PASS"),
        ("NEGATIVE an exact-enrolment row alone",
         obj([HOKUSAI]), "PASS"),
        ("NEGATIVE analysed just below randomised is ordinary, not suspicious",
         obj([CARAVAGGIO]), "PASS"),
        ("NEGATIVE a v1-shaped row -- analysed keyed treatment/control, arms empty",
         obj([row_v1("PARADIGM-HF", "NCT01035255", 4187, 4212, 8442)]), "PASS"),
        ("NEGATIVE a v1 row whose arms carry no participants at all",
         obj([row_v1("Alirocumab LONG TERM", "NCT01507831", 1530, 780, 2341)]), "PASS"),
        ("UNMEASURED no enrolment stored is not a pass",
         obj([row("X", "NCT1", 100, 100, None)]), "UNCHECKABLE"),
        ("DECLARED a recorded conflict is not re-alarmed, and does not pass either",
         obj([row("Y", "NCT2", 101, 102, 246, conflict="recorded")]), "UNCHECKABLE"),
    ]
    for label, o, want in cases:
        v, notes = check(o)
        good = v == want
        ok &= good
        print("  %-62s -> %-12s (want %-12s) %s"
              % (label, v, want, "correct" if good else "WRONG"))
        if not good:
            for n in notes:
                print("        " + n)

    # THE THRESHOLD MUST CONTAIN ITS OWN FOUNDING CASE.
    ratio = 203 / 246.0
    inside = ratio < MIN_ANALYSED_RATIO
    ok &= inside
    print("\n  threshold %.2f vs the founding case's ratio %.3f -> %s"
          % (MIN_ANALYSED_RATIO, ratio,
             "the case is caught" if inside else "WRONG: the gate cannot catch the "
             "defect it was built for"))
    print(_THRESHOLD_NOTE.rstrip())

    print("\nWHAT A FAILURE WOULD LOOK LIKE: the SELECT-D row passing -- which is what "
          "identity_by_registration_gate does today, because it asks whether a "
          "registration is present and unique and never whether it is the right one.")
    print("WHAT THIS GATE STILL CANNOT SEE: a wrong registration of the SAME SIZE. It "
          "screens the key; it does not prove it.")
    print("-> SELFTEST PASS" if ok else "-> SELFTEST FAILED")
    return 0 if ok else 1


def fetch_into(path):
    """Fill registration_enrolment from ClinicalTrials.gov and write it back."""
    import urllib.request
    obj = json.load(open(path, encoding="utf-8"))
    n = 0
    for t in (obj.get("inputs") or {}).get("trials") or []:
        nct = t.get("nct") or ""
        if not nct.upper().startswith("NCT") or t.get("registration_enrolment"):
            continue
        url = ("https://clinicaltrials.gov/api/v2/studies/%s"
               "?fields=protocolSection.designModule,"
               "protocolSection.identificationModule,"
               "protocolSection.armsInterventionsModule" % nct)
        req = urllib.request.Request(url, headers={"User-Agent": "rapidmeta-registry-read"})
        with urllib.request.urlopen(req, timeout=60) as r:
            d = json.loads(r.read().decode("utf-8"))
        ps = d.get("protocolSection") or {}
        cnt = ((ps.get("designModule") or {}).get("enrollmentInfo") or {}).get("count")
        idm = ps.get("identificationModule") or {}
        arms = ((ps.get("armsInterventionsModule") or {}).get("armGroups") or [])
        if cnt:
            t["registration_enrolment"] = cnt
            if arms:
                t["registration_arm_count"] = len(arms)
            t["registration_brief_title"] = idm.get("briefTitle")
            t["registration_org_study_id"] = (idm.get("orgStudyIdInfo") or {}).get("id")
            t["registration_read_utc"] = "2026-08-18"
            n += 1
    json.dump(obj, open(path, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print("filled registration_enrolment on %d trial(s) in %s" % (n, path))
    return 0


def main() -> int:
    if len(sys.argv) < 2 or sys.argv[1] == "--selftest":
        return selftest()
    if sys.argv[1] == "--fetch":
        rc = 0
        for p in sys.argv[2:]:
            rc |= fetch_into(p)
        return rc
    worst = 0
    for p in sys.argv[1:]:
        if not os.path.exists(p):
            print("registration_identity: %s does not exist. NOT RUN -- not a pass." % p,
                  file=sys.stderr)
            worst = max(worst, 2)
            continue
        v, notes = check(json.load(open(p, encoding="utf-8")))
        print("%s" % os.path.basename(p))
        for n in notes:
            print(n)
        print("  -> %s" % v)
        worst = max(worst, {"PASS": 0, "REVIEW": 1, "UNCHECKABLE": 2}.get(v, 2))
    return worst


if __name__ == "__main__":
    sys.exit(main())
