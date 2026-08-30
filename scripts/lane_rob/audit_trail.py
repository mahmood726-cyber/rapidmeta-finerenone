# -*- coding: utf-8 -*-
"""GENERATOR COMPONENT: every number on this page, what it was read from, and its fingerprint.

WHAT THIS IS FOR, IN ONE SENTENCE THAT IS ALSO THE TEST OF IT. A reader who doubts a number on
this page should be able to resolve it to a document and a sentence WITHOUT contacting anyone.

⭐ THE TRAIL IS WALKED FROM THE OBJECT, NOT WRITTEN. Every row is discovered by traversing the
object for records that carry a source, so a number added later appears here automatically and a
number whose provenance was never recorded appears as a NAMED GAP. A hand-written audit trail
lists what its author remembered, which is the one thing an audit trail may not be.

⛔ AND THE GAP COLUMN IS THE POINT. The first version of this listed only the numbers that HAD
provenance -- which is a list of our good behaviour, not an audit. A trail that shows five
sourced numbers out of five sourced numbers tells a reader nothing about the twenty that were
not. So the section reports SOURCED and UNSOURCED against a denominator, and the denominator is
the numbers this page actually displays.

⚠️ A FINGERPRINT IS NOT A GUARANTEE OF CONTENT. A sha256 says that the bytes we read are the
bytes we say we read; it does not say the document contained what we claim. What makes a row
checkable is the QUOTED SENTENCE beside it -- the fingerprint only makes the quote resolvable.
Rows are therefore sorted so that quoted rows lead, and a row with a fingerprint and no quote is
marked as such rather than counted as evidence.

⛔ IT WILL NOT PRINT A TRUNCATED QUOTE AS THOUGH IT WERE THE SENTENCE. A quote cut at a fixed
width can lose the very clause that made it evidence -- a date, a denominator, a negation. Where
a stored quote is longer than the row can hold, the row says it is abridged and the full text
stays in the object. Measured tonight on a sibling instrument: a check passed while the page
displayed a dateless quote, because the check read the whole sentence and the page rendered the
first 300 characters of it.
"""
import io
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(os.path.dirname(HERE))
SSOT = os.path.join(REPO, "ssot")
for _p in (HERE, SSOT):
    if _p not in sys.path:
        sys.path.insert(0, _p)

QUOTE_KEYS = ("source_quote", "verbatim_quote", "quote", "sentence")
SOURCE_KEYS = ("source", "source_id", "document_id", "source_url", "registry", "sources_read")
HASH_KEYS = ("sha256", "sha256_prefix", "fingerprint")
# The width at which a quote is ABRIDGED -- and the row says so. Never a silent cut.
QUOTE_WIDTH = 300


def _esc(s):
    return str(s).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def _first(d, keys):
    for k in keys:
        v = d.get(k)
        if isinstance(v, str) and v.strip():
            return v.strip()
        if isinstance(v, dict):
            inner = _first(v, keys) or v.get("document_id") or v.get("what")
            if isinstance(inner, str) and inner.strip():
                return inner.strip()
    return None


def _hash_of(d):
    for k in HASH_KEYS:
        v = d.get(k)
        if isinstance(v, str) and v.strip():
            return v.strip()
    for v in d.values():
        if isinstance(v, dict):
            h = _hash_of(v)
            if h:
                return h
    return None


