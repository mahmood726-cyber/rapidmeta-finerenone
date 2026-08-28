"""Reduce every discovery surface to the KEEP set. Nothing is deleted; nothing stops serving.

WHAT CHANGES AND WHAT DOES NOT. Every page keeps its URL and keeps serving the bytes it served
before. Only what the INDEXES advertise changes. A reader stops wading through withdrawn and
result-less topics; a reader holding a link, a citation or a bookmark still lands on the page.

DRIVEN BY THE KEEP LIST, NEVER BY A REMOVE LIST. An absence-based selector came within one
commit of retiring 758 pages that hold results. A whitelist cannot make that error: its
failure mode is leaving a dead entry listed, which costs a reader ten seconds.

*** THE INVARIANT IS A SUBSET RELATION, NOT AN EQUAL COUNT, AND THAT IS A DEVIATION. ***

The brief said every surface must end at 28. Measurement says two of them must not:

    NMA_INDEX.html      "22 Class-Level Network Meta-Analyses" -- a DIFFERENT population.
                        It holds 0 of the 28. Writing 28 pairwise reviews into an index of
                        network meta-analyses would be a fabrication, not a fix.
    auto-gallery.html   "Automated (unvalidated) gallery" -- explicitly the UNVALIDATED set.
                        Listing validated reviews there would misdescribe them. (It holds 2
                        of the 28 today, which is its own small finding.)

So what is enforced instead, on every surface without exception:

    NO surface may carry a review entry outside KEEP        <- this is the reader's problem
    index.html and sitemap.xml must carry ALL 28            <- these are the entry points

That is the property Mahmood actually asked for -- "stop routing people through it" -- and it
is checkable. Forcing equal counts would have required inventing entries.

ENTRY-WISE, NEVER A BLANKET REGEX. Each surface has a unit: a card anchor, a <tr>, an <li>,
a <url> block, a JSON key or array member. A surface this cannot parse is REPORTED UNTOUCHED
rather than edited on a guess.

ADDING IS RESTRICTED TO TWO SURFACES ON PURPOSE. index.html and sitemap.xml get missing KEEP
entries written in, because their schema is a link and a title -- facts already established.
audit_table, portfolio_pools and the dashboards carry per-page AUDIT fields; writing rows
there would mean inventing values, so they are stripped to a KEEP subset and reported as
subsets rather than filled in.
"""
import io
import json
import os
import re
import sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(REPO, "outputs", "index_apply_2026_08_28.json")

SITE = "https://mahmood726-cyber.github.io/rapidmeta-finerenone/"
BANNER_ID = "ready-index-note"
BANNER = (
    '<div id="' + BANNER_ID + '" style="margin:0 0 1.2rem;padding:.85rem 1.1rem;'
    'border-left:4px solid #1d4ed8;background:#EFF6FF;font-size:.9rem;line-height:1.55">'
    '<strong>These %d reviews each carry a pooled result with the per-trial evidence behind '
    'it.</strong> Other topics in this project are still published at their own addresses '
    'and nothing has been deleted &mdash; they are not listed here because their estimate '
    'was withdrawn, was never poolable, or is unfinished, and routing readers through them '
    'made the finished reviews hard to find.</div>')

# index.html's own listing unit, taken from the page rather than assumed
CARD = ('<a href="%(page)s" class="card ready"><span class="name">%(title)s</span>'
        '<span class="pub">%(sub)s</span></a>')


def read_text(fp):
    """newline="" so CRLF survives the round trip. Reading with universal newlines and
    writing back rewrote four dashboards entirely -- 297 lines removed, 297 added, content
    byte-identical -- which buries a real change in an unreviewable diff."""
    return io.open(fp, encoding="utf-8", errors="replace", newline="").read()


def write_if_changed(fp, body, original):
    """A file this did not change must not be touched at all."""
    if body == original:
        return False
    io.open(fp, "w", encoding="utf-8", newline="").write(body)
    return True


def review_population(surfaces):
    names = set(s["surface"] for s in surfaces)
    return set(p for p in os.listdir(REPO)
               if p.endswith(".html") and os.path.isfile(os.path.join(REPO, p))
               and p not in names)


