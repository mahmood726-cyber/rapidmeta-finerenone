"""PROJECT THE INDEX CARDS FROM THE OBJECT -- the numbers, at least.

WHY THIS EXISTS
    Measured 2026-08-18: 514 of 514 corpus pages compute their displayed pool
    correctly from their own per-trial numbers. Zero failures. So the arithmetic
    was never the problem. The INDEX CARD was, on all four topics checked:

      PCSK9            page 0.8440 (0.7952-0.8959) k=2   card said 0.85 (0.79-0.92)
      DOAC_CANCER_VTE  page 0.7290 (0.4914-1.0817) k=3   card said 0.55 (0.30-1.00)
      COLCHICINE_CVD   page 0.7940 (0.6750-0.9339) k=5   card said 0.75 (0.61-0.91)
      DOAC_AF          page 0.7817 (0.6710-0.9108) k=3   card said 0.81 (0.73-0.91)

    TOOLING-QUEUE item 3 has said the fix since the beginning: "cards are AUTHORED,
    not projected. A generator that emits the card from the object retires this
    entire class rather than measuring it." Hand-fixing four cards produces four
    correct cards and the next four wrong ones -- every topic finished by hand adds
    a fresh instance of the defect being diagnosed.

WHAT IS PROJECTED AND WHAT IS NOT -- the split matters
    THE NUMBERS ARE PROJECTED. Measure, point, interval and k come from the object
    and are formatted with the same routine the page uses, so a card cannot
    disagree with its page about a value.

    THE PROSE IS AUTHORED. A withdrawal's reason, a precision caveat, a note about
    what a reader should know -- those are written by whoever did the work and are
    carried in the object as `card_note`. Projecting prose would mean generating
    an explanation, which is the one thing a generator must not do.

    So: a card is `<projected numbers><authored note>`, and the defect class this
    retires is exactly the numeric half.

THE MEASURE TRAVELS WITH THE VALUE, ALWAYS.
    A bare number on a card is how a mean difference gets compared against an odds
    ratio. That happened in this very session: an ad-hoc comparison read a card's
    first number, stripped the minus sign from ALIROCUMAB's MD -54.66, compared it
    to an exponentiated log-odds, and reported a discrepancy of 2.9e27 per cent.
    The finding was an artefact of a bare number. This never emits one.

WHAT THIS DOES NOT ESTABLISH
    - NOT that the object is right. It makes the card agree with the object; if the
      object is wrong the card is now confidently wrong, which is why every topic
      still gets read against the registry by hand.
    - NOT anything about the ~500 audit-first cards. They carry no estimate, so
      there is nothing to project; they are left alone and reported as skipped,
      never as clean.

USAGE
    python scripts/project_index_cards.py --check     # report drift, change nothing
    python scripts/project_index_cards.py --apply     # rewrite the cards
    python scripts/project_index_cards.py --selftest
"""
from __future__ import annotations
import io
import json
import os
import re
import sys

if __name__ == "__main__":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)
sys.path.insert(0, os.path.join(REPO, "ssot"))

CARD_RE = re.compile(
    r'(<a href="(?P<page>[A-Z0-9_]+\.html)" class="card [^"]*">'
    r'<span class="name">[^<]*</span><span class="pub">)(?P<pub>.*?)(</span></a>)')


def sig(x, n=4):
    """Four significant figures, matching the page generator.

    Imported from projectors when available so the two cannot drift; the local
    fallback exists only so this runs in a checkout without the ssot package.
    """
    try:
        import projectors as pj
        return pj.sig(x, n)
    except Exception:
        if x is None:
            return ""
        return ("%.*g" % (n, x))


