#!/usr/bin/env python3
"""Build an adjudication dossier for the 47 confirmed Q2 findings. LAYER: served bytes.

WHY A DOSSIER RATHER THAN A VERDICT. Each finding asserts that a page says one thing and
elsewhere shows another. Neither half can be judged from the finding's own wording -- the
wording is the reviewer's, and our reviewers are measurably biased toward accusing our own
pages. So this pulls THE PAGE'S OWN WORDS for both halves and stops there. The adjudication is
a separate act, done against this evidence.

It is a dossier, not a gate or a check, and is named accordingly: it returns material, never a
verdict, and must not carry a name that promises a block.

The first finding adjudicated this way was refuted by its own evidence: a page said "Figure 1
not drawn ... a forest plot is the pooled claim in picture form", and the reviewer called that
a contradiction because forest plots appear elsewhere on the page. Pulling the SVGs showed they
contain only the two per-trial estimates with no pooled summary, so the page declines exactly
what it says it declines. Reading the finding alone would have produced a wrong fix.
"""
import io
import json
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
OUT = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
TAG = re.compile(r"<[^>]+>")
WS = re.compile(r"\s+")
SCRIPT = re.compile(r"(?is)<(script|style)\b.*?</\1>")
NONWORD = re.compile(r"[^a-z0-9 ]+")


def say(s=""):
    OUT.write(s + "\n")
    OUT.flush()


def rendered(html):
    return WS.sub(" ", TAG.sub(" ", SCRIPT.sub(" ", html))).strip()


def norm(s):
    return WS.sub(" ", NONWORD.sub(" ", (s or "").lower())).strip()


def best_window(text, key, span=60):
    """Return the page's own words around the densest cluster of the key's content tokens.
    Contiguity, not bag-of-words: a known-negative control put unrelated pages at median 0.36
    under this measure against 1.00 on the page the finding names."""
    kt = [w for w in norm(key).split() if len(w) > 3]
    if not kt:
        return "", 0.0
    words = text.split()
    nw = [norm(w) for w in words]
    best, at = 0, 0
    for i in range(0, max(1, len(words) - 20), 10):
        w = set(nw[i:i + span])
        c = sum(1 for x in kt if x in w)
        if c > best:
            best, at = c, i
    return " ".join(words[max(0, at - 10):at + span + 10]), best / len(kt)


def main():
    part = json.load(io.open(os.path.join(ROOT, "out", "partition_47.json"), encoding="utf-8"))
    items = part["safe"] + part["readjudicate"]
    pm = json.load(io.open(os.path.join(ROOT, "ssot", "PAGE_MAP.json"), encoding="utf-8"))

    cache = {}

    def page_text(pg):
        if pg not in cache:
            p = os.path.join(ROOT, pg)
            cache[pg] = rendered(io.open(p, encoding="utf-8", errors="replace").read()) \
                if os.path.exists(p) else ""
        return cache[pg]

    dossier = []
    for it in items:
        pg = it.get("page")
        txt = page_text(pg) if pg else ""
        claim, cov = best_window(txt, it["key"]) if txt else ("", 0.0)
        # the reviewer's stated counter-evidence, in the page's own words where locatable
        ex = " ".join(it.get("examples") or [])
        counter, ccov = best_window(txt, ex) if txt and ex else ("", 0.0)
        obj = pm.get(pg)
        dossier.append(dict(page=pg, topic=(it.get("topics") or [None])[0], key=it["key"],
                            cls=it.get("cls"), why=it.get("why"),
                            reviewer_example=ex[:600],
                            page_says=claim[:700], page_says_coverage=round(cov, 2),
                            page_counter=counter[:700], counter_coverage=round(ccov, 2),
                            store_object=obj))

    with io.open(os.path.join(ROOT, "out", "dossier_47.json"), "w",
                 encoding="utf-8", newline="\n") as fh:
        json.dump(dossier, fh, indent=1, ensure_ascii=False)

    say("DOSSIER for %d findings, LAYER: served bytes" % len(dossier))
    say("  pages read            : %d" % len(cache))
    say("  claim located on page : %d" % sum(1 for d in dossier if d["page_says_coverage"] >= 0.85))
    say("  counter-evidence found: %d" % sum(1 for d in dossier if d["counter_coverage"] >= 0.55))
    say("  neither locatable     : %d" % sum(1 for d in dossier
                                             if d["page_says_coverage"] < 0.55
                                             and d["counter_coverage"] < 0.55))
    say("wrote out/dossier_47.json")
    return 0


if __name__ == "__main__":
    sys.exit(main())
