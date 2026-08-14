import io, sys, json, collections

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

# ---------------------------------------------------------------- new tokens
P = r"F:\rapidmeta-ssot-shell\ssot\paper.py"
s = open(P, encoding="utf-8").read()
old = '''        "rob2_overall_agree": _fmt(ag.get("overall_agreed")),
        "rob2_overall_total": _fmt(ag.get("overall_total")),
    }'''
new = '''        "rob2_overall_agree": _fmt(ag.get("overall_agreed")),
        "rob2_overall_total": _fmt(ag.get("overall_total")),
    }
    # Quantities the expanded Results section reports. Added as TOKENS rather
    # than typed into the prose: a number written into manuscript text is a copy
    # that drifts the moment the pool changes, which is the defect that put a
    # k=3 leave-one-out under a k=4 headline and a three-trial title on a
    # four-trial paper.
    pan = res.get("panels") or {}
    pred, eg = pan.get("prediction") or {}, pan.get("egger") or {}
    sp = res.get("post_hoc_aetiology_split") or {}
    strata = sp.get("strata") or []
    it = sp.get("interaction_test") or {}
    pc = (canon.get("published_comparison") or {}).get("denominator") or {}
    loo_rows = [a for a in (sens.get("analyses") or []) if isinstance(a, dict)]
    kept = [a for a in loo_rows if a.get("still_excludes_null")]
    extra = {
        "pi_low": _fmt(pred.get("pi_low")), "pi_high": _fmt(pred.get("pi_high")),
        "egger_p": _fmt(eg.get("p"), 3),
        "egger_intercept": _fmt(eg.get("intercept")),
        "loo_n_excluding_null": _fmt(len(kept)) if loo_rows else None,
        "loo_n_total": _fmt(len(loo_rows)) if loo_rows else None,
        "cmp_checked": _fmt(pc.get("rows_checked")),
        "cmp_confirmed": _fmt(pc.get("confirmed")),
        "cmp_errors": _fmt(pc.get("errors")),
        "cmp_absent": _fmt(pc.get("absent")),
    }
    for i, st in enumerate(strata[:2]):
        extra["strat%d_name" % (i + 1)] = st.get("stratum") or st.get("name")
        extra["strat%d_k" % (i + 1)] = _fmt(st.get("k"))
        extra["strat%d_point" % (i + 1)] = _fmt(st.get("point"))
        extra["strat%d_low" % (i + 1)] = _fmt(st.get("ci_low"))
        extra["strat%d_high" % (i + 1)] = _fmt(st.get("ci_high"))
    extra["interaction_p"] = _fmt(it.get("p"), 3)
    extra["rhr"] = _fmt(it.get("ratio_of_hazard_ratios_chagas_vs_unrestricted"))
    extra["rhr_low"] = _fmt(it.get("rhr_ci_low"))
    extra["rhr_high"] = _fmt(it.get("rhr_ci_high"))
    tok.update(extra)'''
assert s.count(old) == 1
s = s.replace(old, new)
open(P, "w", encoding="utf-8").write(s)
print("paper.py: %d new tokens for the expanded Results" % 20)

# ---------------------------------------------------------------- the prose
O = r"F:\rapidmeta-ssot-shell\ssot\arni-hfref\arni-hfref.json"
d = json.load(open(O, encoding="utf-8"), object_pairs_hook=collections.OrderedDict)
rp = d["manuscript"]["results_prose"]
have = {x["heading"] for x in rp}

NEW = [
 ("Subgroup analysis",
  "One subgroup analysis was performed and it was NOT pre-specified. Splitting "
  "the pool by aetiology gives [[strat1_point]] ([[strat1_low]] to "
  "[[strat1_high]]) across the [[strat1_k]] trials in unrestricted heart failure "
  "and [[strat2_point]] ([[strat2_low]] to [[strat2_high]]) across the "
  "[[strat2_k]] trials restricted to Chagas cardiomyopathy. The test for "
  "interaction returns p = [[interaction_p]] and a ratio of hazard ratios of "
  "[[rhr]] ([[rhr_low]] to [[rhr_high]]), so the difference between the strata is "
  "compatible with chance. Splitting on aetiology does not explain the "
  "heterogeneity: the residual I-squared within strata is higher than the "
  "overall value, not lower. Because the analysis is post hoc it is reported as "
  "hypothesis-generating and is labelled post hoc wherever it appears, in "
  "keeping with the Cochrane Handbook v6.5 section 10.11.5 caution against "
  "presenting unplanned subgroup contrasts as findings."),
 ("Small-study effects",
  "A funnel plot is shown and Egger's regression test was run for completeness, "
  "returning an intercept of [[egger_intercept]] with p = [[egger_p]]. Neither "
  "is interpreted. At [[k]] trials the Cochrane Handbook v6.5 section 13.3.5.4 "
  "advises against interpreting funnel asymmetry or its tests below about ten "
  "studies, and the movement of this p value when the fourth trial entered is "
  "what a test with almost no power does rather than evidence about publication "
  "bias. No claim about small-study effects is made in either direction."),
 ("Comparison with published syntheses",
  "One published synthesis on the same comparison had a readable included-study "
  "table and was reconciled against this review trial by trial. [[cmp_checked]] "
  "checks were applied to it, of which [[cmp_confirmed]] came back clean, "
  "[[cmp_errors]] identified an error and [[cmp_absent]] identified a reporting "
  "item that is absent. Its included-study list is also the reason this review's "
  "k rose during the build: PARALLEL-HF was eligible on every axis of the frozen "
  "question, was absent from the brief this object was built from, and was "
  "recovered from that list, verified against its own publication and registry "
  "record, and pooled. The full reconciliation, the quoted evidence for every "
  "check with its location, and the decomposition of where the two reviews "
  "differ are given in the section on comparison with published syntheses."),
]

added = []
for h, t in NEW:
    if h not in have:
        rp.append(collections.OrderedDict(heading=h, text=t))
        added.append(h)

# Cross-references from the prose into the tables and figures, which is what
# makes a Results section a report rather than a caption index.
REFS = {
 "Study selection": (" The flow of records through screening, with the stages "
                     "this corpus never recorded stated as such, is shown in the "
                     "PRISMA figure."),
 "Trial characteristics": (" Characteristics of the included trials are given in "
                           "the table of included studies and their per-arm event "
                           "counts in the table of per-arm counts."),
 "Primary synthesis": (" The per-trial and pooled estimates are shown in the "
                       "forest plot. The prediction interval for a future study "
                       "runs from [[pi_low]] to [[pi_high]]."),
 "Robustness": (" Each refit is shown in the leave-one-out figure and tabulated "
                "in the leave-one-out table; [[loo_n_excluding_null]] of "
                "[[loo_n_total]] refits still exclude no difference."),
 "Risk of bias": (" Per-domain judgements from both assessors are shown in the "
                  "risk-of-bias figure."),
}
xref = []
for x in rp:
    add = REFS.get(x["heading"])
    if add and add.strip()[:24] not in x["text"]:
        x["text"] = x["text"].rstrip() + add
        xref.append(x["heading"])

json.dump(d, open(O, "w", encoding="utf-8"), indent=1, ensure_ascii=False)
print("added Results sections:", added)
print("cross-references added to:", xref)
print("Results section now has %d prose subsections" % len(rp))
