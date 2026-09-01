# -*- coding: utf-8 -*-
"""Derive the corpus NCT denominator. THE NUMBER IS WHATEVER THIS PRINTS TODAY.

⛔ WHY THIS EXISTS. Three figures were quoted into this lane from memory and
none of them regenerated: `2,034` stored NCTs, `412` trial-identity claims,
`74` registry payloads. Walking the store produces different numbers, and the
quoted ones could not be reproduced under any definition tried.

⇒ A NUMBER NO COMMAND REGENERATES IS NOT A MEASUREMENT, IT IS A MEMORY. This
module is the command. If its output disagrees with a number in a document,
the DOCUMENT is stale -- do not reconcile back to the remembered figure.

⭐ THE DEFINITIONS ARE OPERATIONAL, so they can be disagreed with precisely
rather than argued about loosely:

  STORED NCT        any /NCT\\d{8}/ occurring in ssot/*/*.json or
                    evidence/**/*.json. `re.findall`, never `re.search` --
                    search returns the FIRST match per string, so a prose block
                    naming five trials contributes one. That error undercounted
                    this corpus by 548 (1,648 vs 2,196).

  REGISTRY PAYLOAD  a record keyed on nct_id carrying a NON-EMPTY brief_title
                    read from a registered AACT snapshot, stamped with
                    snapshot_data_date, read_utc and source_type as FIELDS.
                    Presence of the key is the test; prose does not count.

    python scripts/derive_nct_denominator.py
    python scripts/derive_nct_denominator.py --json out.json

NO NETWORK. Walks the store on disk.
"""
import argparse
import collections
import glob
import io
import json
import os
import re
import sys

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
NCT_RE = re.compile(r"NCT\d{8}")

SOURCES = [("ssot", os.path.join(ROOT, "ssot", "*", "*.json")),
           ("evidence", os.path.join(ROOT, "evidence", "**", "*.json"))]


def stored_ncts():
    """Every NCT-shaped id in the store, by source and as a union."""
    by_source, per_file = {}, collections.defaultdict(set)
    union = set()
    for label, pat in SOURCES:
        found = set()
        for f in glob.glob(pat, recursive=True):
            if f.endswith(".striptest"):
                continue
            try:
                txt = open(f, encoding="utf-8", errors="replace").read()
            except Exception:
                continue
            ids = set(NCT_RE.findall(txt))       # findall, NOT search
            if ids:
                per_file[os.path.relpath(f, ROOT).replace("\\", "/")] = ids
            found |= ids
        by_source[label] = found
        union |= found
    return by_source, union, per_file


def payload_coverage(payload_path):
    """How many stored NCTs hold a registry payload, under the stated definition."""
    if not payload_path or not os.path.exists(payload_path):
        return None
    have = set()
    meta = {}
    with open(payload_path, encoding="utf-8") as f:
        for line in f:
            try:
                d = json.loads(line)
            except ValueError:
                continue
            if (d.get("brief_title") or "").strip() and d.get("snapshot_data_date") \
                    and d.get("read_utc") and d.get("source_type"):
                have.add(d["nct_id"])
                meta.setdefault("snapshot_data_date", d["snapshot_data_date"])
                meta.setdefault("read_utc", d["read_utc"])
    return have, meta


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--json", default=None)
    ap.add_argument("--payloads", default=None,
                    help="JSONL of registry payloads to score coverage against")
    a = ap.parse_args()

    by_source, union, per_file = stored_ncts()
    print("STORED NCTs -- derived %s, not quoted" % os.path.basename(__file__))
    for label, ids in by_source.items():
        print("  %-12s %6d" % (label, len(ids)))
    print("  %-12s %6d   <- THE DENOMINATOR" % ("UNION", len(union)))
    print("  files carrying >=1 NCT: %d" % len(per_file))

    out = {"denominator": len(union),
           "by_source": {k: len(v) for k, v in by_source.items()},
           "definition_stored_nct":
               "any /NCT\\d{8}/ in ssot/*/*.json or evidence/**/*.json, re.findall",
           "definition_registry_payload":
               ("record keyed on nct_id with non-empty brief_title from a "
                "registered AACT snapshot, carrying snapshot_data_date, "
                "read_utc and source_type as fields"),
           "command": "python scripts/derive_nct_denominator.py"}

    # ⛔ AN EMPTY STORE IS AN ANOMALY TO REPORT, NOT A DIVISION TO PERFORM.
    # The first run of this module returned 0 because the worktree checkout had
    # been interrupted -- and a denominator script that crashes on 0 tells you
    # less than one that says "the store looks empty; check the checkout".
    if not union:
        print("\n⛔ NO NCTs FOUND. The store looks empty from %s." % ROOT)
        print("   ssot/ present: %s   evidence/ present: %s"
              % (os.path.isdir(os.path.join(ROOT, "ssot")),
                 os.path.isdir(os.path.join(ROOT, "evidence"))))
        print("   This is almost certainly an incomplete checkout, not a corpus "
              "with no trials. Refusing to report 0 as a denominator.")
        out["denominator"] = None
        out["anomaly"] = "no NCTs found; store appears empty or checkout incomplete"
        if a.json:
            json.dump(out, open(a.json, "w", encoding="utf-8"), indent=1)
        return out

    cov = payload_coverage(a.payloads)
    if cov:
        have, meta = cov
        hit = have & union
        print("\nREGISTRY PAYLOAD COVERAGE")
        print("  payloads meeting the definition : %d" % len(have))
        print("  of the denominator              : %d/%d = %.1f%%"
              % (len(hit), len(union), len(hit) / len(union) * 100))
        print("  snapshot_data_date              : %s" % meta.get("snapshot_data_date"))
        out["payload_coverage"] = {"n": len(hit), "of": len(union),
                                   "pct": round(len(hit) / len(union) * 100, 1),
                                   **meta}

    if a.json:
        json.dump(out, open(a.json, "w", encoding="utf-8"), indent=1)
        print("\nwrote %s" % a.json)
    return out


if __name__ == "__main__":
    main()
