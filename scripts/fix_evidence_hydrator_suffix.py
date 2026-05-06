#!/usr/bin/env python3
# sentinel:skip-file — developer tool; hardcoded ROOT is intentional (local Finrenone checkout only)
"""Fix: EvidenceHydrator 400-errors on cohort-suffixed trial IDs.

Found during portfolio audit smoke test: 3 apps trigger CT.gov 400/404
on hydrator fetch:
  INTENSIVE_BP_REVIEW.html  NCT01206062_SENIOR, NCT01206062_CKD
  RENAL_DENERV_REVIEW.html  NCT02439749_ON, NCT02439749_OFF

These suffix-IDs are valid INTERNAL keys (same NCT split into multiple
cohorts in realData) but CT.gov rejects them because the v2 API expects
a bare `NCT\\d{7,8}` ID. Result: EvidenceHydrator fails silently but
logs console.error, and those trials never get Demographics/RoB
evidence populated.

Fix: strip everything after the first valid NCT prefix before the fetch
URL is built, and cache under the stripped key so cohort-suffixed
duplicates of the same NCT share one cache entry.
"""
import argparse, pathlib, sys

ROOT = pathlib.Path(__file__).resolve().parent.parent

OLD = (
    "            async fetchCtgovEvidence(nct) {\n"
    "                try {\n"
    "                    const fields = 'protocolSection.designModule,protocolSection.eligibilityModule,resultsSection.baselineCharacteristicsModule';\n"
    "                    const url = `https://clinicaltrials.gov/api/v2/studies/${encodeURIComponent(nct)}?fields=${fields}&format=json`;\n"
    "                    const r = await fetch(url);\n"
    "                    if (!r.ok) return [];\n"
    "                    const data = await r.json();\n"
    "                    return this.parseToEvidenceItems(nct, data);\n"
    "                } catch (e) { return []; }\n"
    "            },"
)
NEW = (
    "            async fetchCtgovEvidence(nct) {\n"
    "                /* Strip cohort suffix (e.g. NCT01206062_SENIOR -> NCT01206062)\n"
    "                   before hitting CT.gov v2, which rejects anything that isn't\n"
    "                   a bare NCT\\d{7,8}. Cohort-suffixed trials in realData share\n"
    "                   the same real NCT so one fetch covers all cohorts. */\n"
    "                const baseMatch = String(nct).match(/^(NCT\\d{7,8})/);\n"
    "                const baseNct = baseMatch ? baseMatch[1] : nct;\n"
    "                try {\n"
    "                    const fields = 'protocolSection.designModule,protocolSection.eligibilityModule,resultsSection.baselineCharacteristicsModule';\n"
    "                    const url = `https://clinicaltrials.gov/api/v2/studies/${encodeURIComponent(baseNct)}?fields=${fields}&format=json`;\n"
    "                    const r = await fetch(url);\n"
    "                    if (!r.ok) return [];\n"
    "                    const data = await r.json();\n"
    "                    return this.parseToEvidenceItems(baseNct, data);\n"
    "                } catch (e) { return []; }\n"
    "            },"
)


def apply_to_file(path: pathlib.Path, dry_run: bool) -> str:
    text = path.read_text(encoding="utf-8", newline="")
    if "Strip cohort suffix" in text:
        return f"SKIP {path.name}: already-migrated"
    crlf = "\r\n" in text
    work = text.replace("\r\n", "\n") if crlf else text
    if OLD not in work:
        return f"SKIP {path.name}: EvidenceHydrator.fetchCtgovEvidence not present or differs"
    if work.count(OLD) != 1:
        return f"FAIL {path.name}: OLD matched {work.count(OLD)} times (expected 1)"
    work = work.replace(OLD, NEW, 1)
    if not dry_run:
        out = work.replace("\n", "\r\n") if crlf else work
        path.write_text(out, encoding="utf-8", newline="")
    return f"OK   {path.name}"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--apply", action="store_true")
    args = ap.parse_args()
    if not (args.dry_run or args.apply): ap.error("pass --dry-run or --apply")
    targets = sorted(ROOT.glob("*_REVIEW.html"))
    ok = skip = fail = 0
    for p in targets:
        r = apply_to_file(p, dry_run=args.dry_run)
        if r.startswith("OK"): ok += 1
        elif r.startswith("SKIP"): skip += 1
        else: fail += 1
        if not r.startswith("SKIP"): print(r)
    print(f"\nSummary: {len(targets)} | {ok} fix | {skip} skip | {fail} fail | mode={'dry-run' if args.dry_run else 'apply'}")
    if fail: sys.exit(1)


if __name__ == "__main__":
    main()
