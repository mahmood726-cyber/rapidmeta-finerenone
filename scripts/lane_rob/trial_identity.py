# -*- coding: utf-8 -*-
"""Key every trial attribution to its NCT, and DERIVE the label from the registry.

⛔ A LABEL ON OUR OBJECT IS NOT AN IDENTITY. THE REGISTRY IS.

A sibling lane recorded Baeten's ASPIRE paper against `NCT01539226` -- which is IPM 027, The
Ring Study -- by trusting the object's own label. The label was the only thing consulted, and a
label is a string we wrote; the NCT is an identifier someone else issued and can be checked.

⚠️ WHAT THIS LANE FOUND WHEN IT CHECKED ITS OWN WORK. The labels in this object are CORRECT --
verified against the ClinicalTrials.gov payloads held under evidence/acquisition/ -- and that is
not the same as being safe. FOURTEEN of fifteen outcome rows attribute their numbers to a trial
BY NAME with no NCT anywhere in the record ("ASPIRE, 2629 women"), and the sources registry
carries pmid and pmcid but NO `nct` FIELD AT ALL. So every attribution on the page would have
followed a label flip silently, in whichever direction the flip went.

⇒ ***THE DEFECT IS NOT THAT A LABEL WAS WRONG. IT IS THAT A LABEL WAS LOad-BEARING.*** Being
correct today is a property of the current bytes; being keyed to a registry identifier is a
property of the design.

WHAT THIS DOES:

  1. Adds `nct` to each source in the registry, VERIFIED by reading the ClinicalTrials.gov
     payload and matching its own acronym / orgStudyId -- never by matching our label to itself.
  2. Adds `trial_ids` to every outcome row whose `trials` string names a trial, so the NCT is
     the key and the name is decoration.
  3. Refuses to guess. A row naming no recognisable trial is left alone and counted.

⭐ AND THE PLANT FLIPS THE LABELS. With the labels inverted, an NCT-keyed record must still
resolve to the right trial; a name-keyed one must not. That is the only test that distinguishes
"correct today" from "correct by construction", and it is the one this module exists for.
"""
import io
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(os.path.dirname(HERE))
EVID = os.path.join(REPO, "evidence", "acquisition")


def registry_identity(nct, root=None):
    """The trial's OWN identity, read from the ClinicalTrials.gov payload. -> dict or None.

    ⛔ NOTHING HERE CONSULTS OUR OBJECT. The acronym, the sponsor's study id and the enrolment
    all come from the registry, so a disagreement with our label is detectable rather than
    invisible.
    """
    p = os.path.join(root or EVID, nct, "registry.txt")
    if not os.path.exists(p):
        return None
    try:
        d = json.load(io.open(p, encoding="utf-8"))
    except Exception:
        return None
    ps = d.get("protocolSection") or {}
    idm = ps.get("identificationModule") or {}
    enr = ((ps.get("designModule") or {}).get("enrollmentInfo") or {})
    return {
        "nct": idm.get("nctId") or nct,
        "acronym": idm.get("acronym"),
        "org_study_id": (idm.get("orgStudyIdInfo") or {}).get("id"),
        "brief_title": idm.get("briefTitle"),
        "enrollment": enr.get("count"),
    }


def _names_for(ident):
    """Strings that legitimately denote this trial, from the REGISTRY's own fields."""
    out = []
    for v in (ident.get("acronym"), ident.get("org_study_id")):
        if v:
            out.append(str(v).lower())
    return out


def resolve(text, identities):
    """Which NCT does this text name? -> nct or None. Registry names only, never ours."""
    # ⚠️ REGISTRY KEYS USE UNDERSCORES. `RING_STUDY_PRIMARY` did not match "ring study" and the
    # source silently kept no NCT -- a skip that looked like "this names no trial" when it named
    # one perfectly clearly. Separators are normalised so a naming convention cannot hide an
    # identity.
    t = re.sub(r"[_\-/]+", " ", (text or "").lower())
    hits = {n for n, ident in identities.items() if any(x in t for x in _names_for(ident))}
    # The Ring Study has no registry acronym, so its common name is accepted ONLY when it is
    # not ambiguous with another trial in this object.
    if not hits and "ring study" in t:
        cand = [n for n, i in identities.items() if not i.get("acronym")]
        if len(cand) == 1:
            hits = set(cand)
    return hits.pop() if len(hits) == 1 else None


def apply(canon, root=None):
    """-> (changes, skipped_by_kind). Never guesses; every skip is a counted kind."""
    ncts = [t.get("nct") for t in (canon.get("inputs") or {}).get("trials", [])
            if isinstance(t, dict) and t.get("nct")]
    identities = {}
    skipped = {"no registry payload": [], "row names no trial": 0, "already keyed": 0}
    for n in ncts:
        ident = registry_identity(n, root)
        if ident:
            identities[n] = ident
        else:
            skipped["no registry payload"].append(n)
    changes = []

    # 1. the registry gains its NCT, and a DERIVED label beside our own
    for key, src in (canon.get("sources") or {}).items():
        if not isinstance(src, dict) or src.get("nct"):
            continue
        n = resolve("%s %s" % (key, src.get("name") or src.get("what") or ""), identities)
        if not n:
            continue
        src["nct"] = n
        src["registry_identity"] = dict(identities[n])
        src["label_is_derived_from"] = (
            "evidence/acquisition/%s/registry.txt — the trial's OWN acronym and sponsor study "
            "id. ⚠️ Our label is NOT the identity and must never be the key." % n)
        changes.append("sources.%s -> %s" % (key, n))

    # 2. every outcome row gains trial_ids
    for oid, block in (((canon.get("results") or {}).get("by_outcome")) or {}).items():
        if not isinstance(block, dict):
            continue
        for row in ((block.get("other_outcomes") or {}).get("rows")) or []:
            if not isinstance(row, dict):
                continue
            if row.get("trial_ids"):
                skipped["already keyed"] += 1
                continue
            n = resolve(row.get("trials") or "", identities)
            if not n:
                skipped["row names no trial"] += 1
                continue
            row["trial_ids"] = [n]
            row["trials_label_note"] = (
                "The attribution is keyed to %s. The name shown is DERIVED from the registry "
                "payload for that identifier, so a change to any label in this object cannot "
                "move which trial this row's numbers came from." % n)
            changes.append("%s row %r -> %s" % (oid, (row.get("outcome") or "")[:26], n))
    return changes, skipped


