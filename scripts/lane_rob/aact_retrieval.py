# -*- coding: utf-8 -*-
"""Step 0, against the AACT snapshot, which is the registry snapshot that actually has
results. Read-only.

THE FIRST PASS LOOKED IN THE WRONG PLACE. `.ctgov-raw-cache` holds 353 of our 353 NCTs but
only 9 carry a results section -- it is a protocol cache, not a results one. AACT
2026-04-12 holds `outcome_analyses` (95M), `outcome_counts` (107M) and
`outcome_measurements` (2.8G). Reporting "9 actionable" off the protocol cache would have
been a reach figure with a confident denominator attached to it.

FORMAT NOTE, recorded because a stored note disagrees: these files are PIPE-delimited with a
header row, not the quoted CSV a memory entry describes. Read as observed.

TWO KINDS, AND THEY ARE NOT INTERCHANGEABLE:
  READ VERBATIM  outcome_analyses row carrying param_value AND both CI limits. Nothing is
                 computed; the registry's own number is transcribed.
  DERIVE         arm-level counts for two or more result groups. A number is computed and
                 the formula has to be recorded with it.
A trial can offer both; it is counted once, under the stronger kind.
"""
import collections
import glob
import io
import json
import os
import sys

# GUARDED. A module-level stdout reassignment closes the CALLER's stdout the moment
# this file is imported, and every script here is now importable -- three separate
# checks of this lane's own output died that way before it was fixed at the source.
if __name__ == "__main__":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8",
                                  errors="replace", line_buffering=True)
REPO = r"F:\rapidmeta-ssot-shell"
AACT = r"F:\AACT-storage\AACT\2026-04-12"
os.chdir(REPO)


def our_trials():
    rows = []
    for p in sorted(glob.glob("ssot/*/*.json")):
        topic = os.path.basename(os.path.dirname(p))
        if os.path.basename(p) != topic + ".json":
            continue
        try:
            obj = json.load(io.open(p, encoding="utf-8"))
        except Exception:
            continue
        contributing = set()
        for blk in ((obj.get("results") or {}).get("by_outcome") or {}).values():
            for r in (blk.get("per_trial") or []):
                if isinstance(r, dict) and any(
                        r.get(k) is not None for k in
                        ("point", "hr", "rr", "or", "estimate", "se_log")):
                    for k in ("nct", "id", "trial"):
                        if r.get(k):
                            contributing.add(str(r[k]))
        for t in ((obj.get("inputs") or {}).get("trials") or []):
            if not isinstance(t, dict) or not t.get("nct"):
                continue
            contrib = any(str(t.get(k)) in contributing for k in ("nct", "id", "name")
                          if t.get(k))
            rows.append({"topic": topic, "nct": t["nct"],
                         "name": t.get("name") or t.get("id") or "",
                         "contributes": contrib})
    return rows


def scan(fname, nct_col, want, ncts):
    """Stream one pipe-delimited AACT table; return {nct: count-of-qualifying-rows}."""
    out = collections.Counter()
    path = os.path.join(AACT, fname)
    with io.open(path, encoding="utf-8", errors="replace") as fh:
        hdr = fh.readline().rstrip("\n").split("|")
        idx = {h: i for i, h in enumerate(hdr)}
        ci = idx[nct_col]
        for line in fh:
            f = line.rstrip("\n").split("|")
            if len(f) <= ci:
                continue
            n = f[ci]
            if n not in ncts:
                continue
            if want(f, idx):
                out[n] += 1
    return out


def main():
    rows = our_trials()
    ncts = {r["nct"] for r in rows}
    print("OUR TRIALS")
    print("  trial rows across stores                  %4d  == the denominator" % len(rows))
    print("  distinct NCTs                             %4d" % len(ncts))
    print("  contributing an effect already            %4d"
          % len({r["nct"] for r in rows if r["contributes"]}))
    print("  contributing nothing                      %4d"
          % len({r["nct"] for r in rows if not r["contributes"]}))
    print("")
    print("Scanning AACT 2026-04-12 ...")

    def has_effect(f, idx):
        return bool(f[idx["param_value"]].strip()) and \
            bool(f[idx["ci_lower_limit"]].strip()) and \
            bool(f[idx["ci_upper_limit"]].strip())
    eff = scan("outcome_analyses.txt", "nct_id", has_effect, ncts)
    print("  outcome_analyses rows with effect + CI    scanned")

    def any_count(f, idx):
        return bool(f[idx["count"]].strip()) if "count" in idx else True
    cnt = scan("outcome_counts.txt", "nct_id", any_count, ncts)
    print("  outcome_counts rows                       scanned")

    grp = scan("result_groups.txt", "nct_id", lambda f, i: True, ncts)
    print("  result_groups rows                        scanned")
    print("")

    kinds = collections.Counter()
    detail = []
    for r in rows:
        n = r["nct"]
        if eff.get(n):
            k = "READ VERBATIM -- posted analysis with effect and interval"
        elif cnt.get(n) and grp.get(n, 0) >= 2:
            k = "DERIVE -- arm-level counts for >=2 groups"
        elif grp.get(n):
            k = "results posted, but neither an effect nor usable counts"
        else:
            k = "no results in AACT"
        kinds[(k, r["contributes"])] += 1
        detail.append({**r, "kind": k, "n_effect_rows": eff.get(n, 0),
                       "n_count_rows": cnt.get(n, 0), "n_groups": grp.get(n, 0)})

    print("=" * 90)
    print("WHAT THE SNAPSHOT ALREADY HOLDS, split by whether the trial already contributes")
    print("=" * 90)
    print("  %-58s %9s %9s" % ("", "already", "contributes"))
    print("  %-58s %9s %9s" % ("kind", "contributes", "nothing"))
    order = ["READ VERBATIM -- posted analysis with effect and interval",
             "DERIVE -- arm-level counts for >=2 groups",
             "results posted, but neither an effect nor usable counts",
             "no results in AACT"]
    for k in order:
        print("  %-58s %9d %9d" % (k[:58], kinds[(k, True)], kinds[(k, False)]))
    print("  %-58s %9d %9d" % ("sum", sum(v for (k, c), v in kinds.items() if c),
                               sum(v for (k, c), v in kinds.items() if not c)))
    print("")
    act = sum(kinds[(k, False)] for k in order[:2])
    print("  ACTIONABLE WITHOUT RETRIEVING A PAPER, on trials that contribute nothing: %d"
          % act)
    print("     of which read verbatim %d, derive %d"
          % (kinds[(order[0], False)], kinds[(order[1], False)]))
    json.dump(detail, io.open(r"F:\claude-temp\pend\aact_retrieval.json", "w",
                              encoding="utf-8"), indent=1)
    print("")
    print("  detail -> aact_retrieval.json")


if __name__ == "__main__":
    main()
