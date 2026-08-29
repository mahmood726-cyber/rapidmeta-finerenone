# -*- coding: utf-8 -*-
"""COVERAGE: what each component can see, over the population it claims to police.

⛔ WHY THIS EXISTS, AND IT IS ABOUT MY OWN WORK. Four components were built and reported as
"landed in the harness" -- an integrity layer, an estimand statement, both intervals, a currency
query. Each was verified by regenerating a page and reading it back. Each verification passed.

Then the population was counted: the integrity layer was on ONE page of 1,470, and it was the
HAND-BUILT pilot, put there by hand rather than by the generator. The other three were on ZERO.

Every measurement was taken on a scratch build at F:\\claude-temp\\pend\\out\\regen_*.html that
is never delivered. "4 of 13 regeneration features" was true of a page nobody can read.

⇒ A BASELINE OF ZERO OVER AN UNSTATED DENOMINATOR IS A STATEMENT ABOUT REACH, NOT THE CORPUS.
A component ships with its coverage fraction or it does not ship.

WHAT THE DENOMINATOR IS, AND IT IS NOT 1,470. The generator can only reach a page that has an
object behind it: PAGE_MAP entries whose object AND page both exist on disk. Pages outside that
set are not uncovered by this layer -- they are outside its reach entirely, which is a different
and larger problem, and is stated rather than folded in.
"""
import io
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
os.chdir(os.path.dirname(os.path.dirname(HERE)))

COMPONENTS = [
    ("integrity layer", "What was checked before this page was published"),
    ("estimand statement", "What is being estimated"),
    ("both intervals", "Both intervals, and which one this page reports"),
    ("currency query", "What has changed since these trials were last synthesised"),
]


def population():
    """Pages the generator can rebuild: an object that exists and a page that exists."""
    f = os.path.join("ssot", "PAGE_MAP.json")
    pm = json.load(io.open(f, encoding="utf-8")) if os.path.exists(f) else {}
    reachable, orphan_obj, orphan_page = [], [], []
    for page, obj in pm.items():
        if not isinstance(obj, str):
            continue
        (reachable if os.path.exists(obj) and os.path.exists(page)
         else (orphan_obj if not os.path.exists(obj) else orphan_page)).append(page)
    return reachable, orphan_obj, orphan_page


def all_html():
    out = []
    for dp, _d, ns in os.walk("."):
        if any(x in dp for x in (".git", "node_modules", "__pycache__")):
            continue
        out += [os.path.join(dp, n) for n in ns if n.endswith(".html")]
    return out


def main():
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace",
                                  line_buffering=True)
    reachable, orphan_obj, orphan_page = population()
    every = all_html()
    print("")
    print("COMPONENT COVERAGE")
    print("")
    # ⚠️ KINDS BEFORE THE NUMBER.
    print("  html files in the tree                          %5d" % len(every))
    print("  pages the generator can rebuild (denominator)   %5d" % len(reachable))
    print("    PAGE_MAP rows whose object is missing         %5d" % len(orphan_obj))
    print("    PAGE_MAP rows whose page is missing           %5d" % len(orphan_page))
    print("  html outside the generator's reach entirely     %5d   <- a different, larger problem"
          % (len(every) - len(reachable)))
    print("")
    text = {}
    for p in reachable:
        try:
            text[p] = io.open(p, encoding="utf-8", errors="replace").read()
        except Exception:
            text[p] = ""
    for name, marker in COMPONENTS:
        n = sum(1 for p in reachable if marker in text[p])
        print("  %-22s %4d of %d   %5.1f%%"
              % (name, n, len(reachable), 100.0 * n / max(1, len(reachable))))
    print("")
    print("  ⇒ Each figure is REACH over the population this layer can address. A component at")
    print("    0%% is not failing its checks -- it has never run on a delivered page, which no")
    print("    amount of passing on a scratch build will reveal.")
    out = r"F:\claude-temp\pend\out\component_coverage.json"
    json.dump({"reachable": len(reachable), "html_total": len(every),
               "components": {n: sum(1 for p in reachable if m in text[p])
                              for n, m in COMPONENTS}},
              io.open(out, "w", encoding="utf-8"), indent=1)
    print("  detail -> %s" % out)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
