"""THE INTERACTIVE LAYER, CHECKED MECHANICALLY -- because no text reviewer can see it.

WHY. An external reviewer with a browser found, in one pass, a defect class that fifty blind
reviews of the rendered TEXT could not see: `fw-fit`, `fw-w1`, `fw-w2` each occurring three
times on one page, ten range controls sharing `name="fw"`, and a `#search` fragment with no
target. A reviewer handed rendered text is blind to all of it BY CONSTRUCTION, so this belongs
in the mechanical half of the rubric where it cannot be argued with.

WHAT IT CHECKS, each a property of the delivered bytes:
  1. DUPLICATE ELEMENT IDS. `getElementById` returns the first; a `<label for=>` binds to the
     first; so the second and third controls are unreachable and the page silently misbehaves.
  2. ONE RADIO GROUP PER CONTROL CLUSTER. Three forest plots sharing `name="fw"` are ONE group:
     selecting a range on plot 3 deselects plots 1 and 2. With `checked` on all three, only the
     LAST renders selected -- which is why only the third plot appeared active.
  3. IN-PAGE FRAGMENTS RESOLVE. `href="#search"` with no `id="search"` is a dead link.

WHAT THIS DOES NOT ESTABLISH: not that the controls WORK. A page can pass all three and still
mis-wire its handlers. Click-testing is a different instrument and this is not it.
"""
from __future__ import annotations
import collections, io, json, os, re, sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from instrument_controls import require_controls  # noqa: E402

if __name__ == "__main__":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
STUB_MAX = 20000
ID   = re.compile(r"""\sid=(?:"([^"]+)"|'([^']+)')""")
# BOTH QUOTE STYLES. The first version matched only double quotes, so every
# single-quoted id was invisible to it -- and an id it could not see became a "dead
# fragment" in its report. It accused the page of a broken link that was not broken:
# `<h3 id='paper-not-reported'>` exists and is targeted correctly. A detector that
# cannot see half the ids reports a corpus-wide defect that is partly its own blind
# spot, and it does so in the direction of accusing the thing it is checking.
RAD  = re.compile(r'<input[^>]*type=["\']radio["\'][^>]*>', re.I)
NAME = re.compile(r'name=["\']([^"\']+)["\']')
IDA  = re.compile(r'id=["\']([^"\']+)["\']')
CHK  = re.compile(r'\bchecked\b')
FRAG = re.compile(r'href="#([A-Za-z0-9_\-]+)"')
# The tab shell legitimately uses one group for one control cluster.
SHELL_GROUPS = {"rmtab"}


def audit(html):
    _ids = [a or b for a, b in ID.findall(html)]
    dup = {k: v for k, v in collections.Counter(_ids).items() if v > 1}
    groups, checked, ids_in_group = collections.Counter(), collections.Counter(), {}
    for tag in RAD.findall(html):
        n = NAME.search(tag)
        if not n or n.group(1) in SHELL_GROUPS:
            continue
        g = n.group(1)
        groups[g] += 1
        if CHK.search(tag):
            checked[g] += 1
        i = IDA.search(tag)
        if i:
            ids_in_group.setdefault(g, collections.Counter())[i.group(1)] += 1
    shared = {g: dict(c) for g, c in ids_in_group.items()
              if any(v > 1 for v in c.values())}
    multi = {g: n for g, n in checked.items() if n > 1}
    ids = set(_ids)
    dead = sorted({f for f in FRAG.findall(html) if f not in ids})
    return dup, shared, multi, dead


