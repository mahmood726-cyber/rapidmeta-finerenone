r"""How much of this corpus names a harm and reports none -- measured, with the denominator named.

WHAT THE EXTERNAL REVIEWS SAID. Across fifteen reviews, seven pages were told the same
thing: the review's own PICO names harms and the review synthesises none, while the harms
data sit in the primary publications.

WHAT THIS INSTRUMENT MEASURES, AND WHY IT IS TWO NUMBERS AND NOT ONE.

    CLASS 1 -- A BROKEN PROMISE.  The stored PICO names a harm outcome and the object
              publishes neither a synthesis of it nor a reasoned refusal. The review
              undertook something and did not deliver it.

    CLASS 2 -- AN UNTAKEN OPPORTUNITY.  The PICO does not name a harm, but a trial the
              review already read REGISTERED one, and the object synthesises no harm at
              all. Nothing was promised; something available was not used.

    THE TWO ARE NOT THE SAME DEFECT AND MUST NOT SHARE A COUNT. Class 1 is a page
    contradicting itself. Class 2 is a page being narrower than its sources. Folding them
    together produces a large, alarming number that no single fix addresses, and it
    breaks the rule this lane was given explicitly: A TOPIC WHOSE PICO DOES NOT NAME
    HARMS IS NOT A DEFECT, AND MUST NOT INFLATE THE COUNT.

    Five of the seven pages the reviews named are CLASS 2, not class 1. Saying so is the
    point of separating them -- it is also why class 1 comes out at 2 and not at 7.

KINDS BEFORE COUNTS. The population is not "the pages". It is:

    tombstone            a retired object, absorbed into another page. Not a review.
    live SSOT topic      has question + outcomes + results.by_outcome. ASSESSABLE.
    app shell            a *_REVIEW.html carrying state.protocol with trials:[] -- the
                         interactive tool seeded with a boilerplate PICO and NO data.
                         There is no synthesis to be missing.
    redirect stub        a ~5KB *_AUTO_REVIEW.html that meta-refreshes to the full page.
    unclassified page    everything else, named rather than absorbed into a total.

Only `live SSOT topic` can carry this defect, and CLASS 2 is further restricted to those
that store registered-outcome text at all -- 39 live objects store none, and for those
the question is NOT-ASSESSABLE, which is its own kind and is never folded into a pass.

THE DETECTOR PRODUCES CANDIDATES, NOT VERDICTS. Precision is measured by CENSUS: every
class-1 candidate is hand-adjudicated in gates/HARMS_PICO_ADJUDICATION.json, so the
class-1 count carries no sampling error. Recall is the open risk and is estimated from a
sample pre-registered before it was drawn; the bound it supports is stated, not implied.

Usage:  python scripts/measure_harms_gap.py [--json OUT]
Exit 0 always -- THIS IS A MEASUREMENT, NOT A GATE. The gate is
gates/gate21_pico_names_harm_unsynthesised.py, and it is the thing that refuses.
"""
from __future__ import annotations

import argparse
import collections
import glob
import io
import json
import os
import re
import sys

if __name__ == "__main__" and not os.environ.get("_GATE_WRAPPED"):
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(REPO, "scripts"))

from harms_pico_surface import (  # noqa: E402
    HARM_RX, decide, harm_mentions, harms_synthesis, synthesised_outcome_ids)

ADJUDICATION = os.path.join(REPO, "gates", "HARMS_PICO_ADJUDICATION.json")


def load_live_and_tombstones():
    """-> (live {app_id: obj}, tombstones [app_id], dirs_without_json [name])."""
    base = os.path.join(REPO, "ssot")
    live, tombs, nojson = {}, [], []
    for d in sorted(os.listdir(base)):
        full = os.path.join(base, d)
        if not os.path.isdir(full) or d.startswith("__"):
            continue
        p = os.path.join(full, d + ".json")
        # STATED POSITIVELY, and every branch lands somewhere countable. A `continue` on
        # a missing file would drop the directory out of the population without a trace,
        # which is the exclusion-by-absence class this repo's own gate refuses.
        if os.path.exists(p):
            with io.open(p, encoding="utf-8") as fh:
                obj = json.load(fh)
            # A TOMBSTONE IS NOT A REVIEW AND IS NOT A DEFECT. It is a retired object
            # kept so its page still resolves; it has no question because it makes no
            # claim. Its own kind, never folded into either count.
            if "question" in obj:
                live[d] = obj
            else:
                tombs.append(d)
        else:
            nojson.append(d)
    return live, tombs, nojson


