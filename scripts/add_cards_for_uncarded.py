"""Add an index card for every surviving page that has none. Companion to the prune.

A CARD IS A PROMISE THAT A PAGE EXISTS, and the index must list what the site HAS. The prune
strips cards pointing at pruned pages; this adds cards for pages that survived without one --
overwhelmingly split children, which have never been carded because splitting a topic has
never included linking the children.

THE `pub` LINE STATES ONLY WHAT THE OBJECT HOLDS. Where no outcome is pooled it says so in
words rather than leaving a blank: a blank reads as unremarkable, and an absent pool is the
single most important fact about most of these pages. Nothing here asserts quality -- the
four indicator chips are computed by build_index_indicators.py from the audit record, so a
new card cannot look better than an old one merely because nobody has measured it.
"""
import glob, html, io, json, os, re, sys

if __name__ == "__main__":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LABEL = {"cardiology": "Cardiology", "infectious-disease": "Infectious disease",
         "neurology": "Neurology", "ophthalmology": "Ophthalmology",
         "nephrology": "Nephrology", "hepatology": "Hepatology",
         "endocrinology": "Endocrinology",
         "vaccines-global-health": "Vaccines &amp; global health"}


def main():
    idx_path = os.path.join(REPO, "index.html")
    idx = io.open(idx_path, encoding="utf-8", errors="replace").read()
    carded = set(re.findall(r'href="([A-Za-z0-9_\-]+\.html)"', idx))
    surviving = sorted(os.path.basename(p)
                       for p in glob.glob(os.path.join(REPO, "*.html")))
    pm = json.load(io.open(os.path.join(REPO, "ssot", "PAGE_MAP.json"), encoding="utf-8"))
    sids = re.findall(r'id="(sp-[a-z0-9\-]+)"', idx)
    added, skipped = 0, []
    for pg in surviving:
        if pg == "index.html" or pg in carded:
            continue
        op = pm.get(pg)
        obj = json.load(io.open(os.path.join(REPO, op), encoding="utf-8")) \
            if op and os.path.exists(os.path.join(REPO, op)) else {}
        sp = obj.get("specialty") or {}
        spv = sp.get("value") if isinstance(sp, dict) else sp
        sid = "sp-%s" % spv if spv else None
        if not sid or sid not in sids:
            # NO SPECIALTY MEANS NO HONEST SECTION. Named, not silently placed.
            skipped.append(pg)
            continue
        res = (obj.get("results") or {}).get("by_outcome") or {}
        ks = [b.get("k") for b in res.values()
              if isinstance(b, dict) and isinstance(b.get("k"), int)]
        k = max(ks) if ks else 0
        pooled = sum(1 for b in res.values() if isinstance(b, dict)
                     and (b.get("pooled") or {}).get("point") is not None)
        bits = [LABEL.get(spv, spv)]
        bits.append("%d trial%s" % (k, "" if k == 1 else "s") if k else "no trials recorded")
        bits.append("%d pooled outcome%s" % (pooled, "" if pooled == 1 else "s")
                    if pooled else "no pooled estimate")
        title = html.escape(str(obj.get("title") or pg.replace("_", " ").title())[:95],
                            quote=True)
        card = ('<a href="%s" class="card"><span class="name">%s</span>'
                '<span class="pub">%s</span></a>'
                % (html.escape(pg, quote=True), title, " &middot; ".join(bits)))
        i = idx.find('id="%s"' % sid)
        nxt = len(idx)
        for o in sids:
            if o == sid:
                continue
            j = idx.find('id="%s"' % o)
            if i < j < nxt:
                nxt = j
        at = idx.rfind("</a>", i, nxt)
        if at < 0:
            skipped.append(pg)
            continue
        idx = idx[:at + 4] + card + idx[at + 4:]
        added += 1
    io.open(idx_path, "w", encoding="utf-8", newline="").write(idx)
    print("cards added: %d   skipped (no specialty / no section): %d %s"
          % (added, len(skipped), skipped[:4]))


if __name__ == "__main__":
    main()
