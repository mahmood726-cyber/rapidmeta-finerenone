#!/usr/bin/env python3
"""MAP THE UNMAPPED DASHBOARD ROWS -- by agreement between page and object, never by name rule.

WHY THIS OUTRANKS THE TOPIC QUEUE. The projection gate exists to stop a page serving a value its
object does not support. It can only check a row it can MAP. 601 rows serve a pooled value with
`ssot_state: UNMAPPED`, 562 of them with a page on disk -- so the gate's clean result has been
true of the mapped subset and SILENT about the rest. `hepatitis-b-taf-tdf-review` was one of
them, and it was serving an odds ratio comparing a drug with itself.

    A CHECK THAT CANNOT SEE A ROW REPORTS CLEAN ON IT. Same shape as a delivery check that
    verified localhost.

WHY THE MAPPING IS NOT A NAME RULE. Of the 131 existing PAGE_MAP entries, only 48 are what
lowercase-and-hyphenate produces. 83 are not:

    ALIROCUMAB_LIPID_AUTO_FULL_REVIEW.html  ->  alirocumab-lipid       (suffix dropped)
    ARNI_HF_REVIEW.html                     ->  arni-hfref             (not derivable at all)
    AZILSARTAN_HTN_AUTO_FULL_REVIEW.html    ->  azilsartan-chlorthalidone-vs-olmesartan-hctz

A rule that always returns a topic name would map all 601, most of them plausibly, some of them
WRONGLY -- and a wrong mapping is worse than none, because it points the gate at the wrong
object and can either clear a bad row or withdraw a good value. THAT IS THE ARBITRARY-SELECTION
CLASS AGAIN: a rule that cannot return nothing cannot tell you it does not know.

SO THE MAPPING IS VERIFIED, NOT DERIVED. A candidate is accepted only when the PAGE and the
OBJECT AGREE ON THEIR TRIALS: the registration identifiers embedded in the page's own bytes must
intersect the object's included set. Name similarity proposes; trial agreement disposes.

    Candidates with no object on disk        -> UNMAPPABLE_NO_SUCH_OBJECT
    Candidates whose trials do not intersect -> UNMAPPABLE_TRIALS_DISAGREE  (reported, never mapped)
    Rows whose page is not on disk           -> reported separately; these are their own question

USAGE
    python scripts/map_unmapped_dashboard_rows_2026_08_19.py [--apply]
"""
import io
import json
import os
import re
import sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SNAP = os.path.join(REPO, "outputs", "portfolio_index.json")
PMAP = os.path.join(REPO, "ssot", "PAGE_MAP.json")
OUT = os.path.join(REPO, "evidence", "2026-08-19-batch1", "unmapped_row_mapping.json")

NCT = re.compile(r"NCT\d{8}")


def object_trials():
    """{topic: set(nct)} for every live object on disk."""
    import glob
    out = {}
    for p in sorted(glob.glob(os.path.join(REPO, "ssot", "*", "*.json"))):
        topic = os.path.basename(os.path.dirname(p))
        if os.path.basename(p) != topic + ".json":
            continue
        try:
            with io.open(p, "r", encoding="utf-8") as fh:
                o = json.load(fh)
        except Exception:
            continue
        ncts = {t.get("nct") for t in ((o.get("inputs") or {}).get("trials") or [])
                if isinstance(t, dict) and t.get("nct")}
        out[topic] = {n for n in ncts if n and NCT.fullmatch(n)}
    return out


def page_trials(page):
    p = os.path.join(REPO, page)
    if not os.path.exists(p):
        return None
    with io.open(p, "rb") as fh:
        raw = fh.read()
    return set(NCT.findall(raw.decode("utf-8", "replace")))


def candidates(page, topics):
    """Name-similarity CANDIDATES only. Nothing here is accepted without trial agreement."""
    base = page[:-5].lower().replace("_", "-")
    out = []
    for c in (base,
              base.replace("-auto-full-review", ""),
              base.replace("-auto-full-review", "-review"),
              base.replace("-review", ""),
              base.replace("-auto-review", ""),
              base.replace("-ssot", "")):
        if c in topics and c not in out:
            out.append(c)
    # Any topic whose name shares the leading token is also a candidate; trial agreement filters.
    head = base.split("-")[0]
    for t in topics:
        if t.split("-")[0] == head and t not in out:
            out.append(t)
    return out


