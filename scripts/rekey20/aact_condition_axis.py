# -*- coding: utf-8 -*-
"""A CONDITION AXIS SOURCED FROM THE REGISTRY, not parsed from a title. Alongside.

⛔ THE RULE IS FROZEN. `rekey_rule.py` and `axis_states.py` are untouched, and the
intervention axis is byte-identical to the incumbent's. Only the CONDITION terms change
source, and both columns are published.

⭐ WHY THIS SOURCE AND NOT ANOTHER. The ceiling of 18 is set by two topics whose
`condition_span` is null because their TITLES carry no condition connective --
`"Apixaban thromboprophylaxis: four trials, four different primary composites…"` and
`"Evolocumab Ascvd Auto2"`. Both carry NCT ids, and AACT holds `conditions` and
`browse_conditions` as TYPED ROWS keyed by nct_id. A registry row exists where a parsed
string does not.

⭐⭐ AND IT CARRIES PROVENANCE, WHICH MeSH DID NOT. Every term here traces to a named table,
a named nct_id, and an NCT the OBJECT ITSELF includes (R4). That is checkable rather than
trusted -- the thing that was missing when an unverified MeSH record expanded
`supraventricular` into `Tachycardia, Ventricular`.

⛔⛔ THE DATA DATE, NEVER THE FOLDER NAME. `aact_snapshot_guard` records that folder
`2026-04-12` holds data ending `2026-04-08`. Folder `2026-08-30` holds data to `2026-08-27`.
Citing the label would misdate every claim by three days, and a claim about a registry is a
claim about a version.

⚠️ THE RISK, NAMED IN THE PRE-REGISTRATION: `browse_conditions` is MeSH-derived and skews
BROAD, and a thromboprophylaxis trial may be registered under the SURGERY rather than the
clot. A non-empty but WRONG axis is worse than an empty one, so per-term hit counts and the
provenance trail are printed for every term.
"""
import io
import json
import os
import re
import sys
from collections import Counter, OrderedDict

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
os.chdir(HERE)
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace",
                              line_buffering=True)
from rekey_rule import norm, contains, STOP, _stem                      # noqa: E402
from axis_match import prepare, terms_for, sha_set                      # noqa: E402
from axis_states import MATCHED                                         # noqa: E402

FRAME = "F:/claude-temp/pend/cdsr_frame_cardiology.jsonl"
AACT_ROOT = "F:/AACT-storage/AACT"
SNAPSHOT_FOLDER = "2026-08-30"
GUARD = "F:/AACT-storage"
ROOT = "F:/rapidmeta-ssot-shell"
CORR = "../../evidence/2026-08-31-rekey/corrected"
INCUMBENT = "../../evidence/2026-08-31-axis/axis_states_twenty.json"
OUT = "../../evidence/2026-08-31-axis/aact_condition_axis_twenty.json"

MUST_SURVIVE = ["CD004434", "CD006681", "CD014808", "CD015003"]
R3_MAX_FRACTION = 0.25


def data_date():
    """The date the DATA stops, read through the peer lane's guard. Never the folder name."""
    sys.path.insert(0, GUARD)
    from aact_snapshot_guard import Snapshot          # noqa: E402
    return Snapshot.load(SNAPSHOT_FOLDER).data_date


def read_table(name, want_cols):
    """AACT pipe/tab-delimited export -> list of dicts for the requested columns."""
    path = os.path.join(AACT_ROOT, SNAPSHOT_FOLDER, name)
    if not os.path.exists(path):
        raise SystemExit("%s\n  rule: the snapshot does not carry %s, so a condition axis "
                         "from it cannot be built. FAILING CLOSED rather than returning an "
                         "empty axis, which downstream reads as 'no conditions'\n"
                         "  found by: rekey20/aact_condition_axis.py" % (path, name))
    rows = []
    with io.open(path, encoding="utf-8", errors="replace") as fh:
        header = fh.readline().rstrip("\n").split("|")
        idx = {c: header.index(c) for c in want_cols if c in header}
        if len(idx) != len(want_cols):
            raise SystemExit("%s\n  rule: expected columns %s, header has %s\n"
                             "  found by: rekey20/aact_condition_axis.py"
                             % (path, want_cols, header[:12]))
        for line in fh:
            p = line.rstrip("\n").split("|")
            if len(p) <= max(idx.values()):
                continue
            rows.append({c: p[i] for c, i in idx.items()})
    return rows


