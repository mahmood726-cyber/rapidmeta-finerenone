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
    out = []
    for page in sorted(pages or glob.glob("*.html")):
        try:
            raw = open(page, "rb").read()
        except OSError:
            continue
        topic = topic_of(raw, known)
        if not topic:
            continue
        obj_path = os.path.join("ssot", topic, topic + ".json")
        if not os.path.isfile(obj_path):
            continue
        try:
            obj = json.load(io.open(obj_path, encoding="utf-8"))
        except Exception:
            continue
        pend = {oid for oid in ((obj.get("results") or {}).get("by_outcome") or {})
                if ga.resolve(obj, oid).get("state") == "PENDING"}
        if not pend:
            continue
        text = rendered(raw.decode("utf-8", "replace"))
        levels = LEVEL.findall(text)
        derivs = DERIV.findall(text)
        out.append({"page": page, "topic": topic, "pending_outcomes": len(pend),
                    "levels_rendered": len(levels), "derivations_rendered": len(derivs),
                    "pending_rendered": len(PENDING.findall(text)),
                    "violating": bool(levels or derivs)})
    return out


def main():
    argv = [a for a in sys.argv[1:] if not a.startswith("-")]
    rows = scan(argv or None)
    bad = [r for r in rows if r["violating"]]
    print("")
    print("GATE -- no certainty level over an unadjudicated risk-of-bias assessment")
    print("")
    print("  pages examined that have >=1 PENDING outcome   %4d  == the denominator"
          % len(rows))
    print("  pages rendering a certainty LEVEL anyway       %4d" % len(bad))
    print("")
    for r in sorted(rows, key=lambda x: (-x["levels_rendered"], x["page"]))[:24]:
        print("   %-9s %-42s pending %d  levels %d  derivations %d"
              % ("REFUSE" if r["violating"] else "ok", r["page"][:41],
                 r["pending_outcomes"], r["levels_rendered"], r["derivations_rendered"]))
    if len(rows) > 24:
        print("   ... and %d more" % (len(rows) - 24))
    print("")
    if bad:
        print("VERDICT: REFUSED. %d page(s) publish a certainty level while the risk-of-bias "
              "assessment behind it is unadjudicated." % len(bad))
        print("Rebuild them; the generator already withholds the level.")
        return 1
    print("VERDICT: PASS. No page shows a level where the resolver withholds one.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
