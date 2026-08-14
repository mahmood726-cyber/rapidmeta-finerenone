import io, sys

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
P = r"F:\rapidmeta-ssot-shell\ssot\projectors2.py"
s = open(P, encoding="utf-8").read()

s = s.replace(
    "from projectors import (NL, e, fmt, kv_card, fig, scatter_svg, rows_svg,\n"
    "                        funnel_svg, GRADE_DOMAINS)",
    "from projectors import (NL, e, fmt, kv_card, fig, scatter_svg, rows_svg,\n"
    "                        funnel_svg, rob_traffic_light_svg, prisma_flow_svg,\n"
    "                        not_computable_svg, GRADE_DOMAINS)", 1)

ANCHOR = "def count_figures(res, p):"
assert s.count(ANCHOR) == 1

NEW = r'''def rob_figure(canon, p):
    """Risk-of-bias traffic light, both assessors, from the stored RoB-2 block."""
    rb = canon.get("rob2") or {}
    trials = rb.get("trials") or []
    if not trials:
        return fig(not_computable_svg(
            "Risk-of-bias traffic light",
            "No per-domain RoB-2 assessment is stored in this object."),
            "Risk of bias", "rob-traffic-light.svg",
            "Not drawn, because there is nothing to draw it from.")
    doms = [d.get("domain") for d in trials[0].get("domains", [])]
    a = rb.get("assessors") or [{}, {}]
    keys = ("assessor_1_openai", "assessor_2_google")

    def cell(trial_name, domain, idx):
        for t in trials:
            if t.get("trial") != trial_name:
                continue
            for dd in t.get("domains", []):
                if dd.get("domain") == domain:
                    return (dd.get(keys[idx]) or {}).get("judgement")
        return None

    names = [t.get("trial") for t in trials]
    fams = [x.get("model_family", "assessor %d" % (i + 1))
            for i, x in enumerate(a)]
    agree = rb.get("agreement")
    return fig(rob_traffic_light_svg(names, doms, fams, cell),
               "Risk of bias, both assessors", "rob-traffic-light.svg",
               "Every cell carries BOTH independent cross-family assessments and "
               "they are not reconciled: showing one column would be a "
               "reconciliation presented as an observation. Glyph as well as "
               "colour, so the panel survives greyscale printing and colour-blind "
               "reading. %s"
               % (("Agreement as measured: %s." % p(str(agree)))
                  if agree else ""))


def prisma_figure(canon, p):
    """PRISMA flow, with the stages this corpus never recorded stated as such."""
    sc = canon.get("screening") or {}
    corpus = sc.get("corpus") or []
    if not corpus:
        return ""
    cc = sc.get("corpus_counts") or {}
    tiab = sum(v for k, v in cc.items() if str(k).startswith("TiAb"))
    full = sum(v for k, v in cc.items() if str(k).startswith("FullText"))
    inc = sum(v for k, v in cc.items() if str(k).endswith("INCLUDE"))
    und = sum(v for k, v in cc.items() if str(k).endswith("undetermined"))
    ex_tiab = cc.get("TiAb/exclude")
    ex_full = cc.get("FullText/exclude")
    import collections as _c
    ax = _c.Counter(r.get("axis_failed") for r in corpus
                    if r.get("decision") == "exclude" and r.get("axis_failed"))
    why = ", ".join("%s %d" % (k.lower(), v) for k, v in ax.most_common())
    boxes = [
        {"label": "Records identified by database searching", "n": None,
         "note": "Not recorded by the pipeline that built this corpus."},
        {"label": "Duplicates removed", "n": None,
         "note": "Not recorded; cannot be reconstructed without inventing it."},
        {"label": "Records screened on title and abstract", "n": tiab or None,
         "side": ("excluded %s" % fmt(ex_tiab)) if ex_tiab else None},
        {"label": "Full texts assessed for eligibility", "n": full or None,
         "side": ("excluded %s" % fmt(ex_full)) if ex_full else None},
        {"label": "Trials contributing to the synthesis", "n": inc or None,
         "note": ("%s record(s) remain UNDETERMINED and are not counted as "
                  "exclusions." % fmt(und)) if und else None},
    ]
    return fig(prisma_flow_svg(boxes), "PRISMA flow of records",
               "prisma-flow.svg",
               "Two boxes are drawn as NOT RECORDED rather than filled. The "
               "identification counts were never captured by the pipeline that "
               "produced this corpus and cannot be reconstructed after the fact "
               "without inventing numbers; a diagram missing its top box reads as "
               "an oversight, one that states the gap reads as a decision, and "
               "only the second is true here. Exclusion reasons across the whole "
               "corpus: %s." % p(why))


def underpowered_figures(res, p):
    """Diagnostics that this k cannot support, stated rather than drawn.

    GOSH and trial-sequential analysis are both technically computable from what
    is stored -- and both would be pictures of nothing at four studies. Drawing
    them would put a shape on the page that a reader takes as a diagnostic that
    was run and meant something. The honest rendering is the reason.
    """
    k = res.get("k") or len(res.get("per_trial") or [])
    out = ""
    out += fig(not_computable_svg(
        "GOSH plot",
        "Computable but uninformative at k = %d: the whole subset space is %d "
        "points, and its shape is read for clustering that needs an order of "
        "magnitude more studies." % (k, 2 ** k - 1)),
        "GOSH", "gosh.svg",
        "Deliberately not drawn. Every subset meta-analysis of %d trials is %d "
        "points; a cloud that small cannot show the multimodality GOSH exists to "
        "reveal, and a reader would take the picture as evidence of its absence."
        % (k, 2 ** k - 1))
    out += fig(not_computable_svg(
        "Trial-sequential analysis",
        "Not run: TSA needs a pre-specified target information size, and no "
        "anticipated relative risk reduction or control-arm event rate is "
        "registered in this object's protocol."),
        "Trial-sequential analysis", "tsa.svg",
        "TSA boundaries depend entirely on a target information size that must be "
        "pre-specified. This review's protocol registers none, so any boundary "
        "drawn here would be a parameter chosen after seeing the data -- which is "
        "the practice TSA exists to protect against.")
    mods = sorted({t.get("year") for t in
                   (res.get("per_trial") or []) if t.get("year")})
    out += fig(not_computable_svg(
        "Meta-regression bubble plot",
        "Not fitted: %d trials and no pre-specified moderator. A regression on "
        "year would spend 2 of %d degrees of freedom on a covariate this review "
        "never registered." % (k, k)),
        "Meta-regression", "bubble.svg",
        "The protocol pre-specifies no moderator, and at k = %d a meta-regression "
        "would be fitted on %d points. Not drawn rather than drawn with a caveat: "
        "a bubble plot invites reading a slope, and there is no slope here that "
        "any reader should read." % (k, k))
    return out


def count_figures(res, p):'''

s = s.replace(ANCHOR, NEW, 1)
open(P, "w", encoding="utf-8").write(s)
print("projectors2.py: rob_figure, prisma_figure, underpowered_figures")
