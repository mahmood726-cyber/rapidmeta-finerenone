"""What does a DEGENERATE artefact score on each metric that guards something?

THE QUESTION, AND IT IS THE WHOLE FILE: before a metric guards anything, ask what an EMPTY
page scores on it. A page of boilerplate. A page of pure refusals. IF ANY OF THEM BEATS A
GOOD PAGE, THE METRIC WILL BE ENFORCED AGAINST THE GOOD PAGE EVENTUALLY.

THE INSTANCE THAT MADE THIS A FILE. `BOCOCIZUMAB_LIPID_AUTO_FULL_REVIEW.html` served the
honest absent-state banner -- "No manuscript has been generated for
bococizumab-lipid-review" -- two sentences, and ZERO machine-vocabulary sentences. A perfect
score. The rebuild gave it an 81-sentence manuscript carrying 11 machine sentences, and the
rollout's guard read that as a regression and RESTORED THE EMPTY TAB. Twice: once in the
batch predicate and once, independently, in the invariance check.

    A QUALITY METRIC THAT A BLANK PAGE MAXIMISES WILL, GIVEN A GUARD, ACTIVELY DEFEND
    BLANKNESS.

It is not the stale-baseline fault and it is not the concurrency fault. Those compared the
WRONG VALUES. This one compared the right values correctly and reached the wrong verdict,
because the metric assumed both sides were the same KIND of thing.

WHAT THIS FILE DOES. It scores three degenerate artefacts on every metric the rollout uses
as a predicate, and reports whether a guard on that metric would prefer the degenerate one
to a real page. It does not guess: the artefacts are constructed and the real metric
functions are called on them.

    EMPTY       the absent-state banner: no manuscript, two sentences
    BOILERPLATE a manuscript of section headings and nothing beneath them
    REFUSALS    a manuscript whose every section is a correctly-worded refusal

THE THIRD IS THE UNCOMFORTABLE ONE. A page of pure refusals is, by this project's own
standard, HONEST -- refusing by name is the required behaviour. It also carries almost no
machine vocabulary, no unglossed statistics and no field paths in prose, so it scores at or
near the top of every readability measure written tonight. P47 exists because that page
reads as complete on totals; this file is the same observation pointed at the metrics.
"""
import io
import os
import sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from instrument_controls import require_controls
import lint_paper_reads_as_prose as L
import prove_register_change_moved_no_content as PROVE

HEAD = '<span id="paper"></span><h2 id="paper-paper">Paper</h2>'
TAIL = '<section class="panel" id="pn-analysis">'

EMPTY = HEAD + (
    "<h3>Paper Studio</h3><p>Not held in this object. No manuscript has been generated "
    "for this review. A manuscript belongs to one review, so none from another review is "
    "shown here.</p>") + TAIL

BOILERPLATE = HEAD + "".join(
    "<h3>%s</h3><p>This section is part of the standard structure of a systematic "
    "review report and is included here for completeness of presentation.</p>" % h
    for h in ("Abstract", "Introduction", "Methods", "Results", "Discussion",
              "Conclusions", "Limitations", "References")) + TAIL

REFUSALS = HEAD + "".join(
    "<h3>%s</h3><div class='absent-state' role='note'><strong>Refused:</strong> the %s -- "
    "no field on this object supports it, and none is generated here: a %s written by the "
    "renderer would be an argument no field supports.</div>" % (h, h.lower(), h.lower())
    for h in ("Abstract", "Introduction", "Methods", "Results", "Discussion",
              "Conclusions", "Limitations", "Certainty of the evidence")) + TAIL

# A real page, for the comparison. Sentences with the register we actually want.
REAL = HEAD + (
    "<h3>Results</h3><p>The pooled hazard ratio for cardiovascular death or "
    "hospitalisation for heart failure was 0.76 (0.71 to 0.83) across three trials, "
    "against placebo.<sup class='prov-ref'>1</sup></p>"
    "<p>The trials' results were closely consistent with one another: I-squared, the share "
    "of the variation between them that is more than chance alone would produce, was 0%; "
    "the estimated variance of the true effects between trials (tau-squared) was 0.<sup "
    "class='prov-ref'>2</sup></p>"
    "<p>DELIVER does not post the first-event two-component outcome, so a pool of three "
    "trials we can fully vouch for was preferred to a pool of four with one input we "
    "cannot.<sup class='prov-ref'>3</sup></p>"
    "<div class='prov-block'><p class='prov-title'>Where the statements in this section "
    "come from, in order</p><ol class='prov-list'><li><code>results.by_outcome.x.pooled"
    "</code></li></ol></div>") + TAIL


