# -*- coding: utf-8 -*-
"""FAIL CLOSED: no trial id enters a pooled row without existing in a registry.

⛔ THE DEFECT THIS CLOSES IS THE MECHANISM, NOT THE 43 IDS.

The path from a typed id to a pooled estimate has no verification on it at all:

    generate_new_apps.py   "auto_include_ids": ["NCT02065791", ...]   <- a literal
      -> build_auto_include_ids_js()   '"new Set([" + ", ".join(...) + "]))"'
      -> AUTO_INCLUDE_TRIAL_IDS in the served page
      -> the page's autoscreener pre-proposes INCLUDE
      -> the row enters realData and contributes to the pool

`build_auto_include_ids_js` is a string join. Nothing between a keystroke and a
pooled row asks whether the trial exists.

⭐ AND THE CHECK THAT LOOKS LIKE IT GUARDS THIS COMPARES THE SET TO A COPY OF
ITSELF. `audit_40_checks.py::check_10_nct_in_auto_include_vs_realdata` asserts
"AUTO_INCLUDE set must match keys in realData" -- both emitted from the same
unverified config, so it passes with fabricated ids in BOTH. That is a fifth way a
control can be green and worthless: IT COMPARES A THING TO A COPY OF ITSELF.

⭐ The verification that DOES exist is non-blocking by design.
`overmind/gates/retrofit.py` annotates: its own docstring says "Nothing is written
over a live app page." It stages an annotated copy of a decision it can never reach.

⇒ SO THIS GATE SITS ON THE GENERATION PATH AND REFUSES, rather than annotating
afterwards.

    python scripts/gate_registry_existence.py                 # report
    python scripts/gate_registry_existence.py --gate          # exit 1 on any reject
    python scripts/gate_registry_existence.py --selftest      # PLANT a fake id
    python scripts/gate_registry_existence.py --assert-rejects N

⚠️ ABSENT FROM THE SNAPSHOT IS NOT ABSENT FROM THE REGISTRY. NCT01445665 is live on
ClinicalTrials.gov and missing from the AACT 2026-08-27 export, so a snapshot-only
gate would reject a real trial. Ids proven live by a dated probe are carried in
KNOWN_LIVE_NOT_IN_SNAPSHOT with their evidence, and nothing enters that list without
one.

NO NETWORK. Reads the local AACT snapshot, so it can run in a hook or a sandbox.
"""
import argparse
import csv
import glob
import hashlib
import io
import json
import os
import re
import sys

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
csv.field_size_limit(1 << 30)

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
NCT_RE = re.compile(r"NCT\d{8}")
AUTO_RE = re.compile(r"AUTO_INCLUDE_TRIAL_IDS\s*=\s*new\s+Set\(\[(.*?)\]\)", re.S)

SNAPSHOT_DIR = os.environ.get("AACT_SNAPSHOT",
                              r"F:/AACT-storage/AACT/2026-08-30")
SNAPSHOT_DATA_DATE = "2026-08-27"          # from the data, never the folder name

# Ids proven live on ClinicalTrials.gov but absent from the snapshot. Evidence
# required: an HTTP 200 with the date it was observed. This list is not a
# convenience -- it is the only thing standing between this gate and a false
# rejection of a real trial.
KNOWN_LIVE_NOT_IN_SNAPSHOT = {
    "NCT01445665": "probed 2026-09-01, HTTP 200, COMPLETED, "
                   "'Study Comparing the Safety and Efficacy of Intravenous CXA-201'; "
                   "absent from AACT export 2026-08-27",
}


def snapshot_ids():
    """Every nct_id in the snapshot's studies table."""
    p = os.path.join(SNAPSHOT_DIR, "studies.txt")
    if not os.path.exists(p):
        sys.exit("FAIL CLOSED: snapshot not found at %s -- refusing to pass ids "
                 "unchecked. Set AACT_SNAPSHOT." % p)
    ids = set()
    with open(p, encoding="utf-8", errors="replace", newline="") as f:
        r = csv.reader(f, delimiter="|", quotechar='"')
        i = next(r).index("nct_id")
        for row in r:
            if len(row) > i:
                ids.add(row[i])
    if len(ids) < 100000:
        sys.exit("FAIL CLOSED: snapshot yielded only %d ids, which is not a whole "
                 "export -- refusing to judge against a truncated reference." % len(ids))
    return ids


