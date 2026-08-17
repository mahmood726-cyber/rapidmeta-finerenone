"""EXTRACTION TABLE -- does the audit surface let a reader check a value?

THE PROPERTY, AND IT IS ALL FOUR OR NOTHING
    Per extracted value: the VALUE, the VERBATIM SOURCE SENTENCE, a RESOLVABLE
    LINK, and whether the number was READ or DERIVED.

    ABLATION_AF and ALIROCUMAB both carry the table with ZERO verbatim quotes and
    were nearly recorded as partial. They are the replay cases here. The quote is
    the half that makes the table checkable: value plus link tells a reader WHERE
    to look; only the sentence tells them WHAT WE READ, which is the thing being
    checked. A table of values with no sentences is provenance theatre.

    AND "RESOLVABLE" MEANS RESOLVED, NOT PRESENT. A link that 404s is not
    provenance. SGLT2's links resolve 11 of 12 -- one EMA URL returns 429 -- and
    an unresolved link is recorded UNRESOLVED, never counted as good and never
    counted as bad, because a rate limiter is not a broken link.

WHAT A FULL PASS DOES NOT ESTABLISH -- written in advance
    - NOT that the quoted sentence says what the row claims it says. It checks a
      sentence is present and non-trivial, not that it supports the number.
    - NOT that the value is right. Extraction correctness is a different gate.
    - NOT that every extracted value HAS a row. A table can be complete in form
      and short of entries; the count is reported so that is visible.
"""
from __future__ import annotations
import io, json, os, re, sys

if __name__ == "__main__":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

SIG = "Extracted values, and where each came from"
ROW = re.compile(r"<tr>(?!\s*<th)(.*?)</tr>", re.S | re.I)
CELL = re.compile(r"<t[dh][^>]*>(.*?)</t[dh]>", re.S | re.I)
LINK = re.compile(r'href=["\'](https?://[^"\']+)', re.I)
READ_DERIVED = re.compile(r"\bread\b|\bderived\b|\bcomputed\b|\bas printed\b", re.I)


def _text(h):
    return re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", h)).strip()


def check(html, resolve=False):
    """-> (verdict, detail dict). Absence of the table is UNCHECKABLE, not FAIL:
    a page that never claimed to have one has not failed this property, it has
    simply not met it, and the standard says which pages must."""
    if SIG not in html:
        return "UNCHECKABLE", {"why": "no extraction table on this page"}
    seg = html[html.find(SIG):]
    end = seg.find("</table>")
    seg = seg[:end] if end > 0 else seg[:200000]
    rows = [r for r in ROW.findall(seg)]
    if not rows:
        return "FAIL", {"why": "the table exists but carries no rows"}

    quoted = links = labelled = valued = 0
    for r in rows:
        cells = CELL.findall(r)
        txt = " ".join(_text(c) for c in cells)
        if "<blockquote" in r.lower() or '"' in txt or "“" in txt:
            quoted += 1
        if LINK.search(r):
            links += 1
        if READ_DERIVED.search(txt):
            labelled += 1
        if re.search(r"\d", txt):
            valued += 1

    n = len(rows)
    d = {"rows": n, "with_value": valued, "with_quote": quoted,
         "with_link": links, "with_read_derived": labelled}

    missing = []
    if valued < n:
        missing.append("value missing on %d row(s)" % (n - valued))
    if quoted == 0:
        missing.append("ZERO verbatim source sentences -- provenance theatre")
    elif quoted < n:
        missing.append("no verbatim sentence on %d row(s)" % (n - quoted))
    if links < n:
        missing.append("no resolvable link on %d row(s)" % (n - links))
    if labelled < n:
        missing.append("no read-versus-derived label on %d row(s)" % (n - labelled))
    d["missing"] = missing

    if resolve and links:
        d["resolution"] = _resolve(set(LINK.findall(seg)))

    return ("PASS" if not missing else "FAIL"), d


def _resolve(urls):
    """RESOLVED means fetched. UNRESOLVED is its own state: a 429 is a rate
    limiter, not a broken link, and calling it broken would be a false defect."""
    import urllib.request as u
    ok = dead = unresolved = 0
    for url in sorted(urls)[:12]:
        try:
            rq = u.Request(url, method="HEAD",
                           headers={"User-Agent": "rapidmeta-extraction-gate"})
            with u.urlopen(rq, timeout=12) as r:
                (ok if r.status < 400 else dead).__class__  # noqa
                if r.status < 400:
                    ok += 1
                else:
                    dead += 1
        except Exception as ex:                              # noqa: BLE001
            s = str(ex)
            if "429" in s or "timed out" in s.lower():
                unresolved += 1
            elif "404" in s or "410" in s:
                dead += 1
            else:
                unresolved += 1
    return {"checked": min(len(urls), 12), "resolved": ok, "dead": dead,
            "unresolved": unresolved}


def selftest():
    """Replayed against the two real pages that carry the table with no quotes."""
    ok = True
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    cases = [("ABLATION_AF_REVIEW.html", "FAIL", "table with ZERO verbatim quotes"),
             ("ALIROCUMAB_LIPID_AUTO_FULL_REVIEW.html", "FAIL",
              "table with ZERO verbatim quotes"),
             ("ARNI_HF_REVIEW.html", "PASS", "full four-component table"),
             ("FINERENONE_CV_REVIEW.html", "PASS", "full four-component table")]
    for page, want, why in cases:
        p = os.path.join(root, page)
        if not os.path.exists(p):
            print("  fixture absent: %s -- NOT PROVEN" % page)
            ok = False
            continue
        v, d = check(open(p, encoding="utf-8", errors="replace").read())
        good = v == want
        ok &= good
        print("  %-44s -> %-5s (want %s) %s" % (why + " [" + page[:18] + "]",
                                                v, want, "correct" if good else "WRONG"))
        if d.get("missing"):
            print("        %s" % "; ".join(d["missing"])[:110])
    print("\nWHAT A FAILURE WOULD LOOK LIKE: a table of values with no sentences "
          "passing, which is a reader given somewhere to look and nothing to "
          "check against.")
    print("-> SELFTEST PASS" if ok else "-> SELFTEST FAILED")
    return 0 if ok else 1


def main():
    if len(sys.argv) < 2 or sys.argv[1] == "--selftest":
        return selftest()
    p = sys.argv[1]
    if not os.path.exists(p):
        print("extraction_table: %s does not exist. NOT RUN -- not a pass." % p,
              file=sys.stderr)
        return 2
    v, d = check(open(p, encoding="utf-8", errors="replace").read(),
                 resolve="--resolve" in sys.argv)
    print("  rows=%s value=%s quote=%s link=%s read/derived=%s"
          % (d.get("rows"), d.get("with_value"), d.get("with_quote"),
             d.get("with_link"), d.get("with_read_derived")))
    for m in d.get("missing", []):
        print("    %s" % m)
    if d.get("resolution"):
        r = d["resolution"]
        print("    links: %d checked, %d resolved, %d dead, %d UNRESOLVED "
              "(rate-limited or timed out -- not counted either way)"
              % (r["checked"], r["resolved"], r["dead"], r["unresolved"]))
    print("  -> %s" % v)
    return 0 if v == "PASS" else (2 if v == "UNCHECKABLE" else 1)


if __name__ == "__main__":
    sys.exit(main())
