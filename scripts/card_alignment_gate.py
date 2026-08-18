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

THE COMFORTABLE FAILURE MODE THIS GATE SHIPPED WITH, AND WHAT IT COST
    Until 2026-08-18 the first line of check() was: if the card declares a
    withheld state, return UNCHECKABLE. THE WORD "WITHDRAWN" ON THE CARD STOPPED
    THE GATE LOOKING AT THE PAGE AT ALL. That is the exact shape this project
    keeps producing -- a check whose reassuring branch is also its blind branch,
    so nobody investigates it.

    It is not hypothetical. SGLT2_HF went live at 7124fdbed^ with the card
    reading "Four-trial pool WITHDRAWN -- the trials do not share one endpoint"
    and the page's own headline still reading "Pooled result HR 0.7785 (0.7296
    to 0.8306)". THE CARD ANNOUNCED A WITHDRAWAL THE PAGE HAD NOT PERFORMED, and
    this gate returned UNCHECKABLE on it -- not a FAIL it missed, a look it
    declined to take. Every run in between recorded that page as "nothing to
    compare".

    A withdrawal is a CLAIM, and it is checkable on both surfaces exactly as a
    value is. The gate now reads the page in both directions:

      card withheld + page headline withheld   -> WITHHELD  (agreement, exit 3)
      card withheld + page renders a value     -> FAIL      (the SGLT2_HF state)
      card carries a value + page withheld     -> FAIL      (the inverse)
      card value vs page value                 -> PASS/FAIL (numeric, as before)

    WITHHELD IS NOT PASS AND IS NOT UNCHECKABLE. The property is met, by
    withholding on both surfaces, and scoring that as a pass would make a page
    that found a problem and acted on it indistinguishable from one that pooled
    straight through -- the same distinction estimand_definition_gate carries.

WHY THE HEADLINE IS READ FROM MARKUP AND NOT FROM FLATTENED TEXT
    The previous reader regex-searched the whole flattened page for "Pooled
    result <num> (<lo> to <hi>)". SGLT2_HF's page now contains the sentence
    "Pooled result card still read HR 0.7785 (0.7296 to 0.8306) as the headline"
    -- prose ABOUT the defect, in the section that documents it. A reader that
    cannot tell a headline from a sentence describing a headline will convict a
    page for confessing. The slot is now anchored on its own <h2>, and what
    counts is the element immediately after it.

WHAT A FULL PASS DOES NOT ESTABLISH -- written in advance
    - NOT that the value is CORRECT. Three surfaces can agree and all be wrong;
      that is what the source-verification work is for.
    - NOT that the card's MEASURE word is right. It compares numbers; a card
      saying OR where the page says HR with the same number passes here.
    - NOT that a WITHHELD verdict means the withdrawal was JUSTIFIED. It means
      both surfaces say the same thing. Withdrawing a correct estimate destroys a
      true finding, and no agreement between two of our own surfaces can detect
      that -- the reason has to be checked against the registry by hand.
    - NOT anything about cards carrying no number and no withheld state --
      "Audit-first build" cards are UNCHECKABLE, never PASS.
    - NOT that the page itself is internally consistent.
