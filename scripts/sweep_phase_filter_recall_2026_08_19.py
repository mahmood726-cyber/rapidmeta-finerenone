"""CORPUS SWEEP: what did the phase filter cost, per topic, measured against each topic's own
included set.

THE RULE, STATED GENERALLY BECAUSE IT IS NOT A PROPERTY OF ONE TOPIC:

    NA IS NOT A PHASE. A filter that ENUMERATES phases silently drops every registrant who
    declined to declare one.

Found on `ablation-af-medical-therapy`, where `phase=[PHASE3,PHASE4]` cost CABANA (n=2204) and
RAFT-AF -- both registered `phases: ["NA"]` -- reducing recall to 1 of 3. It is the fourth
distinct shape of one defect, and every one of the four runs in the WITHHOLDING direction:

    sglt2-hf      lost DELIVER                to a CONDITION term one word too narrow
    iv-iron-hf    lost AFFIRM-AHF, HEART-FID  to a CONDITION term one word too narrow
    apixaban-vte  lost NCT02366871            to phase=[PHASE3,PHASE4] on a PHASE2 trial
    ablation      lost CABANA and RAFT-AF     to the same filter on `phases: ["NA"]`

WHAT THIS MEASURES, per topic carrying a structured executed query:

    recall WITH the filter as executed   vs   recall WITHOUT it, terms otherwise identical

Only the phase clause is removed. Changing anything else would make the delta unattributable,
which is the same discipline the alirocumab re-pool used when it held the estimator constant.

THE DENOMINATOR IS STATED FIRST, because it is the largest fact here. 135 topic objects exist
and only a handful carry a structured executed query at all. A sweep over those few is not a
statement about the corpus -- the corpus-scale finding is how many topics have NO executed
search to sweep, and that is printed rather than left as the absence it is.
"""
import io
import json
import os
import re
import sys
import urllib.parse
import urllib.request

REPO = "F:/rapidmeta-ssot-shell"
sys.path.insert(0, REPO + "/ssot")
sys.path.insert(0, REPO + "/scripts")
os.environ.setdefault(
    "RM_CTGOV_CACHE",
    "F:/claude-temp/claude/F--rapidmeta-ssot-shell/"
    "eb4d84e5-8a24-4c3b-afe2-34bd91c20bc7/scratchpad/.ctgov-raw-cache")

import ctgov_transport as X                  # noqa: E402

API = "https://clinicaltrials.gov/api/v2/studies"
PHASE_CLAUSE = re.compile(r"\s*AND\s*AREA\[Phase\]\([^)]*\)|\s*AND\s*AREA\[Phase\][A-Z0-9]+"
                          r"|AREA\[Phase\]\([^)]*\)\s*AND\s*|AREA\[Phase\][A-Z0-9]+\s*AND\s*")


def raw_search(expr, page_size=1000):
    ids, token, pages, total = [], None, 0, None
    while True:
        params = dict(expr)
        params["fields"] = "NCTId"
        params["pageSize"] = str(page_size)
        params["countTotal"] = "true"
        if token:
            params["pageToken"] = token
        url = "%s?%s" % (API, urllib.parse.urlencode(params))
        try:
            with urllib.request.urlopen(url, timeout=90) as resp:
                if resp.status != 200:
                    return X.UNREACHABLE, ids, "HTTP %d" % resp.status
                payload = json.loads(resp.read().decode("utf-8"))
        except Exception as exc:                       # noqa: BLE001
            return X.UNREACHABLE, ids, "%s: %s" % (type(exc).__name__, exc)
        for s in payload.get("studies") or []:
            nct = (((s.get("protocolSection") or {}).get("identificationModule")
                    or {}).get("nctId"))
            if nct:
                ids.append(nct)
        pages += 1
        token = payload.get("nextPageToken")
        if pages == 1:                                  # totalCount is on the FIRST page only
            total = payload.get("totalCount")
        if not token:
            return X.OK, ids, "%d ids / %d page(s) / totalCount=%s" % (len(ids), pages, total)
        if pages > 30:
            return X.MALFORMED, ids, "pagination did not terminate"


def included_ncts(topic):
    p = os.path.join(REPO, "ssot", topic, topic + ".json")
    if not os.path.exists(p):
        return None
    obj = json.load(io.open(p, encoding="utf-8"))
    out = []
    for t in ((obj.get("inputs") or {}).get("trials") or []):
        for key in ("nct", "nct_id", "registration", "registration_id", "id"):
            v = t.get(key)
            if isinstance(v, str) and v.upper().startswith("NCT"):
                out.append(v)
                break
    return sorted(set(out))


def phases_of(ncts):
    """What each trial actually declares -- so a miss is explained, not just counted."""
    out = {}
    for n in ncts:
        st, study, _d = X.fetch_raw(n)
        if st != X.OK:
            out[n] = "UNREACHABLE"
            continue
        dm = (X.require_raw_v2(study, n)["protocolSection"].get("designModule") or {})
        out[n] = ",".join(dm.get("phases") or []) or "(none declared)"
    return out