def _esc(s):
    return (str(s).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;"))


def project(obj):
    """(card html, note) for one object, or (None, reason) if nothing to project."""
    results = ((obj.get("results") or {}).get("by_outcome")) or {}
    if not results:
        return None, "object carries no pooled outcome"
    # A MULTI-OUTCOME OBJECT HAS NO SINGLE HEADLINE UNLESS IT SAYS WHICH.
    # The first cut took sorted(results)[0]. On IV_IRON_HF that is `acm`, and it
    # would have rewritten the card from the recurrent-hospitalisation RATE_RATIO
    # 0.8066 the page leads with to all-cause mortality HR 0.978 -- a different
    # outcome's value, silently, on the reader's first surface. A guess here is
    # indistinguishable from a correct answer until somebody opens the page.
    declared = ((obj.get("results") or {}).get("headline_outcome")
                or obj.get("headline_outcome"))
    if declared and declared in results:
        oid = declared
    elif len(results) == 1:
        oid = next(iter(results))
    else:
        return None, ("%d outcomes and no results.headline_outcome declared -- "
                      "REFUSING to guess which one the card should carry"
                      % len(results))
    res = results[oid]
    pooled = res.get("pooled") or {}
    note = (pooled.get("card_note") or res.get("card_note")
            or obj.get("card_note") or "").strip()

    if pooled.get("withdrawn"):
        head = "Estimate withdrawn"
        if not note:
            note = ("see the page for the reason and for the per-trial values the "
                    "registry records")
        return "%s &mdash; %s" % (head, _esc(note)), None

    pt = pooled.get("point")
    if pt is None:
        return None, "no live pooled value and no withdrawal recorded"
    measure = (pooled.get("measure")
               or (next((o.get("measure") for o in (obj.get("outcomes") or [])
                         if o.get("id") == oid), None)) or "")
    lo, hi = pooled.get("ci_low"), pooled.get("ci_high")
    k = res.get("k")
    # THE MEASURE TRAVELS WITH THE VALUE. Never a bare number.
    body = "Pooled: %s %s" % (_esc(measure or "effect"), sig(pt))
    if lo is not None and hi is not None:
        body += " (%s to %s)" % (sig(lo), sig(hi))
    if k is not None:
        body += ", k=%s" % _esc(k)
    if note:
        body += " &mdash; %s" % _esc(note)
    return body, None


def run(apply_changes=False):
    pm_path = os.path.join(REPO, "ssot", "PAGE_MAP.json")
    pm = json.load(open(pm_path, encoding="utf-8"))
    idx_path = os.path.join(REPO, "index.html")
    html = open(idx_path, "rb").read().decode("utf-8")

    changed, same, skipped = [], [], []
    out = html
    for page, rel in sorted(pm.items()):
        op = os.path.join(REPO, rel.replace("/", os.sep))
        if not os.path.exists(op):
            skipped.append((page, "object missing on disk"))
            continue
        obj = json.load(open(op, encoding="utf-8"))
        card, why = project(obj)
        if card is None:
            skipped.append((page, why))
            continue
        m = None
        for c in CARD_RE.finditer(out):
            if c.group("page") == page:
                m = c
                break
        if not m:
            skipped.append((page, "no card for this page in the index"))
            continue
        cur = m.group("pub")
        if cur == card:
            same.append(page)
            continue
        changed.append((page, cur, card))
        if apply_changes:
            out = out[:m.start()] + m.group(1) + card + m.group(4) + out[m.end():]

    print("CARDS PROJECTED FROM THE OBJECT")
    print("  pages in PAGE_MAP           : %d" % len(pm))
    print("  card already matches        : %d" % len(same))
    print("  card DIFFERS from projection: %d" % len(changed))
    print("  skipped (nothing to project): %d" % len(skipped))
    for p, why in skipped:
        print("      %-50s %s" % (p[:50], why))
    for p, cur, new in changed:
        print("\n  %s" % p)
        print("    now : %s" % cur[:150])
        print("    from object : %s" % new[:150])
    if apply_changes and changed:
        open(idx_path, "wb").write(out.encode("utf-8"))
        print("\n  index.html rewritten: %d card(s)" % len(changed))
    elif apply_changes:
        print("\n  nothing to write")
    return 0


def selftest() -> int:
    ok = True
    cases = [
        ("a live pool carries its MEASURE, never a bare number",
         {"outcomes": [{"id": "o", "measure": "HR"}],
          "results": {"by_outcome": {"o": {"k": 3, "pooled": {
              "measure": "HR", "point": 0.7817326, "ci_low": 0.6709903,
              "ci_high": 0.9107521}}}}},
         "Pooled: HR 0.7817 (0.671 to 0.9108), k=3"),
        ("a mean difference keeps its sign and its measure",
         {"outcomes": [{"id": "o", "measure": "MD"}],
          "results": {"by_outcome": {"o": {"k": 3, "pooled": {
              "measure": "MD", "point": -54.00144, "ci_low": -58.16516,
              "ci_high": -49.83772}}}}},
         "Pooled: MD -54 (-58.17 to -49.84), k=3"),
        ("a withdrawal defaults to a safe line when no note is authored",
         {"results": {"by_outcome": {"o": {"pooled": {"withdrawn": True}}}}},
         "Estimate withdrawn &mdash; see the page for the reason and for the "
         "per-trial values the registry records"),
        ("an authored note is carried, not generated",
         {"results": {"by_outcome": {"o": {"pooled": {
             "withdrawn": True, "card_note": "one trial counts cardiac arrest"}}}}},
         "Estimate withdrawn &mdash; one trial counts cardiac arrest"),
    ]
    for label, obj, want in cases:
        got, _ = project(obj)
        good = got == want
        ok &= good
        print("  %-58s %s" % (label[:58], "correct" if good else "WRONG"))
        if not good:
            print("      want: %s" % want)
            print("      got : %s" % got)
    multi = {"results": {"by_outcome": {
        "acm": {"k": 2, "pooled": {"measure": "HR", "point": 0.978}},
        "hfh": {"k": 2, "pooled": {"measure": "RATE_RATIO", "point": 0.8066}}}}}
    got, why = project(multi)
    good = got is None and "REFUSING" in (why or "")
    ok &= good
    print("  %-58s %s" % ("two outcomes and no declared headline -> REFUSES to guess",
                          "correct" if good else "WRONG"))
    if not good:
        print("      got: %r / %r" % (got, why))
    multi["results"]["headline_outcome"] = "hfh"
    got, _ = project(multi)
    good = got == "Pooled: RATE_RATIO 0.8066, k=2"
    ok &= good
    print("  %-58s %s" % ("the declared headline outcome is the one projected",
                          "correct" if good else "WRONG"))
    if not good:
        print("      got: %r" % got)

    none_card, why = project({"results": {"by_outcome": {"o": {"pooled": {}}}}})
    good = none_card is None
    ok &= good
    print("  %-58s %s" % ("no value and no withdrawal projects NOTHING, not a blank",
                          "correct" if good else "WRONG"))
    print("\nWHAT A FAILURE WOULD LOOK LIKE: a card emitting a bare number. A mean "
          "difference and an odds ratio are indistinguishable once the measure is "
          "dropped, and this session produced a 2.9e27%% discrepancy from exactly that.")
    print("-> SELFTEST PASS" if ok else "-> SELFTEST FAILED")
    return 0 if ok else 1


def main() -> int:
    if len(sys.argv) < 2 or sys.argv[1] == "--selftest":
        return selftest()
    if sys.argv[1] == "--apply":
        return run(apply_changes=True)
    return run(apply_changes=False)


if __name__ == "__main__":
    sys.exit(main())
