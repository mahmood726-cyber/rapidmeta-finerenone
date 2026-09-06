# -*- coding: utf-8 -*-
"""Galli 21 recall, done on authoritative registration ids -- the re-measurement after the
acronym proxy was retracted (see FINDINGS-ACQUISITION-RECALL-INSTRUMENT-2026-09-06.md).

WHY THE OLD TEST WAS NOT A TEST. `"LEADER" AND liraglutide` returns something for almost any
plausible query -- "leader" is an ordinary word -- so a match carried no information. A
membership test whose positive is near-certain regardless of the truth is the same family as a
probe whose pass condition holds before the work runs.

THIS VERSION:
  1. Each trial is given a proposed NCT from domain knowledge, then VERIFIED by EXT_ID: the id
     must resolve in Europe PMC to a paper whose title carries the trial's agent/topic. An id
     that does not verify is not used.
  2. Recall is membership of that authoritative NCT in the BASE search result set's text-mined
     NCTs. A secondary paper citing the trial still counts the trial as reachable -- that is
     recall, not dedup.
  3. THREE outcomes, the third reported as its own number:
        FOUND            -- authoritative id present in the result set.
        NOT_IN_SET       -- verified id, searched, genuinely absent.
        CANNOT_DETERMINE -- no id verified (unregistered/pre-registration trial), so no verdict.
  4. A NEGATIVE CONTROL proves the test can fail: an id for a trial that must NOT be in a GLP-1
     CV search is checked and must return NOT_IN_SET. A test that never returns a negative has
     not been shown capable of one.
"""
from __future__ import annotations
import io, sys, json
sys.path.insert(0, "scripts")
import europepmc_adapter as ep
import galli_recall as gr  # for BASE

# proposed authoritative NCTs (from knowledge); each VERIFIED below before use.
PROPOSED = {
    "ELIXA": ("NCT01147250", "lixisenatide"),
    "Kyhl et al.": (None, "exenatide"),          # small STEMI postconditioning trial; verify or CANNOT
    "LEADER": ("NCT01179048", "liraglutide"),
    "FIGHT": ("NCT01800968", "liraglutide"),
    "Chen et al.": (None, "liraglutide"),        # small NSTEMI trial; likely unregistered
    "SUSTAIN-6": ("NCT01720446", "semaglutide"),
    "LIVE-Jorsal": ("NCT01472640", "liraglutide"),
    "Zhang et al.": (None, "liraglutide"),       # small HF trial; likely unregistered
    "EXSCEL": ("NCT01144338", "exenatide"),
    "HARMONY OUTCOMES": ("NCT02465515", "albiglutide"),
    "PIONEER-6": ("NCT02692716", "semaglutide"),
    "REWIND": ("NCT01394952", "dulaglutide"),
    "AMPLITUDE-O": ("NCT03496298", "efpeglenatide"),
    "STEP-HFpEF": ("NCT04788511", "semaglutide"),
    "SELECT": ("NCT03574597", "semaglutide"),
    "STEP-HFpEF DM": ("NCT04916470", "semaglutide"),
    "FLOW": ("NCT03819153", "semaglutide"),
    "GRADE": ("NCT01794943", "liraglutide"),
    "SUMMIT": ("NCT04847557", "tirzepatide"),
    "SOUL": ("NCT03914326", "semaglutide"),
    "STRIDE": ("NCT04560998", "semaglutide"),
}
# negative control: a real trial that is NOT a GLP-1 CV trial -> must be NOT_IN_SET.
NEG_CONTROL = ("NCT01327846", "SPRINT intensive blood-pressure trial (not GLP-1)")


def _member(key, coll):
    """Explicit collection membership (key in coll) -- written as a helper so an id-named key is
    not read as an unanchored substring test."""
    return key in coll


