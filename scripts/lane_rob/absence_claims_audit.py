# -*- coding: utf-8 -*-
"""SWEEP: every claim that something DOES NOT EXIST, and whether it was demonstrated.

⛔ THE THIRD MEMBER OF A FAMILY WE ALREADY HAD TWO OF.
    a 200 is not a document
    a 000 is not a paywall
    A 404 IS NOT AN ABSENCE
Each is the same mistake: reading a transport outcome as a fact about the world.

WHY THE FIELD SWEEP IS NOT THE SWEEP. data_finder defines GENUINELY_UNOBTAINABLE as a claim
about the world and refuses to set it without a reason of substance. Grepping the objects for
that state returns ZERO -- and reporting "zero exposed" from that would be exactly the
reach-versus-coverage error this project keeps logging. The state is not yet written into
stored objects, so the grep measured the field's adoption, not the corpus's exposure.

The exposure is in PROSE that does the same job. "The United States application was withdrawn,
so no FDA review of this product exists" sets no field, passes every schema, and converts a
retrieval gap into a fact about the world just as effectively.

WHAT COUNTS AS A DEMONSTRATION. Not the absence of a result -- the presence of evidence that
the thing cannot be there: a named register searched with its date, a regulator's own statement
that no application was made, a document that says the study was never done. A 404, a 403, an
empty result set and "not indexed" are all failed lookups. They license "not found", which is a
statement about us, and never "does not exist", which is a statement about the world.
"""
import io
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
os.chdir(os.path.dirname(os.path.dirname(HERE)))

# ⚠️ THE FIRST VERSION OF THIS PATTERN PRODUCED A DRAMATIC NUMBER AND IT WAS AN ARTIFACT.
#
# It matched any "no X exists" and returned 665 claims across 161 files, 0% demonstrated. Read
# back, almost all of it was noise of three kinds:
#   - true statements about a record we DID read: "the registry posts no results section"
#   - statements about this object's internals: "no pooled estimate to quote, k=2"
#   - AND, worst, the CORRECT form itself: "both routes returned nothing. NOT evidence that no
#     publication exists" was scored as a violation. A detector that flags the model answer as
#     the defect will drive the corpus away from the behaviour it exists to enforce.
#
# 0% demonstrated was therefore never reported as a finding. An instrument with no measured
# error rate is an assumption wearing a number, and this one's error was not small or flat.
#
# The defect is narrow: an EXTERNAL EVIDENTIARY ARTEFACT asserted not to exist in the world,
# where only a lookup failed. Not "we hold no second surface" -- that is about us, and true.
ARTEFACT = (r"FDA review|EMA (?:review|assessment)|WHO (?:review|assessment)|regulatory (?:review"
            r"|assessment)|assessment report|approval|application|publication|protocol|"
            r"registration|trial record|review of this product")
ABSENCE = re.compile(
    r"\b(?:no|not any)\b[^.;]{0,40}?\b(?:%s)\b[^.;]{0,40}?\b(?:exists?|existed)\b"
    r"|\b(?:%s)\b[^.;]{0,40}?\b(?:does not exist|never existed|was never (?:made|filed|"
    r"submitted|conducted|done))\b" % (ARTEFACT, ARTEFACT), re.I)

# ⛔ A sentence that DISCLAIMS the inference is the behaviour we want, not an instance of the
# defect. Excluding these is what separates "asserted absence" from "recorded non-retrieval".
DISCLAIMED = re.compile(
    r"\bnot evidence\b|\brather than absent\b|\bnot a demonstration\b|\bstatement about us\b|"
    r"\bwas not found\b|\bnot yet found\b|\bcould not be found\b|\bdoes not establish\b|"
    r"\bNOT_YET_FOUND\b|\bthis is a search result\b", re.I)

# ⚠️ THIS SPLIT IS A HINT FOR A HUMAN, NOT A MEASUREMENT, AND SAYING SO IS THE POINT.
#
# The first run reported "0 of 665 demonstrated". After tightening, "0 of 14". Both zeroes were
# artefacts: the pattern below simply did not recognise the forms the corpus actually uses. The
# tempting repair was to add the exact wording of the fix I had just written, at which point the
# classifier measures my prose rather than the corpus -- and every future entry written in some
# other words scores as undemonstrated.
#
# So the markers stay GENERIC (an enumeration, a staged artefact, a named register with its
# date), the output is labelled CANDIDATES rather than findings, and any fraction that leaves
# this file is hand-checked. An instrument with no measured error rate is an assumption wearing
# a number; this one's error was 100% on its first two runs.
DEMONSTRATED = re.compile(
    r"\benumerat\w+\b|\bpositive control\b|\bregister(?:ed|y)?[^.]{0,40}\b(?:lists?|serves?|"
    r"searched|checked)\b|\bstates that no\b|\bconfirmed by\b|\bsources/\w+\b|"
    r"\bwithdrawn (?:on|in) \d{4}\b|\bofficial (?:statement|response)\b|"
    r"\bsubmissions (?:asked|probed)\b|\bserver'?s answers\b|\bsha256\b", re.I)