def html_entries(body, reviews):
    hit = set(re.findall(r"href\s*=\s*[\"']\.?/?([A-Za-z0-9_.\-]+\.html)[\"'#?]", body))
    return hit & reviews


def json_entries(x, reviews, acc=None):
    acc = set() if acc is None else acc
    if isinstance(x, dict):
        for k, v in x.items():
            if isinstance(k, str) and k in reviews:
                acc.add(k)
            json_entries(v, reviews, acc)
    elif isinstance(x, list):
        for v in x:
            json_entries(v, reviews, acc)
    elif isinstance(x, str) and x in reviews:
        acc.add(x)
    return acc


def strip_html(rel, keep, reviews, log):
    fp = os.path.join(REPO, rel)
    original = read_text(fp)
    body = original
    before = len(html_entries(body, reviews))
    removed = [0]

    def refs_dead(seg):
        hit = set(re.findall(r"href\s*=\s*[\"']\.?/?([A-Za-z0-9_.\-]+\.html)[\"'#?]", seg))
        hit &= reviews
        return bool(hit) and not (hit & keep)

    # rows/list-items/articles FIRST so a row containing a dead anchor is dropped whole,
    # rather than hollowed out into an empty row with a dangling label.
    for pat in (r"<tr\b[^>]*>.*?</tr>", r"<li\b[^>]*>.*?</li>",
                r"<article\b[^>]*>.*?</article>", r"<a\b[^>]*>.*?</a>"):
        def drop(m):
            if refs_dead(m.group(0)):
                removed[0] += 1
                return ""
            return m.group(0)
        body = re.sub(pat, drop, body, flags=re.S | re.I)

    # a heading above a grid that is now empty is worse than the entry it replaced
    body = re.sub(r"<h2\b[^>]*>[^<]{0,140}</h2>\s*<div class=\"grid\">\s*</div>", "",
                  body, flags=re.I)
    body = re.sub(r"<div class=\"grid\">\s*</div>", "", body, flags=re.I)
    wrote = write_if_changed(fp, body, original)
    log.append({"surface": rel, "kind": "html" if wrote else "html (unchanged)",
                "before": before,
                "after": len(html_entries(body, reviews)), "removed": removed[0]})
    return body


def strip_xml(rel, keep, reviews, log):
    fp = os.path.join(REPO, rel)
    original = read_text(fp)
    body = original
    rx = re.compile(r"<loc>[^<]*?/([A-Za-z0-9_.\-]+\.html)</loc>")
    before = len(set(rx.findall(body)) & reviews)
    removed = [0]

    def drop(m):
        hit = set(rx.findall(m.group(0))) & reviews
        if hit and not (hit & keep):
            removed[0] += 1
            return ""
        return m.group(0)
    body = re.sub(r"<url>.*?</url>", drop, body, flags=re.S | re.I)
    write_if_changed(fp, body, original)
    log.append({"surface": rel, "kind": "xml", "before": before,
                "after": len(set(rx.findall(body)) & reviews), "removed": removed[0]})
    return body


def strip_json(rel, keep, reviews, log):
    fp = os.path.join(REPO, rel)
    try:
        d = json.load(io.open(fp, encoding="utf-8"))
    except (ValueError, OSError):
        log.append({"surface": rel, "kind": "UNPARSEABLE -- left untouched",
                    "before": None, "after": None, "removed": 0})
        return
    before = len(json_entries(d, reviews))
    removed = [0]

    def dead(v):
        return isinstance(v, str) and v in reviews and v not in keep

    def clean(x):
        if isinstance(x, dict):
            if any(dead(v) for v in x.values()):
                removed[0] += 1
                return None
            return dict((k, clean(v)) for k, v in x.items() if not dead(k))
        if isinstance(x, list):
            out = []
            for v in x:
                if dead(v):
                    removed[0] += 1
                    continue
                cv = clean(v)
                if cv is not None:
                    out.append(cv)
            return out
        return x

    d2 = clean(d)
    io.open(fp, "w", encoding="utf-8").write(json.dumps(d2, indent=1, ensure_ascii=False))
    log.append({"surface": rel, "kind": "json", "before": before,
                "after": len(json_entries(d2, reviews)), "removed": removed[0]})