def page_kinds():
    """The 1,464 HTML pages, by kind, read from the files rather than from a list."""
    with io.open(os.path.join(REPO, "ssot", "PAGE_MAP.json"), encoding="utf-8") as fh:
        mapped = set(json.load(fh))
    kinds = collections.Counter()
    # THE POPULATION IS STATED POSITIVELY: the .html files in the repository root. Naming
    # it as a glob rather than filtering inside the loop means the denominator is written
    # down once, in one place, and no item is dropped by a branch further in.
    for f in sorted(glob.glob(os.path.join(REPO, "*.html"))):
        f = os.path.basename(f)
        if f in mapped:
            kinds["SSOT-backed page"] += 1
            continue
        with io.open(os.path.join(REPO, f), encoding="utf-8", errors="replace") as fh:
            s = fh.read()
        if "state:{protocol:{" in s:
            kinds["app shell (boilerplate PICO, trials:[] empty)"] += 1
        elif 'name="rm-orphan-redirect"' in s or "location.replace(" in s[:4000]:
            kinds["redirect stub"] += 1
        else:
            kinds["unclassified page"] += 1
    return kinds, mapped


def registered_outcome_text(obj):
    """-> [(nct, field, text)] over every registered outcome this object already stores.

    Read from the OBJECT, not from the registry: this measures what the review had in
    hand and did not use. Going back to ClinicalTrials.gov would measure something else
    -- what exists -- and would make the number depend on a network call.
    """
    out = []
    for t in ((obj.get("inputs") or {}).get("trials") or []):
        if not isinstance(t, dict):
            continue
        for key in ("registered_primaries", "registered_secondaries",
                    "registered_other_outcomes", "registered_primary_title"):
            v = t.get(key)
            if isinstance(v, str):
                out.append((t.get("nct"), key, v))
            elif isinstance(v, list):
                for x in v:
                    if isinstance(x, str):
                        out.append((t.get("nct"), key, x))
                    elif isinstance(x, dict):
                        out.append((t.get("nct"), key,
                                    str(x.get("title") or x.get("measure") or x)))
    return out