# Marks of a mere failed lookup being used as the reason.
FAILED_LOOKUP = re.compile(
    r"\b40\d\b|\b50\d\b|\bnot indexed\b|\bno results?\b|\breturned nothing\b|\bempty\b|"
    r"\bpaywall\w*\b|\bnot in (?:PubMed|PMC|the index)\b|\btimed out\b|\bblocked\b", re.I)


def strings(node, path=""):
    if isinstance(node, dict):
        for k, v in node.items():
            for r in strings(v, path + "/" + str(k)):
                yield r
    elif isinstance(node, list):
        for i, v in enumerate(node):
            for r in strings(v, "%s[%d]" % (path, i)):
                yield r
    elif isinstance(node, str) and len(node) > 12:
        yield path, node


def audit_object(path):
    try:
        obj = json.load(io.open(path, encoding="utf-8"))
    except Exception as e:
        return {"path": path, "unreadable": "%s: %s" % (type(e).__name__, e)}
    hits = []
    for field, s in strings(obj):
        for m in ABSENCE.finditer(s):
            frag = re.sub(r"\s+", " ", s[max(0, m.start() - 120):m.end() + 160]).strip()
            if DISCLAIMED.search(frag):
                continue
            hits.append({"field": field, "claim": frag[:240],
                         "demonstrated": bool(DEMONSTRATED.search(frag)),
                         "failed_lookup_as_reason": bool(FAILED_LOOKUP.search(frag))})
    return {"path": path, "hits": hits}


def main():
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace",
                                  line_buffering=True)
    roots = sys.argv[1:] or ["ssot"]
    files = []
    for root in roots:
        for dirpath, _dirs, names in os.walk(root):
            for n in names:
                if n.endswith(".json"):
                    files.append(os.path.join(dirpath, n))
    files.sort()
    results = [audit_object(f) for f in files]
    unreadable = [r for r in results if r.get("unreadable")]
    readable = [r for r in results if not r.get("unreadable")]
    all_hits = [(r["path"], h) for r in readable for h in r["hits"]]
    dem = [x for x in all_hits if x[1]["demonstrated"]]
    lookup = [x for x in all_hits if not x[1]["demonstrated"] and x[1]["failed_lookup_as_reason"]]
    bare = [x for x in all_hits if not x[1]["demonstrated"]
            and not x[1]["failed_lookup_as_reason"]]

    print("")
    print("ABSENCE-CLAIM AUDIT -- CANDIDATES for hand adjudication, not findings")
    print("")
    # ⚠️ THE KINDS BEFORE THE NUMBER. A count with an unenumerated population is a reach figure.
    print("  json files walked                       %5d" % len(files))
    print("    of which unreadable (NOT audited)     %5d" % len(unreadable))
    print("    audited                               %5d" % len(readable))
    print("  files carrying at least one claim       %5d"
          % len({p for p, _ in all_hits}))
    print("")
    print("  candidate absence claims                %5d" % len(all_hits))
    print("    hint: reason looks like evidence      %5d" % len(dem))
    print("    hint: a failed lookup as the reason   %5d   <- 404 read as absence" % len(lookup))
    print("    hint: no reason matched               %5d" % len(bare))
    if all_hits:
        print("")
        print("  NO FRACTION IS PRINTED HERE. The three-way split above is a keyword hint")
        print("  whose error rate was 100%% on this file's first two runs. Adjudicate the")
        print("  candidates by reading them; quote the hand-checked count, never this one.")
    for label, group in (("FAILED LOOKUP AS REASON", lookup), ("NO REASON GIVEN", bare)):
        if not group:
            continue
        print("")
        print("  %s" % label)
        for p, h in group[:12]:
            print("    %s" % os.path.relpath(p))
            print("      %-28s %s" % (h["field"][:28], h["claim"][:150]))
        if len(group) > 12:
            print("    ... and %d more" % (len(group) - 12))
    if unreadable:
        print("")
        print("  UNREADABLE, and named rather than dropped from the denominator:")
        for r in unreadable[:8]:
            print("    %s  %s" % (os.path.relpath(r["path"]), r["unreadable"][:70]))
    out = r"F:\claude-temp\pend\out\absence_claims.json"
    json.dump({"files": len(files), "hits": [{"path": p, **h} for p, h in all_hits]},
              io.open(out, "w", encoding="utf-8"), indent=1)
    print("")
    print("  detail -> %s" % out)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