def card_for(page, pm):
    """Title and a one-line result, both read from the store object."""
    obj = json.load(io.open(os.path.join(REPO, pm[page]), encoding="utf-8"))
    title = short_title((obj.get("title") or obj.get("topic")
                         or page.replace("_", " ")).strip())
    by = (obj.get("results") or {}).get("by_outcome") or {}
    sub = "Pooled result with per-trial evidence"
    for oid, blk in by.items():
        if not isinstance(blk, dict):
            continue
        p = blk.get("pooled") or {}
        if p.get("point") is None or not (blk.get("per_trial") or []):
            continue
        meas = p.get("measure") or "estimate"
        lo, hi = p.get("ci_low"), p.get("ci_high")
        k = blk.get("k")
        if lo is not None and hi is not None:
            sub = "Pooled: %s %.3g (%.3g to %.3g), k=%s" % (meas, p["point"], lo, hi, k)
        else:
            sub = "Pooled: %s %.3g, k=%s" % (meas, p["point"], k)
        break
    return CARD % {"page": page, "title": esc(title[:120]), "sub": esc(sub)}


def short_title(t, limit=78):
    """A card label, not a sentence. Store titles here are full descriptive titles -- one is
    'Apixaban thromboprophylaxis: four trials, four different primary composites, and one
    estimand all four register...' -- and a hard character cut lands mid-word."""
    head = t.split(":")[0].strip()
    if 12 <= len(head) <= limit:
        return head
    if len(t) <= limit:
        return t
    cut = t[:limit].rsplit(" ", 1)[0].rstrip(" ,;-")
    return cut + "…"


