"""EVERY-RANK READ -- does any contributing trial register a CLINICAL endpoint at all?

Run across a whole specialty section, so the answer is a measurement rather than an
anecdote. The prior screen read PRIMARY TITLES only; this reads primary, secondary AND
other, on every seeded trial of every topic.

TWO CLAIMS ARE REPORTED SEPARATELY BECAUSE THEY ARE DIFFERENT CLAIMS
    ALL      every seeded trial registers no clinical endpoint at any rank
    MIXED    some do and some do not
Only ALL is unambiguous; MIXED means the topic contains at least one trial that
pre-specified a clinical outcome.

AND A DISTINCTION THAT MATTERS MORE THAN THE COUNT
    "Registers no clinical endpoint" is a statement about the REGISTRATION, not about
    the trial. Two very different situations produce it:

      (a) the trial MEASURED clinical outcomes and reported them without pre-specifying
          them -- the selective-reporting concern, Handbook 6.5 section 8.7;
      (b) the trial was DESIGNED as an immunogenicity, safety or pharmacokinetic study,
          and a synthesis has treated it as an efficacy trial.

    (b) is the more serious finding, and the criticism belongs on the POOLING and not on
    the registration: a phase-3 immunogenicity trial registering immunogenicity endpoints
    is behaving correctly. Where the registration lets the two be told apart -- by its own
    title, or by its primary purpose field -- this reports which. Where it does not, it
    says so.

WHAT THIS DOES NOT ESTABLISH -- written in advance
    - NOT that the published efficacy figure is wrong. It establishes that the quantity
      was not pre-specified in the registration the page keys to.
    - NOT that no clinical endpoint exists in the publication. Registries are amended and
      publications report more than they register; this reads the registration only.
    - NOT a criticism of the trialists. See the distinction above.

USAGE
    python scripts/every_rank_read.py sp-infectious-disease sp-nephrology
    python scripts/every_rank_read.py sp-cardiology sp-dermatology
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
CACHE = os.path.join(REPO, ".every-rank-cache.json")

EFFICACY = re.compile(
    r"incidence of|episode|infection|mortality|death|hospitali|cure|clearance|"
    r"eradicat|relapse|recurren|treatment failure|viral load|suppress|acquisition|"
    r"severe|symptomatic|confirmed case|parasit|culture conver|sputum|stroke|"
    r"myocardial infarction|revasculari|amputation|dialysis|transplant|"
    r"exacerbation|remission|progression", re.I)
NONCLINICAL = re.compile(
    r"antibody|antibodies|titer|titre|immunogenic|seroconver|seroprotect|"
    r"geometric mean|reactogenic|solicited|adverse event|tolerabilit|safety|"
    r"pharmacokinet|concentration|change from baseline in.*(?:level|score)", re.I)
DESIGNED_NONCLINICAL = re.compile(
    r"safety|immunogenic|tolerabilit|pharmacokinet|reactogenic|dose.finding|"
    r"bioequivalence|dose.rang", re.I)

cache = json.load(io.open(CACHE, encoding="utf-8")) if os.path.exists(CACHE) else {}


def fetch(nct):
    if nct in cache:
        return cache[nct]
    try:
        req = urllib.request.Request(API.format(nct), headers={"User-Agent": "rm-er"})
        with urllib.request.urlopen(req, timeout=45) as r:
            d = json.loads(r.read().decode("utf-8"))
        ps = d.get("protocolSection") or {}
        om = ps.get("outcomesModule") or {}
        des = ps.get("designModule") or {}
        rec = {"title": (ps.get("identificationModule") or {}).get("briefTitle", ""),
               "purpose": ((des.get("designInfo") or {}).get("primaryPurpose") or ""),
               "primary": [o.get("measure", "") for o in (om.get("primaryOutcomes") or [])],
               "secondary": [o.get("measure", "") for o in (om.get("secondaryOutcomes") or [])],
               "other": [o.get("measure", "") for o in (om.get("otherOutcomes") or [])]}
    except Exception as e:
        rec = {"error": str(e)[:40]}
    cache[nct] = rec
    time.sleep(0.07)
    return rec


def has_clinical(rec):
    for bucket in ("primary", "secondary", "other"):
        for m in rec.get(bucket) or []:
            if EFFICACY.search(m or "") and not NONCLINICAL.search(m or ""):
                return True
    return False


def designed_nonclinical(rec):
    """Does the registration itself say it is a safety/immunogenicity study?"""
    t = rec.get("title", "")
    return bool(DESIGNED_NONCLINICAL.search(t))


def main() -> int:
    if len(sys.argv) < 3:
        print("usage: every_rank_read.py <section-id> <next-section-id>")
        return 2
    start, end = sys.argv[1], sys.argv[2]
    idx = io.open(os.path.join(REPO, "index.html"), encoding="utf-8",
                  errors="replace").read()
    a, b = idx.find('id="%s"' % start), idx.find('id="%s"' % end)
    seg = idx[a:b if b > a else len(idx)]
    pages, seen = [], set()
    for m in re.finditer(r'href="([A-Za-z0-9_]+\.html)"', seg):
        p = m.group(1)
        if p in seen:
            continue
        seen.add(p)
        if os.path.exists(os.path.join(REPO, p)) and \
           os.path.getsize(os.path.join(REPO, p)) > 10000:
            pages.append(p)

    print("%s -- topics: %d" % (start, len(pages)))
    print()
    ALL, MIXED, FINE, NOTRIAL = [], [], [], []
    for p in pages:
        html = io.open(os.path.join(REPO, p), encoding="utf-8", errors="replace").read()
        m = AUTO.search(html)
        ids = sorted(set(NCT.findall(m.group(1)))) if m else []
        if not ids:
            NOTRIAL.append(p)
            continue
        without, with_, designed = [], [], []
        for n in ids:
            r = fetch(n)
            if r.get("error"):
                continue
            if has_clinical(r):
                with_.append(n)
            else:
                without.append(n)
                if designed_nonclinical(r):
                    designed.append(n)
        json.dump(cache, io.open(CACHE, "w", encoding="utf-8"), ensure_ascii=False)
        if not without:
            FINE.append(p)
        elif not with_:
            ALL.append((p, len(ids), len(designed)))
            print("ALL    %-50s k=%-2d  of which the REGISTRATION ITSELF says "
                  "safety/immunogenicity: %d" % (p[:49], len(ids), len(designed)))
        else:
            MIXED.append((p, len(with_), len(without), len(designed)))
            print("MIXED  %-50s %d with / %d without  (designed non-clinical: %d)"
                  % (p[:49], len(with_), len(without), len(designed)))

    n = len(pages)
    print()
    print("=" * 96)
    print("EVERY-RANK READ -- %s" % start)
    print("=" * 96)
    print("  topics read                                     : %d" % n)
    print("  ALL seeded trials register NO clinical endpoint  : %d" % len(ALL))
    print("  MIXED -- some do, some do not                    : %d" % len(MIXED))
    print("  every trial registers one                        : %d" % len(FINE))
    print("  no registration seeded                           : %d" % len(NOTRIAL))
    des_all = sum(d for _, _, d in ALL)
    tot_all = sum(k for _, k, _ in ALL)
    print()
    print("  Within the ALL group: %d of %d trials have a registration whose OWN TITLE"
          % (des_all, tot_all))
    print("  says safety / immunogenicity / pharmacokinetics -- i.e. the trial was")
    print("  DESIGNED as such and a synthesis has treated it as an efficacy trial.")
    print("  The remaining %d are the selective-reporting shape instead." % (tot_all - des_all))
    print()
    print("  ONLY 'ALL' IS AN UNAMBIGUOUS CLAIM. MIXED means the topic contains at least")
    print("  one trial that did pre-specify a clinical outcome.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
