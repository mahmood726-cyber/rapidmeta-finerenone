"""UNIT 5 -- a falsy value may not occupy a value slot a reader reads.

THE REAL DEFECT THIS CAME FROM. MASTER-DEFECT-REGISTER row D1, quoted:

    "D1 | Falsy values reaching the reader -- None, ?, em dash, blank links | 21 | OPEN"

and the standing plant AS6, whose probe carried this admission until now:

    "p_falsy_served: page_text carries 'None'; no shipped module refuses a falsy in served
     prose"

with the fixture it proves defective, verbatim:

    "<p>Pooled efficacy: None (95% CI None to None).</p>"

WHY THIS IS THE CLASS WHERE A CARELESS DETECTOR DOES REAL HARM. The correct response to a
value the object does not hold is a VISIBLE REFUSAL WITH A REASON -- derive or refuse, and
never a softer claim. A detector that cannot tell a refusal from a falsy would accuse
"not recorded" and the cheapest way to satisfy it would be to print a number. So the model
answers below are load-bearing, not decoration.

WHY THE BOUNDARY IS STRUCTURAL AND NOT NUMERIC. There is no threshold and no score. A falsy
token is a finding only when it OCCUPIES A SLOT WHERE A VALUE BELONGS, and a slot is defined by
an enclosing structure, not by a distance or a count:

    A  VALUE ELEMENT   the whole normalised text of a <td>, <dd>, <output>, or any element
                       carrying data-value / data-store / data-pool / data-estimate
    B  LABELLED SLOT   `Label:` immediately followed by the token, inside one leaf element,
                       terminated by end of text or by . ; ( or another label
    C  INTERVAL SLOT   the token standing where a bound belongs inside a CI bracket
    D  LINK TARGET     an <a href> that is empty, "#", "none", "null" or "undefined"

The same token in running prose is not examined. That is the point: prose ABOUT a missing
value is how a refusal is written.

DECLARED EXCLUSIONS, WITH THEIR REASONS -- never an ad-hoc cut, and always counted.

  1 THE INTEGRITY SECTION, and any subtree marked data-artefact="integrity" or carrying an
    id/class containing "integrity". REASON: the integrity section's whole job is to NAME the
    defect classes, so it quotes the very tokens this unit scans for. Excluding it silently
    would be the self-referential failure; excluding it by declaration, and printing how many
    nodes that removed, keeps the exclusion measurable.

  2 <pre>, <samp>, <kbd>, and <code> ONLY WHERE IT IS NOT INSIDE A VALUE SLOT. REASON: these
    render source text, so `None` inside them is a literal being DISPLAYED rather than a value
    asserted to a reader. The <code> carve-out was NARROWED on 2026-08-29 after planting into
    a real page: SGLT2_HF_REVIEW.html writes every registration as
    `<td><code>NCT03315143</code></td>`, so a blanket <code> exclusion would have blinded this
    unit to a falsy in the registration column -- the exclusion would have removed exactly the
    mechanism. Inside a value slot, <code> is monospace styling on an identifier; in prose it
    is source text. The boundary is the enclosing value slot, which is structural.

  3 Any element carrying data-refusal. REASON: an explicit, machine-readable statement that
    this slot is a refusal. The corpus is entitled to declare that, and the declaration is the
    behaviour we want more of.

`excluded_count()` returns how many nodes each exclusion removed, so a caller cannot quote a
finding count without also showing what was cut and why.

ZERO IS NOT FALSY. A count of zero events is a measurement. `0`, `0.0` and `0%` are values and
never findings -- getting this wrong would delete real data from the corpus.

THE MODEL ANSWER, asserted to pass. `<td>not recorded</td>` and, better,
`<td>Direction not recorded &mdash; the object does not hold it</td>`: a visible refusal
carrying its reason. Both must pass, and the second contains an em dash, which is a finding
only when it is the WHOLE of a slot and never as a character inside a sentence.

REACH, STATED. This reads served HTML. A falsy that never reaches the served bytes is out of
reach, and a value rendered by client-side script after load is not examined.
"""
from __future__ import annotations

import re
from html.parser import HTMLParser

VALUE_TAGS = ("td", "dd", "output")
VALUE_ATTRS = ("data-value", "data-store", "data-pool", "data-estimate")

CODE_TAGS = ("code", "pre", "samp", "kbd")

# Blocks whose text is read for the labelled-slot and interval-slot shapes. Restricting to
# these keeps a label's value from being re-read once for every ancestor it sits inside.
LEAF_TAGS = ("p", "li", "dd", "dt", "td", "th", "span", "div", "caption", "figcaption",
             "small", "strong", "em", "h1", "h2", "h3", "h4", "h5", "h6", "output", "label")

# Exact whole-slot tokens. Compared after collapsing whitespace and lowercasing.
FALSY = ("none", "null", "nan", "undefined", "nil", "n/a", "na", "n.a.",
         "?", "-", "--", "---", "—", "–", "[object object]", "{}", "[]",
         "nonetype", "false")

DEAD_HREF = ("", "#", "none", "null", "undefined", "javascript:void(0)")

