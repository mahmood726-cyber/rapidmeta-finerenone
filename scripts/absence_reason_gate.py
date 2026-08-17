"""NO SYNTHESISED ABSENCE -- is the reason given for a gap TRUE for this page?

WHY THIS EXISTS, AND WHY IT IS THE SUBTLEST PROPERTY ON THE LIST
    An unexplained gap makes a reader look further. A gap with a stated reason
    STOPS them looking. So a false reason is worse than no reason at all: it
    spends the reader's trust to close an enquiry that should have stayed open.

    THE REAL DEFECT, REPLAYED HERE: a CONVERTED page -- one extracted from an
    already-published page -- carried the AUTHORED reason, "the included set was
    reconciled against published syntheses rather than produced by a database
    search." That sentence is true of a review someone assembled from named
    sources. It is false of a page we scraped, where the honest sentence is "no
    search strategy was recoverable from the published page this object was
    extracted from." It would have shipped on 28 pages.

    The two vocabularies are build-mode-specific and MUTUALLY EXCLUSIVE, which is
    exactly what makes this checkable: an authored sentence on a converted page
    is not a judgement call, it is a category error.

WHAT A FULL PASS DOES NOT ESTABLISH -- written in advance
    - NOT that the reason is true of THIS page's particular history. It
      establishes the reason belongs to this page's BUILD MODE. A converted page
      can still carry a converted-vocabulary reason that misdescribes it.
    - NOT that a gap which states no reason is acceptable. Silence is outside
      this property; it is the manifest gate's business.
    - NOT anything about pages with no absence panels at all -- UNCHECKABLE.
"""
from __future__ import annotations
import io, json, os, re, sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__))), "ssot"))
if __name__ == "__main__":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")


def _vocab():
    import projectors as pj
    return pj.ABSENT_STATE, pj.ABSENT_STATE_CONVERTED


def _sig(s, n=60):
    """A comparable signature: the first n characters of collapsed visible text.
    Compared WHOLE, never as a fragment -- the two vocabularies share opening
    words ('No search ...') and a fragment test would confuse them."""
    return re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", s)).strip()[:n].lower()


def check(html, build_mode):
    authored, converted = _vocab()
    mode = (build_mode or "").upper()
    if mode not in ("CONVERTED", "FULL", "REBUILT_FROM_SOURCE", "AUTHOR"):
        return "UNCHECKABLE", ["build_mode %r is not one this gate knows" % build_mode]
    is_conv = mode == "CONVERTED"
    wrong_vocab = authored if is_conv else converted
    right_name = "converted" if is_conv else "authored"

    vis = re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", html))
    if "absent-state" not in html:
        return "UNCHECKABLE", ["no absence panels on this page"]

    # ENTRIES IDENTICAL IN BOTH VOCABULARIES ARE BUILD-MODE-NEUTRAL AND MUST BE
    # SKIPPED. `paper` and `analysis` read the same in both ("No manuscript has
    # been generated for this review"), because they describe a state of the
    # OBJECT, not of how the page was produced. Comparing against the whole
    # opposite vocabulary flagged FINERENONE_CV -- an authored page carrying a
    # sentence that is true of authored and converted pages alike.
    #
    # The property is "the reason is false for this build mode", and a sentence
    # that belongs to both modes cannot be false for either. Flagging it would
    # be a manufactured defect, which is the failure this whole gate exists to
    # prevent, committed by the gate itself.
    neutral = {k for k in authored
               if _sig(authored.get(k, "")) == _sig(converted.get(k, ""))
               and authored.get(k)}
    bad = []
    for tab, text in wrong_vocab.items():
        if tab in neutral:
            continue
        s = _sig(text)
        if s and s in vis.lower():
            bad.append("the %s tab carries the %s-build reason on a %s page: %r"
                       % (tab, "authored" if is_conv else "converted",
                          right_name, s[:70]))
    return ("FAIL" if bad else "PASS"), bad or ["absence reasons match the build mode"]


def selftest():
    """POSITIVE is the real defect: the authored search reason on a converted page."""
    ok = True
    authored, converted = _vocab()
    page = ('<html><body><div class="absent-state">%s</div></body></html>'
            % authored["search"])
    v, why = check(page, "CONVERTED")
    ok &= v == "FAIL"
    print("  POSITIVE authored reason on a CONVERTED page -> %-5s %s"
          % (v, "correct" if v == "FAIL" else "WRONG"))
    print("        %s" % why[0][:104])

    v2, _ = check(page, "FULL")
    ok &= v2 == "PASS"
    print("  NEGATIVE the same sentence on an AUTHORED page -> %-5s %s"
          % (v2, "correct" if v2 == "PASS" else "WRONG"))

    page2 = ('<html><body><div class="absent-state">%s</div></body></html>'
             % converted["search"])
    v3, _ = check(page2, "CONVERTED")
    ok &= v3 == "PASS"
    print("  NEGATIVE converted reason on a CONVERTED page  -> %-5s %s"
          % (v3, "correct" if v3 == "PASS" else "WRONG"))

    v4, _ = check(page2, "FULL")
    ok &= v4 == "FAIL"
    print("  POSITIVE converted reason on an AUTHORED page  -> %-5s %s"
          % (v4, "correct" if v4 == "FAIL" else "WRONG"))

    neutral_page = ('<html><body><div class="absent-state">%s</div></body></html>'
                    % authored["paper"])
    v6, _ = check(neutral_page, "CONVERTED")
    ok &= v6 == "PASS"
    print("  NEGATIVE a BUILD-MODE-NEUTRAL reason on either page -> %-5s %s"
          % (v6, "correct" if v6 == "PASS" else "WRONG"))

    v5, _ = check("<html><body>no panels</body></html>", "FULL")
    ok &= v5 == "UNCHECKABLE"
    print("  NEGATIVE a page with no absence panels        -> %-5s %s (not a pass)"
          % (v5, "correct" if v5 == "UNCHECKABLE" else "WRONG"))

    print("\nWHAT A FAILURE WOULD LOOK LIKE: the authored reason passing on a "
          "converted page -- a stated reason that stops the reader looking, and "
          "is false.")
    print("-> SELFTEST PASS" if ok else "-> SELFTEST FAILED")
    return 0 if ok else 1


def main():
    if len(sys.argv) < 3 or sys.argv[1] == "--selftest":
        if len(sys.argv) < 3 and sys.argv[1:2] != ["--selftest"]:
            print("absence_reason_gate: needs <page>.html <object>.json. NOT RUN.",
                  file=sys.stderr)
            return 2
        return selftest()
    page, obj = sys.argv[1], sys.argv[2]
    for p in (page, obj):
        if not os.path.exists(p):
            print("absence_reason_gate: %s does not exist. NOT RUN." % p,
                  file=sys.stderr)
            return 2
    o = json.loads(open(obj, encoding="utf-8", errors="replace").read())
    v, why = check(open(page, encoding="utf-8", errors="replace").read(),
                   o.get("build_mode"))
    for w in why:
        print("  %s" % w)
    print("  -> %s" % v)
    return 0 if v == "PASS" else (2 if v == "UNCHECKABLE" else 1)


if __name__ == "__main__":
    sys.exit(main())
