#!/usr/bin/env python
"""
RapidMeta corpus-wide error sweep — READ-ONLY DETECTION.

Applies every STATIC detector in RAPIDMETA_ERROR_REGISTRY.md to every *_REVIEW.html in the repo
and writes an app x error-type matrix with prevalence counts and the worst offenders per type.

    python scripts/rapidmeta_error_sweep.py                     # full corpus
    python scripts/rapidmeta_error_sweep.py --only RM-F01       # one detector
    python scripts/rapidmeta_error_sweep.py --limit 25          # smoke run
    python scripts/rapidmeta_error_sweep.py --selftest          # prove the detectors can fail

NO FILE IS MODIFIED. This drives the gated remediation batches; it does not perform them.

Outputs: RAPIDMETA_ERROR_SWEEP.json, RAPIDMETA_ERROR_SWEEP.md
"""
from __future__ import annotations

import argparse
import io
import json
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path

# Idempotent: this module can be imported a second time under a different name (as __main__ plus
# as `rapidmeta_error_sweep` via the v2 pack). Re-wrapping closes the first wrapper's buffer and
# every later print raises "I/O operation on closed file" - the exact module-level-sys.stdout trap
# in rules/lessons.md. Wrap once, and mark it.
if not getattr(sys.stdout, "_rm_wrapped", False):
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    try:
        sys.stdout._rm_wrapped = True
    except AttributeError:
        pass

ROOT = Path(__file__).resolve().parent.parent

# ============================================================== JS literal parser
# realData is a JavaScript object literal with bare keys and leading-dot numbers (`.74`), so it is
# not JSON. This is a tolerant recursive-descent reader; it raises JsParseError rather than guessing.


class JsParseError(Exception):
    pass


_WS = " \t\r\n"
_IDENT = re.compile(r"[A-Za-z_$][A-Za-z0-9_$]*")
_NUM = re.compile(r"-?(?:\d+\.?\d*|\.\d+)(?:[eE][-+]?\d+)?")


class _R:
    __slots__ = ("s", "i", "n")

    def __init__(self, s: str, i: int = 0):
        self.s, self.i, self.n = s, i, len(s)

    def ws(self):
        s, n = self.s, self.n
        while self.i < n:
            c = s[self.i]
            if c in _WS:
                self.i += 1
            elif c == "/" and self.i + 1 < n and s[self.i + 1] == "/":
                j = s.find("\n", self.i)
                self.i = n if j == -1 else j + 1
            elif c == "/" and self.i + 1 < n and s[self.i + 1] == "*":
                j = s.find("*/", self.i)
                if j == -1:
                    raise JsParseError("unterminated comment")
                self.i = j + 2
            else:
                return

    def value(self, depth=0):
        if depth > 60:
            raise JsParseError("too deep")
        self.ws()
        if self.i >= self.n:
            raise JsParseError("eof")
        c = self.s[self.i]
        if c == "{":
            return self.obj(depth)
        if c == "[":
            return self.arr(depth)
        if c in "\"'`":
            return self.string()
        if c == "!":
            # minified boolean: `!0` is true, `!1` is false. The corpus is minified, so this is
            # not an edge case — missing it silently emptied `realData` for every app with an
            # adverse-event module.
            self.i += 1
            return not self.value(depth + 1)
        if c == "-" or c == "." or c.isdigit():
            m = _NUM.match(self.s, self.i)
            if not m:
                raise JsParseError("bad number")
            self.i = m.end()
            t = m.group(0)
            return float(t) if ("." in t or "e" in t or "E" in t) else int(t)
        m = _IDENT.match(self.s, self.i)
        if m:
            self.i = m.end()
            w = m.group(0)
            if w == "true":
                return True
            if w == "false":
                return False
            if w == "void":                      # minified `void 0` -> undefined
                self.value(depth + 1)
                return None
            if w in ("null", "undefined", "NaN", "Infinity"):
                return None
            # a bare identifier/expression is not a literal we can trust
            raise JsParseError("identifier value " + w)
        raise JsParseError("unexpected " + repr(c))

    def string(self):
        q = self.s[self.i]
        self.i += 1
        out = []
        s, n = self.s, self.n
        while self.i < n:
            c = s[self.i]
            if c == "\\":
                nxt = s[self.i + 1] if self.i + 1 < n else ""
                out.append({"n": "\n", "t": "\t", "r": "\r", "b": "\b", "f": "\f"}.get(nxt, nxt))
                if nxt == "u" and self.i + 5 < n:
                    try:
                        out[-1] = chr(int(s[self.i + 2:self.i + 6], 16))
                        self.i += 6
                        continue
                    except ValueError:
                        pass
                self.i += 2
                continue
            if c == q:
                self.i += 1
                return "".join(out)
            out.append(c)
            self.i += 1
        raise JsParseError("unterminated string")

    def arr(self, depth):
        self.i += 1
        out = []
        while True:
            self.ws()
            if self.i >= self.n:
                raise JsParseError("eof in array")
            if self.s[self.i] == "]":
                self.i += 1
                return out
            if self.s[self.i] == ",":
                self.i += 1
                continue
            out.append(self.value(depth + 1))

    def obj(self, depth):
        self.i += 1
        out = {}
        while True:
            self.ws()
            if self.i >= self.n:
                raise JsParseError("eof in object")
            c = self.s[self.i]
            if c == "}":
                self.i += 1
                return out
            if c == ",":
                self.i += 1
                continue
            if c in "\"'`":
                k = self.string()
            else:
                m = _IDENT.match(self.s, self.i)
                if m:
                    k = m.group(0)
                    self.i = m.end()
                else:
                    m = _NUM.match(self.s, self.i)
                    if not m:
                        raise JsParseError("bad key at " + repr(self.s[self.i:self.i + 20]))
                    k = m.group(0)
                    self.i = m.end()
            self.ws()
            if self.i >= self.n or self.s[self.i] != ":":
                raise JsParseError("expected ':' after key " + k)
            self.i += 1
            out[k] = self.value(depth + 1)


def parse_js_object_at(text: str, start: int):
    r = _R(text, start)
    return r.obj(0), r.i


def balanced_span(text: str, start: int, opener: str = "{", closer: str = "}") -> int:
    """Index just past the matching closer, ignoring braces inside strings. -1 if unbalanced."""
    depth, i, n = 0, start, len(text)
    q = None
    while i < n:
        c = text[i]
        if q:
            if c == "\\":
                i += 2
                continue
            if c == q:
                q = None
        elif c in "\"'`":
            q = c
        elif c == opener:
            depth += 1
        elif c == closer:
            depth -= 1
            if depth == 0:
                return i + 1
        i += 1
    return -1


def balanced_div(text: str, start: int) -> str:
    """Balanced <div>...</div> walk from the '<div' at `start`. A regex matches a prefix and
    silently leaves the rest — that is how the HFrEF 28-vs-27 badge shipped (RECIPE-C 1.3)."""
    depth, i, n = 0, start, len(text)
    while i < n:
        if text.startswith("<div", i) and (i + 4 >= n or text[i + 4] in " \t\r\n>"):
            depth += 1
            i += 4
        elif text.startswith("</div>", i):
            depth -= 1
            i += 6
            if depth == 0:
                return text[start:i]
        else:
            i += 1
    return text[start:min(n, start + 20000)]


# ============================================================== context

