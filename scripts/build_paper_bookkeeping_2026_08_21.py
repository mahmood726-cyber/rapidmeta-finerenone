"""Assemble the three parts of a paper that are NOT argument: references, the Introduction's
factual half, and the five fetchable bookkeeping claims.

NOTHING HERE IS AUTHORED. Every sentence is assembled from a field this object already holds,
and where a field does not exist the absence is STATED rather than filled. The four
interpretive claims -- why the question is open, what this review adds, what the effect means
clinically, and the conclusion -- are NOT written here and are named as owed.

WHAT IS BUILT

  manuscript.references          a bibliography, in three parts:
                                   included studies, by registration
                                   published syntheses this review was compared against
                                   methods guidance and software, with versions
                                 This is NOT the same thing as `sources`, which records the
                                 data provenance layer each fact was read at. Both belong: one
                                 is what a reader would look up, the other is what an auditor
                                 would re-read. The References section refused entirely on
                                 topics whose `sources` is empty, and a paper with no
                                 reference list is incomplete in a way nobody would defend.

  manuscript.introduction        the factual half only: what is being compared, in whom, on
                                 what outcome, over how many trials and participants, and how
                                 the evidence base was assembled -- then a final sentence
                                 naming what is still owed and by whom.

  bookkeeping_2026_08_21         the five claims measured as FETCHABLE, missing on 9 to 20 of
                                 28 topics: which limbs this review refuses, the search with
                                 its date and databases, whether it was prospectively
                                 registered, that a second assessor disagreed and where, and
                                 which risk-of-bias domains drove the rating.

THE SEARCH CLAIM HAS TWO HALVES AND CONFLATING THEM WOULD BE A FALSE CLAIM. The stored
`query_as_executed` is the search for PUBLISHED SYNTHESES (P46 limb 3), not for primary
trials. Most of these topics identified their trials by reading NAMED REGISTRATIONS, which is
not a database search and must not be described as one. Both halves are written, separately
labelled, and the registry half says plainly that no bibliographic search for primary trials
was run.
"""
import glob
import importlib.util
import io
import json
import os
import sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(REPO, "ssot"))
import atomic_write                                            # noqa: E402

_q = importlib.util.spec_from_file_location(
    "p46_queue", os.path.join(REPO, "scripts", "p46_queue.py"))
p46 = importlib.util.module_from_spec(_q)
_q.loader.exec_module(p46)

ALL_TOPICS = "--all" in sys.argv
TODAY = "2026-08-21"

GUIDANCE = {
    "rob2": ("Sterne JAC, Savovic J, Page MJ, et al. RoB 2: a revised tool for assessing risk "
             "of bias in randomised trials. BMJ. 2019;366:l4898. doi:10.1136/bmj.l4898"),
    "grade": ("Schunemann HJ, Higgins JPT, Vist GE, et al. Chapter 14: Completing 'Summary of "
              "findings' tables and grading the certainty of the evidence. In: Cochrane "
              "Handbook for Systematic Reviews of Interventions version 6.5. Cochrane; 2024."),
    "metafor": ("Viechtbauer W. Conducting meta-analyses in R with the metafor package. "
                "J Stat Softw. 2010;36(3):1-48. doi:10.18637/jss.v036.i03"),
    "prisma": ("Page MJ, McKenzie JE, Bossuyt PM, et al. The PRISMA 2020 statement: an updated "
               "guideline for reporting systematic reviews. BMJ. 2021;372:n71. "
               "doi:10.1136/bmj.n71"),
}


def g(o, path, default=None):
    cur = o
    for part in path.split("."):
        if not isinstance(cur, dict):
            return default
        cur = cur.get(part)
    return default if cur is None else cur


def pooled_blocks(obj):
    return ((obj.get("results") or {}).get("by_outcome") or {})


