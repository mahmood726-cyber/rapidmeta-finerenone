"""extractor canonical.json  ->  SSOT object the tabbed projector can consume.

WHAT THIS UNBLOCKS
    28 cardiology pages and then the whole infectious-disease set have an extractor
    object but no SSOT object, so they cannot be built through the tabbed projector
    at all. This is the one build that changes that.

THE GAP IS THE DESIGN, NOT AN OBSTACLE
    The extractor recovered TRIALS, ARMS, EFFECTS and a POOLED RESULT. It did not
    recover a protocol, a search, a screening log, a risk-of-bias assessment, a
    GRADE rating, sources or a manuscript, because none of those are in the page it
    read. Every one of those becomes an HONEST-STATE panel naming its own absence.

    THE CONVERTER NEVER SYNTHESISES A VALUE AND NEVER FALLS BACK TO ANOTHER PAGE.
    A silent fallback is exactly what put ARNI's manuscript -- and its trials, and
    its Table 4 -- onto four unrelated pages this morning. The rule that stopped it
    was making the failure loud instead of convenient, and it is the rule here.

SCALE IS READ, NEVER ASSUMED
    reported.logEffect is a MISNOMER: trials[].effect.scale is 'log' for ratio
    measures and 'natural' for mean differences. Exponentiating a natural-scale MD
    gives ~0, which is how four MD pages were written off as unfixable. The
    back-transform is chosen from the recorded scale.

WHAT A SUCCESSFUL CONVERSION DOES NOT ESTABLISH -- written before it ran
    - NOT that the pooled estimate is CORRECT. It carries the extractor's number
      across unchanged. If the pooling was invalid -- harm mixed with efficacy,
      distinct agents pooled, a duplicated trial effect -- conversion preserves the
      invalidity faithfully. That is why withdrawn pages are refused outright.
    - NOT that the trial set is complete or correctly attributed.
    - NOT that absent sections are absent from the REVIEW; only that they are absent
      from the extractor object. A screening log may exist on paper and be unrecorded.
    - NOT that the page is publishable. It makes a page BUILDABLE.
"""
from __future__ import annotations
import json, math, os, re, sys, io, datetime

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace") \
    if __name__ == "__main__" else sys.stdout

OBJ = r"F:\E156\outputs\codex-corpus-scan\extract\full_run"
SSOT = r"F:\rapidmeta-ssot-shell"
NCT = re.compile(r"NCT\d{8}")

# One marker for every field the extractor could not recover. A reader seeing it
# knows the value is ABSENT FROM THE SOURCE rather than absent from the review.
# Reader-facing wording: this string CAN reach the rendered page, so it must read as
# a sentence a reader understands, not as an internal sentinel. It leaked into
# visible text nine times on the first converted build.
UNREC = "not recorded on the page this object was extracted from"


class Refused(Exception):
    """The converter declines. Refusing is a valid outcome and is never a silent skip."""