def auto_include_sets(pages=None):
    """(page, ids) for every served page declaring an AUTO_INCLUDE set."""
    out = []
    for f in sorted(pages or glob.glob(os.path.join(ROOT, "*.html"))):
        try:
            txt = open(f, encoding="utf-8", errors="replace").read()
        except OSError as e:
            out.append((os.path.basename(f), None, repr(e)))
            continue
        m = AUTO_RE.search(txt)
        ids = set(NCT_RE.findall(m.group(1))) if m else set()
        out.append((os.path.basename(f), ids, None))
    return out


def config_ids():
    """auto_include_ids literals in the generators.

    ⭐ EVERY NAMED GENERATOR GETS A STATE. An earlier version skipped a missing
    generator with `if not os.path.exists(p): continue`, which silently shrinks the
    set of entry points examined: if a generator were renamed, this would report
    "0 unknown ids" for a file it never opened, and the absence would read as a
    clean result. `PRESENT` is the positive property; `ABSENT_NOT_SCANNED` is
    reported, never skipped.
    """
    found = {}
    for gen in ("generate_new_apps.py", "generate_living_ma_v13.py"):
        p = os.path.join(ROOT, gen)
        present = os.path.exists(p)
        rec = {"state": "PRESENT" if present else "ABSENT_NOT_SCANNED", "ids": set()}
        if present:
            txt = open(p, encoding="utf-8", errors="replace").read()
            for m in re.finditer(r'"auto_include_ids"\s*:\s*\[(.*?)\]', txt, re.S):
                rec["ids"] |= set(NCT_RE.findall(m.group(1)))
        found[gen] = rec
    return found


def check(known, pages=None):
    rejects = {}
    reach = {"pages": 0, "with_set": 0, "no_set": 0, "unreadable": [],
             "ids_seen": 0, "accepted_in_snapshot": 0, "accepted_known_live": 0,
             "rejected_ids": 0}
    for page, ids, err in auto_include_sets(pages):
        reach["pages"] += 1
        if err:
            reach["unreadable"].append({"page": page, "error": err})
        elif not ids:
            reach["no_set"] += 1
        else:
            reach["with_set"] += 1
            reach["ids_seen"] += len(ids)
            # ⭐ EVERY ID GETS A POSITIVE STATE, not just every page. Skipping the
            # known-good ones with a bare `continue` would leave the accepted count
            # unstated, so the output could say "43 refused" while never saying out
            # of how many -- a refusal rate with no denominator. The three states
            # are asserted to sum per page.
            for n in sorted(ids):
                if n in known:
                    reach["accepted_in_snapshot"] += 1
                elif n in KNOWN_LIVE_NOT_IN_SNAPSHOT:
                    reach["accepted_known_live"] += 1
                else:
                    reach["rejected_ids"] += 1
                    rejects.setdefault(n, []).append(page)
    assert (reach["accepted_in_snapshot"] + reach["accepted_known_live"]
            + reach["rejected_ids"]) == reach["ids_seen"], "id states do not sum"
    return rejects, reach


