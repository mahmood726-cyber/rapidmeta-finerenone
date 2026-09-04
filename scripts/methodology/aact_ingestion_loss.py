# -*- coding: utf-8 -*-
r"""Is the k deficit RETRIEVAL or INGESTION? A decisive, bounded test.

THE LOGIC, and it needs no ground truth:
  The AACT snapshot is ON LOCAL DISK. If trials that belong in a topic are sitting in that
  snapshot and were not ingested, then NO search-recall explanation can account for their
  absence -- there was no search. Retrieval cannot be the bottleneck for a file you already
  have. That makes this a near-impossibility argument of the same kind as the OR<AND result.

Snapshot: F:\AACT-storage\AACT\2026-08-30  (DATA DATE 2026-08-27 -- cite the data date,
never the folder date). NO PHASE FILTER: NCT01539226 is registered phase=NA and a phase
filter silently drops it.
"""
import io, os, re, sys, json, csv

if __name__ == "__main__":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace",
                                  line_buffering=True)

AACT = os.environ.get("AACT_DIR", r"F:\AACT-storage\AACT\2026-08-30")
DATA_DATE = "2026-08-27"


def col_index(path, want):
    with io.open(path, encoding="utf-8", errors="replace") as f:
        hdr = f.readline().rstrip("\n").split("|")
    return {w: (hdr.index(w) if w in hdr else None) for w in want}, hdr


def scan(path, want, match_col, pattern, out_col="nct_id"):
    """Single pass; returns set of nct_id whose match_col matches pattern."""
    idx, hdr = col_index(path, want + [match_col, out_col])
    mc, oc = idx[match_col], idx[out_col]
    if mc is None or oc is None:
        raise SystemExit("column missing in %s: have %s" % (path, hdr[:12]))
    rx = re.compile(pattern, re.I)
    hits = set()
    with io.open(path, encoding="utf-8", errors="replace") as f:
        f.readline()
        for line in f:
            p = line.rstrip("\n").split("|")
            if len(p) <= max(mc, oc):
                continue
            if rx.search(p[mc]):
                hits.add(p[oc])
    return hits


def col_map(path, key_col, val_cols):
    idx, hdr = col_index(path, [key_col] + val_cols)
    kc = idx[key_col]
    vcs = [idx[v] for v in val_cols]
    if kc is None or any(v is None for v in vcs):
        raise SystemExit("column missing in %s: have %s" % (path, hdr[:20]))
    out = {}
    with io.open(path, encoding="utf-8", errors="replace") as f:
        f.readline()
        for line in f:
            p = line.rstrip("\n").split("|")
            if len(p) <= max([kc] + vcs):
                continue
            out[p[kc]] = [p[v] for v in vcs]
    return out


def main():
    topic = sys.argv[1] if len(sys.argv) > 1 else "dapivirine"
    ingested = set(sys.argv[2].split(",")) if len(sys.argv) > 2 else set()
    print("MEASURED  AACT snapshot %s  (DATA DATE %s -- folder name overstates it)"
          % (AACT, DATA_DATE))
    print("          cmd: python aact_ingestion_loss.py %s" % topic)
    print("")

    iv = os.path.join(AACT, "interventions.txt")
    print("MEASURED  scanning interventions for %r ..." % topic)
    ncts = scan(iv, [], "name", re.escape(topic))
    print("          NCTs with a %s intervention: %d" % (topic, len(ncts)))

    st = col_map(os.path.join(AACT, "studies.txt"), "nct_id",
                 ["study_type", "phase", "overall_status", "enrollment"])
    dz = col_map(os.path.join(AACT, "designs.txt"), "nct_id", ["allocation"])

    interventional = {n for n in ncts if (st.get(n) or [""])[0].lower().startswith("interventional")}
    randomised = {n for n in interventional if "random" in (dz.get(n) or [""])[0].lower()}
    print("          of those, interventional : %d" % len(interventional))
    print("          of those, RANDOMISED     : %d   <-- the available population" % len(randomised))
    print("")

    # phase distribution -- shows what a phase filter would have destroyed
    ph = {}
    for n in randomised:
        p = (st.get(n) or ["", ""])[1] or "(blank)"
        ph[p] = ph.get(p, 0) + 1
    print("MEASURED  phase distribution of the randomised set (NO filter applied):")
    for k, v in sorted(ph.items(), key=lambda x: -x[1]):
        print("            %-22s %d" % (k, v))
    na = sum(v for k, v in ph.items() if k.upper() in ("NA", "(BLANK)", ""))
    print("          => a phase filter would silently drop %d of %d (%.0f%%)"
          % (na, len(randomised), 100.0 * na / max(1, len(randomised))))
    print("")

    if ingested:
        have = ingested & randomised
        miss = randomised - ingested
        print("=== INGESTION LOSS ===")
        print("  available in the LOCAL snapshot : %d" % len(randomised))
        print("  actually ingested by the topic  : %d" % len(ingested))
        print("  ingested AND available          : %d" % len(have))
        print("  AVAILABLE BUT NOT INGESTED      : %d" % len(miss))
        print("  ingestion recall                : %.3f" % (len(have) / float(len(randomised))))
        print("")
        print("  ⇒ every one of those %d was on local disk. No search was involved," % len(miss))
        print("    so search recall cannot explain their absence.")
        print("")
        print("  the missed NCTs, with enrolment (largest first):")
        rows = sorted(miss, key=lambda n: -int((st.get(n) or ["", "", "", "0"])[3] or 0))
        for n in rows[:20]:
            s = st.get(n) or ["", "", "", ""]
            print("    %s  phase=%-10s n=%-7s %s" % (n, s[1] or "NA", s[3] or "?", s[2][:26]))
        json.dump({"topic": topic, "data_date": DATA_DATE, "available": sorted(randomised),
                   "ingested": sorted(ingested), "missed": sorted(miss),
                   "ingestion_recall": len(have) / float(len(randomised))},
                  io.open("aact_ingestion_loss_%s.json" % topic, "w", encoding="utf-8"), indent=1)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
