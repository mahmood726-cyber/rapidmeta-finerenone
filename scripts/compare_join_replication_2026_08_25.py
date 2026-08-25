"""Did the join result replicate at ten times the sample, out of sample?

WHAT IS BEING TESTED. The first end-to-end run used 40 reviews and 886 labels, selected as
every 15th .rda file in Pairwise70/data. Two figures were built on it and everything after
rests on them:

    resolution   676 / 886 = 76% of labels reach exactly one reference
    stratum      0% of labels before 2005 carry a registration, 13-23% after

The widened run applies THE SAME RULE at offsets 0..9 -- 400 reviews. Offset 0 is the original
40, so the other 360 reviews are a HELD-OUT replication under an identical selection rule, not
a fresh design that could differ for uninteresting reasons.

WHY HELD-OUT MATTERS HERE. If the widened figures are quoted including the original 40, the
original result is partly measuring itself. Every number below is therefore reported three
ways: the original 40, the 360 held-out, and the union -- and the held-out column is the one
that answers whether the result replicates.

WHAT WOULD COUNT AS A FAILURE TO REPLICATE, stated before looking:
  * resolution outside 66-86% (the original 76% plus or minus ten points), or
  * any pre-2005 stratum above 2%, which would break the policy-discontinuity validation, or
  * a null resolution rate above 2%, which would mean spurious matching at scale

The pre-2005 criterion is the one that matters most: the discontinuity at 2005 is the
strongest evidence the pipeline measures what it claims, precisely because the instrument was
never told that registration became an ICMJE requirement that year.
"""
import io
import json
import os
import sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
NARROW = os.path.join(REPO, "outputs", "join_end_to_end_2026_08_25.json")
WIDE = os.path.join(REPO, "outputs", "join_end_to_end_wide_2026_08_25.json")
OUT = os.path.join(REPO, "outputs", "join_replication_2026_08_25.json")

ERAS = [("pre-1990", 0, 1990), ("1990-1999", 1990, 2000), ("2000-2004", 2000, 2005),
        ("2005-2009", 2005, 2010), ("2010-2014", 2010, 2015), ("2015+", 2015, 9999)]


def summarise(rows):
    n = len(rows)
    resolved = sum(1 for r in rows if r.get("stage") == "resolved_in_bibliography")
    nct = sum(1 for r in rows if r.get("nct"))
    null = sum(1 for r in rows if r.get("null_hits") == 1)
    eras = {}
    for name, lo, hi in ERAS:
        sel = [r for r in rows if r.get("year") and lo <= int(r["year"]) < hi]
        eras[name] = {"n": len(sel), "nct": sum(1 for r in sel if r.get("nct"))}
    return {"n": n, "resolved": resolved, "nct": nct, "null": null, "eras": eras}


def pct(a, b):
    return (100.0 * a / b) if b else 0.0


def main():
    raw = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace",
                           write_through=True)

    def log(s):
        raw.write(s + chr(10))
        raw.flush()

    if not os.path.exists(WIDE):
        log("NOT MEASURABLE: %s does not exist. The widened run has not produced an "
            "artefact, so no replication is reported." % os.path.relpath(WIDE, REPO))
        return 1

    wide = json.load(io.open(WIDE, encoding="utf-8"))["rows"]
    held = [r for r in wide if r.get("held_out")]
    orig = [r for r in wide if not r.get("held_out")]
    if not held:
        log("NOT MEASURABLE: no row is marked held_out, so the original 40 cannot be "
            "separated from the replication and neither figure is reported.")
        return 1

    groups = [("original 40", orig), ("HELD-OUT 360", held), ("union 400", wide)]
    log("%-14s %7s %11s %9s %9s" % ("group", "labels", "resolved", "with NCT", "null"))
    S = {}
    for name, rows in groups:
        s = summarise(rows)
        S[name] = s
        log("%-14s %7d %6d %4.0f%% %4d %4.0f%% %4d %4.0f%%"
            % (name, s["n"], s["resolved"], pct(s["resolved"], s["n"]),
               s["nct"], pct(s["nct"], s["n"]), s["null"], pct(s["null"], s["n"])))

    log("")
    log("%-11s %s" % ("era", "  ".join("%14s" % g for g, _ in groups)))
    for name, _lo, _hi in ERAS:
        cells = []
        for g, _ in groups:
            e = S[g]["eras"][name]
            cells.append("%5d %5.0f%%" % (e["n"], pct(e["nct"], e["n"])))
        log("%-11s %s" % (name, "     ".join(cells)))

    h = S["HELD-OUT 360"]
    res = pct(h["resolved"], h["n"])
    pre = sum(h["eras"][k]["nct"] for k in ("pre-1990", "1990-1999", "2000-2004"))
    pren = sum(h["eras"][k]["n"] for k in ("pre-1990", "1990-1999", "2000-2004"))
    nullr = pct(h["null"], h["n"])
    fails = []
    if not (66.0 <= res <= 86.0):
        fails.append("resolution %.0f%% is outside the pre-stated 66-86%%" % res)
    if pct(pre, pren) > 2.0:
        fails.append("pre-2005 stratum %.1f%% exceeds 2%%, breaking the discontinuity"
                     % pct(pre, pren))
    if nullr > 2.0:
        fails.append("null %.1f%% exceeds 2%%" % nullr)

    log("")
    log("HELD-OUT 360, against criteria fixed before looking:")
    log("  resolution        %.0f%%   (pass band 66-86%%)" % res)
    log("  pre-2005 with NCT %d / %d = %.1f%%   (must stay at or below 2%%)"
        % (pre, pren, pct(pre, pren)))
    log("  null              %.1f%%   (must stay at or below 2%%)" % nullr)
    log("")
    if fails:
        log("DID NOT REPLICATE:")
        for f in fails:
            log("   " + f)
    else:
        log("REPLICATED on all three criteria, out of sample.")

    json.dump({"criteria": "resolution 66-86%, pre-2005 stratum <=2%, null <=2%; fixed "
                           "before the widened run was read",
               "groups": S, "failures": fails},
              io.open(OUT, "w", encoding="utf-8"), indent=1)
    log("wrote %s" % os.path.relpath(OUT, REPO))
    return 0


if __name__ == "__main__":
    sys.exit(main())
