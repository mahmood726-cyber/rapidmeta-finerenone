"""How many published systematic reviews identify their trials by REGISTRATION?

THE OBSERVATION THIS TESTS came out of scoping something else. Four published reviews were
fetched to see whether our instruments could be run against them, and none of the four
mentioned a single NCT id. If that holds at scale it is a finding in its own right, and a
larger one than the audit it was scoping:

  Published reviews largely do not identify their included trials by registration. So the
  trial-identity defect found in this project's own flagship is STRUCTURAL IN THE FIELD
  rather than one team's lapse -- and it means published reviews mostly CANNOT BE AUDITED
  for it, by us or by anyone.

That is the different-but-equal argument in its strongest form: our corpus can be checked
and theirs cannot.

CHEAP, AND NEEDS NO INCLUDE-LIST RECOVERY. It counts whether an NCT id appears anywhere in
the full text -- body, tables, references. A review that names registrations is auditable; one
that names none is not. Nothing needs to be resolved.

WHAT IT DOES NOT CLAIM. Not naming a registration is not a defect. Many included trials
predate registration entirely -- one review sampled here runs from 1993. The claim is only
about AUDITABILITY, which is a property of the review as published, and it is stated that way.

RETRIEVAL IS VIA NCBI efetch, NOT the PubMed MCP tool. The MCP tool strips reference lists
and most tables: an earlier scoping run concluded from it that include lists were
unrecoverable, which was true of that tool and false of the source. efetch on db=pmc returns
the full JATS XML with <ref> elements and <table-wrap> intact.
"""
import io
import json
import os
import re
import subprocess
import sys
import time

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(REPO, "scripts"))
import instrument_controls

ESEARCH = ("https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi?db=pmc"
           "&retmax=%d&retmode=json&term=%s")
EFETCH = ("https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi?db=pmc"
          "&id=%s&retmode=xml")
# TWO FRAMES, because the first one did not contain the comparator.
#
# The original sample was PMC open access with "systematic review" and "meta-analysis" in
# the title, and it was reported with the limit "Cochrane Reviews are largely not in PMC".
# THAT LIMIT WAS FALSE: PMC holds 13,628 Cochrane Database Syst Rev records. The comparator
# this programme measures itself against was reachable the whole time and simply was not
# asked for. Run with `cochrane` as the second argument to sample it directly.
FRAMES = {
    "general": ("%22systematic+review%22%5BTitle%5D+AND+%22meta-analysis%22%5BTitle%5D"
                "+AND+2023%3A2026%5Bpdat%5D",
                "review_registration_naming_2026_08_25.jsonl"),
    "cochrane": ("%22Cochrane+Database+Syst+Rev%22%5BJournal%5D+AND+2020%3A2026%5Bpdat%5D",
                 "cochrane_registration_naming_2026_08_25.jsonl"),
}
FRAME = sys.argv[2] if len(sys.argv) > 2 else "general"
TERM, _CACHE_NAME = FRAMES[FRAME]
CACHE = os.path.join(REPO, "outputs", _CACHE_NAME)

NCT = re.compile(r"NCT\d{8}")
REF = re.compile(r"<ref\b")
TAB = re.compile(r"<table-wrap")


def fetch(url, timeout=90):
    try:
        p = subprocess.run(["curl", "-sL", "-m", str(timeout), "-w", "\n%{http_code}", url],
                           capture_output=True, timeout=timeout + 20)
        raw = (p.stdout or b"").decode("utf-8", "replace")
    except Exception as e:
        return None, "%s: %s" % (type(e).__name__, e)
    if "\n" not in raw:
        return None, "no body"
    body, code = raw.rsplit("\n", 1)
    if code.strip() != "200":
        return None, "HTTP %s" % code.strip()
    return body, "ok"


def _title(xml):
    """The article title, or "" -- ONE search, not two.

    The first version guarded with `re.search(r"<article-title>", xml)` and then extracted
    with a DIFFERENT, length-bounded pattern. A title longer than the bound made the guard
    succeed and the extraction return None, so `.group(1)` raised on an article whose only
    unusual property was a long title. Two patterns for one question is the bug.
    """
    m = re.search(r"<article-title>(.*?)</article-title>", xml, re.S)
    if not m:
        return ""
    return " ".join(re.sub(r"<[^>]+>", " ", m.group(1)).split())[:150]