RECURRENT_TRIALS = {
    # trials whose PRIMARY is a recurrent-event / rate estimand (registry: RM-A01)
    "soloist-whf": "total first+subsequent primary events; rate 51.0 vs 76.3 per 100 pt-yr",
    "soloist": "total first+subsequent primary events",
    "affirm-ahf": "293 vs 372 TOTAL recurrent events; rate ratio 0.79",
    "ironman": "336 vs 411 TOTAL recurrent events; rate ratio 0.82",
    "paragon-hf": "894 vs 1009 TOTAL events; rate ratio 0.87, not a hazard ratio",
    "scored": "recurrent-event primary (co-primaries)",
}

CONTAMINATION_CLASSES = [
    ("sglt2", ["sglt2", "sglt-2", "dapagliflozin", "empagliflozin", "sotagliflozin",
               "dapa-hf", "emperor-reduced", "emperor-preserved", "empa-reg"]),
    ("sglt2_ae", ["fournier", "genital mycotic", "diabetic ketoacidosis"]),
    ("mra", ["finerenone", "fidelio", "figaro", "eplerenone"]),
    ("ckd", ["egfr slope", "uacr"]),
    ("arni", ["sacubitril", "paradigm-hf", "paragon-hf", "paradise-mi", "paraglide-hf", "entresto"]),
]

FOREIGN_ALIAS_NCTS = ["NCT01035255", "NCT01920711", "NCT02924727", "NCT03988634"]
ARNI_OWNER_TOKENS = ["sacubitril", "arni", "entresto", "valsartan", "neprilysin"]

GREEN_HEXES = ["#15803d", "#0a7d33", "#166534", "#14532d"]
PASS_PHRASES = ["checks passed", "evidence grade: verified", "✓ verified", "externally validated"]

MACHINERY_MIN_K = {
    "funnel": (10, [r"funnel[- ]?plot", r"id=[\"']?plot-funnel"]),
    "egger": (10, [r"\bEgger", r"egger[’']?s test"]),
    "trimfill": (10, [r"trim[- ]and[- ]fill", r"trim[- ]?fill"]),
    "copas": (15, [r"\bCopas\b"]),
    "metaregression": (10, [r"meta[- ]regression", r"metareg"]),
    "tsa": (5, [r"\bTSA\b", r"trial sequential analysis", r"O'?Brien[- ]Fleming"]),
    "nma_league": (3, [r"league table", r"node[- ]split", r"CINeMA"]),
}


class Ctx:
    __slots__ = ("path", "name", "text", "low", "_realdata", "_verdict", "_badge",
                 "_trials", "_title", "_topic", "size", "parse_errors")

    def __init__(self, path: Path, text: str):
        self.path = path
        self.name = path.name
        self.text = text
        self.low = text.lower()
        self.size = len(text)
        self.parse_errors = []
        self._realdata = self._verdict = self._badge = self._trials = self._title = self._topic = None

    # -- lazily derived surfaces ------------------------------------------------
    @property
    def title(self) -> str:
        if self._title is None:
            m = re.search(r"<title>(.{0,300}?)</title>", self.text, re.S | re.I)
            self._title = (m.group(1).strip() if m else "")
        return self._title

    @property
    def topic_tokens(self):
        if self._topic is None:
            src = (self.title + " " + " ".join(
                t.get("group", "") or "" for t in self.trials.values() if isinstance(t, dict))).lower()
            self._topic = set(w for w in re.split(r"[^a-z0-9-]+", src) if len(w) > 3)
        return self._topic

    @property
    def verdict(self):
        if self._verdict is None:
            self._verdict = {}
            m = re.search(r"window\.__verdict\s*=\s*\{", self.text)
            if m:
                end = balanced_span(self.text, m.end() - 1)
                if end > 0:
                    try:
                        self._verdict = json.loads(self.text[m.end() - 1:end])
                    except Exception:
                        try:
                            self._verdict = parse_js_object_at(self.text, m.end() - 1)[0]
                        except JsParseError:
                            self._verdict = {}
        return self._verdict

    @property
    def badge(self) -> str:
        if self._badge is None:
            m = re.search(r"<div id=[\"']rapidmeta-integrity-badge[\"']", self.text)
            self._badge = balanced_div(self.text, m.start()) if m else ""
        return self._badge

    @property
    def realdata(self):
        if self._realdata is None:
            self._realdata = {}
            self.parse_errors = []
            found_block = False
            for m in re.finditer(r"\brealData\s*[:=]\s*\{", self.text):
                found_block = True
                try:
                    obj, _ = parse_js_object_at(self.text, m.end() - 1)
                except JsParseError as e:
                    # FAIL LOUD: a silent parse failure blinds every ledger-based detector and
                    # looks identical to a clean app.
                    self.parse_errors.append(f"realData@{m.start()}: {e}")
                    continue
                if isinstance(obj, dict) and len(obj) > len(self._realdata):
                    self._realdata = obj
                if self._realdata:
                    break
            if found_block and not self._realdata and not self.parse_errors:
                self.parse_errors.append("realData block present but parsed empty")
        return self._realdata

    @property
    def trials(self):
        if self._trials is None:
            self._trials = {k: v for k, v in self.realdata.items() if isinstance(v, dict)}
        return self._trials

    @property
    def k(self) -> int:
        return len(self.trials)

    def has(self, pat: str) -> bool:
        return re.search(pat, self.text, re.I) is not None

    def count(self, pat: str) -> int:
        return len(re.findall(pat, self.text, re.I))


def _num(x):
    try:
        if x is None or isinstance(x, bool):
            return None
        v = float(x)
        return v if v == v and v not in (float("inf"), float("-inf")) else None
    except (TypeError, ValueError):
        return None


def _rows(t: dict):
    r = t.get("allOutcomes") or t.get("outcomes") or []
    return [x for x in r if isinstance(x, dict)] if isinstance(r, list) else []


# ============================================================== detectors
# Each detector returns a list of evidence strings. Empty list = clean.

DETECTORS = {}
META = {}


def detector(eid, name, severity="P1"):
    def deco(fn):
        DETECTORS[eid] = fn
        META[eid] = {"id": eid, "name": name, "severity": severity}
        return fn
    return deco


# ---------------------------------------------------------- family A

@detector("RM-A01", "Recurrent-event coercion", "P0")
def d_a01(c: Ctx):
    out = []
    for nct, t in c.trials.items():
        nm = str(t.get("name") or "").lower()
        key = next((k for k in RECURRENT_TRIALS if k and k in nm), None)
        if not key:
            continue
        est = str(t.get("estimandType") or "").upper()
        has_counts = _num(t.get("tE")) is not None and _num(t.get("cE")) is not None
        if has_counts and est != "RATE_RATIO":
            out.append(f"{t.get('name')} ({nct}) carries tE={t.get('tE')} cE={t.get('cE')} "
                       f"with estimandType={est or 'ABSENT'} — {RECURRENT_TRIALS[key]}")
        for r in _rows(t):
            if str(r.get("type", "")).upper() == "PRIMARY" and _num(r.get("tE")) is not None \
               and str(r.get("estimandType") or "").upper() not in ("RATE_RATIO",):
                out.append(f"{t.get('name')} primary row '{r.get('title')}' has per-arm counts "
                           f"under estimandType={r.get('estimandType') or 'ABSENT'}")
                break
    return out


