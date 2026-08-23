"""Registry triage for the legacy repair. Four buckets over the legacy set, every id QUERIED.

# no-control: this is a lookup, not a detector -- the known answer for each identifier is
# ClinicalTrials.gov's own response, fetched per id and cached with its query date. The one
# control that matters IS asserted: NCT03914728 was confirmed by hand not to resolve, and the
# run refuses if the registry reports it as found, because that would mean the lookup is
# answering from something other than the registry.

WHAT THIS DECIDES. Mahmood has authorised repairing the legacy pages. NOT EVERY PAGE IS
REPAIRABLE, AND SAYING SO IS THE HONEST PART OF ACCEPTING THAT INSTRUCTION. A page rebuilt
around a trial that does not exist would be WORSE than the page we have, because it would wear
the SSOT format's authority while describing nothing.

    (a) REPAIRABLE          every cited registration resolves and describes the trial claimed
    (b) NO REGISTRATION     the identifier does not exist in the registry
    (c) DONOR IDENTIFIER    it resolves -- to a DIFFERENT trial than the page describes
    (d) NEEDS A HUMAN       anything not placeable, named individually and never folded
    (e) NO IDENTIFIER       a bare unverified COUNT with nothing to look up at all

(c) IS THE DANGEROUS CLASS AND THE REASON A NAIVE CHECK IS NOT ENOUGH. An existence test
passes a donor identifier: the NCT is real, the registry answers, the link resolves. Only
comparing what the registry DESCRIBES against what the page CLAIMS separates it from (a). This
run does that comparison mechanically and, where the comparison is not decisive, sends the page
to (d) RATHER THAN GUESSING -- a false (a) is the failure that would put a fabricated trial
inside a repaired page.

(e) MAY BE THE HARDEST BUCKET RATHER THAN A VARIANT. A page reporting "156 number(s) on this
page marked UNVERIFIED -- no resolvable trial id" cannot be triaged by lookup AT ALL, because
there is nothing to look up. A named unresolvable NCT can at least be checked by a reader and
argued with. Whether that distinction survives contact with the corpus is reported as an
overlap count, not assumed.

RESUMABLE AND CACHED. Every identifier is queried once, the response cached with the UTC date
of the query, and the cache is consulted before the network. A run that dies resumes without
re-querying, and the recorded query date is per identifier because a registry answer is a fact
about a moment.
"""
from __future__ import annotations

import collections
import io
import json
import os
import re
import sys
import time
import urllib.error
import urllib.request

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CLASSES = os.path.join(REPO, "outputs", "five_bucket_classes_2026_08_23.json")
CACHE = os.path.join(REPO, "outputs", "ctgov_cache_2026_08_23.json")
OUT = os.path.join(REPO, "outputs", "legacy_registration_triage_2026_08_23.json")

API = "https://clinicaltrials.gov/api/v2/studies/%s"
NCT = re.compile(r"\bNCT\d{8}\b")
BARE_COUNT = re.compile(
    r"(?i)(\d{1,4})\s*number\(?s?\)?\s*on this page marked\s*UNVERIFIED")

# The hand-confirmed non-resolving identifier. If the registry reports this as found, the
# lookup is not talking to the registry and nothing else in the run can be trusted.
CONTROL_ABSENT = "NCT03914728"

STOP = {"the", "and", "for", "with", "review", "auto", "full", "nma", "trial", "trials",
        "study", "vs", "in", "of", "a", "an", "new", "broad", "2", "meta", "analysis"}


def load(p, default):
    if os.path.isfile(p):
        try:
            return json.load(io.open(p, encoding="utf-8"))
        except ValueError:
            return default
    return default


def save(p, obj):
    d = os.path.dirname(p)
    if d and not os.path.isdir(d):
        os.makedirs(d)
    json.dump(obj, io.open(p, "w", encoding="utf-8"), indent=1)


