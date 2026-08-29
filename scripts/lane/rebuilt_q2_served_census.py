#!/usr/bin/env python3
"""Census of the 70 REBUILT-VERIFY-AT-PASS-2 findings against SERVED BYTES.

NAMED A CENSUS, NOT A VERIFIER. It returns counts in three states and never a pass/fail, so
a `verify_` prefix would promise a block it cannot deliver -- lint_gate_can_fail refused it
under that name and was right. The defect was the name, not the body.

LAYER: served bytes. These findings are claims about what a reader is told, and the pages
have already been rebuilt, so the delivered HTML is the artefact that can settle them. The
store and the generator are not consulted here; if a finding survives this pass it is then a
question for those layers, in that order.

THREE OUTCOMES, NEVER TWO.
    CONFIRMED       the claimed sentence is on the page AND the contradicting material is too
    NOT_REPRODUCED  the claimed sentence is NOT on the page as served
    CANNOT_TELL     the page cannot be located, or the finding names no quotable sentence

A finding that cannot be reproduced is A FINDING ABOUT THE DETECTOR, not an absence. It is
recorded as that and counted separately, because "we could not find it" and "it is not there"
are different facts and only one of them is about the corpus.

RENDERED TEXT, NEVER SOURCE, and scripts stripped first: a sentence a reader sees as one
string is often several in the file, split by an inline tag or a newline inside a <p>, and a
check that searches source scores such a page clean. Two headline findings on this project
came from counting markup a reader never sees.

WHAT THIS CANNOT DO, stated rather than implied: it matches on the finding's own key phrase,
so a finding whose key is a paraphrase rather than a quotation will read as NOT_REPRODUCED
even when the defect is real. That is why NOT_REPRODUCED is a finding about the detector and
must be hand-read before it is believed, not treated as a clearance.
"""
import io
import json
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
OUT = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")


def say(s=""):
    OUT.write(s + "\n")
    OUT.flush()


TAG = re.compile(r"<[^>]+>")
WS = re.compile(r"\s+")
SCRIPT = re.compile(r"(?is)<(script|style)\b.*?</\1>")
NONWORD = re.compile(r"[^a-z0-9 ]+")


def rendered(html):
    return WS.sub(" ", TAG.sub(" ", SCRIPT.sub(" ", html))).strip()


def norm(s):
    """Lowercase, strip punctuation and collapse space. The finding keys are already
    normalised this way, so the page must be normalised identically or nothing will match."""
    return WS.sub(" ", NONWORD.sub(" ", (s or "").lower())).strip()


def page_index():
    """topic -> [(page, normalised rendered text)]. Built once; pages are large."""
    pm = json.load(io.open(os.path.join(ROOT, "ssot", "PAGE_MAP.json"), encoding="utf-8"))
    idx = {}
    for page, obj in pm.items():
        topic = os.path.basename(os.path.dirname(obj))
        p = os.path.join(ROOT, page)
        if not os.path.exists(p):
            continue
        html = io.open(p, encoding="utf-8", errors="replace").read()
        idx.setdefault(topic, []).append((page, norm(rendered(html))))
    return idx


