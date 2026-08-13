"""Reverse the NULLED: quarantine where the registry says the trial exists.

WHAT NULLED: ACTUALLY IS. Not a pipeline accident. `scripts/aggregate_8agent_findings.py`
writes it deliberately, via null_key(), to NCTs an 8-agent blinded audit classified
HIGH severity under NCT_CATEGORIES -- "fabricated or unresolvable" -- and it ships a
data-integrity quarantine banner alongside. So this is a reversal of a deliberate
adjudication, and it needs evidence rather than a string operation.

THE EVIDENCE. All 362 distinct quarantined NCTs were resolved against the live
ClinicalTrials.gov API. 361 RESOLVE -- ACCORD, SPS3, and a long tail of ordinary
NIH trials. One, NCT04165116, does not. The quarantine's stated reason is false for
99.7% of the rows it was applied to.

WHAT THIS DOES. Strips the prefix ONLY for ids the registry returned, and leaves
NCT04165116 quarantined, because for that one the original claim still stands. It
records the reversal per app so the change is auditable in the direction it was made.

WHY IT IS NOT NUMBER-AFFECTING, AND WHY THAT IS CHECKED RATHER THAN ASSERTED. The
edit rewrites a KEY, never a value. The script captures every numeric field in each
touched block before and after and refuses to write if any differs.
"""
import io
import json
import os
import re
import sys

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

RES = json.load(open(os.path.join("outputs", "nulled_nct_resolution.json"),
                     encoding="utf-8"))
KEEP = set(RES["unresolved"])          # stays quarantined
FREE = set(RES["resolve"])             # registry says these exist
NUM = re.compile(r'["\']?(hr|lci|uci|w|tE|tN|cE|cN|n|events|point|ci_low|ci_high)'
                 r'["\']?\s*:\s*(-?[\d.eE+]+)')


def numeric_fingerprint(txt):
    """Every numeric field in the file, as an ordered multiset."""
    return sorted(NUM.findall(txt))


def main():
    apply = "--apply" in sys.argv
    import glob
    log, touched, freed, kept = [], 0, 0, 0
    for f in sorted(glob.glob("*_REVIEW.html")):
        s = open(f, encoding="utf-8", errors="replace").read()
        found = set(re.findall(r'["\']NULLED:(NCT\d{8})["\']\s*:', s))
        if not found:
            continue
        before = numeric_fingerprint(s)
        out = s
        did = []
        for nct in sorted(found):
            if nct in KEEP:
                kept += 1
                log.append({"app": f, "nct": nct, "action": "LEFT QUARANTINED",
                            "why": "the registry does not return this id, so the "
                                   "original adjudication still stands"})
                continue
            if nct not in FREE:
                log.append({"app": f, "nct": nct, "action": "SKIPPED",
                            "why": "not in the resolution set; not adjudicated here"})
                continue
            new = out.replace('"NULLED:%s"' % nct, '"%s"' % nct)
            new = new.replace("'NULLED:%s'" % nct, "'%s'" % nct)
            if new != out:
                out = new
                did.append(nct)
        if not did:
            continue
        after = numeric_fingerprint(out)
        if before != after:
            print("REFUSING %s -- a numeric field changed. That must not happen for "
                  "a key rewrite." % f)
            log.append({"app": f, "action": "REFUSED", "why": "numeric drift"})
            continue
        freed += len(did)
        touched += 1
        log.append({"app": f, "action": "UNQUARANTINED", "count": len(did),
                    "ncts": did,
                    "evidence": "each id returned a study record from the live "
                                "ClinicalTrials.gov API",
                    "numeric_fields_unchanged": True,
                    "numeric_fields_checked": len(before)})
        if apply:
            open(f, "w", encoding="utf-8").write(out)
    os.makedirs("outputs", exist_ok=True)
    json.dump({"mode": "APPLIED" if apply else "DRY RUN",
               "reversal_of": "scripts/aggregate_8agent_findings.py null_key()",
               "basis": "live ClinicalTrials.gov resolution of all 362 quarantined ids",
               "apps_touched": touched, "ncts_unquarantined": freed,
               "left_quarantined": kept, "records": log},
              open(os.path.join("outputs", "unquarantine_log.json"), "w",
                   encoding="utf-8"), indent=1, ensure_ascii=False)
    print("%s: %d apps, %d NCTs un-quarantined, %d left quarantined"
          % ("APPLIED" if apply else "DRY RUN", touched, freed, kept))
    print("numeric fingerprints identical in every touched file: "
          "%s" % all(r.get("numeric_fields_unchanged", True) for r in log))
    print("log: outputs/unquarantine_log.json")
    return 0


if __name__ == "__main__":
    sys.exit(main())