def included_studies(obj):
    """Every trial this review pools, keyed by registration. Deduplicated across outcomes."""
    seen, rows = set(), []
    pools = list(pooled_blocks(obj).values())
    srcs = list((obj.get("inputs") or {}).get("trials") or [])
    for blk in pools:
        srcs.extend((blk or {}).get("per_trial") or [])
    for t in srcs:
        if not isinstance(t, dict):
            continue
        nct = t.get("nct") or t.get("trial_id")
        # A NULLED TRIAL IS NOT AN INCLUDED STUDY. It appeared in the reference list under
        # "Included studies, by registration" on finerenone-review while k said three.
        if t.get("nulled") or str(nct or "").startswith("NULLED:"):
            continue
        if not nct or nct in seen:
            continue
        seen.add(nct)
        rows.append({
            "registration": str(nct),
            "label": str(t.get("label") or t.get("trial_id") or "").strip(),
            "registry": str(t.get("registry") or "ClinicalTrials.gov"),
            "url": str(t.get("source_url") or ("https://clinicaltrials.gov/study/%s" % nct)),
            "read_utc": str(t.get("read_utc") or ""),
        })
    return sorted(rows, key=lambda r: r["registration"])


def published_syntheses(obj):
    out = []
    for r in (g(obj, "published_comparison.reviews") or []):
        if not isinstance(r, dict):
            continue
        bits = [str(r.get("title") or "").strip().rstrip(".")]
        if r.get("journal"):
            bits.append(str(r["journal"]))
        if r.get("year"):
            bits.append(str(r["year"]))
        cite = ". ".join([b for b in bits if b])
        ident = []
        if r.get("pmid"):
            ident.append("PMID: %s" % r["pmid"])
        if r.get("doi"):
            ident.append("doi:%s" % r["doi"])
        # A ROW THAT IS BLANK EXCEPT FOR ITS IDENTIFIER IS NOT A REFERENCE.
        # Seven topics hold an appraised synthesis with a PMID and no title, journal or year;
        # emitted as rows they made `add_table` refuse the whole table -- correctly, since an
        # empty cell under a filled header asserts a citation that has nothing behind it.
        # They are counted and named in the note instead of drawn as a blank line.
        if not cite:
            continue
        out.append({
            "citation": cite + ("." if cite and not cite.endswith(".") else ""),
            "identifier": "; ".join(ident) or "no PMID or DOI recorded",
            "url": ("https://pubmed.ncbi.nlm.nih.gov/%s/" % r["pmid"]) if r.get("pmid") else "",
        })
    return out


def unciteable_syntheses(obj):
    """Appraised syntheses whose record carries an identifier and no citable text."""
    out = []
    for r in (g(obj, "published_comparison.reviews") or []):
        if isinstance(r, dict) and not str(r.get("title") or "").strip():
            out.append(str(r.get("pmid") or r.get("doi") or "an unidentified record"))
    return out


def software(obj):
    """The engine string, read from wherever this object actually stored it."""
    cands = [g(obj, "model_output.engine")]
    for blk in pooled_blocks(obj).values():
        ro = (blk or {}).get("r_output") or {}
        cands.append(ro.get("environment") or ro.get("_environment"))
    for c in cands:
        if isinstance(c, str) and c.strip():
            return c.strip()
    return None


def references(obj):
    inc = included_studies(obj)
    pub = published_syntheses(obj)
    meth = []
    if isinstance(obj.get("risk_of_bias"), dict) and (obj["risk_of_bias"].get("by_outcome")):
        meth.append({"cited_for": "risk of bias in the included results",
                     "citation": GUIDANCE["rob2"]})
    if isinstance(obj.get("grade"), dict) and obj["grade"].get("by_outcome"):
        meth.append({"cited_for": "certainty of the evidence",
                     "citation": GUIDANCE["grade"]})
    sw = software(obj)
    if sw:
        meth.append({"cited_for": "the model fitted, as %s" % sw,
                     "citation": GUIDANCE["metafor"]})
    meth.append({"cited_for": "the reporting guideline this manuscript is written against",
                 "citation": GUIDANCE["prisma"]})
    if not inc:
        return None
    return {
        "_what": ("A reference list, assembled from this object's own fields. Distinct from "
                  "`sources`, which records the provenance LAYER each fact was read at; this "
                  "is what a reader would look up."),
        "included_studies": inc,
        "published_syntheses_compared_against": pub,
        "_published_syntheses_note": (
            ("Appraised against this review; the comparison and its denominator are in "
             "`published_comparison`. " if pub else
             "No published synthesis is listed here. The comparison section states its own "
             "denominator and why nothing citable was appraised. ")
            + (("%d appraised record(s) -- %s -- carry an identifier and NO title, journal or "
                "year, so they cannot be written as a citation and are named here rather than "
                "drawn as a blank row under a filled header."
                % (len(unc), ", ".join(unc))) if (unc := unciteable_syntheses(obj)) else "")),
        "methods_guidance_and_software": meth,
    }


