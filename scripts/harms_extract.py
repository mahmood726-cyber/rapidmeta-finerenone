r"""Extract per-arm harm counts, with the window and the population on every row.

WHAT THIS IS FOR. Two topics name a harm outcome in their own PICO and publish none
(gate 21). This is the path that gets the numbers, and it is written so that the numbers
it produces can be checked field by field rather than believed.

⛔ IT CONSUMES A SOURCE HIERARCHY. IT DOES NOT DEFINE ONE.
    A sibling lane owns the publication-first hierarchy. This module reads whatever the
    OBJECT declares at `sources.*.layer_rank` and does two things with it: records which
    layer each row came from, and NAMES THE LAYERS IT DID NOT CONSULT. When an object
    declares no hierarchy -- 117 of 141 live topics declare none -- it says so, in the
    row, rather than letting silence read as "the best source was used".

    That disclosure is not bureaucracy. The dapivirine page reports registry SAE counts
    of 116/1313 vs 130/1316 where its own publication reports 52 vs 48. THE REGISTRY AND
    THE PAPER DISAGREE, AND A ROW THAT DOES NOT SAY WHICH ONE IT IS CANNOT BE CHECKED.

⛔ EVERY ROW CARRIES ITS ASCERTAINMENT WINDOW AND ITS POPULATION, and a row whose
   numerator and denominator do not come from the same population FAILS.
    "Participants experiencing any SAE" and "SAE events" are different quantities. A
    registry safety population and a publication's are different denominators. That rule
    is not theoretical here: it produced a wrong headline number on ceftaroline --
    235/315, where the publication says 235/289 -- by pairing a numerator with the nearest
    denominator to hand.
    In ADOPT the two populations differ by nine hundred people: major bleeding is posted
    on 3,184 As-Treated participants and the VTE outcome on 2,304 evaluable ones. Pairing
    a bleeding numerator with a VTE denominator would be silently wrong by 28%.

⛔ THE ENDPOINT LABEL IS READ, NEVER INFERRED FROM POSITION.
    ClinicalTrials.gov returns a four-row bleeding table as `classes[]`, and the label
    -- "Major bleeding", "CRNM", "Major or CRNM", "Any bleeding" -- lives at
    `classes[].title`. `categories[].title` is None for all four. Reading the first value
    as "major bleeding" because it comes first WOULD have been correct here and is still
    forbidden: it is the right-number-wrong-endpoint class, and it is invisible when it
    is wrong. A class with no title is REFUSED, not guessed.

⛔ A PERCENTAGE IS NOT A COUNT.
    Every bleeding row in these four trials is posted as an event rate, not a count. A
    count reconstructed from a rounded percentage is a DERIVATION, and it is admissible
    only when exactly one integer rounds to the posted value at the posted precision.
    ADOPT: 0.47% of 3,184 admits only 15, and 0.19% of 3,217 admits only 6 -- so those
    two are exact. Where more than one integer qualifies the row is emitted with
    `events: null` and `events_refused_because` naming the candidates. It is never
    rounded to the nearest one.

Usage:
    python scripts/harms_extract.py --nct NCT00457002 [--nct ...] [--json OUT]
    python scripts/harms_extract.py --topic apixaban-vte-prophylaxis [--json OUT]

Exit 0 when every requested trial produced at least one usable row, 1 when any did not.
A trial that posts no results is NOT a failure of this script and is reported as
NO_POSTED_RESULTS, which is its own state and is never folded into "no harms found".
"""
from __future__ import annotations

import argparse
import io
import json
import os
import re
import sys
import time
import urllib.request

if __name__ == "__main__" and not os.environ.get("_GATE_WRAPPED"):
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(REPO, "scripts"))
from harms_pico_surface import HARM_RX                                      # noqa: E402

CACHE = os.path.join(REPO, "outputs", "harms_registry_cache")
API = "https://clinicaltrials.gov/api/v2/studies/%s"

# A percentage is admissible as a count only if exactly ONE integer rounds to it.
PCT_UNITS = re.compile(r"percent|percentage|rate.*%|%", re.I)


def declared_source_hierarchy(obj):
    """-> [(rank, layer_name, source_key)] sorted, or [] when the object declares none.

    READ FROM THE OBJECT. This module does not own the hierarchy and does not invent a
    default one: an object that declares no layers gets an empty list and a row that says
    so, which is a different statement from "the registry is the top layer".
    """
    src = obj.get("sources")
    if not isinstance(src, dict):
        return []
    out = []
    for key, v in src.items():
        if isinstance(v, dict) and ("layer_rank" in v or "layer" in v):
            out.append((v.get("layer_rank"), str(v.get("layer", "")), key))
    return sorted(out, key=lambda r: (r[0] is None, r[0]))