def load_specs():
    """Read the two structured registries without executing their side effects.

    `ssot/batch1_cascade.py` RUNS A FULL SEARCH ON IMPORT, so it cannot be imported here --
    its EXECUTED dict is extracted by parsing the module instead. That is stated because a
    module whose constants can only be reached by running it is a design this file works
    around rather than endorses.
    """
    import ast
    specs = {}
    src = io.open(os.path.join(REPO, "ssot", "batch1_cascade.py"), encoding="utf-8").read()
    tree = ast.parse(src)
    for node in tree.body:
        if isinstance(node, ast.Assign) and getattr(node.targets[0], "id", "") == "EXECUTED":
            for k, v in zip(node.value.keys, node.value.values):
                d = ast.literal_eval(v)
                specs[ast.literal_eval(k)] = {"raw_expr": d["raw_expr"],
                                              "source": "ssot/batch1_cascade.py EXECUTED"}
    import regate_cascade_2026_08_19 as R
    for topic, spec in R.TOPICS.items():
        specs[topic] = {"raw_expr": spec["raw_expr"],
                        "source": "scripts/regate_cascade_2026_08_19.py TOPICS"}
    return specs


def main():
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

    ssot = os.path.join(REPO, "ssot")
    all_topics = [d for d in sorted(os.listdir(ssot))
                  if os.path.exists(os.path.join(ssot, d, d + ".json"))]
    specs = load_specs()
    print("THE DENOMINATOR FIRST")
    print("   topic objects in the corpus                    %4d" % len(all_topics))
    print("   with a STRUCTURED executed query to sweep      %4d" % len(specs))
    print("   with NO executed query at all                  %4d   <- not swept, and not "
          "clean:\n%s" % (len(all_topics) - len(specs),
                          " " * 54 + "unmeasured, which is the corpus-scale finding"))
    print()

    rows = []
    for topic in sorted(specs):
        expr = dict(specs[topic]["raw_expr"])
        adv = expr.get("filter.advanced", "")
        if "AREA[Phase]" not in adv:
            rows.append({"topic": topic, "state": "NO_PHASE_FILTER",
                         "note": "the executed query carries no phase clause; nothing to "
                                 "measure and nothing lost to one"})
            continue
        inc = included_ncts(topic)
        if not inc:
            rows.append({"topic": topic, "state": "NOT_ASSESSABLE",
                         "note": "no included set on the object, so recall has no "
                                 "denominator. NOT a pass."})
            continue

        st_w, ids_w, det_w = raw_search(expr)
        stripped = PHASE_CLAUSE.sub("", adv).strip()
        expr2 = dict(expr)
        expr2["filter.advanced"] = stripped
        st_o, ids_o, det_o = raw_search(expr2)
        if st_w != X.OK or st_o != X.OK:
            rows.append({"topic": topic, "state": "NOT_ASSESSABLE",
                         "note": "a search did not complete (%s / %s)" % (det_w, det_o)})
            continue
        ids_w, ids_o = set(ids_w), set(ids_o)
        miss_w = [n for n in inc if n not in ids_w]
        miss_o = [n for n in inc if n not in ids_o]
        recovered = [n for n in miss_w if n in ids_o]
        rows.append({
            "topic": topic, "state": "MEASURED",
            "advanced_with": adv, "advanced_without": stripped,
            "k0_with": len(ids_w), "k0_without": len(ids_o),
            "included": len(inc),
            "recall_with": "%d/%d" % (len(inc) - len(miss_w), len(inc)),
            "recall_without": "%d/%d" % (len(inc) - len(miss_o), len(inc)),
            "lost_to_the_phase_filter": recovered,
            "phases_of_the_lost": phases_of(recovered) if recovered else {},
            "still_missing_without_it": [n for n in miss_o],
        })

    print("%-46s %8s %8s %9s %9s  lost to the filter"
          % ("topic", "k0 with", "without", "recall w", "recall w/o"))
    total_lost = 0
    for r in rows:
        if r["state"] != "MEASURED":
            print("%-46s %s -- %s" % (r["topic"], r["state"], r["note"]))
            continue
        total_lost += len(r["lost_to_the_phase_filter"])
        print("%-46s %8d %8d %9s %9s  %s"
              % (r["topic"], r["k0_with"], r["k0_without"], r["recall_with"],
                 r["recall_without"],
                 ", ".join("%s [%s]" % (n, r["phases_of_the_lost"].get(n, "?"))
                           for n in r["lost_to_the_phase_filter"]) or "-"))
        if r["still_missing_without_it"]:
            print("%-46s   still missing WITHOUT the filter: %s  <- a DIFFERENT recall "
                  "defect, not this one" % ("", r["still_missing_without_it"]))

    print()
    print("INCLUDED TRIALS LOST TO A PHASE FILTER, ACROSS THE SWEPT TOPICS: %d" % total_lost)
    print("Every one is a trial the review INCLUDES that its own executed search did not "
          "surface --\nthe withholding direction, and invisible in the object because a "
          "trial that was never\nsurfaced leaves no trace in any count.")

    dest = os.path.join(REPO, "evidence", "2026-08-19-batch1", "phase_filter_recall_sweep.json")
    with io.open(dest, "w", encoding="utf-8") as fh:
        fh.write(json.dumps({"corpus_topics": len(all_topics),
                             "structured_queries": len(specs),
                             "unswept_no_executed_query": len(all_topics) - len(specs),
                             "rows": rows}, indent=1))
    print("\nwrote %s" % dest)
    return 0


if __name__ == "__main__":
    sys.exit(main())
