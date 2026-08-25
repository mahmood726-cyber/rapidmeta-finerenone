"""Is the reference a label resolved to actually that trial's paper? Ask a second database.

THE GAP THIS CLOSES. The end-to-end join reports that 676 of 886 labels resolve to exactly one
reference. "Exactly one match" is a statement about the matcher, not about the world -- a
matcher that agrees with itself proves nothing, which is the failure this project has already
recorded once as "consistency does not authenticate a row".

THE INDEPENDENT CHECK. Matching used CROSSREF's author field, carried in the review's own
reference list. PubMed indexes the same paper separately, with its own `<LastName>`. The two
are different databases populated by different processes, so agreement between them is
corroboration rather than self-consistency.

    does PubMed's first author for the resolved PMID equal the surname in the Cochrane label?

NULL, and it is not a formality. Cochrane labels within one review often repeat a surname
(Legare 2008a, Legare 2011, Legare 2012), so a shifted pairing agrees by chance more often
than intuition suggests. Each paper is therefore also scored against the NEXT label's token,
and that rate is reported beside the real one.

ACCENTS ARE FOLDED, and this is not cosmetic. Cochrane labels are ASCII (`Bjorklund 2012`,
`Legare 2008a`) while PubMed holds the accented form (`Bjorklund` with an umlaut, `Legare`
with two acutes). Compared raw, 21 correct resolutions score as disagreements -- a 4% error
rate invented entirely by character encoding. Folded, they agree.
"""
import html
import io
import json
import os
import re
import sys
import unicodedata

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(REPO, "scripts"))
XML = os.path.join(REPO, "outputs", "pubmed_databank_cache")
OUT = os.path.join(REPO, "outputs", "resolution_validated_2026_08_25.json")

LAST = re.compile(r"<LastName>([^<]{1,60})</LastName>")


def fold(text):
    """ASCII-fold for comparison: unescape entities, strip combining marks, lowercase.

    The character sequence is made explicit with list() rather than iterating the parameter.
    lint_string_where_collection_expected refuses a string reaching a parameter that gets
    iterated -- correctly, because that is how a string silently behaves as a collection of
    characters. Here characters ARE the intent, and saying so in the code is better than
    exempting the rule.
    """
    chars = list(unicodedata.normalize("NFKD", html.unescape(text or "")))
    return "".join(c for c in chars if not unicodedata.combining(c)).lower().strip()


def cached(pmid):
    for ext in (".xml", ".txt"):
        fp = os.path.join(XML, str(pmid) + ext)
        if os.path.exists(fp):
            return io.open(fp, encoding="utf-8", errors="replace").read()
    return None


def first_author(pmid):
    m = LAST.search(cached(pmid) or "")
    return m.group(1) if m else None


def run_controls():
    from instrument_controls import require_controls
    require_controls(
        "resolution_validated (fold)",
        ("an accented surname folds to its ASCII label form",
         fold("Bj&#xf6;rklund") == fold("Bjorklund"), True),
        ("two DIFFERENT surnames are FLAGGED as equal",
         fold("Legare") == fold("Stacey"), True))


def main(src=None):
    run_controls()
    src = src or os.path.join(REPO, "outputs", "join_end_to_end_2026_08_25.json")
    raw = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace",
                           write_through=True)

    def log(s):
        raw.write(s + chr(10))
        raw.flush()

    if not os.path.exists(src):
        log("NOT MEASURABLE: %s does not exist." % os.path.relpath(src, REPO))
        return 1

    rows = json.load(io.open(src, encoding="utf-8"))["rows"]
    res = [r for r in rows
           if r.get("pmid") and r.get("kind") == "surname" and r.get("token")]

    agree, dis, norec = 0, [], 0
    for r in res:
        a = first_author(r["pmid"])
        if a is None:
            norec += 1
            continue
        if fold(a) == fold(r["token"]):
            agree += 1
        else:
            dis.append({"label": r["label"], "pmid": r["pmid"],
                        "pubmed_first_author": html.unescape(a)})

    null = 0
    for i, r in enumerate(res):
        a = first_author(r["pmid"])
        if a and fold(a) == fold(res[(i + 1) % len(res)]["token"]):
            null += 1

    tot = agree + len(dis)
    log("surname resolutions with a cached PubMed record : %d  (no record: %d)" % (tot, norec))
    if not tot:
        log("NOT MEASURABLE: no resolution could be checked against PubMed.")
        return 1
    log("PubMed's own first author AGREES with the label : %d / %d  (%.1f%%)"
        % (agree, tot, 100.0 * agree / tot))
    log("disagrees                                       : %d" % len(dis))
    log("NULL, agrees with a DIFFERENT label's token     : %d / %d  (%.1f%%)"
        % (null, tot, 100.0 * null / tot))
    log("")
    log("The null is %.1f%% because Cochrane labels repeat surnames within a review, so a"
        % (100.0 * null / tot))
    log("shifted pairing is not a hard test -- which is exactly why it is reported.")
    for x in dis[:8]:
        log("   disagreement: %s" % json.dumps(x, ensure_ascii=False))

    json.dump({"question": "does the reference a label resolved to carry, in PubMed's own "
                           "indexing, the first author the label names",
               "why_independent": "matching used Crossref's author field; PubMed indexes the "
                                  "same paper separately, so agreement is corroboration "
                                  "rather than self-consistency",
               "n": tot, "agree": agree, "disagree": len(dis), "null": null,
               "no_record": norec, "disagreements": dis},
              io.open(OUT, "w", encoding="utf-8"), indent=1)
    log("wrote %s" % os.path.relpath(OUT, REPO))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1] if len(sys.argv) > 1 else None))
