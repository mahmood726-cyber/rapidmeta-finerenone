"""INFECTIOUS DISEASE TRIAGE -- the whole section, before anything is opened by hand.

CARRIES THREE THINGS ACROSS FROM CARDIOLOGY, all of them things that cost something:

1. RESIDUE IS CONDITIONAL FROM THE START. A global identifier denylist produced two
   wrong verdicts and one wrong report in cardiology, because the same id is build
   contamination on one page and the subject trial on another. Here a residue id is
   KEPT when the topic's own subject appears in that trial's registered title or
   interventions.

2. THE SUBJECT IS RESOLVED TO AN ARM, not to the trial record. A drug-name search that
   matches anywhere produced three cardiology pages whose titled drug was the
   comparator in every trial. Development codes are matched as well as generic names.

3. AN EXPLICIT UNREGISTERED-ENDPOINT SCREEN. The sharpest instance found anywhere was
   a malaria vaccine trial with EIGHTEEN registered outcome measures, none of which
   mentions malaria, under a page reporting a clinical malaria episode ratio. Vaccine
   trials commonly register IMMUNOGENICITY and SAFETY while the literature reports
   EFFICACY, so this class may be systematic here rather than incidental. Every topic
   is flagged when NO trial registers a clinical-efficacy-shaped primary.

WHAT THIS DOES NOT ESTABLISH -- written in advance
    - NOT that a POOL POSSIBLE topic should be built. It tests the OUTCOME limb and,
      where the subject resolves, the INTERVENTION limb. Comparator and participants
      are read by hand. In cardiology, SIX of seven topics that reached that stage
      failed on one of those two -- including the only one this screen called POOL
      POSSIBLE.
    - NOT that a NOT POOLABLE topic is finished. It is finished when its registrations,
      its registered endpoints and its reason are on the page.
"""
from __future__ import annotations
import io
import json
import os
import re
import sys
import time
import urllib.request

if __name__ == "__main__":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
API = "https://clinicaltrials.gov/api/v2/studies/{}?format=json"
NCT = re.compile(r"NCT\d{8}")
AUTO = re.compile(r"AUTO_INCLUDE_TRIAL_IDS\s*=\s*new Set\(\[(.*?)\]\)", re.S)
RESIDUE = {"NCT01920711", "NCT02924727", "NCT05901831", "NCT01035255"}
CACHE = os.path.join(REPO, ".id-triage-cache.json")

# A registered primary that is a CLINICAL EFFICACY endpoint, as opposed to
# immunogenicity, reactogenicity or safety.
EFFICACY = re.compile(
    r"incidence of|episode|infection|mortality|death|hospitali|cure|clearance|"
    r"eradicat|relapse|recurren|failure|response|viral load|suppress|acquisition|"
    r"severe|symptomatic|confirmed case|parasit", re.I)
NONCLINICAL = re.compile(
    r"antibody|antibodies|titer|titre|immunogenic|seroconver|seroprotect|geometric mean|"
    r"reactogenic|solicited|adverse event|tolerabilit|safety|pharmacokinet", re.I)

FAMILY = [
    ("mortality", r"mortalit|death|survival"),
    ("infection_incidence", r"incidence|episode|infection|acquisition|confirmed case"),
    ("cure_clearance", r"cure|clearance|eradicat|response|resolution"),
    ("viral_suppression", r"viral load|suppress|undetectable|HIV-1 RNA"),
    ("relapse_recurrence", r"relapse|recurren|failure"),
    ("hospitalisation", r"hospitali"),
    ("immunogenicity", r"antibody|antibodies|titer|titre|seroconver|geometric mean"),
    ("safety", r"adverse event|reactogenic|solicited|tolerabilit|safety"),
]

cache = json.load(io.open(CACHE, encoding="utf-8")) if os.path.exists(CACHE) else {}


