# -*- coding: utf-8 -*-
"""Content-completeness acceptance test: does the generated page LOSE anything the original served?

Per Mahmood: make 'loses no content' a MEASURED test, not a judgement -- enumerate the sections/claims of
each page and report the DELTA as a named list. A generator that silently drops a section is the
stale-panel defect inverted: it serves nothing where the original served something, and nothing is harder
to notice than a missing table. Also run it against the ORIGINAL vs the OBJECT, so we learn whether the
generator is behind the original or already ahead of it.
"""
from __future__ import annotations
import io, os, re, json, sys, html

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

_HEADING = re.compile(r"<h[1-3][^>]*>(.*?)</h[1-3]>", re.S | re.I)
_CLAIM_KINDS = {
    "harms": re.compile(r"\bharm|\badverse|\bsafety|infection|hypotension|ketoacidosis|amputation", re.I),
    "grade": re.compile(r"\bGRADE\b|certainty of evidence|certainty:", re.I),
    "rob": re.compile(r"risk of bias|\bRoB[\s-]?2?\b|robins", re.I),
    "absolute_effect": re.compile(r"\bNNT\b|absolute risk|ARR\b|number needed", re.I),
    "screening": re.compile(r"screen|PRISMA|records identified|eligibility", re.I),
    "funding": re.compile(r"\bfund|sponsor|Boehringer|AstraZeneca|Novartis|Regeneron|Sanofi", re.I),
    "heterogeneity": re.compile(r"heterogeneit|I.{0,3}squared|tau.?squared|\bI2\b", re.I),
    "forest": re.compile(r"<svg", re.I),
}


def sections(page_text):
    """A stable, comparable set of content labels for one page."""
    labs = set()
    for m in _HEADING.finditer(page_text):
        t = html.unescape(re.sub(r"<[^>]+>", " ", m.group(1)))
        t = re.sub(r"\s+", " ", t).strip().lower()
        if t:
            labs.add("h:" + t[:50])
    for kind, rx in _CLAIM_KINDS.items():
        if rx.search(page_text):
            labs.add("claim:" + kind)
    n_tables = len(re.findall(r"<table", page_text, re.I))
    if n_tables:
        labs.add("tables:%d" % n_tables)
    return labs


def delta(original_html, generated_html):
    o, g = sections(original_html), sections(generated_html)
    return {
        "missing_in_generated": sorted(o - g),   # the original served it, the generator dropped it
        "extra_in_generated": sorted(g - o),      # the generator serves it, the original did not
        "shared": len(o & g),
    }


# What the OBJECT holds that a page SHOULD therefore carry (so we can judge original vs object too).
def object_claims(obj):
    held = set()
    s = json.dumps(obj).lower()
    for kind, rx in _CLAIM_KINDS.items():
        if kind == "forest":
            continue
        if rx.search(s):
            held.add("claim:" + kind)
    # harms specifically: does the object hold harms DATA?
    held.add("_object_has_harms_data:%s" % bool(re.search(r'"harms"\s*:\s*\[[^\]]', s) or "genital myco" in s or "hyperkal" in s))
    return held


def _selftest():
    ok, rows = True, []
    def chk(n, c):
        nonlocal ok; ok &= bool(c); rows.append((n, "OK" if c else "*** FAIL ***"))
    orig = "<h2>Harms</h2><p>genital infections</p><h2>GRADE</h2><table></table>"
    gen = "<h2>Primary result</h2><svg></svg>"
    d = delta(orig, gen)
    chk("delta names the dropped harms section", "claim:harms" in d["missing_in_generated"])
    chk("delta names the dropped GRADE", "claim:grade" in d["missing_in_generated"])
    chk("delta credits the generator's forest as extra", "claim:forest" in d["extra_in_generated"])
    chk("delta is a NAMED list, not a boolean", isinstance(d["missing_in_generated"], list))
    return ok, rows


def run(review_id, original_path, generated_path):
    orig = io.open(os.path.join(ROOT, original_path), encoding="utf-8", errors="replace").read()
    gen = io.open(generated_path if os.path.isabs(generated_path) else os.path.join(ROOT, generated_path),
                  encoding="utf-8", errors="replace").read()
    d = delta(orig, gen)
    return d


if __name__ == "__main__":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    if "--selftest" in sys.argv[1:] or len(sys.argv) == 1:
        ok, rows = _selftest()
        print("content_completeness selftest")
        for n, v in rows:
            print("  %-52s %s" % (n, v))
        print("\n%s" % ("ALL PASS" if ok else "FAILURES"))
        raise SystemExit(0 if ok else 1)
    # usage: content_completeness.py <original.html> <generated.html>
    d = run("", sys.argv[1], sys.argv[2])
    print("CONTENT DELTA (generated vs original)")
    print("  shared labels: %d" % d["shared"])
    print("  MISSING in generated (%d):" % len(d["missing_in_generated"]))
    for m in d["missing_in_generated"]:
        print("     - %s" % m)
    print("  EXTRA in generated (%d):" % len(d["extra_in_generated"]))
    for m in d["extra_in_generated"]:
        print("     + %s" % m)
    raise SystemExit(0)
