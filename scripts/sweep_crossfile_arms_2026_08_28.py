"""Cross-file: `as_posted` against `findings/pmid_groups.json`, WITHOUT sorting the arms.

THE OTHER LANE BUILT THIS AND NAMED ITS OWN LIMITATION: its test SORTS both sides, so it can
say THAT two copies differ and not WHICH ARM differs. That is the one thing worth adding, so
this compares treatment against treatment and control against control, positionally.

  Its real denominator was 7, not 72 -- 65 of 70 have no topic object and 5 have an object
  with no as_posted. Of the 2 with both values, both diverged.

AND IT MISSES THE PERCENTAGE SHAPE, so its sweep never looked at hepatitis-b-taf-tdf, the
object that motivated the whole thread. This routes through the shared `_as_posted_pairs`,
which handles all EIGHT schemas in this corpus, so that gap does not repeat here.

WHAT A DIVERGENCE MEANS DEPENDS ON ITS SIZE, and conflating the two would be the second-name
trap again:

    ~0.5   a CONTINUITY CORRECTION -- as_posted holds the uncorrected count and the analysis
           adds 0.5 to a zero or complete cell. The same quantity, two states.
    large  a DIFFERENT POPULATION -- interim micro-ITT against ITT. The other lane's two
           divergences are 12 to 536, which is this, not a correction.

So the size is reported beside every divergence and the two are never summed.

NOTHING IS WRITTEN. Deciding which population a page should report is a published-number
decision.
"""
import collections
import io
import json
import os
import sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(REPO, "ssot"))
from paper_projector import _as_posted_pairs        # noqa: E402  one parser, every caller

OUT = os.path.join(REPO, "outputs", "crossfile_arms_2026_08_28.json")
GROUPS = os.path.join(REPO, "findings", "pmid_groups.json")
CORRECTION = 0.6      # anything at or under this is the 0.5 continuity-correction shape


def num(v):
    try:
        return float(str(v).strip())
    except (TypeError, ValueError):
        return None


def main():
    raw = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace",
                           write_through=True)

    def say(s):
        raw.write(s + chr(10))
        raw.flush()

    pm = json.load(io.open(os.path.join(REPO, "ssot", "PAGE_MAP.json"), encoding="utf-8"))
    groups = json.load(io.open(GROUPS, encoding="utf-8"))

    c = collections.Counter()
    rows = []
    n_pages = len(groups)

    for page, rec in sorted(groups.items()):
        rel = pm.get(page)
        if not rel or not os.path.exists(os.path.join(REPO, rel)):
            c["page has NO topic object"] += 1
            continue
        obj = json.load(io.open(os.path.join(REPO, rel), encoding="utf-8"))
        # Side A, keyed by NCT, through the shared parser
        sideA = {}
        for _oid, blk in ((obj.get("results") or {}).get("by_outcome") or {}).items():
            if not isinstance(blk, dict):
                continue
            for r in blk.get("per_trial") or []:
                if not isinstance(r, dict):
                    continue
                pairs = _as_posted_pairs(r.get("as_posted"))
                if pairs and r.get("nct"):
                    sideA[r["nct"]] = pairs
        if not sideA:
            c["object has NO as_posted"] += 1
            continue

        for pmid, members in (rec.get("dups") or {}).items():
            for m in members or []:
                nct = str(m.get("name") or "")
                if nct not in sideA:
                    continue
                (a_lab, a_e, a_n), (b_lab, b_e, b_n) = sideA[nct]
                tE, tN, cE, cN = (num(m.get("tE")), num(m.get("tN")),
                                  num(m.get("cE")), num(m.get("cN")))
                a_e_n, b_e_n = num(a_e), num(b_e)
                if None in (tE, tN, cE, cN) or a_e_n is None or b_e_n is None:
                    c["values not both numeric"] += 1
                    continue

                # POSITIONAL, NOT SORTED. treatment against treatment, control against control.
                diffs = []
                for who, ours, theirs in (("treatment events", a_e_n, tE),
                                          ("treatment n", num(a_n), tN),
                                          ("control events", b_e_n, cE),
                                          ("control n", num(b_n), cN)):
                    if ours is None or theirs is None:
                        continue
                    d = abs(ours - theirs)
                    if d > 0:
                        diffs.append((who, ours, theirs, d))
                if not diffs:
                    c["AGREE"] += 1
                    continue
                worst = max(d for _, _, _, d in diffs)
                kind = ("CONTINUITY-CORRECTION SHAPE" if worst <= CORRECTION
                        else "DIFFERENT POPULATION SHAPE")
                c[kind] += 1
                rows.append({"page": page, "nct": nct, "pmid": pmid, "kind": kind,
                             "largest_delta": worst,
                             "which_arms_differ": [{"field": w, "as_posted": o,
                                                    "pmid_groups": t, "delta": d}
                                                   for w, o, t, d in diffs]})

    total = sum(v for k, v in c.items() if k in ("AGREE", "CONTINUITY-CORRECTION SHAPE",
                                                 "DIFFERENT POPULATION SHAPE",
                                                 "values not both numeric"))
    say("pages in pmid_groups.json          : %d" % n_pages)
    say("  page has NO topic object         : %d" % c["page has NO topic object"])
    say("  object has NO as_posted          : %d" % c["object has NO as_posted"])
    say("")
    say("TRIALS ACTUALLY COMPARABLE         : %d   <- the real denominator" % total)
    for k in ("AGREE", "CONTINUITY-CORRECTION SHAPE", "DIFFERENT POPULATION SHAPE",
              "values not both numeric"):
        say("  %-30s %d" % (k, c[k]))
    say("")
    say("DIVERGENCES, AND WHICH ARM -- not sorted, so this can say which")
    for r in rows:
        say("  %-38s %s  %s  worst delta %.1f"
            % (r["page"][:38], r["nct"], r["kind"], r["largest_delta"]))
        for d in r["which_arms_differ"]:
            say("       %-18s as_posted=%-8s pmid_groups=%-8s delta %.1f"
                % (d["field"], d["as_posted"], d["pmid_groups"], d["delta"]))
    if not rows:
        say("  (none)")

    json.dump({"question": "does as_posted agree with findings/pmid_groups.json, arm by arm",
               "improvement_over_the_prior_sweep": "positional, not sorted -- so it names "
                                                   "WHICH arm differs, not only THAT the "
                                                   "copies differ",
               "schemas": "routes through the shared _as_posted_pairs, which handles all "
                          "eight as_posted shapes; the prior sweep missed the percentage "
                          "shape and so never examined hepatitis-b-taf-tdf",
               "delta_meaning": {"~0.5": "continuity correction -- same quantity, two states",
                                 "large": "different population -- interim micro-ITT against "
                                          "ITT. Never sum the two kinds."},
               "counts": dict(c), "real_denominator": total, "rows": rows,
               "not_written": "which population a page should report is a published-number "
                              "decision"},
              io.open(OUT, "w", encoding="utf-8"), indent=1)
    say("")
    say("wrote %s" % os.path.relpath(OUT, REPO))
    return 0


if __name__ == "__main__":
    sys.exit(main())
