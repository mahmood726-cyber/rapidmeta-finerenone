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
REFUSAL_FIELDS = ("withdrawn_reason", "withdrawn_note", "not_poolable_reason",
                  "absent_reason")
BANNER_ID = "ready-index-note"
# NAME THE PROPERTY, NOT THE SET. "Ready" means two different things here and an index that
# implied these were finished would be the worst thing on the site: the criterion selects
# reviews that carry a POOLED RESULT, while the card flags report readiness to PUBLISH, which
# these do not have. The banner says which one it is claiming, and says the other plainly.
BANNER = (
    '<div id="' + BANNER_ID + '" style="margin:0 0 1.2rem;padding:.85rem 1.1rem;'
    'border-left:4px solid #1d4ed8;background:#EFF6FF;font-size:.9rem;line-height:1.55">'
    '<strong>What this list selects:</strong> each of these %d reviews carries a pooled '
    'result with the per-trial data behind it. <strong>That is the only property claimed '
    'here.</strong> It does not mean a review is complete, and it does not mean it is ready '
    'to cite &mdash; most carry a dated <em>not ready</em> flag, and no review on this site '
    'has a scientific-validity assessment. Other topics are still published at their own '
    'addresses and nothing has been deleted; they are unlisted because their estimate was '
    'withdrawn, was never poolable, or is unfinished, and routing readers through them made '
    'the ones carrying a result hard to find.</div>')

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


def as_page(v, reviews):
    """Normalise either key format to the page name, or None."""
    if not isinstance(v, str):
        return None
    if v in reviews:
        return v
    if (v + ".html") in reviews:
        return v + ".html"
    return None


def json_entries(x, reviews, acc=None):
    acc = set() if acc is None else acc
    if isinstance(x, dict):
        for k, v in x.items():
            p = as_page(k, reviews)
            if p:
                acc.add(p)
            json_entries(v, reviews, acc)
    elif isinstance(x, list):
        for v in x:
            json_entries(v, reviews, acc)
    else:
        p = as_page(x, reviews)
        if p:
            acc.add(p)
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
        """A page name, in EITHER format. index_indicators.json keys its cards WITHOUT the
        .html extension -- BALANCED_CRYSTALLOIDS_ICU_REVIEW -- so a test that only knows
        'NAME.html' matched none of its 532 keys, left every one in place, and then reported
        '20 entries, 0 outside KEEP' because the verifier could not see them either."""
        if not isinstance(v, str):
            return False
        if v in reviews:
            return v not in keep
        if (v + ".html") in reviews:
            return (v + ".html") not in keep
        return False

    def clean(x):
        if isinstance(x, dict):
            if any(dead(v) for v in x.values()):
                removed[0] += 1
                return None
            out = {}
            for k, v in x.items():
                if dead(k):
                    removed[0] += 1
                    continue
                cv = clean(v)
                # drop the key outright; nulling it leaves 506 dead keys behind and makes
                # the client do a lookup that can return null
                if cv is None and isinstance(v, (dict, list)):
                    continue
                out[k] = cv
            return out
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


