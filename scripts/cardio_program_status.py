"""CARDIOLOGY PROGRAMME STATUS -- the denominator, and what is on each topic.

WHY THIS EXISTS
    "53 cardiology topics" was a number carried in prose. A denominator that
    lives in a sentence drifts the moment a page is added, consolidated or
    retired, and every rate computed against it drifts with it silently. This
    derives it from the index each time it runs, and prints how it got there.

HOW THE DENOMINATOR IS DERIVED, so a reader can disagree with the derivation
    The #sp-cardiology section of index.html, up to the next specialty heading.
    Every distinct page link in it is a topic, MINUS redirect stubs -- a stub is
    a pointer to a topic, not a second topic, and counting it would inflate both
    the denominator and the not-done count.

WHAT THIS DOES NOT ESTABLISH -- written in advance
    - NOT that a topic listed as DONE is correct. DONE means it has an object,
      was built to the written standard, and its endpoints were read. Every one
      of those is structural. A page can satisfy all of them and pool the wrong
      trials.
    - NOT that a card's state is TRUE. It reads what the card claims. A card
      saying "Audit-first build" is recorded as audit-first whether or not the
      page beneath it publishes something.
    - NOT that a withdrawal was justified. It counts withdrawals; the reason has
      to be checked against the registry by hand.
    - NOT anything about topics that have no card and no link here. A topic
      missing from the index is invisible to this script, which is exactly why
      the link count and the card count are printed separately.
"""
from __future__ import annotations
import io, json, os, re, sys

if __name__ == "__main__":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
STUB_MAX = 20000          # bytes; a real review page is ~850 KB
CARD = re.compile(r'<a href="([A-Za-z0-9_]+\.html)" class="card [^"]*">'  # [A-Z0-9_] MISSED ANY PAGE WITH A LOWERCASE LETTER.
# INCRETIN_HFpEF_REVIEW.html has a lowercase 'p'. Its card existed and
# published 'HR 0.41 (0.22-0.79), k=3' -- and BOTH this scanner and the card
# projector reported it as having NO CARD, for weeks. A page invisible to the
# tool that counts pages is worse than an uncounted page: it is counted as a
# DIFFERENT thing, and it silently escaped card-alignment checking entirely.
                  r'<span class="name">[^<]*</span><span class="pub">(.*?)</span></a>')


def section(html, start_id, end_id):
    i = html.find('id="%s"' % start_id)
    j = html.find('id="%s"' % end_id)
    if i < 0 or j < 0 or j <= i:
        raise SystemExit("cannot locate the section between %s and %s -- the "
                         "index headings have changed and this derivation is "
                         "void. Refusing to report a denominator." % (start_id, end_id))
    return html[i:j]


def card_state(pub):
    p = (pub or "").lower()
    if "audit-first" in p:
        return "AUDIT-FIRST"
    if "withdrawn" in p:
        return "WITHDRAWN"
    if "not poolable" in p or "not analysable" in p or "not pooled" in p:
        return "NOT-POOLABLE"
    if "reported separately" in p:
        return "REPORTED-SEPARATELY"
    if re.search(r"\d\.\d", pub or ""):
        return "LIVE-ESTIMATE"
    return "OTHER"


def main() -> int:
    idx = open(os.path.join(REPO, "index.html"), encoding="utf-8",
               errors="replace").read()
    seg = section(idx, "sp-cardiology", "sp-dermatology")
    links = sorted(set(re.findall(r'href="([A-Za-z0-9_\-]+\.html)"', seg)))
    cards = dict(CARD.findall(idx))
    pm = json.loads(open(os.path.join(REPO, "ssot", "PAGE_MAP.json"),
                         encoding="utf-8").read())

    stubs, topics = [], []
    for p in links:
        fp = os.path.join(REPO, p)
        if os.path.exists(fp) and os.path.getsize(fp) <= STUB_MAX:
            t = open(fp, encoding="utf-8", errors="replace").read()
            if "http-equiv=\"refresh\"" in t.lower() or "location.replace" in t:
                stubs.append(p)
                continue
        topics.append(p)

    print("DENOMINATOR")
    print("  page links in #sp-cardiology : %d" % len(links))
    print("  redirect stubs (not topics)  : %d  %s" % (len(stubs), ", ".join(stubs)))
    print("  TOPICS                       : %d" % len(topics))

    done, rest = [], []
    for p in topics:
        (done if p in pm else rest).append(p)
    print("\nDONE (has an SSOT object in PAGE_MAP): %d of %d" % (len(done), len(topics)))
    for p in done:
        print("   %-52s %s" % (p[:52], card_state(cards.get(p, ""))))

    print("\nNOT DONE, by what the index card claims:")
    tally = {}
    for p in rest:
        k = "NO-CARD" if p not in cards else card_state(cards[p])
        tally.setdefault(k, []).append(p)
    for k in sorted(tally, key=lambda x: -len(tally[x])):
        print("   %-22s %d" % (k, len(tally[k])))

    # The self-contradiction on the audit-first cards, counted rather than recalled.
    contra = []
    for p in topics:
        pub = cards.get(p, "")
        if "Audit-first" not in pub:
            continue
        mt = re.search(r"(\d+)\s+trials", pub)
        mk = re.search(r"k>=(\d+)", pub)
        if mt and mk and int(mt.group(1)) < int(mk.group(1)):
            contra.append((p, int(mt.group(1)), int(mk.group(1))))
    print("\nAUDIT-FIRST CARDS WHOSE OWN TRIAL COUNT IS BELOW THE k THEY CLAIM: "
          "%d of %d" % (len(contra), sum(1 for p in topics
                                         if "Audit-first" in cards.get(p, ""))))
    for p, t, k in contra:
        print("   %-52s says %d trials AND k>=%d" % (p[:52], t, k))
    if contra:
        print("   card_alignment_gate cannot see this: an audit-first card is "
              "UNCHECKABLE by construction.")

    print("\nThis script counts what the index SAYS. It does not open the pages "
          "to check whether the cards are true.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
