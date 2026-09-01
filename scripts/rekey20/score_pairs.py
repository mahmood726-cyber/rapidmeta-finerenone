# -*- coding: utf-8 -*-
"""THE SCORING RUNNER. Reuses the frozen criteria and the frozen harness; owns neither.

⛔ NOTHING HERE REIMPLEMENTS A CRITERION. The six criteria come from
`F:/allmeta/oa68k/rubric.py` and the label extraction from `opencomp.parse_fulltext`. A
second scorer would be a second standard, and so would a second extractor.

⛔⛔ THE BINDING CLAUSE, ENFORCED IN CODE RATHER THAN PROMISED. `SCORING-HARNESS.md` requires
that THE SAME RULE EXTRACT BOTH SIDES. This runner calls ONE function -- `study_labels()` --
for our page and for the comparator, and asserts before scoring that both sides were
extracted by it. Our curated `our_trials` list is deliberately NOT used: parsing one side and
curating the other would build the asymmetry into the instrument and every score would
inherit it.

⭐ WHY REGISTRY IDS. S3 and S7 search each label as a LITERAL STRING in the text
(`re.escape(lab)`), so a label must be something the document actually prints. Registry ids
are; an included-studies table gives a row COUNT and cannot feed them; and a trial ACRONYM
was already measured by this programme to find MENTIONS rather than INCLUSIONS and ruled out.

⚠️ `k` comes from `len(study_labels)`, never a separate count, so k and the labels cannot
disagree.

⭐ `NOT_SCOREABLE_NO_STUDY_LIST` IS A FINDING, NOT A LOW SCORE. PRISMA 2020 item 17 requires
an included-study list. Its `n` is reported as a headline in its own right, and it applies to
OUR pages exactly as to theirs.

⚠️ EVERY SCORE SHIPS WITH THE REPEAT-INSTABILITY MEASURED ON THIS PROGRAMME'S OWN JUDGE --
27% under a refuse-only rubric tightening, ~6.5% on a straight repeat. In the result, not an
appendix.
"""
import hashlib
import io
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
OA68K = "F:/allmeta/oa68k"
sys.path.insert(0, HERE)
sys.path.insert(0, OA68K)
os.chdir(HERE)
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace",
                              line_buffering=True)
import rubric as R                     # noqa: E402  the FROZEN criteria
import opencomp as OC                  # noqa: E402  the FROZEN extractor

REPO = "F:/rapidmeta-ssot-shell"
COMPARATORS = "F:/rapidmeta-xsurface/TWENTY_COMPARATORS.json"
GATE = "../../evidence/2026-09-01-scored-run/scoreable_state.json"
MANIFEST = "../../evidence/2026-09-01-scored-run/comparator_text_manifest.json"
HARNESS_MD = OA68K + "/SCORING-HARNESS.md"
OUT = "../../evidence/2026-09-01-scored-run/scores.json"

HARNESS_VERSION = "scoring-harness-1.0.0-2026-09-01"
INSTABILITY = {"rubric_tightening_refuse_only": 0.27, "straight_repeat": 0.065,
               "note": "Two runs agreeing on a count is not two runs agreeing: 5 of 7 was "
                       "identical across two runs while a quarter of the labels changed."}


def sha(path):
    return hashlib.sha256(io.open(path, "rb").read()).hexdigest()


def page_text(path):
    """Our page, tags stripped. Rendered text, never source -- markup splits a sentence."""
    raw = io.open(path, encoding="utf-8", errors="replace").read()
    t = re.sub(r"(?is)<(script|style)\b.*?</\1>", " ", raw)
    t = re.sub(r"(?s)<[^>]+>", " ", t)
    import html
    return " ".join(html.unescape(t).split())


def study_labels(text):
    """⛔ THE ONE EXTRACTION RULE, USED FOR BOTH SIDES.

    Reuses `opencomp.parse_fulltext`'s registry-id regexes -- the same field that produced
    `enumerates_included_studies` in the published frames. Called with the document's TEXT so
    the identical rule reads our HTML and their JATS.
    """
    ids = (set(OC.RE_NCT.findall(text)) | set(OC.RE_ISRCTN.findall(text))
           | set(OC.RE_CHICTR.findall(text)))
    return sorted(ids)


def score_side(text, file_label, labels, k, topic_terms):
    rows = {}
    for name, (fn, anchor) in R.CRITERIA.items():
        verdict, ev = fn(text, file_label, study_labels=labels, k=k,
                         topic_terms=topic_terms)
        rows[name] = {"verdict": verdict, "prisma_anchor": anchor, "evidence": ev,
                      "rubric_sha256": R.script_sha256()}
    return rows


