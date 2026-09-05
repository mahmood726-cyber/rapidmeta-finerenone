#!/usr/bin/env python
"""Prefer the analysis denominator carried in the OUTCOME CLASS TITLE over the
randomised total in denoms.counts.

Registry results tables routinely put the per-arm analysis N in the class title as
free text -- AACT NCT00423319: "All DVT (n=1944, 1911)", "Calcium, total, low
(n=2618, 2598)" -- while denoms.counts holds the randomised total. The posted
proportions/rates in that class are evaluated against the CLASS N, not the
randomised total. Recovering a count (see recover_count.py) with the randomised
total gives a UNIQUELY WRONG integer: on this trial denoms.counts resolves to 96
where the class title determines 68, and to 191 where it determines 176. A unique
resolution can be uniquely wrong; the cross-check against the class title is the
only thing that caught it, so where a class title carries an (n=...) it wins.

parse_class_ns(title) -> the per-arm Ns in the title, in order, or [].
choose_denominators(title, denoms_counts) -> the class-title Ns if present, else
the fallback -- and it says which it used, because a silent denominator swap is
exactly how a wrong count looks right.
"""
from __future__ import annotations
import re

# "(n=1944, 1911)"  and  "(n=360; n=347; n=352)"  and "(N = 68)" -- one bracketed
# group whose body is n/N assignments and integers separated by commas or semicolons.
_NGROUP = re.compile(r"\(\s*[nN]\s*=\s*([0-9][0-9,;\s=nN]*?)\s*\)")


def parse_class_ns(title):
    """Per-arm analysis Ns embedded in a class title, in order. [] when none."""
    m = _NGROUP.search(title or "")
    if not m:
        return []
    return [int(x) for x in re.findall(r"\d+", m.group(1))]


def choose_denominators(class_title, denoms_counts):
    """(denominators, source). The class-title Ns win where present; denoms.counts
    is the fallback. `source` is 'class_title' or 'denoms_counts' -- recorded, never
    silent, because a denominator swap that is not announced is undetectable."""
    ns = parse_class_ns(class_title)
    if ns:
        return ns, "class_title"
    return list(denoms_counts or []), "denoms_counts"


def _selftest():
    out, ok = [], True

    def check(name, got, want):
        nonlocal ok
        good = got == want
        ok &= good
        out.append((name, "OK" if good else "*** FAIL ***", got, want))

    # real AACT class titles from NCT00423319
    check("All DVT (n=1944, 1911)", parse_class_ns("All DVT (n=1944, 1911)"), [1944, 1911])
    check("Calcium, total, low (n=2618, 2598)",
          parse_class_ns("Calcium, total, low (n=2618, 2598)"), [2618, 2598])
    check("Proximal DVT (n=2196, 2190)",
          parse_class_ns("Proximal DVT (n=2196, 2190)"), [2196, 2190])
    # the three-arm semicolon format the audit named
    check("Week 4 (n=360; n=347; n=352)",
          parse_class_ns("Week 4 (n=360; n=347; n=352)"), [360, 347, 352])
    # a title with no analysis N -> nothing, so the fallback is used
    check("no (n=) in title", parse_class_ns("Symptomatic distal DVT"), [])

    # PREFERENCE: class title wins over the randomised total, and says so
    d, src = choose_denominators("All DVT (n=1944, 1911)", [2691, 2646])
    check("class title beats denoms.counts", (d, src), ([1944, 1911], "class_title"))
    d, src = choose_denominators("Symptomatic distal DVT", [2691, 2646])
    check("fallback to denoms.counts when title carries no n",
          (d, src), ([2691, 2646], "denoms_counts"))
    return ok, out


if __name__ == "__main__":
    import sys, io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    good, rows = _selftest()
    print("class_title_denominator selftest")
    for name, verdict, got, want in rows:
        print("  %-42s %-12s got=%s want=%s" % (name, verdict, got, want))
    print("\n%s" % ("ALL PASS" if good else "FAILURES ABOVE"))
    raise SystemExit(0 if good else 1)
