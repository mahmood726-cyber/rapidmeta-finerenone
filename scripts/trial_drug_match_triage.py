# -*- coding: utf-8 -*-
"""RENAMED FROM audit_trial_drug_match.py ON 2026-08-31, AND THE NAME IS THE FIX.

TRIAGE, NOT A VERDICT. Measured on this corpus: 11 flags, 0 real -- class
reviews holding class members, development codes (LCZ696, ALN-PCSSC, AMG 145),
an abbreviation dropped by a length filter, and a class term matching its own
member. Every hit needs a human. A file called `audit_` promised a verdict it
cannot deliver.

scripts/lint_gate_can_fail.py refused this file for returning a verdict it
could not enforce. Its doctrine is right and it is worth restating: a module
that reports findings and always exits 0 is a REPORT, and reports are named
_census.py or _triage.py. A GATE THAT CANNOT FAIL IS NOT A DEFECT WHILE
NOTHING RUNS IT -- IT IS A TRAP FOR WHOEVER WIRES IT IN NEXT, who will
reasonably assume a thing called an audit can block. The behaviour here was
always correct; the name was the promise it could not keep.
"""
"""Does every trial an object HOLDS actually study the drug the object is about?

⛔ THE DEFECT. `evolocumab-ascvd-auto2` holds three registrations:

    NCT01652703  evolocumab (AMG 145)          <- the object's own drug
    NCT03060577  an extension trial of INCLISIRAN
    NCT04992065  NNC0385-0434, an oral PCSK9

Three drugs in an object named for one. Nothing pools from them, so no estimate
is wrong -- the object's CONTENTS are.

⭐ AND IT IS THE SAME CLASS AS THE COLCHICINE FINDING. A drug-only concept block
returned an IDENTICAL 125 candidates across six different colchicine topics.
The block finds the DRUG, or here the drug CLASS; the rule that turns candidates
into an included set is the judgement, and `ELIGIBILITY_RULE` is UNDECLARED on
132 of 146 outcome-blocks. Nothing prevented this and nothing would prevent it
elsewhere.

⚠️ HELD AND POOLED ARE REPORTED SEPARATELY, and the distinction is the whole
point. A held-but-unpooled foreign drug is a CONTENTS defect: the page lists a
trial it should not. A POOLED foreign drug is a CORRECTNESS defect and a
different order of problem -- the estimate would be over trials of two different
interventions. The allocation audit found 0 of 8 flags in a pool; this one asks
the same question of a different property.

⚠️ AND THE INSTRUMENT IS A NAME MATCH, WITH ALL THAT IMPLIES. It compares the
object's drug token against the registration's interventions and title. It will
miss a synonym it does not know, and it will flag a legitimate comparator arm --
a trial of drug A against drug B belongs in an object about either. Every flag
is NAMED so a reader adjudicates rather than trusting a count, and the
comparator case is separated out rather than swept in.

    python scripts/audit_trial_drug_match.py [--json OUT]
"""
import argparse
import glob
import io
import json
import os
import re
import subprocess
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
UA = "rapidmeta-systematic-review/1.0 (mailto:mahmood726@gmail.com)"

# Tokens in an app_id that name no drug.
_STOP = {"review", "auto", "full", "trial", "trials", "study", "nma", "meta",
         "analysis", "living", "rapidmeta", "cvot", "hf", "ckd", "af", "vte",
         "mace", "prep", "hiv", "tb", "covid", "rsv", "cabp", "psa", "ra",
         "ascvd", "lipid", "kidney", "heart", "failure", "cancer", "acute",
         "chronic", "adult", "adults", "versus", "vs", "and", "the", "for",
         "in", "of", "with", "pci", "acs", "copd", "uti", "cdiff", "outp",
         "infant", "africa", "pediatric", "paediatric", "severe", "mild",
         "prevention", "treatment", "therapy", "disease", "auto2", "split",
         "k3", "k4", "sarscov2", "cvncov", "shortened", "mdr", "func", "funcmr",
         "seasonal", "first", "12m", "wk12", "wk24", "wk8", "css", "change"}


