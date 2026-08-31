# -*- coding: utf-8 -*-
"""THE SEED, BEFORE AND AFTER, FOR ALL TWENTY TOPICS.

⛔ WHY THIS TABLE EXISTS. `search_topic.candidate_intervention` seeded the concept block
from THE FIRST CONTENT WORD OF THE TITLE. Correct for `Sacubitril/valsartan in adults...`,
wrong for `Intravenous iron...` (searched the ROUTE, 475,723 PubMed records) and for
`SGLT2 inhibitors...` (searched the PROTEIN, 16,917 -- and 16,917 is an entirely plausible
size for that literature, so nothing flagged it).

⚠️ THE DANGEROUS CASE IS THE PLAUSIBLE ONE. So this table PRINTS THE SEED ITSELF beside
every count. A reader must be able to see WHAT WAS SEARCHED, not only how much came back.
The fix was scored on the four comparison topics in
`evidence/2026-08-31-search-ids/SEED-FIX-SCORED.md`; this extends it to all twenty, which
is where a seed that is wrong in a plausible way would still be hiding.

OFFLINE HALF (this file, no network): for every topic, `seed_old` under the superseded
first-content-word rule and `seed_new` under the shipped rule, with the PROVENANCE of the
new seed. Deterministic and complete over the twenty.

NETWORK HALF (--hits): PubMed `esearch` counts for the raw seed blocks, free source, no
key. Run only for topics where the seed CHANGED, because a count for an unchanged seed is
the same count twice.
"""
import io, json, os, re, sys, time, urllib.parse, urllib.request
from collections import Counter

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, ".."))
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace",
                              line_buffering=True)
from search_topic import intervention_terms, seed_role_state, STOP     # noqa: E402

# ⭐ THE REGRESSION CONTROL. These four are the topics the seed fix was SCORED on in
# `evidence/2026-08-31-search-ids/SEED-FIX-SCORED.md`. The schedule-token and arm-role
# guards added afterwards must not move them: a later guard that silently re-narrows an
# already-measured topic would invalidate a published table without touching it.
SCORED_FOUR = {"arni-hfref": ["LCZ696", "sacubitril/valsartan"],
               "sotagliflozin-hf": None, "iv-iron-hf": None, "sglt2-hf": None}

ROOT = "F:/rapidmeta-ssot-shell"
TWENTY = os.path.join(HERE, "../../evidence/2026-08-31-rekey/corrected/twenty.json")
OUT = os.path.join(HERE, "../../evidence/2026-08-31-axis/seed_before_after_twenty.json")
EUTILS = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi"


def seed_old(obj):
    """THE SUPERSEDED RULE, reconstructed here so the BEFORE column is the rule's own
    output and not a memory of it. First content word of the title, else of the question."""
    for src in (str(obj.get("title") or ""), str(obj.get("question") or "")):
        for w in re.findall(r"[A-Za-z][A-Za-z0-9-]{3,}", src):
            if w.lower() in STOP:
                continue
            return w
    return None


def pubmed_count(terms):
    """Free source, no key. -> (count, status, query_as_sent). Never invents a number."""
    if not terms:
        return None, "NO_TERMS", ""
    q = " OR ".join('"%s"' % t if " " in t else t for t in terms)
    url = "%s?db=pubmed&retmode=json&retmax=0&term=%s" % (EUTILS, urllib.parse.quote(q))
    for attempt in range(4):
        try:
            with urllib.request.urlopen(url, timeout=45) as fh:
                d = json.loads(fh.read().decode("utf-8"))
            return int(d["esearchresult"]["count"]), "OK", q
        except Exception as e:                                  # noqa: BLE001
            if attempt == 3:
                return None, "ERROR %s" % type(e).__name__, q
            time.sleep(2 + 3 * attempt)
    return None, "ERROR", q