def introduction(obj):
    """The factual half. The interpretive sentences are named as owed, never written."""
    q = str(obj.get("question") or "").strip()
    outs = [o for o in (obj.get("outcomes") or []) if isinstance(o, dict)]
    pools = pooled_blocks(obj)
    ks, n = [], 0
    for blk in pools.values():
        if isinstance((blk or {}).get("k"), int):
            ks.append(blk["k"])
        for t in ((blk or {}).get("per_trial") or []):
            for key in ("n", "n_total", "enrolment", "registered_enrolment"):
                if isinstance((t or {}).get(key), int):
                    n += t[key]
                    break
    if not q or not pools:
        return None
    k = max(ks) if ks else 0
    names = [str(o.get("name") or o.get("id")) for o in outs if o.get("name") or o.get("id")]
    comp = next((str(o.get("comparator")) for o in outs if o.get("comparator")), None)
    if not comp:
        comp = next((str((b or {}).get("comparator")) for b in pools.values()
                     if (b or {}).get("comparator")), None)

    parts = []
    parts.append("This review asks: %s" % (q if q.endswith("?") else q + "."))
    base = "It pools %d randomised trial%s" % (k, "" if k == 1 else "s")
    if n:
        base += " comprising %s participants as registered" % format(n, ",")
    if comp:
        base += ", against %s" % comp
    parts.append(base + ".")
    if names:
        parts.append("The outcome%s pooled %s %s."
                     % ("" if len(names) == 1 else "s",
                        "is" if len(names) == 1 else "are",
                        "; ".join(names[:6])))
    prov = str(obj.get("provenance") or "").strip()
    if prov:
        parts.append("Every count and denominator behind those estimates is read as follows. "
                     + (prov if prov.endswith(".") else prov + "."))
    parts.append(
        "Everything in this paragraph is derived from stored fields and none of it is "
        "authored. The interpretive sentences that follow are marked as drafts and are the "
        "author's to replace.")
    return "\n\n".join(parts)


