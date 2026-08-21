"""Re-read the registrations for risk-of-bias entries that recorded judgements but not facts.

TWELVE TOPICS COULD NOT HAVE A BLIND SECOND ASSESSMENT BUILT FOR THEM, because their
risk-of-bias entries record a judgement and a reason and NOT THE REGISTRY FIELDS THE JUDGEMENT
WAS MADE FROM. The assessment says masking was quadruple in its prose; no field holds it.

THAT IS THE WORK, AND IT ALSO FIXES THE COMPARABILITY PROBLEM RATHER THAN WORKING AROUND IT.
The alternative -- building a thinner prompt from whatever happened to be stored -- would have
produced a disagreement rate measuring the gaps in our own records. This project already
learned that lesson once today: widening the fact allow-list from 9 fields to 14 HALVED
`gepotidacin`'s disagreement, because its entire D5 divergence was a fact the second assessor
had never been shown.

WHAT IS WRITTEN. Only fields read off ClinicalTrials.gov API v2, onto the existing entry:

    registered_enrolment, registered_masking, registered_sites,
    registered_primary_count, registered_primary_outcome, registered_arm_count

NO JUDGEMENT IS TOUCHED. Every `domains.*`, every `overall`, every reason already written stays
exactly as it is. This adds the evidence beside the verdict; it does not revisit the verdict.

AND IT REFUSES RATHER THAN GUESSES. An entry whose `nct` is absent cannot be backfilled -- the
registration cannot be identified -- and is reported by name instead of being filled from the
result id or from a sibling.
"""
import io
import json
import os
import sys
import time
import urllib.request

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(REPO, "ssot"))
import atomic_write

TODAY = "2026-08-21"
API = "https://clinicaltrials.gov/api/v2/studies/%s?fields=protocolSection"


def fetch(nct, cache={}):
    if nct in cache:
        return cache[nct]
    for attempt in range(3):
        try:
            with urllib.request.urlopen(API % nct, timeout=90) as fh:
                cache[nct] = json.load(fh)["protocolSection"]
            return cache[nct]
        except Exception as exc:                                   # noqa: BLE001
            if attempt == 2:
                sys.exit("REFUSED: could not read %s after 3 attempts (%s). A backfill that "
                         "silently skips a registration leaves an entry looking complete."
                         % (nct, exc))
            time.sleep(2 + 3 * attempt)


def facts(d):
    de = d.get("designModule") or {}
    om = d.get("outcomesModule") or {}
    mi = (de.get("designInfo") or {}).get("maskingInfo") or {}
    who = mi.get("whoMasked") or []
    masking = str(mi.get("masking") or "NOT RECORDED")
    if who:
        masking = "%s -- %s" % (masking, ", ".join(str(w).replace("_", " ").lower()
                                                   for w in who))
    elif masking.upper() == "NONE":
        masking = "NONE -- OPEN LABEL"
    prim = om.get("primaryOutcomes") or []
    sites = sorted({(l.get("country") or "") for l in
                    ((d.get("contactsLocationsModule") or {}).get("locations") or [])} - {""})
    out = {
        "registered_masking": masking,
        "registered_primary_count": len(prim),
        "registered_arm_count": len((d.get("armsInterventionsModule") or {})
                                    .get("armGroups") or []),
    }
    n = (de.get("enrollmentInfo") or {}).get("count")
    if isinstance(n, int):
        out["registered_enrolment"] = n
    if prim:
        out["registered_primary_outcome"] = "; ".join(
            str(o.get("measure") or "").strip() for o in prim if o.get("measure"))[:600]
    if sites:
        out["registered_sites"] = ", ".join(sites)
    return out


def main():
    dry = "--apply" not in sys.argv
    touched = filled = refused = 0
    for path in sorted(__import__("glob").glob(os.path.join(REPO, "ssot", "*", "*.json"))):
        topic = os.path.basename(os.path.dirname(path))
        if os.path.basename(path) != topic + ".json":
            continue
        obj = json.load(io.open(path, encoding="utf-8"))
        rob = obj.get("risk_of_bias")
        if not isinstance(rob, dict) or not rob.get("by_outcome"):
            continue
        if any(k.startswith("SECOND_ASSESSOR") for k in rob):
            continue
        changed = []
        for oid, per in (rob["by_outcome"] or {}).items():
            if not isinstance(per, dict):
                continue
            for rid, j in per.items():
                if not isinstance(j, dict) or j.get("registered_masking"):
                    continue
                nct = j.get("nct") or (rid.split("::")[0] if rid.startswith("NCT") else None)
                if not nct:
                    print("   REFUSED %-30s %-26s no `nct` on the entry -- the registration "
                          "cannot be identified" % (oid[:30], rid[:26]))
                    refused += 1
                    continue
                f = facts(fetch(nct))
                j.setdefault("nct", nct)
                j.update(f)
                j["registry_facts_backfilled_%s" % TODAY.replace("-", "_")] = (
                    "READ FROM ClinicalTrials.gov API v2 on %s. THE JUDGEMENTS ABOVE WERE NOT "
                    "REVISITED -- this adds the registry evidence beside a verdict that was "
                    "made from it and did not record it, so a blind second assessor can be "
                    "shown the same facts. A second assessment built on fewer facts is not a "
                    "comparable assessment." % TODAY)
                changed.append("%s/%s" % (oid, nct))
                filled += 1
        if changed:
            touched += 1
            obj.setdefault("display_change_announced", []).append({
                "date": TODAY,
                "change": "registry facts backfilled onto risk-of-bias entries",
                "values_moved": "NONE -- no judgement, reason or overall is touched",
                "what_changed": "%d entr(ies): %s" % (len(changed), ", ".join(changed[:6])),
                "why": ("These entries recorded a judgement and the reason for it without the "
                        "registry fields the judgement was made from, so no blind second "
                        "assessment could be given the same evidence."),
            })
            print("%-42s %d entr(ies) backfilled" % (topic[:42], len(changed)))
            if not dry:
                atomic_write.write_json(path, obj, indent=1)
    print("\n%d topic(s), %d entr(ies) filled, %d refused for want of an nct"
          % (touched, filled, refused))
    if dry:
        print("DRY RUN -- pass --apply to write")


if __name__ == "__main__":
    main()
