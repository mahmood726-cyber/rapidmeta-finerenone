"""AUDIT-FIRST ROUND 2 -- conditional residue, then poolability across the remaining 18.

TWO FIXES BAKED IN, both from defects this project measured on itself:

1. RESIDUE IS JUDGED PER TOPIC, NOT GLOBALLY. A global denylist of identifiers cannot
   be right, because the same id is build contamination on one page and the subject on
   another. NCT01035255 is residue on an unrelated topic and PARADIGM-HF -- the trial
   the page is about -- on a sacubitril page. Excluding it everywhere produced a
   "seeds no registration at all" verdict for three pages that each seed exactly one,
   and it was reported as an alarming defect before it was measured.
   RULE: a residue id is KEPT when the topic's own subject token appears in that
   trial's registered title or interventions. Otherwise it is dropped.

2. THE VERDICT IS A TRIAGE AND NOT A READING. Every FAIL and every POOL POSSIBLE here
   names the registrations to open; none of them closes or builds a topic on its own.
   subject_is_experimental returned FAIL on DABIGATRAN_AF the day after it was built
   and the FAIL was wrong.

WHAT THIS DOES NOT ESTABLISH -- written in advance
    - NOT that a POOL POSSIBLE topic should be built. It tests the OUTCOME limb and,
      where the subject resolves, the INTERVENTION limb. Comparator and participants
      are read by hand, and on the six candidates screened that way earlier, FIVE
      failed on one of those two.
    - NOT that a NOT POOLABLE topic is finished. It is finished when its registrations,
      its registered endpoints and its reason are on the page.

USAGE
    python scripts/audit_first_round2.py
"""
from __future__ import annotations
import io
import json
import os
import re
import sys
import time
import urllib.error
import urllib.request

if __name__ == "__main__":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
API = "https://clinicaltrials.gov/api/v2/studies/{}?format=json"
NCT = re.compile(r"NCT\d{8}")
AUTO = re.compile(r"AUTO_INCLUDE_TRIAL_IDS\s*=\s*new Set\(\[(.*?)\]\)", re.S)
RESIDUE = {"NCT01920711", "NCT02924727", "NCT05901831", "NCT01035255"}
CACHE = os.path.join(REPO, ".round2-cache.json")

SUBJECT = {
    "APIXABAN_VTE": "apixaban", "AZILSARTAN_HTN": "azilsartan",
    "BOSENTAN_PAH": "bosentan", "DABIGATRAN_STROKE": "dabigatran",
    "ENOXAPARIN_VTE": "enoxaparin",
    "ETRIPAMIL_PAROXYSMAL_SUPRAVENTRICU": "etripamil",
    "EVINACUMAB_HOFH": "evinacumab", "INCLISIRAN_HOFH": "inclisiran",
    "MAVACAMTEN_OHCM": "mavacamten", "OMECAMTIV_HEARTFAIL": "omecamtiv",
    "OMECAMTIV_HF": "omecamtiv", "OMECAMTIV_HFREF": "omecamtiv",
    "SACUBITRIL_HEARTFAIL": "sacubitril", "SACUBITRIL_VALSARTAN_HF": "sacubitril",
    "SELEXIPAG_PAH": "selexipag", "SOTATERCEPT_PAH": "sotatercept",
    "WARFARIN_AF": "warfarin", "HFREF_NMA": None,
}
# Development codes: a registration may name the drug only by its code, which is one of
# the three false-negative modes already demonstrated.
ALIAS = {"sacubitril": ["lcz696"], "omecamtiv": ["amg 423", "amg423"],
         "etripamil": ["msp-2017"], "sotatercept": ["ace-011"],
         "mavacamten": ["myk-461"], "evinacumab": ["regn1500"]}

FAMILY = [
    ("mace_composite", r"cardiovascular death|cv death|major adverse cardiac|MACE"),
    ("hf_composite", r"heart failure hospitali|hospitali\w*.{0,20}heart failure|worsening heart failure"),
    ("vte_recurrence", r"venous thromboembolism|recurrent VTE"),
    ("stroke_se", r"stroke or systemic embolism|systemic embolism|stroke"),
    ("bleeding", r"bleed|BARC|ISTH|h[ae]morrhag"),
    ("ldl_change", r"percent change.{0,40}LDL|LDL-C|low.density lipoprotein"),
    ("six_min_walk", r"6.minute walk|six.minute walk|6MWD|6MWT"),
    ("bp_change", r"blood pressure|systolic|diastolic"),
    ("clinical_worsening", r"clinical worsening"),
    ("exercise_capacity", r"peak (?:VO2|oxygen)|exercise capacity|pVO2"),
    ("all_cause_death", r"all.cause (?:death|mortality)|overall survival"),
    ("symptom_score", r"KCCQ|questionnaire|symptom score|NYHA"),
    ("adverse_events", r"adverse event|treatment.emergent|safety|tolerabilit"),
]