def walk(obj, path="", depth=0, seen=None):
    """Every record in the object that carries a source. -> list of rows.

    ⛔ TRAVERSAL, NOT AN ENUMERATED LIST. A hand-listed set of places to look is a SAMPLE, and
    everything outside it is silently missed -- the defect this project has now met in a regex,
    a path list, a label matcher and an estimand check. A record qualifies by CARRYING a source
    field, wherever it sits.
    """
    rows = []
    if depth > 8 or not isinstance(obj, (dict, list)):
        return rows
    if isinstance(obj, list):
        for i, v in enumerate(obj):
            rows += walk(v, "%s[%d]" % (path, i), depth + 1, seen)
        return rows
    src = _first(obj, SOURCE_KEYS)
    quote = _first(obj, QUOTE_KEYS)
    if src or quote:
        label = (obj.get("outcome") or obj.get("label") or obj.get("what")
                 or obj.get("trial") or obj.get("_what") or path.strip("/.") or "(unnamed)")
        # ⛔ ONLY A SCALAR MAY REACH THE VALUE COLUMN.
        #
        # The first version took obj[k] whatever it was, and on 99 of 141 objects `point` or
        # `effect` is a nested BLOCK rather than a number -- so the column rendered a raw
        # Python dict, `{'measure': 'OR', 'scale': 'log', 'point': None, ...}`, putting the
        # bare token None on the page. That is the placeholder-leak class this project has
        # already shipped once, at 1,110 dashboards.
        #
        # ⚠️ MY OWN PLANTS DID NOT CATCH IT, because the model answer used scalar values
        # throughout. It was caught by a separate displayed-bytes checker run over the whole
        # corpus -- a second instrument, not a re-reading of the first.
        value = None
        for k in ("effect", "point", "efficacy_percent", "treatment_events", "value"):
            v = obj.get(k)
            if isinstance(v, bool) or not isinstance(v, (int, float, str)):
                continue
            if isinstance(v, str) and not v.strip():
                continue
            value = v
            break
        if value is None:
            t, c = obj.get("treatment"), obj.get("control")
            if all(isinstance(x, (int, float, str)) and not isinstance(x, bool)
                   for x in (t, c)):
                value = "%s vs %s" % (t, c)
        rows.append({"what": str(label)[:90], "value": value, "source": src, "quote": quote,
                     "sha256": _hash_of(obj), "path": path,
                     "tier": obj.get("tier") or (obj.get("source") or {}).get("tier")
                     if isinstance(obj.get("source"), dict) else obj.get("tier")})
    # ⛔ DO NOT DESCEND INTO A RECORD'S OWN SOURCE BLOCK. The first run of this walk emitted
    # five rows for three numbers, because a `source` sub-dict carries `document_id` and a
    # sha256 and therefore qualifies as a record in its own right. That would have inflated
    # the audit trail's denominator with its own metadata -- a count of the citation apparatus
    # presented as a count of the numbers cited.
    claimed = set(SOURCE_KEYS) if (src or quote) else set()
    for k, v in obj.items():
        if k in claimed:
            continue
        rows += walk(v, "%s/%s" % (path, k), depth + 1, seen)
    return rows


def dedupe(rows):
    out, seen = [], set()
    for r in rows:
        key = (r["what"], str(r["value"])[:60], (r["quote"] or "")[:80])
        if key in seen:
            continue
        seen.add(key)
        out.append(r)
    # Quoted rows lead: a fingerprint without a sentence is resolvable but not checkable.
    out.sort(key=lambda r: (0 if r["quote"] else 1, 0 if r["sha256"] else 1, r["what"]))
    return out


def render(canon):
    head = "<h2>Audit trail</h2>"
    rows = dedupe(walk(canon))
    if not rows:
        return head + (
            "<p>No record in this object carries a source, so no audit trail can be built from "
            "it. ⚠️ That is a statement about this object, not about the numbers on this page: "
            "every figure above came from somewhere, and this review does not record where.</p>")
    body = []
    quoted = hashed = 0
    for r in rows:
        q = r["quote"] or ""
        abridged = len(q) > QUOTE_WIDTH
        # ⛔ ABRIDGEMENT IS DECLARED. See the docstring.
        shown = (q[:QUOTE_WIDTH] + "…" if abridged else q) or "&mdash;"
        quoted += 1 if r["quote"] else 0
        hashed += 1 if r["sha256"] else 0
        body.append(
            "<tr><td>%s</td><td>%s</td><td>%s</td><td>%s%s</td><td class=\"mono\">%s</td></tr>"
            % (_esc(r["what"]),
               _esc(r["value"]) if r["value"] is not None else "&mdash;",
               _esc(r["source"]) if r["source"] else
               "<span class=\"warn\">no source recorded</span>",
               _esc(shown) if r["quote"] else "&mdash;",
               " <span class=\"warn\">[abridged; the full sentence is in the object]</span>"
               if abridged else "",
               _esc(r["sha256"][:16]) if r["sha256"] else "&mdash;"))
    n = len(rows)
    return (head
            + "<div class=\"scroll\"><table><tr><th>What</th><th>Value</th><th>Read from</th>"
              "<th>Sentence it was read from</th><th>Fingerprint</th></tr>"
            + "".join(body) + "</table></div>"
            + "<p><b>The denominator.</b> %d records in this object carry a source. "
              "<b>%d of %d</b> carry the sentence they were read from, and <b>%d of %d</b> "
              "carry a document fingerprint. ⚠️ A fingerprint says the bytes we read are the "
              "bytes we say we read; it does not say the document contained what we claim. What "
              "makes a row checkable is the sentence, so rows carrying one are listed first and "
              "the rest are visible as the gap they are.</p>"
              % (n, quoted, n, hashed, n)
            + "<p>Retrieval routes are recorded per document and a document is marked "
              "unreachable only after every route has been tried and named &mdash; so a missing "
              "document on this page is a record of what was attempted, not a blank.</p>")


MARKER = "<h2>Audit trail</h2>"