def withdrawn_pages(index_html):
    """Every page whose live index state says we are NOT publishing a pooled value.

    THE FIRST VERSION READ GRID CARDS ONLY and the batch dry-run caught what it
    missed -- three classes, each of which conversion would have resurrected:

      TABLE-ROW WITHDRAWALS. AZITHROMYCIN_CHILD_MORTALITY has no grid card; it was
      withdrawn in its table row. It came back as convertible at HR 0.86, k=2 --
      the DUP-1 page, where both trials carry log(0.86) so k=2 is arithmetically
      k=1 and I-squared 0 is an artefact of the duplication.

      "REPORTED SEPARATELY, NOT POOLED" cards. MALARIA_VACCINE and
      HIV_PREP_INJECTABLE deliberately present per-trial results and decline to
      pool. Converting them would manufacture the pooled estimate their cards
      exist to avoid.

      HARM-FLAGGED PAGES NEVER PUBLISHED. DABIGATRAN_AF, DABIGATRAN_STROKE and
      WARFARIN_AF carry no number on the index at all, pending a decision. Absence
      of a card is not permission; it is an unfinished decision.

    A page we decided not to publish a number for must not acquire one by being
    rebuilt through a different pipeline.
    """
    out = set()
    WITHHELD = re.compile(r"withdrawn|not analysable|not poolable|not pooled|"
                          r"reported separately", re.I)
    for m in re.finditer(r'<a href="([A-Z0-9_]+\.html)" class="card [^"]*">'
                         r'<span class="name">[^<]*</span><span class="pub">(.*?)</span></a>',
                         index_html):
        if WITHHELD.search(m.group(2)):
            out.add(m.group(1))
    # table rows: <a href=X>label</a> ... <td>estimate cell</td>
    for m in re.finditer(r'<a href="([A-Z0-9_]+\.html)"[^>]*>[^<]*</a></td><td>[^<]*</td>'
                         r'<td[^>]*>[^<]*</td><td[^>]*>([^<]*)</td>', index_html):
        if WITHHELD.search(m.group(2)):
            out.add(m.group(1))
    # explicitly held pending a human decision -- never inferred from the index
    out |= {"DABIGATRAN_AF_AUTO_FULL_REVIEW.html",
            "DABIGATRAN_STROKE_AUTO_FULL_REVIEW.html",
            "WARFARIN_AF_AUTO_FULL_REVIEW.html"}
    return out


def back_transform(point, lo, hi, scale):
    """exp() for log scale, identity for natural. Chosen from the record."""
    if scale == "log":
        return math.exp(point), math.exp(lo), math.exp(hi)
    return point, lo, hi





def skeleton(template, keep):
    """Structure from a template object, VALUES from nowhere.

    WHY THIS SHAPE-MATCHES INSTEAD OF GUESSING FIELD BY FIELD
        The projector reads a long tail of structural keys - pool_uniformity as a
        dict, handbook with a 'sections' list, and so on - and patching them one
        KeyError at a time took five rounds and was still going. That is the
        symptom-fix pattern this project refuses: each patch made one error go away
        without making the object structurally right.

    THE DANGER, AND THE GUARD
        Copying structure from another review is EXACTLY the move that put ARNI's
        manuscript on four unrelated pages this morning. So every leaf is replaced:
        strings become the UNREC marker, numbers become None, lists become empty.
        NOTHING from the template's content survives - only the shape of its keys.
        subject_match() then re-checks the finished object against this page's own
        extractor output, so a leak cannot reach a build even if this is wrong.
    """
    if isinstance(template, dict):
        return {k: (template[k] if k in keep else skeleton(template[k], keep))
                for k in template}
    if isinstance(template, list):
        return []
    if isinstance(template, bool) or template is None:
        return None
    if isinstance(template, (int, float)):
        return None
    return UNREC


def _per_trial(t, scale, est):
    """The per-trial row the projector renders, in its own shape.

    Every displayed number here is DERIVED and says so in `derivation`. The
    extractor holds an estimate and a variance on the analysis scale and nothing
    else; the point and interval are computed and back-transformed. Compare the
    authored objects, where `derivation` reads "the printed hazard ratio" because a
    source actually printed it. The two must never be confusable.
    """
    import math as _m
    e = t.get("effect") or {}
    i = t.get("identity") or {}
    est_, var = e.get("estimate"), e.get("variance")
    se = _m.sqrt(var) if var else None
    pt = lo = hi = None
    if est_ is not None:
        l = est_ - 1.959963984540054 * se if se is not None else None
        h = est_ + 1.959963984540054 * se if se is not None else None
        if scale == "log":
            pt = _m.exp(est_); lo = _m.exp(l) if l is not None else None
            hi = _m.exp(h) if h is not None else None
        else:
            pt, lo, hi = est_, l, h
    rid = str(i.get("id") or "")
    return {"trial_id": rid or (i.get("label") or "unknown"),
            "nct": i.get("registry_id") if NCT.fullmatch(str(i.get("registry_id") or "")) else None,
            "measure": e.get("measure") or (est or {}).get("effect_measure") or "",
            "point": pt, "ci_low": lo, "ci_high": hi, "ci_level": 95,
            "log_point": est_ if scale == "log" else None,
            "log_se": se if scale == "log" else None,
            "estimand_id": "primary",
            "population": UNREC,
            "derivation": ("DERIVED by conversion: the extractor recovered an estimate and a "
                           "variance on the analysis scale; the point and interval are "
                           "estimate +/- 1.96*sqrt(variance), back-transformed. No source "
                           "printed this interval.")}