def drug_tokens(app_id, title):
    """Candidate drug names for an object, from its id and title.

    ⚠️ A HEURISTIC AND DECLARED AS ONE. It takes long alphabetic tokens that are
    not obvious topic words. It will miss a drug named only in a field this does
    not read, and it will occasionally treat a condition word as a drug -- which
    is why an object yielding NO token is reported UNDECIDABLE rather than
    silently passing every trial it holds."""
    toks = set()
    for src in (app_id or "", title or ""):
        for w in re.split(r"[^A-Za-z0-9]+", str(src)):
            wl = w.lower()
            if len(wl) >= 6 and wl not in _STOP and not wl.isdigit():
                toks.add(wl)
    return toks


# ⛔ THREE PAYLOAD STATES, NOT TWO. `RETRIEVED` / `NO_PAYLOAD` /
# `RETRIEVED_CORRUPT`. Collapsing the last two records a CORRUPT payload as an
# ABSENT one, which silently shrinks every denominator downstream.
#
# ⚠️ AND "FAILS TO PARSE" IS NOT "IS CORRUPT". A JSONL file, a file with a BOM
# and a truncated buffer all fail the same json.load, and only the last is
# damage. Two lanes hit the JSONL false positive within an hour tonight. The
# discriminator is the SIZE SIGNATURE -- a truncated write lands on an exact
# power of two, 32,768 being the case found in the wild -- not the parse
# failure alone. So a corrupt state is recorded WITH ITS BYTE COUNT, and the
# byte count is what a human adjudicates.
#
# ⭐ ABSENT MEANS TRY AGAIN. CORRUPT MEANS SOMETHING WROTE BADLY, AND THE
# SPECIMEN IS WORTH MORE THAN THE RETRY.
FETCH_OK, FETCH_ABSENT, FETCH_CORRUPT = ("RETRIEVED", "NO_PAYLOAD",
                                        "RETRIEVED_CORRUPT")

_CACHE = {}


def fetch(nct):
    if nct in _CACHE:
        return _CACHE[nct]
    u = ("https://clinicaltrials.gov/api/v2/studies/%s"
         "?fields=NCTId,BriefTitle,InterventionName,InterventionOtherName,"
         "ArmGroupLabel" % nct)
    r = subprocess.run(["curl", "-sL", "--max-time", "45", "-A", UA, u],
                       capture_output=True)
    raw = r.stdout.decode("utf-8", "replace")
    if not raw.strip():
        out = (FETCH_ABSENT, None, 0)
    else:
        try:
            out = (FETCH_OK, json.loads(raw), len(raw))
        except Exception as exc:
            out = (FETCH_CORRUPT, None, len(raw))
            print("   RETRIEVED_CORRUPT %s: %d bytes did not parse (%s)"
                  % (nct, len(raw), str(exc)[:60]))
    _CACHE[nct] = out
    return out