def fetch(nct):
    if nct in cache:
        return cache[nct]
    try:
        req = urllib.request.Request(API.format(nct), headers={"User-Agent": "rm-id"})
        with urllib.request.urlopen(req, timeout=45) as r:
            d = json.loads(r.read().decode("utf-8"))
        ps = d.get("protocolSection") or {}
        om = ps.get("outcomesModule") or {}
        ai = ps.get("armsInterventionsModule") or {}
        rec = {"title": (ps.get("identificationModule") or {}).get("briefTitle", ""),
               "primaries": [o.get("measure", "") for o in (om.get("primaryOutcomes") or [])],
               "n_secondary": len(om.get("secondaryOutcomes") or []),
               "arms": [{"type": a.get("type") or "",
                         "names": (" ".join(a.get("interventionNames") or []) + " " +
                                   (a.get("label") or ""))}
                        for a in (ai.get("armGroups") or [])]}
    except Exception as e:
        rec = {"error": str(e)[:40]}
    cache[nct] = rec
    time.sleep(0.08)
    return rec


def subject_of(page):
    stem = page.replace("_AUTO_FULL_REVIEW.html", "").replace("_REVIEW.html", "")
    stem = stem.replace(".html", "")
    tok = stem.split("_")[0].lower()
    return tok if len(tok) >= 4 else None


def family_of(m):
    for k, pat in FAMILY:
        if re.search(pat, m or "", re.I):
            return k
    return None


def main() -> int:
    idx = io.open(os.path.join(REPO, "index.html"), encoding="utf-8",
                  errors="replace").read()
    a = idx.find('id="sp-infectious-disease"')
    b = idx.find('id="sp-nephrology"')
    seg = idx[a:b if b > a else len(idx)]
    pm = json.load(io.open(os.path.join(REPO, "ssot", "PAGE_MAP.json"), encoding="utf-8"))
    pages, seen = [], set()
    for m in re.finditer(r'href="([A-Za-z0-9_]+\.html)"', seg):
        p = m.group(1)
        if p in seen:
            continue
        seen.add(p)
        fp = os.path.join(REPO, p)
        if os.path.exists(fp) and os.path.getsize(fp) > 10000 and p not in pm:
            pages.append(p)

    print("INFECTIOUS DISEASE -- topics not yet done: %d" % len(pages))
    print()
    tally, unreg = {}, []
    for p in pages:
        subj = subject_of(p)
        html = io.open(os.path.join(REPO, p), encoding="utf-8", errors="replace").read()
        m = AUTO.search(html)
        ids = sorted(set(NCT.findall(m.group(1)))) if m else sorted(set(NCT.findall(html)))
        keep = []
        for n in ids:
            if n in RESIDUE:
                r = fetch(n)
                blob = (r.get("title", "") + " " +
                        " ".join(x["names"] for x in r.get("arms", []))).lower()
                if not (subj and subj in blob):
                    continue
            keep.append(n)
        recs = {n: fetch(n) for n in keep}
        json.dump(cache, io.open(CACHE, "w", encoding="utf-8"), ensure_ascii=False)

        # unregistered-endpoint screen: does ANY trial register a clinical primary?
        clinical = 0
        for r in recs.values():
            if r.get("error"):
                continue
            for pr in r["primaries"]:
                if EFFICACY.search(pr) and not NONCLINICAL.search(pr):
                    clinical += 1
                    break
        if keep and clinical == 0:
            unreg.append((p, len(keep)))

        if len(keep) < 2:
            v, why = "NOT POOLABLE", "k=%d" % len(keep)
        else:
            fams = {}
            for n, r in recs.items():
                if r.get("error"):
                    continue
                for k in {family_of(x) for x in r["primaries"]} - {None}:
                    fams.setdefault(k, []).append(n)
            shared = {k: v2 for k, v2 in fams.items()
                      if len(v2) >= 2 and k not in ("safety",)}
            if not shared:
                v, why = "NOT POOLABLE", "%d trials, no shared registered primary family" % len(keep)
            else:
                best = max(shared.items(), key=lambda x: len(x[1]))
                v = "POOL POSSIBLE"
                why = "%d share '%s'" % (len(best[1]), best[0])
        tally[v] = tally.get(v, 0) + 1
        print("%-50s k=%-2d %-14s %s" % (p[:49], len(keep), v, why[:44]))

    print()
    print("TRIAGE SPLIT")
    for k in sorted(tally, key=lambda x: -tally[x]):
        print("   %-16s %d" % (k, tally[k]))
    print()
    print("NO TRIAL REGISTERS A CLINICAL-EFFICACY PRIMARY: %d topic(s)" % len(unreg))
    for p, k in unreg:
        print("   %-50s k=%d" % (p[:49], k))
    print()
    print("Every verdict names registrations to OPEN. None closes or builds a topic.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
