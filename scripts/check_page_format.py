# -*- coding: utf-8 -*-
"""Measure BUILT pages against the declared tab list in ssot/page_format_v1.json.

⭐ THE POINT IS THE DENOMINATOR. On 2026-08-30 two lanes measured the same page and
reported "6 of 8" and "6 of 10". Neither had the page wrong; they were counting different
REQUIRED lists, because the required list existed only in messages. This reads the list from
a file and reports `present / declared`, so the ratio carries its own denominator.

⛔ MEASURED FROM THE BUILT BYTES. Panel ids and nav labels are read out of the shipped HTML,
never from the generator -- a generator states what was meant, and the whole class of defect
this repo keeps finding is the gap between that and what shipped.

⚠️ EXTRA TABS ARE REPORTED, NEVER NETTED. A page carrying a tab the standard does not name is
interesting and is not credit; adding it to the numerator would let a page satisfy the format
by carrying the wrong things.

Read-only. Usage:  python scripts/check_page_format.py [PAGE.html ...]
With no arguments it walks every page in ssot/PAGE_MAP.json.
"""
from __future__ import annotations

import io
import json
import os
import re
import sys

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

_HERE = os.path.dirname(os.path.abspath(__file__))
_ROOT = os.path.abspath(os.path.join(_HERE, ".."))

PANEL_RE = re.compile(r'<section[^>]*id="([^"]+)"')
NAVLABEL_RE = re.compile(r">\s*(?:\d+\.\s*)?([A-Za-z][A-Za-z /&-]{2,40}?)\s*<")


def load_format():
    p = os.path.join(_ROOT, "ssot", "page_format_v1.json")
    with open(p, encoding="utf-8") as fh:
        return json.load(fh)


def panels_of(html):
    """Panel ids actually present in the shipped bytes."""
    return [i for i in PANEL_RE.findall(html) if i.startswith("pn-")]


def navlabels_of(html):
    m = re.search(r'class="tabnav"[^>]*>(.{0,4000})', html, re.S)
    if not m:
        return []
    return [t.strip() for t in NAVLABEL_RE.findall(m.group(1)) if t.strip()]


TOMBSTONE_RE = re.compile(r"has been retired|Retired review|retired, answered at", re.I)

# AMENDMENT 2026-09-10: recognise the WITHDRAWN-POOL page as a fourth kind that is also
# not a review. A page whose pooled estimate is withdrawn (topic NOT retired -- archive
# preserved, trials named, a future pool possible) declares itself with this exact marker,
# the same one the regression gate reads to enter its no-pool branch. Until now this checker
# knew only the RETIRED spelling, so it scored a withdrawn-pool notice as a review at 0/8
# tabs and refused a correct page -- the third latent blocker the SGLT2 withdrawal hit when
# the plumbing bypass was closed. TWO gates held two independent detectors for one concept
# ("this delivered page is not a review") and drifted; this aligns them. The fix does NOT put
# "retired" language in the notice (that would be false -- the topic is not retired).
NO_POOL_RE = re.compile(r'name="rapidmeta:pooled-estimate"\s+content="NONE"')


def is_tombstone(html):
    """A retired-review tombstone is a THIRD KIND OF PAGE -- not a review, not a defect,
    and a WITHDRAWN-POOL notice is a FOURTH (see AMENDMENT above). Both are excluded from
    review-tab scoring; a real review is neither.

    ⛔ SCORING ONE AGAINST THE REVIEW FORMAT IS A CATEGORY ERROR. The first run of this
    checker reported 14 pages at 0/8 required tabs, which reads as 14 broken pages. They are
    deliberate tombstones (~2.8 KB) that exist so a link to a retired review does not break,
    and they say so in their own text: "It is not a redirect: a reader who arrives here is
    told what happened rather than moved silently."

    Counting them as review pages would have put 14 fabricated failures into a corpus
    number. Before reporting any count, the KINDS of item in the population have to be
    enumerated -- reviews, tombstones, withdrawn-pool notices, and whatever else.

    THE `< 20000` GUARD IS LOAD-BEARING and applies to BOTH markers: a large page claiming to
    be a tombstone or a no-pool notice must still be scored, so a full review cannot escape
    tab-scoring by merely carrying a marker. A withdrawn-pool notice is small by construction.
    """
    return bool(TOMBSTONE_RE.search(html) or NO_POOL_RE.search(html)) and len(html) < 20000


