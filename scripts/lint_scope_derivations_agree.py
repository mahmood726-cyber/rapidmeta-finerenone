"""TWO DERIVATIONS OF THE SAME POPULATION MUST AGREE, OR ONE OF THEM IS LOSING PAGES.

WHY THIS EXISTS -- a defect I committed, not one I found in someone else's code.
The Paper Studio lane ran two scopes at once. Its mechanical checks took their population
from `ssot/PAGE_MAP.json`; its reviewer runs took theirs from the specialty sections of
`index.html`. Nobody noticed they were different populations. They differed by three pages,
two of which were full manuscripts that never reached a reviewer -- and BOTH appeared in the
mechanical check's own output the whole time. The disagreement was visible in my own results
and I read past it, because a page present in one list and absent from another looks like a
curiosity rather than a defect.

THE CAUSE was retirement stubs. Fourteen of fifteen sub-20KB links in those sections are
RETIRED pages carrying `rapidmeta:page-state` + `rapidmeta:absorbed-by` + a canonical link,
and only ONE carries `http-equiv=refresh`. A resolver that follows meta-refresh alone
resolves 1 of 15 and silently drops the rest. A stub scores as a small, quiet, well-behaved
page: it has a title, it renders, and one of them even prints
"no unlocated world-claim numbers detected on this page" -- a provenance check reporting
clean over 285 characters, because there was nothing in it to find.

THE RULE: index-derived scope, after following EVERY retirement marker, must equal
PAGE_MAP-derived scope. Any difference is a harness defect and blocks.

WHAT THIS DOES NOT ESTABLISH: not that either population is CORRECT. Two derivations can
agree and both be wrong. It establishes only that they are the same, which is the thing that
was silently false.
"""
from __future__ import annotations
import io, json, os, re, sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from instrument_controls import require_controls  # noqa: E402

if __name__ == "__main__":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
STUB_MAX = 20000
SPECIALTIES = ("sp-cardiology", "sp-infectious-disease")

REFRESH = re.compile(r'http-equiv=["\']refresh["\'][^>]*url=([A-Za-z0-9_\-.]+)', re.I)
ABSORB  = re.compile(r'name=["\']rapidmeta:absorbed-by["\']\s+content=["\']([A-Za-z0-9_\-]+)', re.I)
CANON   = re.compile(r'rel=["\']canonical["\']\s+href=["\']([^"\']+)', re.I)
LINK    = re.compile(r'href="([A-Za-z0-9_\-]+\.html)"')


def resolve(root, page, depth=5):
    """Follow a stub to the page a reader actually lands on. Cycle-safe, bounded."""
    seen = set()
    while depth > 0:
        p = os.path.join(root, page)
        if not os.path.exists(p) or os.path.getsize(p) >= STUB_MAX or page in seen:
            return page
        seen.add(page)
        h = io.open(p, encoding="utf-8", errors="replace").read()
        m = REFRESH.search(h)
        t = m.group(1) if m else None
        if not t:
            c, a = CANON.search(h), ABSORB.search(h)
            t = (c.group(1).rsplit("/", 1)[-1] if c else None) or (a.group(1) if a else None)
        if not t or not os.path.exists(os.path.join(root, t)):
            return page
        page, depth = t, depth - 1
    return page


def section(idx, sid, all_ids):
    i = idx.find('id="%s"' % sid)
    if i < 0:
        raise SystemExit("scope: no section %s in index.html" % sid)
    nxt = len(idx)
    for o in all_ids:
        if o == sid:
            continue
        j = idx.find('id="%s"' % o)
        if i < j < nxt:
            nxt = j
    return idx[i:nxt]


def index_scope(root):
    idx = io.open(os.path.join(root, "index.html"), encoding="utf-8", errors="replace").read()
    ids = re.findall(r'id="(sp-[a-z0-9\-]+)"', idx)
    out = set()
    for sid in SPECIALTIES:
        if 'id="%s"' % sid not in idx:
            continue
        for p in dict.fromkeys(LINK.findall(section(idx, sid, ids))):
            if not os.path.exists(os.path.join(root, p)):
                continue
            r = resolve(root, p)
            if os.path.getsize(os.path.join(root, r)) >= STUB_MAX:
                out.add(r)
    return out


def pagemap_scope(root, index_pages):
    """PAGE_MAP entries that are real pages AND carry a paper tab. Specialty membership is
    taken from the index side, so this is the SAME question asked of a different list."""
    pm = json.load(io.open(os.path.join(root, "ssot", "PAGE_MAP.json"), encoding="utf-8"))
    out = set()
    for pg in pm:
        p = os.path.join(root, pg)
        if not os.path.exists(p) or os.path.getsize(p) < STUB_MAX:
            continue
        if pg not in index_pages:
            continue
        if 'id="pn-paper"' in io.open(p, encoding="utf-8", errors="replace").read():
            out.add(pg)
    return out


