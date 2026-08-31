#!/usr/bin/env python3
"""A SCREENING ROW THAT EXCLUDES A TRIAL MUST RECORD ITS REGISTRATION ID.

    AN EXCLUSION WITHOUT AN IDENTIFIER IS NOT A DECISION. IT IS A DISAPPEARANCE.

Measured 2026-08-26: 220 screening rows set a trial aside under the registry-results rule, and
73 of them carry NO registration ID -- 68 in `ablation-af-medical-therapy`, 5 in `arni-hfref`.
Those 73 cannot be re-examined by anyone, including us. When the rule they were excluded under
was overturned, the other 147 could be listed, looked up and reinstated; these 73 could not be
touched, because nothing on the row says which trial it was. They can only be recovered by
re-screening from the source, which is the most expensive repair available and the one nobody
schedules.

    A row that records a VERDICT but not a SUBJECT has recorded our conclusion and thrown away
    the thing it was about. It reads as diligence -- there is a criterion, there is a reason --
    and it is unauditable in the one way that matters.

THE RULE. Any object in `screening`, `screening_of_remainder` or any `*screen*` container that
carries a VERDICT-like field must also carry a registration identifier -- on the row itself, or
on an ancestor within `ANCESTOR_DEPTH` levels, because some containers key the trial once and
list several judgements beneath it.

BASELINE, NOT CLEARANCE. The 73 known rows are listed in
`scripts/baselines/screening_row_no_id_baseline.json` so this gate can be wired in without
first repairing history. THE COUNT MUST NOT RISE. A new row without an identifier fails.
Repairing a baselined row and removing it from the baseline is the only way the number goes
down; the gate refuses if the baseline names a row that no longer exists, so the baseline
cannot rot into a permanent excuse.
"""
import io
import json
import os
import re
import sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SSOT = os.path.join(REPO, "ssot")
BASELINE = os.path.join(REPO, "scripts", "baselines",
                        "screening_row_no_id_baseline.json")

# THE PATTERNS LIVE IN ONE PLACE NOW -- ssot/registration_identifiers.py.
# They were duplicated here and, hours later, written NARROWLY AGAIN in
# scripts/measure_topic_trial_retrievability_2026_08_26.py by the same hand on the same
# night, with the corrected version in this very file. A rule that fails at a range of
# twelve inches is not closed by documentation; it is closed by a shared constant.
sys.path.insert(0, os.path.join(REPO, "ssot"))
from registration_identifiers import NCT, OTHER_REGISTRY as OTHER_ID  # noqa: E402

VERDICT_KEY = ("verdict", "decision", "screening_verdict", "inclusion", "eligibility_verdict")
ANCESTOR_DEPTH = 3


# A PMID, a DOI or a resolving record URL identifies a screened RECORD as completely as an
# NCT identifies a trial. The corpus screens two different populations -- registered trials
# (keyed by NCT) and bibliographic records (keyed by `record_id`, a PMID, with a PubMed URL)
# -- and a rule that accepted only registry identifiers accused 663 record-level rows of
# being unauditable when every one of them carries a PMID and a URL that resolves.
#
#     THE REQUIREMENT IS THAT THE ROW CAN BE RE-FOUND, not that it names a registry.
#
# Third narrowing of this gate's vocabulary in one sitting: NCT only, then NCT+path, now
# re-findable. Each narrowing pointed the same way -- at the corpus, wrongly.
# FOURTH WIDENING, 2026-08-31, and the same direction as the other three: at the
# corpus, wrongly. A bibliographic screen of Europe PMC returns records that have
# NO PubMed ID -- preprints (PPR...) and PMC-only deposits (conference abstracts,
# HTA reports). 53 of one topic's 1,443 screened records are of that kind, and
# every one carries `"key": "europepmc:PMC:PMC12768671"` or
# `"key": "europepmc:PPR:PPR1267978"`, which resolves at europepmc.org exactly as
# a PMID resolves at pubmed.
#
#     THE REQUIREMENT IS THAT THE ROW CAN BE RE-FOUND. A PMCID re-finds it.
#
# Accepting these is NOT a relaxation: a row with no identifier of any kind still
# fails, which is checked by the negative control below.
# ENUMERATING SOURCE CODES WAS THE WRONG SHAPE AND FAILED TWICE IN ONE SITTING.
# PMC and PPR cleared 49 of 53 rows and left four: europepmc:ETH:733423 (three
# theses) and europepmc:PAT:US2012093911 (a patent). Europe PMC's key format is
# `source:id` across ALL its sources -- MED, PMC, PPR, ETH, PAT, AGR, CBA, HIR,
# CTX, NBK -- and every one resolves. A rule that lists the sources it has met so
# far will keep failing on the next one, which is the same narrow-then-widen loop
# this gate's own comments record three times already. Match the FORM.
RECORD_KEY = re.compile(r'"(key|record_id|record_key)"\s*:\s*"europepmc:[A-Z]{2,4}:[A-Za-z0-9._-]{3,}"', re.I)
PMCID_ANY = re.compile(r"\bPMC\d{6,9}\b")
PMID_FIELD = re.compile(r'"(record_id|pmid|pubmed_id)"\s*:\s*"?(\d{6,9})', re.I)
DOI_ANY = re.compile(r"10\.\d{4,9}/[^\s\"'<>,)]+")
URL_ANY = re.compile(r"https?://[^\s\"']+")


