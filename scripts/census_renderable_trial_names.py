# -*- coding: utf-8 -*-
"""WHICH PAGES HOLD A TRIAL NAME AND RENDER ONLY ITS REGISTRATION NUMBER?

⛔ THE KEY-SET ASSERTION COMES FIRST, AND IT EXISTS BECAUSE THIS CENSUS WAS RUN
TWICE ON A FIELD THAT DOES NOT CARRY THE DATA. Keyed on `label` it reported 251
trials across 64 pages "with no name". The store carries the name under `name`
for 205 of 412 trials; the true figure is 52 across 6. A census keyed on a
missing field does not error -- it returns a clean, plausible number, and both
wrong numbers looked entirely reasonable.

    BEFORE COUNTING ANYTHING, PRINT THE KEY SET OF A REAL OBJECT AND ASSERT THE
    KEY IS IN IT. Three defects in one session came from reading a plausible
    field name and never confirming it: `withdrawn` (one level down, on `pooled`
    not on the record), `indirectness` (two shapes, only one of them read), and
    `label` vs `name`. All three produced confident wrong numbers.
"""
import importlib.util
import io
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)
NAME_KEYS = ("name", "label", "acronym", "short_name")
WINDOW = 300


def load_gate():
    p = os.path.join(REPO, "gates", "gate16_reader_can_check.py")
    spec = importlib.util.spec_from_file_location("g16", p)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


_UNREADABLE = object()


def _read_json(path):
    """The object, or _UNREADABLE. Never a silent skip -- callers count it."""
    try:
        with io.open(path, encoding="utf-8") as fh:
            return json.load(fh)
    except Exception:
        return _UNREADABLE


def _read_pair(m, page):
    """(canon, html) for one page, or _UNREADABLE. Counted, never dropped."""
    sp = m.store_for(page)
    canon = _read_json(sp) if sp else _UNREADABLE
    if canon is _UNREADABLE:
        return _UNREADABLE
    try:
        html = io.open(os.path.join(REPO, page), encoding="utf-8",
                       errors="replace").read()
    except Exception:
        return _UNREADABLE
    return canon, html


def real(v):
    return isinstance(v, str) and v.strip() not in ("", "None", "none")


def assert_keys_exist(m):
    """Print the key set of a real trial object and prove our keys are in it."""
    for p in m.pages():
        sp = m.store_for(p)
        canon = _read_json(sp) if sp else _UNREADABLE
        if canon is _UNREADABLE:
            continue
        for t in ((canon.get("inputs") or {}).get("trials") or []):
            if isinstance(t, dict) and t.get("nct"):
                ks = sorted(t.keys())
                print("  KEY-SET ASSERTION -- one real trial object (%s)" % p[:38])
                print("    keys: %s" % ", ".join(ks[:14]))
                hit = [k for k in NAME_KEYS if k in ks]
                print("    name keys sought : %s" % ", ".join(NAME_KEYS))
                print("    present on it    : %s" % (", ".join(hit) or "*** NONE ***"))
                return bool(hit)
    return False


def main():
    m = load_gate()
    if not assert_keys_exist(m):
        print("  REFUSED: no name key is present on a real trial object. A census")
        print("  keyed on an absent field returns a clean, plausible, wrong number.")
        return 3
    print("")

    kinds = {"no_name_in_store": 0, "rendered_with_name": 0,
             "RENDERABLE_BUT_NOT_RENDERED": 0, "nct_not_on_page": 0,
             "no_registration_on_trial": 0}
    page_kinds = {"tombstone": 0, "unreadable": 0}
    fixable = {}
    pages = [p for p in m.pages() if m.store_for(p)]
    n_pages = 0
    for page in pages:
        # POSITIVE FORM, and the refusal that produced it was right twice in one
        # session -- this is the SECOND script of mine the gate caught. A census
        # that skips silently reports its own reach as coverage, which is the one
        # error this file already exists to prevent.
        pair = _read_pair(m, page)
        if pair is _UNREADABLE:
            page_kinds["unreadable"] = page_kinds.get("unreadable", 0) + 1
            continue
        canon, html = pair
        if m.is_tombstone(html):
            # ⛔ PAGE-LEVEL, SO IT IS COUNTED SEPARATELY. Adding it to `kinds`
            # made the total 427 -- 412 trials plus 13 tombstoned PAGES plus 2
            # trials -- a denominator with two units in it. Stating the guards
            # positively surfaced the hidden population, which was the point;
            # dropping it into the nearest counter then invented a number that
            # is of nothing. Both halves of that are the same lesson: name the
            # kinds, and name what the denominator is OF.
            page_kinds["tombstone"] = page_kinds.get("tombstone", 0) + 1
            continue
        n_pages += 1
        body = m._body(html)
        for t in ((canon.get("inputs") or {}).get("trials") or []):
            if isinstance(t, dict) and real(t.get("nct")):
                pass
            else:
                kinds["no_registration_on_trial"] = kinds.get(
                    "no_registration_on_trial", 0) + 1
                continue
            nct = t["nct"].strip()
            nm = next((t[k].strip() for k in NAME_KEYS if real(t.get(k))), None)
            # POSITIVE FORM. This is the third pass over this file's guards and
            # the gate caught every one of them. The value of that is not tidiness:
            # each rewrite has surfaced population the skip was hiding, and this
            # branch is the one that decides the headline number, so a silent skip
            # here would move the answer directly.
            if nm:
                pass
            else:
                kinds["no_name_in_store"] += 1
                continue
            spots = [mm.start() for mm in re.finditer(re.escape(nct), body)]
            if spots:
                pass
            else:
                kinds["nct_not_on_page"] += 1
                continue
            near = any(nm.lower() in body[max(0, s - WINDOW):s + WINDOW].lower()
                       for s in spots)
            if near:
                kinds["rendered_with_name"] += 1
            else:
                kinds["RENDERABLE_BUT_NOT_RENDERED"] += 1
                fixable.setdefault(page, []).append((nct, nm))

    print("  pages evaluated (tombstones excluded) : %d" % n_pages)
    print("  TRIAL-REGISTRATION KINDS -- these sum to the population, by design")
    tot = sum(kinds.values())
    for k, v in sorted(kinds.items(), key=lambda x: -x[1]):
        print("    %-30s %4d" % (k, v))
    print("    %-30s %4d  <- the denominator, OF TRIAL REGISTRATIONS"
          % ("TOTAL", tot))
    print("")
    print("  PAGE KINDS -- a different unit, so a different total")
    for k, v in sorted(page_kinds.items(), key=lambda x: -x[1]):
        print("    %-30s %4d" % (k, v))
    print("    %-30s %4d  <- the denominator, OF PAGES"
          % ("TOTAL", n_pages + sum(page_kinds.values())))
    print("")
    print("  PAGES WITH AT LEAST ONE RENDERABLE-BUT-UNRENDERED NAME : %d"
          % len(fixable))
    for p, items in sorted(fixable.items(), key=lambda x: -len(x[1]))[:15]:
        print("    %-46s %d  e.g. %s -> %s"
              % (p[:46], len(items), items[0][0], items[0][1]))
    return 0


if __name__ == "__main__":
    sys.exit(main())
