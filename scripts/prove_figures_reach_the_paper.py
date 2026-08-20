"""Does a figure reach the manuscript, and does one that cannot be drawn REFUSE IN PLACE?

WHY THIS EXISTS. Mahmood read `SGLT2_HF_REVIEW.html#paper` and said there was no forest
plot. There was not -- in the paper. There were THREE on the Analysis tab of the same page,
drawn by `projectors.forest_svg` from the same object. One delivered page out of 118 with a
paper panel carried a figure at all, and that one is ARNI, served by the docmodel renderer.
The manuscript projector could emit prose, tables and refusals and had no way to carry an
image.

WHAT THIS CHECKS, AND THE SECOND ONE IS THE ONE THAT GETS DROPPED FOR EXPEDIENCE:

  1. A drawable outcome PRODUCES A DRAWN FIGURE carrying a number, a caption and at least
     one source field a reader can check. A figure with no stated source is a picture.

  2. An outcome that CANNOT be plotted still occupies its numbered slot and says why. A gap
     where a funnel plot belongs reads to a reviewer as an oversight; `k = 3, and a funnel
     has almost no power below about ten trials` reads as a decision.

  3. AN OBJECT WITH NO POOLED OUTCOME GAINS NO FIGURE. This is the degenerate case. A
     refusal figure about a result that does not exist is manufactured content, which is
     registry class 58 read from the other direction -- and the metric here (`figures on the
     page`) is exactly the kind a degenerate artefact maximises, so it is guarded rather
     than trusted (class 60).

  4. THE FUNNEL'S DRAW PATH IS PROVEN BY GRAFT. Measured across the corpus, 0 of 175
     outcome blocks would draw one: 174 fall below k = 10 and the single k = 26 outcome
     carries no stored funnel panel. A branch that cannot fire on any real input is not
     evidence that it works (class 58), so the draw path is exercised against a constructed
     outcome and the graft is declared as a graft.
"""
import io
import json
import os
import sys
import glob

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(REPO, "ssot"))
from instrument_controls import require_controls          # noqa: E402
import paper_projector as ppj                             # noqa: E402


def figures_of(obj):
    """The `figures` section's figure list, or [] if the section refused."""
    for s in ppj.project(obj):
        if getattr(s, "key", None) == "figures":
            return list(getattr(s, "figures", []))
    return []


DRAWABLE = {
    "outcomes": [{"id": "primary", "name": "A registered outcome", "effect_scale": "log",
                  "null_value": 1}],
    "results": {"by_outcome": {"primary": {
        "k": 2,
        "pooled": {"point": 0.8, "ci_low": 0.7, "ci_high": 0.9, "measure": "HR"},
        "per_trial": [{"trial_id": "T1", "point": 0.75, "ci_low": 0.6, "ci_high": 0.94,
                       "log_se": 0.11},
                      {"trial_id": "T2", "point": 0.85, "ci_low": 0.7, "ci_high": 1.03,
                       "log_se": 0.10}],
    }}},
}

NO_OUTCOME = {"outcomes": [], "results": {"by_outcome": {}}}

UNPLOTTABLE = {
    "outcomes": [{"id": "primary", "name": "A registered outcome", "null_value": 1}],
    "results": {"by_outcome": {"primary": {"k": 0, "pooled": {}, "per_trial": []}}},
}


def grafted_funnel():
    """The funnel draw path, on a constructed outcome. DECLARED AS A GRAFT."""
    import math
    pts = [(math.log(0.7 + 0.02 * i), 0.08 + 0.01 * i, "T%d" % i) for i in range(12)]
    obj = {
        "outcomes": [{"id": "primary", "name": "A grafted outcome", "effect_scale": "log",
                      "null_value": 1}],
        "results": {"by_outcome": {"primary": {
            "k": 12,
            "pooled": {"point": 0.78, "ci_low": 0.70, "ci_high": 0.87, "measure": "HR"},
            "per_trial": [{"trial_id": t, "point": math.exp(le), "ci_low": math.exp(le - 2 * se),
                           "ci_high": math.exp(le + 2 * se), "log_se": se}
                          for le, se, t in pts],
            "panels": {"funnel": [{"log_effect": le, "se": se, "trial": t}
                                  for le, se, t in pts]},
        }}},
    }
    return figures_of(obj)