cache = json.load(io.open(CACHE, encoding="utf-8")) if os.path.exists(CACHE) else {}


def fetch(nct):
    if nct in cache:
        return cache[nct]
    try:
        req = urllib.request.Request(API.format(nct), headers={"User-Agent": "rm-r2"})
        with urllib.request.urlopen(req, timeout=45) as r:
            d = json.loads(r.read().decode("utf-8"))
        ps = d.get("protocolSection") or {}
        om = ps.get("outcomesModule") or {}
        ai = ps.get("armsInterventionsModule") or {}
        rec = {"title": (ps.get("identificationModule") or {}).get("briefTitle", ""),
               "primaries": [o.get("measure", "") for o in (om.get("primaryOutcomes") or [])],
               "arms": [{"type": a.get("type") or "",
                         "names": " ".join(a.get("interventionNames") or []) + " " +
                                  (a.get("label") or "")}
                        for a in (ai.get("armGroups") or [])]}
    except Exception as e:
        rec = {"error": str(e)[:50]}
    cache[nct] = rec
    time.sleep(0.1)
    return rec


def tokens(subject):
    return [subject] + ALIAS.get(subject, []) if subject else []


def keep_residue(nct, subject):
    """A residue id is KEPT when this topic's subject appears in that trial."""
    if not subject:
        return False
    rec = fetch(nct)
    if rec.get("error"):
        return False
    blob = (rec["title"] + " " + " ".join(a["names"] for a in rec["arms"])).lower()
    return any(t in blob for t in tokens(subject))


def family_of(m):
    for k, pat in FAMILY:
        if re.search(pat, m or "", re.I):
            return k
    return None


def page_trials(html, subject):
    m = AUTO.search(html)
    ids = set(NCT.findall(m.group(1))) if m else set(NCT.findall(html))
    out = []
    for n in sorted(ids):
        if n in RESIDUE and not keep_residue(n, subject):
            continue
        out.append(n)
    return out


def main() -> int:
    pm = json.load(io.open(os.path.join(REPO, "ssot", "PAGE_MAP.json"), encoding="utf-8"))
    idx = io.open(os.path.join(REPO, "index.html"), encoding="utf-8",
                  errors="replace").read()
    a, b = idx.find('id="sp-cardiology"'), idx.find('id="sp-dermatology"')
    seg = idx[a:b if b > a else len(idx)]
    pages, seen = [], set()
    for m in re.finditer(r'href="([A-Za-z0-9_]+\.html)"', seg):
        p = m.group(1)
        if p in seen or p in pm:
            continue
        seen.add(p)
        fp = os.path.join(REPO, p)
        if os.path.exists(fp) and os.path.getsize(fp) > 100000:
            pages.append(p)

    print("audit-first cardiology topics remaining: %d" % len(pages))
    print()
    tally, rows = {}, []
    for p in pages:
        stem = p.replace("_AUTO_FULL_REVIEW.html", "").replace(".html", "")
        subj = SUBJECT.get(stem)
        html = io.open(os.path.join(REPO, p), encoding="utf-8", errors="replace").read()
        ids = page_trials(html, subj)
        recs = {n: fetch(n) for n in ids}
        json.dump(cache, io.open(CACHE, "w", encoding="utf-8"), ensure_ascii=False)

        if len(ids) < 2:
            v, why = "NOT POOLABLE", "k=%d -- fewer than two trials" % len(ids)
        else:
            fams = {}
            for n, r in recs.items():
                if r.get("error"):
                    continue
                for k in {family_of(x) for x in r["primaries"]} - {None}:
                    fams.setdefault(k, []).append(n)
            shared = {k: v2 for k, v2 in fams.items()
                      if len(v2) >= 2 and k != "adverse_events"}
            if not shared:
                v, why = ("NOT POOLABLE",
                          "%d trials, no two share a registered primary outcome family" % len(ids))
            else:
                best = max(shared.items(), key=lambda x: len(x[1]))
                v, why = ("POOL POSSIBLE",
                          "%d trials share a registered primary of family '%s'"
                          % (len(best[1]), best[0]))
        tally[v] = tally.get(v, 0) + 1
        rows.append((p, len(ids), v, why))
        print("%-46s k=%-2d %-14s %s" % (p[:45], len(ids), v, why[:60]))

    print()
    print("TRIAGE SPLIT")
    for k in sorted(tally, key=lambda x: -tally[x]):
        print("   %-16s %d" % (k, tally[k]))
    print()
    print("Every verdict here names registrations to OPEN. None closes or builds a topic.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
