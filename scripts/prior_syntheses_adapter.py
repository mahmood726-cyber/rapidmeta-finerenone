# -*- coding: utf-8 -*-
"""Prior-syntheses adapter: find prior meta-analyses of a question and harvest their included
trial sets -- the source most likely to already hold the arm-level data we are missing.

Same five-field contract as the Europe PMC adapter, and the same four states. Two operations:

  SEARCH  -- (/search) prior meta-analyses of the question. Denominator = hitCount, funnel of
             per-record decisions with rule ids, known-positive control.
  HARVEST -- (/{source}/{id}/references) a chosen meta's reference list, mined to the trial
             registration ids it included. Each harvested trial is recorded at tier
             SYNTHESIS_REPORTED and ATTRIBUTED to the meta (its id) -- never as if we read the
             trial. A value from a prior meta is that review's extraction, a weaker claim than
             a registry posting; if it later disagrees with our own, the disagreement is the
             finding and is not reconciled silently.

FOUR STATES on both operations: NOT_RUN / RAN_ERROR (asked, unusable -- e.g. the /references
503 seen on 2026-09-06) / RAN_ZERO / RAN_RESULTS. A down endpoint is RAN_ERROR, never "the meta
had no references".

The known-positive control has been shown able to FAIL: a trial the meta did NOT include must
be absent from the harvest, checked alongside one it did include.

ARM-LEVEL CELLS: the reference harvest gives the trial SET. Pulling arm-level counts from the
meta's TABLE (e.g. "Burnett 2017, Table 2, row 8") is the next layer and needs the full text;
when built it must attribute every cell to its table and row, so inheriting the source's
extraction error stays detectable. Not done here; the harvest set is the first, deterministic
half the design calls the highest-value and cheapest.
"""
from __future__ import annotations
import io, sys, json, time, urllib.request, re
sys.path.insert(0, "scripts")
import europepmc_adapter as ep

REST = "https://www.ebi.ac.uk/europepmc/webservices/rest"
NOT_RUN, RAN_ERROR, RAN_ZERO, RAN_RESULTS = ep.NOT_RUN, ep.RAN_ERROR, ep.RAN_ZERO, ep.RAN_RESULTS


def _member(key, coll):
    return key in coll


def search_prior_metas(question_query, control_pmid=None):
    """Prior meta-analyses of the question. Uses the europepmc adapter's five-field discipline."""
    q = "(%s) AND (PUB_TYPE:\"Meta-Analysis\" OR PUB_TYPE:\"systematic review\")" % question_query
    return ep.run("prior_syntheses_search", q,
                  control={"pmid": control_pmid} if control_pmid else None)


def harvest_references(source, idv, include_control=None, exclude_control=None):
    """Mine a prior meta's reference list to the trial NCTs it included. Returns a record with
    state, denominator, per-reference NCTs (SYNTHESIS_REPORTED, attributed), and a falsifiable
    control. /references 503 -> RAN_ERROR, never RAN_ZERO."""
    url = "%s/%s/%s/references?format=json&pageSize=1000" % (REST, source, idv)
    state, http, detail = None, None, None
    data = None
    for attempt in range(4):
        try:
            with urllib.request.urlopen(urllib.request.Request(url, headers={"User-Agent": "harness/1.0"}), timeout=30) as r:
                http = r.getcode()
                data = json.loads(r.read().decode("utf-8", "replace"))
            break
        except urllib.error.HTTPError as e:
            http = e.code
            if e.code in (429, 500, 502, 503):
                time.sleep(3 * (attempt + 1)); detail = "HTTP %s" % e.code; continue
            state, detail = RAN_ERROR, "HTTP %s" % e.code; break
        except Exception as e:
            detail = "transport: %s" % (str(e)[:80]); time.sleep(3 * (attempt + 1))
    rec = {"source": "prior_syntheses", "operation": "harvest_references",
           "tool": url, "tier": "SYNTHESIS_REPORTED",
           "meta_source": source, "meta_id": idv, "executed_utc": ep._utc(), "http_status": http}
    if data is None:
        rec["state"] = RAN_ERROR
        rec["state_detail"] = detail or "unreachable"
        rec["why_no_denominator"] = ("/references did not return; RAN_ERROR is not 'the meta had "
                                     "no references'. Re-run when the endpoint recovers.")
        rec["harvested_trials"] = None
        return rec
    refl = (data.get("referenceList") or {}).get("reference", []) or []
    trials = []
    for i, r in enumerate(refl):
        ncts = sorted(set(re.findall(r"NCT\d{8}", json.dumps(r))))
        for n in ncts:
            trials.append({"nct": n, "tier": "SYNTHESIS_REPORTED",
                           "attribution": {"meta_id": idv, "reference_index": i + 1,
                                           "citation": (r.get("citationType"), r.get("id"), r.get("title", "")[:80])}})
    nct_set = {t["nct"] for t in trials}
    rec["state"] = RAN_RESULTS if trials else RAN_ZERO
    rec["denominator"] = {"references": len(refl), "references_with_nct": len({t["nct"] for t in trials})}
    rec["harvested_trials"] = trials
    if include_control or exclude_control:
        rec["control"] = {
            "include_known_positive": include_control,
            "include_found": (_member(include_control, nct_set) if include_control else None),
            "exclude_known_negative": exclude_control,
            "exclude_absent": (not _member(exclude_control, nct_set) if exclude_control else None),
        }
        inc_ok = (rec["control"]["include_found"] is not False)
        exc_ok = (rec["control"]["exclude_absent"] is not False)
        rec["control"]["verdict"] = ("PROVEN_FALSIFIABLE" if (inc_ok and exc_ok)
                                     else "CONTROL_FAILED -- included-trial missing or excluded-trial present")
    return rec