# B: a label, a colon, then the token standing where the value belongs.
_LABEL_SLOT = re.compile(
    r"(?P<label>[A-Za-z][A-Za-z0-9 ()/%'’-]{1,48}?)\s*:\s*"
    r"(?P<tok>None|null|NaN|undefined|N/A|nan|NULL|\?)"
    r"(?=$|[\s.;,)—–]|\s*\()",
)

# C: a bound slot inside a confidence interval.
_CI_SLOT = re.compile(
    r"(?:9[05](?:\.\d)?\s*%\s*(?:CI|confidence interval)|CI)\s*[:=]?\s*"
    r"(?P<lo>None|null|NaN|undefined|\?|-{1,2})\s*(?:to|–|—|,|;)\s*"
    r"(?P<hi>None|null|NaN|undefined|\?|-{1,2}|[-−]?\d+(?:\.\d+)?)",
    re.I)


def _norm(s):
    return " ".join((s or "").replace("\xa0", " ").split())


class _Slots(HTMLParser):
    """Collects value slots and leaf text, honouring the declared exclusions."""

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.stack = []          # (tag, attrs_dict, excluded_reason_or_None)
        self.slots = []          # (kind, tag, text)
        self.leaves = []         # text of leaf-ish blocks, for B and C
        self.links = []          # href values
        self.excluded = {"integrity section": 0, "code sample": 0, "declared refusal": 0}
        self.texts = []          # one text accumulator per OPEN element

    # -- exclusion decision, made once per element and inherited by its subtree ----------
    def _reason(self, tag, a):
        if tag in CODE_TAGS:
            if tag == "code" and self._in_value_slot():
                return None          # monospace styling on a value, not a source listing
            return "code sample"
        if "data-refusal" in a:
            return "declared refusal"
        if a.get("data-artefact", "").strip().lower() == "integrity":
            return "integrity section"
        blob = (a.get("id", "") + " " + a.get("class", "")).lower()
        if "integrity" in blob:
            return "integrity section"
        return None

    def _inherited(self):
        for _, _, r in reversed(self.stack):
            if r:
                return r
        return None

    def _in_value_slot(self):
        return any(t in VALUE_TAGS or any(k in a for k in VALUE_ATTRS)
                   for t, a, _ in self.stack)

    def handle_starttag(self, tag, attrs):
        a = {k.lower(): (v or "") for k, v in attrs}
        reason = self._inherited() or self._reason(tag, a)
        if reason and not self._inherited():
            self.excluded[reason] = self.excluded.get(reason, 0) + 1
        self.stack.append((tag, a, reason))
        self.texts.append([])
        if tag == "a" and not reason:
            self.links.append(a.get("href", ""))

    def handle_startendtag(self, tag, attrs):
        self.handle_starttag(tag, attrs)
        self.handle_endtag(tag)

    def handle_data(self, data):
        # text belongs to EVERY open element, so a value slot still sees content that an
        # inline child wrote. A single shared buffer loses it at the child's closing tag --
        # measured on a real page, where <td><strong>&mdash;</strong></td> read as empty and
        # two thirds of a table's falsy cells were silently not examined.
        for t in self.texts:
            t.append(data)

    def handle_endtag(self, tag):
        while self.stack:
            t, a, reason = self.stack.pop()
            text = _norm("".join(self.texts.pop())) if self.texts else ""
            if text and not reason:
                if t in VALUE_TAGS or any(k in a for k in VALUE_ATTRS):
                    self.slots.append(("value element", t, text))
                if t in LEAF_TAGS:
                    self.leaves.append(text)
            if t == tag:
                break


def _parse(html):
    p = _Slots()
    p.feed(html)
    p.close()
    while p.stack:                      # unclosed tags: read what they hold rather than drop it
        t, a, reason = p.stack.pop()
        text = _norm("".join(p.texts.pop())) if p.texts else ""
        if text and not reason:
            if t in VALUE_TAGS or any(k in a for k in VALUE_ATTRS):
                p.slots.append(("value element", t, text))
            if t in LEAF_TAGS:
                p.leaves.append(text)
    return p


def excluded_count(html):
    """How many subtrees each declared exclusion removed. Printed beside every count."""
    return dict(_parse(html).excluded)


# The population of labelled slots, falsy or not. Counting only the falsy ones and calling it
# a denominator would report a finding count twice and never show what it was out of.
_ANY_LABEL_SLOT = re.compile(
    r"(?P<label>[A-Za-z][A-Za-z0-9 ()/%'\u2019-]{1,48}?)\s*:\s*(?P<val>\S+)")


def assessable(html):
    """(value_slots, labelled_slots, links, findings) -- the denominator, always.

    Each of the first three is a POPULATION, not a finding count: a caller quoting "4 falsy
    slots" must be able to say 4 out of how many, and a page on which this unit examines
    nothing must report 0/0 rather than a clean bill.
    """
    p = _parse(html)
    lab = sum(len(_ANY_LABEL_SLOT.findall(t)) for t in p.leaves)
    return len(p.slots), lab, len(p.links), len(findings(html))


