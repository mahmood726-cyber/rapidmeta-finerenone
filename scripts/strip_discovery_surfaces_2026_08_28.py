"""Remove retired pages from every DISCOVERY surface, in the same change as the tombstones.

WHY THE SAME CHANGE. A tombstone reachable from an index that still advertises a review is
worse than either alone: the reader is invited to a page that then tells them it is retired.

WHICH SURFACES. Enumerated by SEARCHING every tracked text file, never by recalling which
surfaces exist. That search found 2,040 files mentioning these pages and eight that a reader
can actually navigate -- four of which nobody would have listed: auto-gallery.html,
EVIDENCE_GAPS.html, index_indicators.json and portfolio_pools.html.

  And no two surfaces agreed on the same 763 pages: index.html 642, sitemap.xml 616,
  portfolio_pools 631, audit_table 737, portfolio_index.json 752, index_indicators 392,
  auto-gallery 144, EVIDENCE_GAPS 129. Removing from index.html alone would have left 616 in
  the sitemap and 737 in the audit table.

DISCOVERY IS NOT THE SAME AS MENTION. The other ~2,030 files are evidence archives, lane
prompts, scripts and findings. A reader cannot navigate from them, and rewriting an evidence
archive to hide a retirement would be falsifying the record. They are reported, not edited.

HOW EACH SURFACE IS EDITED. Line- or entry-wise, never by a blanket regex over the file: an
HTML row is dropped whole, a sitemap <url> block is dropped whole, a JSON key or array member
is dropped by parsing rather than by text substitution. A surface this cannot parse is
REPORTED UNTOUCHED rather than edited on a guess.
"""
import io
import json
import os
import re
import sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(REPO, "outputs", "surface_strip_2026_08_28.json")

HTML_SURFACES = ["index.html", "audit_table.html", "portfolio_pools.html",
                 "auto-gallery.html", "EVIDENCE_GAPS.html"]
JSON_SURFACES = ["outputs/portfolio_index.json", "index_indicators.json"]
XML_SURFACES = ["sitemap.xml"]


def strip_html(path, targets, log):
    body = io.open(path, encoding="utf-8", errors="replace").read()
    # a row/card is the unit; drop any <tr>...</tr> or <li>...</li> or <div class=card>
    # containing a target href. Whole-element, never a partial line.
    removed = 0
    for pat in (r"<tr\b[^>]*>.*?</tr>", r"<li\b[^>]*>.*?</li>",
                r"<article\b[^>]*>.*?</article>"):
        def drop(m):
            nonlocal removed
            seg = m.group(0)
            if any(t in seg for t in targets):
                removed += 1
                return ""
            return seg
        body = re.sub(pat, drop, body, flags=re.S | re.I)
    # any remaining bare anchors
    def drop_a(m):
        nonlocal removed
        if any(t in m.group(0) for t in targets):
            removed += 1
            return ""
        return m.group(0)
    body = re.sub(r"<a\b[^>]*>.*?</a>", drop_a, body, flags=re.S | re.I)
    io.open(path, "w", encoding="utf-8").write(body)
    log.append((os.path.relpath(path, REPO), "html", removed))
    return removed


def strip_json(path, targets, log):
    try:
        d = json.load(io.open(path, encoding="utf-8"))
    except (ValueError, OSError):
        log.append((os.path.relpath(path, REPO), "UNPARSEABLE -- left untouched", 0))
        return 0
    removed = [0]

    def clean(x):
        if isinstance(x, dict):
            out = {}
            for k, v in x.items():
                if isinstance(k, str) and k in targets:
                    removed[0] += 1
                    continue
                if isinstance(v, str) and v in targets:
                    removed[0] += 1
                    continue
                out[k] = clean(v)
            return out
        if isinstance(x, list):
            out = []
            for v in x:
                if isinstance(v, str) and v in targets:
                    removed[0] += 1
                    continue
                if isinstance(v, dict) and any(
                        isinstance(vv, str) and vv in targets for vv in v.values()):
                    removed[0] += 1
                    continue
                out.append(clean(v))
            return out
        return x

    d2 = clean(d)
    io.open(path, "w", encoding="utf-8").write(json.dumps(d2, indent=1, ensure_ascii=False))
    log.append((os.path.relpath(path, REPO), "json", removed[0]))
    return removed[0]


def strip_xml(path, targets, log):
    body = io.open(path, encoding="utf-8", errors="replace").read()
    removed = 0

    def drop(m):
        nonlocal removed
        if any(t in m.group(0) for t in targets):
            removed += 1
            return ""
        return m.group(0)
    body = re.sub(r"<url>.*?</url>", drop, body, flags=re.S | re.I)
    io.open(path, "w", encoding="utf-8").write(body)
    log.append((os.path.relpath(path, REPO), "xml", removed))
    return removed


def main():
    targets = set(l.strip() for l in io.open(sys.argv[1], encoding="utf-8") if l.strip())
    raw = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace",
                           write_through=True)

    def say(s):
        raw.write(s + chr(10))
        raw.flush()

    say("targets: %d pages" % len(targets))
    log, total = [], 0
    for rel in HTML_SURFACES:
        p = os.path.join(REPO, rel)
        if os.path.exists(p):
            total += strip_html(p, targets, log)
    for rel in JSON_SURFACES:
        p = os.path.join(REPO, rel)
        if os.path.exists(p):
            total += strip_json(p, targets, log)
    for rel in XML_SURFACES:
        p = os.path.join(REPO, rel)
        if os.path.exists(p):
            total += strip_xml(p, targets, log)

    say("")
    say("%-40s %-12s %s" % ("surface", "kind", "entries removed"))
    for rel, kind, n in log:
        say("%-40s %-12s %6d" % (rel[:40], kind[:12], n))
    say("")
    say("total entries removed: %d" % total)
    json.dump({"targets": len(targets), "surfaces": [
        {"surface": r, "kind": k, "removed": n} for r, k, n in log],
        "total_removed": total,
        "not_edited": "evidence archives, lane prompts, scripts and findings mention these "
                      "pages but are not navigable; rewriting an archive to hide a "
                      "retirement would falsify the record"},
        io.open(OUT, "w", encoding="utf-8"), indent=1)
    say("wrote %s" % os.path.relpath(OUT, REPO))
    return 0


if __name__ == "__main__":
    sys.exit(main())
