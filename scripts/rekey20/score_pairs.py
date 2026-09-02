# -*- coding: utf-8 -*-
"""THE SCORING RUNNER. Reuses the frozen criteria and the frozen harness; owns neither.

⛔ NOTHING HERE REIMPLEMENTS A CRITERION. The six come from `F:/allmeta/oa68k/rubric.py`.
A second scorer would be a second standard, and so would a second extractor.

⛔⛔ AMENDMENT 1 -- SYMMETRIC CODE IS NOT A SYMMETRIC RULE. The first implementation ran ONE
function over both sides and still built the asymmetry in. Our pages print a registry id per
INCLUDED trial; their papers print registry ids mainly for trials they are NOT including --
"Ongoing RCTs, such as (CABA-HFPEF; NCT05508256) … may provide more definitive evidence".
Same code, both sides, DIFFERENT KINDS OF THING. So a study label is a registry identifier
whose OWN SENTENCE does not mark it ongoing / planned / future / excluded, and fewer than two
survivors is NOT_SCOREABLE_NO_STUDY_LIST -- a PRISMA 2020 item 17 finding about that
document, applied identically to ours and theirs.

⛔ AMENDMENT 2 -- §5.2 COVERS SIX TOPICS AND THE PROGRAMME HAS FOURTEEN. `S2_estimand` binds
`topic_terms` to the vocabularies frozen in OPEN-COMPARATOR-PROTOCOL.md §5.2, "no new list is
introduced here". They are PARSED from the protocol so it stays the source of truth; a topic
absent from §5.2 yields NOT_SCOREABLE_NO_FROZEN_TOPIC_TERMS rather than a list invented here.

⚠️ §5.2 DISCLOSES ITS OWN BIAS and it travels with every S2 result: the lists "were written by
someone who already knew which trials our reviews pool, so they are tuned to find our
questions. They are not tuned to any comparator." S2 is the one criterion with a known pro-us
tilt; it is STATED, not corrected, because correcting it introduces the forbidden new list.

⚠️ OPEN-LABEL, and it says so: the blind fails 9/9, p = 0.00195.
⚠️ Every score ships with the repeat-instability measured on this programme's own judge --
27% under a refuse-only rubric tightening, ~6.5% on a straight repeat -- in the result header.
⚠️ 20 comparators · 14 topics · 10 families · 24 pairs. A pair count is never a review count.
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
# ⛔⛔ GUARDED, AND THE GUARD IS THE POINT. An unguarded module-level reassignment closes the
# CALLER's stdout on import -- five times this session, the fifth while measuring whether this
# very run was fair. `scripts/rekey20/lint_stdout_rebind.py` now REFUSES an unguarded one, so
# the defence is a check in the path rather than a rule someone has to remember.
if __name__ == "__main__":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace",
                                  line_buffering=True)
import rubric as R                     # noqa: E402  the FROZEN criteria
import opencomp as OC                  # noqa: E402  the FROZEN id regexes

REPO = "F:/rapidmeta-ssot-shell"
COMPARATORS = "F:/rapidmeta-xsurface/TWENTY_COMPARATORS.json"
GATE = "../../evidence/2026-09-01-scored-run/scoreable_state.json"
MANIFEST = "../../evidence/2026-09-01-scored-run/comparator_text_manifest.json"
HARNESS_MD = OA68K + "/SCORING-HARNESS.md"
PROTOCOL_MD = OA68K + "/OPEN-COMPARATOR-PROTOCOL.md"
OUT = "../../evidence/2026-09-01-scored-run/scores.json"

HARNESS_VERSION = "scoring-harness-1.0.0-2026-09-01+amend1..4"
HANDV = "../../evidence/2026-09-01-scored-run/hand_verified_labels.json"
INCL  = "../../evidence/2026-09-01-scored-run/included_lists.json"
NO_POOLED_PAGES = {"ABLATION_AF_REVIEW.html", "ATTR_PN_REVIEW.html",
                   "COLCHICINE_CVD_REVIEW.html"}
INSTABILITY = {"rubric_tightening_refuse_only": 0.27, "straight_repeat": 0.065,
               "note": "Two runs agreeing on a count is not two runs agreeing: 5 of 7 was "
                       "identical across two runs while a quarter of the labels changed."}
DENOMINATORS = "20 comparators · 14 topics · 10 families · 24 pairs — a pair count is not a review count"

NOT_INCLUDED = re.compile(
    r"(?i)\b(ongoing|on-going|planned|future|forthcoming|upcoming|awaited|awaiting|"
    r"in progress|recruiting|not yet|will (?:provide|report|assess)|"
    r"excluded|we excluded|exclusion)")


def sha(path):
    return hashlib.sha256(io.open(path, "rb").read()).hexdigest()


def page_text(path):
    raw = io.open(path, encoding="utf-8", errors="replace").read()
    t = re.sub(r"(?is)<(script|style)\b.*?</\1>", " ", raw)
    t = re.sub(r"(?s)<[^>]+>", " ", t)
    import html
    return " ".join(html.unescape(t).split())


def study_labels(text):
    """-> (kept, dropped). ONE rule, both sides, about WHAT IS EXTRACTED."""
    ids = (set(OC.RE_NCT.findall(text)) | set(OC.RE_ISRCTN.findall(text))
           | set(OC.RE_CHICTR.findall(text)))
    kept, dropped = [], []
    for i in sorted(ids):
        excluded = False
        for m in re.finditer(re.escape(i), text):
            lo = text.rfind(".", 0, m.start()) + 1
            hi = text.find(".", m.end())
            sent = text[lo:(hi if hi > 0 else min(len(text), m.end() + 200))]
            if NOT_INCLUDED.search(sent):
                excluded = True
                break
        (dropped if excluded else kept).append(i)
    return kept, dropped


def frozen_topic_terms(topic):
    """§5.2, PARSED from the protocol. None if the topic is not frozen there."""
    md = io.open(PROTOCOL_MD, encoding="utf-8").read()
    out = {}
    for line in md.splitlines():
        m = re.match(r"^\|\s*`([a-z0-9-]+)`\s*\|([^|]+)\|([^|]+)\|\s*$", line)
        if m:
            iv = [x.strip() for x in m.group(2).split(",") if x.strip()]
            pop = [x.strip() for x in m.group(3).split(",") if x.strip()]
            if iv and pop:
                out[m.group(1)] = {"iv": iv, "pop": pop}
    return out.get(topic)


def coordinate_forms():
    """§5.3 -> {topic: [[nct, acronym, pmid], ...]}. All coordinate forms of each declared
    study, parsed from the protocol so the protocol stays the source of truth."""
    md = io.open(PROTOCOL_MD, encoding="utf-8").read()
    out = {}
    for line in md.splitlines():
        m = re.match(r"^\|\s*`([a-z0-9-]+)`\s*\|\s*(\d+)\s*\|(.+)\|\s*$", line)
        if not m:
            continue
        studies = []
        for chunk in m.group(3).split("·"):
            nct = OC.RE_NCT.search(chunk)
            if not nct:
                continue
            # ⭐ POSITION, NOT SHAPE. §5.3 writes each study as
            # `NCT<id> <ACRONYM> <PMID>`, so the acronym is whatever lies BETWEEN them. A
            # shape regex requiring a hyphen silently lost `DELIVER` and `SCORED`, which are
            # acronyms without one -- the same defect as matching a form instead of reading
            # the declaration.
            rest = chunk.replace(nct.group(0), " ")
            pmid = re.search(r"\b\d{8}\b", rest)
            mid = rest[:pmid.start()] if pmid else rest
            acro = mid.strip() or None
            studies.append([nct.group(0), acro,
                            pmid.group(0) if pmid else None])
        if studies:
            out[m.group(1)] = studies
    return out


def selftest():
    """⭐ PLANTS for amendment 1. Each plant paired with a clean sibling -- without the
    siblings, dropping everything would pass every plant."""
    cases = [
        ("plant: the real comparator sentence",
         "Ongoing RCTs, such as the comparison of CA for AF (CABA-HFPEF; NCT05508256) and "
         "CA for AF in HFpEF (STABLE-SR IV; NCT06125925), may provide evidence.",
         [], ["NCT05508256", "NCT06125925"]),
        ("clean sibling: INCLUDED trials survive",
         "CASTLE-AF (NCT00643188) randomised 179 patients. "
         "RAFT-AF (NCT01420393) reported a hazard ratio of 0.86.",
         ["NCT00643188", "NCT01420393"], []),
        ("plant: an explicitly excluded trial is dropped",
         "We excluded NCT02000000 because it enrolled children.", [], ["NCT02000000"]),
        ("clean sibling: 'ongoing' in a NEIGHBOURING sentence does not poison a clean id",
         "Ongoing work continues. Separately, DAPA-HF (NCT03036124) randomised 4744.",
         ["NCT03036124"], []),
    ]
    ok = True
    print("=== PLANTS -- amendment 1, ongoing/excluded exclusion ===")
    for label, txt, wk, wd in cases:
        keep, drop = study_labels(txt)
        good = (keep == wk and drop == wd)
        ok = ok and good
        print("   %-58s %s" % (label, "OK" if good else
                               "FAIL keep=%s drop=%s" % (keep, drop)))
    print("")
    print("=== PLANTS -- amendment 4, coordinate forms ===")
    cf = coordinate_forms()
    for t, k in (("sglt2-hf", 4), ("iv-iron-hf", 5), ("sotagliflozin-hf", 2)):
        got = len(cf.get(t) or [])
        ok = ok and (got == k)
        print("   %-58s studies=%-3d want=%-3d %s" % (t, got, k, "OK" if got == k else "FAIL"))
    sg = cf.get("sglt2-hf") or []
    has3 = sum(1 for f in sg if f[0] and f[1] and f[2])
    ok = ok and (has3 == 4)
    print("   %-58s all-three-forms=%-3d want=4   %s"
          % ("sglt2-hf studies carrying nct+acronym+pmid", has3, "OK" if has3 == 4 else "FAIL"))
    print("")
    print("=== PLANTS -- amendment 5, ANY declared form satisfies ===")
    # ⭐ THE INTENTION, not the implementation. Amendment 4's plants proved the three forms
    # were PARSED; they could not see that the runner then silently used the first. These
    # assert that a criterion satisfied via the ACRONYM is satisfied for the study -- and the
    # sibling asserts a study no form satisfies still FAILS, without which "always satisfied"
    # would pass the plant.
    fn5 = R.CRITERIA["S3"][0]
    # ⚠️ THE FIRST VERSION OF THIS PLANT PASSED FOR THE WRONG REASON. It put the registration
    # ids in the same paragraph as the numbers, so the NCT was inside S3's 600-char window and
    # the plant would have passed under the NCT-first convention this amendment overturns.
    # The ids are now pushed BEYOND that window, so only the acronym can satisfy: the plant
    # now fails if amendment 5 is not in force.
    pad = ("This sentence carries no estimate and exists to separate the registrations "
           "from the results. ") * 12                       # ~1.1k chars, S3's window is 600
    hit = ("We included two trials. DAPA-HF reported a hazard ratio of 0.74 "
           "(95% CI 0.65 to 0.85). EMPEROR-Reduced reported a hazard ratio of 0.75 "
           "(95% CI 0.65 to 0.86). " + pad
           + "Registration: NCT03036124 and NCT03057977.")
    miss = ("We included two trials, NCT03036124 and NCT03057977, and narrate their "
            "findings without any numeric estimate for either one anywhere in this text.")
    st = [["NCT03036124", "DAPA-HF", "31535829"], ["NCT03057977", "EMPEROR-Reduced", "32865377"]]
    for lbl, txt, want in (("acronym-only numbers -> ANY form satisfies", hit, "SATISFIED"),
                           ("clean sibling: no form satisfies -> still fails", miss,
                            "NOT_SATISFIED")):
        use = choose_form(fn5, txt, "plant", st, 2, {"iv": [], "pop": []})
        v, _ = fn5(txt, "plant", study_labels=use, k=2, topic_terms={"iv": [], "pop": []})
        ok = ok and (v == want)
        print("   %-58s %-13s want=%-13s %s"
              % (lbl, v, want, "OK" if v == want else "FAIL"))
    picked = choose_form(fn5, hit, "plant", st, 2, {"iv": [], "pop": []})
    disc = all(x in ("DAPA-HF", "EMPEROR-Reduced") for x in picked)
    ok = ok and disc
    print("   %-58s %s %s" % ("forms chosen -- must be ACRONYMS or the plant is inert",
                              picked, "OK" if disc else "FAIL"))
    nct_only, _ = fn5(hit, "plant", study_labels=[st[0][0], st[1][0]], k=2,
                      topic_terms={"iv": [], "pop": []})
    ok = ok and (nct_only == "NOT_SATISFIED")
    print("   %-58s %-13s want=%-13s %s"
          % ("detector control: NCT-first on the SAME text must fail", nct_only,
             "NOT_SATISFIED", "OK" if nct_only == "NOT_SATISFIED" else "FAIL"))

    print("")
    print("=== PLANTS -- amendment 2, frozen topic terms ===")
    for t, want in (("sglt2-hf", True), ("iv-iron-hf", True),
                    ("finerenone-cv", False), ("ablation-af-review", False)):
        got = frozen_topic_terms(t) is not None
        ok = ok and (got == want)
        print("   %-58s frozen=%-5s want=%-5s %s"
              % (t, got, want, "OK" if got == want else "FAIL"))
    return ok


def choose_form(fn, text, file_label, studies, k, topic_terms):
    """AMENDMENT 5. Per declared study, ask THE CRITERION ITSELF about each coordinate form
    with a single-study list; the first form it answers SATISFIED for is that study's label.
    If none does, the first declared form is used so the study correctly FAILS.

    ⛔ Nothing here re-derives the criterion -- the criterion is the test. That is what makes
    this study IDENTITY rather than a second scorer.
    """
    labels = []
    for forms in studies:
        cands = [f for f in forms if f]
        pick = None
        for f in cands:
            try:
                v, _ = fn(text, file_label, study_labels=[f], k=k,
                          topic_terms=topic_terms or {"iv": [], "pop": []})
            except Exception:                                       # noqa: BLE001
                v = None
            if v == "SATISFIED":
                pick = f
                break
        labels.append(pick or (cands[0] if cands else None))
    return [x for x in labels if x]


def score_side(text, file_label, labels, k, topic_terms, studies=None):
    rows = {}
    for name, (fn, anchor) in R.CRITERIA.items():
        if name == "S2" and not topic_terms:
            rows[name] = {"verdict": "NOT_SCOREABLE_NO_FROZEN_TOPIC_TERMS",
                          "prisma_anchor": anchor, "evidence": None,
                          "rubric_sha256": R.script_sha256()}
            continue
        use = labels
        if studies and name in ("S3", "S4", "S7"):
            use = choose_form(fn, text, file_label, studies, k, topic_terms)
        verdict, ev = fn(text, file_label, study_labels=use, k=k,
                         topic_terms=topic_terms or {"iv": [], "pop": []})
        rows[name] = {"verdict": verdict, "prisma_anchor": anchor, "evidence": ev,
                      "rubric_sha256": R.script_sha256()}
    return rows


def main():
    if "--selftest" in sys.argv:
        sys.exit(0 if selftest() else 1)
    dry = "--dry-run" in sys.argv
    comp = json.load(io.open(COMPARATORS, encoding="utf-8"))
    gate = json.load(io.open(GATE, encoding="utf-8"))
    global HAND, FROZEN, INCLROWS
    HAND = json.load(io.open(HANDV, encoding="utf-8"))
    incl = json.load(io.open(INCL, encoding="utf-8"))
    FROZEN = {k: v for k, v in (incl.get("our_side") or {}).items() if v}
    global FORMS
    FORMS = coordinate_forms()
    INCLROWS = {r["pmid"]: r.get("labels_extracted") or [] for r in incl["rows"]}
    man = {r["pmid"]: r for r in json.load(io.open(MANIFEST, encoding="utf-8"))["records"]}
    scoreable = {p["page"] for p in gate["pages"] if p["state"] == "SCOREABLE"}

    print("=== REF ===")
    print("   rubric        %s   sha %s" % (R.RULE_VERSION, R.script_sha256()[:16]))
    print("   harness       %s" % HARNESS_VERSION)
    print("   harness sha   %s" % sha(HARNESS_MD)[:16])
    print("   comparators   sha %s" % sha(COMPARATORS)[:16])
    print("   ⚠️ OPEN-LABEL -- the blind fails 9/9, p=0.00195")
    print("   ⚠️ instability shipped with the result: %.0f%% / %.1f%%"
          % (100 * INSTABILITY["rubric_tightening_refuse_only"],
             100 * INSTABILITY["straight_repeat"]))
    print("   ⚠️ %s" % DENOMINATORS)
    print("")

    rows_out, nsl, nft, npe = [], 0, 0, 0
    pairs = [p for p in comp["comparators"]]
    if dry:
        pairs = [p for p in pairs if p["our_page_filename"] in scoreable][:1]

    for p in sorted(pairs, key=lambda x: (x["our_page_filename"], x["comparator_pmid"])):
        page_f = p["our_page_filename"]
        pmid = p["comparator_pmid"]
        if page_f in NO_POOLED_PAGES:
            npe += 1
            rows_out.append({"our_topic": p["our_topic"], "our_page": page_f,
                             "comparator_pmid": pmid,
                             "state": "NOT_SCOREABLE_NO_POOLED_ESTIMATE_OUR_SIDE"})
            continue
        if page_f not in scoreable:
            rows_out.append({"our_topic": p["our_topic"], "our_page": page_f,
                             "comparator_pmid": pmid,
                             "state": "NOT_SCOREABLE_SURFACE_DISAGREEMENT"})
            continue
        page = os.path.join(REPO, page_f)
        rec = man.get(pmid) or {}
        tpath = rec.get("path") or ""
        if not os.path.exists(page) or not (tpath and os.path.exists(tpath)):
            rows_out.append({"our_topic": p["our_topic"], "our_page": page_f,
                             "comparator_pmid": pmid, "state": "MATERIAL_MISSING"})
            continue

        ours_txt = page_text(page)
        theirs_txt = io.open(tpath, encoding="utf-8").read()
        # AMENDMENT 3. OUR side = the frozen included set the protocol DECLARES (5.3).
        # THEIR side = the included-studies table they DECLARE, HAND-VERIFIED. One rule --
        # "what the artefact declares" -- two declaration mechanisms.
        # AMENDMENT 4. One label per DECLARED study: whichever coordinate form the document
        # actually uses. Passing all three forms as three labels would make S3/S7 -- which
        # are CONJUNCTIONS -- demand a numeric row near each form, stricter than the
        # criterion means. k is unchanged and equals the number of declared studies.
        fz = FORMS.get(p["our_topic"]) or []
        ok_lab, ok_drop = [], []
        for forms in fz:
            used = next((f for f in forms if f and f in ours_txt), None)
            if used:
                ok_lab.append(used)
            else:
                ok_drop.append(forms[0])
        hv = HAND["rows"].get(pmid) or {}
        if hv.get("state"):
            rows_out.append({"our_topic": p["our_topic"], "our_page": page_f,
                             "comparator_pmid": pmid, "state": hv["state"],
                             "k_extracted": hv.get("k_extracted"),
                             "k_hand_verified": hv.get("k_hand_verified"),
                             "correction": hv.get("correction"), "basis": hv.get("basis")})
            continue
        kh = hv.get("k_hand_verified")
        if kh is not None and kh < 2:
            rows_out.append({"our_topic": p["our_topic"], "our_page": page_f,
                             "comparator_pmid": pmid,
                             "state": "NOT_SCOREABLE_NO_STUDY_LIST",
                             "k_extracted": hv.get("k_extracted"), "k_hand_verified": kh,
                             "correction": hv.get("correction"), "basis": hv.get("basis")})
            continue
        th_lab = hv.get("labels") or [x for x in INCLROWS.get(pmid, [])][:kh or 0]
        th_drop = []
        tt = frozen_topic_terms(p["our_topic"])
        if tt is None:
            nft += 1
        row = {"our_topic": p["our_topic"], "our_page": page_f, "comparator_pmid": pmid,
               "comparator_title": (p.get("comparator_title") or "")[:150],
               "text_source": rec.get("text_source"), "state": "SCORED",
               "ours_labels": ok_lab, "ours_k": len(ok_lab),
               "ours_source": "OPEN-COMPARATOR-PROTOCOL 5.3 frozen included set",
               "theirs_labels": th_lab, "theirs_k": len(th_lab),
               "theirs_k_extracted": hv.get("k_extracted"),
               "theirs_k_hand_verified": kh,
               "theirs_parser_correction": hv.get("correction"),
               "theirs_source": "the comparator's own included-studies table, hand-verified",
               "topic_terms_frozen": tt is not None}
        row["ours"] = score_side(ours_txt, page_f,
                                 ok_lab if len(ok_lab) >= 2 else [], len(ok_lab), tt,
                                 studies=fz)
        row["theirs"] = score_side(theirs_txt, "PMID:" + pmid,
                                   th_lab if len(th_lab) >= 2 else [], len(th_lab), tt)
        row["derived"] = {c: R.derive(row["ours"][c]["verdict"], row["theirs"][c]["verdict"])
                          for c in R.CRITERIA}
        nsl += sum(1 for s in ("ours", "theirs") for c in R.CRITERIA
                   if row[s][c]["verdict"] == "NOT_SCOREABLE_NO_STUDY_LIST")
        rows_out.append(row)

        print("   %-26s vs PMID %-9s ours k=%-3d theirs k=%-3d dropped o/t %d/%d [%s]"
              % (p["our_topic"][:26], pmid, len(ok_lab), len(th_lab),
                 len(ok_drop), len(th_drop), rec.get("text_source")))
        for c in ("S2", "S3", "S4", "S5", "S6", "S7"):
            print("      %-3s ours=%-36s theirs=%-36s -> %s"
                  % (c, row["ours"][c]["verdict"], row["theirs"][c]["verdict"],
                     row["derived"][c]))

    scored = [r for r in rows_out if r.get("state") == "SCORED"]
    print("")
    print("=== DISPOSITION OF ALL %d PAIRS ===" % len(rows_out))
    from collections import Counter
    for k, v in Counter(r.get("state", "SCORED") for r in rows_out).most_common():
        print("   %-46s %2d" % (k, v))
    print("")
    print("=== NOT_SCOREABLE COUNTS -- findings, not low scores ===")
    print("   NO_STUDY_LIST criterion-sides        : %d   (PRISMA 2020 item 17)" % nsl)
    print("   NO_FROZEN_TOPIC_TERMS pairs (S2)     : %d   (§5.2 covers 6 of 14 topics)" % nft)
    print("   NO_POOLED_ESTIMATE_OUR_SIDE pairs    : %d   (our artefact, not theirs)" % npe)
    print("")
    print("=== DERIVED, over the %d scored pairs ===" % len(scored))
    tally = Counter(r["derived"][c] for r in scored for c in R.CRITERIA)
    for k, v in tally.most_common():
        print("   %-28s %3d" % (k, v))

    json.dump({"rubric_version": R.RULE_VERSION, "rubric_sha256": R.script_sha256(),
               "harness_version": HARNESS_VERSION, "harness_sha256": sha(HARNESS_MD),
               "comparators_sha256": sha(COMPARATORS), "open_label": True,
               "blind_fails": "9/9, p=0.00195", "denominators": DENOMINATORS,
               "repeat_instability": INSTABILITY,
               "runner": "scripts/rekey20/score_pairs.py", "dry_run": dry,
               "rows": rows_out}, io.open(OUT, "w", encoding="utf-8"),
              ensure_ascii=False, indent=1)
    print("")
    print("   written: %s" % OUT)


if __name__ == "__main__":
    main()