def bookkeeping(obj, topic):
    out = {"_what": ("The five reporting claims a PRISMA-2020 manuscript needs that are "
                     "FETCHABLE rather than argued -- each derived from a field here, or "
                     "stated as an honest absence.")}

    # 1. WHICH LIMBS THIS REVIEW REFUSES
    try:
        sc = p46.score(obj)
    except Exception:                                          # noqa: BLE001
        sc = None
    if isinstance(sc, dict):
        # `score` returns {limb: [STATE, detail]}, not {limb: STATE}. Read the state.
        def _state(v):
            return str(v[0] if isinstance(v, (list, tuple)) and v else v).upper()
        held = sorted(k for k, v in sc.items() if _state(v) == "HELD")
        not_held = sorted(k for k, v in sc.items() if k not in held)
        out["which_limbs_this_review_refuses"] = (
            "Of the four properties this project requires of a completed topic, %d are held "
            "(%s)%s." % (len(held), ", ".join(x.replace("_", " ") for x in held) or "none",
                         "" if not not_held else
                         " and %d are refused with the obstacle named in the evidence (%s)"
                         % (len(not_held),
                            ", ".join(x.replace("_", " ") for x in not_held))))

    # 2. THE SEARCH -- TWO HALVES, NEVER CONFLATED
    scr = None
    for p in sorted(glob.glob(os.path.join(REPO, "ssot", topic, "appraisal", "*.json"))):
        try:
            d = json.load(io.open(p, encoding="utf-8"))
        except ValueError:
            continue
        if d.get("query_as_executed"):
            scr = d
            break
    halves = []
    prov = str(obj.get("provenance") or "")
    vb = str(obj.get("verification_basis") or "")
    inc = included_studies(obj)
    if inc:
        dates = sorted({r["read_utc"] for r in inc if r["read_utc"]})
        halves.append(
            "PRIMARY TRIALS. NO BIBLIOGRAPHIC SEARCH FOR PRIMARY TRIALS WAS RUN. The %d "
            "included trial%s %s identified by reading named registration%s on %s%s."
            % (len(inc), "" if len(inc) == 1 else "s",
               "was" if len(inc) == 1 else "were", "" if len(inc) == 1 else "s",
               " and ".join(dates) if dates else "the dates recorded on each entry",
               "; " + (vb or prov).rstrip(".") if (vb or prov) else ""))
    if scr:
        halves.append(
            "PUBLISHED SYNTHESES. %s, executed %s. Query as executed: %s. It matched %s "
            "record(s), of which %s were retrieved and %s read; %s appraised."
            % (scr.get("source", "a bibliographic database"), scr.get("executed_utc", "?"),
               scr.get("query_as_executed"), scr.get("matched", "?"),
               scr.get("retrieved", "?"), scr.get("read", "?"),
               len(scr.get("appraised") or []) if isinstance(scr.get("appraised"), list)
               else scr.get("appraised", "?")))
    if halves:
        out["the_search_its_date_and_its_databases"] = " ".join(halves)

    # 3. PROSPECTIVE REGISTRATION
    pro = g(obj, "prospero") or g(obj, "protocol.prospero") or g(obj, "protocol.registration")
    out["whether_this_review_was_prospectively_registered"] = (
        str(pro) if isinstance(pro, str) and pro.strip() else
        "NO PROSPERO REGISTRATION OR PROTOCOL RECORD IS HELD ON THIS OBJECT. That is not the "
        "same as knowing this review was not registered, and neither claim is made. It is "
        "recorded here as an absence so that a reader does not have to infer it from silence.")

    # 4. THE SECOND ASSESSOR
    rob = obj.get("risk_of_bias") or {}
    sa = next((rob[k] for k in sorted(rob) if str(k).startswith("SECOND_ASSESSOR")
               and isinstance(rob[k], dict)), None)
    if sa:
        rc = next((sa[k] for k in sorted(sa) if k.startswith("RECOUNTED_AFTER")
                   and isinstance(sa[k], dict)), None)
        out["that_two_assessors_disagreed_and_where"] = (
            "Risk of bias was assessed independently a second time by %s, blind to this "
            "assessment and given the same registry facts. %s By domain: %s.%s"
            % (sa.get("assessor_2", "a second assessor"),
               sa.get("DISAGREEMENT_RATE", ""),
               ", ".join("%s %s" % (k, v) for k, v in
                         sorted((sa.get("PER_DOMAIN") or {}).items())) or "not recorded",
               (" Recounted after this review's D1 judgements moved: %s."
                % rc.get("recounted_now", "")) if rc else ""))
    else:
        out["that_two_assessors_disagreed_and_where"] = (
            "NO SECOND, INDEPENDENT RISK-OF-BIAS ASSESSMENT IS RECORDED FOR THIS TOPIC. The "
            "judgements were made once. Stated so that single assessment is not mistaken for "
            "agreement between two.")

    # 5. WHICH ROB DOMAINS DROVE THE RATING
    drove = {}
    for oid, per in (rob.get("by_outcome") or {}).items():
        if not isinstance(per, dict):
            continue
        for rid, j in per.items():
            if not isinstance(j, dict):
                continue
            ov = str(j.get("overall") or "").upper()
            if ov in ("", "LOW"):
                continue
            for k, v in (j.get("domains") or {}).items():
                if isinstance(v, dict) and str(v.get("judgement") or "").upper() == ov:
                    drove[str(k).split("_")[0].upper()] = drove.get(
                        str(k).split("_")[0].upper(), 0) + 1
    if drove:
        out["which_risk_of_bias_domains_drove_the_rating"] = (
            "Where a result is rated worse than LOW overall, the domain carrying that "
            "judgement is: %s. The overall rating is the worst domain, so these are the "
            "domains that determine it."
            % ", ".join("%s on %d result(s)" % (k, n)
                        for k, n in sorted(drove.items(), key=lambda kv: (-kv[1], kv[0]))))
    return out


