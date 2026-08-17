"""CARD ALIGNMENT -- does the index card agree with its page and its object?

WHY THIS EXISTS
    ABLATION_AF_REVIEW shipped with its card reading HR 0.77 (0.64-0.93) and its
    page reading OR 0.7151 (0.5922-0.8634). A page reported as done was serving a
    value its own card contradicted, in public. A reader who checks us finds us
    disagreeing with ourselves, which is worse than being wrong in one place.

THE UNDERLYING DEFECT IS THAT CARDS ARE AUTHORED, NOT PROJECTED
    integrate_new_topics.py inserts a card ONCE with a static string, and nothing
    keeps it in step afterwards. Every card correction today was a hand edit.
    A hand-maintained surface drifts, and drifts silently, so this gate is a
    stopgap for a generator that does not exist: the real fix is to project cards
    from the object like every other surface.

AND IT IS THE UNGATED SURFACE
    Word-vs-HTML alignment was gated. The index cards were not -- and they are the
    FIRST thing any reader sees and the only thing used to navigate. Drift
    accumulates wherever there is no gate, which is why it accumulated here.

WHAT A FULL PASS DOES NOT ESTABLISH -- written in advance
    - NOT that the value is CORRECT. Three surfaces can agree and all be wrong;
      that is what the source-verification work is for.
    - NOT that the card's MEASURE word is right. It compares numbers; a card
      saying OR where the page says HR with the same number passes here.
    - NOT anything about cards carrying no number -- "Audit-first build" cards are
      UNCHECKABLE, never PASS, because there is nothing to compare.
    - NOT that the page itself is internally consistent.
"""
from __future__ import annotations
import json, os, re, sys, io

if __name__ == "__main__":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

SSOT = r"F:\rapidmeta-ssot-shell"
NUM = re.compile(r"-?\d+\.\d{2,4}")
WITHHELD = re.compile(r"withdrawn|not analysable|not poolable|not pooled|"
                      r"reported separately|audit-first", re.I)
TOL = 0.006


def nums(s):
    return [float(x) for x in NUM.findall((s or "").replace("&minus;", "-")
                                          .replace("\u2212", "-"))]


def page_headline(text):
    """The page's own pooled result, as rendered."""
    v = re.sub(r"<(script|style)[^>]*>.*?</\1>", " ", text, flags=re.S)
    v = re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", v))
    m = re.search(r"Pooled result\s+([A-Z_]+)?\s*(-?[\d.]+)\s*\("
                  r"(-?[\d.]+) to (-?[\d.]+)\)", v)
    if m:
        return m.group(1), [float(m.group(2)), float(m.group(3)), float(m.group(4))]
    return None, []


def check(card_pub, page_text):
    if WITHHELD.search(card_pub):
        return "UNCHECKABLE", "card states a withheld or audit-first state: no value to compare"
    cn = nums(card_pub)
    if not cn:
        return "UNCHECKABLE", "card carries no numeric value"
    meas, pn = page_headline(page_text)
    if not pn:
        return "UNCHECKABLE", "page renders no pooled result to compare against"
    hit = any(abs(c - p) <= TOL for c in cn for p in pn)
    if hit:
        return "PASS", "card %s agrees with page %s" % (cn[:3], pn)
    return "FAIL", "card %s vs page %s %s -- a served contradiction" % (cn[:3], meas or "", pn)