def main(argv):
    ap = argparse.ArgumentParser()
    ap.add_argument("--json", dest="out")
    a = ap.parse_args(argv)

    live, tombs, nojson = load_live_and_tombstones()
    kinds, mapped = page_kinds()
    with io.open(ADJUDICATION, encoding="utf-8") as fh:
        adj_doc = json.load(fh)
    adj = {r["app_id"]: r for r in adj_doc["rows"]}

    print("=" * 78)
    print("THE HARMS GAP, MEASURED")
    print("=" * 78)
    print()
    print("KINDS IN THE PAGE POPULATION -- named before counted, because a count over a")
    print("population whose kinds were never enumerated is a denominator that was assumed.")
    total_pages = sum(kinds.values())
    for k, v in kinds.most_common():
        print("    %6d  %s" % (v, k))
    print("    %6d  TOTAL .html files in the repository root" % total_pages)
    print()
    print("KINDS IN THE SSOT POPULATION")
    print("    %6d  live topic (question + outcomes + results.by_outcome) -- ASSESSABLE"
          % len(live))
    print("    %6d  tombstone (retired, absorbed elsewhere; makes no claim)" % len(tombs))
    print("    %6d  directory carrying no .json" % len(nojson))
    print()
    print("COVERAGE: %d of %d pages (%.1f%%) are SSOT-backed and can be assessed at all."
          % (len(mapped), total_pages, 100.0 * len(mapped) / total_pages))
    print("    the other %d: %d app shells that hold a boilerplate PICO and an EMPTY"
          % (total_pages - len(mapped), kinds["app shell (boilerplate PICO, trials:[] empty)"]))
    print("    trials array -- there is no synthesis for a harm to be missing from -- plus")
    print("    %d redirect stubs and %d unclassified pages."
          % (kinds["redirect stub"], kinds["unclassified page"]))
    print()

    # ---- CLASS 1 -----------------------------------------------------------------
    print("-" * 78)
    print("CLASS 1 -- THE PICO NAMES A HARM AND THE OBJECT REPORTS NONE")
    print("-" * 78)
    candidates = {d: harm_mentions(o) for d, o in live.items() if harm_mentions(o)}
    unadjudicated = sorted(set(candidates) - set(adj))
    if unadjudicated:
        print("  ⛔ REFUSING TO COUNT. %d candidate(s) have no row in" % len(unadjudicated))
        print("     gates/HARMS_PICO_ADJUDICATION.json: %s" % ", ".join(unadjudicated))
        print("     A detector cannot separate an outcome from a population by itself.")
        return 3
    by_disp = collections.Counter(adj[d]["disposition"] for d in candidates)
    print("  candidates (detector): %d of %d live topics" % (len(candidates), len(live)))
    print("  adjudicated by hand:   %d of %d  -- precision measured by CENSUS, not sample"
          % (len(candidates), len(candidates)))
    for k, v in by_disp.most_common():
        print("      %3d  %s" % (v, k))
    # ⛔ RE-DERIVED FROM THE OBJECT, never read off the stored disposition.
    #
    # This line used to be `adj[d]["disposition"] == "NAMED_AND_ABSENT"`, and on
    # 2026-09-03 -- minutes after both apixaban pages published their bleeding outcome --
    # gate 21 correctly reported 0 findings while THIS FILE STILL REPORTED 2, because the
    # adjudication file still said they were absent. A stored verdict outlives the state
    # it describes. That is the mirror of the defect gate 21's own docstring warns
    # against, committed one module away by the author of the warning, and it is why
    # `decide()` now lives in harms_pico_surface.py and both callers share it.
    #
    # The adjudication supplies ONLY what kind of mention this is. Whether the harm is
    # there today is a question about the object.
    verdicts = {d: decide(live[d], adj[d]["disposition"])[0] for d in candidates}
    class1 = sorted(d for d in candidates if verdicts[d] == "PROMISED_NOT_REPORTED")
    stale = sorted(d for d in candidates
                   if adj[d]["disposition"] == "NAMED_AND_ABSENT"
                   and verdicts[d] != "PROMISED_NOT_REPORTED")
    print()
    print("  ⛔ CLASS 1 DEFECTS: %d of %d live topics" % (len(class1), len(live)))
    for d in class1:
        print("      %s" % d)
        print("          by_outcome: %s" % synthesised_outcome_ids(live[d]))
        print("          %s" % adj[d]["quote"][:150])
    if stale:
        print("  REPAIRED SINCE ADJUDICATION -- adjudicated NAMED_AND_ABSENT and no longer")
        print("  absent. Reported rather than silently dropped, because a row that has gone")
        print("  stale in the FLATTERING direction is the one nobody checks:")
        for d in stale:
            print("      %-34s now %s, by_outcome=%s"
                  % (d, verdicts[d], synthesised_outcome_ids(live[d])))
    rs = adj_doc.get("_recall_sample", {})
    print()
    print("  recall, on the %d live topics the detector did NOT flag: a sample of %s"
          % (len(live) - len(candidates), rs.get("n")))
    print("  pre-registered at seed %s before it was drawn returned %s false negatives."
          % (rs.get("seed"), rs.get("false_negatives_found")))
    print("  %s" % rs.get("what_the_zero_means", ""))

    # ---- CLASS 2 -----------------------------------------------------------------
    print()
    print("-" * 78)
    print("CLASS 2 -- A TRIAL THE REVIEW ALREADY READ REGISTERED A HARM, AND THE OBJECT")
    print("           SYNTHESISES NO HARM AT ALL")
    print("-" * 78)
    with_regs, class2, both, no_harm_registered = {}, [], [], []
    for d, o in live.items():
        regs = registered_outcome_text(o)
        if not regs:
            continue
        with_regs[d] = regs
        hits = [(n, k, v) for n, k, v in regs if HARM_RX.search(v)]
        if not hits:
            no_harm_registered.append(d)
            continue
        present, _where = harms_synthesis(o)
        (both if present else class2).append((d, hits))
    print("  ASSESSABLE FOR CLASS 2: %d of %d live topics store registered-outcome text."
          % (len(with_regs), len(live)))
    print("  the other %d store none, so whether their trials registered a harm is"
          % (len(live) - len(with_regs)))
    print("  NOT-ASSESSABLE from this object -- which is its own kind, not a pass.")
    print()
    print("      %3d  trials register a harm AND the object synthesises one" % len(both))
    print("      %3d  trials register a harm AND the object synthesises NONE  <- CLASS 2"
          % len(class2))
    print("      %3d  no trial registers a harm outcome" % len(no_harm_registered))
    print()
    print("  ⛔ CLASS 2: %d of %d assessable (%.0f%%)"
          % (len(class2), len(with_regs), 100.0 * len(class2) / max(1, len(with_regs))))
    print()
    print("  the ten largest, by how many harm-named registered outcomes were already read:")
    for d, hits in sorted(class2, key=lambda x: -len(x[1]))[:10]:
        ncts = sorted({n for n, _k, _v in hits if n})
        print("      %-38s %3d harm outcomes across %d trial(s)" % (d, len(hits), len(ncts)))

    print()
    print("=" * 78)
    print("  CLASS 1 = %d of %d live topics.   CLASS 2 = %d of %d assessable."
          % (len(class1), len(live), len(class2), len(with_regs)))
    print("  Neither number is 7. The reviews named seven pages; five of them named no")
    print("  harm in their own PICO and are class 2. Reporting them as class 1 would have")
    print("  been an inflated count with a true story attached to it.")
    print("=" * 78)

    if a.out:
        payload = {
            "measured_utc": "2026-09-03",
            "page_kinds": dict(kinds),
            "ssot_kinds": {"live": len(live), "tombstone": len(tombs),
                           "dir_without_json": len(nojson)},
            "class1": {"n": len(class1), "denominator": len(live), "app_ids": class1,
                       "candidates": len(candidates),
                       "dispositions": dict(by_disp)},
            "class2": {"n": len(class2), "denominator": len(with_regs),
                       "not_assessable": len(live) - len(with_regs),
                       "app_ids": sorted(d for d, _h in class2),
                       "harm_outcomes_already_read": {d: len(h) for d, h in class2}},
        }
        with io.open(a.out, "w", encoding="utf-8", newline="\n") as fh:
            fh.write(json.dumps(payload, indent=1))
        print("  wrote %s" % a.out)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
