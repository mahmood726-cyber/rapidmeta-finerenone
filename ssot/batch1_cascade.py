"""Batch 1 arm-role / comparator cascade, k reported at EVERY stage.

TWO SEARCH INSTRUMENTS ARE RECORDED, DELIBERATELY, AND THEIR TOTALS ARE COMPARED.

  * MCP `search_trials` -- ran Claude-side. Its query and its total are archived verbatim
    below in EXECUTED. This is the executed systematic search.
  * Raw CTGov v2 `/studies?query.*` -- run here, because the MCP payload is FLATTENED and
    carries no arm types (see ssot/ctgov_transport.py). It is the only way to get the role
    payload, and it also yields the id list mechanically rather than by transcription.

The two totals are reported SIDE BY SIDE and never reconciled silently. MCP applies its own
synonym expansion; the raw API does not. A divergence is a fact about the instruments and is
printed as one. Collapsing them to a single number is the "one k" error this cascade exists
to avoid.

STAGES, and every one prints its own k:
  k0 surfaced        -- records the search returned
  k1 interventional  -- study type
  k2 role located    -- topic drug found in an eligible identity field  (locate() != NOT_ASSESSABLE)
  k3 experimental    -- topic drug in an EXPERIMENTAL arm
  k4 comparator      -- topic drug is the CONTROL (the OLMESARTAN_HTN class)
  k5 background      -- coadministered, not the contrast
  kNA not_assessable -- COULD NOT CLASSIFY. Never merged into "excluded".
"""
import json
import os
import sys
import time
import urllib.parse
import urllib.request

sys.path.insert(0, "F:/rapidmeta-ssot-shell/ssot")
os.environ.setdefault("RM_CTGOV_CACHE",
                      "F:/claude-temp/claude/F--rapidmeta-ssot-shell/"
                      "eb4d84e5-8a24-4c3b-afe2-34bd91c20bc7/scratchpad/.ctgov-raw-cache")

import ctgov_transport as X
import topic_identity as T

SEARCH_DATE = "2026-08-18"