def fetch_study(nct, refresh=False):
    """-> (study_json, provenance). Cached, because a number that changes between two
    runs of the same command cannot be checked by anyone."""
    os.makedirs(CACHE, exist_ok=True)
    path = os.path.join(CACHE, nct + ".json")
    if os.path.exists(path) and not refresh:
        with io.open(path, encoding="utf-8") as fh:
            blob = json.load(fh)
        return blob["study"], blob["provenance"]
    raw = urllib.request.urlopen(API % nct, timeout=60).read()
    study = json.loads(raw.decode("utf-8"))
    provenance = {
        "source": "ClinicalTrials.gov API v2",
        "url": API % nct,
        "retrieved_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "bytes": len(raw),
    }
    with io.open(path, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(json.dumps({"provenance": provenance, "study": study}, indent=1))
    return study, provenance


def _counts_matching(pct_text, n):
    """Which integer counts round to this posted percentage at ITS OWN precision?

    The precision is read from the posted string -- "0.47" is two decimals, "5.3" is one
    -- because assuming two would admit counts the registry's own rounding excludes, and
    assuming more would admit none.
    """
    try:
        pct = float(pct_text)
    except (TypeError, ValueError):
        return None
    dp = len(pct_text.split(".")[1]) if "." in str(pct_text) else 0
    return [c for c in range(0, int(n) + 1) if round(100.0 * c / n, dp) == round(pct, dp)]


def harm_rows(nct, study, hierarchy):
    """-> (rows, states). Every per-arm harm row this registration posts, with the window
    and the population attached to each."""
    rows, states = [], []
    results = study.get("resultsSection") or {}
    if not results:
        return rows, ["NO_POSTED_RESULTS"]
    om = (results.get("outcomeMeasuresModule") or {}).get("outcomeMeasures") or []
    for o in om:
        title = str(o.get("title") or "")
        if not HARM_RX.search(title):
            continue
        groups = {g.get("id"): g.get("title") for g in (o.get("groups") or [])}
        denoms = {c.get("groupId"): c.get("value")
                  for cl in (o.get("denoms") or []) for c in (cl.get("counts") or [])}
        window = o.get("timeFrame")
        population = o.get("populationDescription")
        unit = str(o.get("unitOfMeasure") or "")
        is_pct = bool(PCT_UNITS.search(unit))
        for cls in (o.get("classes") or []):
            label = cls.get("title")
            multi = len(o.get("classes") or []) > 1
            if multi and not label:
                # ⛔ REFUSED, NOT GUESSED. A multi-row table whose row labels are absent
                # cannot be read positionally without inventing the endpoint.
                states.append("REFUSED_UNLABELLED_CLASS: %s" % title[:70])
                continue
            for cat in (cls.get("categories") or []):
                for m in (cat.get("measurements") or []):
                    gid = m.get("groupId")
                    arm = groups.get(gid)
                    n = denoms.get(gid)
                    if not arm or not n:
                        # A numerator with no denominator, or a value with no named arm,
                        # is not a row. It is dropped BY NAME, never silently.
                        states.append("REFUSED_NO_ARM_OR_DENOMINATOR: %s/%s" % (title[:50], gid))
                        continue
                    row = {
                        "nct": nct,
                        "endpoint_label": label or title,
                        "endpoint_label_read_from": ("outcomeMeasures[].classes[].title"
                                                     if label else
                                                     "outcomeMeasures[].title (single-class)"),
                        "outcome_title": title,
                        "outcome_rank": o.get("type"),
                        # ⛔ THE TWO FIELDS THE CEFTAROLINE ERROR WOULD HAVE NEEDED
                        "ascertainment_window": window,
                        "population": population,
                        "arm": arm,
                        "arm_keyed_from": "outcomeMeasures[].groups[].title, NOT the "
                                          "group index -- OG/EG ordering is not stable "
                                          "across modules within one registration",
                        "denominator": int(n),
                        "denominator_from": "this outcome's OWN denoms block, so "
                                            "numerator and denominator are the same "
                                            "population by construction",
                        "posted_value": m.get("value"),
                        "posted_unit": unit,
                        "source_layer": "REGISTRY -- ClinicalTrials.gov posted results",
                        "layers_above_not_consulted": [
                            "%s (rank %s)" % (name, rank)
                            for rank, name, _k in hierarchy if rank is not None and rank < 5]
                        or ["THIS OBJECT DECLARES NO SOURCE HIERARCHY. The registry was "
                            "the sole source and the trial publications were NOT read. "
                            "Where the two disagree this row follows the registry, and "
                            "nothing here establishes which is right."],
                    }
                    if is_pct:
                        cands = _counts_matching(m.get("value"), int(n))
                        if cands and len(cands) == 1:
                            row["events"] = cands[0]
                            row["events_derivation"] = (
                                "DERIVED, not read. The registry posts %s%% on %d. "
                                "Exactly one integer rounds to that at the posted "
                                "precision, so the count is determined: %d."
                                % (m.get("value"), int(n), cands[0]))
                        else:
                            row["events"] = None
                            row["events_refused_because"] = (
                                "%s%% on %d admits %s integer count(s) %s. A count is "
                                "not rounded to the nearest candidate."
                                % (m.get("value"), int(n),
                                   len(cands) if cands is not None else "un-parseable",
                                   (cands or [])[:6]))
                    else:
                        try:
                            row["events"] = int(float(m.get("value")))
                            row["events_derivation"] = "READ as a participant count."
                        except (TypeError, ValueError):
                            row["events"] = None
                            row["events_refused_because"] = (
                                "value %r is not an integer count and the unit %r does "
                                "not say it is a percentage"
                                % (m.get("value"), unit))
                    rows.append(row)
    if not rows and not states:
        states.append("RESULTS_POSTED_BUT_NO_HARM_OUTCOME_MATCHED")
    return rows, states


def pair_arms(rows, endpoint_label, window=None):
    """-> [{endpoint, window, population, arms:[...]}] grouped so a 2x2 is only ever
    assembled from rows that share an endpoint, a window AND a population.

    THIS IS THE RULE, MADE MECHANICAL. Rows that differ in any of the three are never
    put in the same contrast, so a bleeding numerator cannot meet a VTE denominator.
    """
    buckets = {}
    for r in rows:
        if r["endpoint_label"] != endpoint_label:
            continue
        if window is not None and r["ascertainment_window"] != window:
            continue
        key = (r["nct"], r["endpoint_label"], r["ascertainment_window"], r["population"])
        buckets.setdefault(key, []).append(r)
    out = []
    for (nct, ep, win, pop), rs in sorted(buckets.items()):
        out.append({"nct": nct, "endpoint": ep, "ascertainment_window": win,
                    "population": pop,
                    "arms": [{"arm": r["arm"], "events": r["events"],
                              "n": r["denominator"], "posted": r["posted_value"],
                              "unit": r["posted_unit"]} for r in rs]})
    return out


def main(argv):
    ap = argparse.ArgumentParser()
    ap.add_argument("--nct", action="append", default=[])
    ap.add_argument("--topic")
    ap.add_argument("--endpoint", default=None,
                    help="only emit contrasts for this exact endpoint label")
    ap.add_argument("--json", dest="out")
    ap.add_argument("--refresh", action="store_true")
    a = ap.parse_args(argv)

    hierarchy, ncts = [], list(a.nct)
    if a.topic:
        p = os.path.join(REPO, "ssot", a.topic, a.topic + ".json")
        with io.open(p, encoding="utf-8") as fh:
            obj = json.load(fh)
        hierarchy = declared_source_hierarchy(obj)
        ncts += [t.get("nct") for t in ((obj.get("inputs") or {}).get("trials") or [])
                 if isinstance(t, dict) and t.get("nct")]
    ncts = [n for n in dict.fromkeys(ncts) if n]
    if not ncts:
        print("no NCTs given")
        return 1

    print("SOURCE HIERARCHY DECLARED BY THIS OBJECT: %s"
          % ("; ".join("rank %s = %s" % (r, n) for r, n, _k in hierarchy) or
             "NONE. The registry is the sole source and the publications were NOT read."))
    print()

    all_rows, report = [], {}
    for nct in ncts:
        try:
            study, prov = fetch_study(nct, a.refresh)
        except Exception as exc:                    # a fetch failure is not "no harms"
            report[nct] = {"state": "FETCH_FAILED", "detail": repr(exc)}
            print("  %-13s FETCH_FAILED %r" % (nct, exc))
            continue
        rows, states = harm_rows(nct, study, hierarchy)
        all_rows += rows
        report[nct] = {"state": "OK" if rows else (states[0] if states else "NO_ROWS"),
                       "rows": len(rows), "notes": states, "provenance": prov}
        print("  %-13s %-42s rows=%d %s"
              % (nct, report[nct]["state"], len(rows),
                 ("; ".join(states)[:60] if states else "")))

    labels = sorted({r["endpoint_label"] for r in all_rows})
    print()
    print("ENDPOINT LABELS FOUND, read from classes[].title and never from position:")
    for lab in labels:
        wins = sorted({r["ascertainment_window"] for r in all_rows
                       if r["endpoint_label"] == lab})
        print("    %-46s %d trial(s), %d distinct window(s)"
              % (lab[:46], len({r["nct"] for r in all_rows if r["endpoint_label"] == lab}),
                 len(wins)))

    contrasts = []
    for lab in ([a.endpoint] if a.endpoint else labels):
        contrasts += pair_arms(all_rows, lab)
    print()
    print("CONTRASTS -- each assembled ONLY from rows sharing endpoint + window + population:")
    for c in contrasts:
        arms = ", ".join("%s %s/%s" % (x["arm"][:22], x["events"], x["n"]) for x in c["arms"])
        print("    %-13s %-26s %s" % (c["nct"], c["endpoint"][:26], arms))
        print("        window: %s" % str(c["ascertainment_window"])[:96])
        print("        pop:    %s" % str(c["population"])[:96])

    if a.out:
        with io.open(a.out, "w", encoding="utf-8", newline="\n") as fh:
            fh.write(json.dumps({"topic": a.topic, "ncts": ncts,
                                 "declared_hierarchy": hierarchy,
                                 "per_trial": report, "rows": all_rows,
                                 "contrasts": contrasts}, indent=1))
        print("\n  wrote %s" % a.out)
    return 0 if all(v.get("rows") for v in report.values()) else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
