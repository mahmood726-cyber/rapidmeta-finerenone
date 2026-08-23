"""Every PMID recorded in more than one place, and whether the records agree.

# no-control: routed through require_controls. POSITIVE is KRONOS, where
# PUBLISHED_META_BENCHMARKS.json says 30201345 and regenerate_catastrophic_sidecars.R says
# 30232048, and PubMed shows the first is a lymphoma case report -- so the pair must be found
# as a disagreement. NEGATIVE is a trial whose PMID appears identically in two places, which
# must not be reported as a conflict.

THE INSTANCE. Two of this project's own records named different publications for KRONOS. The
one in `PUBLISHED_META_BENCHMARKS.json` -- THE FILE EVERY POOL IS VALIDATED AGAINST -- is
30201345, "Multiple Polypoid Lesions in the Ileum After Treatment for Primary Ileal Follicular
Lymphoma", Gastroenterology. A case report about a different disease, in a field named
`pmid_kronos`.

A WRONG IDENTIFIER THAT RESOLVES PASSES EVERY MECHANICAL CHECK. It is a real PMID, it fetches,
it has a title and a DOI. The only test that catches it is reading the title and asking whether
it is the trial -- which is why this audit reports the pairs for a person and does not try to
adjudicate them.

WHERE THEY DISAGREE, BOTH MUST BE LOOKED UP AND NEITHER ASSUMED. In this instance the
disagreement was resolved AGAINST the more-trusted file: the script already known to have
written placeholder hazard ratios had the correct citation. PRIOR DEFECTIVENESS IS A PRIOR, NOT
EVIDENCE.

SCOPE, STATED. This reads the SSOT objects, the benchmark file and the sidecars -- the records
that carry per-trial identity. It does NOT read the 1,500 delivered pages: a full-text scan of
those exceeds every search tool available here, and saying so is better than reporting a clean
result over a set that was never read.
"""
from __future__ import annotations

import collections
import glob
import io
import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from instrument_controls import require_controls          # noqa: E402

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(REPO, "outputs", "pmid_identity_2026_08_23.json")
PMID = re.compile(r"\b\d{7,8}\b")


def walk(x, path=""):
    if isinstance(x, dict):
        for k, v in x.items():
            yield from walk(v, path + "." + str(k))
    elif isinstance(x, list):
        for i, v in enumerate(x):
            yield from walk(v, path + "[%d]" % i)
    else:
        yield path, x


def collect():
    """trial key -> {pmid -> [where]}. Trial key is an NCT where one is available, else a name."""
    by_trial = collections.defaultdict(lambda: collections.defaultdict(list))
    files = (sorted(glob.glob(os.path.join(REPO, "ssot", "*", "*.json")))
             + sorted(glob.glob(os.path.join(REPO, "outputs", "r_validation", "*.json")))
             + [os.path.join(REPO, "PUBLISHED_META_BENCHMARKS.json")])
    for p in files:
        if not os.path.isfile(p):
            continue
        try:
            obj = json.load(io.open(p, encoding="utf-8"))
        except (ValueError, OSError):
            continue
        rel = os.path.relpath(p, REPO).replace("\\", "/")
        # PER-TRIAL RECORDS LIVE UNDER TWO DIFFERENT KEYS and reading only one missed the
        # founding case. SSOT objects use `inputs.trials`; the R sidecars use a top-level
        # `trials`. The control refused because KRONOS's second PMID was in the shape this
        # collector did not read -- the same one-of-two coverage that has recurred all day.
        trial_lists = []
        if isinstance(obj, dict):
            trial_lists.append((obj.get("inputs") or {}).get("trials") or [])
            trial_lists.append(obj.get("trials") or [])
        for lst in trial_lists:
            for tr in lst:
                if not isinstance(tr, dict):
                    continue
                # Key by NAME where present: the same trial appears as NCT02497001 in one
                # record and "KRONOS" in another, and keying by NCT alone would file the two
                # PMIDs under different trials and report no disagreement.
                for key in (tr.get("name"), tr.get("nct"), tr.get("trial_id")):
                    pm = tr.get("pmid")
                    if key and pm:
                        by_trial[str(key).upper()][str(pm)].append(rel + " trials")
        # any *pmid* field anywhere
        for path, val in walk(obj):
            if "pmid" not in path.lower():
                continue
            s = str(val)
            if not PMID.fullmatch(s.strip()):
                continue
            # the trial this pmid is about: the field name usually names it
            # A PATH IS NOT A TRIAL IDENTITY. Keying by the JSON path filed
            # `.trials[0].pmid` from two different sidecars under one "trial" and reported
            # them as disagreeing -- they are different trials at the same array index. Only a
            # field that NAMES the trial (`pmid_kronos`) identifies one; everything else is
            # skipped rather than guessed at, because a false conflict on an identity question
            # costs a person a lookup and teaches them to distrust the audit.
            m = re.search(r"pmid[_\.]([a-z][a-z0-9]{2,})$", path.lower())
            if not m or m.group(1) in ("pmid", "impact_pmid"):
                continue
            by_trial[m.group(1).upper()][s.strip()].append("%s %s" % (rel, path))
    return by_trial


def main():
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    by_trial = collect()
    disagree = {k: dict(v) for k, v in by_trial.items() if len(v) > 1}
    agree = {k: dict(v) for k, v in by_trial.items()
             if len(v) == 1 and len(list(v.values())[0]) > 1}

    kronos = by_trial.get("KRONOS", {})
    require_controls(
        "pmid_identity",
        ("KRONOS carries two different PMIDs across our records (got %s)"
         % sorted(kronos), len(kronos) > 1, True),
        ("a trial whose PMID is identical in two places is not reported as a conflict "
         "(%d such trials found)" % len(agree), len(agree) < 0, True))

    print("")
    print("PMID IDENTITY ACROSS OUR OWN RECORDS")
    print("")
    print("   trials carrying a PMID somewhere        %4d" % len(by_trial))
    print("   recorded in MORE THAN ONE place         %4d" % (len(agree) + len(disagree)))
    print("      and the records AGREE                %4d" % len(agree))
    print("      and the records DISAGREE             %4d   <- both must be looked up"
          % len(disagree))
    print("")
    for k, v in sorted(disagree.items())[:20]:
        print("   %s" % k)
        for pm, wheres in sorted(v.items()):
            print("      %-10s %s" % (pm, "; ".join(w[:70] for w in wheres[:2])))
    print("")
    print("A WRONG IDENTIFIER THAT RESOLVES PASSES EVERY MECHANICAL CHECK. Only reading the")
    print("title and asking whether it is the trial catches it, so these pairs are reported")
    print("for a person rather than adjudicated here.")
    print("")
    print("NOT READ: the 1,500 delivered pages. A full-text scan of those exceeds every search")
    print("tool available here, so whether a wrong PMID reached a reader is UNMEASURED rather")
    print("than clean.")
    if not os.path.isdir(os.path.dirname(OUT)):
        os.makedirs(os.path.dirname(OUT))
    json.dump({"disagree": disagree, "agree_count": len(agree),
               "trials_with_pmid": len(by_trial)},
              io.open(OUT, "w", encoding="utf-8"), indent=1)
    print("")
    print("written: %s" % os.path.relpath(OUT, REPO))


if __name__ == "__main__":
    main()