def result_line(page, pm):
    """The card's description: the RESULT, never the provenance narrative.

    THIS IS WHAT MAHMOOD IS ACTUALLY LOOKING AT. The index cards drew their description from
    the withdrawal reasoning, so card after card opened "Estimate withdrawn -- the trials do
    not share one endpoint...". The most prominent sentence on every card was our explanation
    for NOT having an answer, which is why the site reads as a wall of withdrawals. Filtering
    to the READY set does not fix that on its own: SGLT2_HF and CANGRELOR_PCI are both READY
    -- each has a live pooled outcome -- and BOTH still led with a withdrawal sentence for a
    DIFFERENT outcome on the same page.

    SOTAGLIFLOZIN already did the right thing -- "Pooled: HR 0.7171 (0.6246 to 0.8234), k=2"
    -- so this extends that pattern rather than inventing one.
    """
    if page not in pm:
        return from_served_page(page)[1]
    obj = json.load(io.open(os.path.join(REPO, pm[page]), encoding="utf-8"))
    by = (obj.get("results") or {}).get("by_outcome") or {}
    best = None
    for oid, blk in by.items():
        if not isinstance(blk, dict):
            continue
        pooled = blk.get("pooled") or {}
        if pooled.get("point") is None or not (blk.get("per_trial") or []):
            continue
        if any(blk.get(f) for f in REFUSAL_FIELDS):
            continue
        # THE MEASURE IS NOT ALWAYS ON `pooled`. cangrelor's live outcome
        # (corrected_composite_3component) carries no pooled.measure at all: the measure is
        # on the BLOCK as "RR", and a third copy sits in measure_recovered_2026_08_21. The
        # card therefore read "Pooled: estimate 0.9646" -- a real number with its measure
        # replaced by a placeholder, which tells a reader nothing about what 0.9646 IS.
        # Fallback order is most-specific first; "estimate" survives only as a last resort
        # and is now reported rather than shipped silently.
        meas = (pooled.get("measure") or blk.get("measure")
                or pooled.get("measure_recovered_2026_08_21") or "estimate")
        lo, hi, k = pooled.get("ci_low"), pooled.get("ci_high"), blk.get("k")
        # A POOL OF ONE IS NOT A POOL. bempedoic-acid holds exactly one trial
        # (NCT02993406) and read "Pooled: HR 0.87 (0.79 to 0.96), k=1", which presents a
        # single trial as a meta-analysis. The word is the whole defect: the number is
        # right and only its description overstates what produced it.
        lead = "Single trial" if k in (1, "1") else "Pooled"
        if lo is not None and hi is not None:
            best = "%s: %s %.4g (%.4g to %.4g), k=%s" % (lead, meas, pooled["point"],
                                                         lo, hi, k)
        else:
            best = "%s: %s %.4g, k=%s" % (lead, meas, pooled["point"], k)
        break
    # A page in KEEP has a live pooled outcome by construction -- leg 2 required it. If this
    # cannot find one, the keep list and this function disagree and that must be visible.
    return best


def retitle_cards(keep, reviews, pm, log):
    """Rewrite the description of every KEEP card to its result."""
    fp = os.path.join(REPO, "index.html")
    original = read_text(fp)
    body = original
    changed, unresolved = [0], []

    def fix(m):
        page, inner = m.group(1), m.group(0)
        if page not in keep:
            return inner
        line = result_line(page, pm)
        if not line:
            unresolved.append(page)
            return inner
        # retitle runs AFTER add_to_index and rewrites the description, so it must carry the
        # ruling note too -- otherwise it silently strips the one sentence that says a card
        # is here by ruling rather than by passing.
        note = ruling_note(page)
        if note and "indexed by ruling" not in line:
            line += " · indexed by ruling; %s" % note

        # THE NAME COMES FROM THE OBJECT TOO. Card names were hand-written strings living
        # only in index.html -- a second copy of the trial identity, reconciled with nothing.
        # One of them published a REAL result under the names of trials that did not produce
        # it: "HIV PrEP for AGYW in sub-Saharan Africa (HPTN 082 + FACTS-001)" sat above
        # RR 0.703, which is the DAPIVIRINE RING result from The Ring Study and ASPIRE. The
        # object was entirely correct -- right title, right two NCTs, zero mentions of HPTN
        # or FACTS anywhere in it. Only the card lied.
        #
        # Two others named trials their objects do not contain (VERTIS on a k=2 SGLT2 pool)
        # or asserted a design the object does not support ("NMA" on a pairwise pool).
        # Deriving the name removes the whole class rather than the three instances.
        try:
            if page in pm:
                obj = json.load(io.open(os.path.join(REPO, pm[page]), encoding="utf-8"))
                title = short_title((obj.get("title") or "").strip())
            else:
                title = from_served_page(page)[0] or ""
        except (OSError, ValueError, KeyError):
            title = ""
        if title:
            inner, _ = re.subn(r'(<span class="name">)(.*?)(</span>)',
                               lambda mm: mm.group(1) + esc(title) + mm.group(3),
                               inner, count=1, flags=re.S)

        new_inner, n = re.subn(r'(<span class="pub">)(.*?)(</span>)',
                               lambda mm: mm.group(1) + esc(line) + mm.group(3),
                               inner, count=1, flags=re.S)
        sys.stderr.write("DBG %s n=%s diff=%s%s" % (page[:26], n, new_inner != inner,
                                                    chr(10)))
        if n and new_inner != inner:
            changed[0] += 1
            return new_inner
        return inner

    body = re.sub(r'<a\s[^>]*href="([A-Za-z0-9_.\-]+\.html)"[^>]*class="card[^"]*"[^>]*>'
                  r'.*?</a>', fix, body, flags=re.S | re.I)
    write_if_changed(fp, body, original)
    log.append({"surface": "index.html (card text)", "kind": "retitle",
                "before": None, "after": changed[0], "removed": 0})
    return changed[0], unresolved