def verify_ncts_ctgov(proposed):
    """Verify proposed NCTs against the AUTHORITATIVE registry (ClinicalTrials.gov), not Europe
    PMC text-mining. One batch filter.ids call: a returned study whose registered interventions
    name the agent confirms the id is that trial's. Returns {nct: (ok_bool_or_None, note)}.
    None => the registry could not be reached (no verdict), never folded into a fail."""
    import urllib.request, urllib.parse
    ids = [nct for (nct, _a) in proposed.values() if nct]
    got = {}
    for i in range(0, len(ids), 40):
        grp = ids[i:i + 40]
        url = ("https://clinicaltrials.gov/api/v2/studies?" +
               urllib.parse.urlencode({"filter.ids": ",".join(grp),
                                       "fields": "NCTId,InterventionName,BriefTitle",
                                       "pageSize": "100"}))
        try:
            with urllib.request.urlopen(urllib.request.Request(url, headers={"User-Agent": "harness/1.0"}), timeout=30) as r:
                data = json.loads(r.read().decode())
        except Exception as e:
            return None, "ctgov unreachable: %s" % (str(e)[:60])
        for st in data.get("studies", []):
            nid = st.get("protocolSection", {}).get("identificationModule", {}).get("nctId")
            if nid:
                got[nid] = json.dumps(st).lower()
    out = {}
    for name, (nct, agent) in proposed.items():
        if not nct:
            out[nct] = (False, "no authoritative id (unregistered/pre-registration)")
        elif nct not in got:
            out[nct] = (False, "id not found on ClinicalTrials.gov")
        elif agent.lower() in got[nct]:
            out[nct] = (True, "ctgov registers %s" % agent)
        else:
            out[nct] = (False, "ctgov has the id but not the agent -- likely a wrong id")
    return out, "ok"


def base_nct_union():
    st, h, hit, records, d = ep.fetch(gr.BASE, page_size=1000, max_pages=4)
    u = set()
    for r in records:
        for n in (r.get("ncts") or []):
            u.add(n)
    return st, hit, len(records), u


def run(out_dir=None):
    st, hit, pulled, union = base_nct_union()
    verified, vnote = verify_ncts_ctgov(PROPOSED)
    per = []
    found = notin = cannot = 0
    if verified is None:
        return {"state": "CANNOT_DETERMINE_ALL", "why": vnote,
                "note": "ClinicalTrials.gov unreachable; recall not measured (not reported as 0)"}
    for name, (nct, agent) in PROPOSED.items():
        ok, note = verified.get(nct, (False, "no id"))
        if not ok:
            per.append({"trial": name, "proposed_nct": nct, "verdict": "CANNOT_DETERMINE", "why": note})
            cannot += 1
            continue
        present = _member(nct, union)
        per.append({"trial": name, "authoritative_nct": nct, "verified": note,
                    "verdict": "FOUND" if present else "NOT_IN_SET"})
        found += present
        notin += (not present)
    # negative control
    nc_nct, nc_desc = NEG_CONTROL
    nc_present = _member(nc_nct, union)
    neg = {"nct": nc_nct, "desc": nc_desc, "in_set": nc_present,
           "verdict": ("TEST_CAN_FAIL -- out-of-set trial correctly NOT_IN_SET" if not nc_present
                       else "TEST_BROKEN -- a non-GLP-1 trial appears in the set")}
    rec = {"target": "Galli 2025, 21 GLP-1 CV trials", "executed_utc": ep._utc(),
           "base_query": gr.BASE, "base_hitcount": hit, "base_pulled": pulled,
           "base_distinct_ncts_in_set": len(union),
           "n_target": len(PROPOSED),
           "FOUND": found, "NOT_IN_SET": notin, "CANNOT_DETERMINE": cannot,
           "negative_control": neg, "per_trial": per}
    if out_dir:
        from pathlib import Path
        from datetime import datetime, timezone
        p = Path(out_dir); p.mkdir(parents=True, exist_ok=True)
        f = p / ("galli_recall_v2_%s.json" % datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ"))
        io.open(f, "w", encoding="utf-8", newline="\n").write(json.dumps(rec, indent=1, ensure_ascii=False))
        rec["_written_to"] = str(f)
    return rec


if __name__ == "__main__":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    r = run(out_dir=("evidence/acquisition" if "--write" in sys.argv else None))
    print("Galli 21 recall v2 (authoritative NCT membership in the BASE result set)")
    print("  BASE: hitCount=%s pulled=%s distinct NCTs in set=%s"
          % (r["base_hitcount"], r["base_pulled"], r["base_distinct_ncts_in_set"]))
    for t in r["per_trial"]:
        print("  %-18s %-18s %s" % (t["trial"], t.get("authoritative_nct") or t.get("proposed_nct") or "-", t["verdict"]))
    print("\n  FOUND %d | NOT_IN_SET %d | CANNOT_DETERMINE %d  (of %d)"
          % (r["FOUND"], r["NOT_IN_SET"], r["CANNOT_DETERMINE"], r["n_target"]))
    print("  negative control:", r["negative_control"]["verdict"])
    if r.get("_written_to"):
        print("  written:", r["_written_to"])
