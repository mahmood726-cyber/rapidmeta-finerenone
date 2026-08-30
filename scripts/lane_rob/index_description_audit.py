# -*- coding: utf-8 -*-
"""How many pages does the portfolio index describe more than one way?

⛔ THE FINDING THIS MEASURES. `AGYW_HIV_PREP_REVIEW.html` is described THREE ways on one index:

    tile      "Dapivirine vaginal ring versus placebo ring for HIV prevention in women
               -- Pooled: RR 0.703 (0.566 to 0.8731), k=2"          <- matches the artefact
    table     "HIV PrEP for AGYW in sub-Saharan Africa · Digital Health (HIV) · 1 ·
               adherence RR 1.23 (1.06-1.43) · v0.1"                <- a DIFFERENT review
    registry  {"num": 687, "title": "HIV PrEP Modalities for Adolescent Girls and Young Women
               in sub-Saharan Africa NMA"}                          <- a third thing

Different outcome, different estimate, different k, different specialty. The table row is not
STALE -- it describes another review entirely, and a corrected page would land beneath it.

⇒ ***THE IDENTITY IS BEING CARRIED BY THE DESCRIPTION RATHER THAN BY THE URL.*** Same class as
the trial-label inversion, one level up: the URL is the identifier, three descriptions of it
disagree, and nothing reconciles them.

⚠️ AND THREE DISAGREEING DESCRIPTIONS ARE WORSE THAN ONE WRONG ONE. We know the tile is right
only because we independently know the artefact. A READER CANNOT ADJUDICATE -- the disagreement
destroys the very checkability the index exists to offer.

THIS SCRIPT ONLY MEASURES. It fixes nothing, by instruction: a hand-fix of one row is how a
class stays invisible, and the size of the class is the thing worth knowing first.
"""
import html as H
import io
import json
import os
import re
import sys

# ⛔ GATE 9 REFUSED A PUSH FOR THE LINE THAT USED TO BE HERE, AND IT WAS RIGHT.
# `F:/claude-temp/served_index.html` is a GENERIC NAME IN THE SHARED SCRATCH ROOT. Every lane
# auditing the index would pick the same path, so one lane would be reading bytes another lane
# had just overwritten -- and the audit would report a disagreement that belonged to neither
# index. The gate's own note records that this is not hypothetical: it "did not fire when this
# lane truncated another lane's file in the shared root".
#
# ⚠️ AND THE WRONG FIX IS A DIFFERENT GENERIC NAME. Uniqueness has to be STRUCTURAL, not a
# suffix someone chose: the path now lives inside THIS WORKTREE, which is unique by
# construction because each lane has its own and needs no coordination to keep it.
_DEFAULT = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__)))), "out", "fetched", "served_index.html")
INDEX = os.environ.get("INDEX_HTML", _DEFAULT)
HREF = re.compile(r'href="([A-Za-z0-9_.\-]+\.html)"')
REG = re.compile(r'"([A-Za-z0-9_.\-]+\.html)"\s*:\s*\{([^{}]*)\}')
TITLE = re.compile(r'"title"\s*:\s*"((?:[^"\\]|\\.)*)"')
STOP = set("""with versus against review living meta analysis rapidmeta pooled trial trials
study studies placebo compared comparison patients adults women results outcome outcomes
""".split())


def _txt(x):
    t = re.sub(r"<[^>]+>", " ", x)
    return re.sub(r"\s+", " ", H.unescape(t)).strip()


def _words(x):
    return {w for w in re.findall(r"[a-z]{4,}", (x or "").lower()) if w not in STOP}


def table_rows(html):
    """The big results table: {url: row text}. THE THIRD DESCRIPTION.

    ⛔ THIS IS THE ONE THAT DESCRIBES A DIFFERENT REVIEW. For our page the row reads
    "HIV PrEP for AGYW in sub-Saharan Africa · Digital Health (HIV) · 1 · adherence
    RR 1.23 (1.06-1.43) · v0.1" -- another outcome, another estimate, another k, another
    specialty. Not stale: a different study.
    """
    out = {}
    for m in re.finditer(r"<tr[^>]*>(.*?)</tr>", html, re.S | re.I):
        row = m.group(1)
        u = HREF.search(row)
        if not u:
            continue
        cells = [_txt(c) for c in re.findall(r"<t[dh][^>]*>(.*?)</t[dh]>", row, re.S | re.I)]
        if cells:
            out.setdefault(u.group(1), " · ".join(x for x in cells if x)[:180])
    return out