def findings(html, source="?"):
    """Every falsy token standing in a slot where a value belongs."""
    p = _parse(html)
    out = []

    for kind, tag, text in p.slots:                                        # A
        if text.lower() in FALSY:
            out.append({"source": source, "kind": "value element",
                        "slot": "<%s>" % tag, "token": text,
                        "quote": "<%s>%s</%s>" % (tag, text, tag)})

    for text in p.leaves:                                                  # B
        for m in _LABEL_SLOT.finditer(text):
            out.append({"source": source, "kind": "labelled slot",
                        "slot": m.group("label").strip(), "token": m.group("tok"),
                        "quote": _norm(text[max(0, m.start() - 20):m.end() + 20])})
        for m in _CI_SLOT.finditer(text):                                  # C
            for side in ("lo", "hi"):
                tok = m.group(side)
                if tok and tok.lower() in FALSY:
                    out.append({"source": source, "kind": "interval bound",
                                "slot": "%s bound" % ("lower" if side == "lo" else "upper"),
                                "token": tok,
                                "quote": _norm(m.group(0))})

    for href in p.links:                                                   # D
        if _norm(href).lower() in DEAD_HREF:
            out.append({"source": source, "kind": "link target",
                        "slot": "href", "token": href,
                        "quote": '<a href="%s">' % href})
    return out


# ---------------------------------------------------------------------------
# CONTROLS, anchored to fixtures.
# ---------------------------------------------------------------------------
KNOWN_NEGATIVES = [
    # THE MODEL ANSWER: a visible refusal, in words.
    "<td>not recorded</td>",
    # THE MODEL ANSWER WITH ITS REASON -- and it contains an em dash, which is a finding only
    # as a whole slot and never as a character inside a sentence.
    "<td>Direction not recorded &mdash; the object does not hold it</td>",
    "<p>Direction of benefit: not recorded, because the object holds no direction.</p>",
    # a declared refusal, exclusion 3
    '<td data-refusal="no direction held">None</td>',
    # ZERO IS A MEASUREMENT, not a falsy. Getting this wrong deletes real data.
    "<td>0</td>", "<td>0.0</td>", "<td>0%</td>", "<td>0 (0.0 to 0.0)</td>",
    # ordinary values
    "<p>Pooled efficacy: 0.79 (95% CI 0.71 to 0.88).</p>",
    "<td>RR 0.79</td>", "<dd>2 trials</dd>",
    # the word None inside running prose is prose, not a slot
    "<p>None of the trials reported the outcome.</p>",
    "<p>The registry lists none of these as non-inferiority designs.</p>",
    "<p>A dash is used where no value applies - see the notes.</p>",
    # EXCLUSION 1: the integrity section quotes the tokens this unit scans for
    ('<section id="integrity-statement"><p>Checked against 19 known defect classes. '
     "One was falsy values reaching the reader: None, ?, em dash, blank links.</p>"
     "<td>None</td></section>"),
    ('<div data-artefact="integrity"><td>None</td><td>?</td><td>&mdash;</td></div>'),
    # EXCLUSION 2: source text being displayed
    "<pre>{'direction': None}</pre>", "<code>None</code>",
    "<p>The store holds <code>None</code> for this field, so the page refuses.</p>",
    # a live link
    '<a href="https://clinicaltrials.gov/study/NCT00509106">NCT00509106</a>',
    # an anchor to a real target on the page
    '<a href="#methods">Methods</a>',
    # a label whose value is a legitimate hyphenated word
    "<p>Design: non-inferiority.</p>",
    # a negative number in a bound
    "<p>MD -2.50 (95% CI -4.00 to -1.00).</p>",
]

KNOWN_POSITIVES = [
    # the motivating fixture, verbatim from the AS6 probe
    "<p>Pooled efficacy: None (95% CI None to None).</p>",
    # THE SHAPE THE REAL PAGE USES -- a value wrapped in inline markup inside its cell.
    # Both of these read as EMPTY before 2026-08-29 and were silently not examined.
    "<td><strong>&mdash;</strong></td>",
    "<td><small>None</small></td>",
    # and a registration cell, where <code> is monospace styling on a value, not a listing
    "<td><code>None</code></td>",
    # D1's four named shapes
    "<td>None</td>",
    "<td>?</td>",
    "<td>&mdash;</td>",
    '<a href="">the protocol</a>',
    # the same falsy under a typed value attribute rather than a td
    '<span data-value="pooled">null</span>',
    "<output>undefined</output>",
    # a labelled slot in prose
    "<p>Certainty: None.</p>",
    "<p>Risk of bias: NaN</p>",
    # one bound of an interval missing
    "<p>The pooled effect was 1.20 (95% CI None to 1.60).</p>",
    # a dead link target
    '<a href="#">the protocol</a>',
    '<a href="null">the protocol</a>',
    # a definition list value
    "<dd>N/A</dd>",
]


def control():
    """(n_negatives, n_false_positives, examples), (n_positives, n_missed, examples)."""
    fp = [t for t in KNOWN_NEGATIVES if findings(t, "control")]
    missed = [t for t in KNOWN_POSITIVES if not findings(t, "control")]
    return (len(KNOWN_NEGATIVES), len(fp), fp), (len(KNOWN_POSITIVES), len(missed), missed)
