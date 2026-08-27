# -*- coding: utf-8 -*-
"""Stage a trial's ORIGINAL registration alongside its current one, for RoB 2 domain 5.

WHY THIS IS THE CRITICAL PATH AND NOT A FOLLOW-UP. D5 asks whether the reported result was
selected from among analyses that were PLANNED. Without the original registration there is
nothing to compare the report against, so the domain cannot be answered and defaults to
"no information" -- which the corpus-wide split showed is 83% a statement about our retrieval
rather than about the trials. The full 375-comparison adjudication then came back a null:
strip cells where any reader abstained and 31 of 360 remain.

WITH THE ORIGINAL IN HAND, THREE STATES BECOME DISTINGUISHABLE THAT WERE PREVIOUSLY ONE:

    registered and reported as registered                       -> Low
    registered, changed, and the change is documented           -> a judgement call
    registered, changed, with no documentation                  -> High

Until tonight none of those could be told apart.

THE ENDPOINT, RECORDED SO NOBODY REDISCOVERS IT:

    https://clinicaltrials.gov/api/int/studies/<NCT>/history        -> 200, version index
    https://clinicaltrials.gov/api/int/studies/<NCT>/history/<n>    -> 200, one version
    https://clinicaltrials.gov/api/v2/studies/<NCT>/history         -> 404. The documented
                                                                       v2 path does NOT
                                                                       serve history.

The index carries `changes` (one row per version, with its date) and an `originalData` block
holding the version-0 outcome lists directly.

ONE TRIAL PER RUN, AND BYTES VERIFIED. A corpus-shaped attempt at this staged two files
BYTE-IDENTICAL to ones already held, wrote no manifest, and narrated success. Every file
here is recorded with its length and sha256, and a file identical to one already staged is
reported as such rather than counted as a retrieval.
"""
import hashlib
import io
import json
import os
import subprocess
import sys
import time

# GUARDED. A module-level stdout reassignment closes the CALLER's stdout the moment
# this file is imported, and every script here is now importable -- three separate
# checks of this lane's own output died that way before it was fixed at the source.
if __name__ == "__main__":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8",
                                  errors="replace", line_buffering=True)
HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(os.path.dirname(HERE))
os.chdir(REPO)

BASE = "https://clinicaltrials.gov/api/int/studies/%s/history"


def fetch(url):
    r = subprocess.run(["curl", "-s", "--max-time", "90", url], capture_output=True)
    return r.stdout


def sha(b):
    return hashlib.sha256(b).hexdigest()


def outcomes_of(block):
    out = []
    for o in (block or []):
        if isinstance(o, dict) and o.get("measure"):
            out.append({"measure": o["measure"],
                        "description": o.get("description"),
                        "timeFrame": o.get("timeFrame")})
    return out


def main():
    if len(sys.argv) < 3:
        sys.exit("usage: ingest_registration_history.py <topic> <NCT>")
    topic, nct = sys.argv[1], sys.argv[2]
    outdir = os.path.join("ssot", topic, "sources")
    if not os.path.isdir(outdir):
        sys.exit("REFUSED: %s does not exist; wrong topic name." % outdir)

    print("TRIAL %s   topic %s" % (nct, topic))
    idx_raw = fetch(BASE % nct)
    print("  history index                    %d bytes" % len(idx_raw))
    if not idx_raw.strip().startswith(b"{"):
        sys.exit("REFUSED: the history endpoint did not return JSON. Nothing staged.")
    idx = json.loads(idx_raw.decode("utf-8", "replace"))
    changes = idx.get("changes") or []
    print("  versions listed                  %d" % len(changes))
    if not changes:
        sys.exit("REFUSED: no versions listed. Nothing staged.")
    v0, vlast = changes[0], changes[-1]
    print("  version 0                        %s" % v0.get("date"))
    print("  latest version                   %s (v%s)"
          % (vlast.get("date"), vlast.get("version")))

    staged = []
    for name, blob in (("%s.ctgov.history-index.json" % nct, idx_raw),
                       ("%s.ctgov.v0_%s.json" % (nct, v0.get("date")),
                        fetch((BASE % nct) + "/0"))):
        path = os.path.join(outdir, name)
        d = sha(blob)
        dup = None
        for existing in os.listdir(outdir):
            ep = os.path.join(outdir, existing)
            if os.path.isfile(ep) and existing != name and sha(open(ep, "rb").read()) == d:
                dup = existing
                break
        io.open(path, "wb").write(blob)
        staged.append({"file": name, "bytes": len(blob), "sha256": d,
                       "identical_to_existing": dup})
        print("  staged %-44s %7d bytes  sha %s%s"
              % (name, len(blob), d[:16],
                 "  IDENTICAL TO " + dup if dup else ""))

    orig = idx.get("originalData") or {}
    cur_path = os.path.join(outdir, "%s.ctgov.json" % nct)
    cur = {}
    if os.path.isfile(cur_path):
        cur = json.load(io.open(cur_path, encoding="utf-8"))
    cur_primary = outcomes_of((((cur.get("protocolSection") or {})
                                .get("outcomesModule") or {}).get("primaryOutcomes")))
    orig_primary = outcomes_of(orig.get("primaryOutcomes"))

    print("")
    print("  ORIGINAL primary outcomes (version 0, %s): %d" % (v0.get("date"),
                                                               len(orig_primary)))
    for o in orig_primary:
        print("     - %s" % o["measure"][:104])
    print("  CURRENT primary outcomes: %d" % len(cur_primary))
    for o in cur_primary:
        print("     - %s" % o["measure"][:104])
    changed = ([o["measure"] for o in orig_primary]
               != [o["measure"] for o in cur_primary])
    print("")
    print("  PRIMARY OUTCOME CHANGED: %s" % changed)

    man = os.path.join(outdir, "D5_REGISTRATION_HISTORY_%s.json" % nct)
    io.open(man, "w", encoding="utf-8", newline="\n").write(json.dumps({
        "_what": ("The original and current registered primary outcomes, staged for RoB 2 "
                  "domain 5. This records WHAT WAS PLANNED so the reported result can be "
                  "compared against it. It makes no judgement."),
        "nct": nct, "retrieved_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "endpoint": BASE % nct,
        "endpoint_note": ("The documented v2 path /api/v2/studies/<NCT>/history returns 404. "
                          "The internal path above serves it."),
        "versions_listed": len(changes),
        "version_0_date": v0.get("date"), "latest_version_date": vlast.get("date"),
        "original_primary_outcomes": orig_primary,
        "current_primary_outcomes": cur_primary,
        "primary_outcome_changed": changed,
        "staged_files": staged,
        "what_this_does_not_establish": (
            "Whether any change was made before database lock or unblinding, and whether it "
            "was documented in a protocol amendment. Those decide between the three D5 "
            "states and need the protocol and SAP, which this does not retrieve."),
    }, indent=1, ensure_ascii=False))
    print("  manifest -> %s" % man)
    print("")
    print("INGEST RESULT: %d file(s) staged, changed=%s" % (len(staged), changed))


if __name__ == "__main__":
    main()