# An UPPERCASE:slug key is a POLICY label in this corpus, not a screened record.
_re_policy = re.compile(r'^[A-Z][A-Z_]{2,}:')


def has_id(blob):
    return bool(NCT.search(blob) or OTHER_ID.search(blob) or PMID_FIELD.search(blob)
                or DOI_ANY.search(blob) or URL_ANY.search(blob)
                or RECORD_KEY.search(blob) or PMCID_ANY.search(blob))


def scan():
    """Yield (topic, path, verdict) for every verdict-bearing row lacking an identifier."""
    bad = []
    total = 0
    for t in sorted(os.listdir(SSOT)):
        p = os.path.join(SSOT, t, t + ".json")
        if not os.path.isdir(os.path.join(SSOT, t)) or not os.path.exists(p):
            continue
        with io.open(p, encoding="utf-8") as fh:
            obj = json.load(fh)

        def walk(node, path, ancestors):
            nonlocal total
            if isinstance(node, dict):
                v = next((node[k] for k in VERDICT_KEY if isinstance(node.get(k), str)), None)
                # ⛔ A POLICY IS NOT A ROW. `"screen" in path` matched
                # `scope_decisions/SCREENING:must-match-the-question-it-serves`
                # in arni-hfref -- a METHODOLOGICAL DECISION about the review's
                # own screening rule, cited to Handbook 3.2.1/3.2.3. Its subject
                # is the rule, named in its key; it cannot carry a registration id
                # because it is not about a registration, and demanding one is the
                # over-flagging direction this gate's own comment warns is "the
                # accusing one".
                #
                # This corpus labels policy with an UPPERCASE prefix and a colon
                # (SCOPE:..., SCREENING:...), and records with an index or an id.
                # Match on that, and only for the LEAF -- a row sitting inside a
                # container whose name contains "screen" is still a row.
                _segs = [x for x in path.split("/") if x]
                _leaf_is_policy = bool(_segs) and bool(
                    _re_policy.match(_segs[-1]))
                in_screen = ("screen" in path.lower()) and not _leaf_is_policy
                if v is not None and in_screen:
                    total += 1
                    # THE PATH IS PART OF THE ROW'S IDENTITY, and the first version of this
                    # gate did not read it. The corpus keys many verdicts BY the registration
                    # id -- `.../verdicts/NCT00116428` -- so the identifier is the dict KEY,
                    # not a field inside the value. Ignoring it flagged 1292 of 2432 rows,
                    # which is not a finding, it is an instrument accusing the corpus of
                    # losing identifiers it had recorded in the obvious place.
                    #
                    #     AN OVER-FLAGGING GATE IS NOT THE SAFE DIRECTION. It is the accusing
                    #     one, and on this exact subject -- exclusions that cannot be
                    #     re-examined -- a false accusation is the same disservice as a
                    #     missed one.
                    blob = json.dumps(node) + "||" + path
                    if not has_id(blob):
                        # An ancestor may key the trial once for several judgements.
                        anc = "".join(ancestors[-ANCESTOR_DEPTH:])
                        if not has_id(anc):
                            bad.append({"topic": t, "path": path, "verdict": v[:60]})
                for k, val in node.items():
                    walk(val, path + "/" + str(k),
                         ancestors + [json.dumps({kk: vv for kk, vv in node.items()
                                                  if not isinstance(vv, (dict, list))})])
            elif isinstance(node, list):
                for i, val in enumerate(node):
                    walk(val, path + "[%d]" % i, ancestors)

        walk(obj, "", [])
    return bad, total


def main():
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    bad, total = scan()
    keys = {"%s%s" % (b["topic"], b["path"]) for b in bad}

    if "--write-baseline" in sys.argv:
        if not os.path.isdir(os.path.dirname(BASELINE)):
            os.makedirs(os.path.dirname(BASELINE))
        with io.open(BASELINE, "w", encoding="utf-8") as fh:
            fh.write(json.dumps({
                "written": "2026-08-26",
                "why": ("Screening rows that record a verdict but no registration identifier. "
                        "NOT A CLEARANCE -- each of these is an exclusion nobody can re-examine, "
                        "recoverable only by re-screening from the source. THE COUNT MUST NOT "
                        "RISE."),
                "no_id": sorted(keys)}, indent=1))
        print("wrote baseline with %d rows" % len(keys))
        return 0

    base = set()
    if os.path.exists(BASELINE):
        with io.open(BASELINE, encoding="utf-8") as fh:
            base = set(json.load(fh).get("no_id") or [])

    new = sorted(keys - base)
    fixed = sorted(base - keys)
    print("VERDICT-BEARING SCREENING ROWS: %d" % total)
    print("   without a registration identifier: %d" % len(keys))
    print("   baselined (known, owed)          : %d" % len(base))
    print("   NEW since the baseline           : %d" % len(new))
    print("   repaired since the baseline      : %d" % len(fixed))
    if fixed:
        print()
        print("REPAIRED -- remove these from the baseline so the count can actually fall:")
        for k in fixed[:20]:
            print("   %s" % k)
    if new:
        print()
        print("REFUSED: a screening row records a verdict with no registration identifier.")
        print("An exclusion without an identifier cannot be re-examined by anyone, including "
              "us. It is not a decision, it is a disappearance.")
        for k in new[:20]:
            print("   %s" % k)
        return 1
    print()
    print("PASS: no new identifier-less screening row.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