def _trial_effect(t, scale):
    """Per-trial block in the shape the projector reads: point / ci_low / ci_high.

    The extractor stores estimate + variance on the analysis scale. The projector
    needs a displayed point and interval, so they are COMPUTED here as
    estimate +/- 1.96*sqrt(variance) and back-transformed. That is a DERIVATION and
    is labelled one: derived_from and derivation_note say so on every trial, so a
    reader can never mistake a computed interval for one the source printed. This
    is the same distinction the Extraction tab makes between READ and DERIVED, and
    the reason it exists is MORDOR-I -- a ratio computed from a percentage
    reduction and then presented as if the paper had reported it.
    """
    import math as _m
    e = t.get("effect") or {}
    est, var = e.get("estimate"), e.get("variance")
    pt = lo = hi = None
    if est is not None:
        se = _m.sqrt(var) if var else None
        l = est - 1.959963984540054 * se if se is not None else None
        h = est + 1.959963984540054 * se if se is not None else None
        if scale == "log":
            pt = _m.exp(est)
            lo = _m.exp(l) if l is not None else None
            hi = _m.exp(h) if h is not None else None
        else:
            pt, lo, hi = est, l, h
    return {
        "effect": {"measure": e.get("measure"), "scale": scale,
                   "point": pt, "ci_low": lo, "ci_high": hi, "ci_level": 95,
                   "analysis_scale_estimate": est, "analysis_scale_variance": var,
                   "derived_from": "extractor recovery from the published page",
                   "derivation_note": (
                       "The point estimate and interval shown here are DERIVED, not read: the "
                       "extractor recovered an estimate and a variance on the analysis scale, "
                       "and the interval is estimate +/- 1.96*sqrt(variance) back-transformed. "
                       "No source document was consulted and no source sentence is recorded.")},
        "provenance": {"tag": "RECOVERED", "source_quotes": [],
                       "quote_note": ("No verbatim source sentence is held for this value. It was "
                                      "recovered from the page's own embedded data, so it can be "
                                      "traced to the page but NOT to a paper.")},
        "source_url": None,
        "analysed": {a.get("role"): a.get("n") for a in (t.get("arms") or [])},
    }


