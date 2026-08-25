"""Does `Carter 1970` identify one reference INSIDE the review that uses it?

WHY THIS IS THE RIGHT NEXT QUESTION. Stage B measured an author-year label against all of
PubMed and found recall 20/20, resolved 0/20, median result set 147. But a Cochrane label is
never used against all of PubMed. It is used inside one review, whose bibliography holds a
few dozen references. If the label is unique THERE, the join is achievable without any schema
change: resolve the label within the review's own reference list, then take the PMID to
stage A, which already recovers the registration 32/34 with zero wrong answers.

So the question is not "how ambiguous is Carter 1970 in the world" but "how ambiguous is it
where it is actually used".

WHAT IS MEASURED, per review:
  * how many references yield a (surname, year) label at all -- a reference with no parseable
    author or year cannot be addressed by a label of that form, and that is a real limit on
    the route rather than a parsing nuisance
  * how many labels are shared by two or more references in the SAME bibliography

The reportable quantity is the fraction of labels that are UNIQUE within their own review.

SUBSTRATE. The 61 Cochrane reviews from `cochrane_registration_naming_2026_08_25.jsonl` whose
PMC deposit carried a parseable reference list, 4,256 references in total. These are the
reviews' full bibliographies -- included studies, excluded studies, methods citations -- not
only the included trials, so the collision rate here is an UPPER bound on the ambiguity a
label faces among included studies alone. Stated, not buried.

CONTROLS, both directions, before any count is printed:
  positive  two references by the same surname and year in one bibliography MUST collide
  negative  a bibliography whose labels are all distinct MUST report zero collisions
A collision detector that cannot report zero is not measuring collisions.
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
LEDGER = os.path.join(REPO, "outputs", "cochrane_registration_naming_2026_08_25.jsonl")
CACHE = os.path.join(REPO, "outputs", "pmc_refs_cache")
OUT = os.path.join(REPO, "outputs", "label_within_bibliography_2026_08_25.json")

EFETCH = ("https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi"
          "?db=pmc&retmode=xml&id=%s")

REF = re.compile(r"<ref\b.*?</ref>", re.S | re.I)
SURNAME = re.compile(r"<surname>([^<]{1,60})</surname>", re.I)
YEAR = re.compile(r"<year[^>]*>(\d{4})</year>", re.I)


def label_of(ref_xml):
    """(surname, year) for one reference, or None when either part is absent."""
    s = SURNAME.search(ref_xml)
    y = YEAR.search(ref_xml)
    if not s or not y:
        return None
    return (s.group(1).strip().lower(), y.group(1))


def labels_in(xml):
    """Every reference's label, with None kept so the unparseable ones stay counted."""
    return [label_of(r) for r in REF.findall(xml or "")]


def collisions(labels):
    """(n_labelled, n_unique, n_in_a_collision). Ignores the unparseable."""
    got = [l for l in labels if l is not None]
    seen = {}
    for l in got:
        seen[l] = seen.get(l, 0) + 1
    uniq = sum(1 for v in seen.values() if v == 1)
    coll = sum(v for v in seen.values() if v > 1)
    return len(got), uniq, coll


def run_controls():
    """The shared assertion, both directions, before any finding is printed."""
    from instrument_controls import require_controls
    same = [("carter", "1970"), ("carter", "1970"), ("coope", "1986")]
    dist = [("carter", "1970"), ("coope", "1986"), ("shep", "1991")]
    _, _, c_same = collisions(same)
    _, _, c_dist = collisions(dist)
    # The negative control is a FLAG, not a count. Written first as
    # ("...reports zero", c_dist, 0) it asserted "must not be 0" when 0 is the correct
    # answer -- the control refused a working instrument. A negative control names the
    # case the instrument must not FLAG, so the value passed has to be the flag.
    require_controls(
        "label_within_bibliography",
        ("two references sharing surname and year collide", c_same, 2),
        ("a bibliography of distinct labels is FLAGGED as having a collision",
         c_dist > 0, True))


