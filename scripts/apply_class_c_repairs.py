"""Class C repairs from NAFIS_REPAIR_QUEUE_v1: withdraw four wrong evidence blocks.

WHAT THESE ARE. Four rows whose numeric estimate is correct and untouched, but
whose `evidence[0]` quotes a completely unrelated document -- an orthodontics
Cochrane review under a DAPT trial, a dupilumab nasal-polyps quote under two
benralizumab COPD rows, VIALE-A's adverse-event text under QUAZAR-AML. Class C
is number-affecting: NO, so no cross-family certification is required and these
are the four items that can clear immediately.

WITHDRAWN, NOT DELETED. The queue's own rule is quarantine rather than delete:
the row and its history stay visible. Setting `evidence:[]` would leave a reader
unable to distinguish "we looked and found nothing" from "we removed something
wrong", and a later audit would have no record that the block ever existed. Each
block is therefore replaced by a withdrawal notice carrying the reason, the date,
and the first 200 characters of what was there, so the defect stays inspectable.

NOT DONE HERE. R-09 is Class B -- a chimera of two trials -- and needs
adjudication, not a script. The upstream writer that seeded it
(scripts/clone_tier4_batch_B.py) is fixed separately, because fixing the row
without fixing the writer re-injects the defect on the next clone run.
"""
import datetime
import io
import json
import os
import re
import sys

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

NOW = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

# (file, nct, item, why)
TARGETS = [
    ("DAPT_DE_ESCALATION_PCI_REVIEW.html", "NCT03971500", "R-02",
     "Quoted an orthodontics Cochrane review (overjet and ANB in malocclusion) "
     "under ULTIMATE-DAPT. Wrong document entirely. Not replaced with a guess: "
     "the block must be repopulated from ULTIMATE-DAPT's own primary publication "
     "when that is verified. The trial's HR is unchanged and remains separately "
     "pending verification."),
    ("COPD_BIOLOGICS_BROAD_REVIEW.html", "NCT02138916", "R-03a",
     "Quoted dupilumab in chronic rhinosinusitis with nasal polyps (SINUS-24 / "
     "SINUS-52 nasal polyp score) under GALATHEA, a benralizumab COPD trial. "
     "Wrong drug, wrong disease, wrong outcome. The identical text also appeared "
     "on TERRANOVA, and that duplication across two rows is the tell."),
    ("COPD_BIOLOGICS_BROAD_REVIEW.html", "NCT02155660", "R-03b",
     "Byte-identical dupilumab nasal-polyps quote, here under TERRANOVA. Same "
     "defect as GALATHEA in the same app."),
    ("AML_VEN_FLT3_NMA_REVIEW.html", "NCT01757535", "R-05",
     "Carried VIALE-A's adverse-event text and VIALE-A's DOI "
     "(10.1056/NEJMoa2012971) under QUAZAR-AML. QUAZAR-AML's own paper is "
     "10.1056/NEJMoa2004444. Name, PMID and hazard ratio are correct and "
     "untouched."),
]


def find_entry(s, nct):
    """The realData entry for one NCT. Keys are UNQUOTED JS identifiers here."""
    for m in re.finditer(r"[{,]\s*['\"]?%s['\"]?\s*:\s*\{" % re.escape(nct), s):
        start = s.index("{", m.end() - 1)
        d = 0
        for j in range(start, len(s)):
            if s[j] == "{":
                d += 1
            elif s[j] == "}":
                d -= 1
                if d == 0:
                    body = s[start:j + 1]
                    if "publishedHR" in body or "baseline" in body or "tE" in body:
                        return start, j + 1, body
                    break
    return None, None, None


def find_evidence(body):
    m = re.search(r"evidence\s*:\s*\[", body)
    if not m:
        return None, None
    k = m.end() - 1
    d = 0
    for j in range(k, len(body)):
        if body[j] == "[":
            d += 1
        elif body[j] == "]":
            d -= 1
            if d == 0:
                return k, j + 1
    return None, None


def main():
    log = []
    for f, nct, item, why in TARGETS:
        if not os.path.exists(f):
            print("MISSING FILE %s -- skipped" % f)
            log.append({"item": item, "file": f, "status": "FILE NOT FOUND"})
            continue
        s = open(f, encoding="utf-8", errors="replace").read()
        a, b, body = find_entry(s, nct)
        if body is None:
            print("%s %s: realData entry not found -- skipped" % (item, nct))
            log.append({"item": item, "file": f, "nct": nct,
                        "status": "ENTRY NOT FOUND"})
            continue
        ka, kb = find_evidence(body)
        if ka is None:
            print("%s %s: no evidence array -- nothing to withdraw" % (item, nct))
            log.append({"item": item, "file": f, "nct": nct,
                        "status": "NO EVIDENCE ARRAY"})
            continue
        old = body[ka:kb]
        if "WITHDRAWN" in old:
            print("%s %s: already withdrawn -- idempotent, no change" % (item, nct))
            log.append({"item": item, "file": f, "nct": nct, "status": "ALREADY DONE"})
            continue
        excerpt = re.sub(r"\s+", " ", old)[:200].replace('"', "'")
        new = ('[{label:"Evidence withdrawn",source:"WITHDRAWN %s (%s)",'
               'text:"%s Withdrawn text began: %s",'
               'withdrawn:true,withdrawnUtc:"%s",repairItem:"%s"}]'
               % (NOW[:10], item, why.replace('"', "'"), excerpt, NOW, item))
        body2 = body[:ka] + new + body[kb:]
        s2 = s[:a] + body2 + s[b:]
        open(f, "w", encoding="utf-8").write(s2)
        print("%s %-8s %-38s withdrew %d chars -> %d"
              % (item, nct, f[:38], len(old), len(new)))
        log.append({"item": item, "file": f, "nct": nct, "status": "WITHDRAWN",
                    "old_chars": len(old), "excerpt": excerpt, "why": why,
                    "utc": NOW})
    out = os.path.join("outputs", "class_c_repairs_%s.json" % NOW[:10])
    os.makedirs("outputs", exist_ok=True)
    json.dump({"applied_utc": NOW, "source": "NAFIS_REPAIR_QUEUE_v1.md",
               "class": "C -- provenance only, no displayed number changes",
               "certification_required": False, "items": log},
              open(out, "w", encoding="utf-8"), indent=1, ensure_ascii=False)
    done = sum(1 for x in log if x["status"] == "WITHDRAWN")
    print("\n%d/%d withdrawn | log: %s" % (done, len(TARGETS), out))
    return 0 if done or all(x["status"] == "ALREADY DONE" for x in log) else 1


if __name__ == "__main__":
    sys.exit(main())