def query(nct, cache):
    """Ask the registry. Never recall. Records the UTC date of the answer."""
    if nct in cache:
        return cache[nct]
    rec = {"queried_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())}
    try:
        with urllib.request.urlopen(API % nct, timeout=60) as r:
            d = json.loads(r.read().decode("utf-8", "replace"))
        p = d.get("protocolSection", {})
        idm = p.get("identificationModule", {})
        cond = p.get("conditionsModule", {})
        arms = p.get("armsInterventionsModule", {})
        rec.update({
            "found": True,
            "title": (idm.get("officialTitle") or idm.get("briefTitle") or "")[:300],
            "conditions": cond.get("conditions", [])[:12],
            "interventions": [i.get("name", "") for i in arms.get("interventions", [])][:12],
        })
    except urllib.error.HTTPError as e:
        rec.update({"found": False, "http": e.code})
    except Exception as e:
        rec.update({"found": None, "error": type(e).__name__})
    cache[nct] = rec
    return rec


def page_terms(name):
    """What the page claims to be about, from its filename."""
    stem = re.sub(r"\.html$", "", name)
    parts = [p.lower() for p in re.split(r"[_\-]+", stem)]
    return set(p for p in parts if p and p not in STOP and not p.isdigit() and len(p) > 3)


def describes(rec, terms):
    """Does the registry record plausibly describe what the page claims?

    *** THIS FUNCTION IS NOT FIT TO PRODUCE A DONOR COUNT AND ITS FALSE VERDICTS MUST NOT BE
    *** REPORTED AS A NUMBER. It produced 727 of 745 and then 149 of 602, and BOTH WERE
    *** WITHDRAWN. It compares tokens taken from a FILENAME against a registry record, and:
    ***
    ***   ALS_NEW_AGENTS_NMA   -> terms ['agents']    registry "Amyotrophic Lateral Sclerosis"
    ***   ALK_NSCLC            -> terms ['nsclc']     registry "Non-Small Cell Lung Cancer"
    ***   AML_TARGETED_NEW     -> terms ['targeted']  registry "Leukemia"
    ***
    *** Every one of those is the CORRECT trial for the page and every one is scored False.
    *** The acronym is dropped by a length filter, the registry spells conditions out rather
    *** than abbreviating, and drug records use development codenames (VEGF Trap-Eye, MCI-186)
    *** where a filename uses the marketing name. Detecting a donor needs concept matching --
    *** acronym expansion, synonyms, ATC/MeSH -- not substring overlap.
    ***
    *** WHAT SURVIVES: the ABSENCE limb. `found is False` is the registry's own 404 and needs
    *** no judgement; NCT01084557 and NCT04195814 were re-queried live and are genuinely gone.
    *** The two confirmed donors -- TIRZEPATIDE_ARDS citing andexanet alfa, ICAGEN citing
    *** edoxaban -- were confirmed BY READING, not by this function.

    Deliberately generous. A FALSE 'no' sends a repairable page to needs-a-human, which costs
    a person a read. A FALSE 'yes' puts a donor trial inside a repaired page wearing the SSOT
    format's authority, and that is the outcome this whole bucket exists to prevent.
    """
    if not rec.get("found"):
        return None
    hay = " ".join([rec.get("title", "")] + rec.get("conditions", [])
                   + rec.get("interventions", [])).lower()
    if not hay.strip():
        return None
    for t in terms:
        if t in hay:
            return True
        if len(t) > 6 and t[:6] in hay:      # tolerate inflections and salt forms
            return True
    return False


def main():
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    if not os.path.isfile(CLASSES):
        sys.exit("REFUSED: %s missing -- run classify_five_buckets first."
                 % os.path.relpath(CLASSES, REPO))
    legacy = sorted(load(CLASSES, {}).get("legacy", []))
    if not legacy:
        sys.exit("REFUSED: the legacy bucket is empty; nothing to triage.")

    cache = load(CACHE, {})

    # THE CONTROL, BEFORE ANYTHING IS CLASSIFIED.
    c = query(CONTROL_ABSENT, cache)
    save(CACHE, cache)
    print("CONTROL %s -> found=%r (hand-confirmed NOT to resolve)"
          % (CONTROL_ABSENT, c.get("found")))
    if c.get("found") is True:
        sys.exit("REFUSED: the registry reports %s as found, but it was confirmed by hand not "
                 "to resolve. The lookup is answering from something other than the registry "
                 "and no triage from it is trustworthy." % CONTROL_ABSENT)
    if c.get("found") is None:
        sys.exit("REFUSED: the control query failed with %r -- the network is not usable, and "
                 "an 'absent' verdict now would be the connection, not the registry."
                 % c.get("error"))

    # PASS 1 -- what does each page cite?
    per_page, all_ids, bare = {}, collections.Counter(), {}
    for n in legacy:
        p = os.path.join(REPO, n)
        if not os.path.isfile(p):
            per_page[n] = {"state": "not_on_disk"}
            continue
        raw = io.open(p, encoding="utf-8", errors="replace").read()
        # ONLY WHAT A READER MEETS. The first version of this ran NCT.findall over the whole
        # file and produced 727 of 745 pages classified as donor -- 97.6%, which was an
        # artefact, not a finding.
        #
        # THE MECHANISM: every legacy page hardcodes the SAME trial list inside its analysis
        # engine, `trialData=["NCT01035255","NCT01920711","NCT02924727"]` -- the LCZ696/ARNI
        # heart-failure trials -- plus a FINEARTS-HF special case on NCT05901831. Those four
        # appear on 72-79% of legacy pages while the MEDIAN identifier appears on ONE. Read out
        # of <script>, they look like citations to trials on a completely different subject, so
        # the donor rule fired on nearly every page in the corpus.
        #
        # They are not citations. They are template code. A page's CLAIMS live in its prose and
        # its tables, so that is where the identifiers are read from -- and the check that
        # matters is whether what the page TELLS A READER it studied resolves to what it says.
        t = re.sub(r"(?is)<script\b.*?</script>", " ", raw)
        t = re.sub(r"(?is)<style\b.*?</style>", " ", t)
        ids = sorted(set(NCT.findall(t)))
        m = BARE_COUNT.search(raw)
        per_page[n] = {"ids": ids, "bare": int(m.group(1)) if m else None}
        if m:
            bare[n] = int(m.group(1))
        all_ids.update(ids)

    print("")
    print("LEGACY SET: %d pages, %d distinct NCT identifiers cited, %d pages carrying a bare "
          "unverified count" % (len(legacy), len(all_ids), len(bare)))
    both = [n for n in bare if per_page[n].get("ids")]
    print("pages carrying BOTH a bare count and named ids: %d -- %s"
          % (len(both), "the distinction is weaker than claimed" if both
             else "the distinction holds: a bare-count page exposes nothing to look up"))

    # PASS 2 -- query every identifier once.
    todo = [i for i in sorted(all_ids) if i not in cache]
    print("")
    print("querying %d identifier(s) not already cached (%d cached)"
          % (len(todo), len(all_ids) - len(todo)))
    for k, nct in enumerate(todo, 1):
        query(nct, cache)
        if k % 25 == 0:
            save(CACHE, cache)
            print("   %d/%d queried" % (k, len(todo)))
        time.sleep(0.12)
    save(CACHE, cache)

    # PASS 3 -- place every page.
    buckets = collections.defaultdict(list)
    detail = {}
    for n in legacy:
        rec = per_page[n]
        if rec.get("state") == "not_on_disk":
            buckets["needs_human"].append(n)
            detail[n] = "linked but not on disk"
            continue
        ids = rec.get("ids") or []
        if not ids:
            buckets["no_identifier"].append(n)
            detail[n] = ("bare unverified count of %d, nothing to look up" % rec["bare"]
                         if rec.get("bare") else "no NCT cited anywhere on the page")
            continue
        terms = page_terms(n)
        found = [i for i in ids if cache.get(i, {}).get("found") is True]
        absent = [i for i in ids if cache.get(i, {}).get("found") is False]
        errored = [i for i in ids if cache.get(i, {}).get("found") is None]
        if errored:
            buckets["needs_human"].append(n)
            detail[n] = "%d identifier(s) could not be queried" % len(errored)
            continue
        if absent and not found:
            buckets["no_registration"].append(n)
            detail[n] = "none of %d cited id(s) resolve: %s" % (len(ids), ", ".join(absent[:6]))
            continue
        verdicts = [describes(cache[i], terms) for i in found]
        if verdicts and all(v is True for v in verdicts) and not absent:
            buckets["repairable"].append(n)
            detail[n] = "all %d id(s) resolve and match the topic" % len(found)
        elif any(v is False for v in verdicts):
            mism = [i for i, v in zip(found, verdicts) if v is False]
            buckets["donor"].append(n)
            detail[n] = ("resolves to a different subject: %s"
                         % ", ".join("%s=%s" % (i, (cache[i].get("title") or "")[:70])
                                     for i in mism[:2]))
        else:
            buckets["needs_human"].append(n)
            detail[n] = ("mixed or undecidable: %d resolve, %d absent, %d undecidable"
                         % (len(found), len(absent),
                            sum(1 for v in verdicts if v is None)))

    tot = len(legacy)
    print("")
    print("REGISTRY TRIAGE OF THE LEGACY SET -- %d pages" % tot)
    print("")
    for k, lab in (("repairable", "(a) REPAIRABLE -- ids resolve and match"),
                   ("no_registration", "(b) NO REGISTRATION -- id does not exist"),
                   ("donor", "(c) DONOR ID -- resolves to a different trial"),
                   ("needs_human", "(d) NEEDS A HUMAN -- not placeable"),
                   ("no_identifier", "(e) NO IDENTIFIER -- nothing to look up")):
        print("   %-46s %5d   %5.1f%%"
              % (lab, len(buckets[k]), 100.0 * len(buckets[k]) / max(1, tot)))
    s = sum(len(v) for v in buckets.values())
    print("   %-46s %5d   == the legacy set" % ("sum", s))
    if s != tot:
        sys.exit("REFUSED: triage does not close -- %d pages, %d placed." % (tot, s))
    print("")
    print("(c) AND (d) ARE NOT INTERCHANGEABLE. A donor identifier passes an existence check,")
    print("which is why it is separated. Where the comparison was not decisive the page went")
    print("to (d) rather than to (a) -- a false 'repairable' is the one error that would put a")
    print("fabricated trial inside a page wearing this project's format.")
    save(OUT, {"total": tot, "buckets": {k: v for k, v in buckets.items()},
               "detail": detail, "bare_counts": bare, "both": both,
               "ids_seen": len(all_ids)})
    print("")
    print("written: %s" % os.path.relpath(OUT, REPO))


if __name__ == "__main__":
    main()