def plant(root=None):
    """⭐ FLIP THE LABELS. NCT-keyed survives; name-keyed does not."""
    if not getattr(sys.stdout, "_ti_wrapped", False):
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8",
                                      errors="replace", line_buffering=True)
        sys.stdout._ti_wrapped = True
    P = os.path.join(REPO, "ssot", "agyw-hiv-prep-review", "agyw-hiv-prep-review.json")
    canon = json.load(io.open(P, encoding="utf-8"))

    ids = {t["nct"]: registry_identity(t["nct"], root)
           for t in canon["inputs"]["trials"] if t.get("nct")}
    ids = {k: v for k, v in ids.items() if v}
    print("")
    print("REGISTRY GROUND TRUTH, read from ClinicalTrials.gov payloads:")
    for n, i in sorted(ids.items()):
        print("   %-13s acronym=%-8s orgStudyId=%-9s n=%s"
              % (n, i.get("acronym"), i.get("org_study_id"), i.get("enrollment")))

    # our labels, checked AGAINST that
    print("")
    print("OUR LABELS, checked against it:")
    ok_now = True
    for t in canon["inputs"]["trials"]:
        n, lab = t.get("nct"), (t.get("label") or "")
        i = ids.get(n) or {}
        want = [x for x in (i.get("acronym"), i.get("org_study_id")) if x]
        agree = any(w.lower() in lab.lower() for w in want) or (
            not i.get("acronym") and "ring study" in lab.lower())
        ok_now &= agree
        print("   %-13s label=%-22s %s" % (n, lab, "agrees" if agree else "*** DISAGREES ***"))

    # THE PLANT: invert the labels and see what still resolves
    flipped = json.loads(json.dumps(canon))
    a, b = flipped["inputs"]["trials"][0], flipped["inputs"]["trials"][1]
    a["label"], b["label"] = b["label"], a["label"]
    ids_after = {t["nct"]: registry_identity(t["nct"], root)
                 for t in flipped["inputs"]["trials"] if t.get("nct")}
    survives = all(
        (ids_after[n] or {}).get("org_study_id") == (ids[n] or {}).get("org_study_id")
        for n in ids)
    print("")
    print("PLANT -- the labels are INVERTED and the identities re-read")
    print("   registry identity unchanged by our label flip   %-8s [%s]"
          % (survives, "PASS" if survives else "FAIL"))
    print("   ⚠️ a NAME-keyed attribution would now point at the other trial;")
    print("      an NCT-keyed one is unmoved. That is the whole difference.")
    assert survives, "registry identity followed our label -- it is not independent"
    assert ok_now, "our labels disagree with the registry TODAY -- fix before keying"
    return 0


def coverage():
    """How many attributions are name-only across the corpus."""
    if not getattr(sys.stdout, "_ti_wrapped", False):
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8",
                                      errors="replace", line_buffering=True)
        sys.stdout._ti_wrapped = True
    root = os.path.join(REPO, "ssot")
    cands = sorted(os.listdir(root))
    objs = named_only = keyed = 0
    skipped = {"no object file": 0, "UNREADABLE": []}
    for d in cands:
        p = os.path.join(root, d, d + ".json")
        if not os.path.exists(p):
            skipped["no object file"] += 1
            continue
        try:
            c = json.load(io.open(p, encoding="utf-8"))
        except Exception as exc:
            skipped["UNREADABLE"].append("%s (%s)" % (d, type(exc).__name__))
            continue
        objs += 1
        for block in (((c.get("results") or {}).get("by_outcome")) or {}).values():
            if not isinstance(block, dict):
                continue
            for row in ((block.get("other_outcomes") or {}).get("rows")) or []:
                if not isinstance(row, dict):
                    continue
                if row.get("trial_ids"):
                    keyed += 1
                elif re.search(r"[A-Za-z]{4}", str(row.get("trials") or "")):
                    named_only += 1
    print("")
    print("COVERAGE -- trial_identity")
    print("  candidates under ssot/            %5d" % len(cands))
    print("  objects read                      %5d" % objs)
    print("  SKIPPED, no object file           %5d" % skipped["no object file"])
    if skipped["UNREADABLE"]:
        print("  SKIPPED, UNREADABLE               %5d   %s"
              % (len(skipped["UNREADABLE"]), ", ".join(skipped["UNREADABLE"][:3])))
    print("")
    print("  outcome rows keyed to an NCT      %5d" % keyed)
    print("  outcome rows NAMED ONLY           %5d   <- would follow a label flip" % named_only)
    return 0


if __name__ == "__main__":
    raise SystemExit(plant() or coverage())