def main() -> int:
    if "--selftest" in sys.argv:
        return selftest()
    # SCOPE. This gate took a page and an object as arguments AND IGNORED BOTH,
    # sweeping the whole index regardless -- so it returned byte-identical output
    # for two different objects, and card_matches_page passed GLOBALLY while
    # being unmeasured PER PAGE. A gate whose result does not change when its
    # subject changes is not checking the subject. Named targets now restrict it.
    targets = {os.path.basename(a) for a in sys.argv[1:]
               if a.upper().endswith(".HTML")}
    idx = open(os.path.join(SSOT, "index.html"), encoding="utf-8", errors="replace").read()
    cards = re.findall(r'<a href="([A-Z0-9_]+\.html)" class="card [^"]*">'
                       r'<span class="name">[^<]*</span><span class="pub">(.*?)</span></a>', idx)
    if targets:
        cards = [(h, pub) for h, pub in cards if h in targets]
        missing = targets - {h for h, _ in cards}
        for m in sorted(missing):
            print("  %-46s NO CARD ON THE INDEX -- not a pass" % m)
        if not cards:
            print("  -> UNCHECKABLE: none of the named pages has a card on the index.")
            return 2
    tot = {"PASS": 0, "FAIL": 0, "UNCHECKABLE": 0, "NOPAGE": 0}
    bad = []
    for href, pub in cards:
        p = os.path.join(SSOT, href)
        if not os.path.exists(p):
            tot["NOPAGE"] += 1
            continue
        v, why = check(pub, open(p, encoding="utf-8", errors="replace").read())
        tot[v] += 1
        if v == "FAIL":
            bad.append((href, why))
    print("cards on the index: %d" % len(cards))
    for k in ("PASS", "FAIL", "UNCHECKABLE", "NOPAGE"):
        print("  %-12s %d" % (k, tot[k]))
    # THE PROPORTION CARRIES ITS COMPARABLE FRACTION, INLINE, ALWAYS.
    # "0.0% drift" over 6 comparable cards while 508 of 514 are UNCHECKABLE is a
    # reassuring headline computed over 1.2% of the corpus. It is not a rate over
    # an empty set -- but a rate whose denominator excludes almost everything,
    # printed without saying so, is the same family one degree down.
    d = tot["PASS"] + tot["FAIL"]
    n = sum(tot.values())
    if not d:
        print("  drift: UNCHECKABLE -- 0 of %d cards were comparable. No rate is "
              "rendered, because a proportion over nothing is not 0%%." % n)
    else:
        print("  drift among COMPARABLE cards: %d/%d = %.1f%%  "
              "[comparable: %d of %d cards = %.1f%% of the set; the other %d are "
              "UNMEASURED, not clean]"
              % (tot["FAIL"], d, 100.0 * tot["FAIL"] / d, d, n,
                 100.0 * d / n if n else 0.0, n - d))
    for h, w in bad:
        print("    %-46s %s" % (h[:46], w))
    json.dump([{"page": h, "why": w} for h, w in bad],
              open(r"F:\E156\outputs\codex-corpus-scan\CARD-DRIFT.json", "w",
                   encoding="utf-8"), indent=1)
    return 1 if tot["FAIL"] else 0


def selftest() -> int:
    """Positive from the real drift; negative from a card known to agree."""
    ok = True
    cases = [("POSITIVE ABLATION_AF (card 0.77 vs page 0.7151)",
              "Published: HR 0.77 (0.64&ndash;0.93), k=4", "ABLATION_AF_REVIEW.html", "FAIL"),
             ("NEGATIVE SOTAGLIFLOZIN (card == page)",
              "Published: HR 0.7171 (0.6246&ndash;0.8234), k=2",
              "SOTAGLIFLOZIN_HF_REVIEW.html", "PASS"),
             ("NEGATIVE a withdrawn card", "Estimate withdrawn &mdash; pooling invalid",
              "MAVACAMTEN_HCM_REVIEW.html", "UNCHECKABLE")]
    for name, pub, page, want in cases:
        p = os.path.join(SSOT, page)
        if not os.path.exists(p):
            print("  %-46s page absent -- NOT PROVEN" % name); ok = False; continue
        v, why = check(pub, open(p, encoding="utf-8", errors="replace").read())
        good = v == want
        ok &= good
        print("  %-46s -> %-11s (want %-11s) %s" % (name, v, want, "correct" if good else "WRONG"))
        print("        %s" % why[:100])
    print("\nWHAT A FAILURE WOULD LOOK LIKE: the ablation card passing, leaving a public "
          "contradiction between a card and the page it points at.")
    print("-> SELFTEST PASS" if ok else "-> SELFTEST FAILED")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
