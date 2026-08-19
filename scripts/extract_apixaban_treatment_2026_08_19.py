#!/usr/bin/env python3
"""EXTRACT the eleven recoverable trials for `apixaban-vte-treatment`, FROM SOURCE.

THESE ELEVEN ARE A GAP IN OUR OWN EVIDENCE BASE, NOT A LITERATURE GAP. Each was surfaced by our
own search, passed our own eligibility criteria, and was poolable -- and none was in the object.
`ELIGIBLE_POOLABLE_NOT_INCLUDED` exists precisely to name that state rather than let it read as
an exclusion.

    nine from the mechanical screen + two recovered by adjudication (AMPLIFY-EXT and APIDULCIS,
    the second of which the REGISTRY'S OWN `primaryPurpose` field would have sent to the wrong
    review -- it is coded PREVENTION while randomising extended anticoagulation in patients who
    have already had a VTE).

TWO RULES THIS SCRIPT ENFORCES BECAUSE BOTH WERE LEARNED THE HARD WAY TONIGHT:

  P35  THE PRIMARY IS READ BY MATCHING ITS REGISTERED TEXT, NEVER BY POSITION. `outcomeMeasures`
       is NOT ordered with the primary first -- on ADVANCE-2 element zero is a SECONDARY. Every
       posted result here is matched back to the registered primary's own string, and where no
       posted measure matches, that is reported rather than the nearest one being taken.

  P24  Every disposition this script can assign is reported with its count, including the ones
       reached zero times, so a state that cannot be reached is visible rather than silently
       absent.

AND IT READS EVERY REGISTERED RANK, not just the primaries -- the withholding question. Four
instances tonight say that trials sharing a composite's NAME rarely share its DEFINITION, so
the harmonisable estimand is as likely to be at secondary rank as at primary. Twice tonight it
was.
"""
import io
import json
import os
import sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(REPO, "ssot"))
import ctgov_transport as X                                        # noqa: E402

DEST = os.path.join(REPO, "evidence", "2026-08-19-batch1",
                    "apixaban_treatment_extraction.json")

# nine from the mechanical screen, two from adjudication. Named individually so the list is a
# record rather than a query result that could change under us.
FROM_SCREEN = ["NCT00643201", "NCT01780987", "NCT02585713", "NCT02744092", "NCT03045406",
               "NCT03196349", "NCT03266783", "NCT03590743", "NCT04168203"]
FROM_ADJUDICATION = ["NCT00633893", "NCT03678506"]


def ranks(ps):
    """[(rank, measure, description)] over EVERY registered rank."""
    om = ps.get("outcomesModule") or {}
    out = []
    for rank, key in (("PRIMARY", "primaryOutcomes"), ("SECONDARY", "secondaryOutcomes"),
                      ("OTHER", "otherOutcomes")):
        for o in (om.get(key) or []):
            out.append((rank, o.get("measure") or "", o.get("description") or ""))
    return out


def norm(s):
    return " ".join((s or "").lower().replace("-", " ").split())


def main():
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    rows, tally = [], {}
    for nct in FROM_SCREEN + FROM_ADJUDICATION:
        # hasResults MUST be requested explicitly -- it is absent from a protocolSection-only
        # payload, and its absence once made ELIGIBLE_NOT_POOLABLE unreachable (P24/P26).
        state, study, detail = X.fetch_raw(nct, fields="protocolSection,hasResults,resultsSection")
        if state != X.OK:
            rows.append({"nct": nct, "state": "NOT_ASSESSABLE", "detail": str(detail)[:160]})
            tally["NOT_ASSESSABLE"] = tally.get("NOT_ASSESSABLE", 0) + 1
            continue
        ps = study.get("protocolSection") or {}
        ident = ps.get("identificationModule") or {}
        st = (ps.get("statusModule") or {}).get("overallStatus")
        has = study.get("hasResults")
        rk = ranks(ps)
        primaries = [m for (r, m, _d) in rk if r == "PRIMARY"]
        posted = [(o.get("title") or "")
                  for o in (((study.get("resultsSection") or {})
                             .get("outcomeMeasuresModule") or {}).get("outcomeMeasures") or [])]
        # P35: match the registered primary's TEXT among the posted measures. Never element 0.
        matched, match_idx = None, None
        for i, title in enumerate(posted):
            for p in primaries:
                a, b = norm(title), norm(p)
                if a and b and (a in b or b in a or
                                len(set(a.split()) & set(b.split())) >= max(3, len(b.split()) // 2)):
                    matched, match_idx = title, i
                    break
            if matched:
                break
        disp = ("HAS_RESULTS_PRIMARY_MATCHED" if matched else
                "HAS_RESULTS_PRIMARY_NOT_MATCHED" if has else
                "NO_RESULTS_POSTED")
        tally[disp] = tally.get(disp, 0) + 1
        rows.append({
            "nct": nct,
            "acronym": ident.get("acronym") or ident.get("briefTitle", "")[:60],
            "status": st, "hasResults": has,
            "enrolment": (ps.get("designModule") or {}).get("enrollmentInfo", {}).get("count"),
            "primaryPurpose": ((ps.get("designModule") or {}).get("designInfo") or {})
                              .get("primaryPurpose"),
            "registered_primaries": primaries,
            "n_secondary": sum(1 for (r, _m, _d) in rk if r == "SECONDARY"),
            "n_other": sum(1 for (r, _m, _d) in rk if r == "OTHER"),
            "n_posted_outcome_measures": len(posted),
            "posted_titles_first_5": posted[:5],
            "primary_matched_by_text": matched,
            "matched_at_index": match_idx,
            "element_zero_is_the_primary": (match_idx == 0) if match_idx is not None else None,
            "disposition": disp,
            "source": "from the mechanical screen" if nct in FROM_SCREEN else
                      "recovered by cross-family adjudication",
        })
        print("%-13s %-14s %-10s results=%-5s ranks P/S/O=%d/%d/%d  match@%s"
              % (nct, (rows[-1]["acronym"] or "")[:14], st, has,
                 len(primaries), rows[-1]["n_secondary"], rows[-1]["n_other"],
                 match_idx if match_idx is not None else "-"))

    # P24 -- every disposition reported, including the ones reached zero times.
    for d in ("HAS_RESULTS_PRIMARY_MATCHED", "HAS_RESULTS_PRIMARY_NOT_MATCHED",
              "NO_RESULTS_POSTED", "NOT_ASSESSABLE"):
        tally.setdefault(d, 0)
    print("\nDISPOSITIONS (every state this script can assign, including those reached zero "
          "times)")
    for k in sorted(tally):
        print("   %-34s %d" % (k, tally[k]))

    zero_idx = [r for r in rows if r.get("element_zero_is_the_primary") is False]
    if zero_idx:
        print("\nP35 EARNS ITS PLACE AGAIN -- %d trial(s) where the registered primary is NOT "
              "element zero\nof the posted outcome measures:" % len(zero_idx))
        for r in zero_idx:
            print("   %s matched at index %d, not 0" % (r["nct"], r["matched_at_index"]))

    with io.open(DEST, "w", encoding="utf-8") as fh:
        fh.write(json.dumps({"extracted_utc": "2026-08-19",
                             "topic": "apixaban-vte-treatment",
                             "n": len(rows), "tally": tally, "trials": rows}, indent=1))
    print("\nwrote %s" % DEST)
    return 0


if __name__ == "__main__":
    sys.exit(main())