def esc(s):
    return (str(s).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;"))


def add_to_index(keep, reviews, pm, log):
    fp = os.path.join(REPO, "index.html")
    original = read_text(fp)
    body = original
    have = html_entries(body, reviews) & keep
    missing = sorted(keep - have)
    if missing:
        cards = "".join(card_for(p, pm) for p in missing)
        block = ('<h2 id="sp-ready-more">Also ready</h2><div class="grid">%s</div>' % cards)
        body = body.replace("</body>", block + "</body>", 1) if "</body>" in body \
            else body + block
    if BANNER_ID not in body:
        body = re.sub(r"(<body[^>]*>)", lambda m: m.group(1) + (BANNER % len(keep)),
                      body, count=1)
    write_if_changed(fp, body, original)
    log.append({"surface": "index.html (added)", "kind": "add",
                "before": len(have), "after": len(html_entries(body, reviews) & keep),
                "removed": -len(missing)})


def add_to_sitemap(keep, reviews, log):
    fp = os.path.join(REPO, "sitemap.xml")
    original = read_text(fp)
    body = original
    rx = re.compile(r"<loc>[^<]*?/([A-Za-z0-9_.\-]+\.html)</loc>")
    have = set(rx.findall(body)) & keep
    missing = sorted(keep - have)
    if missing and "</urlset>" in body:
        blocks = "".join("<url><loc>%s%s</loc></url>" % (SITE, p) for p in missing)
        body = body.replace("</urlset>", blocks + "</urlset>", 1)
        write_if_changed(fp, body, original)
    log.append({"surface": "sitemap.xml (added)", "kind": "add", "before": len(have),
                "after": len(set(rx.findall(body)) & keep), "removed": -len(missing)})


def main():
    apply_ = "--apply" in sys.argv
    raw = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace",
                           write_through=True)

    def say(s):
        raw.write(s + chr(10))
        raw.flush()

    keep = set(l.strip() for l in
               io.open(os.path.join(REPO, "outputs", "_ready_keep.txt"), encoding="utf-8")
               if l.strip())
    pm = json.load(io.open(os.path.join(REPO, "ssot", "PAGE_MAP.json"), encoding="utf-8"))
    surf = json.load(io.open(os.path.join(REPO, "outputs", "surfaces_2026_08_28.json"),
                             encoding="utf-8"))
    reviews = review_population(surf["surfaces"])
    targets = [s["surface"] for s in surf["surfaces"]]

    say("KEEP               : %d" % len(keep))
    say("review population  : %d" % len(reviews))
    say("discovery surfaces : %d  (enumerated by search, not recalled)" % len(targets))
    say("")
    say("%-40s %8s %8s %9s" % ("surface BEFORE", "entries", "in KEEP", "not KEEP"))
    for s in surf["surfaces"]:
        say("%-40s %8d %8d %9d" % (s["surface"][:40], s["entries"], s["in_keep"],
                                   s["not_keep"]))
    say("")
    if not apply_:
        say("(dry run -- nothing written; pass --apply)")
        return 0

    log = []
    for rel in targets:
        low = rel.lower()
        if low.endswith(".xml"):
            strip_xml(rel, keep, reviews, log)
        elif low.endswith(".json"):
            strip_json(rel, keep, reviews, log)
        else:
            strip_html(rel, keep, reviews, log)
    add_to_index(keep, reviews, pm, log)
    add_to_sitemap(keep, reviews, log)

    say("%-40s %8s %8s %9s" % ("surface AFTER", "before", "after", "removed"))
    for e in log:
        say("%-40s %8s %8s %9d" % (e["surface"][:40], e["before"], e["after"], e["removed"]))

    # THE INVARIANT. Subset everywhere; complete on the two entry points.
    say("")
    violations = []
    for rel in targets:
        fp = os.path.join(REPO, rel)
        low = rel.lower()
        if low.endswith(".json"):
            try:
                ents = json_entries(json.load(io.open(fp, encoding="utf-8")), reviews)
            except ValueError:
                continue
        elif low.endswith(".xml"):
            b = io.open(fp, encoding="utf-8", errors="replace").read()
            ents = set(re.findall(r"<loc>[^<]*?/([A-Za-z0-9_.\-]+\.html)</loc>", b)) & reviews
        else:
            ents = html_entries(io.open(fp, encoding="utf-8", errors="replace").read(),
                                reviews)
        extra = ents - keep
        say("%-40s %4d entries, %d outside KEEP" % (rel[:40], len(ents), len(extra)))
        if extra:
            violations.append((rel, sorted(extra)[:5]))

    entry_ok = []
    for rel in ("index.html", "sitemap.xml"):
        fp = os.path.join(REPO, rel)
        b = io.open(fp, encoding="utf-8", errors="replace").read()
        ents = (set(re.findall(r"<loc>[^<]*?/([A-Za-z0-9_.\-]+\.html)</loc>", b))
                if rel.endswith(".xml") else html_entries(b, reviews)) & reviews
        entry_ok.append((rel, len(ents & keep), len(keep)))

    say("")
    for rel, got, want in entry_ok:
        say("ENTRY POINT %-20s carries %d of %d KEEP" % (rel, got, want))
    if violations:
        say("")
        say("STOP: %d surface(s) still carry entries outside KEEP" % len(violations))
        for rel, ex in violations:
            say("   %-38s e.g. %s" % (rel[:38], ", ".join(ex)))

    json.dump({"keep": sorted(keep), "n_keep": len(keep), "surfaces": log,
               "violations": [{"surface": r, "examples": e} for r, e in violations],
               "entry_points": [{"surface": r, "keep_carried": g, "keep_total": w}
                                for r, g, w in entry_ok],
               "invariant": "no surface carries a review entry outside KEEP; index.html and "
                            "sitemap.xml carry all of KEEP",
               "deviation": "the brief asked for every surface to end at 28. NMA_INDEX.html "
                            "indexes network meta-analyses and auto-gallery.html is the "
                            "explicitly unvalidated gallery -- both are different "
                            "populations, and writing the 28 into them would fabricate "
                            "listings. They are emptied of non-KEEP instead.",
               "note": "nothing deleted; every page still serves at its URL"},
              io.open(OUT, "w", encoding="utf-8"), indent=1)
    say("")
    say("wrote %s" % os.path.relpath(OUT, REPO))
    return 1 if violations else 0


if __name__ == "__main__":
    sys.exit(main())