# ---------------------------------------------------------------------------
# THE EXECUTED SEARCHES, VERBATIM. Copied from the MCP calls actually made.
# `mcp_total` is what the tool reported; it is evidence, not a target.
# ---------------------------------------------------------------------------
EXECUTED = {
    "ablation-af-review": {
        "topic_key": "catheter ablation",
        "mcp_tool": "mcp__plugin_bio-research_c-trials__search_trials",
        "mcp_params": {"condition": "atrial fibrillation",
                       "intervention": "catheter ablation OR pulmonary vein isolation OR cryoballoon ablation",
                       "study_type": "INTERVENTIONAL", "phase": ["PHASE3", "PHASE4"],
                       "count_total": True, "page_size": 100},
        "mcp_total": 143, "mcp_returned": 100,
        "raw_expr": {"query.cond": "atrial fibrillation",
                     "query.intr": "catheter ablation OR pulmonary vein isolation OR cryoballoon ablation",
                     "filter.advanced": "AREA[StudyType]INTERVENTIONAL AND AREA[Phase](PHASE3 OR PHASE4)"},
    },
    "alirocumab-lipid": {
        "topic_key": "alirocumab",
        "mcp_tool": "mcp__plugin_bio-research_c-trials__search_trials",
        "mcp_params": {"condition": "hypercholesterolemia OR dyslipidemia",
                       "intervention": "alirocumab", "study_type": "INTERVENTIONAL",
                       "phase": ["PHASE3", "PHASE4"], "count_total": True, "page_size": 100},
        "mcp_total": 39, "mcp_returned": 39,
        "raw_expr": {"query.cond": "hypercholesterolemia OR dyslipidemia",
                     "query.intr": "alirocumab",
                     "filter.advanced": "AREA[StudyType]INTERVENTIONAL AND AREA[Phase](PHASE3 OR PHASE4)"},
    },
    "apixaban-vte": {
        "topic_key": "apixaban",
        "mcp_tool": "mcp__plugin_bio-research_c-trials__search_trials",
        "mcp_params": {"condition": "venous thromboembolism", "intervention": "apixaban",
                       "study_type": "INTERVENTIONAL", "phase": ["PHASE3", "PHASE4"],
                       "count_total": True, "page_size": 100},
        "mcp_total": 36, "mcp_returned": 36,
        "raw_expr": {"query.cond": "venous thromboembolism", "query.intr": "apixaban",
                     "filter.advanced": "AREA[StudyType]INTERVENTIONAL AND AREA[Phase](PHASE3 OR PHASE4)"},
    },
    "attr-cm-review": {
        "topic_key": "tafamidis OR acoramidis",
        "mcp_tool": "mcp__plugin_bio-research_c-trials__search_trials",
        "mcp_params": {"condition": "transthyretin amyloid cardiomyopathy",
                       "intervention": "tafamidis OR acoramidis",
                       "study_type": "INTERVENTIONAL", "count_total": True, "page_size": 100},
        "mcp_total": 20, "mcp_returned": 20,
        # The MCP call for this topic carried NO phase filter, so the raw query carries none
        # either. Adding one here would make the two queries different questions again --
        # in the opposite direction from the bug this block is fixing.
        "raw_expr": {"query.cond": "transthyretin amyloid cardiomyopathy",
                     "query.intr": "tafamidis OR acoramidis",
                     "filter.advanced": "AREA[StudyType]INTERVENTIONAL"},
    },
    "azilsartan-chlorthalidone-vs-olmesartan-hctz": {
        "topic_key": "azilsartan",
        "mcp_tool": "mcp__plugin_bio-research_c-trials__search_trials",
        "mcp_params": {"condition": "hypertension",
                       "intervention": "azilsartan OR azilsartan medoxomil",
                       "study_type": "INTERVENTIONAL", "phase": ["PHASE3", "PHASE4"],
                       "count_total": True, "page_size": 60},
        "mcp_total": 36, "mcp_returned": 36,
        "raw_expr": {"query.cond": "hypertension",
                     "query.intr": "azilsartan OR azilsartan medoxomil",
                     "filter.advanced": "AREA[StudyType]INTERVENTIONAL AND AREA[Phase](PHASE3 OR PHASE4)"},
    },
    "bempedoic-acid-review": {
        "topic_key": "bempedoic acid",
        "mcp_tool": "mcp__plugin_bio-research_c-trials__search_trials",
        "mcp_params": {"condition": "hypercholesterolemia OR dyslipidemia OR cardiovascular disease",
                       "intervention": "bempedoic acid", "study_type": "INTERVENTIONAL",
                       "phase": ["PHASE3", "PHASE4"], "count_total": True, "page_size": 60},
        "mcp_total": 21, "mcp_returned": 21,
        "raw_expr": {"query.cond": "hypercholesterolemia OR dyslipidemia OR cardiovascular disease",
                     "query.intr": "bempedoic acid",
                     "filter.advanced": "AREA[StudyType]INTERVENTIONAL AND AREA[Phase](PHASE3 OR PHASE4)"},
    },
    "bococizumab-lipid-review": {
        "topic_key": "bococizumab",
        "mcp_tool": "mcp__plugin_bio-research_c-trials__search_trials",
        "mcp_params": {"condition": "hypercholesterolemia OR dyslipidemia",
                       "intervention": "bococizumab", "study_type": "INTERVENTIONAL",
                       "count_total": True, "page_size": 60},
        "mcp_total": 21, "mcp_returned": 21,
        # As with attr-cm-review: the MCP call carried no phase filter, so neither does this.
        "raw_expr": {"query.cond": "hypercholesterolemia OR dyslipidemia",
                     "query.intr": "bococizumab",
                     "filter.advanced": "AREA[StudyType]INTERVENTIONAL"},
    },
    "bosentan-pah": {
        "topic_key": "bosentan",
        "mcp_tool": "mcp__plugin_bio-research_c-trials__search_trials",
        "mcp_params": {"condition": "pulmonary arterial hypertension", "intervention": "bosentan",
                       "study_type": "INTERVENTIONAL", "phase": ["PHASE3", "PHASE4"],
                       "count_total": True, "page_size": 60},
        "mcp_total": 42, "mcp_returned": 42,
        "raw_expr": {"query.cond": "pulmonary arterial hypertension", "query.intr": "bosentan",
                     "filter.advanced": "AREA[StudyType]INTERVENTIONAL AND AREA[Phase](PHASE3 OR PHASE4)"},
    },
}

SEARCH_API = "https://clinicaltrials.gov/api/v2/studies"


def raw_search(expr, page_size=1000):
    """Return (state, [nct_ids], detail). Paginates. Never returns a partial list as complete."""
    ids, token, pages = [], None, 0
    while True:
        params = dict(expr)
        params["fields"] = "NCTId"
        params["pageSize"] = str(page_size)
        params["countTotal"] = "true"
        if token:
            params["pageToken"] = token
        url = f"{SEARCH_API}?{urllib.parse.urlencode(params)}"
        try:
            with urllib.request.urlopen(url, timeout=60) as resp:
                if resp.status != 200:
                    return X.UNREACHABLE, ids, f"HTTP {resp.status} on page {pages + 1}"
                payload = json.loads(resp.read().decode("utf-8"))
        except Exception as exc:                      # noqa: BLE001 - transport, reported
            return X.UNREACHABLE, ids, f"{type(exc).__name__}: {exc} on page {pages + 1}"
        for s in payload.get("studies") or []:
            nct = (((s.get("protocolSection") or {}).get("identificationModule")
                    or {}).get("nctId"))
            if nct:
                ids.append(nct)
        pages += 1
        token = payload.get("nextPageToken")
        total = payload.get("totalCount")
        if not token:
            return X.OK, ids, f"{len(ids)} ids over {pages} page(s), totalCount={total}"
        if pages > 20:
            return X.MALFORMED, ids, "pagination did not terminate in 20 pages"


