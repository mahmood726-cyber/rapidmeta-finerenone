"""RE-GATE THE FIVE COMPLETED TOPICS AGAINST THE REPAIRED CLASSIFIER.

Commit e20f94068 repaired `topic_identity.locate()` for the TRAILING placebo convention
(`Drug: Apixaban-matching placebo`) and stated, in its own message:

    "no INCLUDED trial of any of the five gated topics changed role -- checked, not assumed.
     Their CASCADE COUNTS may move where a changed registration was in their surfaced set,
     and those four topics are now knowably below the instrument that produced them. To be
     re-run and re-gated with old and new side by side, not silently."

This file is that re-run. It answers ONE question per topic: does the repaired classifier
change any k on a page that is already gated?

TWO CLASSIFIERS, BOTH LOADED FROM GIT, NEITHER REIMPLEMENTED FROM MEMORY.
  NEW = ssot/topic_identity.py at the working tree
  OLD = ssot/topic_identity.py at 7a08bcbe1, the commit immediately BEFORE e20f94068
Reimplementing the old rule from the commit message would test this script against its
author's reading of it, which is detector 10's rule in the other direction.

THE SURFACED SET IS HELD CONSTANT ON PURPOSE. Each topic's BROAD query is re-executed
verbatim from the object's own `search.databases[].query_as_executed`, so k0 is measured
rather than inherited. If today's k0 differs from the stored k0 that is REGISTRY DRIFT, and
it is printed as a separate line and never folded into the classifier delta -- two causes
summed into one number is the "one k" error the cascade exists to avoid.

Pagination is checked, not assumed (E10): returned == totalCount and nextPageToken is null,
per query, printed.
"""
import importlib.util
import json
import os
import subprocess
import sys
import urllib.parse
import urllib.request

REPO = "F:/rapidmeta-ssot-shell"
sys.path.insert(0, REPO + "/ssot")
os.environ.setdefault(
    "RM_CTGOV_CACHE",
    "F:/claude-temp/claude/F--rapidmeta-ssot-shell/"
    "eb4d84e5-8a24-4c3b-afe2-34bd91c20bc7/scratchpad/.ctgov-raw-cache")

import ctgov_transport as X          # noqa: E402  (path set above)
import topic_identity as NEW         # noqa: E402

OLD_REV = "7a08bcbe1"
SCRATCH = ("F:/claude-temp/claude/F--rapidmeta-ssot-shell/"
           "6b629e1e-cc8c-4565-af03-e40341ee43f3/scratchpad")