def convert(page, ex, withdrawn):
    if page in withdrawn:
        raise Refused("%s carries a withheld state on the live index. Its pooled value was "
                      "removed because the POOLING was invalid, not because the arithmetic "
                      "was wrong, so converting it would resurrect an invalid estimate in a "
                      "new wrapper." % page)
    c = ex.get("canonical") or {}
    trials = c.get("trials") or []
    if not trials:
        raise Refused("no trials in the extractor object: nothing to build a review from")
    est = c.get("estimand") or {}
    rep = ((c.get("result") or {}).get("reported")) or {}
    if rep.get("logEffect") is None:
        raise Refused("no pooled result in the extractor object")

    scales = {(t.get("effect") or {}).get("scale") for t in trials}
    if len(scales) > 1:
        raise Refused("trials disagree on effect scale %s: the back-transform would be "
                      "wrong for at least one of them" % sorted(scales))
    scale = scales.pop() or "log"
    pt, lo, hi = back_transform(rep["logEffect"], rep["lci"], rep["uci"], scale)

    stem = page[:-5]
    app = stem.lower().replace("_", "-")
    oid = "primary"
    tpl = json.loads(open(os.path.join(SSOT, "ssot", "sotagliflozin-hf",
                                       "sotagliflozin-hf.json"),
                          encoding="utf-8", errors="replace").read())
    base = skeleton(tpl, keep=set())
    base.pop("results", None); base.pop("outcomes", None); base.pop("inputs", None)
    base.pop("sources", None)
    ssot = {**base, **{
        "app_id": app,
        "schema_version": "2-converted-from-extractor",
        "title": est.get("outcome_definition") or stem.replace("_", " ").title(),
        "question": est.get("outcome_definition") or "",
        "built": datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%MZ"),
        "build_mode": "CONVERTED",
        "conversion_note": (
            "This object was CONVERTED from an extractor recovery artefact, not authored. "
            "The trials, arms, effects and pooled result below were recovered from the "
            "published page. Everything a review also needs -- protocol, search, screening "
            "log, risk-of-bias assessment, certainty rating, sources and manuscript -- is "
            "ABSENT FROM THE SOURCE and is recorded as absent. Nothing is substituted from "
            "any other review."),
        "sources": {},
        # Fields the projector needs but the extractor never recovered are filled with
        # an explicit UNRECORDED marker, never with a plausible default. "placebo" is
        # the commonest comparator in this corpus and would be right most of the time,
        # which is precisely why guessing it is dangerous: a wrong comparator on a page
        # nobody checks reads exactly like a right one.
        "outcomes": [{"id": oid,
                      "name": est.get("outcome_definition") or "primary outcome",
                      "definition": est.get("outcome_definition") or UNREC,
                      "definition_note": UNREC,
                      "measure": est.get("effect_measure") or "",
                      "effect_scale": scale,
                      "type": "primary",
                      "estimand": {"id": oid, "family": UNREC, "model": est.get("model") or UNREC},
                      "comparator": UNREC, "comparator_type": UNREC,
                      "direction_of_benefit": UNREC,
                      "null_value": 0 if scale == "natural" else 1}],
        "inputs": {"trials": [{
            "id": str((t.get("identity") or {}).get("id") or ""),
            "name": (t.get("identity") or {}).get("label") or "",
            "nct": (lambda i: i if NCT.fullmatch(str(i or "")) else None)(
                (t.get("identity") or {}).get("registry_id")),
            "pmid": (t.get("identity") or {}).get("pmid"),
            "arms": [{"label": a.get("label") or a.get("role"), "role":
                      "treatment" if a.get("role") == "intervention" else "control",
                      "events": a.get("events"),
                      "participants": a.get("n")} for a in (t.get("arms") or [])],
            "by_outcome": {oid: _trial_effect(t, scale)},
        } for t in trials]},
        "config": {"model": est.get("model") or "", "method": est.get("method") or "",
                   "scale": scale},
        "results": {"by_outcome": {oid: {
            "k": rep.get("k"),
            "estimand_id": oid, "estimand_id_means": UNREC,
            "model": est.get("model") or UNREC,
            "estimator": est.get("method") or UNREC,
            "estimator_used": est.get("method") or UNREC,
            # The overlay must supply EVERY key the projector reads, not a simpler
            # dict of my own: replacing handbook wholesale dropped 'sections', which
            # the projector joins into a string. A partial overlay over a correct
            # skeleton is worse than no overlay - it looks filled and is not.
            "handbook": {"decision": "NOT RECORDED - no methods decision was recoverable "
                                     "from the page",
                         "sections": [],
                         "conformance": UNREC},
            "comparator_type": UNREC,
            "favours": ("treatment" if (pt is not None and ((scale=="log" and pt<1) or (scale!="log" and pt<0)))
                        else "control" if pt is not None else UNREC),
            "poolable": True,
            "poolable_reason": ("The extractor recovered a pooled result from this page, so the "
                                "page pooled these trials. Whether they SHOULD have been pooled "
                                "is not established by conversion - several pages in this corpus "
                                "pooled harm with efficacy, or distinct agents, and their "
                                "estimates were withdrawn for that reason."),
            "estimand_homogeneous_across_cohorts": None,
            "pool_uniformity": {"effect_measure": ["NOT ESTABLISHED", UNREC],
                                "estimand": ["NOT ESTABLISHED", UNREC]},
            "heterogeneity": {"i2": rep.get("I2"), "tau2": rep.get("tau2"), "q": rep.get("Q"),
                              "df": (rep.get("k") - 1) if rep.get("k") else None},
            "heterogeneity_status": UNREC,
            "grade": None,
            "cross_engine": None,
            "sensitivity": None,
            "single_study_ref": None,
            "per_trial": [_per_trial(t, scale, est) for t in trials],
            "pooled": {"measure": est.get("effect_measure") or "",
                       "point": pt, "ci_low": lo, "ci_high": hi, "ci_level": 95},
        }}},
        # hard-required by the projector; each states its own absence rather than
        # being omitted, so the tab renders an honest state instead of failing.
        "manuscript": None,
        "risk_of_bias_verdict": None,
        "carried_contrasts": [],
        "absent_from_source": {
            "protocol": "No protocol or registration record was recoverable from the page.",
            "search": "No search strategy was recoverable from the page.",
            "screening": "No screening log was recoverable from the page.",
            "rob2": "No risk-of-bias assessment was recoverable from the page.",
            "grade": "No certainty rating was recoverable from the page.",
            "sources": "No source registry was recoverable from the page, so no value on this "
                       "page carries a resolvable link or a quoted source sentence.",
            "manuscript": "No manuscript exists for this review."},
    }}
    return ssot