@detector("RM-A02", "Estimand mixing in one pool", "P0")
def d_a02(c: Ctx):
    out = []
    if re.search(r'"RR"\s*!==\s*String\(', c.text):
        out.append('the DENYLIST guard `"RR" !== String(d?.estimandType ?? "HR")` is present — '
                   "anything not literally RR is treated as a hazard ratio")
    ests = Counter()
    for t in c.trials.values():
        e = str(t.get("estimandType") or "").upper()
        if e:
            ests[e] += 1
    ratio_like = {"HR", "OR", "RR"}
    if len(ests) > 1 and c.k >= 2:
        foreign = {e for e in ests if e not in ratio_like}
        if foreign and (set(ests) & ratio_like):
            out.append("mixed estimands across pooled trials: " +
                       ", ".join(f"{e}x{n}" for e, n in sorted(ests.items())))
    return out


@detector("RM-A03", "Wrong effect-measure label", "P1")
def d_a03(c: Ctx):
    out = []
    for nct, t in c.trials.items():
        est = str(t.get("estimandType") or "").upper()
        if est in ("RR", "OR", "RATE_RATIO") and (t.get("publishedHR") is not None or t.get("pubHR") is not None):
            out.append(f"{t.get('name') or nct}: estimandType={est} beside a publishedHR field "
                       f"({t.get('publishedHR') if t.get('publishedHR') is not None else t.get('pubHR')})")
    return out


@detector("RM-A04", "Peto output labelled HR", "P1")
def d_a04(c: Ctx):
    out = []
    for m in re.finditer(r"[Pp]eto", c.text):
        seg = c.text[m.start():m.start() + 90]
        if re.search(r"\b(hazard ratio|HR)\b", seg):
            out.append("Peto near an HR label: " + re.sub(r"\s+", " ", seg)[:110])
            if len(out) >= 3:
                break
    return out


@detector("RM-A05", "Continuous outcome in a ratio model", "P0")
def d_a05(c: Ctx):
    out = []
    if re.search(r"trials\.some\(\s*\w*\s*=>[^)]{0,120}(continuous|isCont|\bmd\b)", c.text, re.I):
        out.append("`trials.some(...)` routes the WHOLE analysis to the continuous engine if ANY "
                   "trial has a continuous outcome")
    if re.search(r"\|\|\s*\{\s*md\s*:", c.text):
        out.append("`|| {md: t.data.md, se: t.data.se}` fallback substitutes a different estimand "
                   "for trials lacking the selected continuous outcome")
    return out


@detector("RM-A07", "Non-ratio quantity in a ratio field", "P0")
def d_a07(c: Ctx):
    out = []
    fields = ("publishedHR", "pubHR", "hrLCI", "hrUCI", "pubHR_LCI", "pubHR_UCI")
    for nct, t in c.trials.items():
        for f in fields:
            v = _num(t.get(f))
            if v is None:
                continue
            if v <= 0:
                out.append(f"{t.get('name') or nct}.{f} = {v} — a ratio of positive rates cannot be <= 0")
            elif v > 20:
                out.append(f"{t.get('name') or nct}.{f} = {v} — outside any reported ratio range")
        for r in _rows(t):
            title = str(r.get("title") or "")
            if re.search(r"(percent|percentage|%)\s*change|change from baseline", title, re.I) and \
               (r.get("effect") is not None or t.get("publishedHR") is not None):
                out.append(f"{t.get('name') or nct}: change-from-baseline outcome '{title[:60]}' "
                           f"carries a ratio-field value")
                break
    return out


@detector("RM-A08", "Component counts paired with a composite effect", "P1")
def d_a08(c: Ctx):
    out = []
    for nct, t in c.trials.items():
        tE, tN, cE, cN = (_num(t.get(x)) for x in ("tE", "tN", "cE", "cN"))
        eff = _num(t.get("publishedHR")) or _num(t.get("pubHR"))
        if None in (tE, tN, cE, cN) or eff is None or tN <= 0 or cN <= 0 or cE <= 0 or tE <= 0:
            continue
        crude = (tE / tN) / (cE / cN)
        if (crude - 1) * (eff - 1) < 0 and abs(crude - 1) > 0.02 and abs(eff - 1) > 0.02:
            out.append(f"{t.get('name') or nct}: crude RR {crude:.3f} vs published effect {eff} "
                       "— opposite directions")
    return out


@detector("RM-A09", "Win-ratio estimate paired with an HR", "P1")
def d_a09(c: Ctx):
    out = []
    for nct, t in c.trials.items():
        blob = json.dumps(t, default=str).lower()
        if "win ratio" in blob or "winratio" in blob:
            if t.get("publishedHR") is not None or t.get("pubHR") is not None:
                out.append(f"{t.get('name') or nct}: a win-ratio trial carries publishedHR="
                           f"{t.get('publishedHR', t.get('pubHR'))}")
    return out


# ---------------------------------------------------------- family B

@detector("RM-B01", "Scope-lock failure", "P0")
def d_b01(c: Ctx):
    out = []
    modal = re.search(r"sort\(\s*\(a,\s*b\)\s*=>\s*b\.count\s*-\s*a\.count\s*\)", c.text)
    idx0 = re.search(r"(allOutcomes|outcomes)\s*\[\s*0\s*\]", c.text)
    if modal and idx0:
        out.append("outcomeLabel derives from a MODAL-TITLE frequency sort while the binding "
                   "indexes outcomes[0] — label and binding are decoupled")
    elif modal:
        out.append("outcomeLabel derives from a modal-title frequency sort")
    return out


@detector("RM-B02", "Stale outcome-state leakage", "P0")
def d_b02(c: Ctx):
    out = []
    if "COMPLETE-POOLING-REPAIR" in c.text or "[pooling-repair]" in c.text:
        disabled = re.search(r"pooling[- ]repair[^\n]{0,200}(disabled|neutralis|no-op)", c.text, re.I)
        if not disabled:
            out.append("the `pooling-repair` block is present and not disabled — it copies "
                       "realData tE/cE into t.data and force-sets effectMeasure='HR', bypassing the scope lock")
    if re.search(r"\?\?\s*t\.data\.(tE|cE|tN|cN)", c.text):
        out.append("`?? t.data.<count>` fallback leaks the previously bound endpoint's counts")
    if "ensureAnalysisReady" in c.text and not re.search(
            r"ensureAnalysisReady\s*=\s*function\s*\(\s*\)\s*\{\s*\}|ensureAnalysisReady\s*=\s*\(\)\s*=>\s*\{?\s*\}?", c.text):
        out.append("`ensureAnalysisReady` is reachable without an app-local no-op override — "
                   "opening the Paper tab can flip the analysis scope")
    return out


@detector("RM-B03", "Silent endpoint fallback", "P0")
def d_b03(c: Ctx):
    hits = re.findall(r"(?:allOutcomes|outcomes)\s*\[\s*0\s*\]", c.text)
    return [f"{len(hits)} `outcomes[0]` fallback site(s) — a missing scope substitutes another endpoint"] if hits else []


# ---------------------------------------------------------- family C

@detector("RM-C01", "Randomised vs analysed denominator unlabelled", "P2")
def d_c01(c: Ctx):
    out = []
    labelled = bool(re.search(r"\b(nRandomised|nAnalysed|randomised\s*/\s*analysed|analysed\s*n\b)", c.text, re.I))
    for nct, t in c.trials.items():
        base = t.get("baseline") if isinstance(t.get("baseline"), dict) else {}
        bn, tN, cN = _num(base.get("n")), _num(t.get("tN")), _num(t.get("cN"))
        if None in (bn, tN, cN) or bn <= 0:
            continue
        if abs((tN + cN) - bn) / bn > 0.02 and not labelled:
            out.append(f"{t.get('name') or nct}: baseline n={int(bn)} vs arms {int(tN)}+{int(cN)}"
                       f"={int(tN + cN)} ({abs((tN + cN) - bn) / bn:.1%} gap) with no randomised/analysed label")
    return out


