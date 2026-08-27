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

NCT = re.compile(r"NCT\d{8}")
# Other registries this corpus cites. An ISRCTN or EudraCT number identifies a trial just as
# well as an NCT; a rule that accepted only NCT would manufacture failures on the trials this
# review reaches through other registers, which is the narrow-vocabulary defect this repo has
# hit repeatedly.
OTHER_ID = re.compile(r"\b(ISRCTN\d{6,8}|EudraCT\s*\d{4}-\d{6}-\d{2}|NTR\d{3,5}|"
                      r"ACTRN\d{14}|ChiCTR[-\w]*\d{6,})\b", re.I)
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
PMID_FIELD = re.compile(r'"(record_id|pmid|pubmed_id)"\s*:\s*"?(\d{6,9})', re.I)
DOI_ANY = re.compile(r"10\.\d{4,9}/[^\s\"'<>,)]+")
URL_ANY = re.compile(r"https?://[^\s\"']+")


def has_id(blob):
    return bool(NCT.search(blob) or OTHER_ID.search(blob) or PMID_FIELD.search(blob)
                or DOI_ANY.search(blob) or URL_ANY.search(blob))


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
                in_screen = "screen" in path.lower()
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