def sources(html):
    """-> (registry {url: title}, tiles {url: text}). Keyed on the URL, which is the identity."""
    reg = {}
    for m in REG.finditer(html):
        t = TITLE.search(m.group(2))
        if t:
            reg[m.group(1)] = H.unescape(t.group(1))
    tiles = {}
    for m in HREF.finditer(html):
        url = m.group(1)
        blob = html[m.end():m.end() + 900]
        nxt = HREF.search(blob)
        if nxt:
            blob = blob[:nxt.start()]
        txt = _txt(blob)
        if "Pooled" in txt or "k=" in txt:
            tiles.setdefault(url, txt[:180])
    return reg, tiles


def _ov(a, b):
    wa, wb = _words(a), _words(b)
    if not wa or not wb:
        return None
    return round(len(wa & wb) / float(min(len(wa), len(wb))), 2)


def audit(html):
    """All THREE descriptions, pairwise, keyed on the URL."""
    reg, tiles = sources(html)
    tab = table_rows(html)
    rows = []
    for url in sorted(set(reg) | set(tiles) | set(tab)):
        d = {"url": url, "registry": reg.get(url), "tile": tiles.get(url),
             "table": tab.get(url)}
        have = [k for k in ("registry", "tile", "table") if d[k]]
        d["described_by"] = have
        d["ov_reg_tile"] = _ov(d["registry"], d["tile"])
        d["ov_reg_table"] = _ov(d["registry"], d["table"])
        d["ov_tile_table"] = _ov(d["tile"], d["table"])
        scores = [v for v in (d["ov_reg_tile"], d["ov_reg_table"], d["ov_tile_table"])
                  if v is not None]
        d["worst"] = min(scores) if scores else None
        d["comparable_pairs"] = len(scores)
        if len(have) >= 2:
            rows.append(d)
    rows.sort(key=lambda r: (r["worst"] if r["worst"] is not None else 9))
    return reg, tiles, tab, rows


def main():
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace",
                                  line_buffering=True)
    if not os.path.exists(INDEX):
        print("REFUSED: %s is absent. Fetch the index first; this script does not invent one."
              % INDEX)
        return 2
    html = io.open(INDEX, encoding="utf-8", errors="replace").read()
    reg, tiles, tab, rows = audit(html)
    print("INDEX DESCRIPTION AUDIT -- keyed on the URL, which is the identity")
    print("  bytes read                        %8d" % len(html))
    print("  JSON registry entries             %8d" % len(reg))
    print("  tiles carrying a pooled result    %8d" % len(tiles))
    print("  results-table rows                %8d" % len(tab))
    print("  URLs with >=2 descriptions        %8d   <- the denominator" % len(rows))
    three = [r for r in rows if len(r["described_by"]) == 3]
    print("  URLs described all THREE ways     %8d" % len(three))
    print("  URLs in the registry ONLY         %8d" % len(set(reg) - set(tiles) - set(tab)))
    if not rows:
        print("  ⚠️ nothing comparable: this is a fact about the parse, not about the index.")
        return 1
    dis = [r for r in rows if r["worst"] is not None and r["worst"] < 0.34]
    print("")
    print("  DISAGREE (word overlap < 0.34)    %8d   = %.0f%% of %d compared"
          % (len(dis), 100.0 * len(dis) / len(rows), len(rows)))
    print("")
    for r in dis[:12]:
        print("  %-34s worst %.2f  (described %d ways)"
              % (r["url"][:34], r["worst"], len(r["described_by"])))
        for k in ("registry", "tile", "table"):
            if r[k]:
                print("     %-9s: %s" % (k, r[k][:96]))
    _outdir = os.path.dirname(INDEX)
    os.makedirs(_outdir, exist_ok=True)
    json.dump(rows, io.open(os.path.join(_outdir, "index_description_audit.json"),
                            "w", encoding="utf-8"), indent=1)
    print("")
    print("  ⛔ NOTHING IS FIXED HERE. A hand-fix of one row is how a class stays invisible.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