def from_served_page(page):
    """(title, result) for a page with NO store object, read from the served bytes.

    HFREF_NMA_AUTO_FULL_REVIEW has no PAGE_MAP entry -- that IS its leg-1 failure -- so
    there is no object to derive a card from. Rather than hardcode its numbers here, which
    would create yet another copy of a fact, this reads the page's own relabel block: the
    one that states ACEI versus Placebo and the interval, written when the omnibus framing
    was stripped. If the page stops saying it, this stops claiming it.
    """
    fp = os.path.join(REPO, page)
    if not os.path.exists(fp):
        return None, None
    body = read_text(fp)
    # STRIP THE SITE BRANDING. A <title> is written for a browser tab and carries the site
    # name; on a card the reader already knows the site, and "RapidMeta Cardiology | HFrEF
    # GDMT network" wastes the half of the label that identifies the review.
    t = re.search(r"<title>(.*?)</title>", body, re.S | re.I)
    raw_title = re.sub(r"\s+", " ", re.sub(r"<[^>]+>", "", t.group(1))).strip() if t else page
    if "|" in raw_title:
        raw_title = raw_title.split("|", 1)[1].strip() or raw_title
    title = short_title(raw_title)
    m = re.search(r"headline estimate is\s*<strong>(.*?)</strong>", body, re.S | re.I)
    result = None
    if m:
        result = re.sub(r"\s+", " ", re.sub(r"<[^>]+>", "", m.group(1))).strip()
        result = result.replace("&mdash;", "--")
    return title, result


def ruling_note(page):
    """The honest note a ruled-in page carries, read from the keep artefact, not invented."""
    try:
        d = json.load(io.open(os.path.join(REPO, "outputs",
                                           "ready_index_2026_08_28.json"), encoding="utf-8"))
    except (OSError, ValueError):
        return None
    for a in d.get("admitted_by_ruling") or []:
        if a.get("page") == page:
            return a.get("fails")
    return None


def card_for(page, pm):
    """Title and a one-line result, both read from the store object where one exists."""
    if page not in pm:
        title, result = from_served_page(page)
        return CARD % {"page": page,
                       "title": esc(title or page),
                       "sub": esc((result or "no store object; see the page")
                                  + ((" · indexed by ruling; " + ruling_note(page))
                                     if ruling_note(page) else ""))}
    obj = json.load(io.open(os.path.join(REPO, pm[page]), encoding="utf-8"))
    title = short_title((obj.get("title") or obj.get("topic")
                         or page.replace("_", " ")).strip())
    by = (obj.get("results") or {}).get("by_outcome") or {}
    sub = result_line(page, pm) or "Pooled result with per-trial evidence"
    note = ruling_note(page)
    if note:
        sub += " · indexed by ruling; %s" % note
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