def check(path, fmt):
    with open(path, encoding="utf-8", errors="replace") as fh:
        html = fh.read()
    if is_tombstone(html):
        return None
    panels = set(panels_of(html))
    labels = navlabels_of(html)
    low = " | ".join(labels).lower()

    present, missing = [], []
    for t in fmt["required_tabs"]:
        hit = (t["panel_id_hint"] in panels) or (t["label"].lower() in low)
        (present if hit else missing).append(t["id"])

    extra_known = [e["id"] for e in fmt["observed_but_not_in_the_required_list"]
                   if e["panel_id_hint"] in panels]
    named = {t["panel_id_hint"] for t in fmt["required_tabs"]}
    named |= {e["panel_id_hint"] for e in fmt["observed_but_not_in_the_required_list"]}
    extra_unknown = sorted(panels - named)
    return present, missing, extra_known, extra_unknown, len(panels)


_BASELINE = os.path.join(_ROOT, "scripts", "baselines",
                         "page_format_baseline.json")


def main(argv):
    # ⭐ --gate MAKES THIS ABLE TO FAIL. Without it the file was a REPORT wearing
    # a `check_` name: its only terminal return was `return 0`, so a page with
    # ZERO of the eight required tabs exited 0 -- verified by execution, not by
    # reading. That is verification theatre on the one format that is the
    # deliverable. The default stays a report (exit 0) so nothing that runs it
    # today changes behaviour; --gate is the verdict mode.
    gate = "--gate" in argv
    argv = [a for a in argv if a != "--gate"]
    fmt = load_format()
    declared = len(fmt["required_tabs"])
    if argv:
        pages = argv
    else:
        pm = json.load(open(os.path.join(_ROOT, "ssot", "PAGE_MAP.json"), encoding="utf-8"))
        pages = sorted(pm)
    print("DECLARED REQUIRED TABS: %d  (ssot/page_format_v1.json, status=%s)"
          % (declared, fmt.get("_status", "")[:40]))
    print("unit: REQUIRED PRESENT / REQUIRED DECLARED. Extras reported, never netted.\n")

    # ⭐ EVERY CANDIDATE LANDS IN A NAMED BUCKET AND THE BUCKETS MUST SUM.
    # This loop carried `if not os.path.exists(full): continue` and
    # `if got is None: continue` -- two negative guards in a corpus walk, so a
    # page listed in PAGE_MAP but MISSING FROM DISK was dropped before being
    # counted anywhere and the denominator shrank in silence. That is the
    # defect this file's own tombstone comment warns about, one branch away.
    hist, rows, seen, tombstones, absent = {}, [], 0, [], []
    for pg in pages:
        full = pg if os.path.isabs(pg) else os.path.join(_ROOT, pg)
        if os.path.exists(full):
            seen += 1
        else:
            absent.append(os.path.basename(pg))
            continue
        got = check(full, fmt)
        if got is not None:
            present, missing, ek, eu, npanels = got
        else:
            tombstones.append(os.path.basename(pg))
            continue
        hist[len(present)] = hist.get(len(present), 0) + 1
        rows.append((os.path.basename(pg), len(present), missing, ek, eu))

    # ⭐ THE POPULATION, BY KIND -- never a bare total. A tombstone is not a review page and
    # not a defect; it is a third thing, and it must leave the denominator explicitly rather
    # than by being silently skipped.
    if len(rows) + len(tombstones) + len(absent) != len(pages):
        raise SystemExit(
            "REFUSED: buckets do not sum (%d review + %d tombstone + %d absent "
            "!= %d candidates). A candidate fell through every named bucket, "
            "which is the silent drop this walk was rewritten to prevent."
            % (len(rows), len(tombstones), len(absent), len(pages)))
    # KNOWN_NEGATIVE -- A TOMBSTONE, BECAUSE THAT IS THE CASE THIS CHECKER ALREADY GOT WRONG.
    #
    # `is_tombstone`'s own docstring records it: "The first run of this checker reported 14
    # pages at 0/8 required tabs, which reads as 14 broken pages." They are ~2.8 KB retirement
    # stubs. A tombstone therefore LOOKS EXACTLY LIKE THE WORST POSSIBLE DEFECT -- zero of
    # eight required tabs -- while being entirely correct, which is the definition of the case
    # most likely to be got wrong, and it is not hypothetical: it produced 14 fabricated
    # failures once already.
    #
    # A KNOWN-NEGATIVE DRAWN FROM THE EASY MAJORITY WOULD MEASURE NOTHING: 148 of 149 pages
    # carry 6/8 and any of them would pass under a broken implementation too. This one would
    # not. It is in PAGE_MAP, so it is inside the population this checker actually judges --
    # a control outside the traversal proves nothing about the traversal.
    #
    # FAILS CLOSED: if the row is absent from PAGE_MAP or from disk the rate is UNMEASURED and
    # the checker refuses, because an unmeasured false-positive rate is not a measured zero.
    # CORPUS-ANCHORED, therefore perishable -- if this tombstone is ever deleted or rebuilt,
    # pin a copy rather than dropping the control.
    KNOWN_NEGATIVE = "CVNCOV_SARSCOV2_AUTO_FULL_REVIEW.html"
    neg_seen = KNOWN_NEGATIVE in tombstones
    neg_fp = any(n == KNOWN_NEGATIVE for n, _, _, _, _ in rows)
    print("KNOWN-NEGATIVE CONTROL: %s" % KNOWN_NEGATIVE)
    if not neg_seen and not neg_fp:
        print("   UNMEASURED -- not reached by this traversal. An unmeasured false-positive")
        print("   rate is NOT a measured zero. REFUSED.")
        return 1
    print("   %d/1 matched (measured false-positive rate %.1f%%) -- a ~2.8 KB retirement"
          % (1 if neg_fp else 0, 100.0 if neg_fp else 0.0))
    print("   stub carrying 0 of %d required tabs. It must be counted as a TOMBSTONE, never"
          % declared)
    print("   as a short review page: scoring one against the review format is the error")
    print("   that produced 14 fabricated failures on this checker's first run.")
    if neg_fp:
        print("   CONTROL FAILED: the tombstone was scored as a review page. REFUSED.")
        return 1
    print()

    # AMENDMENT CONTROL 2026-09-10 -- PROVE THE WITHDRAWN-POOL RECOGNITION BOTH WAYS, fail
    # closed. A gate change without a still-fails control is a weakening whatever its intent.
    # On REAL bytes, with planted negatives:
    #   A  the withdrawn-pool notice (carries the marker, < 20 KB) is EXCLUDED  -> it passes;
    #   B  the SAME notice with the marker REMOVED is NOT excluded              -> it still
    #      fails (reverts to a scored 0/8 review), so exclusion is gated on the DECLARATION,
    #      not on shortness;
    #   C  a real (large) review page with the marker INJECTED is STILL scored  -> the
    #      < 20000 guard holds, so a full review cannot escape tab-scoring by carrying it.
    NOPOOL_POS = "SGLT2_MACE_CVOT_REVIEW.html"
    _pos = os.path.join(_ROOT, NOPOOL_POS)
    print("AMENDMENT CONTROL (withdrawn-pool recognition, 2026-09-10):")
    if not os.path.exists(_pos):
        print("   UNMEASURED -- %s absent; a gate change with no exercised control is a"
              % NOPOOL_POS)
        print("   weakening. REFUSED.")
        return 1
    _pos_html = open(_pos, encoding="utf-8", errors="replace").read()
    if not is_tombstone(_pos_html):
        print("   CONTROL A FAILED: the withdrawn-pool notice is NOT excluded. REFUSED.")
        return 1
    if is_tombstone(NO_POOL_RE.sub("", _pos_html)):
        print("   CONTROL B FAILED: the notice is still excluded with its marker removed --")
        print("   exclusion is not gated on the declaration. REFUSED.")
        return 1
    # pick a REAL review page big enough to exercise the < 20000 guard (names already
    # carry .html; resolve as the walk does, relative to _ROOT).
    _rev, _rev_html = None, ""
    for _n, _c, _m, _ek, _eu in rows:
        _p = _n if os.path.isabs(_n) else os.path.join(_ROOT, _n)
        if os.path.exists(_p):
            _h = open(_p, encoding="utf-8", errors="replace").read()
            if len(_h) >= 20000:
                _rev, _rev_html = _n, _h
                break
    if not _rev:
        print("   UNMEASURED -- no real review page over the guard size to plant the guard")
        print("   control on. A gate change with no exercised guard control is a weakening."
              " REFUSED.")
        return 1
    if is_tombstone('<meta name="rapidmeta:pooled-estimate" content="NONE">' + _rev_html):
        print("   CONTROL C FAILED: a large review carrying the marker escaped scoring; the")
        print("   < 20000 guard did not hold. REFUSED.")
        return 1
    print("   held: notice excluded (A); notice without its marker still scored (B);")
    print("   marker-injected large review %s still scored (C). Guard is load-bearing." % _rev)
    print()
    print("PAGE MAP ENTRIES  : %d" % len(pages))
    print("  files found     : %d" % seen)
    print("  LISTED BUT ABSENT FROM DISK (counted, not dropped): %d" % len(absent))
    if absent:
        print("     %s" % ", ".join(a[:34] for a in absent[:6])
              + (" ... and %d more" % (len(absent) - 6) if len(absent) > 6 else ""))
    print("  RETIRED-REVIEW TOMBSTONES (excluded, not defects): %d" % len(tombstones))
    print("  REVIEW PAGES -- the real denominator             : %d\n" % len(rows))
    if tombstones:
        print("  tombstones: %s\n" % ", ".join(t[:34] for t in tombstones[:6])
              + ("    ... and %d more\n" % (len(tombstones) - 6) if len(tombstones) > 6 else ""))
    seen = len(rows)
    print("distribution of required-tabs-present:")
    for k in sorted(hist, reverse=True):
        print("   %d/%d required present : %3d pages" % (k, declared, hist[k]))

    worst = sorted(rows, key=lambda r: r[1])[:5]
    print("\nfewest required tabs:")
    for name, n, missing, ek, eu in worst:
        print("   %-52s %d/%d  missing=%s" % (name[:52], n, declared, ",".join(missing)))

    allmissing = {}
    for _, _, missing, _, _ in rows:
        for m in missing:
            allmissing[m] = allmissing.get(m, 0) + 1
    print("\nrequired tab MISSING, by tab:")
    for k, v in sorted(allmissing.items(), key=lambda kv: -kv[1]):
        print("   %-16s missing on %3d/%d pages" % (k, v, seen))

    extras = {}
    for _, _, _, ek, eu in rows:
        for e in list(ek) + list(eu):
            extras[e] = extras.get(e, 0) + 1
    print("\nEXTRA tabs present but not required (reported, not credited):")
    for k, v in sorted(extras.items(), key=lambda kv: -kv[1]):
        print("   %-16s on %3d pages" % (k, v))

    if gate:
        # A RATCHET, NOT AN ULTIMATUM -- AND THE FIRST VERSION WAS AN ULTIMATUM.
        # `--gate` originally refused any page carrying fewer than the declared
        # eight. Measured over the corpus: 1 page of 149 carries 8/8 and 148
        # carry 6/8, every one missing exactly hta and guideline, because the
        # eight-tab format is newer than the pages. So the gate refused the
        # whole corpus and blocked a push -- I had tested it on ONE page and on
        # a planted bad one, both non-empty, and never on the population it
        # would actually judge. A gate that refuses everything is as useless as
        # one that refuses nothing, and it is louder about it.
        #
        # The rule that is worth enforcing is that a page MUST NOT LOSE A TAB,
        # and that a NEW page arrives complete. Both are checked here; the
        # baseline records where each page stands today and the count may only
        # go up.
        base = {}
        if os.path.exists(_BASELINE):
            with open(_BASELINE, encoding="utf-8") as fh:
                base = json.load(fh).get("pages", {})
        regressed, new_short = [], []
        for n, c, m, _, _ in rows:
            was = base.get(n)
            if was is None:
                if c < declared:
                    new_short.append((n, c, m))
            elif c < was:
                regressed.append((n, was, c, m))
        print()
        if regressed or new_short:
            if regressed:
                print("REFUSED: %d page(s) LOST a required tab since the baseline."
                      % len(regressed))
                for n, was, c, m in regressed[:20]:
                    print("   %-46s %d/%d -> %d/%d  missing %s"
                          % (n[:46], was, declared, c, declared, ",".join(m)))
            if new_short:
                print("REFUSED: %d NEW page(s) arrive with fewer than the %d "
                      "declared required tabs." % (len(new_short), declared))
                for n, c, m in new_short[:20]:
                    print("   %-46s %d/%d  missing %s"
                          % (n[:46], c, declared, ",".join(m)))
            return 1
        at_full = sum(1 for _, c, _, _, _ in rows if c >= declared)
        print("NO PAGE LOST A TAB, AND NO NEW PAGE ARRIVED SHORT.")
        print("  %d of %d review page(s) carry all %d declared required tabs."
              % (at_full, len(rows), declared))
        print("  The remaining %d are baselined BELOW the declared set and are "
              "owed, not cleared." % (len(rows) - at_full))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