def control():
    """The counter must be able to find an NCT id, and must not invent one."""
    pos = len(set(NCT.findall("...registered as NCT03630081 and NCT02497781...")))
    neg = len(set(NCT.findall("This review cites Smith 2019 and Jones 2021 only.")))
    # THE NEGATIVE CONTROL ASSERTS WHAT THE INSTRUMENT MUST NOT DO, which is find an id
    # where there is none. The first version passed `(label, neg, 0)` -- "must not be 0" --
    # when 0 is the CORRECT answer for text with no ids, so the control refused a working
    # counter. `require_controls` takes (label, actual, must_not_be); the thing it must not
    # do is report a hit, so the actual is "did it find any" and the forbidden value is True.
    instrument_controls.require_controls(
        "reviews-naming-registrations",
        ("text containing two NCT ids", pos, 2),
        ("text containing none must not yield a hit", neg > 0, True))
    return True


def main():
    control()
    want = int(sys.argv[1]) if len(sys.argv) > 1 else 60
    body, why = fetch(ESEARCH % (want, TERM))
    if not body:
        print("REFUSED: the search did not return (%s). NO COUNT IS PRINTED." % why)
        return 2
    try:
        ids = json.loads(body)["esearchresult"]["idlist"]
    except Exception:
        print("REFUSED: the search response could not be parsed. NO COUNT IS PRINTED.")
        return 2

    done = {}
    if os.path.exists(CACHE):
        for line in io.open(CACHE, encoding="utf-8"):
            try:
                r = json.loads(line)
            except ValueError:
                continue
            if r.get("pmcid"):
                done[r["pmcid"]] = r

    raw = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace",
                           write_through=True)

    def log(s):
        raw.write(s + "\n")
        raw.flush()

    log("FRAME: %s" % FRAME)
    log("reviews found in PMC for this frame: %d" % len(ids))
    rows, failed = [], []
    for i, pid in enumerate(ids, 1):
        if pid in done and done[pid].get("status") == "ok":
            rows.append(done[pid])
            continue
        xml, why = fetch(EFETCH % pid)
        if not xml or len(xml) < 2000:
            rec = {"pmcid": pid, "status": "error", "why": why or "body too short"}
            failed.append(rec)
        else:
            n = sorted(set(NCT.findall(xml)))
            rec = {"pmcid": pid, "status": "ok", "bytes": len(xml),
                   "n_nct": len(n), "sample": n[:4],
                   "refs": len(REF.findall(xml)), "tables": len(TAB.findall(xml)),
                   "title": _title(xml)}
            rows.append(rec)
        with io.open(CACHE, "a", encoding="utf-8") as fh:
            fh.write(json.dumps(rec, ensure_ascii=False) + "\n")
        if i % 10 == 0:
            log("  fetched %d/%d" % (i, len(ids)))
        time.sleep(0.4)

    ok = [r for r in rows if r.get("status") == "ok"]
    named = [r for r in ok if r["n_nct"] > 0]
    log("")
    log("reviews retrieved                     : %d   (%d failed to fetch)"
        % (len(ok), len(failed)))
    log("  naming at least one NCT registration: %d   (%.0f%%)"
        % (len(named), 100.0 * len(named) / max(len(ok), 1)))
    log("  naming NONE                         : %d   (%.0f%%)"
        % (len(ok) - len(named), 100.0 * (len(ok) - len(named)) / max(len(ok), 1)))
    log("")
    log("reference lists present in the XML    : %d of %d"
        % (sum(1 for r in ok if r.get("refs", 0) > 5), len(ok)))
    log("tables present                        : %d of %d"
        % (sum(1 for r in ok if r.get("tables", 0) > 0), len(ok)))
    if named:
        log("")
        log("how many registrations, where any are named:")
        for r in sorted(named, key=lambda x: -x["n_nct"])[:10]:
            log("   %-10s %3d ids   %s" % (r["pmcid"], r["n_nct"], r["title"][:70]))
    log("")
    log("NOT NAMING A REGISTRATION IS NOT A DEFECT -- many trials predate registration.")
    log("The claim is about AUDITABILITY: a review that names none cannot be checked for")
    log("trial identity by anyone, including its own authors.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