results = {}
for topic_dir, spec in EXECUTED.items():
    key = spec["topic_key"]
    syns = T.synonyms_for(key)                 # KeyError here is deliberate and correct
    state, ids, detail = raw_search(spec["raw_expr"])
    ids = sorted(set(ids))

    rec = {
        "topic_dir": topic_dir, "topic_key": key, "search_date": SEARCH_DATE,
        "mcp_tool": spec["mcp_tool"], "mcp_params": spec["mcp_params"],
        "mcp_total": spec["mcp_total"], "mcp_returned": spec["mcp_returned"],
        "raw_expr": spec["raw_expr"], "raw_state": state, "raw_detail": detail,
        "k0_surfaced_raw": len(ids), "ids": ids,
        "roles": {}, "fetch_failures": {},
    }
    if state != X.OK:
        rec["stage_note"] = ("raw search did not complete; downstream k are FLOORS over a "
                             "partial id list and must not be read as counts")

    tally = {T.EXPERIMENTAL: [], T.COMPARATOR: [], T.BACKGROUND: [],
             T.NOT_ASSESSABLE: [], "UNREACHABLE": []}
    for nct in ids:
        st, study, det = X.fetch_raw(nct)
        if st != X.OK:
            rec["fetch_failures"][nct] = f"{st}: {det}"
            tally["UNREACHABLE"].append(nct)      # NOT not_assessable: we never read it
            continue
        role, ev = T.locate(X.require_raw_v2(study, nct), syns)
        rec["roles"][nct] = {"role": role, "evidence": ev}
        tally[role].append(nct)
        time.sleep(0.03)

    rec["k2_role_located"] = (len(tally[T.EXPERIMENTAL]) + len(tally[T.COMPARATOR])
                              + len(tally[T.BACKGROUND]))
    rec["k3_experimental"] = len(tally[T.EXPERIMENTAL])
    rec["k4_comparator"] = len(tally[T.COMPARATOR])
    rec["k5_background"] = len(tally[T.BACKGROUND])
    rec["kNA_not_assessable"] = len(tally[T.NOT_ASSESSABLE])
    rec["kUNREACHABLE"] = len(tally["UNREACHABLE"])
    rec["experimental_ids"] = tally[T.EXPERIMENTAL]
    rec["comparator_ids"] = tally[T.COMPARATOR]
    rec["not_assessable_ids"] = tally[T.NOT_ASSESSABLE]
    results[topic_dir] = rec

    print(f"--- {topic_dir}")
    print(f"    MCP total {spec['mcp_total']:>4}  |  raw total {len(ids):>4}  "
          f"({'AGREE' if spec['mcp_total'] == len(ids) else 'DIVERGE -- reported, not reconciled'})")
    print(f"    raw search: {state} -- {detail}")
    print(f"    k0 surfaced        {len(ids):>4}")
    print(f"    k2 role located    {rec['k2_role_located']:>4}")
    print(f"    k3 EXPERIMENTAL    {rec['k3_experimental']:>4}")
    print(f"    k4 COMPARATOR      {rec['k4_comparator']:>4}   <- topic drug is the CONTROL")
    print(f"    k5 background      {rec['k5_background']:>4}")
    print(f"    kNA not assessable {rec['kNA_not_assessable']:>4}   <- COULD NOT CLASSIFY, not excluded")
    print(f"    kUNREACHABLE       {rec['kUNREACHABLE']:>4}   <- never read; not a verdict")

out = ("F:/claude-temp/claude/F--rapidmeta-ssot-shell/"
       "eb4d84e5-8a24-4c3b-afe2-34bd91c20bc7/scratchpad/batch1_cascade.json")
with open(out, "w", encoding="utf-8") as fh:
    json.dump(results, fh, indent=1)

print()
print("BATCH TOTALS (sum of per-topic stages; the per-topic numbers are the result)")
for stage in ("k0_surfaced_raw", "k2_role_located", "k3_experimental", "k4_comparator",
              "k5_background", "kNA_not_assessable", "kUNREACHABLE"):
    print(f"  {stage:<22} {sum(r[stage] for r in results.values()):>5}")
print(f"\nwrote {out}")