def run(root):
    a = index_scope(root)
    b = pagemap_scope(root, a)
    # ONLY pages that actually carry a paper tab. Without this filter the refusal message
    # said "carry a paper tab" about pages that do not -- HFREF_NMA_AUTO_FULL_REVIEW is a
    # legacy page with no paper tab and no object, correctly outside this population, and
    # the first run of this gate reported it as a mismatch. A refusal whose sentence does
    # not match its predicate is the same defect this lane is auditing elsewhere.
    only_index = sorted(
        p for p in (a - b)
        if 'id="pn-paper"' in io.open(os.path.join(root, p), encoding="utf-8",
                                      errors="replace").read())
    return a, b, only_index


def selftest():
    """PLANT: an index that links a RETIRED stub whose target is a real page. A resolver
    that follows only meta-refresh must MISS it; this one must find it. Fixture only --
    no corpus state can make it pass."""
    import tempfile, shutil
    tmp = tempfile.mkdtemp(prefix="scope_")
    try:
        io.open(os.path.join(tmp, "index.html"), "w", encoding="utf-8").write(
            '<h2 id="sp-cardiology">Cardiology</h2><a href="OLD_REVIEW.html">x</a>'
            '<h2 id="sp-infectious-disease">ID</h2>')
        io.open(os.path.join(tmp, "OLD_REVIEW.html"), "w", encoding="utf-8").write(
            '<meta name="rapidmeta:page-state" content="RETIRED">'
            '<meta name="rapidmeta:absorbed-by" content="NEW_REVIEW">'
            '<link rel="canonical" href="https://x/NEW_REVIEW.html">')
        io.open(os.path.join(tmp, "NEW_REVIEW.html"), "w", encoding="utf-8").write(
            'x' * 30000 + '<div id="pn-paper">body</div>')
        got = resolve(tmp, "OLD_REVIEW.html")
        assert got == "NEW_REVIEW.html", "stub resolver MISSED a RETIRED marker: %s" % got
        naive = REFRESH.search(io.open(os.path.join(tmp, "OLD_REVIEW.html"),
                                       encoding="utf-8").read())
        assert naive is None, "fixture is wrong: it carries a meta-refresh"
        # AND THE GATE ITSELF MUST REFUSE. Resolving a stub proves the resolver; it says
        # nothing about whether this check can block. Plant the real condition -- a page
        # with a paper tab present in the index and ABSENT from PAGE_MAP -- and require a
        # non-empty refusal set. Then remove it and require an empty one, so the check is
        # shown to discriminate rather than merely to complain.
        os.makedirs(os.path.join(tmp, "ssot"))
        io.open(os.path.join(tmp, "ssot", "PAGE_MAP.json"), "w",
                encoding="utf-8").write('{}')
        _a, _b, only = run(tmp)
        _only_bad = only
        assert only == ["NEW_REVIEW.html"], (
            "GATE CANNOT FAIL: planted a paper-tab page missing from PAGE_MAP and the "
            "refusal set was %r" % (only,))
        io.open(os.path.join(tmp, "ssot", "PAGE_MAP.json"), "w", encoding="utf-8").write(
            '{"NEW_REVIEW.html": "ssot/x/x.json"}')
        _a, _b, only = run(tmp)
        _only_ok = only
        assert only == [], "GATE OVER-FLAGS: agreeing populations reported as %r" % (only,)
        require_controls(
            "lint_scope_derivations_agree",
            positive=("a paper-tab page present in the index and absent from PAGE_MAP is "
                      "refused", _only_bad, ["NEW_REVIEW.html"]),
            negative=("populations that agree must produce an EMPTY refusal set -- the "
                      "over-flag direction, since a spurious mismatch would block every "
                      "commit in the repository", _only_ok, ["NEW_REVIEW.html"]))
        print("selftest: RETIRED stub resolved to its target (a meta-refresh-only resolver "
              "would have missed it); gate REFUSED a planted mismatch and PASSED the "
              "matching case. OK")
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def main():
    selftest()
    a, b, only_index = run(REPO)
    print()
    print("index-derived scope (stubs resolved) : %d" % len(a))
    print("PAGE_MAP-derived scope               : %d" % len(b))
    if only_index:
        print()
        print("REFUSED: %d page(s) in the index-derived scope carry a paper tab but are "
              "absent from the PAGE_MAP-derived scope. The two populations are not the "
              "same, and any rate computed across 'the corpus' is computed across "
              "whichever one the caller happened to use:" % len(only_index))
        for p in only_index:
            print("   %s" % p)
        raise SystemExit(1)
    # STATE THE RECONCILIATION, NOT A ROUND NUMBER. The first version of this line read
    # "both derivations name the same N page(s)" while printing two different totals above
    # it. The totals differ legitimately -- index-derived counts real pages, PAGE_MAP-derived
    # counts those carrying a paper tab -- but a PASS that hides its own arithmetic is the
    # comfortable message this whole lane exists to find.
    excluded = sorted(a - b)
    print("PASS: %d index-derived, %d with a paper tab in PAGE_MAP, %d excluded for having "
          "no paper tab (%s), 0 unexplained."
          % (len(a), len(b), len(excluded),
             ", ".join(excluded) if excluded else "none"))


if __name__ == "__main__":
    main()