def selftest(known):
    """PLANT a fabricated id, require refusal, restore, PROVE the restoration.

    ⛔ THIS TEST DAMAGED A SERVED PAGE AND THEN REPORTED THAT IT HAD NOT.

    The first version read the victim in TEXT mode and wrote it back the same way.
    Universal-newline decoding turned every CRLF into LF, and writing with
    newline="" put LF back -- so the restore silently stripped 6,166 bytes from
    ABALOPARATIDE_OSTEO_AUTO_FULL_REVIEW.html, changing all 6,166 lines.

    ⭐ AND THE CHECK THAT WAS SUPPOSED TO CATCH IT COMPARED THE DECODED STRING TO
    THE DECODED STRING -- `restored == original`, both lossy, both text-mode. It
    compared a thing to a copy of itself and printed "restored byte-identical:
    True" over a corrupted file. That is precisely the defect this module's own
    docstring diagnoses in check_10_nct_in_auto_include_vs_realdata, committed by
    the module that names it.

    ⇒ The victim is now read and written as BYTES, and the restoration is proved
    by sha256 of the file on disk against the sha256 taken before the plant.
    """
    victim = None
    for f in sorted(glob.glob(os.path.join(ROOT, "*.html"))):
        raw = open(f, "rb").read()                      # BYTES, not text
        txt = raw.decode("utf-8", "replace")
        m = AUTO_RE.search(txt)
        if m and NCT_RE.findall(m.group(1)):
            victim, original_raw, mm, original_txt = f, raw, m, txt
            break
    if not victim:
        sys.exit("SELFTEST INCONCLUSIVE: no page carries an AUTO_INCLUDE set")

    fake = "NCT09999999"
    assert fake not in known, "planted id must not really exist"
    sha_before = hashlib.sha256(original_raw).hexdigest()
    before, _ = check(known, [victim])

    planted_txt = (original_txt[:mm.start(1)] + mm.group(1) + ", '%s'" % fake
                   + original_txt[mm.end(1):])
    open(victim, "wb").write(planted_txt.encode("utf-8"))
    try:
        after, _ = check(known, [victim])
        fired = fake in after
    finally:
        open(victim, "wb").write(original_raw)          # the ORIGINAL BYTES back

    sha_after = hashlib.sha256(open(victim, "rb").read()).hexdigest()
    ok_restore = sha_after == sha_before
    after_restore, _ = check(known, [victim])

    print("PLANT TEST on %s" % os.path.basename(victim))
    print("  before plant   : %d rejects" % len(before))
    print("  planted %s -> gate fired: %s" % (fake, fired))
    print("  sha256 before  : %s" % sha_before[:32])
    print("  sha256 after   : %s" % sha_after[:32])
    print("  restored, proved by sha256 of the bytes on disk : %s" % ok_restore)
    print("  after restore  : %d rejects (must equal before)" % len(after_restore))
    ok = fired and ok_restore and set(after_restore) == set(before)
    print("  SELFTEST %s" % ("PASS" if ok else "FAIL"))
    if not ok:
        sys.exit(1)
    return ok


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--gate", action="store_true", help="exit 1 if anything rejects")
    ap.add_argument("--selftest", action="store_true")
    ap.add_argument("--assert-rejects", type=int, default=None)
    ap.add_argument("--json", default=None)
    a = ap.parse_args()

    known = snapshot_ids()
    print("registry reference : AACT snapshot %s, data date %s, %d trials"
          % (os.path.basename(SNAPSHOT_DIR), SNAPSHOT_DATA_DATE, len(known)))

    if a.selftest:
        selftest(known)
        return 0

    cfg = config_ids()
    for gen, rec in cfg.items():
        if rec["state"] != "PRESENT":
            print("  %-28s %s" % (gen, rec["state"]))
            continue
        ids = rec["ids"]
        bad = sorted(i for i in ids
                     if i not in known and i not in KNOWN_LIVE_NOT_IN_SNAPSHOT)
        print("  %-28s PRESENT, %d ids in config, %d unknown to the registry%s"
              % (gen, len(ids), len(bad), (" -> %s" % bad[:4]) if bad else ""))

    rejects, reach = check(known)
    print("\nREACH -- every page assigned a state")
    print("  pages scanned            : %d" % reach["pages"])
    print("  declaring an AUTO_INCLUDE: %d" % reach["with_set"])
    print("  no AUTO_INCLUDE set      : %d" % reach["no_set"])
    print("  unreadable               : %d" % len(reach["unreadable"]))
    print("  ids seen in those sets   : %d" % reach["ids_seen"])
    print("    accepted, in snapshot  : %d" % reach["accepted_in_snapshot"])
    print("    accepted, known live   : %d" % reach["accepted_known_live"])
    print("    REJECTED               : %d" % reach["rejected_ids"])
    assert (reach["with_set"] + reach["no_set"] + len(reach["unreadable"])
            == reach["pages"]), "reach does not sum"

    print("\nIDS THAT WOULD BE REFUSED: %d" % len(rejects))
    for n, pgs in sorted(rejects.items()):
        print("  %s  on %d page(s): %s" % (n, len(pgs), ", ".join(p[:38] for p in pgs[:2])))

    if a.json:
        json.dump({"snapshot_data_date": SNAPSHOT_DATA_DATE,
                   "n_rejected": len(rejects),
                   "rejects": {k: v for k, v in rejects.items()},
                   "reach": reach},
                  open(a.json, "w", encoding="utf-8"), indent=1)

    if a.assert_rejects is not None and len(rejects) != a.assert_rejects:
        print("\nPREDICTION FAILED: expected %d rejects, got %d"
              % (a.assert_rejects, len(rejects)))
        return 2
    if a.gate and rejects:
        print("\n⛔ REFUSED: %d id(s) do not exist in the registry. An id that "
              "resolves to nothing cannot contribute a row to a pooled estimate."
              % len(rejects))
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