def object_ncts(app):
    p = os.path.join(ROOT, "ssot", app, app + ".json")
    if not os.path.exists(p):
        return []
    o = json.load(io.open(p, encoding="utf-8"))
    out = []
    for tr in ((o.get("inputs") or {}).get("trials") or []):
        for v in (tr.get("id"), tr.get("nct"), tr.get("name")):
            if isinstance(v, str):
                out += re.findall(r"NCT\d{8}", v)
    return sorted(set(out))


def terms_from(names):
    """Condition names -> normalised match terms, phrase and content words."""
    terms = OrderedDict()
    for n in names:
        p = norm(n).strip()
        if p:
            terms.setdefault(p, set()).add(n)
        for w in p.split():
            if w not in STOP and len(w) > 3:
                terms.setdefault(_stem(w), set()).add(n)
    return terms


def main():
    dd = data_date()
    rows, reviews = prepare(FRAME)
    twenty = json.load(io.open(os.path.join(CORR, "twenty.json"), encoding="utf-8"))["topics"]
    inc = {t["app_id"]: t for t in json.load(io.open(INCUMBENT, encoding="utf-8"))["topics"]}

    print("=== REF ===")
    print("   frame            %s   %d reviews" % (sha_set(r["cd_base"] for r in rows)[:16],
                                                   len(reviews)))
    print("   rule             FROZEN -- a COLUMN, not a rule change")
    print("   AACT folder      %s" % SNAPSHOT_FOLDER)
    print("   ⛔ AACT DATA DATE %s   <- every claim below is about THIS version" % dd)
    print("")

    cond = read_table("conditions.txt", ["nct_id", "name"])
    brow = read_table("browse_conditions.txt", ["nct_id", "mesh_term"])
    by_nct = {}
    for r in cond:
        by_nct.setdefault(r["nct_id"], []).append(("conditions", r["name"]))
    for r in brow:
        by_nct.setdefault(r["nct_id"], []).append(("browse_conditions", r["mesh_term"]))
    print("=== SNAPSHOT LOADED ===")
    print("   conditions.txt        rows %d" % len(cond))
    print("   browse_conditions.txt rows %d" % len(brow))
    print("   NCTs with >=1 condition row: %d" % len(by_nct))
    print("")

    out, prov, unresolved = [], [], []
    for t in sorted(twenty, key=lambda x: x["app_id"]):
        app = t["app_id"]
        dt, ct, _ = terms_for(t.get("drug") or {})
        iterms = sorted(set(dt) | set(ct))
        ncts = object_ncts(app)
        # R4 -- every term traces to a typed row for an NCT THE OBJECT INCLUDES.
        names, missing = [], []
        for n in ncts:
            got = by_nct.get(n)
            if not got:
                missing.append(n)
                continue
            for table, val in got:
                names.append((n, table, val))
        if missing:
            unresolved.append((app, missing))
        terms = terms_from([v for _n, _tb, v in names])
        rec = {"app_id": app, "ncts": ncts, "ncts_not_in_snapshot": missing,
               "incumbent_state": inc[app]["state"],
               "incumbent_condition_terms": t.get("condition_terms") or [],
               "aact_terms": list(terms.keys()),
               "aact_term_provenance": {k: sorted(v) for k, v in terms.items()}}

        if not iterms or not terms:
            rec.update({"aact_state": "REFUSED_NO_TERMS", "axis_condition_aact": None,
                        "verified_aact": []})
            out.append(rec)
            continue

        need = min(2, len(terms))
        keys = list(terms.keys())
        ch = [r for r in reviews
              if len([k for k in keys if contains(r["_all"], k)]) >= need]
        ih = [r for r in ch if any(contains(r["_all"], x) for x in iterms)]
        ver = [r["cd_base"] for r in ih
               if r["_obj"] is not None
               and any(contains(r["_obj"], x) for x in iterms)
               and len([k for k in keys if contains(r["_obj"], k)]) >= need]
        rec.update({"aact_state": MATCHED if ver else "not_matched", "need": need,
                    "axis_condition_aact": {"n": len(ch),
                                            "frac": round(len(ch) / float(len(reviews)), 4)},
                    "verified_aact": sorted(ver), "verified_aact_sha": sha_set(ver)})
        out.append(rec)
        for k in keys:
            prov.append((app, k, sum(1 for r in reviews if contains(r["_all"], k))))

    print("=== title axis -> AACT axis, PER TOPIC. Both columns published. ===")
    print("   %-46s %-22s %7s %9s %s"
          % ("app_id", "incumbent state", "condC t", "condC aact", "verified t -> aact"))
    for r in out:
        a = (inc[r["app_id"]].get("axis_condition") or {})
        iv = (inc[r["app_id"]].get("verified") or {})
        b = r["axis_condition_aact"]
        tag = ""
        if not r["incumbent_condition_terms"]:
            tag = "   <- WAS BLOCKED (no title condition)"
        print("   %-46s %-22s %7s %9s   %s -> %d%s"
              % (r["app_id"], r["incumbent_state"], a.get("n", "-"),
                 ("%d %2.0f%%" % (b["n"], 100 * b["frac"])) if b else "-",
                 iv.get("n", 0) if iv else 0, len(r["verified_aact"]), tag))

    print("")
    print("=== ⭐ THE TWO BLOCKED TOPICS ===")
    for r in out:
        if r["incumbent_condition_terms"]:
            continue
        print("   %s" % r["app_id"])
        print("      NCTs in the object      : %d   %s" % (len(r["ncts"]), ", ".join(r["ncts"])))
        print("      not in the snapshot     : %s" % (r["ncts_not_in_snapshot"] or "none"))
        print("      AACT terms derived      : %d" % len(r["aact_terms"]))
        b = r["axis_condition_aact"]
        print("      condition axis          : %s" % (("%d rows (%.0f%%)"
              % (b["n"], 100 * b["frac"])) if b else "REFUSED_NO_TERMS"))
        for k in r["aact_terms"][:8]:
            src = r["aact_term_provenance"][k][:2]
            print("         %-34s <- %s" % (k, "; ".join(src)))

    print("")
    print("=== R4 PROVENANCE -- NCTs the object includes that the snapshot does not hold ===")
    print("   topics with an unresolved NCT: %d" % len(unresolved))
    for app, m in unresolved:
        print("      %-46s %s" % (app, ", ".join(m)))

    print("")
    print("=== EVERY AACT TERM WITH ITS OWN HIT COUNT ===")
    live = [x for x in prov if x[2] > 0]
    print("   terms %d   live %d   dead %d" % (len(prov), len(live), len(prov) - len(live)))
    for app, k, n in sorted(live, key=lambda x: -x[2])[:12]:
        print("      %-40s %-30s %5d" % (app, k[:30], n))

    print("")
    print("=== ⛔ REGRESSION R1-R5 ===")
    trips = []
    for r in out:
        iv = (inc[r["app_id"]].get("verified") or {})
        if inc[r["app_id"]]["state"] == MATCHED and not r["verified_aact"]:
            trips.append(("R1", "%s was MATCHED on the title axis and is not on AACT"
                          % r["app_id"]))
        lost = set(iv.get("bases", [])) - set(r["verified_aact"])
        keep = [b for b in MUST_SURVIVE if b in lost]
        if keep:
            trips.append(("R2", "%s loses %s" % (r["app_id"], ", ".join(keep))))
        b = r["axis_condition_aact"]
        if b and b["frac"] > R3_MAX_FRACTION:
            trips.append(("R3", "%s AACT axis is %.0f%% of the frame"
                          % (r["app_id"], 100 * b["frac"])))
    print("   R1 no MATCHED topic may become unmatched")
    print("   R2 %s must all survive" % " ".join(MUST_SURVIVE))
    print("   R3 no condition axis above %.0f%% of the frame" % (100 * R3_MAX_FRACTION))
    print("   R4 every term traces to a typed AACT row for an NCT the object includes")
    print("   R5 ALONGSIDE -- both columns published, incumbent not removed")
    print("")
    if trips:
        print("   ⛔ TRIPPED %d:" % len(trips))
        for k, m in trips[:14]:
            print("      %-3s %s" % (k, m))
        if len(trips) > 14:
            print("      … and %d more" % (len(trips) - 14))
        print("")
        print("   ⇒ THE AACT AXIS IS NOT ADOPTED. The incumbent title axis stands.")
    else:
        print("   no criterion tripped -- and that is still not an adoption without a")
        print("   judgement on every new verified pair.")

    print("")
    print("=== CEILING ===")
    unblocked = [r["app_id"] for r in out
                 if not r["incumbent_condition_terms"] and r["axis_condition_aact"]]
    print("   topics previously unreachable for want of a condition: 2")
    print("   now carrying a registry-sourced condition axis        : %d   %s"
          % (len(unblocked), ", ".join(unblocked) if unblocked else "none"))
    print("   ⇒ ceiling 18 -> %d" % (18 + len(unblocked)))
    print("   ⚠️ a reachable topic is NOT a topic with a counterpart. The measured count is")
    print("     unchanged until a pair is judged, and judging is the unreliable stage.")

    json.dump({"aact_folder": SNAPSHOT_FOLDER, "aact_data_date": dd,
               "trips": trips, "topics": out},
              io.open(OUT, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print("")
    print("   written: %s" % OUT)


if __name__ == "__main__":
    main()