def main():
    gate = "--gate" in sys.argv

    drawn = figures_of(DRAWABLE)
    empty = figures_of(NO_OUTCOME)
    unplot = figures_of(UNPLOTTABLE)
    require_controls(
        "prove_figures_reach_the_paper",
        positive=("a drawable outcome yields a DRAWN figure",
                  bool(drawn) and bool(drawn[0][2]), True),
        negative=("an object with NO pooled outcome yields any figure at all",
                  bool(empty), True))

    print("")
    print("THE REFUSAL-IN-PLACE PROPERTY")
    ok_refuse = bool(unplot) and not unplot[0][2] and bool(unplot[0][3])
    print("    an outcome that cannot be plotted keeps a numbered slot   %s"
          % ("YES" if ok_refuse else "NO -- IT VANISHED"))
    if ok_refuse:
        print("        Figure %d reason: %s" % (unplot[0][0], unplot[0][3][:96]))

    print("")
    print("THE FUNNEL DRAW PATH, PROVEN BY GRAFT (declared: this input is CONSTRUCTED)")
    gf = grafted_funnel()
    fun = [f for f in gf if f[1].startswith("Funnel")]
    graft_ok = bool(fun) and bool(fun[0][2])
    print("    k = 12 with a stored funnel panel draws a funnel          %s"
          % ("YES, %d bytes" % len(fun[0][2]) if graft_ok else "NO -- THE PATH IS DEAD"))
    print("    0 of 175 real outcome blocks reach this branch, which is why it is grafted.")

    print("")
    print("EVERY FIGURE CARRIES A NUMBER, A CAPTION AND A SOURCE")
    bad = []
    for n, cap, svg, reason, fields in drawn + unplot + gf:
        if not isinstance(n, int) or not cap.strip() or not fields:
            bad.append((n, cap[:40]))
    print("    figures inspected %d, missing number/caption/source %d"
          % (len(drawn + unplot + gf), len(bad)))
    for b in bad:
        print("        %r" % (b,))

    # ---- THE CORPUS, AGAINST THE PREDICTION --------------------------------------------
    # THE POSITIVE PROPERTY IS `IS A TOPIC OBJECT THAT PARSES`, and objects that are not
    # are COUNTED AND NAMED rather than skipped -- open item O2, which this project has
    # already reproduced once in a new instrument.
    objs = fig_draw = fig_ref = no_outcome_objs = with_figs = 0
    unreadable = []
    for path in sorted(glob.glob(os.path.join(REPO, "ssot", "*", "*.json"))):
        topic = os.path.basename(os.path.dirname(path))
        if os.path.basename(path) != topic + ".json":
            continue
        try:
            obj = json.load(io.open(path, encoding="utf-8"))
        except ValueError:
            unreadable.append(topic)
            continue
        objs += 1
        figs = figures_of(obj)
        if figs:
            with_figs += 1
            fig_draw += len([f for f in figs if f[2]])
            fig_ref += len([f for f in figs if not f[2]])
        elif not ((obj.get("results") or {}).get("by_outcome") or {}):
            no_outcome_objs += 1

    print("")
    print("THE CORPUS, MEASURED AFTER THE CHANGE")
    print("    topic objects read                              %d" % objs)
    if unreadable:
        print("    objects that do not parse (NAMED, not dropped) %d -- %s"
              % (len(unreadable), ", ".join(unreadable)))
    print("    objects that GAIN at least one figure           %d" % with_figs)
    print("    objects with NO outcome, gaining NO figure      %d" % no_outcome_objs)
    print("    figures DRAWN                                   %d" % fig_draw)
    print("    figures REFUSED IN PLACE, with a reason         %d" % fig_ref)
    print("    total figure slots                              %d" % (fig_draw + fig_ref))

    failed = (not ok_refuse) or (not graft_ok) or bool(bad)
    if failed:
        print("")
        print("FAILED. A figure vanished instead of refusing, or the grafted draw path is")
        print("dead, or a figure reached the page without a source a reader can check.")
    if gate and failed:
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