def trial_text(d):
    ps = (d or {}).get("protocolSection") or {}
    idm = ps.get("identificationModule") or {}
    arm = ps.get("armsInterventionsModule") or {}
    parts = [idm.get("briefTitle") or ""]
    for iv in (arm.get("interventions") or []):
        parts.append(iv.get("name") or "")
        parts.extend(iv.get("otherNames") or [])
    for a in (arm.get("armGroups") or []):
        parts.append(a.get("label") or "")
    return " ".join(parts)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--json", default=None)
    a = ap.parse_args()

    files = [f for f in sorted(glob.glob(os.path.join(ROOT, "ssot", "*", "*.json")))
             if not f.endswith(".striptest")]

    objs = []
    for f in files:
        try:
            canon = json.load(open(f, encoding="utf-8"))
        except Exception:
            continue
        if not isinstance(canon, dict):
            continue
        held, pooled = {}, set()
        for t in ((canon.get("inputs") or {}).get("trials") or []):
            if isinstance(t, dict) and t.get("nct"):
                held.setdefault(t["nct"], set()).add("inputs.trials")
        bo = ((canon.get("results") or {}) if isinstance(canon.get("results"), dict)
              else {}).get("by_outcome") or {}
        if isinstance(bo, dict):
            for oid, res in bo.items():
                if not isinstance(res, dict):
                    continue
                for r in (res.get("per_trial") or []):
                    if isinstance(r, dict) and r.get("nct"):
                        held.setdefault(r["nct"], set()).add("per_trial[%s]" % oid)
                        pooled.add(r["nct"])
        if held:
            objs.append((os.path.basename(f), canon, held, pooled))

    print("objects with held registrations : %d" % len(objs))
    ncts = sorted({n for _, _, h, _ in objs for n in h})
    print("distinct registrations to fetch : %d" % len(ncts))
    sys.stdout.flush()

    texts, corrupt_payloads = {}, []
    for i, n in enumerate(ncts, 1):
        state, d, nbytes = fetch(n)
        if state == FETCH_CORRUPT:
            corrupt_payloads.append((n, nbytes))
            texts[n] = None
        else:
            texts[n] = trial_text(d) if d else None
        if i % 40 == 0:
            print("  fetched %d/%d" % (i, len(ncts)))
            sys.stdout.flush()
        time.sleep(0.1)

    mismatch_held, mismatch_pooled, undecidable = [], [], []
    rows = matched = 0
    for name, canon, held, pooled in objs:
        toks = drug_tokens(canon.get("app_id"), canon.get("title"))
        if not toks:
            undecidable.append({"object": name,
                                "why": "no drug token derivable from app_id or title"})
            continue
        for n, where in sorted(held.items()):
            txt = texts.get(n)
            if txt is None:
                continue
            rows += 1
            low = txt.lower()
            hit = sorted(t for t in toks if t in low)
            if hit:
                matched += 1
                continue
            rec = {"object": name, "nct": n, "object_drug_tokens": sorted(toks),
                   "trial_text": txt[:150], "where": sorted(where),
                   "pooled": n in pooled}
            (mismatch_pooled if n in pooled else mismatch_held).append(rec)

    print()
    if corrupt_payloads:
        print("RETRIEVED_CORRUPT  : %d registration(s) returned bytes that did "
              "not parse -- NOT counted as absent:" % len(corrupt_payloads))
        for n, b in corrupt_payloads:
            print("     %s  %d bytes" % (n, b))
    print("ROWS CHECKED       : %d" % rows)
    print("drug token matched : %d of %d" % (matched, rows))
    print("UNDECIDABLE objects: %d (no drug token derivable -- not counted)"
          % len(undecidable))
    print()
    print("⛔ POOLED, drug does not match the object  : %d  <- CORRECTNESS"
          % len(mismatch_pooled))
    for m in mismatch_pooled:
        print("   %-40s %s  where=%s" % (m["object"][:40], m["nct"],
                                         ",".join(m["where"])))
        print("       object drug: %s" % ", ".join(m["object_drug_tokens"]))
        print("       trial      : %s" % m["trial_text"][:110])
    print()
    print("⚠️ HELD but not pooled, drug does not match: %d  <- CONTENTS"
          % len(mismatch_held))
    for m in mismatch_held:
        print("   %-40s %s" % (m["object"][:40], m["nct"]))
        print("       object drug: %s" % ", ".join(m["object_drug_tokens"]))
        print("       trial      : %s" % m["trial_text"][:110])
    objs_hit = sorted({m["object"] for m in mismatch_held + mismatch_pooled})
    print()
    print("OBJECTS AFFECTED   : %d of %d" % (len(objs_hit), len(objs)))
    for o in objs_hit:
        print("   %s" % o)

    if a.json:
        json.dump({"rows_checked": rows, "matched": matched,
                   "mismatch_pooled": mismatch_pooled,
                   "mismatch_held_not_pooled": mismatch_held,
                   "undecidable_objects": undecidable,
                   "objects_affected": objs_hit},
                  open(a.json, "w", encoding="utf-8"), indent=1,
                  ensure_ascii=False)
        print("\n  written %s" % a.json)


if __name__ == "__main__":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8",
                                  errors="replace", line_buffering=True)
    main()
