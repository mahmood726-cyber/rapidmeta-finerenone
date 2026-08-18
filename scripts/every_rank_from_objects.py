"""EVERY-RANK READ, for pages whose trials live in the SSOT OBJECT, not a JS seed.

The seed-based reader could not see 29 of cardiology's 53 pages, because the v1
projector generation holds its trials in `inputs.trials[]` rather than in an embedded
`AUTO_INCLUDE_TRIAL_IDS`. This reads those, so the section can be reported whole
instead of as the 24-page subset the other method happened to be able to see.

Same question, same rank coverage: does ANY contributing trial register a clinical
endpoint at primary, secondary or other rank?
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
CACHE = os.path.join(REPO, ".every-rank-cache.json")

EFFICACY = re.compile(
    r"incidence of|episode|infection|mortality|death|hospitali|cure|clearance|"
    r"eradicat|relapse|recurren|treatment failure|viral load|suppress|acquisition|"
    r"severe|symptomatic|confirmed case|parasit|culture conver|sputum|stroke|"
    r"myocardial infarction|revasculari|amputation|dialysis|transplant|"
    r"exacerbation|remission|progression|walk|worsening", re.I)
NONCLINICAL = re.compile(
    r"antibody|antibodies|titer|titre|immunogenic|seroconver|seroprotect|"
    r"geometric mean|reactogenic|solicited|adverse event|tolerabilit|safety|"
    r"pharmacokinet|concentration", re.I)
DESIGNED = re.compile(
    r"safety|immunogenic|tolerabilit|pharmacokinet|reactogenic|dose.finding|"
    r"bioequivalence|dose.rang|open.label extension|extension study", re.I)

cache = json.load(io.open(CACHE, encoding="utf-8")) if os.path.exists(CACHE) else {}


def fetch(nct):
    if nct in cache:
        return cache[nct]
    try:
        req = urllib.request.Request(API.format(nct), headers={"User-Agent": "rm-obj"})
        with urllib.request.urlopen(req, timeout=45) as r:
            d = json.loads(r.read().decode("utf-8"))
        ps = d.get("protocolSection") or {}
        om = ps.get("outcomesModule") or {}
        rec = {"title": (ps.get("identificationModule") or {}).get("briefTitle", ""),
               "primary": [o.get("measure", "") for o in (om.get("primaryOutcomes") or [])],
               "secondary": [o.get("measure", "") for o in (om.get("secondaryOutcomes") or [])],
               "other": [o.get("measure", "") for o in (om.get("otherOutcomes") or [])]}
    except Exception as e:
        rec = {"error": str(e)[:40]}
    cache[nct] = rec
    time.sleep(0.07)
    return rec


def has_clinical(r):
    for b in ("primary", "secondary", "other"):
        for m in r.get(b) or []:
            if EFFICACY.search(m or "") and not NONCLINICAL.search(m or ""):
                return True
    return False


def main() -> int:
    pm = json.load(io.open(os.path.join(REPO, "ssot", "PAGE_MAP.json"), encoding="utf-8"))
    idx = io.open(os.path.join(REPO, "index.html"), encoding="utf-8",
                  errors="replace").read()
    a, b = idx.find('id="sp-cardiology"'), idx.find('id="sp-dermatology"')
    seg = idx[a:b]
    pages, seen = [], set()
    for m in re.finditer(r'href="([A-Za-z0-9_]+\.html)"', seg):
        p = m.group(1)
        if p not in seen:
            seen.add(p)
            pages.append(p)

    ALL, MIXED, FINE, NOOBJ = [], [], [], []
    AUTO = re.compile(r"AUTO_INCLUDE_TRIAL_IDS")
    for p in pages:
        fp = os.path.join(REPO, p)
        if not os.path.exists(fp) or os.path.getsize(fp) < 10000:
            continue
        html = io.open(fp, encoding="utf-8", errors="replace").read()
        if AUTO.search(html):
            continue                      # the other reader already covered these
        obj_rel = pm.get(p)
        if not obj_rel or not os.path.exists(os.path.join(REPO, obj_rel)):
            NOOBJ.append(p)
            continue
        obj = json.load(io.open(os.path.join(REPO, obj_rel), encoding="utf-8"))
        ncts = []
        for t in ((obj.get("inputs") or {}).get("trials") or []):
            n = t.get("nct") or t.get("registration")
            if isinstance(n, str) and n.startswith("NCT"):
                ncts.append(n)
        ncts = sorted(set(ncts))
        if not ncts:
            NOOBJ.append(p)
            continue
        with_, without, designed = [], [], []
        for n in ncts:
            r = fetch(n)
            if r.get("error"):
                continue
            if has_clinical(r):
                with_.append(n)
            else:
                without.append(n)
                if DESIGNED.search(r.get("title", "")):
                    designed.append(n)
        json.dump(cache, io.open(CACHE, "w", encoding="utf-8"), ensure_ascii=False)
        if not without:
            FINE.append(p)
        elif not with_:
            ALL.append((p, len(ncts), len(designed)))
            print("ALL    %-50s k=%-2d  designed non-clinical: %d"
                  % (p[:49], len(ncts), len(designed)))
        else:
            MIXED.append((p, len(with_), len(without), len(designed)))
            print("MIXED  %-50s %d with / %d without  (designed: %d)"
                  % (p[:49], len(with_), len(without), len(designed)))

    n = len(ALL) + len(MIXED) + len(FINE) + len(NOOBJ)
    print()
    print("=" * 92)
    print("OBJECT-BASED READ -- the cardiology pages the seed reader could not see")
    print("=" * 92)
    print("  pages read from objects            : %d" % n)
    print("  ALL trials register no clinical    : %d" % len(ALL))
    print("  MIXED                              : %d" % len(MIXED))
    print("  every trial registers one          : %d" % len(FINE))
    print("  object has no usable registration  : %d" % len(NOOBJ))
    for p in NOOBJ:
        print("      %s" % p)
    return 0


if __name__ == "__main__":
    sys.exit(main())
