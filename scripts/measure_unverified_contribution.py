"""Do unverifiable NCT ids CONTRIBUTE rows to served pooled estimates?

A banner disclosing an id is not the same as excluding it from a pooled estimate.
This measures which, per id per page.

The pages encode the distinction themselves:

    "NULLED:NCT01993004":{...}   <- excluded; the key is prefixed
    NCT00098560:{...,tE:35,cE:40,publishedHR:.88}   <- live, with effect data
    AUTO_INCLUDE_TRIAL_IDS=new Set([...])           <- included in the analysis

STATES
  CONTRIBUTES      live (un-NULLED) key in realData carrying effect data
  DISCLOSED_ONLY   present only in the provenance banner, or NULLED
  NOT_POOLED       live key but no effect data to pool

⛔ REPORTS ONLY. Fixes nothing. If anything CONTRIBUTES it is a retraction
question for a person, not an edit for a script.
"""
import glob
import io
import json
import os
import re
import sys

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

SP = (r"F:/claude-temp/claude/F--AACT-storage/"
      r"9e740389-664c-4a27-937f-bd15251130e0/scratchpad")
ROOT = r"F:/aactwt"

bad = sorted(n for n, r in json.load(
    open(os.path.join(SP, "absent_nct_classification.json"), encoding="utf-8")
)["by_nct"].items() if r["state"] == "MALFORMED_ID_IN_OUR_STORE")

EFFECT = ("publishedHR", "tE", "cE", "tN", "cN", "effect")


def classify(txt, nct):
    nulled = re.search(r'"NULLED:%s"\s*:' % nct, txt) is not None
    live = re.search(r'[,{]\s*"?%s"?\s*:\s*\{' % nct, txt) is not None
    auto = False
    m = re.search(r"AUTO_INCLUDE_TRIAL_IDS\s*=\s*new Set\(\[(.*?)\]\)", txt, re.S)
    if m:
        auto = nct in m.group(1)
    body = ""
    if live:
        m2 = re.search(r'[,{]\s*"?%s"?\s*:\s*\{' % nct, txt)
        body = txt[m2.end():m2.end() + 700]
    fields = [f for f in EFFECT if re.search(r"\b%s\s*:" % f, body)]
    if live and fields:
        state = "CONTRIBUTES"
    elif live:
        state = "NOT_POOLED"
    else:
        state = "DISCLOSED_ONLY"
    name = ""
    mn = re.search(r'name\s*:\s*"([^"]+)"', body)
    if mn:
        name = mn.group(1)
    return {"state": state, "nulled": nulled, "live_key": live,
            "in_auto_include": auto, "effect_fields": fields, "name": name}


# ⭐ EVERY PAGE IS ASSIGNED A POSITIVE STATE. No page leaves the loop unaccounted.
#
# An earlier draft carried two silent `continue`s -- one for an unreadable file, one
# for a page holding none of the 45 ids. Both are negative guards inside a
# corpus-wide loop, and both make the scan's REACH invisible: the output would have
# read "38 pages" while never saying how many were looked at, or how many could not
# be read at all. A scan reports where it LOOKED, not the population it claims to
# cover. The states below are positive, and they are asserted to sum to the pages
# found -- so a page cannot vanish between the glob and the table.
rows = []
reach = {"CARRIES_UNVERIFIED_ID": 0, "CLEAN_OF_ALL_45": 0, "UNREADABLE": []}
pages = sorted(glob.glob(os.path.join(ROOT, "*.html")))
for f in pages:
    base = os.path.basename(f)
    txt = None
    try:
        txt = open(f, encoding="utf-8", errors="replace").read()
    except Exception as e:                      # recorded, never silent
        reach["UNREADABLE"].append({"page": base, "error": repr(e)})
    if txt is not None:
        present = [n for n in bad if n in txt]
        if present:
            reach["CARRIES_UNVERIFIED_ID"] += 1
            for n in present:
                r = classify(txt, n)
                r.update({"page": base, "nct": n})
                rows.append(r)
        else:
            # POSITIVE property: this page contains none of the 45 ids.
            reach["CLEAN_OF_ALL_45"] += 1

assert (reach["CARRIES_UNVERIFIED_ID"] + reach["CLEAN_OF_ALL_45"]
        + len(reach["UNREADABLE"])) == len(pages), "reach does not sum to pages found"
print("REACH -- every page assigned a state, none skipped")
print(f"  pages found               : {len(pages)}")
print(f"  carries >=1 unverified id : {reach['CARRIES_UNVERIFIED_ID']}")
print(f"  clean of all 45           : {reach['CLEAN_OF_ALL_45']}")
print(f"  unreadable                : {len(reach['UNREADABLE'])}"
      + (f"  {reach['UNREADABLE']}" if reach["UNREADABLE"] else ""))
print()

# ---- controls: the classifier must separate a KNOWN nulled id from a KNOWN live one
ctrl_txt = open(os.path.join(ROOT, "HYPOFRAC_BREAST_RT_NMA_REVIEW.html"),
                encoding="utf-8", errors="replace").read()
c_null = classify(ctrl_txt, "NCT01993004")     # page shows "NULLED:NCT01993004"
c_live = classify(ctrl_txt, "NCT00041223")     # bare key, START-A, in auto-include
print("CLASSIFIER CONTROLS")
print(f"  known NULLED  NCT01993004 -> {c_null['state']:<15} (expect DISCLOSED_ONLY)")
print(f"  known LIVE    NCT00041223 -> {c_live['state']:<15} (expect CONTRIBUTES)")
ok = c_null["state"] == "DISCLOSED_ONLY" and c_live["state"] == "CONTRIBUTES"
print(f"  CONTROLS {'PASS' if ok else 'FAIL -- do not believe the table below'}\n")

counts = {}
for r in rows:
    counts[r["state"]] = counts.get(r["state"], 0) + 1
print("=" * 78)
print("UNVERIFIABLE IDs IN SERVED PAGES")
print("=" * 78)
for k, v in sorted(counts.items(), key=lambda x: -x[1]):
    print(f"  {k:<18}{v:>4}")
print(f"  {'TOTAL (id x page)':<18}{len(rows):>4}")

contrib = [r for r in rows if r["state"] == "CONTRIBUTES"]
print(f"\ndistinct ids contributing : "
      f"{len({r['nct'] for r in contrib})} of {len(bad)}")
print(f"distinct pages affected   : {len({r['page'] for r in contrib})}")

print("\n" + "=" * 78)
print("CONTRIBUTING ROWS -- each is a pooled estimate built on an id that 404s")
print("=" * 78)
print(f"{'page':<44}{'nct':<13}{'name':<16}auto  fields")
for r in sorted(contrib, key=lambda x: x["page"]):
    print(f"{r['page'][:43]:<44}{r['nct']:<13}{r['name'][:15]:<16}"
          f"{str(r['in_auto_include']):<6}{','.join(r['effect_fields'])}")

json.dump({"controls_pass": ok, "counts": counts, "rows": rows},
          open(os.path.join(SP, "unverified_contribution.json"), "w",
               encoding="utf-8"), indent=1)
print(f"\nwrote {SP}/unverified_contribution.json")
print("MEASURE_COMPLETE")