# ---------------------------------------------------------- family D

@detector("RM-D01", "Wrong NCT / registry-concordance failure", "P1")
def d_d01(c: Ctx):
    out = []
    by_nct = defaultdict(set)
    for nct, t in c.trials.items():
        if re.fullmatch(r"NCT\d{8}", str(nct)):
            by_nct[nct].add(str(t.get("name") or ""))
        elif str(nct).upper().startswith("NCT"):
            out.append(f"malformed registry identifier: {nct}")
    for nct, names in by_nct.items():
        if len(names) > 1:
            out.append(f"{nct} carries {len(names)} different trial names: {sorted(names)}")
    return out


@detector("RM-D02", "Wrong or cross-topic citation", "P1")
def d_d02(c: Ctx):
    out = []
    by_pmid = defaultdict(set)
    for nct, t in c.trials.items():
        p = str(t.get("pmid") or "").strip()
        if not p:
            continue
        if not re.fullmatch(r"\d{6,9}", p):
            out.append(f"{t.get('name') or nct}: malformed PMID {p!r}")
            continue
        by_pmid[p].add(str(t.get("name") or nct))
    for p, names in by_pmid.items():
        if len(names) > 1:
            out.append(f"PMID {p} cited for {len(names)} different trials: {sorted(names)}")
    return out


@detector("RM-D05", "Fabricated / imported analysis row", "P1")
def d_d05(c: Ctx):
    out = []
    for nct, t in c.trials.items():
        for r in _rows(t):
            if r.get("effect") is not None and not (r.get("source") or r.get("sourceUrl") or r.get("pmid")):
                out.append(f"{t.get('name') or nct}: outcome '{str(r.get('title'))[:50]}' carries "
                           f"effect={r.get('effect')} with no source field")
                break
    return out


@detector("RM-D06", "App identity mismatch", "P1")
def d_d06(c: Ctx):
    if not c.title:
        return ["no <title> — the app does not declare its subject"]
    stem = re.sub(r"_(AUTO_)?(FULL_)?REVIEW$", "", c.path.stem, flags=re.I)
    toks = [w.lower() for w in re.split(r"[^A-Za-z0-9]+", stem) if len(w) > 3]
    if not toks:
        return []
    hay = (c.title + " " + " ".join(str(t.get("group") or "") for t in c.trials.values())).lower()
    # Strip separators on BOTH sides: the filename token ANTIAMYLOID must match the title's
    # "Anti-Amyloid", and ANTIVEGF must match "Anti-VEGF". Without this the detector reported a
    # false identity mismatch for every hyphenated drug-class name.
    flat = re.sub(r"[^a-z0-9]+", "", hay)
    if not any(t in hay or t in flat for t in toks):
        return [f"filename tokens {toks} appear in neither the title "
                f"({c.title[:80]!r}) nor any ledger group"]
    return []


# ---------------------------------------------------------- family E

# A hit inside one of these is a CLAIM-BEARING slot and is P0; elsewhere it is a residue advisory.
CLAIM_SLOT_RE = re.compile(
    r"(hasDrug\s*=|screenScore|eligib|inclusion|exclusion|PUBLISHED_META_BENCHMARKS|"
    r"safetyOutcome|adverseEvent|dataSeal|exportTitle|protocol\.|state\.protocol|PICO)", re.I)


@detector("RM-E01", "Cross-topic template contamination", "P0")
def d_e01(c: Ctx):
    out = []
    topic = " ".join(c.topic_tokens)
    for cid, tokens in CONTAMINATION_CLASSES:
        if any(tok.split("-")[0] in topic for tok in tokens):
            continue
        for tok in tokens:
            for m in re.finditer(re.escape(tok), c.low):
                # the repo's own asset/URL namespace is not contamination
                if c.low[max(0, m.start() - 12):m.start()].endswith("rapidmeta-"):
                    continue
                ctx = re.sub(r"\s+", " ", c.text[max(0, m.start() - 110):m.start() + 90])
                slot = "CLAIM-BEARING" if CLAIM_SLOT_RE.search(ctx) else "residue"
                out.append(f"{cid}/{tok} [{slot}]: ...{ctx.strip()[:200]}...")
                break
            if len(out) >= 6:
                return out
    return out


@detector("RM-E02", "Foreign trial-alias registry", "P1")
def d_e02(c: Ctx):
    topic = " ".join(c.topic_tokens)
    if any(t in topic for t in ARNI_OWNER_TOKENS):
        return []
    hits = [n for n in FOREIGN_ALIAS_NCTS if n in c.text]
    if len(hits) >= 2:
        return [f"sacubitril/valsartan alias table baked into a non-ARNI app: {hits}"]
    return []


# ---------------------------------------------------------- family F

def _badge_is_green(c: Ctx):
    b = c.badge.lower()
    if not b:
        return False, ""
    for h in GREEN_HEXES:
        if h in b:
            return True, h
    for p in PASS_PHRASES:
        if p in b:
            return True, p
    return False, ""


def _verdict_open(c: Ctx):
    counts = c.verdict.get("counts") or {}
    return sum(int(v) for k, v in counts.items()
               if re.match(r"^P[012]_", str(k)) and isinstance(v, (int, float)) and v > 0)


@detector("RM-F01", "False-green verdict badge", "P0")
def d_f01(c: Ctx):
    green, tok = _badge_is_green(c)
    if not green:
        return []
    out = []
    v = c.verdict
    word = str(v.get("verdict") or "").upper()
    counts = v.get("counts") or {}
    reasons = v.get("reasons") or []
    seen = counts.get("n_trials_seen")
    if word and word != "STABLE":
        out.append(f"green badge ({tok}) over __verdict='{word}'")
    open_n = _verdict_open(c)
    if open_n:
        out.append(f"green badge ({tok}) over {open_n} open P1/P2 finding(s)")
    if reasons:
        out.append(f"green badge ({tok}) over {len(reasons)} verdict reason(s): {reasons[:2]}")
    if seen == 0 or c.k == 0:
        out.append(f"green badge ({tok}) over an empty ledger (n_trials_seen={seen}, realData k={c.k})")
    return out


@detector("RM-F02", "Verdict-surface disagreement", "P0")
def d_f02(c: Ctx):
    out = []
    counts = c.verdict.get("counts") or {}
    seen = counts.get("n_trials_seen")
    m = re.search(r"Trials?\s*:\s*<[^>]*>\s*(\d+)|Trials?\s*:\s*(\d+)", c.badge)
    badge_n = int(m.group(1) or m.group(2)) if m else None
    if seen is not None and c.k and int(seen) != c.k:
        out.append(f"__verdict.n_trials_seen={seen} vs realData k={c.k}")
    if badge_n is not None and seen is not None and badge_n != int(seen):
        out.append(f"badge 'Trials: {badge_n}' vs __verdict.n_trials_seen={seen}")
    if badge_n is not None and c.k and badge_n != c.k:
        out.append(f"badge 'Trials: {badge_n}' vs realData k={c.k}")
    if c.badge and not c.verdict:
        out.append("a visible badge with no window.__verdict — one surface asserting, one silent")
    if c.verdict and not c.badge:
        out.append("a machine verdict with no visible badge — the reader sees nothing")
    return out


