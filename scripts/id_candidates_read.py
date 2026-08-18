"""Read the 26 ID POOL-POSSIBLE candidates on ALL FOUR LIMBS, in one batch.

Cardiology's lesson: the OUTCOME limb passes and the other three close the topic. Six
of seven candidates that reached hand-reading there failed on comparator or participants,
including the only one its screen called poolable.

TWO SHAPES TO WATCH FOR SPECIFICALLY, both learned in cardiology:

  COMPARATOR-AS-SUBJECT -- the page's titled drug is the comparator in every trial.
  Three instances in cardiology. Especially likely where a newer agent is tested against
  an established one, which is the normal design in anti-infectives. AND ARM TYPES ARE
  UNRELIABLE: RE-LY typed all three of its arms ACTIVE_COMPARATOR including the
  experimental ones, so a type-only check reaches the right answer for the wrong reason
  or the wrong answer outright.

  PREVENTION POOLED WITH TREATMENT -- closed EDOXABAN_VTE in cardiology, and endemic
  here: prophylaxis and treatment trials of one agent, where the event counted means a
  different thing because in one the infection has not happened yet.

Reports per topic: interventions and their arm types, comparators, conditions, and the
registered primaries -- the four limbs side by side, so the verdict is a reading.
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
CACHE = os.path.join(REPO, ".id-cand-cache.json")
cache = json.load(io.open(CACHE, encoding="utf-8")) if os.path.exists(CACHE) else {}

PREVENTION = re.compile(r"prevent|prophyla|pre-exposure|preexposure|vaccin", re.I)
TREATMENT = re.compile(r"treatment of|therapy for|treat\b|cure|eradicat", re.I)


def fetch(nct):
    if nct in cache:
        return cache[nct]
    try:
        req = urllib.request.Request(API.format(nct), headers={"User-Agent": "rm-cand"})
        with urllib.request.urlopen(req, timeout=45) as r:
            d = json.loads(r.read().decode("utf-8"))
        ps = d.get("protocolSection") or {}
        om = ps.get("outcomesModule") or {}
        ai = ps.get("armsInterventionsModule") or {}
        des = ps.get("designModule") or {}
        rec = {
            "title": (ps.get("identificationModule") or {}).get("briefTitle", ""),
            "conditions": (ps.get("conditionsModule") or {}).get("conditions") or [],
            "purpose": ((des.get("designInfo") or {}).get("primaryPurpose") or ""),
            "primaries": [o.get("measure", "") for o in (om.get("primaryOutcomes") or [])],
            "arms": [{"type": a.get("type") or "",
                      "label": a.get("label") or "",
                      "iv": " ".join(a.get("interventionNames") or [])}
                     for a in (ai.get("armGroups") or [])],
        }
    except Exception as e:
        rec = {"error": str(e)[:40]}
    cache[nct] = rec
    time.sleep(0.07)
    return rec


def subject_of(page):
    stem = page.replace("_AUTO_FULL_REVIEW.html", "").replace("_REVIEW.html", "")
    tok = stem.replace(".html", "").split("_")[0].lower()
    return tok if len(tok) >= 4 else None


def main() -> int:
    pm = json.load(io.open(os.path.join(REPO, "ssot", "PAGE_MAP.json"), encoding="utf-8"))
    idx = io.open(os.path.join(REPO, "index.html"), encoding="utf-8",
                  errors="replace").read()
    a, b = idx.find('id="sp-infectious-disease"'), idx.find('id="sp-nephrology"')
    seg = idx[a:b]
    pages, seen = [], set()
    for m in re.finditer(r'href="([A-Za-z0-9_]+\.html)"', seg):
        p = m.group(1)
        if p in seen or p in pm:
            continue
        seen.add(p)
        fp = os.path.join(REPO, p)
        if os.path.exists(fp) and os.path.getsize(fp) > 10000:
            pages.append(p)

    print("candidates to read: %d" % len(pages))
    print()
    out = {}
    for page in pages:
        subj = subject_of(page)
        html = io.open(os.path.join(REPO, page), encoding="utf-8", errors="replace").read()
        m = AUTO.search(html)
        ids = sorted(set(NCT.findall(m.group(1))) - RESIDUE) if m else []
        rows = [dict(nct=n, **fetch(n)) for n in ids]
        json.dump(cache, io.open(CACHE, "w", encoding="utf-8"), ensure_ascii=False)
        out[page] = rows

        print("=" * 100)
        print("%s   subject '%s'  k=%d" % (page[:60], subj, len(rows)))
        subj_exp, subj_comp, prev, treat, conds = 0, 0, 0, 0, set()
        for r in rows:
            if r.get("error"):
                print("   %s FETCH FAILED" % r["nct"])
                continue
            conds |= set(c.lower() for c in r["conditions"])
            blob = " ".join(x["iv"] + " " + x["label"] for x in r["arms"]).lower()
            exp = any(subj and subj in (x["iv"] + " " + x["label"]).lower()
                      and x["type"] == "EXPERIMENTAL" for x in r["arms"])
            anywhere = bool(subj and subj in blob)
            if exp:
                subj_exp += 1
            elif anywhere:
                subj_comp += 1
            t = r["title"]
            if PREVENTION.search(t):
                prev += 1
            elif TREATMENT.search(t):
                treat += 1
            print("   %s %-62s [%s]" % (r["nct"], t[:62], r.get("purpose", "")[:10]))
            print("        conditions: %s" % ", ".join(r["conditions"])[:74])
            for x in r["arms"][:4]:
                print("        [%-18s] %-30s %s" % (x["type"][:18], x["label"][:29],
                                                    x["iv"][:38]))
            for p in r["primaries"][:2]:
                print("        PRIMARY: %s" % p[:84])
        flags = []
        if subj_exp == 0 and subj_comp:
            flags.append("COMPARATOR-AS-SUBJECT: experimental in 0, comparator in %d" % subj_comp)
        if prev and treat:
            flags.append("PREVENTION+TREATMENT mixed: %d prevention, %d treatment" % (prev, treat))
        if len(conds) > 1:
            flags.append("conditions differ: %s" % "; ".join(sorted(conds))[:70])
        for f in flags:
            print("   >>> %s" % f)
        print()

    json.dump(out, io.open(os.path.join(REPO, ".id-cand-read.json"), "w",
                           encoding="utf-8"), ensure_ascii=False, indent=1)
    print("written .id-cand-read.json")
    return 0


if __name__ == "__main__":
    sys.exit(main())