def score(name, raw):
    tmp = os.path.join(REPO, "outputs", "_degenerate_%s.html" % name)
    os.makedirs(os.path.dirname(tmp), exist_ok=True)
    io.open(tmp, "w", encoding="utf-8", newline=chr(10)).write(raw)
    try:
        m = L.measure(tmp)
        fp = PROVE.flow_paths(raw)
        if m is None:
            return None
        rate = (100.0 * m["machine"] / m["sentences"]) if m["sentences"] else 0.0
        return {"sentences": m["sentences"], "machine": m["machine"], "rate": rate,
                "flow_paths": fp}
    finally:
        if os.path.exists(tmp):
            os.remove(tmp)


def main():
    cases = [("EMPTY", EMPTY), ("BOILERPLATE", BOILERPLATE), ("REFUSALS", REFUSALS),
             ("REAL", REAL)]
    scores = dict((n, score(n, raw)) for n, raw in cases)

    # CONTROL. The whole file is worthless if the empty page does NOT beat the real one --
    # that is the finding, and if it fails to reproduce, the metrics have changed and the
    # rest of this output describes a repository that no longer exists.
    e, r = scores["EMPTY"], scores["REAL"]
    require_controls(
        "audit_degenerate_artefact_scores",
        positive=("the EMPTY page's machine-vocabulary rate is no worse than the REAL "
                  "page's -- the finding this file exists to state",
                  e is not None and r is not None and e["rate"] <= r["rate"], True),
        negative=("the REAL page scores as a degenerate one on sentence count",
                  r is not None and r["sentences"] < 3, True))

    print("")
    print("%-12s %10s %10s %10s %12s" % ("artefact", "sentences", "machine", "rate %",
                                         "flow paths"))
    print("-" * 60)
    for n, _raw in cases:
        s = scores[n]
        if s is None:
            print("%-12s   NO PAPER PANEL FOUND" % n)
            continue
        print("%-12s %10d %10d %9.0f%% %12d"
              % (n, s["sentences"], s["machine"], s["rate"], s["flow_paths"]))

    print("")
    print("WOULD A GUARD ON EACH METRIC PREFER A DEGENERATE PAGE TO THE REAL ONE?")
    print("")
    verdicts = []
    for metric, better in (("machine sentences (absolute)", lambda a, b: a["machine"] <= b["machine"]),
                           ("machine-vocabulary RATE", lambda a, b: a["rate"] <= b["rate"]),
                           ("field paths in the flow", lambda a, b: a["flow_paths"] <= b["flow_paths"]),
                           ("sentence count", lambda a, b: a["sentences"] >= b["sentences"])):
        losers = [n for n in ("EMPTY", "BOILERPLATE", "REFUSALS")
                  if scores[n] and scores["REAL"] and better(scores[n], scores["REAL"])]
        verdicts.append((metric, losers))
        if losers:
            print("    %-32s DEFENDS %s" % (metric, ", ".join(losers)))
        else:
            print("    %-32s prefers the real page" % metric)

    print("")
    print("READ THE `sentence count` ROW CAREFULLY. It is the only metric here that a blank")
    print("page LOSES, which is why the rollout's gained-a-manuscript branch is keyed on it")
    print("rather than on any of the quality measures. A COUNT OF THINGS PRESENT IS THE ONLY")
    print("ONE OF THESE A DEGENERATE ARTEFACT CANNOT WIN, and it is the crudest of them.")
    print("")
    print("AND THE REFUSALS PAGE IS THE UNCOMFORTABLE CASE. Refusing by name is REQUIRED")
    print("behaviour in this project. A page that does nothing else is honest, scores at or")
    print("near the top of every readability measure written tonight, and is worthless to a")
    print("reader. P47 exists for that reason; these metrics do not know it.")


if __name__ == "__main__":
    main()