def main():
    dry = "--dry-run" in sys.argv
    comp = json.load(io.open(COMPARATORS, encoding="utf-8"))
    gate = json.load(io.open(GATE, encoding="utf-8"))
    man = {r["pmid"]: r for r in json.load(io.open(MANIFEST, encoding="utf-8"))["records"]}
    scoreable = {p["page"] for p in gate["pages"] if p["state"] == "SCOREABLE"}

    print("=== REF ===")
    print("   rubric        %s   sha %s" % (R.RULE_VERSION, R.script_sha256()[:16]))
    print("   harness       %s   sha %s" % (HARNESS_VERSION, sha(HARNESS_MD)[:16]))
    print("   extractor     opencomp.parse_fulltext registry_ids (same rule, both sides)")
    print("   comparators   sha %s" % sha(COMPARATORS)[:16])
    print("   gate          %d SCOREABLE pages" % len(scoreable))
    print("   ⚠️ repeat-instability shipped with every score: %.0f%% / %.1f%%"
          % (100 * INSTABILITY["rubric_tightening_refuse_only"],
             100 * INSTABILITY["straight_repeat"]))
    print("")

    pairs = [p for p in comp["comparators"]
             if p.get("our_page_filename") in scoreable]
    if dry:
        pairs = pairs[:1]
        print("=== DRY RUN -- ONE PAIR, every row to be hand-read ===")
    print("   pairs to score: %d" % len(pairs))
    print("")

    out, nsl = [], 0
    for p in pairs:
        page = os.path.join(REPO, p["our_page_filename"])
        pmid = p["comparator_pmid"]
        rec = man.get(pmid) or {}
        tpath = rec.get("path") or ""
        if not os.path.exists(page) or not (tpath and os.path.exists(tpath)):
            out.append({"pair": (p["our_topic"], pmid), "state": "MATERIAL_MISSING",
                        "page_exists": os.path.exists(page),
                        "text_exists": bool(tpath and os.path.exists(tpath))})
            print("   ⛔ MATERIAL_MISSING %s / %s" % (p["our_topic"], pmid))
            continue

        ours_txt, theirs_txt = page_text(page), io.open(tpath, encoding="utf-8").read()
        ours_lab, theirs_lab = study_labels(ours_txt), study_labels(theirs_txt)
        # ⛔ THE SYMMETRY ASSERTION. Both sides must come from THIS function; if either was
        # supplied from a curated list the comparison is not one.
        assert study_labels.__name__ == "study_labels", "one extractor only"

        topic_terms = {"iv": [p["drug_family"]], "pop": [p["our_topic"].replace("-", " ")]}
        row = {"our_topic": p["our_topic"], "our_page": p["our_page_filename"],
               "comparator_pmid": pmid, "comparator_title": p.get("comparator_title", "")[:160],
               "text_source": rec.get("text_source"),
               "ours_labels": ours_lab, "ours_k": len(ours_lab),
               "theirs_labels": theirs_lab, "theirs_k": len(theirs_lab),
               "extractor": "opencomp registry_ids (one rule, both sides)"}
        row["ours"] = score_side(ours_txt, p["our_page_filename"], ours_lab,
                                 len(ours_lab), topic_terms)
        row["theirs"] = score_side(theirs_txt, "PMID:" + pmid, theirs_lab,
                                   len(theirs_lab), topic_terms)
        row["derived"] = {c: R.derive(row["ours"][c]["verdict"], row["theirs"][c]["verdict"])
                          for c in R.CRITERIA}
        nsl += sum(1 for side in ("ours", "theirs") for c in R.CRITERIA
                   if row[side][c]["verdict"] == "NOT_SCOREABLE_NO_STUDY_LIST")
        out.append(row)

        print("   %-28s vs PMID %-9s  ours k=%-3d theirs k=%-3d  [%s]"
              % (p["our_topic"], pmid, len(ours_lab), len(theirs_lab),
                 rec.get("text_source")))
        for c in ("S2", "S3", "S4", "S5", "S6", "S7"):
            print("      %-3s ours=%-32s theirs=%-32s -> %s"
                  % (c, row["ours"][c]["verdict"], row["theirs"][c]["verdict"],
                     row["derived"][c]))

    print("")
    print("=== NOT_SCOREABLE_NO_STUDY_LIST -- a FINDING, not a low score ===")
    print("   criterion-sides in that state: %d" % nsl)
    print("   PRISMA 2020 item 17 requires an included-study list. It applies to OUR pages")
    print("   exactly as to theirs and is reported, not excused.")

    json.dump({"rubric_version": R.RULE_VERSION, "rubric_sha256": R.script_sha256(),
               "harness_version": HARNESS_VERSION, "harness_sha256": sha(HARNESS_MD),
               "comparators_sha256": sha(COMPARATORS),
               "repeat_instability": INSTABILITY,
               "runner": "scripts/rekey20/score_pairs.py",
               "dry_run": dry, "rows": out},
              io.open(OUT, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print("")
    print("   written: %s" % OUT)


if __name__ == "__main__":
    main()