def run(apply_it):
    snap = json.load(io.open(SNAP, encoding="utf-8"))
    pmap = json.load(io.open(PMAP, encoding="utf-8"))
    topics = object_trials()

    rows = [r for r in snap["rows"]
            if r.get("ssot_state") == "UNMAPPED"
            and isinstance(r.get("pooled_OR"), (int, float))]
    print("UNMAPPED rows serving a pooled value: %d" % len(rows))

    mapped, no_page, no_obj, disagree, ambiguous = [], [], [], [], []
    for r in rows:
        page = r.get("file")
        pt = page_trials(page)
        if pt is None:
            no_page.append(page)
            continue
        cands = candidates(page, topics)
        if not cands:
            no_obj.append({"page": page, "why": "no object name resembles this page"})
            continue
        agree = [c for c in cands if topics[c] and pt and (topics[c] & pt)]
        if not agree:
            disagree.append({"page": page, "candidates": cands[:4],
                             "n_ncts_on_the_page": len(pt),
                             "why": ("name-similar objects exist but NONE shares a registration "
                                     "identifier with the page. Mapping on the name alone would "
                                     "point the gate at the wrong object.")})
            continue
        if len(agree) > 1:
            best = max(agree, key=lambda c: len(topics[c] & pt))
            ties = [c for c in agree if len(topics[c] & pt) == len(topics[best] & pt)]
            if len(ties) > 1:
                ambiguous.append({"page": page, "tied": ties,
                                  "why": "more than one object agrees equally on trials"})
                continue
            agree = [best]
        t = agree[0]
        mapped.append({"page": page, "topic": t,
                       "ncts_shared": sorted(topics[t] & pt),
                       "n_shared": len(topics[t] & pt),
                       "n_in_object": len(topics[t]), "n_on_page": len(pt)})

    print("\n  MAPPED by page/object trial agreement : %d" % len(mapped))
    print("  page not on disk                      : %d" % len(no_page))
    print("  no name-similar object                : %d" % len(no_obj))
    print("  name-similar but TRIALS DISAGREE      : %d" % len(disagree))
    print("  ambiguous, more than one object agrees: %d" % len(ambiguous))

    doc = {
        "run_utc": "2026-08-19",
        "why": ("The projection gate can only check a row it can map. 601 rows served a pooled "
                "value while UNMAPPED, so the gate's clean result was true of the mapped subset "
                "and silent about the rest."),
        "method": ("VERIFIED, NOT DERIVED. Name similarity proposes a candidate; the page and "
                   "the object must AGREE ON THEIR TRIALS -- the registration identifiers in "
                   "the page's own bytes must intersect the object's included set -- before any "
                   "mapping is written. Only 48 of 131 existing PAGE_MAP entries are what a "
                   "name rule produces, so a name rule would have mapped hundreds of rows "
                   "plausibly and some wrongly, with nothing to say which."),
        "counts": {"unmapped_rows_serving_a_value": len(rows),
                   "mapped_by_trial_agreement": len(mapped),
                   "page_not_on_disk": len(no_page),
                   "no_name_similar_object": len(no_obj),
                   "trials_disagree": len(disagree),
                   "ambiguous": len(ambiguous)},
        "mapped": mapped, "page_not_on_disk": no_page, "no_name_similar_object": no_obj,
        "trials_disagree": disagree, "ambiguous": ambiguous,
        "what_this_does_not_do": (
            "It does not check the mapped rows' VALUES. Mapping only makes them visible to the "
            "projection gate; what the gate then finds is a separate result."),
    }
    if apply_it:
        for m in mapped:
            pmap[m["page"]] = "ssot/%s/%s.json" % (m["topic"], m["topic"])
        with io.open(PMAP, "w", encoding="utf-8", newline="") as fh:
            fh.write(json.dumps(pmap, indent=1, ensure_ascii=False, sort_keys=True))
        with io.open(OUT, "w", encoding="utf-8", newline="") as fh:
            fh.write(json.dumps(doc, indent=1, ensure_ascii=False))
        print("\n  PAGE_MAP now holds %d entries; wrote %s"
              % (len(pmap), os.path.relpath(OUT, REPO)))
    else:
        print("\nDRY RUN -- nothing written.")
    return 0


if __name__ == "__main__":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    sys.exit(run("--apply" in sys.argv))