def selftest():
    """Plant each defect and require detection; plant a clean page and require silence.

    THE NEGATIVE CONTROL IS A REAL CORPUS FACT, AND IT IS THE ONE THAT MATTERS HERE.
    The first version of this linter matched only DOUBLE-quoted ids, so every
    `id='...'` was invisible to it -- and an id it could not see was reported as a DEAD
    FRAGMENT. It accused a page of a broken link that works, and the corpus number it
    produced (197 dead fragments) was inflated by roughly 49 of its own blind spots.
    A person reading one instance caught it; the instrument could not, because it had
    only ever been asked whether it could say yes.

    So the negative is pinned to that exact case: `paper-not-reported` on a delivered page
    is written with SINGLE quotes and IS targeted by a fragment, and this instrument must
    never report it dead."""
    bad = ('<a href="#search">s</a><div id="pn-a"></div>'
           '<input type="radio" name="fw" id="fw-fit" checked>'
           '<input type="radio" name="fw" id="fw-fit" checked>')
    dup, shared, multi, dead = audit(bad)
    _planted = (dup.get("fw-fit"), multi.get("fw"), tuple(dead))
    _expect = (2, 2, ("search",))
    assert dup.get("fw-fit") == 2, "duplicate id NOT detected: %r" % dup
    assert shared.get("fw", {}).get("fw-fit") == 2, "shared-group id reuse NOT detected"
    assert multi.get("fw") == 2, "multiple checked in one group NOT detected"
    assert dead == ["search"], "dead fragment NOT detected: %r" % dead
    good = ('<a href="#search">s</a><div id="search"></div>'
            '<input type="radio" name="fw-total" id="fw-total-fit" checked>'
            '<input type="radio" name="fw-first" id="fw-first-fit" checked>')
    dup, shared, multi, dead = audit(good)
    assert not dup and not shared and not multi and not dead, \
        "OVER-FLAGS a correctly built page: %r %r %r %r" % (dup, shared, multi, dead)
    # The real page, read as delivered -- not a fixture, so this control also fails if the
    # corpus stops containing a single-quoted targeted id and the pin has to be renewed.
    _real = os.path.join(REPO, "SOTAGLIFLOZIN_HF_REVIEW.html")
    _dead_on_real = None
    if os.path.exists(_real):
        _h = io.open(_real, encoding="utf-8", errors="replace").read()
        _dead_on_real = "paper-not-reported" in audit(_h)[3]
    require_controls(
        "lint_interactive_layer",
        positive=("planted duplicate id + shared group + dead fragment detected",
                  _planted, _expect),
        negative=("single-quoted id 'paper-not-reported' on a delivered page, which IS "
                  "targeted and must not be called dead", _dead_on_real, True))
    print("selftest: all four detectors fire on planted defects, stay silent on a "
          "correctly built page, and do not call a single-quoted id dead. OK")


def main():
    selftest()
    pm = json.load(io.open(os.path.join(REPO, "ssot", "PAGE_MAP.json"), encoding="utf-8"))
    pages = sorted(p for p in pm
                   if os.path.exists(os.path.join(REPO, p))
                   and os.path.getsize(os.path.join(REPO, p)) >= STUB_MAX)
    bad = []
    tot = collections.Counter()
    for pg in pages:
        h = io.open(os.path.join(REPO, pg), encoding="utf-8", errors="replace").read()
        dup, shared, multi, dead = audit(h)
        if dup or shared or multi or dead:
            bad.append((pg, len(dup), len(shared), len(multi), len(dead)))
            tot["dup_ids"] += len(dup)
            tot["shared_group_ids"] += len(shared)
            tot["multi_checked"] += len(multi)
            tot["dead_fragments"] += len(dead)
    print()
    print("pages scanned: %d" % len(pages))
    for k in ("dup_ids", "shared_group_ids", "multi_checked", "dead_fragments"):
        print("   %-20s %d" % (k, tot[k]))
    if bad:
        print()
        print("REFUSED: %d page(s) carry interactive-layer defects a text reviewer "
              "cannot see:" % len(bad))
        for pg, a, b, c, d in bad[:40]:
            print("   %-52s dup=%d sharedgrp=%d multichecked=%d deadfrag=%d"
                  % (pg[:52], a, b, c, d))
        if len(bad) > 40:
            print("   ... and %d more" % (len(bad) - 40))
        raise SystemExit(1)
    print("PASS: no duplicate ids, no shared control groups, no dead fragments.")


if __name__ == "__main__":
    main()