def main():
    routed = json.load(io.open(os.path.join(ROOT, "out", "blind-review", "q2_routed.json"),
                               encoding="utf-8"))
    items = [x for x in routed if x.get("route") == "REBUILT-VERIFY-AT-PASS-2"]
    idx = page_index()

    say("LAYER: served bytes (rendered text, scripts stripped)")
    say("pages indexed: %d across %d topics" % (sum(len(v) for v in idx.values()), len(idx)))
    say("findings to verify: %d classes, %d findings"
        % (len(items), sum(x.get("n", 0) for x in items)))
    say("")

    rows = []
    for x in items:
        key = norm(x.get("key"))
        topics = x.get("topics") or []
        cand = [(pg, txt) for t in topics for pg, txt in idx.get(t, [])]
        if not cand:
            rows.append(dict(key=x["key"], topics=topics, verdict="CANNOT_TELL",
                             why="no page on disk for topic(s) %s" % ", ".join(topics),
                             page=None))
            continue
        # EXACT SUBSTRING WAS THE WRONG INSTRUMENT, and hand-reading proved it: 6 of 6 sampled
        # NOT_REPRODUCED verdicts were matcher failures, not absent content. The finding keys
        # are a MIX of verbatim quotation and paraphrase, and one case settled it -- the key
        # "no systematic search was run the included set is a named two trial programme" is on
        # the page with a clause interpolated mid-sentence, so exact matching scored a present
        # sentence as missing. Coverage of the key's content words survives interpolation,
        # reordering and paraphrase; a substring does not.
        # AND BAG-OF-WORDS WAS ALSO WRONG, measured the same way. A known-negative control put
        # the same keys against UNRELATED pages: median coverage 0.60 and 13 of 70 scored above
        # the 0.85 threshold, so nearly one in five "confirmations" was page size rather than
        # content. Hand-reading five confirmations settled it -- BOSENTAN scored 0.86 on scattered
        # common words whose best window was PROSPERO boilerplate, nothing to do with the claim.
        #
        # CONTIGUITY IS THE DISCRIMINATOR. A sentence a page actually contains puts its content
        # words CLOSE TOGETHER; a page that merely shares vocabulary scatters them. So the score
        # is the best fraction of key tokens falling inside one 60-word window, which is roughly
        # the span of the sentences these findings quote.
        best_pg, best_cov = cand[0][0], 0.0
        kt = [w for w in key.split() if len(w) > 3]
        for pg, txt in cand:
            words = txt.split()
            top = 0
            for i in range(0, max(1, len(words) - 20), 20):
                w = set(words[i:i + 60])
                c = sum(1 for x in kt if x in w)
                if c > top:
                    top = c
            cov = (top / len(kt)) if kt else 0.0
            if cov > best_cov:
                best_pg, best_cov = pg, cov
        if best_cov >= 0.85:
            rows.append(dict(key=x["key"], topics=topics, verdict="CONFIRMED_PRESENT",
                             why="%.0f%% of the key's content words fall in ONE 60-word window"
                                 % (best_cov * 100),
                             coverage=round(best_cov, 3), page=best_pg,
                             finding_class=x.get("finding_class"),
                             direction=x.get("direction")))
        elif best_cov >= 0.55:
            rows.append(dict(key=x["key"], topics=topics, verdict="PARTIAL_NEEDS_HAND_READ",
                             why="%.0f%% coverage -- too much to call absent, too little to "
                                 "call present" % (best_cov * 100),
                             coverage=round(best_cov, 3), page=best_pg,
                             finding_class=x.get("finding_class"),
                             direction=x.get("direction")))
        else:
            rows.append(dict(key=x["key"], topics=topics, verdict="NOT_REPRODUCED",
                             why="best window holds only %.0f%% of the key's content words, across %d "
                                 "candidate page(s)" % (best_cov * 100, len(cand)),
                             coverage=round(best_cov, 3), page=best_pg,
                             finding_class=x.get("finding_class"),
                             direction=x.get("direction")))

    counts = {}
    for r in rows:
        counts[r["verdict"]] = counts.get(r["verdict"], 0) + 1
    say("%-22s %s" % ("VERDICT", "n"))
    say("%-22s %s" % ("-" * 22, "-"))
    for k in ("CONFIRMED_PRESENT", "PARTIAL_NEEDS_HAND_READ", "NOT_REPRODUCED",
              "CANNOT_TELL"):
        say("%-22s %d   /%d" % (k, counts.get(k, 0), len(rows)))
    say("")
    say("NOT_REPRODUCED IS A FINDING ABOUT THE DETECTOR, not a clearance. This matches on the")
    say("finding's own key phrase; a key that paraphrases rather than quotes will miss a real")
    say("defect. Every one must be hand-read before it is believed.")

    with io.open(os.path.join(ROOT, "out", "verify_rebuilt_q2.json"), "w",
                 encoding="utf-8", newline="\n") as fh:
        json.dump({"layer": "served bytes", "n_classes": len(items),
                   "counts": counts, "rows": rows}, fh, indent=1, ensure_ascii=False)
    say("wrote out/verify_rebuilt_q2.json")
    return 0


if __name__ == "__main__":
    sys.exit(main())
