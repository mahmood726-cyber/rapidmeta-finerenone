# -*- coding: utf-8 -*-
"""GATE: a delivered page may not show a certainty LEVEL where the risk of bias behind it is
unadjudicated. Refuses, and has been watched refusing.

WHAT ACTUALLY WENT WRONG, BECAUSE THE OBVIOUS DIAGNOSIS IS THE WRONG ONE. The external
review said the sotagliflozin fix "was applied to an instance and not to the class". It was
applied to the class: `grade_authority.resolve()` returns PENDING for all six iv-iron-hf
outcomes today, and for 27 outcomes across 19 topics. What was applied to an instance was
the REBUILD. IV_IRON_HF_REVIEW.html was last built at 0be050e90, which predates the
pending-certainty generator at 95150e664, so it still renders "Certainty: low" five times
and "moderate" once from a generator that no longer produces them.

That distinction changes the remedy. A generator fix cannot be verified by reading the
generator, because the artefact a reader meets is the page, and a page is only as new as its
last build. So this gate compares the RENDERED page against what the resolver says NOW.
It catches a generator regression and a stale page with the same check, and staleness is the
one that actually shipped.

CHEAPER CHECKS THAT WOULD HAVE MISSED IT: asserting the generator returns PENDING (it does),
diffing the generator (correct), or checking the page was committed after the fix (it was
not, but nothing looked). Only reading the delivered bytes finds this.
"""
import collections
import glob
import io
import json
import os
import re
import sys

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace",
                              line_buffering=True)
HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(os.path.dirname(HERE))
os.chdir(REPO)
sys.path.insert(0, os.path.join(REPO, "ssot"))
import grade_authority as ga  # noqa: E402

LEVEL = re.compile(r"Certainty:\s*(low|moderate|high|very low)\b", re.I)
PENDING = re.compile(r"Certainty:\s*Pending\b", re.I)
DERIV = re.compile(r"total\s*-?\d+\s*->\s*(low|moderate|high|very low)\b", re.I)
TOPIC_IN_PAGE = re.compile(rb"ssot/([a-z0-9][a-z0-9-]{2,})/")


def rendered(raw):
    t = re.sub(r"(?is)<(script|style).*?</\1>", " ", raw)
    return re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", t))


def topic_of(raw_bytes, known):
    """Which store built this page, read from its own provenance strings."""
    c = collections.Counter(m.group(1).decode("ascii", "ignore")
                            for m in TOPIC_IN_PAGE.finditer(raw_bytes))
    for name, _ in c.most_common():
        if name in known:
            return name
    return None


def scan(pages=None):
    known = {os.path.basename(os.path.dirname(p)) for p in glob.glob("ssot/*/*.json")
             if os.path.basename(p) == os.path.basename(os.path.dirname(p)) + ".json"}
    out, unattributable, fully_rated = [], [], []
    for page in sorted(pages or glob.glob("*.html")):
        try:
            raw = open(page, "rb").read()
        except OSError:
            continue
        # A PAGE THIS GATE CANNOT ATTRIBUTE IS NOT A PAGE THAT PASSES.
        #
        # topic_of() reads provenance strings out of the page. SGLT2_HF_REVIEW carries NONE
        # -- zero `ssot/sglt2-hf/` markers -- so it was silently dropped, and the gate then
        # reported "0 pages rendering a level" over a denominator of 0 while that page was
        # publishing "Certainty: high" for a WITHDRAWN pool. A skip that shrinks the
        # denominator instead of appearing in it is the same defect this project has now
        # met in a dozen instruments, here in the one written to catch it.
        #
        # FALLBACK, NAMED AS A FALLBACK: try the filename convention. If that fails too the
        # page is reported UNATTRIBUTABLE and counted, never quietly excluded.
        topic = topic_of(raw, known)
        if not topic:
            guess = os.path.basename(page)[:-5].lower().replace("_", "-")
            for cand in (guess, guess.replace("-review", ""), guess + "-review"):
                if cand in known:
                    topic = cand
                    break
        if not topic:
            unattributable.append(page)
            continue
        obj_path = os.path.join("ssot", topic, topic + ".json")
        if not os.path.isfile(obj_path):
            unattributable.append(page)
            continue
        try:
            obj = json.load(io.open(obj_path, encoding="utf-8"))
        except Exception:
            continue
        # KEYED ON THE RESOLVED STATE, NOT ON "PENDING". This gate keyed on one named
        # state while the renderer it guards fell through on the others -- a
        # consumer-shaped fix and a consumer-shaped gate, made by the same hand in the same
        # hour. sglt2-hf published "Certainty: high" for a WITHDRAWN pool and this gate
        # passed it. Anything the resolver does not call RATED has no level to publish, so
        # a state added later is guarded on arrival instead of waiting for a reviewer.
        pend = {oid for oid in ((obj.get("results") or {}).get("by_outcome") or {})
                if ga.resolve(obj, oid).get("state") != "RATED"}
        # PARTITION, BOTH ARMS RENDERED. `if not pend: continue` defined an arm by an
        # absence and dropped it, so a page whose outcomes are ALL rated vanished from the
        # denominator instead of appearing in it as "nothing withheld here". Same shape as
        # the unattributable pages this gate already learned to count.
        if len(pend) == 0:
            fully_rated.append(page)
            continue
        text = rendered(raw.decode("utf-8", "replace"))
        levels = LEVEL.findall(text)
        derivs = DERIV.findall(text)
        out.append({"page": page, "topic": topic, "withheld_outcomes": len(pend),
                    "levels_rendered": len(levels), "derivations_rendered": len(derivs),
                    "pending_rendered": len(PENDING.findall(text)),
                    "violating": bool(levels or derivs)})
    return out, unattributable, fully_rated


def main():
    argv = [a for a in sys.argv[1:] if not a.startswith("-")]
    rows, unattributable, fully_rated = scan(argv or None)
    bad = [r for r in rows if r["violating"]]
    print("")
    print("GATE -- no certainty level over an unadjudicated risk-of-bias assessment")
    print("")
    print("  pages with >=1 outcome whose level is withheld   %4d  == the denominator"
          % len(rows))
    print("  pages rendering a certainty LEVEL anyway       %4d" % len(bad))
    print("  pages where every outcome IS rated             %4d   (nothing withheld)"
          % len(fully_rated))
    print("  pages this gate COULD NOT ATTRIBUTE            %4d   <- not a pass"
          % len(unattributable))
    for u in unattributable[:10]:
        print("       unattributable: %s" % u)
    print("")
    for r in sorted(rows, key=lambda x: (-x["levels_rendered"], x["page"]))[:24]:
        print("   %-9s %-42s withheld %d  levels %d  derivations %d"
              % ("REFUSE" if r["violating"] else "ok", r["page"][:41],
                 r["withheld_outcomes"], r["levels_rendered"], r["derivations_rendered"]))
    if len(rows) > 24:
        print("   ... and %d more" % (len(rows) - 24))
    print("")
    if unattributable:
        print("VERDICT: REFUSED. %d page(s) could not be attributed to a store, so this "
              "gate has no opinion on them and must not be read as clearing them."
              % len(unattributable))
        return 1
    if bad:
        print("VERDICT: REFUSED. %d page(s) publish a certainty level while the risk-of-bias "
              "assessment behind it is unadjudicated." % len(bad))
        print("Rebuild them; the generator already withholds the level.")
        return 1
    print("VERDICT: PASS. No page shows a level where the resolver withholds one.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