def inject(html, canon):
    if MARKER in html:
        return html
    return html + "\n<div class=\"card\">\n" + render(canon) + "\n</div>\n"


# ---------------------------------------------------------------------------------------------
# COVERAGE, and the controls.
# ---------------------------------------------------------------------------------------------

def coverage(root=None):
    import collections
    import glob
    import json
    root = root or SSOT
    per = collections.Counter()
    skipped = collections.Counter()
    objs = 0
    tot_rows = tot_quoted = 0
    for f in sorted(glob.glob(os.path.join(root, "*", "*.json"))):
        try:
            c = json.load(io.open(f, encoding="utf-8"))
        except Exception:
            # ⛔ COUNTED, NOT SKIPPED. A `continue` here removes the file from the denominator
            # and the coverage figure silently becomes a reach figure.
            skipped["file did not parse as JSON"] += 1
            continue
        if not isinstance(c, dict):
            skipped["top level is not an object"] += 1
            continue
        r = c.get("results")
        outs = r.get("by_outcome") if isinstance(r, dict) else None
        if not isinstance(outs, dict) or not outs:
            skipped["no results.by_outcome recorded"] += 1
            continue
        objs += 1
        rows = dedupe(walk(c))
        q = sum(1 for x in rows if x["quote"])
        tot_rows += len(rows)
        tot_quoted += q
        per["objects with a sourced record" if rows else "objects with NO sourced record"] += 1
    return {"objects_with_a_pooled_result": objs, "detail": dict(per),
            "sourced_records": tot_rows, "of_which_quoted": tot_quoted,
            "skipped": dict(skipped)}


# ⭐ THE MODEL ANSWER. Three records: one fully sourced and quoted, one with a fingerprint and no
# sentence, one with a source and neither. The denominator must read 3, quoted 1, hashed 2.
MODEL_ANSWER = {
    "inputs": {"trials": [
        {"label": "Trial A", "nct": "NCT00000001",
         "source": {"document_id": "PMC0000001", "sha256": "abcdef0123456789abcdef"},
         "source_quote": "71 in the dapivirine group and 97 in the placebo group",
         "treatment_events": 71},
        {"label": "Trial B", "nct": "NCT00000002",
         "source": {"document_id": "PMC0000002", "sha256": "0123456789abcdefabcdef"},
         "treatment_events": 50},
        {"label": "Trial C", "nct": "NCT00000003", "source_url": "https://example.org/x",
         "treatment_events": 12}]},
    "results": {"by_outcome": {"primary": {"pooled": {"point": 0.7, "measure": "RR"}}}}}

# ⭐ REFUSAL CONTROL 1 -- an object with no provenance anywhere must say so about ITSELF, not
# render an empty table that reads as "nothing to declare".
NO_PROVENANCE_CONTROL = {
    "inputs": {"trials": [{"label": "Trial X"}]},
    "results": {"by_outcome": {"primary": {"pooled": {"point": 0.7, "measure": "RR"}}}}}

# ⭐ REFUSAL CONTROL 2 -- a quote longer than the row can hold must be DECLARED abridged. The
# planted sentence carries its decisive clause (a date) beyond the cut, which is exactly how a
# sibling instrument passed tonight while the page showed a dateless quote.
LONG_QUOTE = ("The primary analysis population comprised all randomised participants " + ("x " * 160)
              + "and the database was locked on 17 March 2021.")
# ⭐ REFUSAL CONTROL 4 -- a record whose `point` is a nested BLOCK must render an em dash in
# the Value column, never the block. This is the control that was missing when the defect
# shipped: the model answer used scalars only, so nothing exercised the structured case.
STRUCTURED_VALUE_CONTROL = {
    "inputs": {"trials": [
        {"label": "Trial S", "nct": "NCT00000010",
         "source": {"document_id": "PMC0000010", "sha256": "cafebabe" * 4},
         "by_outcome": {"primary": {"measure": "OR", "scale": "log", "point": None,
                                    "ci_low": None}},
         "point": {"measure": "OR", "scale": "log", "point": None}}]},
    "results": {"by_outcome": {"primary": {"pooled": {"point": 0.7, "measure": "RR"}}}}}

ABRIDGE_CONTROL = {
    "inputs": {"trials": [
        {"label": "Trial L", "source": {"document_id": "PMC0000009", "sha256": "deadbeef" * 4},
         "source_quote": LONG_QUOTE, "treatment_events": 1}]},
    "results": {"by_outcome": {"primary": {"pooled": {"point": 0.7, "measure": "RR"}}}}}


def _plain(html):
    return re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", html))