@detector("RM-F03", "Badge self-contradiction", "P0")
def d_f03(c: Ctx):
    b = c.badge
    if not b:
        return []
    out = []
    for label, pat in (("trial count", r"Trials?\s*:\s*(?:<[^>]*>\s*)?(\d+)"),
                       ("internal-consistency rounds", r"(\d+)\s+internal-consistency rounds"),
                       ("k", r"\bk\s*=\s*(\d+)")):
        vals = sorted(set(re.findall(pat, b)))
        if len(vals) > 1:
            out.append(f"two {label} values in one badge: {' vs '.join(vals)}")
    return out


@detector("RM-F04", "Interface state desync", "P2")
def d_f04(c: Ctx):
    # Only APP-version tokens count. A bare `v0.4` from a vendored library is not interface drift,
    # so the token must sit next to a RapidMeta / version / engine label.
    vers = set()
    for pat in (r"RapidMeta[^<\n]{0,60}?\bv(\d+\.\d+)",
                r"\bapp[_ ]?version\b[^0-9]{0,12}v?(\d+\.\d+)",
                r"\bengine\b[^0-9<]{0,20}v(\d+\.\d+)",
                r"softwareVersion\"?\s*:\s*\"v?(\d+\.\d+)"):
        vers.update(re.findall(pat, c.text, re.I))
    out = []
    if len(vers) > 1:
        out.append(f"{len(vers)} distinct APP version tokens on RapidMeta-labelled surfaces: "
                   f"{sorted(vers)}")
    if re.search(r"living systematic review", c.text, re.I) and re.search(r"LIVING\s*:\s*NEVER", c.text, re.I):
        out.append("'Living Systematic Review' title contradicts the app's own LIVING:NEVER badge")
    return out


@detector("RM-F05", "Missing rendered as zero", "P1")
def d_f05(c: Ctx):
    out = []
    if re.search(r"Number\.isFinite\(\s*Number\(", c.text):
        out.append("`Number.isFinite(Number(x))` presence check — Number(null)===0 passes it")
    if re.search(r"\bd\.tN\s*>\s*0\b|\bt\.data\.tN\s*>\s*0\b", c.text):
        out.append("presence guard tests the DENOMINATOR only; a null numerator coerces to 0")
    for nct, t in c.trials.items():
        if t.get("tE") is None and _num(t.get("tN")):
            out.append(f"{t.get('name') or nct}: tE is null with tN={t.get('tN')} — renders as 0.0%")
            break
    return out


@detector("RM-F06", "Impossible PRISMA zeros", "P1")
def d_f06(c: Ctx):
    out = []
    # PRISMA counts are not inside a literal `prisma{...}` object — that pattern matched the CSS
    # rule `.prisma-node {`. Find any PRISMA-SHAPED object: >=2 stage keys with numeric values.
    stages = {}
    keys = ("identified", "screened", "eligible", "included")
    for m in re.finditer(r"\{[^{}]{0,600}\}", c.text):
        blob = m.group(0)
        found = {}
        for key in keys:
            mm = re.search(r"[\"']?(?:records[_ ]?)?" + key + r"[\"']?\s*:\s*(\d+)", blob, re.I)
            if mm:
                found[key] = int(mm.group(1))
        if len(found) >= 2 and len(found) > len(stages):
            stages = found
    if not stages:
        # PRISMA may be rendered by vendor/prisma-flow.js from data this sweep cannot see.
        if re.search(r"prisma-flow\.js", c.text) and c.k > 0:
            return []          # honest: not measurable statically, so do NOT report clean or dirty
    if stages.get("identified") == 0 and c.k > 0:
        out.append(f"PRISMA identified=0 while the ledger holds {c.k} trial(s) — a 0 asserts a "
                   "search that returned nothing")
    prev, prevk = None, ""
    for key in ("identified", "screened", "eligible", "included"):
        if key in stages:
            if prev is not None and stages[key] > prev:
                out.append(f"PRISMA {key}({stages[key]}) > {prevk}({prev})")
            prev, prevk = stages[key], key
    return out


@detector("RM-F07", "Unearned confidence on unsourced fields", "P1")
def d_f07(c: Ctx):
    out = []
    fr = re.search(r"[Ff]abrication[- ]risk score:?\s*<?[^>]*>?\s*(\d\.\d+)", c.badge or c.text)
    if fr and float(fr.group(1)) == 0.0:
        inc = (c.verdict.get("counts") or {}).get("P2_evidence_incomplete") or 0
        if inc:
            out.append(f"fabrication-risk {fr.group(1)} while __verdict records "
                       f"P2_evidence_incomplete={inc}")
    if re.search(r"100\s*%\s*(confidence|verified)", c.text, re.I):
        out.append("a '100% confidence/verified' claim is rendered")
    dash = len(re.findall(r'"source"\s*:\s*"(?:--|—|–|N/?A)"', c.text)) + \
        len(re.findall(r"\bsource\s*:\s*[\"'](?:--|—|–|N/?A)[\"']", c.text))
    if dash and re.search(r"\bVERIFIED\b", c.text):
        out.append(f"{dash} field(s) with a '--' source under a VERIFIED claim")
    return out


# ---------------------------------------------------------- family G

@detector("RM-G01", "safeRob unknown -> low", "P0")
def d_g01(c: Ctx):
    out = []
    if "safeRob" not in c.text:
        return out
    m = re.search(r"safeRob\s*=\s*(.{0,420})", c.text, re.S)
    seg = m.group(1) if m else ""
    if re.search(r'valid\s*\.\s*includes\s*\(\s*r\s*\)\s*\?\s*r\s*:\s*"low"', seg) or \
       re.search(r'includes\(r\)\?r:"low"', seg):
        out.append('safeRob resolves every unrecognised rating to "low" — '
                   '"some-concerns" is not in the valid list, so every Some-Concerns renders as Low Risk')
    elif re.search(r'\["low","some","high"\]', seg) and '"some-concerns"' not in seg and "some concerns" not in seg:
        out.append('safeRob\'s valid list is ["low","some","high"] and does not recognise the '
                   'curated "some-concerns" vocabulary')
    if re.search(r'\[\s*"low"\s*,\s*"low"\s*,\s*"low"', seg):
        out.append('a non-array RoB resolves to all-"low"')
    return out


@detector("RM-G02", "RoB asserted from design fields alone", "P2")
def d_g02(c: Ctx):
    # The bare word "signalling" appears in every app's i18n strings, so testing for it made this
    # detector vacuously clean. Require actual STORED domain judgements.
    if re.search(r"rob2Domains|robDomains|signallingAnswers|rob2Answers|robJudgements", c.text):
        return []
    robs = []
    for t in c.trials.values():
        r = t.get("rob")
        if isinstance(r, list) and r:
            robs.append(r)
    if robs and all(all(str(x).lower() == "low" for x in r) for r in robs):
        return [f"all {len(robs)} trial(s) carry an all-'low' RoB array with no stored RoB 2 domain answers"]
    return []


# ---------------------------------------------------------- family H

@detector("RM-H01", "k-inappropriate machinery", "P1")
def d_h01(c: Ctx):
    out = []
    k = c.k
    if k == 0:
        return out
    for panel, (mink, pats) in MACHINERY_MIN_K.items():
        if k >= mink:
            continue
        for p in pats:
            if re.search(p, c.text, re.I):
                out.append(f"{panel} rendered at k={k} (requires k>={mink})")
                break
    if k < 10 and re.search(r"\bNNT\b\s*[≈~=]", c.text):
        out.append(f"NNT derived at k={k}")
    return out


