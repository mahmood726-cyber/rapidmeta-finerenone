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


# ---------------------------------------------------------------------------------------------
# TABS ARE THE DELIVERABLE. The tabbed shell is the format reviewers and Mahmood assess, so a
# generated page with fewer POPULATED tabs than the page it replaces is a different artefact, not a
# leaner one -- and the semantic-category delta above is BLIND to it (it enumerates claims, not
# structure, and it reported 8/8 on a page that had lost all ten tabs). This counts tabs WITH
# CONTENT -- our own standing rule, "COUNT TABS WITH CONTENT, not tabs that exist".
_PANEL_MIN_VISIBLE = 60   # a panel with less visible text than this is an empty stub, not a tab

def populated_tabs(page_html):
    """Return a list of (tab_id, visible_chars) for every panel that actually carries content."""
    opens = [m.start() for m in re.finditer(r'class="panel"', page_html)]
    ids = re.findall(r'class="panel"[^>]*id="([^"]+)"|id="([^"]+)"[^>]*class="panel"', page_html)
    out = []
    for i, s in enumerate(opens):
        e = opens[i + 1] if i + 1 < len(opens) else len(page_html)
        seg = page_html[s:e]
        visible = re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", seg)).strip()
        has_structure = ("<table" in seg) or bool(re.search(r"<h[1-3]", seg)) or ("<svg" in seg)
        if len(visible) >= _PANEL_MIN_VISIBLE or has_structure:
            tid = ""
            if i < len(ids):
                tid = ids[i][0] or ids[i][1]
            out.append((tid or ("panel%d" % (i + 1)), len(visible)))
    return out


def tab_delta(original_html, generated_html):
    """The tab acceptance criterion: the generated page must not have FEWER populated tabs than the
    original. Returns the counts, the lost tab ids, and a boolean `ok` (False = deliverable regressed)."""
    o_tabs = populated_tabs(original_html)
    g_tabs = populated_tabs(generated_html)
    o_ids = [t for t, _ in o_tabs]
    g_ids = [t for t, _ in g_tabs]
    lost = [t for t in o_ids if t not in g_ids]
    return {
        "original_populated_tabs": len(o_tabs),
        "generated_populated_tabs": len(g_tabs),
        "lost_tab_ids": lost,
        "ok": len(g_tabs) >= len(o_tabs),   # fewer populated tabs than the page it replaces = FAIL
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
    # TAB CRITERION: an original with ten populated tabs vs a generated page with none MUST fail.
    orig_tabbed = "".join('<section class="panel" id="pn-%d"><h2>Tab %d</h2><p>%s</p></section>'
                          % (i, i, "content " * 20) for i in range(10))
    gen_flat = "<h2>Primary result</h2><svg></svg><p>no tabs here</p>"
    td = tab_delta(orig_tabbed, gen_flat)
    chk("tab_delta counts 10 populated tabs in the original", td["original_populated_tabs"] == 10)
    chk("tab_delta counts 0 populated tabs in the flat generated page", td["generated_populated_tabs"] == 0)
    chk("tab_delta FAILS when the generated page loses tabs (ok is False)", td["ok"] is False)
    chk("tab_delta names the lost tabs", len(td["lost_tab_ids"]) == 10)
    # a page that keeps its tabs must PASS the criterion
    td_ok = tab_delta(orig_tabbed, orig_tabbed)
    chk("tab_delta passes when tabs are preserved", td_ok["ok"] is True)
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
    import os
    orig = io.open(os.path.join(ROOT, sys.argv[1]), encoding="utf-8", errors="replace").read()
    gen_path = sys.argv[2] if os.path.isabs(sys.argv[2]) else os.path.join(ROOT, sys.argv[2])
    gen = io.open(gen_path, encoding="utf-8", errors="replace").read()
    d = delta(orig, gen)
    print("CONTENT DELTA (generated vs original)")
    print("  shared labels: %d" % d["shared"])
    print("  MISSING in generated (%d):" % len(d["missing_in_generated"]))
    for m in d["missing_in_generated"]:
        print("     - %s" % m)
    print("  EXTRA in generated (%d):" % len(d["extra_in_generated"]))
    for m in d["extra_in_generated"]:
        print("     + %s" % m)
    # TAB CRITERION -- first-class, and it can FAIL the whole test.
    td = tab_delta(orig, gen)
    print("\nTAB CRITERION (the tabbed shell is the deliverable):")
    print("  populated tabs: original %d -> generated %d"
          % (td["original_populated_tabs"], td["generated_populated_tabs"]))
    if not td["ok"]:
        print("  *** FAIL: the generated page has FEWER populated tabs than the page it replaces.")
        print("  lost tabs (%d): %s" % (len(td["lost_tab_ids"]), ", ".join(td["lost_tab_ids"])))
        print("  This page must NOT replace the original: it drops the navigational structure reviewers assess.")
    else:
        print("  OK: no populated tab was lost.")
    raise SystemExit(0 if td["ok"] else 1)
