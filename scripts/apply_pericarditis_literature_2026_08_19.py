#!/usr/bin/env python3
"""APPLY THE PERICARDITIS LITERATURE LIMB to the object and rebuild its page.

WHAT CHANGES, AND IT IS THE HEADLINE. The object said
`NO_ESTIMATE_POSSIBLE_NOTHING_HAS_REPORTED`. That was TRUE OF THE REGISTRY and FALSE OF THE
WORLD: four of the five trials are published, three of them in Ann Intern Med, NEJM and Lancet.

    A REGISTRY IS AN INDEX. "An absence reported by an index is not an absence in the world"
    was written about PAGE_MAP eight hours ago; ClinicalTrials.gov's results section is the same
    kind of object, and the same sentence applies to it. `ELIGIBLE_COMPLETED_NO_RESULTS_POSTED`
    is a statement about a database, not about a literature.

AND THE POOL IS STILL REFUSED, but now on evidence rather than on silence. The three
recurrence-type trials are three DIFFERENT DISEASE STAGES -- first attack (ICAP), first
recurrence (CORP), multiple recurrences (CORP-2) -- and ICAP's published primary counts
INCESSANT disease, which the other two do not. The registry's outcome-title field showed none of
that; all three read "Recurrence rate at 18 months".

WHAT IS NOT DONE. No pool is computed. Pooling across disease stage is a declarable judgement,
not a title match, and it is owed as its own decision.
"""
import io
import json
import os
import sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import build_colchicine_readings_2026_08_19 as B                        # noqa: E402

TOPIC = "colchicine-pericarditis"
PATH = os.path.join(REPO, "ssot", TOPIC, TOPIC + ".json")
EXTRACT = os.path.join(REPO, "evidence", "2026-08-19-batch1",
                       "pericarditis_publication_extraction.json")

LIMBS = [
    {"property": "P37",
     "finding": ("THE REGISTERED TITLES MATCH AND THE ENDPOINTS DO NOT. All three recurrence "
                 "trials register 'Recurrence rate at 18 months'. ICAP's PUBLISHED primary is "
                 "'incessant or recurrent pericarditis' -- it counts INCESSANT disease, which "
                 "CORP and CORP-2 do not. Read from the papers, not the registry.")},
    {"property": "P43",
     "finding": ("THREE DIFFERENT DISEASE STAGES UNDER ONE TITLE. ICAP (NCT00128453) randomised "
                 "a FIRST ATTACK of acute pericarditis; CORP (NCT00128414) a FIRST RECURRENCE; "
                 "CORP-2 (NCT00235079) MULTIPLE recurrences. The population is part of the "
                 "estimand and the registry's outcome-title field carries none of it.")},
]