@detector("RM-H02", "Inadmissible estimator / uninterpretable tau2 at small k", "P1")
def d_h02(c: Ctx):
    out = []
    k = c.k
    if k and k < 10 and re.search(r"pooled_DL|DerSimonian", c.text, re.I):
        out.append(f"DerSimonian-Laird at k={k} (inadmissible below k=10)")
    if k and k < 3 and re.search(r"I(?:²|\^2|2)\s*=\s*0", c.text):
        out.append(f"I^2 quoted at k={k} — an artefact, not evidence of homogeneity")
    return out


@detector("RM-H03", "Fragility index where undefined", "P1")
def d_h03(c: Ctx):
    if not re.search(r"fragility", c.text, re.I):
        return []
    out = []
    if re.search(r"\bindirect\b", c.text, re.I) and re.search(r"fragility", c.text, re.I):
        if not re.search(r"fragility[^.]{0,120}(undefined|not defined|unmeasurable|N/?A)", c.text, re.I):
            out.append("a fragility index is rendered in an app carrying indirect estimates "
                       "with no 'undefined for indirect' statement")
    counted = any(_num(t.get("tE")) is not None for t in c.trials.values())
    if c.k and not counted:
        out.append("a fragility index is rendered where no trial carries an observed 2x2")
    return out


@detector("RM-H04", "N/A gate reported as a pass", "P1")
def d_h04(c: Ctx):
    out = []
    counts = c.verdict.get("counts") or {}
    if "P0_grim" in counts and counts.get("P0_grim") == 0:
        has_mean = any(
            any(_num(r.get("md")) is not None or _num(r.get("mean")) is not None for r in _rows(t))
            or _num(t.get("md")) is not None
            for t in c.trials.values())
        if c.k and not has_mean:
            out.append("P0_grim=0 on an all-binary ledger — GRIM is N/A (no mean of a bounded "
                       "integer scale to reconstruct); a 0 reads as a pass")
    if re.search(r"[Bb]enford", c.text):
        digits = sum(1 for t in c.trials.values() for f in ("tE", "tN", "cE", "cN")
                     if _num(t.get(f)) is not None)
        if 0 < digits < 30 and not re.search(r"[Bb]enford[^.]{0,80}(underpowered|N/?A|cannot test)", c.text):
            out.append(f"a Benford verdict on {digits} values (needs >=30) with no UNDERPOWERED label")
    return out


@detector("RM-H05", "External-validation claim vs a different-scope benchmark", "P1")
def d_h05(c: Ctx):
    out = []
    if not re.search(r"externally validated|PUBLISHED_META_BENCHMARKS", c.text, re.I):
        return out
    m = re.search(r"BENCHMARK_OUTCOME_MAP\s*=\s*\{(.{0,400}?)\}", c.text, re.S)
    if m:
        body = m.group(1)
        if re.search(r"\b(ACM|ALLCAUSE|all_cause)\b", body) and re.search(r"\bMACE\b", body):
            out.append("BENCHMARK_OUTCOME_MAP routes an all-cause-mortality scope onto a MACE "
                       "(composite) benchmark")
    mb = re.search(r"MACE\s*:\s*\{(.{0,400}?)\}", c.text, re.S)
    if mb:
        kk = re.search(r"\bk\s*:\s*(\d+)", mb.group(1))
        scope = re.search(r"scope\s*:\s*[\"']([^\"']{0,80})", mb.group(1))
        if kk and scope:
            named = len(re.findall(r"[A-Z][A-Z-]{3,}", scope.group(1)))
            if named and named != int(kk.group(1)):
                out.append(f"benchmark k={kk.group(1)} against {named} trials named in its own "
                           f"scope string {scope.group(1)!r}")
    return out


# ---------------------------------------------------------- family I

@detector("RM-I01", "Direction inversion risk (no explicit polarity)", "P1")
def d_i01(c: Ctx):
    out = []
    if c.k == 0:
        return out
    if not re.search(r"\bpolarity\b", c.text):
        out.append(f"no outcome row carries an explicit polarity across {c.k} trial(s) — an OR<1 on "
                   "a GOOD outcome cannot be distinguished from an OR<1 on a bad one")
    if re.search(r"\bNNH\b", c.text) and not re.search(r"\bpolarity\b", c.text):
        out.append("an NNH is rendered with no polarity field to justify the direction")
    return out


# ---------------------------------------------------------- family J

@detector("RM-J01", "False ICMJE / PROSPERO equivalence attribution", "P0")
def d_j01(c: Ctx):
    out = []
    for m in re.finditer(r"ICMJE", c.text):
        out.append("ICMJE attribution: " + re.sub(r"\s+", " ", c.text[max(0, m.start() - 90):m.start() + 130])[:200])
        break
    if re.search(r"(equivalent\s+to|constitutes?\s+a[^.<]{0,60}equivalent)[^.<]{0,60}PROSPERO", c.text, re.I) or \
       re.search(r"PROSPERO[^.<]{0,40}\bequivalen", c.text, re.I):
        out.append("a literal PROSPERO-equivalence label is asserted")
    return out


@detector("RM-J02", "Retrospective protocol framed as prospective", "P1")
def d_j02(c: Ctx):
    stripped = re.sub(r"\b(not|never|is not|was not)\s+prospectively\s+registered\b", "", c.text, flags=re.I)
    out = []
    if re.search(r"\bprospectively\s+registered\b", stripped, re.I):
        if re.search(r"[Rr]etrospective", c.text):
            out.append("a prospective-registration claim co-occurs with an admission that the "
                       "protocol is retrospective")
    if re.search(r"Retrospective Public Protocol Pack", c.text, re.I):
        out.append("'Retrospective Public Protocol Pack (OSF-ready)' is presented as a registration artefact")
    return out


@detector("RM-J05", "COMPLETED-only registry filter", "P2")
def d_j05(c: Ctx):
    out = []
    if re.search(r"overallStatus[^,\n]{0,40}COMPLETED|status\s*[:=]\s*[\"']COMPLETED[\"']|AREA\[OverallStatus\]COMPLETED", c.text):
        if not re.search(r"TERMINATED|WITHDRAWN|SUSPENDED", c.text):
            out.append("the stored registry query filters to COMPLETED with no TERMINATED/WITHDRAWN "
                       "— a trial stopped early for harm would be excluded")
    return out


# ============================================================== v2 detector pack
# Detectors added after the mitral-TEER / PCSK9 / bempedoic-acid calibration cases live in their
# own module. Imported for its side effects: each @detector call registers into DETECTORS/META.
try:
    import rapidmeta_error_sweep_v2  # noqa: F401,E402
except ImportError as _e:            # fail loud - a missing pack means a silently smaller sweep
    raise SystemExit("v2 detector pack failed to import: " + str(_e))


# ============================================================== runner

def read_text(p: Path) -> str:
    b = p.read_bytes()
    for enc in ("utf-8-sig", "utf-8", "cp1252"):
        try:
            return b.decode(enc)
        except UnicodeDecodeError:
            continue
    return b.decode("utf-8", errors="replace")


STUB_MAX = 20000  # bytes; below this the file is a redirect stub, not an app


