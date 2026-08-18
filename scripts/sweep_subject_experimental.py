"""Run subject_is_experimental across every remaining audit-first cardiology topic.

One run, before any topic is opened by hand. It tells us which are OLMESARTAN-shaped
-- the topic named for a drug that is only ever the comparator.
"""
import io
import json
import os
import re
import sys
import time
import urllib.error
import urllib.request

sys.path.insert(0, r"F:\rapidmeta-ssot-shell\scripts")
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

import subject_is_experimental_gate as G  # noqa: E402

REPO = r"F:\rapidmeta-ssot-shell"
NCT = re.compile(r"NCT\d{8}")
AUTO_SET = re.compile(r"AUTO_INCLUDE_TRIAL_IDS\s*=\s*new Set\(\[(.*?)\]\)", re.S)
RESIDUE = {"NCT01920711", "NCT02924727", "NCT05901831", "NCT01035255"}

# Subject token per page. Derived from the page name, then hand-checked: a token that
# is a class rather than a drug cannot resolve to an arm and must return UNRESOLVED
# rather than a false verdict.
SUBJECT = {
    "APIXABAN_VTE": "apixaban", "AZILSARTAN_HTN": "azilsartan",
    "BOSENTAN_PAH": "bosentan", "DABIGATRAN_AF": "dabigatran",
    "DABIGATRAN_STROKE": "dabigatran", "EDOXABAN_VTE": "edoxaban",
    "ENOXAPARIN_VTE": "enoxaparin",
    "ETRIPAMIL_PAROXYSMAL_SUPRAVENTRICU": "etripamil",
    "EVINACUMAB_HOFH": "evinacumab", "FONDAPARINUX_VTE": "fondaparinux",
    "INCLISIRAN_HOFH": "inclisiran", "MAVACAMTEN_OHCM": "mavacamten",
    "OMECAMTIV_HEARTFAIL": "omecamtiv", "OMECAMTIV_HF": "omecamtiv",
    "OMECAMTIV_HFREF": "omecamtiv", "RIOCIGUAT_PAH": "riociguat",
    "SACUBITRIL_HEARTFAIL": "sacubitril", "SACUBITRIL_VALSARTAN_HF": "sacubitril",
    "SELEXIPAG_PAH": "selexipag", "SOTATERCEPT_PAH": "sotatercept",
    "WARFARIN_AF": "warfarin", "MIPOMERSEN_HOFH": "mipomersen",
}

CACHE = os.path.join(REPO, ".triage-registry-cache-full.json")
cache = {}
if os.path.exists(CACHE):
    try:
        cache = json.load(io.open(CACHE, encoding="utf-8"))
    except Exception:
        cache = {}


def fetch(nct):
    if nct in cache:
        return cache[nct]
    try:
        req = urllib.request.Request(G.API.format(nct), headers={"User-Agent": "rm-sweep"})
        with urllib.request.urlopen(req, timeout=45) as r:
            d = json.loads(r.read().decode("utf-8"))
        ai = (d.get("protocolSection") or {}).get("armsInterventionsModule") or {}
        rec = {"protocolSection": {"armsInterventionsModule":
                                   {"armGroups": ai.get("armGroups") or []}}}
    except Exception:
        rec = {"protocolSection": {}}
    cache[nct] = rec
    time.sleep(0.12)
    return rec


def page_trials(html):
    m = AUTO_SET.search(html)
    src = m.group(1) if m else html
    return sorted(set(NCT.findall(src)) - RESIDUE)


pm = json.load(io.open(os.path.join(REPO, "ssot", "PAGE_MAP.json"), encoding="utf-8"))
idx = io.open(os.path.join(REPO, "index.html"), encoding="utf-8", errors="replace").read()
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

print("remaining audit-first cardiology pages: %d" % len(pages))
print()
tally = {}
for p in pages:
    stem = p.replace("_AUTO_FULL_REVIEW.html", "").replace(".html", "")
    subj = SUBJECT.get(stem)
    html = io.open(os.path.join(REPO, p), encoding="utf-8", errors="replace").read()
    ids = page_trials(html)
    if not subj:
        print("%-46s SUBJECT TOKEN NOT SET -- not judged" % p[:45])
        tally["NOT JUDGED"] = tally.get("NOT JUDGED", 0) + 1
        continue
    if not ids:
        print("%-46s no registration seeded -- UNRESOLVED" % p[:45])
        tally["UNRESOLVED"] = tally.get("UNRESOLVED", 0) + 1
        continue
    studies = {n: fetch(n) for n in ids}
    v, why, roles = G.assess(subj, studies)
    tally[v] = tally.get(v, 0) + 1
    print("%-46s %-11s %-11s %s" % (p[:45], subj[:10], v,
                                    " ".join("%s=%s" % (n[-5:], r[:4]) for n, r in
                                             sorted(roles.items()))))
    if v == "FAIL":
        print("%-46s   %s" % ("", why[:120]))
    json.dump(cache, io.open(CACHE, "w", encoding="utf-8"), ensure_ascii=False)

print()
print("SWEEP RESULT")
for k in sorted(tally, key=lambda x: -tally[x]):
    print("   %-14s %d" % (k, tally[k]))
