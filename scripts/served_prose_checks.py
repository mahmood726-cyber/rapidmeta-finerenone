# -*- coding: utf-8 -*-
"""CANONICAL served-prose defect checks -- the SINGLE definition used by the census, the gate, and the
fixture, so none can drift from the others.

Every check reads the bytes a READER sees: scripts/styles removed, tags stripped, ENTITIES UNESCAPED,
whitespace collapsed. The cardinal bug these close: the old census check searched html-escaped bytes
(`&#x27;`) with a pattern that only matched a literal quote, so a Python dict repr on the page scored
clean. A verifier must search the SAME bytes it showed.
"""
from __future__ import annotations
import re, html as _html


def rendered_text(html):
    t = re.sub(r"<(script|style)[^>]*>.*?</\1>", " ", html, flags=re.S | re.I)
    t = re.sub(r"<[^>]+>", " ", t)
    t = _html.unescape(t)                       # <-- the line whose absence hid the dict-repr defect
    return re.sub(r"[ \t]+", " ", t)


def visible_paragraphs(html):
    body = re.sub(r"<(script|style)[^>]*>.*?</\1>", " ", html, flags=re.S | re.I)
    out = []
    for m in re.finditer(r"<p\b[^>]*>(.*?)</p>", body, flags=re.S | re.I):
        txt = _html.unescape(re.sub(r"<[^>]+>", " ", m.group(1)))
        txt = re.sub(r"\s+", " ", txt).strip()
        if txt:
            out.append(txt)
    return out


_DANGLING = {"these", "the", "a", "an", "that", "which", "this", "those", "to", "of", "for",
             "and", "or", "with", "in", "on", "at", "by", "from", "as", "pools", "than", "into"}


def defect_truncation(html):
    """A reader-facing paragraph ending mid-clause (ends on a word that demands a continuation)."""
    hits = []
    for p in visible_paragraphs(html):
        last = p.rstrip()
        if not last or last[-1] in ".!?:;)’\"'":
            continue
        word = re.sub(r"[^A-Za-z]", "", last.split()[-1]).lower() if last.split() else ""
        if word in _DANGLING:
            hits.append(last[-70:])
    return hits


def defect_dict_repr(html):
    """A Python dict/repr in prose, OR an underscore-prefixed internal key in dict-key position."""
    t = rendered_text(html)
    hits = []
    if re.search(r"\{\s*['\"][A-Za-z_]+['\"]\s*:", t):
        hits.append(re.search(r"\{\s*['\"][A-Za-z_]+['\"]\s*:[^}]{0,40}", t).group(0)[:60])
    for m in re.finditer(r"['\"](_[a-z][a-z0-9_]{2,})['\"]\s*:", t):
        hits.append(m.group(1))
    return hits


def defect_false_wordforword(html):
    """A 'word for word / verbatim / identical' claim about registrations that in fact differ."""
    t = rendered_text(html)
    return [m.group(0)[:70] for m in re.finditer(r"(word[ -]for[ -]word|verbatim)[^.]{0,80}registrat", t, re.I)]


def defect_method_mismatch(html):
    """Heterogeneity prose naming REML/tau^2 UNDER REML while the served analysis is fixed-effect."""
    t = rendered_text(html)
    m = re.search(r"under REML", t)
    if m and re.search(r"fixed[- ]effect", t):
        return [t[max(0, m.start() - 40):m.start() + 12]]
    return []


def defect_duplicate_absence(html):
    """Two near-identical adjacent declared-absence headings (e.g. 'Screening and search' / 'Screening')."""
    heads = [re.sub(r"<[^>]+>", "", h).strip().lower()
             for h in re.findall(r"<h[23][^>]*>(.*?)</h[23]>", html, flags=re.S | re.I)]
    hits = []
    for i in range(len(heads) - 1):
        a, b = heads[i], heads[i + 1]
        if a and b and a.split()[:1] == b.split()[:1] and "screen" in a and "screen" in b:
            hits.append("%r then %r" % (heads[i], heads[i + 1]))
    return hits


CHECKS = [
    ("truncated paragraph (mid-clause)", defect_truncation),
    ("dict repr / underscore-internal key in prose", defect_dict_repr),
    ("false 'word for word' vs registrations", defect_false_wordforword),
    ("REML/tau^2 prose while fixed-effect served", defect_method_mismatch),
    ("duplicate declared-absence blocks", defect_duplicate_absence),
]


def scan(html):
    """Return list of (label, [hits]) for every check that fired. Empty list = clean."""
    out = []
    for label, fn in CHECKS:
        hits = fn(html)
        if hits:
            out.append((label, hits))
    return out