"""
from __future__ import annotations
import json, os, re, sys, io

if __name__ == "__main__":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

# THE REPO IS THE ONE THIS FILE LIVES IN. It was hardcoded to an absolute path,
# which is the false-life defect in the ledger's matched pair: run from a sibling
# clone, the gate silently graded ANOTHER working tree's index and pages and
# reported green about bytes nobody was pushing. A gate reading the wrong tree is
# worse than no gate, because no gate at least never produces a green.
SSOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
NUM = re.compile(r"-?\d+\.\d{2,4}")

# THE VOCABULARY OF NOT-PUBLISHING, AND WHY THIS LIST IS LONGER THAN IT WAS.
#
# A CONSTANT NAMED `WITHHELD` DID NOT MATCH THE WORD "WITHHELD". It listed
# withdrawn / not analysable / not poolable / not pooled / reported separately /
# audit-first, and two live cards -- PCSK9_REVIEW and SGLT2_CKD_REVIEW -- read
# "Withheld pending rebuild -- HR 0.85 (0.79-0.92), k=2, not checkable from the
# page". The gate classified both as ORDINARY PUBLISHED VALUES and stood ready to
# compare the quoted number against the page and report PASS: agreement, on a
# card whose own first word says the estimate is not being published.
#
# Found the same day the withheld branch was widened, and it is the ledger's own
# rule turned on its author: WIDENING A FINDER WITHOUT WIDENING ITS CLASSIFIER IS
# NOT A PARTIAL FIX. Teaching the gate what to DO with a withheld card while
# leaving it unable to RECOGNISE one is the same defect as matching a phrase and
# assigning it to no key.
#
# "superseded" is here for the same reason: FINERENONE_REVIEW's card says the page
# was superseded because it pooled a kidney primary with a cardiovascular one.
# That is a page not publishing a value, and the branch that handles it is the
# withheld branch.
#
# THE STANDING HAZARD: this is a fixed phrase list over a HAND-AUTHORED surface,
# so it is wrong again the first time someone writes a new way of saying "we are
# not publishing this". The list cannot fix that -- only projecting cards from
# objects can. Until then, `--audit-vocabulary` prints every card the gate treats
# as carrying a live value while containing not-publishing language, so the next
# gap is found by running the gate rather than by an incident.
WITHHELD = re.compile(r"withdrawn|withheld|withhold|not analysable|not poolable|"
                      r"not pooled|reported separately|audit-first|superseded", re.I)

# Language that reads like a page declining to publish, used ONLY by
# --audit-vocabulary to hunt the next gap. Deliberately over-broad: it reports,
# it never decides.
SUSPECT = re.compile(r"withheld|withhold|pending|not established|no estimate|"
                     r"cannot|unavailable|suppress|retract|under review|"
                     r"provisional|invalid|unverified|superseded|deprecated", re.I)
TOL = 0.006

# The headline slot, anchored on its own heading. Both generations of the
# projector are accepted: <h2>Pooled result</h2> (pre-tabbed) and
# <h2 id="extract-pooled-result...">Pooled result</h2> (tabbed).
SLOT = re.compile(r"<h2(?:\s+id=[\"']extract-pooled-result[^\"']*[\"'])?\s*>"
                  r"\s*Pooled result\s*</h2>", re.I)
# What may immediately follow it: a value, or a declared withdrawal.
LIVE = re.compile(r"^\s*<p class=['\"]num['\"]>\s*([A-Za-z_]*)\s*(-?[\d.]+)\s*"
                  r"\(\s*(-?[\d.]+)\s+to\s+(-?[\d.]+)\s*\)", re.I)
WD_SLOT = re.compile(r"^\s*<div class=['\"]absent-state['\"][^>]*>\s*<strong>\s*"
                     r"(?:Estimate withdrawn|Pool withdrawn|No pooled estimate)", re.I)
SCRIPTY = re.compile(r"<(script|style)[^>]*>.*?</\1\s*>", re.I | re.S)


def nums(s):
    return [float(x) for x in NUM.findall((s or "").replace("&minus;", "-")
                                          .replace("\u2212", "-"))]


def page_headlines(text):
    """Every pooled-result slot on the page, in document order.

    Returns a list of ("LIVE", measure, [point, lo, hi]) or ("WITHDRAWN", None, [])
    or ("UNREADABLE", None, []) -- the last for a slot whose next element is
    neither, which is reported rather than guessed at.
    """
    t = SCRIPTY.sub(" ", text)
    out = []
    for m in SLOT.finditer(t):
        tail = t[m.end():m.end() + 500]
        lv = LIVE.search(tail)
        if lv:
            out.append(("LIVE", lv.group(1) or None,
                        [float(lv.group(2)), float(lv.group(3)), float(lv.group(4))]))
        elif WD_SLOT.search(tail):
            out.append(("WITHDRAWN", None, []))
        else:
            out.append(("UNREADABLE", None, []))
    return out


def page_headline(text):
    """Back-compat single-value reader: the first LIVE slot, or (None, [])."""
    for kind, meas, vals in page_headlines(text):
        if kind == "LIVE":
            return meas, vals
    return None, []


def check(card_pub, page_text):
    slots = page_headlines(page_text)
    live = [s for s in slots if s[0] == "LIVE"]
    withdrawn = [s for s in slots if s[0] == "WITHDRAWN"]
    card_withheld = bool(WITHHELD.search(card_pub or ""))

    if not slots:
        return ("UNCHECKABLE",
                "page renders no pooled-result slot this gate can read -- "
                "neither a value nor a declared withdrawal")

    if card_withheld:
        if live:
            return ("FAIL",
                    "card declares a WITHHELD state and the page still publishes "
                    "%s %s in its headline -- the withdrawal was announced on one "
                    "surface and not performed on the other"
                    % (live[0][1] or "", live[0][2]))
        if withdrawn:
            return ("WITHHELD",
                    "card and page both withhold; %d slot(s) declare it. The "
                    "AGREEMENT is checked here, the JUSTIFICATION is not"
                    % len(withdrawn))
        return ("UNCHECKABLE",
                "card declares a withheld state; the page's slot is neither a "
                "value nor a recognised withdrawal statement")

    cn = nums(card_pub)
    if not cn:
        return "UNCHECKABLE", "card carries no numeric value and no withheld state"
    if not live:
        return ("FAIL",
                "card publishes %s while the page's headline is WITHDRAWN -- the "
                "index is serving a value the page has retracted" % (cn[:3],))
    pn = [v for s in live for v in s[2]]
    hit = any(abs(c - p) <= TOL for c in cn for p in pn)
    if hit:
        return "PASS", "card %s agrees with page %s" % (cn[:3], live[0][2])
    return ("FAIL", "card %s vs page %s %s -- a served contradiction"
            % (cn[:3], live[0][1] or "", live[0][2]))


def audit_vocabulary() -> int:
    """Every card the gate treats as a LIVE VALUE while its text reads like a
    page declining to publish. This is how the next vocabulary gap gets found by
    running the gate instead of by an incident.

    It reports and never decides: a card saying "Published: ... k=4 -- OPEN
    QUESTION: ..." is a live value with a caveat and belongs on this list as
    something to LOOK at, not as a defect.
    """
    idx = open(os.path.join(SSOT, "index.html"), encoding="utf-8",
               errors="replace").read()
    cards = re.findall(r'<a href="([A-Za-z0-9_]+\.html)" class="card [^"]*">'
                       r'<span class="name">[^<]*</span><span class="pub">(.*?)</span></a>', idx)
    live = [(h, p) for h, p in cards if not WITHHELD.search(p)]
    flag = [(h, p) for h, p in live if SUSPECT.search(p)]
    print("cards on the index: %d" % len(cards))
    print("treated as carrying a LIVE VALUE: %d" % len(live))
    print("OF THOSE, cards whose text reads like a page NOT publishing: %d" % len(flag))
    for h, p in sorted(flag):
        print("  [%-15s] %-42s %s"
              % (SUSPECT.search(p).group(0).lower()[:15], h[:42],
                 re.sub(r"\s+", " ", p)[:80]))
    print("\nEach line is a card to READ, not a defect. A gap here is a phrase "
          "this gate cannot recognise; the fix is the vocabulary, or better, "
          "projecting cards from objects so there is no vocabulary to miss.")
    return 0


def main() -> int:
    if "--selftest" in sys.argv:
        return selftest()
    if "--audit-vocabulary" in sys.argv:
        return audit_vocabulary()
    # SCOPE. This gate took a page and an object as arguments AND IGNORED BOTH,
    # sweeping the whole index regardless -- so it returned byte-identical output
    # for two different objects, and card_matches_page passed GLOBALLY while
    # being unmeasured PER PAGE. A gate whose result does not change when its
    # subject changes is not checking the subject. Named targets now restrict it.
    targets = {os.path.basename(a) for a in sys.argv[1:]
               if a.upper().endswith(".HTML")}
    idx = open(os.path.join(SSOT, "index.html"), encoding="utf-8", errors="replace").read()
    cards = re.findall(r'<a href="([A-Za-z0-9_]+\.html)" class="card [^"]*">'
                       r'<span class="name">[^<]*</span><span class="pub">(.*?)</span></a>', idx)
    if targets:
        cards = [(h, pub) for h, pub in cards if h in targets]
        missing = targets - {h for h, _ in cards}
        for m in sorted(missing):
            print("  %-46s NO CARD ON THE INDEX -- not a pass" % m)
        if not cards:
            print("  -> UNCHECKABLE: none of the named pages has a card on the index.")
            return 2
    tot = {"PASS": 0, "FAIL": 0, "WITHHELD": 0, "UNCHECKABLE": 0, "NOPAGE": 0}
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
    for k in ("PASS", "FAIL", "WITHHELD", "UNCHECKABLE", "NOPAGE"):
        print("  %-12s %d" % (k, tot[k]))
    # THE PROPORTION CARRIES ITS COMPARABLE FRACTION, INLINE, ALWAYS.
    # "0.0% drift" over 6 comparable cards while 508 of 514 are UNCHECKABLE is a
    # reassuring headline computed over 1.2% of the corpus. It is not a rate over
    # an empty set -- but a rate whose denominator excludes almost everything,
    # printed without saying so, is the same family one degree down.
    #
    # WITHHELD cards are MEASURED and are stated separately rather than folded
    # into either the numerator or the unmeasured remainder: they carry no number
    # to drift, and counting them as clean would inflate the agreement rate with
    # pages that publish nothing to agree about.
    d = tot["PASS"] + tot["FAIL"]
    n = sum(tot.values())
    if not d:
        print("  drift: UNCHECKABLE -- 0 of %d cards were numerically comparable. "
              "No rate is rendered, because a proportion over nothing is not 0%%. "
              "%d card(s) agree by withholding; %d are unmeasured."
              % (n, tot["WITHHELD"], tot["UNCHECKABLE"] + tot["NOPAGE"]))
    else:
        print("  drift among COMPARABLE cards: %d/%d = %.1f%%  "
              "[comparable: %d of %d cards = %.1f%% of the set; %d agree by "
              "WITHHOLDING; the other %d are UNMEASURED, not clean]"
              % (tot["FAIL"], d, 100.0 * tot["FAIL"] / d, d, n,
                 100.0 * d / n if n else 0.0, tot["WITHHELD"],
                 n - d - tot["WITHHELD"]))
    for h, w in bad:
        print("    %-46s %s" % (h[:46], w))
    try:
        json.dump([{"page": h, "why": w} for h, w in bad],
                  open(r"F:\E156\outputs\codex-corpus-scan\CARD-DRIFT.json", "w",
                       encoding="utf-8"), indent=1)
    except OSError as e:
        # SAID OUT LOUD. A report that could not be written is not a report that
        # was written, and this gate has a ledger entry about exactly that.
        print("  NOTE: CARD-DRIFT.json was NOT written (%s). The verdicts above "
              "stand; the durable record of them does not." % e)
    if tot["FAIL"]:
        return 1
    # 3 = MET BY WITHHOLDING, and only when EVERY card examined was withheld.
    # Over a mixed sweep the exit code cannot say this, so it does not try.
    if tot["WITHHELD"] and not tot["PASS"] and not tot["UNCHECKABLE"] and not tot["NOPAGE"]:
        return 3
    return 0


def _git_show(rev_path):
    """Real historical bytes, or None. Never a substitute constructed by hand."""
    import subprocess
    try:
        r = subprocess.run(["git", "show", rev_path], cwd=SSOT,
                           capture_output=True, timeout=120)
    except Exception:
        return None
    if r.returncode != 0 or not r.stdout:
        return None
    return r.stdout.decode("utf-8", "replace")


def selftest() -> int:
    """Every case is real bytes this project actually served. A synthetic input
    proves a detector CAN fire; a replayed defect is the only thing that shows it
    DISCRIMINATES."""
    ok = True

    disk_cases = [
        # The historical ABLATION card (a live value) against today's page, whose
        # headline is WITHDRAWN. This is the inverse branch, and it is the state
        # that would have existed had 1d652297a withdrawn the page and not the
        # card -- which is precisely what that commit's message says it avoided.
        ("ABLATION card 'HR 0.77' vs page now WITHDRAWN  [inverse branch]",
         "Published: HR 0.77 (0.64&ndash;0.93), k=4",
         "ABLATION_AF_REVIEW.html", "FAIL"),
        ("NEGATIVE SOTAGLIFLOZIN (card == page)",
         "Published: HR 0.7171 (0.6246&ndash;0.8234), k=2",
         "SOTAGLIFLOZIN_HF_REVIEW.html", "PASS"),
        ("WITHHELD ABLATION_AF (both surfaces withhold)",
         "Estimate withdrawn &mdash; the four trials measure four DIFFERENT "
         "primary composites", "ABLATION_AF_REVIEW.html", "WITHHELD"),
        ("WITHHELD SGLT2_HF (both surfaces withhold)",
         "Four-trial pool WITHDRAWN &mdash; the trials do not share one endpoint",
         "SGLT2_HF_REVIEW.html", "WITHHELD"),
    ]

    # ---- THE VOCABULARY CASE, from two cards live on the index today ------
    # A constant named WITHHELD did not match the word "withheld". Both of these
    # were classified as ordinary published values.
    for name, pub in (
        ("VOCABULARY 'Withheld pending rebuild' is a withheld state (SGLT2_CKD)",
         "Withheld pending rebuild &mdash; HR 0.68 (0.60&ndash;0.77), k=3, not "
         "checkable from the page: no per-value provenance"),
        ("VOCABULARY 'Withheld pending rebuild' is a withheld state (PCSK9)",
         "Withheld pending rebuild &mdash; HR 0.85 (0.79&ndash;0.92), k=2, not "
         "checkable from the page: no per-value provenance"),
        ("VOCABULARY 'Superseded' is a withheld state (FINERENONE)",
         "Superseded &mdash; pooled a kidney primary with a cardiovascular "
         "primary; rebuilt from source as Finerenone CV composite"),
    ):
        got = bool(WITHHELD.search(pub))
        ok &= got
        print("  %-62s -> recognised=%-5s (want True) %s"
              % (name[:62], got, "correct" if got else "WRONG"))

    for name, pub, page, want in disk_cases:
        p = os.path.join(SSOT, page)
        if not os.path.exists(p):
            print("  %-62s page absent -- NOT PROVEN" % name[:62]); ok = False; continue
        v, why = check(pub, open(p, encoding="utf-8", errors="replace").read())
        good = v == want
        ok &= good
        print("  %-62s -> %-11s (want %-11s) %s"
              % (name[:62], v, want, "correct" if good else "WRONG"))
        print("        %s" % why[:110])

    # ---- THE REPLAY. The state that actually went live. -------------------
    # SGLT2_HF at 7124fdbed^: card announces the withdrawal, page headline still
    # publishes HR 0.7785. The gate that shipped returned UNCHECKABLE here.
    name = "REPLAY SGLT2_HF @7124fdbed^ (card withdrawn, page LIVE 0.7785)"
    blob = _git_show("7124fdbed^:SGLT2_HF_REVIEW.html")
    if blob is None:
        print("  %-62s history unavailable -- NOT PROVEN" % name[:62]); ok = False
    else:
        pub = ("Four-trial pool WITHDRAWN &mdash; the trials do not share one "
               "endpoint. Urgent-visit composite HR 0.7835 (0.7090&ndash;0.8659), "
               "k=2; hospitalisation-only composite HR 0.7708 "
               "(0.7000&ndash;0.8488), k=2")
        v, why = check(pub, blob)
        good = v == "FAIL"
        ok &= good
        print("  %-62s -> %-11s (want %-11s) %s"
              % (name[:62], v, "FAIL", "correct" if good else "WRONG"))
        print("        %s" % why[:110])
        # AND THE OLD GATE MUST NOT HAVE CAUGHT IT. A replay the previous version
        # also caught proves nothing about this change.
        print("        the version this replaces returned UNCHECKABLE on these "
              "same bytes: the card said 'WITHDRAWN' and it stopped reading")

    # ---- the reader must not convict a page for DESCRIBING the defect -----
    name = "NEGATIVE prose about a headline is not a headline"
    p = os.path.join(SSOT, "SGLT2_HF_REVIEW.html")
    if not os.path.exists(p):
        print("  %-62s page absent -- NOT PROVEN" % name[:62]); ok = False
    else:
        t = open(p, encoding="utf-8", errors="replace").read()
        has_prose = "still read HR 0.7785" in t
        kinds = [k for k, _, _ in page_headlines(t)]
        good = has_prose and "LIVE" not in kinds
        ok &= good
        print("  %-62s -> slots=%s prose=%s %s"
              % (name[:62], kinds, has_prose, "correct" if good else "WRONG"))

    print("\nWHAT A FAILURE WOULD LOOK LIKE: the SGLT2_HF replay returning "
          "UNCHECKABLE or PASS -- a card announcing a withdrawal the page never "
          "performed, recorded as 'nothing to compare'.")
    print("-> SELFTEST PASS" if ok else "-> SELFTEST FAILED")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