def run(apply_it):
    with io.open(EXTRACT, "r", encoding="utf-8") as fh:
        ex = json.load(fh)
    with io.open(PATH, "r", encoding="utf-8") as fh:
        o = json.load(fh)
    by = {t["nct"]: t for t in ex["trials"]}
    pr = o["results"]["by_outcome"]["primary"]

    before = pr["estimand_screen_verdict"]
    n_pub = 0
    for t in o["inputs"]["trials"]:
        e = by.get(t["nct"])
        if not e:
            t["published_report"] = {
                "state": "NONE_FOUND",
                "why": ("No publication is listed on the registration and none was resolved. "
                        "Reported as unresolved, never approximated."),
            }
            continue
        n_pub += 1
        t["pmid"] = e["pmid"]
        t["pmid_state"] = "RESOLVED from the registration's own references, confirmed via PubMed"
        t["published_report"] = {
            "state": "PUBLISHED",
            "citation": e["citation"], "pmid": e["pmid"], "doi": e["doi"],
            "according_to": "PubMed, retrieved 2026-08-19",
            "population_as_the_paper_states_it": e["population_as_the_paper_states_it"],
            "primary_outcome_as_the_paper_states_it":
                e["primary_outcome_as_the_paper_states_it"],
            "extracted_cells": e["cells"],
            "extraction_state": e["extraction_state"],
        }

    pr["estimand_screen_verdict"] = "POOL_NOT_ADMISSIBLE"
    pr["failing_limbs"] = LIMBS
    pr["k_with_published_reports"] = n_pub
    pr["poolable_reason"] = " ".join("[%s] %s" % (f["property"], f["finding"]) for f in LIMBS)
    pr["absent_is_not_zero"] = (
        "SUPERSEDED BY THE LITERATURE LIMB, and the supersession is the finding. This object "
        "previously recorded NO_ESTIMATE_POSSIBLE_NOTHING_HAS_REPORTED, which was TRUE OF THE "
        "REGISTRY and FALSE OF THE WORLD: %d of %d trials are published, three of them in Ann "
        "Intern Med, NEJM and Lancet. A REGISTRY IS AN INDEX, and an absence reported by an "
        "index is not an absence in the world."
        % (n_pub, len(o["inputs"]["trials"])))
    pr["previous_verdict_before_the_literature_limb"] = before
    pr["pooled"]["absent_reason"] = (
        pr["poolable_reason"] + " NO POOL IS COMPUTED: combining across disease stage is a "
        "declarable judgement, not a title match, and it is owed as its own decision.")
    pr["what_this_verdict_does_not_establish"] = (
        "NOT that colchicine is ineffective in pericarditis -- each published trial reports a "
        "reduction on its own endpoint in its own population. NOT that these trials can never "
        "be combined: a pool across disease stage may well be defensible, but it must be "
        "DECLARED on a named axis rather than inherited from three identical registry titles.")
    o["screening"]["registries_and_limbs_not_searched"] = (
        "The PubMed limb has now been run FOR THIS READING and its five trials only; 523 "
        "colchicine records remain unscreened across the other readings. ANZCTR was never "
        "searched, and LoDoCo2 is registered there.")
    o["sources"]["literature_extraction"] = (
        "evidence/2026-08-19-batch1/pericarditis_publication_extraction.json")
    o["verification_basis"]["what_verifies_this_object"] = (
        "ClinicalTrials.gov protocol records read 2026-08-19 at every registered rank, AND the "
        "published reports of four of the five trials, read cell by cell with each number's "
        "quote and location recorded. Bibliographic detail according to PubMed.")

    print("  verdict %s -> %s" % (before, pr["estimand_screen_verdict"]))
    print("  published reports resolved: %d of %d" % (n_pub, len(o["inputs"]["trials"])))
    for f in LIMBS:
        print("     %s  %s" % (f["property"], f["finding"][:88]))

    if not apply_it:
        print("\nDRY RUN -- nothing written. Re-run with --apply.")
        return 0

    with io.open(PATH, "w", encoding="utf-8", newline="") as fh:
        fh.write(json.dumps(o, indent=1, ensure_ascii=False))

    scr = json.load(io.open(os.path.join(REPO, "evidence", "2026-08-19-batch1",
                                         "colchicine_split_screening.json"), encoding="utf-8"))
    disp = {r["nct"]: r["disposition"] for r in scr["rows"]}
    spec = B.READINGS["PERICARD"]
    sibs = [(B.READINGS[r]["page"], B.READINGS[r]["title"])
            for r in B.READINGS if r != "PERICARD"]
    html = B.page_html(spec, o, disp, sibs)
    # PUBLISHED REPORTS ARE ADDED TO THE PAGE, not left only in the object.
    rows = []
    for t in o["inputs"]["trials"]:
        p = t.get("published_report") or {}
        if p.get("state") != "PUBLISHED":
            rows.append("<tr><td><code>%s</code></td><td colspan='3'>%s</td></tr>"
                        % (B.esc(t["nct"]), B.esc(p.get("why") or "no report resolved")))
            continue
        cells = "; ".join(
            "%s = %s" % (B.esc(k), B.esc(c.get("value")))
            for k, c in p["extracted_cells"].items() if c.get("value") is not None)
        miss = [k for k, c in p["extracted_cells"].items()
                if c.get("value") is None]
        rows.append(
            "<tr><td><code>%s</code></td><td>%s<br><span class='sub'>%s</span></td>"
            "<td>%s</td><td>%s%s</td></tr>"
            % (B.esc(t["nct"]), B.esc(p["citation"]),
               "PMID %s &middot; doi %s &middot; according to PubMed"
               % (B.esc(p["pmid"]), B.esc(p["doi"])),
               B.esc(p["population_as_the_paper_states_it"]["value"]),
               cells,
               ("<br><span class='sub'>NOT STATED in the source read: %s</span>"
                % B.esc(", ".join(miss))) if miss else ""))
    block = (
        "<h2>The published reports</h2>"
        "<p>Bibliographic detail and abstracts <b>according to PubMed</b>, retrieved "
        "2026-08-19. This is the first literature-limb extraction in this corpus and was done "
        "cell by cell: every number records the quote and location it came from, and "
        "<b>nothing is computed from another cell</b> &mdash; a percentage is not turned into a "
        "count, and a total is not split into arms.</p>"
        "<div class='wrap'><table><thead><tr><th>Registration</th><th>Report</th>"
        "<th>Population as the paper states it</th><th>Extracted cells</th></tr></thead>"
        "<tbody>%s</tbody></table></div>" % "".join(rows))
    html = html.replace("<h2>What was and was not searched</h2>",
                        block + "<h2>What was and was not searched</h2>")
    with io.open(os.path.join(REPO, spec["page"]), "w", encoding="utf-8", newline="") as fh:
        fh.write(html)
    print("\n  rewrote %s (%d bytes)" % (spec["page"], len(html.encode("utf-8"))))
    return 0


if __name__ == "__main__":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    sys.exit(run("--apply" in sys.argv))
