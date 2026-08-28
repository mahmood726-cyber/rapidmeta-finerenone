# -*- coding: utf-8 -*-
"""Re-test every claim in the corpus that a document could not be obtained.

WHY. Seven "abstract only" claims were retracted as false today, before anyone knew that a
single-index lookup reports paywalls that are not there. Europe PMC says `isOpenAccess=N` and
404s on a deposit NCBI `efetch` serves in full; 43 of 317 reachable trials (14%) are reachable
only by the second route. So every stored claim of inaccessibility that was decided on one
index is suspect, and re-testing them is the cheapest way to grow the answerable set.

⚠️ A CLAIM OF ABSENCE IS A CLAIM ABOUT A METHOD. "No full text" without a named route is not a
finding about the document; it is a finding about whichever API was asked once. This script
re-tests each claim through every route and reports which one succeeded.

BOTH ARMS ARE COUNTED. Stores carrying no access claim are the majority and are reported, so
the number of claims is a rate over a stated population rather than a bare count.
"""
import collections
import glob
import io
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(os.path.dirname(HERE))
os.chdir(REPO)
sys.path.insert(0, HERE)
import multiroute_retrieve as MR  # noqa: E402

CLAIM = re.compile(
    r"abstract[- ]only|no full[- ]text|full text (?:not|un)available|not retrievable|"
    r"paywall(?:ed)?|could not (?:be )?(?:retrieve|obtain|access)|inaccessible", re.I)
NCT = re.compile(r"NCT\d{8}")
PMCID = re.compile(r"PMC\d{6,9}")
PMID = re.compile(r'"pmid"\s*:\s*"?(\d{7,8})')
DOI = re.compile(r"10\.\d{4,9}/[^\s\"',}]{4,60}")


def walk(node, path, out):
    """Every string in the object, with the path that reaches it."""
    if isinstance(node, dict):
        for k, v in node.items():
            walk(v, path + [str(k)], out)
    elif isinstance(node, list):
        for i, v in enumerate(node):
            walk(v, path + ["[%d]" % i], out)
    elif isinstance(node, str):
        out.append(("/".join(path), node))


def main():
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace",
                                  line_buffering=True)
    reach = {}
    fr = r"F:\claude-temp\pend\funder_retrievability.jsonl"
    if os.path.exists(fr):
        for ln in io.open(fr, encoding="utf-8"):
            try:
                r = json.loads(ln)
                reach[r["nct"]] = r
            except Exception:
                pass

    stores = []
    for p in sorted(glob.glob("ssot/*/*.json")):
        t = os.path.basename(os.path.dirname(p))
        if os.path.basename(p) == t + ".json":
            stores.append((t, p))

    claims, with_claim = [], set()
    for t, p in stores:
        try:
            o = json.load(io.open(p, encoding="utf-8"))
        except Exception:
            continue
        strings = []
        walk(o, [], strings)
        for path, s in strings:
            m = CLAIM.search(s)
            if not m:
                continue
            with_claim.add(t)
            ctx = s
            claims.append({"topic": t, "path": path, "phrase": m.group(0).lower(),
                           "nct": (NCT.search(path + " " + ctx).group(0)
                                   if NCT.search(path + " " + ctx) else None),
                           "pmcid": (PMCID.search(ctx).group(0)
                                     if PMCID.search(ctx) else None),
                           "doi": (DOI.search(ctx).group(0) if DOI.search(ctx) else None),
                           "text": s[:190]})

    print("")
    print("RE-TEST OF STORED CLAIMS THAT A DOCUMENT COULD NOT BE OBTAINED")
    print("")
    print("  stores in the corpus                    %4d  == the denominator" % len(stores))
    print("  stores carrying an access claim         %4d   %5.1f%%"
          % (len(with_claim), 100.0 * len(with_claim) / len(stores)))
    print("  stores carrying none                    %4d" % (len(stores) - len(with_claim)))
    print("  individual access claims                %4d" % len(claims))
    print("")
    c = collections.Counter(x["phrase"] for x in claims)
    for k, v in c.most_common(8):
        print("     %-26s %3d" % (k, v))

    # WHICH CLAIMS CARRY AN IDENTIFIER WE CAN ACT ON -- both arms, because a claim with no
    # identifier is not retestable and must not be counted as either confirmed or refuted.
    actionable = [x for x in claims if x["pmcid"] or x["nct"] or x["doi"]]
    print("")
    print("  claims naming an identifier             %4d" % len(actionable))
    print("  claims naming NOTHING to re-test        %4d  <- not confirmed, not refuted"
          % (len(claims) - len(actionable)))

    res = collections.Counter()
    rows = []
    for x in actionable:
        pmcid = x["pmcid"]
        if not pmcid and x["nct"] and reach.get(x["nct"], {}).get("pmcid"):
            pmcid = reach[x["nct"]]["pmcid"]
        if not (pmcid or x["doi"]):
            res["NO_ROUTE_INPUT"] += 1
            continue
        rec = MR.retrieve(pmcid=pmcid, doi=x["doi"])
        got = bool(rec.get("route"))
        res["RETRIEVABLE" if got else "CONFIRMED_UNREACHABLE"] += 1
        if got:
            res["via_" + rec["route"]] += 1
        rows.append({**x, "probe_pmcid": pmcid, "route": rec.get("route"),
                     "rendered_chars": rec.get("rendered_chars"),
                     "attempts": rec.get("attempts")})
    print("")
    print("  RE-TESTED                               %4d" % (res["RETRIEVABLE"] + res["CONFIRMED_UNREACHABLE"]))
    print("     actually RETRIEVABLE                 %4d  <- the claim was false" % res["RETRIEVABLE"])
    print("     confirmed unreachable                %4d" % res["CONFIRMED_UNREACHABLE"])
    print("     no usable identifier for a probe     %4d" % res["NO_ROUTE_INPUT"])
    print("")
    print("  by the route that succeeded:")
    for k, v in res.most_common():
        if k.startswith("via_"):
            print("     %-26s %3d" % (k[4:], v))
    out = r"F:\claude-temp\pend\access_claim_retest.json"
    json.dump(rows, io.open(out, "w", encoding="utf-8"), indent=1)
    import provenance as pv
    pv.stamp(out, note="re-test of stored inaccessibility claims through every route")
    print("  detail -> access_claim_retest.json (+ .prov.json)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
