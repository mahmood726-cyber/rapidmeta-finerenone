# -*- coding: utf-8 -*-
"""topic -> OUR PAGE -> COUNTERPART, for the topics that carry a judged counterpart.

⛔ THIS DOES NOT RANK. Another lane owns `tabs_with_content` and the only content detector
worth trusting; ranking here would be a second opinion from the wrong instrument. This
produces the MAPPING and hands it over.

⭐ WHY THE POOL IS THE TEN AND NOT THE TWENTY. A page at full moat standard with no
counterpart cannot be scored against anything. The candidate pool is exactly the topics with
a judged COUNTERPART -- 5 from the CDSR frame, 5 from the open-access lane.

⛔⛔ PAGE_MAP IS RESOLVED, THEN CHECKED AGAINST THE DISK, AND DISAGREEMENT IS REPORTED.
`ssot/PAGE_MAP.json` is the canonical pointer and it has been WRONG in a way that cost a
count: it pointed at a LEGACY page while a newer delivered page existed, under-counting
manuscripts by three and blinding a scan to its own founding case. So both are resolved:
what PAGE_MAP says, and what files actually exist. A topic where they disagree is NAMED, not
silently resolved in favour of either.

⚠️ Counterparts come from TWO sources with DIFFERENT verification material and they are kept
apart. A CDSR counterpart was verified against a Cochrane objectives statement; an
open-access one against an abstract. They may not be pooled into one quality claim.
"""
import glob
import io
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
os.chdir(HERE)
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace",
                              line_buffering=True)

ROOT = "F:/rapidmeta-ssot-shell"
PAGE_MAP = os.path.join(ROOT, "ssot", "PAGE_MAP.json")
CDSR_J = "../../evidence/2026-08-31-rekey/corrected/judgements.json"
OA_J = "../../evidence/2026-08-31-axis/oa_judgements.json"
OA_STATES = "../../evidence/2026-08-31-axis/oa_states_twenty.json"
OUT = "../../evidence/2026-08-31-axis/counterpart_page_map.json"


SUFFIX = re.compile(r"_(AUTO_FULL_REVIEW|AUTO_REVIEW|FULL_REVIEW|REVIEW)$")


def pages_on_disk(app_id):
    """Pages belonging to THIS topic, by exact base equality after suffix stripping.

    ⛔ NOT A PREFIX MATCH. The first version used `name.startswith(base)` and handed
    `bosentan-pah` the pages of its SIBLINGS -- `BOSENTAN_PAH_CHILDREN_REVIEW.html` and
    `BOSENTAN_PAH_MONOTHERAPY_REVIEW.html` are different topics with their own objects and
    their own counterparts. A prefix match on a topic family silently absorbs every member
    whose name extends it, and this mapping is being handed to another lane, so an
    over-match here propagates as a wrong page to score.

    ⇒ The base must be EQUAL after stripping a known suffix, never merely a prefix.
    `SOTATERCEPT_PAH_AUTO_2` is correctly excluded from `sotatercept-pah` for the same
    reason: `_AUTO_2` is not a delivery suffix, so the base does not match.
    """
    want = SUFFIX.sub("", app_id.replace("-", "_").upper())
    hits = []
    for p in glob.glob(os.path.join(ROOT, "*.html")):
        n = os.path.basename(p)
        if SUFFIX.sub("", n.upper()[:-5]) == want:
            hits.append(n)
    return sorted(hits)


def main():
    pm = {}
    if os.path.exists(PAGE_MAP):
        raw = json.load(io.open(PAGE_MAP, encoding="utf-8"))
        pm = raw if isinstance(raw, dict) else {}
    print("=== SOURCES ===")
    print("   PAGE_MAP present : %s   entries %d" % (os.path.exists(PAGE_MAP), len(pm)))

    cdsr = json.load(io.open(CDSR_J, encoding="utf-8"))
    oa = json.load(io.open(OA_J, encoding="utf-8"))
    titles = {}
    st = json.load(io.open(OA_STATES, encoding="utf-8"))
    for t in st["topics"]:
        for r in ((t.get("verified") or {}).get("rows") or []):
            titles[r["oa_id"]] = r["title"]

    pool = {}
    for j in cdsr:
        if j["label"] == "COUNTERPART":
            pool.setdefault(j["app_id"], {"cdsr": [], "oa": []})["cdsr"].append(j["cd_base"])
    for j in oa:
        if j["label"] == "COUNTERPART":
            pool.setdefault(j["app_id"], {"cdsr": [], "oa": []})["oa"].append(j["cd_base"])

    print("   topics with >=1 judged COUNTERPART: %d" % len(pool))
    print("")
    print("=== topic -> OUR PAGE -> COUNTERPART ===")
    rows, disagree, missing = [], [], []
    for app in sorted(pool):
        declared = pm.get(app)
        disk = pages_on_disk(app)
        if not declared and not disk:
            missing.append(app)
        elif declared and disk and declared not in disk:
            disagree.append((app, declared, disk))
        rec = {"app_id": app, "page_declared": declared, "pages_on_disk": disk,
               "counterparts_cdsr": sorted(set(pool[app]["cdsr"])),
               "counterparts_oa": sorted(set(pool[app]["oa"])),
               "verification_material": {"cdsr": "cochrane_objectives", "oa": "abstract"}}
        rows.append(rec)
        print("   %-34s page(declared)=%s" % (app, declared or "-"))
        print("        pages on disk : %s" % (", ".join(disk) if disk else "NONE FOUND"))
        if rec["counterparts_cdsr"]:
            print("        CDSR counterpart(s), objectives-verified : %s"
                  % ", ".join(rec["counterparts_cdsr"]))
        for b in rec["counterparts_oa"]:
            print("        OA counterpart, abstract-verified        : %-13s %s"
                  % (b, titles.get(b, "")[:64]))

    print("")
    print("=== ⛔ PAGE_MAP vs DISK ===")
    print("   topics where PAGE_MAP names a page NOT among the files on disk: %d" % len(disagree))
    for app, d, disk in disagree:
        print("      %-34s declared %-44s disk %s" % (app, d, ", ".join(disk)))
    print("   topics with NO page found by either route: %d   %s"
          % (len(missing), ", ".join(missing) if missing else ""))
    multi = [r for r in rows if len(r["pages_on_disk"]) > 1]
    print("   topics with MORE THAN ONE page on disk: %d" % len(multi))
    for r in multi:
        print("      %-34s %s" % (r["app_id"], ", ".join(r["pages_on_disk"])))
    print("   ⚠️ one object with two delivered pages has cost this project a count before;")
    print("     the ranking lane must be told WHICH page it is scoring.")

    print("")
    print("=== HANDOVER ===")
    nc = sum(len(r["counterparts_cdsr"]) for r in rows)
    no = sum(len(r["counterparts_oa"]) for r in rows)
    print("   TOPICS in the candidate pool          : %d" % len(rows))
    print("   COMPARATORS, objectives-verified (CDSR): %d" % nc)
    print("   COMPARATORS, abstract-verified (OA)    : %d" % no)
    print("   ⛔ the two are NOT pooled: different verification material, so a quality claim")
    print("     across them would compare two measurements under one name.")
    print("   ⛔ NOT RANKED HERE. tabs_with_content is another lane's instrument.")

    json.dump({"pool": rows, "page_map_vs_disk_disagreements": disagree,
               "topics_without_a_page": missing}, io.open(OUT, "w", encoding="utf-8"),
              ensure_ascii=False, indent=1)
    print("")
    print("   written: %s" % OUT)


if __name__ == "__main__":
    main()
