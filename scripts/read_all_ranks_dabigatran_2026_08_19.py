#!/usr/bin/env python3
"""ASK THE WITHHOLDING QUESTION AT EVERY REGISTERED RANK, for the four dabigatran readings.

WHY. `scripts/lint_withholding_asked.py` refused the split: three successors declined to pool
having read only `primaryOutcomes[0]`. That refusal is P17 -- a refusal to pool that never
looked below the primary -- and it is not a formality. Twice tonight the harmonisable estimand
WAS a secondary: `sglt2-hf`, and `apixaban-vte-prophylaxis` where a shared secondary across four
trials replaced a k=1 figure that measured BLEEDING.

WHAT THIS DOES. For every trial in every reading it reads PRIMARY, SECONDARY and OTHER outcome
measures from the registration, records them verbatim, and then asks the question the primary
screen could not:

    IS THERE ANY ENDPOINT, AT ANY RANK, SHARED BY TWO OR MORE TRIALS THAT HAVE REPORTED
    AND THAT RANDOMISED AGAINST THE SAME COMPARATOR FAMILY?

Matching is on EXACT normalised title text -- case-folded and whitespace-collapsed, nothing
more. Loosening it would be comparing endpoints by their names, which is the error P37 exists to
name. An exact match is a LOWER BOUND and is reported as one.

WHAT A HIT WOULD AND WOULD NOT MEAN. A shared title at a shared comparator is a CANDIDATE, not a
pool. The components still have to be read, the analysis sets still have to line up, and no
estimate is computed here. What it does foreclose is a refusal to pool that never asked.
"""
import io
import json
import os
import sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(REPO, "ssot"))
import ctgov_transport as X                                             # noqa: E402

EV = os.path.join(REPO, "evidence", "2026-08-19-batch1")
OUT = os.path.join(EV, "dabigatran_vte_all_ranks.json")


def norm(t):
    return " ".join((t or "").lower().split())


def read_ranks(nct):
    st, s, detail = X.fetch_raw(nct, fields="protocolSection")
    if st != X.OK:
        return {"nct": nct, "state": "UNREACHABLE", "why": str(detail)[:160]}
    om = ((s.get("protocolSection") or {}).get("outcomesModule") or {})
    out = {"nct": nct, "state": "READ", "all_ranks_read_utc": "2026-08-19",
           "source_field": "protocolSection.outcomesModule (all ranks)",
           "source_url": "https://clinicaltrials.gov/study/%s" % nct}
    for key, field in (("registered_primaries", "primaryOutcomes"),
                       ("registered_secondaries", "secondaryOutcomes"),
                       ("registered_other_outcomes", "otherOutcomes")):
        out[key] = [o.get("measure") for o in (om.get(field) or [])]
    out["ranks_read"] = 3
    out["n_endpoints_at_all_ranks"] = sum(
        len(out[k]) for k in ("registered_primaries", "registered_secondaries",
                              "registered_other_outcomes"))
    return out


def shared_at_any_rank(members, ranks):
    """Endpoint titles shared by >=2 of `members`, at ANY rank. Exact normalised match only."""
    seen = {}
    for nct in members:
        r = ranks.get(nct) or {}
        if r.get("state") != "READ":
            continue
        titles = set()
        for k in ("registered_primaries", "registered_secondaries",
                  "registered_other_outcomes"):
            for t in r.get(k) or []:
                if norm(t):
                    titles.add((norm(t), k))
        for t, rank in titles:
            seen.setdefault(t, {})[nct] = rank
    return {t: v for t, v in seen.items() if len(v) >= 2}