def load_old_classifier():
    """topic_identity.py AS IT WAS, read out of git. Not a reimplementation."""
    # DECODED EXPLICITLY, not via text=True: that decodes with the console codepage, so on a
    # cp1252 box a source file containing any non-ASCII byte either mangles or raises -- and
    # the thing being read here is the CLASSIFIER whose behaviour the whole run depends on.
    src = subprocess.run(["git", "-C", REPO, "show", f"{OLD_REV}:ssot/topic_identity.py"],
                         capture_output=True, check=True).stdout.decode("utf-8", "replace")
    os.makedirs(SCRATCH, exist_ok=True)
    path = os.path.join(SCRATCH, "topic_identity_OLD.py")
    with open(path, "w", encoding="utf-8") as fh:
        fh.write(src)
    spec = importlib.util.spec_from_file_location("topic_identity_OLD", path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


# ---------------------------------------------------------------------------
# THE FIVE GATED TOPICS. Each query is the BROAD one recorded in the object's own
# `search` block -- the one whose recall on the included set was measured.
# ---------------------------------------------------------------------------
TOPICS = {
    "alirocumab-lipid": {
        "topic_key": "alirocumab",
        "stored_k0": 99,
        "query_as_stored": ('query.intr="alirocumab OR praluent OR SAR236553 OR REGN727"; '
                            'filter.advanced=AREA[StudyType]INTERVENTIONAL'),
        "raw_expr": {"query.intr": "alirocumab OR praluent OR SAR236553 OR REGN727",
                     "filter.advanced": "AREA[StudyType]INTERVENTIONAL"},
    },
    "attr-cm-review": {
        "topic_key": "tafamidis OR acoramidis",
        "stored_k0": 55,
        "query_as_stored": ('query.intr="tafamidis OR acoramidis OR vyndaqel OR vyndamax OR '
                            'attruby OR AG10"; filter.advanced=AREA[StudyType]INTERVENTIONAL'),
        "raw_expr": {"query.intr": ("tafamidis OR acoramidis OR vyndaqel OR vyndamax OR "
                                    "attruby OR AG10"),
                     "filter.advanced": "AREA[StudyType]INTERVENTIONAL"},
    },
    "bempedoic-acid-review": {
        "topic_key": "bempedoic acid",
        "stored_k0": 21,
        "query_as_stored": ('condition="hypercholesterolemia OR dyslipidemia OR cardiovascular '
                            'disease"; intervention="bempedoic acid"; INTERVENTIONAL; '
                            'phase=[PHASE3,PHASE4]'),
        "raw_expr": {"query.cond": "hypercholesterolemia OR dyslipidemia OR cardiovascular disease",
                     "query.intr": "bempedoic acid",
                     "filter.advanced": ("AREA[StudyType]INTERVENTIONAL AND "
                                         "AREA[Phase](PHASE3 OR PHASE4)")},
    },
    "iv-iron-hf": {
        "topic_key": "intravenous iron",
        "stored_k0": 47,
        "query_as_stored": ('query.cond="heart failure"; query.intr="ferric carboxymaltose OR '
                            'iron sucrose OR ferric derisomaltose OR iron isomaltoside OR '
                            'intravenous iron"; filter.advanced=AREA[StudyType]INTERVENTIONAL'),
        "raw_expr": {"query.cond": "heart failure",
                     "query.intr": ("ferric carboxymaltose OR iron sucrose OR ferric "
                                    "derisomaltose OR iron isomaltoside OR intravenous iron"),
                     "filter.advanced": "AREA[StudyType]INTERVENTIONAL"},
    },
    "sglt2-hf": {
        "topic_key": "sglt2 inhibitors",
        "stored_k0": 56,
        "query_as_stored": ('condition="heart failure"; intervention="dapagliflozin OR '
                            'empagliflozin OR sotagliflozin OR canagliflozin OR ertugliflozin"; '
                            'INTERVENTIONAL; phase=[PHASE3]'),
        "raw_expr": {"query.cond": "heart failure",
                     "query.intr": ("dapagliflozin OR empagliflozin OR sotagliflozin OR "
                                    "canagliflozin OR ertugliflozin"),
                     "filter.advanced": ("AREA[StudyType]INTERVENTIONAL AND "
                                         "AREA[Phase]PHASE3")},
    },
}

SEARCH_API = "https://clinicaltrials.gov/api/v2/studies"


def raw_search(expr, page_size=1000):
    """(state, ids, detail). Paginates; never returns a partial list as if complete."""
    ids, token, pages, total = [], None, 0, None
    while True:
        params = dict(expr)
        params["fields"] = "NCTId"
        params["pageSize"] = str(page_size)
        params["countTotal"] = "true"
        if token:
            params["pageToken"] = token
        url = f"{SEARCH_API}?{urllib.parse.urlencode(params)}"
        try:
            with urllib.request.urlopen(url, timeout=90) as resp:
                if resp.status != 200:
                    return X.UNREACHABLE, ids, f"HTTP {resp.status} on page {pages + 1}"
                payload = json.loads(resp.read().decode("utf-8"))
        except Exception as exc:                       # noqa: BLE001 - transport, reported
            return X.UNREACHABLE, ids, f"{type(exc).__name__}: {exc} on page {pages + 1}"
        for s in payload.get("studies") or []:
            nct = (((s.get("protocolSection") or {}).get("identificationModule")
                    or {}).get("nctId"))
            if nct:
                ids.append(nct)
        pages += 1
        token = payload.get("nextPageToken")
        # FROM THE FIRST PAGE ONLY. `countTotal=true` populates totalCount on the first
        # response and returns null on later ones, so reading it here reported
        # `returned==totalCount: False` on a complete multi-page fetch. Every query this file
        # runs fits in one page, so the last page WAS the first and the defect could not
        # show -- it was found on a two-page query in scripts/search_ablation_split.
        # A guard that has only ever run on single-page inputs has not been tested on the
        # case it exists for.
        if pages == 1:
            total = payload.get("totalCount")
        if not token:
            return (X.OK, ids,
                    f"{len(ids)} ids over {pages} page(s), totalCount={total}, "
                    f"nextPageToken=null, returned==totalCount: {len(ids) == total}")
        if pages > 20:
            return X.MALFORMED, ids, "pagination did not terminate in 20 pages"


def included_ncts(topic_dir):
    """The object's own included set, read from the object -- never recalled."""
    path = f"{REPO}/ssot/{topic_dir}/{topic_dir}.json"
    obj = json.load(open(path, encoding="utf-8"))
    out = []
    pf = (obj.get("prisma_flow") or {}).get("included") or {}
    out += [str(n) for n in (pf.get("nct") or [])]
    for t in ((obj.get("inputs") or {}).get("trials") or []):
        for key in ("nct", "nct_id", "registration", "registration_id", "id"):
            v = t.get(key)
            if isinstance(v, str) and v.upper().startswith("NCT"):
                out.append(v)
                break
    return sorted(set(out))


def tally(roles, mod):
    return {
        "k2_role_located": sum(1 for r in roles.values()
                               if r in (mod.EXPERIMENTAL, mod.COMPARATOR, mod.BACKGROUND)),
        "k3_experimental": sum(1 for r in roles.values() if r == mod.EXPERIMENTAL),
        "k4_comparator": sum(1 for r in roles.values() if r == mod.COMPARATOR),
        "k5_background": sum(1 for r in roles.values() if r == mod.BACKGROUND),
        "kNA_not_assessable": sum(1 for r in roles.values() if r == mod.NOT_ASSESSABLE),
    }


def main():
    OLD = load_old_classifier()
    print(f"OLD classifier loaded from git {OLD_REV}:ssot/topic_identity.py "
          f"({len(OLD.TOPIC_SYNONYMS)} declared topics)")
    print(f"NEW classifier from working tree ({len(NEW.TOPIC_SYNONYMS)} declared topics)")
    print()

    report = {}
    for topic_dir, spec in sorted(TOPICS.items()):
        key = spec["topic_key"]
        syns_new = NEW.synonyms_for(key)
        syns_old = OLD.synonyms_for(key)
        if syns_new != syns_old:
            print(f"!! {topic_dir}: SYNONYM SET ALSO CHANGED between the two revisions. "
                  f"The delta below is NOT attributable to locate() alone.")
        state, ids, detail = raw_search(spec["raw_expr"])
        ids = sorted(set(ids))
        inc = included_ncts(topic_dir)

        roles_old, roles_new, unreachable = {}, {}, []
        for nct in ids:
            st, study, det = X.fetch_raw(nct)
            if st != X.OK:
                unreachable.append(nct)
                continue
            payload = X.require_raw_v2(study, nct)
            roles_old[nct] = OLD.locate(payload, syns_old)[0]
            roles_new[nct], ev = NEW.locate(payload, syns_new)
            if roles_old[nct] != roles_new[nct]:
                roles_new[nct + "_ev"] = ev

        t_old, t_new = tally(roles_old, OLD), tally(
            {k: v for k, v in roles_new.items() if not k.endswith("_ev")}, NEW)
        changed = {n: (roles_old[n], roles_new[n]) for n in roles_old
                   if roles_old[n] != roles_new[n]}
        changed_included = {n: v for n, v in changed.items() if n in inc}
        inc_not_surfaced = [n for n in inc if n not in ids]

        rec = {"topic_dir": topic_dir, "topic_key": key,
               "query_as_stored": spec["query_as_stored"],
               "search_state": state, "search_detail": detail,
               "stored_k0": spec["stored_k0"], "k0_today": len(ids),
               "k0_drift": len(ids) - spec["stored_k0"],
               "kUNREACHABLE": len(unreachable), "unreachable_ids": unreachable,
               "old": t_old, "new": t_new,
               "changed": {n: {"old": a, "new": b} for n, (a, b) in sorted(changed.items())},
               "changed_evidence": {n[:-3]: roles_new[n] for n in roles_new
                                    if n.endswith("_ev")},
               "included_in_object": inc,
               "included_that_changed_role": changed_included,
               "included_not_surfaced_by_this_query": inc_not_surfaced}
        report[topic_dir] = rec

        print(f"--- {topic_dir}   [{key}]")
        print(f"    search  {state} -- {detail}")
        print(f"    k0 stored {spec['stored_k0']:>4}  |  k0 today {len(ids):>4}  "
              f"({'SAME SURFACED SIZE' if len(ids) == spec['stored_k0'] else 'REGISTRY DRIFT -- reported, NOT folded into the classifier delta'})")
        if unreachable:
            print(f"    kUNREACHABLE {len(unreachable)} -- never read; not a verdict: {unreachable}")
        print(f"    {'stage':<20}{'OLD':>6}{'NEW':>6}{'delta':>8}")
        for stg in ("k2_role_located", "k3_experimental", "k4_comparator",
                    "k5_background", "kNA_not_assessable"):
            d = t_new[stg] - t_old[stg]
            print(f"    {stg:<20}{t_old[stg]:>6}{t_new[stg]:>6}{d:>+8}"
                  f"{'   <-- MOVED' if d else ''}")
        print(f"    role changes: {len(changed)}")
        for n, (a, b) in sorted(changed.items()):
            mark = "  *** IN THIS OBJECT'S INCLUDED SET ***" if n in inc else ""
            print(f"      {n}  {a} -> {b}{mark}")
            print(f"        NEW evidence: {roles_new.get(n + '_ev')}")
        print(f"    included set ({len(inc)}): {inc}")
        if inc_not_surfaced:
            print(f"    !! included but NOT surfaced by this query: {inc_not_surfaced}")
        print(f"    INCLUDED trials whose role changed: "
              f"{changed_included if changed_included else 'NONE'}")
        print()

    out = os.path.join(SCRATCH, "regate_cascade_2026_08_19.json")
    os.makedirs(SCRATCH, exist_ok=True)
    with open(out, "w", encoding="utf-8") as fh:
        json.dump(report, fh, indent=1)
    print(f"wrote {out}")

    moved = [t for t, r in report.items()
             if any(r["new"][s] != r["old"][s] for s in r["old"])]
    drifted = [t for t, r in report.items() if r["k0_drift"]]
    print()
    print("SUMMARY")
    print(f"  topics whose cascade MOVED under the repaired classifier: "
          f"{moved if moved else 'NONE'}")
    print(f"  topics whose k0 drifted since the stored search: "
          f"{drifted if drifted else 'NONE'}")
    print("  A moved cascade requires the page to be RESTATED and RE-GATED, not silently "
          "rebuilt.")


if __name__ == "__main__":
    main()