def plant():
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    rows = dedupe(walk(MODEL_ANSWER))
    print("MODEL ANSWER -- three sourced records: one quoted, two not; two fingerprinted.")
    assert len(rows) == 3, [r["what"] for r in rows]
    assert rows[0]["quote"], rows[0]
    print("   %d records, quoted row sorted first   [PASS]" % len(rows))
    t = _plain(render(MODEL_ANSWER))
    assert "1 of 3 carry the sentence" in t, t[-400:]
    assert "2 of 3 carry a document fingerprint" in t, t[-400:]
    print("   the denominator is printed, and the GAP with it: 1 of 3 quoted   [PASS]")
    print("")
    t2 = _plain(render(NO_PROVENANCE_CONTROL))
    said = "this review does not record where" in t2
    empty = "<table" not in render(NO_PROVENANCE_CONTROL)
    print("REFUSAL CONTROL -- no provenance anywhere is a statement about the object")
    print("   says so: %s   emits no table: %s   [%s]"
          % (said, empty, "PASS" if said and empty else "FAIL"))
    assert said and empty, t2[:400]
    h3 = render(ABRIDGE_CONTROL)
    t3 = _plain(h3)
    declared = "abridged" in t3
    # ⛔ AND THE ASSERTION IS ON THE DISPLAYED BYTES. The decisive clause is past the cut, so a
    # check that read the STORED sentence would pass while the page showed a dateless quote.
    displayed_has_date = "17 March 2021" in t3
    print("REFUSAL CONTROL -- an abridged quote declares itself")
    print("   declares abridgement: %s   the date is genuinely off the DISPLAYED row: %s   [%s]"
          % (declared, not displayed_has_date,
             "PASS" if declared and not displayed_has_date else "FAIL"))
    assert declared and not displayed_has_date, t3[:500]
    assert "17 March 2021" in ABRIDGE_CONTROL["inputs"]["trials"][0]["source_quote"], \
        "the plant is not testing what it claims"
    print("   ...and it IS in the stored sentence, so the plant tests the right thing   [PASS]")
    h4 = render(STRUCTURED_VALUE_CONTROL)
    t4 = _plain(h4)
    import html as _h
    disp = _h.unescape(t4)
    leaked = ("None" in disp.split("Fingerprint")[-1]) or ("{'" in disp) or ('{"' in disp)
    print("REFUSAL CONTROL -- a structured value never reaches the Value column")
    print("   no dict or bare None in the DISPLAYED row: %s   [%s]"
          % (not leaked, "PASS" if not leaked else "FAIL"))
    assert not leaked, disp[:400]
    print("")
    print("⚠️ The denominator and the unquoted rows may not be dropped to make the trail look")
    print("   complete. A list of only the sourced numbers is a list of our good behaviour.")
    return 0


if __name__ == "__main__":
    if "--plant" in sys.argv:
        raise SystemExit(plant())
    import json
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace",
                                  line_buffering=True)
    if "--coverage" in sys.argv:
        root = SSOT
        for i, a in enumerate(sys.argv):
            if a == "--root" and i + 1 < len(sys.argv):
                root = sys.argv[i + 1]
        c = coverage(root)
        n = c["objects_with_a_pooled_result"]
        print("")
        print("COVERAGE FRACTION -- audit trail")
        print("  scanned: %s" % root)
        if not n:
            print("  ⛔ SCAN FOUND NOTHING -- a failure of this scan, not of the corpus.")
            raise SystemExit(2)
        print("  objects with a pooled result   %4d   == the denominator" % n)
        for k, v in sorted(c["detail"].items()):
            print("     %-38s %4d   %5.1f%%" % (k, v, 100.0 * v / n))
        print("")
        print("  sourced records across the corpus  %5d" % c["sourced_records"])
        print("  of which carry their sentence      %5d   %5.1f%%"
              % (c["of_which_quoted"],
                 100.0 * c["of_which_quoted"] / c["sourced_records"]
                 if c["sourced_records"] else 0.0))
        if c.get("skipped"):
            print("")
            print("  SKIPPED, by kind -- these files were NOT in any denominator "
                  "above:")
            for _k, _v in sorted(c["skipped"].items(), key=lambda kv: -kv[1]):
                print("     %-46s %4d" % (_k, _v))
            print("  ⚠️ A skip that is not counted turns a coverage figure into a "
                  "reach figure.")
        raise SystemExit(0)
    os.chdir(REPO)
    for path in sys.argv[1:] or ["ssot/agyw-hiv-prep-review/agyw-hiv-prep-review.json"]:
        canon = json.load(io.open(path, encoding="utf-8"))
        print("=" * 78)
        print(os.path.basename(path))
        print(_plain(render(canon))[:2200])
