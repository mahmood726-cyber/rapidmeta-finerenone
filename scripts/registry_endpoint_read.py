"""REGISTRY ENDPOINT READ -- fetch each trial's outcome DEFINITION, word for word.

WHY THIS EXISTS
    SGLT2_HF pooled four trials as one estimand because the object recorded
    RESULT sentences as provenance and no endpoint definition at all. The fix is
    not a better gate: it is reading what the registry says was COUNTED, from the
    registry, before anything is pooled.

WHAT THIS TOOL DOES NOT ESTABLISH -- written in advance
    - NOT that the registry entry is correct, or that it matches the publication.
      Registries are amended; a trial whose endpoint CHANGED shows the amended
      text and this tool cannot see the history. Where a publication says the
      endpoint was changed during the trial, both must be read.
    - NOT that identical wording licenses a pool. Populations, follow-up and
      analysis sets can still differ.
    - NOT anything at all when the fetch fails. A failed fetch prints FETCH
      FAILED and exits non-zero; it never prints an empty definition, because an
      empty field beside a trial name reads as "no endpoint" rather than "not
      asked", and this project has already shipped that confusion once.

USAGE  python scripts/registry_endpoint_read.py NCT03521934 NCT03315143 ...
"""
from __future__ import annotations
import io, json, sys, urllib.request, urllib.error

if __name__ == "__main__":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

API = ("https://clinicaltrials.gov/api/v2/studies/%s"
       "?fields=protocolSection.identificationModule,"
       "protocolSection.outcomesModule,protocolSection.designModule,"
       "protocolSection.armsInterventionsModule,protocolSection.statusModule")


def fetch(nct):
    req = urllib.request.Request(API % nct, headers={"User-Agent": "rapidmeta-registry-read"})
    with urllib.request.urlopen(req, timeout=60) as r:
        return json.loads(r.read().decode("utf-8"))


def main():
    ncts = [a for a in sys.argv[1:] if a.upper().startswith("NCT")]
    if not ncts:
        print("usage: registry_endpoint_read.py NCT........ [NCT........ ...]",
              file=sys.stderr)
        return 2
    failed = []
    for nct in ncts:
        try:
            d = fetch(nct)
        except Exception as ex:                       # noqa: BLE001
            print("=== %s  FETCH FAILED: %s" % (nct, ex))
            failed.append(nct)
            continue
        ps = d.get("protocolSection") or {}
        idm = ps.get("identificationModule") or {}
        om = ps.get("outcomesModule") or {}
        dm = ps.get("designModule") or {}
        stm = ps.get("statusModule") or {}
        print("=== %s  %s" % (nct, idm.get("acronym") or ""))
        print("    officialTitle: %s" % (idm.get("officialTitle") or "")[:300])
        enr = (dm.get("enrollmentInfo") or {})
        print("    enrolment: %s (%s)   lastUpdate: %s"
              % (enr.get("count"), enr.get("type"),
                 (stm.get("lastUpdateSubmitDate") or "")))
        for kind in ("primaryOutcomes", "secondaryOutcomes"):
            for o in (om.get(kind) or []):
                if kind == "secondaryOutcomes" and "--all" not in sys.argv:
                    continue
                print("    [%s] MEASURE: %s" % (kind[:-8].upper(), o.get("measure")))
                if o.get("description"):
                    print("        DESCRIPTION: %s" % o["description"])
                if o.get("timeFrame"):
                    print("        TIMEFRAME: %s" % o["timeFrame"])
        print("")
    if failed:
        print("FETCH FAILED for %d: %s -- nothing is recorded for these."
              % (len(failed), ", ".join(failed)))
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