def main():
    do_hits = "--hits" in sys.argv
    twenty = json.load(io.open(TWENTY, encoding="utf-8"))["topics"]
    out = []
    for t in sorted(twenty, key=lambda x: x["app_id"]):
        app = t["app_id"]
        p = os.path.join(ROOT, "ssot", app, app + ".json")
        rec = {"app_id": app, "object_path": p, "object_present": os.path.exists(p)}
        if not rec["object_present"]:
            # NAMED ABSENT, never silently skipped -- an object that vanished before it was
            # counted cannot appear in any denominator derived from this table.
            rec.update({"seed_old": None, "seed_new": None, "how": "OBJECT_ABSENT",
                        "changed": None})
            out.append(rec)
            continue
        obj = json.load(io.open(p, encoding="utf-8"))
        terms, how = intervention_terms(obj)
        old = seed_old(obj)
        role_state, conflicts, _ = seed_role_state(obj)
        rec.update({"title": str(obj.get("title") or "")[:90],
                    "seed_old": old, "seed_new": terms, "how": how,
                    "seed_role_state": role_state,
                    "arm_role_conflicts": [c["term"] for c in conflicts],
                    "changed": bool(terms) and [old] != terms})
        out.append(rec)

    print("=== SEED BEFORE / AFTER, ALL TWENTY. The seed is printed, not just its count. ===")
    print("   %-46s %-22s %s" % ("app_id", "seed_old (title word)", "seed_new (object's own record)"))
    for r in out:
        if not r["object_present"]:
            print("   %-46s %-22s OBJECT ABSENT AT %s" % (r["app_id"], "-", r["object_path"]))
            continue
        new = ", ".join(r["seed_new"]) if r["seed_new"] else "(none)"
        print("   %-46s %-22s %s%s" % (r["app_id"], str(r["seed_old"])[:22], new[:78],
                                       "" if r["changed"] else "   [UNCHANGED]"))

    print("")
    print("=== PROVENANCE OF THE NEW SEED -- which source in the stated order won ===")

    c = Counter((r["how"] or "").split(" --")[0].split(",")[0] for r in out if r["object_present"])
    for k, v in c.most_common():
        print("   %2d  %s" % (v, k))
    lastresort = [r["app_id"] for r in out if (r["how"] or "").startswith("LAST RESORT")]
    print("   ⚠️ still on the LAST RESORT path (title's first word): %d   %s"
          % (len(lastresort), ", ".join(lastresort) if lastresort else "none"))
    print("   ⇒ those are the topics where the fix changed the SOURCE of the seed without")
    print("     changing its QUALITY. Named, because a respectable provenance is the harder")
    print("     failure to see.")

    changed = [r for r in out if r.get("changed")]
    print("")
    print("   seeds CHANGED by the fix : %d / %d" % (len(changed), len(out)))
    print("   seeds UNCHANGED          : %d / %d"
          % (sum(1 for r in out if r["object_present"] and not r["changed"]), len(out)))

    print("")
    print("=== ARM-ROLE STATE -- a named state, never a silent pass ===")
    c2 = Counter(r.get("seed_role_state") for r in out if r["object_present"])
    for k, v in c2.most_common():
        print("   %2d  %s" % (v, k))
    for r in out:
        if r.get("seed_role_state") == "SEED_LEADS_WITH_CONFLICT":
            print("   ⛔ %s   seed leads with %r, and %r appear in BOTH arm roles"
                  % (r["app_id"], r["seed_new"][0], r["arm_role_conflicts"]))
    named = [r["app_id"] for r in out if r.get("arm_role_conflicts")]
    print("   topics with ANY role-ambiguous term (reported, not repaired): %d   %s"
          % (len(named), ", ".join(named)))

    print("")
    print("=== REGRESSION CONTROL -- the four topics the seed fix was already SCORED on ===")
    for app, expect in sorted(SCORED_FOUR.items()):
        p = os.path.join(ROOT, "ssot", app, app + ".json")
        if not os.path.exists(p):
            print("   %-20s OBJECT ABSENT at %s -- cannot serve as a control" % (app, p))
            continue
        o = json.load(io.open(p, encoding="utf-8"))
        terms, how = intervention_terms(o)
        ok = (expect is None) or (terms == expect)
        print("   %-20s %-4s %s" % (app, "PASS" if ok else "FAIL", ", ".join(terms)[:88]))
        if expect is not None and not ok:
            print("        expected %r -- the later guards moved an already-measured topic"
                  % (expect,))

    if do_hits:
        print("")
        print("=== PubMed hits, old seed vs new seed. Free source (E-utilities), no key. ===")
        print("   Raw seed blocks, NO MeSH expansion -- this measures the SEED, not the")
        print("   procedure's full block. Only topics whose seed changed are queried.")
        print("   %-46s %10s %10s  %s" % ("app_id", "hits_old", "hits_new", "seed_new sent"))
        for r in out:
            if not r.get("changed"):
                continue
            ho, so, _ = pubmed_count([r["seed_old"]] if r["seed_old"] else [])
            time.sleep(0.4)
            hn, sn, qn = pubmed_count(r["seed_new"])
            time.sleep(0.4)
            r["hits_old"], r["hits_old_status"] = ho, so
            r["hits_new"], r["hits_new_status"] = hn, sn
            r["pubmed_query_new"] = qn
            print("   %-46s %10s %10s  %s"
                  % (r["app_id"],
                     ho if ho is not None else so, hn if hn is not None else sn, qn[:60]))

    json.dump(out, io.open(OUT, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print("")
    print("   written: %s" % OUT)


if __name__ == "__main__":
    main()
