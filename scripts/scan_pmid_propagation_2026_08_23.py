"""Did either wrong PMID reach a delivered page? A byte scan with progress.

# no-control: a search, not a detector. Its control is asserted: a PMID known to be present
# somewhere (29668352, the correct IMPACT citation) must be FOUND, or the scan is not reading
# the files it claims to read and a zero from it means nothing.

WHY THE FIRST ATTEMPT FAILED, because it is the reusable part. A Python pass over the same
files timed out at 500 seconds and ripgrep timed out at 20. The Python version opened each
file with `io.open(..., encoding='utf-8', errors='replace')` -- DECODING every byte of a 7 MB
page into a Python string, 1,500 times, to look for an eight-digit number that is ASCII.

A byte scan needs no decoding. `open(f,'rb').read()` then `b'30201345' in data` compares raw
bytes and never builds a string. The work is I/O, not codec.

THE MEASUREMENT MATTERS BECAUSE IT DECIDES WHAT THE CORRECTION IS. A wrong PMID confined to a
benchmark file is an internal defect fixed in one place. A wrong PMID on a delivered page is a
CITATION TO A READER -- and citing a spinal-surgery case report as a migraine trial is the kind
of thing a reviewer finds.
"""
from __future__ import annotations

import glob
import io
import json
import os
import sys
import time

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(REPO, "outputs", "pmid_propagation_2026_08_23.json")

# The two wrong citations, and one known-present PMID as the control.
WRONG = {b"30201345": "cited as KRONOS; is a lymphoma case report",
         b"29180078": "cited as STRIVE (CGRP); is a spinal-surgery case report"}
CONTROL_PRESENT = b"29668352"          # IMPACT, correct, known to be in COPD_TRIPLE.json


def targets():
    seen = set()
    for pat in ("*.html", "retired/*.html", "*.json", "outputs/**/*.json",
                "ssot/*/*.json", "scripts/*.py", "scripts/*.R", "ssot/*.py"):
        for p in glob.glob(os.path.join(REPO, pat), recursive=True):
            rp = os.path.realpath(p)
            if rp not in seen and os.path.isfile(rp):
                seen.add(rp)
                yield p


def main():
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    files = list(targets())
    print("scanning %d file(s) as BYTES -- no decoding" % len(files), flush=True)
    hits = {k.decode(): [] for k in WRONG}
    control_hits = []
    t0 = time.time()
    read = 0
    for i, p in enumerate(files, 1):
        try:
            with open(p, "rb") as fh:
                data = fh.read()
        except OSError:
            continue
        read += 1
        rel = os.path.relpath(p, REPO).replace("\\", "/")
        for needle in WRONG:
            if needle in data:
                hits[needle.decode()].append(rel)
        if CONTROL_PRESENT in data:
            control_hits.append(rel)
        if i % 250 == 0:
            print("   %4d/%d  %.0fs elapsed" % (i, len(files), time.time() - t0), flush=True)

    print("")
    print("read %d file(s) in %.0fs" % (read, time.time() - t0))
    print("")
    print("CONTROL -- 29668352 (IMPACT, a correct citation known to be present): %d file(s)"
          % len(control_hits))
    if not control_hits:
        sys.exit("REFUSED: the control PMID was not found anywhere, so this scan is not "
                 "reading the files it claims to. A zero from it means nothing.")
    for f in control_hits[:4]:
        print("      %s" % f)
    print("")
    for k, why in WRONG.items():
        ks = k.decode()
        print("%s -- %s" % (ks, why))
        print("   found in %d file(s)" % len(hits[ks]))
        for f in hits[ks][:12]:
            kind = "DELIVERED PAGE" if f.endswith(".html") else "internal"
            print("      %-14s %s" % (kind, f))
    print("")
    pages = {k: [f for f in v if f.endswith(".html")] for k, v in hits.items()}
    total_pages = sum(len(v) for v in pages.values())
    if total_pages:
        print("A WRONG CITATION HAS REACHED %d DELIVERED PAGE(S). That is a citation to a "
              "reader, not an internal defect." % total_pages)
    else:
        print("NEITHER WRONG PMID APPEARS ON ANY DELIVERED PAGE. Both are confined to internal")
        print("records, so the correction is one edit in one file rather than a republication.")
    if not os.path.isdir(os.path.dirname(OUT)):
        os.makedirs(os.path.dirname(OUT))
    json.dump({"files_read": read, "hits": hits, "delivered_pages": pages,
               "control_files": len(control_hits)},
              io.open(OUT, "w", encoding="utf-8"), indent=1)
    print("")
    print("written: %s" % os.path.relpath(OUT, REPO))


if __name__ == "__main__":
    main()