def sweep(files, only=None, verbose=False):
    ids = [only] if only else list(DETECTORS)
    # Keyed by RELATIVE PATH, never basename: 17 basenames occur twice in this repo (an app in the
    # root and a stale copy under e156-submission/assets), and basename keying silently overwrote
    # the root app's result with the copy's.
    results, errors, stubs, unparsed = {}, {}, [], {}
    for n, p in enumerate(files, 1):
        key = str(p.relative_to(ROOT)).replace("\\", "/")
        try:
            text = read_text(p)
        except OSError as e:
            errors[key] = f"read: {e}"
            continue
        if len(text) < STUB_MAX:
            stubs.append(key)
            continue
        c = Ctx(p, text)
        hits = {}
        for eid in ids:
            try:
                ev = DETECTORS[eid](c)
            except Exception as e:                    # a detector crash is a finding about the detector
                errors.setdefault(key, "")
                errors[key] += f"{eid}:{type(e).__name__}:{e}; "
                continue
            if ev:
                hits[eid] = ev
        if c.parse_errors:                            # fail loud, never silently blind
            unparsed[key] = c.parse_errors
        results[key] = {"app": p.name, "k": c.k, "title": c.title[:140], "bytes": len(text),
                        "ledger_parse_errors": c.parse_errors, "hits": hits}
        if verbose and n % 100 == 0:
            print(f"  ... {n}/{len(files)}", flush=True)
    return results, errors, stubs, unparsed


SELFTEST_CASES = [
    ("RM-G01", "<html>"+"x"*20001+"<script>safeRob=rob=>{const valid=[\"low\",\"some\",\"high\"];"
     "return Array.isArray(rob)?rob.map(r=>valid.includes(r)?r:\"low\"):[\"low\",\"low\",\"low\"]}</script>", True),
    ("RM-G01", "<html>"+"x"*20001+"<script>safeRob=rob=>rob.map(r=>ALIASES[r]||\"some\")</script>", False),
    ("RM-F01", "<html>"+"x"*20001+"<script>window.__verdict = {\"verdict\": \"UNCERTAIN\", "
     "\"counts\": {\"n_trials_seen\": 0}, \"reasons\": [\"x\"]};</script>"
     "<div id=\"rapidmeta-integrity-badge\" style=\"background:#15803d\">INTERNAL CHECKS PASSED</div>", True),
    ("RM-F01", "<html>"+"x"*20001+"<script>window.__verdict = {\"verdict\": \"STABLE\", "
     "\"counts\": {\"n_trials_seen\": 4}, \"reasons\": []};</script>"
     "<div id=\"rapidmeta-integrity-badge\" style=\"background:#7c2d12\">VERDICT: UNCERTAIN</div>", False),
    ("RM-F03", "<html>"+"x"*20001+"<div id=\"rapidmeta-integrity-badge\">Trials: 28 ... "
     "10 internal-consistency rounds ... 14 internal-consistency rounds</div>", True),
    ("RM-A02", "<html>"+"x"*20001+"<script>var q = \"RR\" !== String(d?.estimandType ?? \"HR\");</script>", True),
    ("RM-E02", "<html>"+"x"*20001+"<title>RapidMeta | Rifapentine for latent tuberculosis</title>"
     "<script>KNOWN_TRIAL_ALIASES={NCT01035255:[\"paradigm-hf\"],NCT01920711:[\"paragon-hf\"],"
     "NCT02924727:[\"paradise-mi\"],NCT03988634:[\"paraglide-hf\"]}</script>", True),
    ("RM-E02", "<html>"+"x"*20001+"<title>RapidMeta | Sacubitril/valsartan in heart failure</title>"
     "<script>KNOWN_TRIAL_ALIASES={NCT01035255:[\"paradigm-hf\"],NCT01920711:[\"paragon-hf\"]}</script>", False),
    ("RM-J01", "<html>"+"x"*20001+"<p>Per ICMJE 2023, the commit hash constitutes a record.</p>", True),
    ("RM-B02", "<html>"+"x"*20001+"<script>/* COMPLETE-POOLING-REPAIR (2026-06) */</script>", True),
    ("RM-A07", "<html>"+"x"*20001+"<script>var realData={NCT02329327:{name:\"Siegal 2015\","
     "pubHR:0.80,hrLCI:-0.5509,hrUCI:2.1509}};</script>", True),
    ("RM-A01", "<html>"+"x"*20001+"<script>var realData={NCT03521934:{name:\"SOLOIST-WHF\","
     "estimandType:\"RR\",tE:245,tN:608,cE:355,cN:614}};</script>", True),
]


def selftest():
    print("=" * 78)
    print("SWEEP DETECTOR SELF-TEST — every detector must fire on a seeded defect and stay silent on a clean file")
    print("=" * 78)
    ok = True
    for i, (eid, html, expect_hit) in enumerate(SELFTEST_CASES, 1):
        c = Ctx(Path(f"selftest_{i}_REVIEW.html"), html)
        ev = DETECTORS[eid](c)
        got = bool(ev)
        good = got == expect_hit
        ok &= good
        print(f"[{i:2d}] {eid:8s} expect={'HIT ' if expect_hit else 'CLEAN'} "
              f"got={'HIT ' if got else 'CLEAN'}  {'OK' if good else 'FAIL'}"
              + (f"   -> {ev[0][:90]}" if ev else ""))
    print("-" * 78)
    print("VERDICT:", "SELFTEST PASS" if ok else "SELFTEST FAIL")
    print("=" * 78)
    return 0 if ok else 1


