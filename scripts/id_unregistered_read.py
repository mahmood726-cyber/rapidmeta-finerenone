"""Read the 14 flagged ID topics: is a clinical endpoint registered at ANY rank?

TWO QUESTIONS, KEPT SEPARATE, because they have different answers and different
consequences:

  1. DOES THE TOPIC HOLD UP? If the efficacy endpoint is a registered SECONDARY, the
     page may be sound with a risk-of-bias flag -- exactly how ANSWER-HF resolved on
     the ARNI flagship, and the precedent Mahmood ruled on.

  2. IS THE PATTERN REAL? Across the 14, how many register NO clinical endpoint at
     ANY rank -- primary or secondary? THAT number is the finding, and it is a claim
     about the evidence base rather than about our extraction.

WHY IT MATTERS BEYOND THE 14
    If a trial registers only immunogenicity and safety while the literature reports
    efficacy, the gap is between what was PRE-SPECIFIED and what was PUBLISHED. That
    applies to every synthesis in the field, not only ours.

THE PRIOR SCREEN READ PRIMARY TITLES ONLY, which is why this exists. A topic flagged
there can still be sound.

WHAT THIS DOES NOT ESTABLISH -- written in advance
    - NOT a rate. 14 flagged of 62 is a screen output; only the confirmed count is a
      reading, and 14 is too few to be a rate either way. Two findings have already
      shrunk under their own denominators in this programme, both because the first
      number came from a screen.
    - NOT that a trial with no registered clinical endpoint reported one improperly.
      It establishes that the reported quantity was not pre-specified, which is a
      risk-of-bias judgement under Handbook 6.5 section 8.7 and not an eligibility one.
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

FLAGGED = ["AMOXICILLIN_AOM", "DELAMANID_TB", "DORAVIRINE_HIV", "INFLUENZA_RECOMBINANT",
           "LENACAPAVIR_HIV", "LINEZOLID_MRSA", "MENACWY_BOOSTER", "POSACONAZOLE_FUNGAL",
           "PREVNAR15_PNEUMO", "REMDESIVIR_COVID", "RIFAPENTINE_TB", "TECOVIRIMAT_MPOX",
           "THIAMINE_SEPSIS", "TIGECYCLINE_INFECTION"]

EFFICACY = re.compile(
    r"incidence of|episode|infection|mortality|death|hospitali|cure|clearance|"
    r"eradicat|relapse|recurren|treatment failure|viral load|suppress|acquisition|"
    r"severe|symptomatic|confirmed case|parasit|culture conver|sputum", re.I)
NONCLINICAL = re.compile(
    r"antibody|antibodies|titer|titre|immunogenic|seroconver|seroprotect|"
    r"geometric mean|reactogenic|solicited|adverse event|tolerabilit|safety|"
    r"pharmacokinet|concentration", re.I)

CACHE = os.path.join(REPO, ".id-unreg-cache.json")
cache = json.load(io.open(CACHE, encoding="utf-8")) if os.path.exists(CACHE) else {}


def fetch(nct):
    if nct in cache:
        return cache[nct]
    try:
        req = urllib.request.Request(API.format(nct), headers={"User-Agent": "rm-unreg"})
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
    time.sleep(0.08)
    return rec


def clinical(measures):
    return [m for m in measures if EFFICACY.search(m or "") and not NONCLINICAL.search(m or "")]


def main() -> int:
    confirmed, holds_up, unreadable = [], [], []
    print("Reading the 14 flagged topics at EVERY rank.")
    print()
    for stem in FLAGGED:
        page = stem + "_AUTO_FULL_REVIEW.html"
        fp = os.path.join(REPO, page)
        if not os.path.exists(fp):
            unreadable.append((stem, "page not found"))
            continue
        html = io.open(fp, encoding="utf-8", errors="replace").read()
        m = AUTO.search(html)
        ids = sorted(set(NCT.findall(m.group(1)))) if m else []
        any_primary, any_secondary, none_at_all = [], [], []
        for n in ids:
            r = fetch(n)
            if r.get("error"):
                continue
            p, s, o = clinical(r["primary"]), clinical(r["secondary"]), clinical(r["other"])
            if p:
                any_primary.append(n)
            elif s or o:
                any_secondary.append(n)
            else:
                none_at_all.append(n)
        json.dump(cache, io.open(CACHE, "w", encoding="utf-8"), ensure_ascii=False)

        if any_primary:
            verdict = "SCREEN WAS WRONG -- a clinical PRIMARY exists after all"
            holds_up.append(stem)
        elif any_secondary and not none_at_all:
            verdict = "HOLDS UP -- clinical endpoint registered as a SECONDARY on every trial"
            holds_up.append(stem)
        elif any_secondary:
            verdict = ("MIXED -- secondary on %d, NOTHING at any rank on %d"
                       % (len(any_secondary), len(none_at_all)))
            confirmed.append(stem)
        elif none_at_all:
            verdict = ("CONFIRMED -- NO clinical endpoint at ANY rank on %d of %d trials"
                       % (len(none_at_all), len(ids)))
            confirmed.append(stem)
        else:
            verdict = "UNREADABLE -- no registration resolved"
            unreadable.append((stem, "no registration resolved"))
        print("%-24s k=%-2d  %s" % (stem[:23], len(ids), verdict))
        if none_at_all:
            print("%-26s  no clinical endpoint anywhere: %s" % ("", ", ".join(none_at_all[:6])))

    print()
    print("=" * 92)
    print("THE TWO ANSWERS, KEPT SEPARATE")
    print("=" * 92)
    print("  flagged by the title screen           : 14 of 62")
    print("  CONFIRMED on reading every rank       : %d of 14" % len(confirmed))
    print("  hold up (endpoint registered lower)   : %d of 14" % len(holds_up))
    print("  unreadable                            : %d of 14" % len(unreadable))
    print()
    print("  confirmed: %s" % ", ".join(confirmed))
    print()
    print("14 flagged is a SCREEN output. %d confirmed is a READING. Neither is a rate,"
          % len(confirmed))
    print("and this file does not offer one.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