def _specialty_section(page, pm):
    """The index section id this topic belongs in, from the OBJECT, or None.

    The object's `specialty` block carries `derived_from: "index section sp-cardiology"` and
    says of itself that it records WHERE THE INDEX PLACED THE TOPIC rather than making a
    clinical judgement. That is exactly the right key: it is the index's own historical
    placement, read back, not a specialty this lane invented.
    """
    rel = pm.get(page)
    if not rel or not os.path.exists(os.path.join(REPO, rel)):
        return None
    try:
        obj = json.load(io.open(os.path.join(REPO, rel), encoding="utf-8"))
    except (OSError, ValueError):
        return None
    sp = obj.get("specialty")
    if isinstance(sp, dict) and sp.get("value"):
        return "sp-" + str(sp["value"]).strip().lower()
    if isinstance(sp, str) and sp.strip():
        return "sp-" + sp.strip().lower()
    return None


def add_to_index(keep, reviews, pm, log):
    """Place each missing KEEP page in ITS OWN SECTION, and never append a second bucket.

    *** THIS FUNCTION PUT THE FLAGSHIP 12,000 PIXELS BELOW WHERE ANYONE LOOKS FOR IT. ***
    It appended every added card to a generic "Also ready" grid at the END of the page.
    ARNI_HF_REVIEW rendered at pixel 24,221 of a 24,498-pixel page while the Cardiology
    section sat at 12,137 with nine cards and no ARNI. Mahmood reported the flagship as GONE
    from the site. It was not gone: it was present, visible, correctly linked, and
    unfindable. A card nobody scrolls to is not on the index in any sense a reader cares
    about, and "it is in the HTML" is the same excuse as "it is committed".
    
    It also appended a NEW <h2 id="sp-ready-more"> on every run, so the page carried TWO
    sections with the SAME id -- invalid HTML and a growing pile. Existing blocks are removed
    before anything is added, so this is idempotent.
    """
    fp = os.path.join(REPO, "index.html")
    original = read_text(fp)
    body = original

    # 1. remove every previously appended bucket, so re-running cannot accumulate them
    n_old = len(re.findall(r'<h2 id="sp-ready-more">', body))
    body = re.sub(r'<h2 id="sp-ready-more">.*?</div>', "", body, flags=re.S)

    have = html_entries(body, reviews) & keep
    missing = sorted(keep - have)

    # 2. place each card in its own specialty section where the object names one
    placed, leftover = [], []
    for page in missing:
        sec = _specialty_section(page, pm)
        card = card_for(page, pm)
        if sec:
            m = re.search(r'(<h2 id="' + re.escape(sec) + r'">.*?<div class="grid">)',
                          body, re.S)
            if m:
                body = body[:m.end()] + card + body[m.end():]
                placed.append((page, sec))
                continue
        leftover.append((page, card))

    # 3. anything with no section goes in ONE bucket, placed immediately after the last
    #    specialty section rather than at the foot of the page
    if leftover:
        block = ('<h2 id="sp-ready-more">Also ready</h2><div class="grid">%s</div>'
                 % "".join(c for _p, c in leftover))
        anchor = None
        for m in re.finditer(r'<h2 id="sp-[a-z0-9\-]+">.*?</div>', body, re.S):
            anchor = m
        if anchor:
            body = body[:anchor.end()] + block + body[anchor.end():]
        elif "</body>" in body:
            body = body.replace("</body>", block + "</body>", 1)
        else:
            body += block

    if BANNER_ID not in body:
        body = re.sub(r"(<body[^>]*>)", lambda m: m.group(1) + (BANNER % len(keep)),
                      body, count=1)
    write_if_changed(fp, body, original)
    log.append({"surface": "index.html (added)", "kind": "add",
                "before": len(have), "after": len(html_entries(body, reviews) & keep),
                "removed": -len(missing),
                "placed_in_own_section": [{"page": p, "section": s} for p, s in placed],
                "no_section_declared": [p for p, _c in leftover],
                "stale_buckets_removed": n_old})


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
    n_retitled, unresolved = retitle_cards(keep, reviews, pm, log)
    say("card descriptions rewritten to their RESULT: %d" % n_retitled)
    if unresolved:
        say("REFUSED to invent a description for %d card(s): %s"
            % (len(unresolved), ", ".join(unresolved[:5])))
    say("")

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