def main():
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    dry = "--apply" not in sys.argv
    only = [a for a in sys.argv[1:] if not a.startswith("--")]
    n_ref = n_int = n_bk = topics = 0
    no_ref = []
    for path in sorted(glob.glob(os.path.join(REPO, "ssot", "*", "*.json"))):
        topic = os.path.basename(os.path.dirname(path))
        if os.path.basename(path) != topic + ".json":
            continue
        if only and topic not in only:
            continue
        try:
            obj = json.load(io.open(path, encoding="utf-8"))
        except ValueError:
            continue
        # `--all` WIDENS THE SCOPE TO EVERY TOPIC WITH A PAGE, not only the 28 that
        # pool. Each part still refuses on its own terms: a topic with no included
        # registration gets no reference list, one with no pooled interval gets no
        # drafts. That is a per-part absence with a reason, not a whole topic
        # skipped for want of one field.
        if not ALL_TOPICS and not p46.pooled_outcomes(obj):
            continue
        topics += 1
        # `setdefault` RETURNS AN EXISTING NULL. Twelve topics hold `manuscript: null`, so
        # `setdefault("manuscript", {})` handed back None, the isinstance guard skipped them,
        # and the run reported 16 of 28 while printing no reason for the other 12.
        man = obj.get("manuscript")
        if not isinstance(man, dict):
            man = {}
            obj["manuscript"] = man

        refs = references(obj)
        if refs:
            man["references"] = refs
            n_ref += 1
        else:
            no_ref.append(topic)

        intro = introduction(obj)
        if intro and not str(man.get("introduction") or "").strip():
            man["introduction"] = intro
            n_int += 1

        bk = bookkeeping(obj, topic)
        if len(bk) > 1:
            obj["bookkeeping_%s" % TODAY.replace("-", "_")] = bk
            n_bk += 1

        obj.setdefault("display_change_announced", []).append({
            "date": TODAY,
            "change": "references, the Introduction's factual half, and the five fetchable "
                      "bookkeeping claims assembled from stored fields",
            "values_moved": "NONE -- no estimate, judgement, rating or certainty is touched",
            "what_changed": "references %s, introduction %s, bookkeeping claims %d"
                            % ("built" if refs else "not buildable",
                               "written" if intro else "not buildable", len(bk) - 1),
            "why": ("A paper with no reference list and a 47-character Introduction is "
                    "incomplete in ways that are pure assembly. Nothing interpretive is "
                    "written: the four judgement claims are named as owed."),
        })
        print("%-44s refs %-3s intro %-3s bookkeeping %d"
              % (topic[:44], "yes" if refs else "NO", "yes" if intro else "NO", len(bk) - 1))
        if not dry:
            atomic_write.write_json(path, obj, indent=1)

    if not topics:
        sys.exit("PROOF FAILED: no topic with a pooled outcome was read. 28 have one.")
    print("\n%d topic(s): references on %d, introduction on %d, bookkeeping on %d"
          % (topics, n_ref, n_int, n_bk))
    if no_ref:
        print("NO REFERENCE LIST BUILDABLE (no included trial carries a registration): %s"
              % ", ".join(no_ref))
    if dry:
        print("DRY RUN -- pass --apply to write")


if __name__ == "__main__":
    main()