def subject_match(ssot, ex):
    """HARD GATE. Every registration id in the converted object must come from THIS
    page's extractor object. Not a report -- a refusal."""
    src = set(NCT.findall(json.dumps(ex.get("canonical") or {}, ensure_ascii=False)))
    got = set(NCT.findall(json.dumps(ssot, ensure_ascii=False)))
    foreign = sorted(got - src)
    if foreign:
        raise Refused("SUBJECT-MATCH FAILED: %s appear in the converted object but not in "
                      "this page's own extractor object" % foreign[:5])
    return len(got)


def main() -> int:
    page = sys.argv[1]
    ex = json.loads(open(os.path.join(OBJ, page + ".canonical.json"),
                         encoding="utf-8", errors="replace").read())
    idx = open(os.path.join(SSOT, "index.html"), encoding="utf-8", errors="replace").read()
    wd = withdrawn_pages(idx)
    try:
        s = convert(page, ex, wd)
    except Refused as e:
        print("REFUSED %s\n  %s" % (page, e))
        return 2
    n = subject_match(s, ex)
    rep = ((ex["canonical"].get("result") or {}).get("reported")) or {}
    p = s["results"]["by_outcome"]["primary"]["pooled"]
    print("converted %s -> app_id=%s" % (page, s["app_id"]))
    print("  scale=%s  stored logEffect=%.6f -> displayed %s %.4f (%.4f to %.4f)"
          % (s["config"]["scale"], rep["logEffect"], p["measure"], p["point"],
             p["ci_low"], p["ci_high"]))
    print("  k=%s  trials=%d  registration ids=%d (all from this page's own object)"
          % (s["results"]["by_outcome"]["primary"]["k"], len(s["inputs"]["trials"]), n))
    print("  absent-from-source: %s" % ", ".join(sorted(s["absent_from_source"])))
    out = sys.argv[2] if len(sys.argv) > 2 else None
    if out:
        os.makedirs(os.path.dirname(out), exist_ok=True)
        json.dump(s, open(out, "w", encoding="utf-8"), indent=1)
        print("  written: %s" % out)
    return 0


if __name__ == "__main__":
    sys.exit(main())