def run(out_dir=None):
    # GLP-1 CV question. NO OpenAccess restriction on the SEARCH: the landmark metas we most want
    # (Kristensen 2019, Navarese 2023) are isOpenAccess=N, so an OA filter would silently drop
    # exactly the targets. Positive control = Kristensen 2019 (PMID 31422062), a GLP-1 CV meta
    # that MUST be in this search; the trial LEADER (a non-meta) is the conceptual negative and
    # was shown absent from the meta-typed search on the prior run.
    smeta = search_prior_metas('(GLP-1 OR "glucagon-like peptide") AND cardiovascular',
                               control_pmid="31422062")
    result = {"executed_utc": ep._utc(), "search": {
        "state": smeta["state"], "denominator": smeta.get("denominator"),
        "query_as_executed": smeta["query_as_executed"], "control": smeta.get("control"),
        "control_is": "Kristensen 2019 (PMID 31422062), a GLP-1 CV meta that must be present"}}
    # harvest a meta that has a PMCID (required for /references)
    harvest = None
    if smeta["state"] == RAN_RESULTS:
        st, http, hit, recs, d = ep.fetch(smeta["query_as_executed"], page_size=25, max_pages=1)
        pick = next((r for r in recs if r.get("pmcid")), None)
        if pick:
            harvest = harvest_references("PMC", pick["pmcid"],
                                         include_control="NCT01179048",   # LEADER, should be cited
                                         exclude_control="NCT01327846")   # SPRINT, must not be
            harvest["harvested_from"] = {"pmid": pick["pmid"], "pmcid": pick["pmcid"],
                                         "title": (pick.get("title") or "")[:90]}
    result["harvest"] = harvest
    if out_dir:
        from pathlib import Path
        from datetime import datetime, timezone
        p = Path(out_dir); p.mkdir(parents=True, exist_ok=True)
        f = p / ("prior_syntheses_%s.json" % datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ"))
        io.open(f, "w", encoding="utf-8", newline="\n").write(json.dumps(result, indent=1, ensure_ascii=False))
        result["_written_to"] = str(f)
    return result


if __name__ == "__main__":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    r = run(out_dir=("evidence/acquisition" if "--write" in sys.argv else None))
    s = r["search"]
    print("PRIOR-SYNTHESES adapter")
    print("  SEARCH state=%s denominator(hitCount)=%s control=%s"
          % (s["state"], (s["denominator"] or {}).get("hit_count"),
             (s["control"] or {}).get("verdict")))
    h = r["harvest"]
    if not h:
        print("  HARVEST: not attempted (search did not run)")
    else:
        print("  HARVEST state=%s from=%s" % (h["state"], (h.get("harvested_from") or {}).get("pmcid")))
        if h["state"] in (RAN_ZERO, RAN_RESULTS):
            print("    references=%s with_nct=%s trials_harvested=%s tier=SYNTHESIS_REPORTED"
                  % (h["denominator"]["references"], h["denominator"]["references_with_nct"],
                     len(h["harvested_trials"])))
            print("    control:", (h.get("control") or {}).get("verdict"))
        else:
            print("    %s -- %s" % (h["state"], h.get("state_detail")))
    if r.get("_written_to"):
        print("  written:", r["_written_to"])