def fetch(pmcid):
    os.makedirs(CACHE, exist_ok=True)
    fp = os.path.join(CACHE, "%s.xml" % pmcid)
    if os.path.exists(fp) and os.path.getsize(fp) > 800:
        return io.open(fp, encoding="utf-8", errors="replace").read()
    for attempt in (1, 2, 3):
        r = subprocess.run(["curl", "-sS", "-g", "--max-time", "120", EFETCH % pmcid],
                           capture_output=True)
        body = (r.stdout or b"").decode("utf-8", "replace")
        if "<ref" in body and len(body) > 800:
            io.open(fp, "w", encoding="utf-8").write(body)
            return body
        time.sleep(2 * attempt)
    return None


def main():
    run_controls()
    raw = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace",
                           write_through=True)

    def log(s):
        raw.write(s + chr(10))
        raw.flush()

    targets = []
    for line in io.open(LEDGER, encoding="utf-8"):
        try:
            d = json.loads(line)
        except ValueError:
            continue
        if d.get("status") == "ok" and d.get("refs", 0) > 0:
            targets.append(d)

    log("reviews with a parsed reference list: %d" % len(targets))
    log("")

    rows, missing = [], 0
    for i, t in enumerate(targets, 1):
        xml = fetch(t["pmcid"])
        if xml is None:
            missing += 1
            rows.append({"pmcid": t["pmcid"], "status": "MISSING"})
            log("[%2d/%d] PMC%-9s MISSING -- no payload after 3 attempts"
                % (i, len(targets), t["pmcid"]))
            continue
        labs = labels_in(xml)
        n_lab, uniq, coll = collisions(labs)
        rows.append({"pmcid": t["pmcid"], "status": "ok", "n_refs": len(labs),
                     "n_labelled": n_lab, "unique": uniq, "in_collision": coll,
                     "title": (t.get("title") or "")[:90]})
        log("[%2d/%d] PMC%-9s refs=%-4d labelled=%-4d unique=%-4d collided=%-3d  %s"
            % (i, len(targets), t["pmcid"], len(labs), n_lab, uniq, coll,
               (t.get("title") or "")[:44]))
        time.sleep(0.34)

    ok = [r for r in rows if r["status"] == "ok"]
    if not ok:
        log("")
        log("NOT MEASURABLE: no reference list was obtained, so nothing is reported.")
        return 0

    refs = sum(r["n_refs"] for r in ok)
    lab = sum(r["n_labelled"] for r in ok)
    uniq = sum(r["unique"] for r in ok)
    coll = sum(r["in_collision"] for r in ok)
    log("")
    log("reviews measured             : %d   (MISSING %d)" % (len(ok), missing))
    log("references                   : %d" % refs)
    log("  yielded a surname+year     : %d / %d  (%.0f%%)"
        % (lab, refs, 100.0 * lab / refs if refs else 0))
    log("  UNIQUE within their review : %d / %d  (%.0f%%)"
        % (uniq, lab, 100.0 * uniq / lab if lab else 0))
    log("  sharing a label            : %d / %d  (%.0f%%)"
        % (coll, lab, 100.0 * coll / lab if lab else 0))
    log("")
    log("Against all of PubMed the same label form resolved 0/20 with a median result set of")
    log("147. Inside the review that uses it, the comparison is the number above.")
    log("UPPER BOUND on ambiguity: these are whole bibliographies, not included studies only.")

    json.dump({"question": "is an author-year label unique inside the review that uses it",
               "substrate": "61 Cochrane reviews whose PMC deposit carried a reference list",
               "bound": "whole bibliographies, not included studies only -- so the collision "
                        "rate is an upper bound on what a label faces among included trials",
               "n_reviews": len(ok), "missing": missing, "n_refs": refs,
               "n_labelled": lab, "unique": uniq, "in_collision": coll, "rows": rows},
              io.open(OUT, "w", encoding="utf-8"), indent=1)
    log("wrote %s" % os.path.relpath(OUT, REPO))
    return 0


if __name__ == "__main__":
    sys.exit(main())