def write_reports(results, errors, stubs, unparsed, files_scanned, out_md: Path, out_json: Path):
    per_type = defaultdict(list)
    for app, r in results.items():
        for eid, ev in r["hits"].items():
            per_type[eid].append((app, len(ev), ev))

    n_apps = len(results)
    payload = {
        "generated": "2026-07-30",
        "registry": "RAPIDMETA_ERROR_REGISTRY.md v1.0",
        "read_only": True,
        "corpus": {
            "files_matched": files_scanned,
            "apps_scanned": n_apps,
            "stubs_skipped": len(stubs),
            "detector_errors": len(errors),
            "apps_with_unparsable_ledger": len(unparsed),
        },
        "unparsable_ledgers": unparsed,
        "detectors": {eid: META[eid] for eid in DETECTORS},
        "prevalence": {
            eid: {
                "name": META[eid]["name"], "severity": META[eid]["severity"],
                "apps_affected": len(per_type.get(eid, [])),
                "pct_of_apps": round(100 * len(per_type.get(eid, [])) / n_apps, 1) if n_apps else 0.0,
                "total_evidence_items": sum(x[1] for x in per_type.get(eid, [])),
                "worst_offenders": [
                    {"app": a, "evidence_count": n, "evidence": ev[:3]}
                    for a, n, ev in sorted(per_type.get(eid, []), key=lambda x: -x[1])[:5]
                ],
            } for eid in DETECTORS
        },
        "matrix": {app: sorted(r["hits"].keys()) for app, r in sorted(results.items()) if r["hits"]},
        "apps": results,
        "errors": errors,
        "stubs_skipped": sorted(stubs),
    }
    out_json.write_text(json.dumps(payload, indent=1, ensure_ascii=False), encoding="utf-8")

    order = sorted(DETECTORS, key=lambda e: (-len(per_type.get(e, [])), e))
    clean = sum(1 for r in results.values() if not r["hits"])
    worst_apps = sorted(results.items(), key=lambda kv: -len(kv[1]["hits"]))[:25]
    p0 = [e for e in order if META[e]["severity"] == "P0" and per_type.get(e)]

    L = []
    L.append("# RAPIDMETA ERROR SWEEP\n")
    L.append("**Generated:** 2026-07-30 · **Registry:** `RAPIDMETA_ERROR_REGISTRY.md` v1.0 · "
             "**Mode:** READ-ONLY DETECTION — no file was modified.\n")
    L.append("**Command:** `python scripts/rapidmeta_error_sweep.py`\n")
    L.append("Every STATIC detector in the registry applied to every `*_REVIEW.html` in the repo. "
             "SOURCE- and RENDER-class detectors are **not** in these counts — they need a registry "
             "lookup or a browser, and their absence is a limit of this sweep, not a clean result.\n")
    L.append("## 1. Corpus\n")
    L.append("| | count |\n|---|---:|")
    L.append(f"| `*_REVIEW.html` files matched | {files_scanned} |")
    L.append(f"| Apps scanned (>= {STUB_MAX//1000} KB) | {n_apps} |")
    L.append(f"| Redirect stubs skipped (< {STUB_MAX//1000} KB) | {len(stubs)} |")
    L.append(f"| Apps with **zero** static findings | {clean} ({100*clean/n_apps:.1f}%) |" if n_apps else "")
    L.append(f"| Apps with >= 1 finding | {n_apps-clean} ({100*(n_apps-clean)/n_apps:.1f}%) |" if n_apps else "")
    L.append(f"| Detectors run | {len(DETECTORS)} |")
    L.append(f"| Files where a detector raised | {len(errors)} |")
    L.append(f"| **Apps whose `realData` ledger did not parse** (ledger detectors blind there) | "
             f"**{len(unparsed)}** |\n")
    if unparsed:
        L.append("> A ledger that does not parse is a **finding about the app**, not a clean "
                 "result. Every `RM-A*`, `RM-C*`, `RM-D*` and `RM-G02` count below is measured on "
                 f"{n_apps - len(unparsed)} apps, not {n_apps}. Full list in the JSON "
                 "(`unparsable_ledgers`).\n")

    L.append("## 2. Prevalence — apps affected per error type\n")
    L.append("| id | error type | sev | apps | % of apps | evidence items |")
    L.append("|---|---|---|---:|---:|---:|")
    for eid in order:
        rows = per_type.get(eid, [])
        pct = (100 * len(rows) / n_apps) if n_apps else 0
        L.append(f"| `{eid}` | {META[eid]['name']} | {META[eid]['severity']} | "
                 f"{len(rows)} | {pct:.1f}% | {sum(x[1] for x in rows)} |")
    L.append("")

    if p0:
        L.append("### 2a. P0 types, by prevalence\n")
        L.append("| id | error type | apps | % |")
        L.append("|---|---|---:|---:|")
        for eid in p0:
            rows = per_type[eid]
            L.append(f"| `{eid}` | {META[eid]['name']} | {len(rows)} | "
                     f"{100*len(rows)/n_apps:.1f}% |")
        L.append("")

    L.append("## 3. Worst offenders per type\n")
    for eid in order:
        rows = per_type.get(eid, [])
        if not rows:
            continue
        L.append(f"### `{eid}` — {META[eid]['name']} ({len(rows)} apps, {META[eid]['severity']})\n")
        for app, n, ev in sorted(rows, key=lambda x: -x[1])[:5]:
            L.append(f"- **{app}** ({n} item{'s' if n != 1 else ''})")
            for e in ev[:2]:
                L.append(f"  - {e[:300]}")
        L.append("")

    L.append("## 4. Worst offenders overall — apps by distinct error types\n")
    L.append("| app | distinct error types | k | ids |")
    L.append("|---|---:|---:|---|")
    for app, r in worst_apps:
        if not r["hits"]:
            continue
        L.append(f"| `{app}` | {len(r['hits'])} | {r['k']} | " +
                 ", ".join(f"`{e}`" for e in sorted(r["hits"])) + " |")
    L.append("")

    if errors:
        L.append("## 5. Detector errors (recorded, not hidden)\n")
        for app, e in list(errors.items())[:30]:
            L.append(f"- `{app}`: {e[:220]}")
        if len(errors) > 30:
            L.append(f"- ... and {len(errors)-30} more (full list in the JSON)")
        L.append("")

    L.append("## 6. What this sweep cannot see\n")
    L.append("- **SOURCE-class detectors** (RM-A06 rate-as-proportion, RM-B04 outcome substitution, "
             "RM-B05 omitted trial, RM-B06 PICO mismatch, RM-B07 arm dropping, RM-C02 arm-as-overall, "
             "RM-C03 arm orientation, RM-D03 protocol-paper citation, RM-D04 fabricated counts, "
             "RM-H06 NI margin, RM-J03 eligibility contradiction) need a registry/PubMed lookup per "
             "trial. A zero here is **not** a clean result for those types.")
    L.append("- **RENDER-class detectors** (RM-B02 Defect 4, RM-F08 hidden sensitivity interval) need "
             "the app served and driven in-browser. The HFrEF badge contradiction was found by "
             "rendering, after a file-level gate had passed it.")
    L.append("- **Redirect stubs** are excluded from the denominator. A fix applied to one variant is "
             "not applied to the app (RECIPE-C 0.2) — variant consistency is a separate check.")
    L.append("- A detector that fires is a **hypothesis**, not a proven defect. The HFrEF pass "
             "withdrew three of its five findings on verification.\n")
    out_md.write_text("\n".join(L) + "\n", encoding="utf-8")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--only", help="run a single detector id, e.g. RM-F01")
    ap.add_argument("--limit", type=int, help="scan only the first N files")
    ap.add_argument("--selftest", action="store_true", help="prove every seeded detector can fire")
    ap.add_argument("--root", default=str(ROOT))
    args = ap.parse_args()

    if args.selftest:
        return selftest()
    if args.only and args.only not in DETECTORS:
        print(f"unknown detector {args.only}; known: {', '.join(sorted(DETECTORS))}")
        return 2

    root = Path(args.root)
    files = sorted(root.glob("*_REVIEW.html"))
    files += sorted(p for p in root.rglob("*_REVIEW.html")
                    if p.parent != root and ".git" not in p.parts)
    if args.limit:
        files = files[:args.limit]
    print(f"scanning {len(files)} *_REVIEW.html file(s) with "
          f"{1 if args.only else len(DETECTORS)} detector(s) ...", flush=True)

    results, errors, stubs, unparsed = sweep(files, only=args.only, verbose=True)
    write_reports(results, errors, stubs, unparsed, len(files),
                  root / "RAPIDMETA_ERROR_SWEEP.md", root / "RAPIDMETA_ERROR_SWEEP.json")

    n = len(results)
    flagged = sum(1 for r in results.values() if r["hits"])
    print(f"\napps scanned: {n}  (stubs skipped: {len(stubs)}, detector errors: {len(errors)}, "
          f"unparsable ledgers: {len(unparsed)})")
    print(f"apps with >=1 finding: {flagged} ({100*flagged/n:.1f}%)" if n else "")
    per = Counter()
    for r in results.values():
        per.update(r["hits"].keys())
    print("\ntop error types by apps affected:")
    for eid, cnt in per.most_common(15):
        print(f"  {eid:8s} {META[eid]['severity']:3s} {cnt:5d}  {100*cnt/n:5.1f}%  {META[eid]['name']}")
    print("\nwrote RAPIDMETA_ERROR_SWEEP.md and RAPIDMETA_ERROR_SWEEP.json")
    return 0


if __name__ == "__main__":
    sys.exit(main())