def run():
    screen = json.load(io.open(os.path.join(EV, "dabigatran_vte_screening.json"),
                               encoding="utf-8"))
    est = json.load(io.open(os.path.join(EV, "dabigatran_vte_estimand_screen.json"),
                            encoding="utf-8"))

    disp = {r["nct"]: r["disposition"] for r in screen["rows"]}
    result = {"read_utc": "2026-08-19",
              "question_this_answers": (
                  "Is there any endpoint, at ANY registered rank, shared by two or more trials "
                  "that have REPORTED and that randomised against the SAME comparator family? "
                  "A refusal to pool that never asked this is a withholding (P17)."),
              "matching": ("EXACT normalised title -- case-folded, whitespace-collapsed. "
                           "Nothing looser, because comparing endpoints by name is the error "
                           "P37 names. Therefore a LOWER BOUND."),
              "readings": {}, "ranks": {}}

    for name in ("TREATMENT", "EXTENDED", "SURGICAL", "CEREBRAL"):
        v = est["readings"][name]
        trials = [t for t in v.get("trials", []) if t.get("state") == "READ"]
        fams = {}
        for t in trials:
            for f in t.get("comparator_families_present") or []:
                fams.setdefault(f, []).append(t["nct"])

        for t in trials:
            if t["nct"] not in result["ranks"]:
                result["ranks"][t["nct"]] = read_ranks(t["nct"])

        rows = []
        for fam, ncts in sorted(fams.items()):
            reported = [n for n in ncts if disp.get(n) == "ELIGIBLE_WITH_RESULTS"]
            if len(reported) < 2:
                rows.append({"comparator_family": fam, "k_with_posted_results": len(reported),
                             "state": "NOT_ASSESSABLE",
                             "why": ("Fewer than two trials in this comparator family have "
                                     "posted results, so no shared endpoint can be pooled "
                                     "whatever the registrations declare.")})
                continue
            sh = shared_at_any_rank(reported, result["ranks"])
            rows.append({
                "comparator_family": fam,
                "k_with_posted_results": len(reported),
                "members_with_results": sorted(reported),
                "n_endpoints_shared_at_any_rank": len(sh),
                "shared": [{"title": t, "trials": v2} for t, v2 in sorted(sh.items())][:40],
                "state": "CANDIDATES_FOUND" if sh else "NOTHING_SHARED_AT_ANY_RANK",
                "what_a_candidate_is": (
                    "A shared title at a shared comparator is a CANDIDATE, not a pool. The "
                    "components still have to be read and no estimate is computed here."),
            })
        result["readings"][name] = {"by_comparator_family": rows}

        print("\n== %s" % name)
        for r in rows:
            if r["state"] == "NOT_ASSESSABLE":
                print("   %-18s k_reported=%d  NOT_ASSESSABLE"
                      % (r["comparator_family"], r["k_with_posted_results"]))
                continue
            print("   %-18s k_reported=%d  shared_at_any_rank=%d  %s"
                  % (r["comparator_family"], r["k_with_posted_results"],
                     r["n_endpoints_shared_at_any_rank"], r["state"]))
            for s in r["shared"][:6]:
                ranks = sorted(set(s["trials"].values()))
                print("        %-70s %s" % (s["title"][:70], ",".join(
                    x.replace("registered_", "") for x in ranks)))

    with io.open(OUT, "w", encoding="utf-8", newline="") as fh:
        fh.write(json.dumps(result, indent=1, ensure_ascii=False))
    print("\nwrote %s" % os.path.relpath(OUT, REPO))
    return 0


def selftest():
    fails = []

    def ck(n, got, want):
        ok = got == want
        print("  %-64s %s  %r" % (n, "ok" if ok else "FAIL", got))
        if not ok:
            fails.append(n)

    ranks = {
        "A": {"state": "READ", "registered_primaries": ["Recurrent VTE"],
              "registered_secondaries": ["Major bleeding", "All-cause death"]},
        "B": {"state": "READ", "registered_primaries": ["Something else entirely"],
              "registered_secondaries": ["MAJOR   BLEEDING"]},
        "C": {"state": "UNREACHABLE"},
    }
    print("1. A SHARED ENDPOINT IS FOUND BELOW THE PRIMARY, which is the whole point:")
    sh = shared_at_any_rank(["A", "B"], ranks)
    ck("one shared title", sorted(sh), ["major bleeding"])
    ck("...and it is a SECONDARY in both",
       sorted(set(sh["major bleeding"].values())), ["registered_secondaries"])

    print("\n2. MATCHING IS EXACT AFTER NORMALISATION, and no looser:")
    ck("case and whitespace fold", norm("MAJOR   BLEEDING"), "major bleeding")
    ck("but 'Recurrent VTE' does not match 'Recurrent VTE at 6 months'",
       norm("Recurrent VTE") == norm("Recurrent VTE at 6 months"), False)

    print("\n3. AN UNREADABLE REGISTRATION CONTRIBUTES NOTHING, rather than a false match:")
    ck("C is skipped", shared_at_any_rank(["A", "C"], ranks), {})

    print("\n%s" % ("SELFTEST FAILED: %s" % fails if fails else "SELFTEST PASSED"))
    return 1 if fails else 0


if __name__ == "__main__":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    sys.exit(selftest() if "--selftest" in sys.argv else run())
