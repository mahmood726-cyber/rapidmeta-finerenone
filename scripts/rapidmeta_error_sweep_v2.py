#!/usr/bin/env python
"""
RapidMeta error sweep — v2 detector pack.

Imported by scripts/rapidmeta_error_sweep.py. Holds the detectors added after the
mitral-TEER, PCSK9 and bempedoic-acid calibration cases (2026-07-30). Kept in its own module so
the v1 pack stays reviewable; both register into the same DETECTORS/META tables.

Every detector here was written against a real offending string in one of those three apps.
"""
from __future__ import annotations

import json
import re

import sys as _sys


def _base_module():
    """Bind to the base pack that is ALREADY loaded rather than importing a second copy.

    When the sweep runs as a script the base pack is `__main__`; a fresh `import
    rapidmeta_error_sweep` would execute it a second time under another name, duplicating its
    module-level side effects. Defence in depth alongside the idempotent stdout wrap.
    """
    for name in ("rapidmeta_error_sweep", "__main__"):
        m = _sys.modules.get(name)
        if m is not None and hasattr(m, "DETECTORS") and hasattr(m, "detector"):
            return m
    import rapidmeta_error_sweep as m  # noqa: E402  - genuine first load
    return m


_BASE = _base_module()
Ctx = _BASE.Ctx
detector = _BASE.detector
_num = _BASE._num
_rows = _BASE._rows
CLAIM_SLOT_RE = _BASE.CLAIM_SLOT_RE


# --------------------------------------------------------------------------- helpers

def _crude_rr(tE, tN, cE, cN):
    tE, tN, cE, cN = (_num(x) for x in (tE, tN, cE, cN))
    if None in (tE, tN, cE, cN) or tN <= 0 or cN <= 0 or cE <= 0:
        return None
    return (tE / tN) / (cE / cN)


# Percentages a Kaplan-Meier estimate is reported as. A KM % is a MODEL-BASED cumulative
# incidence under censoring; it is not events/N and must never be multiplied back by N.
KM_CONTEXT_RE = re.compile(
    r"(kaplan[- ]?meier|KM (estimate|rate|event rate)|cumulative incidence|"
    r"event rate at \d+ (month|year)|estimated \d+-(month|year) (rate|incidence))", re.I)
RATE_PER_PT_YR_RE = re.compile(
    r"(per|/)\s*100\s*(patient|person|pt)[- ]?years?|annuali[sz]ed (event )?rate|"
    r"events? per 100 (patient|person)[- ]?years?", re.I)


def _evidence_text(t: dict) -> str:
    """All prose the app displays for a trial: evidence rows, snippet, highlights."""
    parts = [str(t.get("snippet") or "")]
    ev = t.get("evidence")
    if isinstance(ev, list):
        for e in ev:
            if isinstance(e, dict):
                parts.append(str(e.get("text") or ""))
                parts.append(str(e.get("label") or ""))
    return " ".join(parts)


def _highlight_counts(t: dict):
    """Count/denominator pairs the app highlights in its own evidence prose."""
    out = []
    ev = t.get("evidence")
    if not isinstance(ev, list):
        return out
    for e in ev:
        if not isinstance(e, dict):
            continue
        hl = e.get("highlights")
        if isinstance(hl, list):
            nums = [_num(h) for h in hl if _num(h) is not None]
            if len(nums) >= 4:
                out.append((nums[0], nums[1], nums[2], nums[3], str(e.get("text") or "")[:220]))
    return out


# =========================================================== A10 KM read as a crude count

@detector("RM-A10", "Kaplan-Meier risk rendered as a crude event count", "P0")
def d_a10(c: Ctx):
    """A KM % (or a per-100-patient-year rate) multiplied by N to manufacture per-arm counts.

    A KM estimate is a model-based cumulative incidence under censoring. events = KM% x N is not
    a count of anything; the true numerator is smaller (COAPT) or on a different scale entirely.
    """
    out = []
    for nct, t in c.trials.items():
        text = _evidence_text(t)
        km = KM_CONTEXT_RE.search(text)
        rate = RATE_PER_PT_YR_RE.search(text)
        if not (km or rate):
            continue
        for r in _rows(t) + [t]:
            if not isinstance(r, dict):
                continue
            tE, tN, cE, cN = (_num(r.get(k)) for k in ("tE", "tN", "cE", "cN"))
            if None in (tE, tN, cE, cN) or tN <= 0 or cN <= 0:
                continue
            # A KM percentage reproduced by count/N to within half a point is the signature.
            for pm in re.finditer(r"(\d{1,2}\.\d)\s*%", text):
                pct = float(pm.group(1))
                for e, n, arm in ((tE, tN, "treatment"), (cE, cN, "control")):
                    if abs(100.0 * e / n - pct) <= 0.5:
                        out.append(
                            f"{t.get('name') or nct}: {arm} {int(e)}/{int(n)} = {100.0*e/n:.1f}% "
                            f"reproduces the {pct}% figure, and the source states it as "
                            f"{'a Kaplan-Meier estimate' if km else 'a per-patient-year rate'} "
                            f"— \"{re.sub(r'\\s+', ' ', text[max(0, (km or rate).start()-40):(km or rate).start()+90]).strip()[:130]}\"")
                        break
                if out:
                    break
            if out:
                break
        if len(out) >= 4:
            break
    return out


# ==================================================== A12 effect contradicts its own 2x2

@detector("RM-A12", "Effect estimate contradicts its own 2x2", "P0")
def d_a12(c: Ctx):
    """The displayed effect sits on the opposite side of 1 from the crude ratio of the counts
    displayed beside it. Distinct from RM-A08 (which is a wrong count/effect PAIRING): here the
    effect is simply not derivable from these counts at all."""
    out = []
    for nct, t in c.trials.items():
        eff = _num(t.get("publishedHR")) if t.get("publishedHR") is not None else _num(t.get("pubHR"))
        if eff is None or eff <= 0:
            continue
        rr = _crude_rr(t.get("tE"), t.get("tN"), t.get("cE"), t.get("cN"))
        src = "ledger counts"
        if rr is None:
            for a, b, cc, dd, txt in _highlight_counts(t):
                rr = _crude_rr(a, b, cc, dd)
                if rr is not None:
                    src = f'displayed evidence "{re.sub(r"\\s+", " ", txt)[:120]}"'
                    break
        if rr is None:
            continue
        if (rr - 1) * (eff - 1) < 0 and abs(rr - 1) > 0.05 and abs(eff - 1) > 0.05:
            out.append(f"{t.get('name') or nct}: displayed effect {eff} vs crude ratio "
                       f"{rr:.3f} from {src} — opposite sides of 1")
    return out


# ============================================ A13 composite component sets differ across rows

MACE3_RE = re.compile(r"(cv|cardiovascular) death[^.,;]{0,30}(nonfatal )?mi[^.,;]{0,30}stroke", re.I)
REVASC_RE = re.compile(r"revascular", re.I)
UA_RE = re.compile(r"unstable angina", re.I)
CHD_DEATH_RE = re.compile(r"chd death|coronary heart disease death", re.I)


@detector("RM-A13", "Estimand-granularity mismatch: composite component sets differ", "P0")
def d_a13(c: Ctx):
    """MACE-3 pooled with MACE-4, or composites whose component sets differ, under one scope
    label. The trials are each correctly extracted; the POOL is of different constructs."""
    out = []
    sigs = {}
    for nct, t in c.trials.items():
        for r in _rows(t):
            if str(r.get("type", "")).upper() != "PRIMARY":
                continue
            title = str(r.get("title") or "")
            if not title:
                continue
            sig = (bool(REVASC_RE.search(title)), bool(UA_RE.search(title)),
                   bool(CHD_DEATH_RE.search(title)))
            sigs.setdefault(sig, []).append(f"{t.get('name') or nct}: \"{title[:90]}\"")
    if len(sigs) > 1:
        parts = []
        for sig, names in sigs.items():
            comp = "+".join([n for n, on in zip(("revasc", "unstable-angina", "CHD-death"), sig) if on]) or "core-3"
            parts.append(f"[{comp}] " + "; ".join(names[:2]))
        out.append("primary composites with DIFFERENT component sets are pooled under one scope: "
                   + " || ".join(parts))
    return out


# ================================= A14 the escalc smoking gun: cross-endpoint binary pooling

@detector("RM-A14", "escalc(measure=RR) over rows the ledger tags as different endpoints", "P0")
def d_a14(c: Ctx):
    """The generated R code builds ai/ci from trials.map(t=>t.data.tE) across EVERY included
    trial, regardless of what endpoint or timepoint each row actually is. Rendered, it emits a
    literal vector of three different constructs pooled as one binary RR."""
    out = []
    if not re.search(r"escalc\(\s*measure\s*=", c.text):
        return out
    gen = re.search(r"ai\s*=\s*c\(\$\{trials\.map\([^)]{0,60}\)", c.text)
    titles, tps = [], set()
    for nct, t in c.trials.items():
        for r in _rows(t):
            if str(r.get("type", "")).upper() == "PRIMARY":
                title = str(r.get("title") or "")
                titles.append(f"{t.get('name') or nct}: \"{title[:70]}\" (tE={r.get('tE')}, cE={r.get('cE')})")
                m = re.search(r"at\s+(\d+)\s*(month|year|week)", title, re.I)
                tps.add(m.group(0).lower() if m else "unstated")
                break
    if gen and len(titles) >= 2:
        distinct = len({t.split(': ', 1)[1] for t in titles})
        if distinct > 1 or len(tps) > 1:
            out.append("the generated R builds `ai = c(${trials.map(t=>t.data.tE)})` and pools it "
                       "with escalc(measure=RR) across primaries that are NOT the same construct: "
                       + " | ".join(titles[:4]))
            if len(tps) > 1:
                out.append("timepoints mixed in one binary pool: " + ", ".join(sorted(tps)))
    return out


# ============================================================ C04 arm reversal (device/control)

@detector("RM-C04", "Arm reversal: intervention and control denominators swapped", "P0")
def d_c04(c: Ctx):
    """RM-C03's registry-verified form is SOURCE-class. This is its STATIC form: the app's own
    displayed evidence names an arm size that matches the OTHER arm's ledger denominator."""
    out = []
    for nct, t in c.trials.items():
        tN, cN = _num(t.get("tN")), _num(t.get("cN"))
        if None in (tN, cN) or tN == cN:
            continue
        text = _evidence_text(t)
        if not text:
            continue
        # "<device/intervention word> ... N" patterns
        for m in re.finditer(r"(device|intervention|treatment|TEER|MitraClip|implant)[^.;]{0,80}?\b(\d{2,5})\b",
                             text, re.I):
            n = _num(m.group(2))
            if n is None:
                continue
            if abs(n - cN) < 1 and abs(n - tN) >= 1:
                out.append(f"{t.get('name') or nct}: evidence names the intervention arm as n={int(n)}, "
                           f"which is the ledger's CONTROL denominator (tN={int(tN)}, cN={int(cN)}) "
                           f"— \"{re.sub(r'\\s+', ' ', m.group(0))[:110]}\"")
                break
    return out


# ================================================== D07 false "no external benchmark exists"

@detector("RM-D07", "False claim that no external benchmark exists", "P2")
def d_d07(c: Ctx):
    out = []
    claims = re.search(r"no (external )?(published )?(benchmark|synthesis|meta-analysis)[^.<]{0,60}"
                       r"(exist|available|found|identified)|benchmark[^.<]{0,30}not (available|found|established)",
                       c.text, re.I)
    if not claims:
        return out
    has_bench = re.search(r"PUBLISHED_META_BENCHMARKS\s*=\s*\{\s*\w", c.text)
    if not has_bench:
        return out          # no benchmark stored -> the claim may simply be true
    # The string is a RENDER-TIME FALLBACK (`benchmark?.summary ?? "No published benchmark
    # available."`). Whether a reader sees it depends on BENCHMARK_OUTCOME_MAP coverage, so this
    # is a RENDER-confirm finding, not a proven false claim. Report it as such.
    unmapped = []
    mm = re.search(r"BENCHMARK_OUTCOME_MAP\s*=\s*\{([^}]{0,600})\}", c.text, re.S)
    mapped = set(re.findall(r"[\"']?(\w+)[\"']?\s*:", mm.group(1))) if mm else set()
    for r in [row for t in c.trials.values() for row in _rows(t)]:
        sl = str(r.get("shortLabel") or "")
        if sl and sl not in mapped:
            unmapped.append(sl)
    out.append("a 'No published benchmark available' fallback ships while "
               "PUBLISHED_META_BENCHMARKS is populated — RENDER-confirm which scopes hit the "
               "fallback" + (f"; scopes absent from BENCHMARK_OUTCOME_MAP: {sorted(set(unmapped))[:6]}"
                             if unmapped else ""))
    return out


# =============================================== D08 registry-status assertions vs the record

@detector("RM-D08", "False registry-status claim", "P1")
def d_d08(c: Ctx):
    """'0/N posted CT.gov results', 'no linked publications', 'all endpoints match the registered
    primary' — assertions about the registry that the registry contradicts."""
    out = []
    m = re.search(r"(\d+)\s*/\s*(\d+)\s*(tracked )?(records? )?(have )?posted", c.text, re.I)
    if m and m.group(1) == "0" and int(m.group(2) or 0) > 0:
        out.append(f"asserts 0/{m.group(2)} records have posted CT.gov results — verify each NCT; "
                   "posted results are common for landmark CVOTs and device RCTs")
    if re.search(r"no linked publications?", c.text, re.I):
        pmids = sum(1 for t in c.trials.values() if str(t.get("pmid") or "").strip())
        if pmids > 0:          # 0 PMIDs is not a contradiction - it is a different finding (RM-D02)
            out.append(f"asserts 'no linked publications' while the ledger itself carries {pmids} PMID(s)")
    if re.search(r"all endpoints match[^.<]{0,40}registered primary", c.text, re.I):
        sel = re.search(r"(all-cause mortality|overall survival)", c.text, re.I)
        if sel:
            out.append("asserts 'all endpoints match the registered primary' while the selectable "
                       "scope includes all-cause mortality, which is a registered SECONDARY in "
                       "these trials")
    return out


# ================================================ D09 phase mislabel on device/behavioural RCTs

DEVICE_RE = re.compile(r"\b(TEER|MitraClip|transcatheter|device|implant|stent|catheter|ablation|"
                       r"valve|pacemaker|defibrillator)\b", re.I)


@detector("RM-D09", "Phase label inapplicable to a device or behavioural trial", "P1")
def d_d09(c: Ctx):
    """ClinicalTrials.gov records device and behavioural RCTs as phase 'NA'. A ledger asserting
    Phase III/IV is wrong, AND a phase-III/IV eligibility rule would wrongly exclude the trial."""
    out = []
    topic_is_device = bool(DEVICE_RE.search(c.title)) or any(
        DEVICE_RE.search(str(t.get("group") or "")) for t in c.trials.values())
    for nct, t in c.trials.items():
        ph = str(t.get("phase") or "").strip().upper().replace("PHASE", "").strip()
        if ph not in ("I", "II", "III", "IV", "1", "2", "3", "4"):
            continue
        blob = (str(t.get("name") or "") + " " + str(t.get("group") or "") + " " + _evidence_text(t))
        if topic_is_device or DEVICE_RE.search(blob):
            out.append(f"{t.get('name') or nct}: ledger phase '{t.get('phase')}' on a device trial "
                       "— ClinicalTrials.gov records these as phase Not Applicable; a phase-III/IV "
                       "eligibility rule would wrongly exclude it")
    return out


# ================================================= D10 duplicate / NULLED / ghost trial rows

@detector("RM-D10", "Duplicate, NULLED or ghost trial rows", "P0")
def d_d10(c: Ctx):
    out = []
    keys = list(c.realdata.keys())
    nulled = [k for k in keys if str(k).upper().startswith("NULLED")]
    for k in nulled:
        bare = re.sub(r"^NULLED:?", "", str(k))
        out.append(f"row key '{k}' is a NULLED placeholder"
                   + (f", and the bare id {bare} is also referenced elsewhere in the file"
                      if bare and bare in c.text.replace(str(k), "") else ""))
    ncts = [re.sub(r"^NULLED:?", "", str(k)) for k in keys]
    seen = {}
    for n in ncts:
        seen[n] = seen.get(n, 0) + 1
    for n, cnt in seen.items():
        if cnt > 1:
            out.append(f"{n} appears as {cnt} separate ledger rows")
    m = re.search(r"Trials?\s*:\s*(?:<[^>]*>\s*)?(\d+)", c.badge or "")
    if m:
        distinct = len({n for n in ncts if re.fullmatch(r"NCT\d{8}", n)})
        if distinct and int(m.group(1)) != distinct:
            out.append(f"badge claims 'Trials: {m.group(1)}' against {distinct} distinct NCT(s) "
                       f"in a {len(keys)}-row ledger")
    # per-trial duplicate outcome rows
    for nct, t in c.trials.items():
        rows = _rows(t)
        sigs = [json.dumps({k: r.get(k) for k in ("shortLabel", "title", "tE", "cE")}, sort_keys=True,
                           default=str) for r in rows]
        dupes = {s for s in sigs if sigs.count(s) > 1}
        if dupes:
            out.append(f"{t.get('name') or nct}: {len(dupes)} outcome row(s) duplicated verbatim "
                       f"in allOutcomes")
    return out


# ========================================== D11 a published pooled estimate shown as trial-level

@detector("RM-D11", "Published pooled estimate presented as a trial-level effect", "P1")
def d_d11(c: Ctx):
    """A trial row's effect equals a benchmark's pooled estimate, or its evidence prose describes
    a pooled/meta analysis while the number is displayed as that single trial's result."""
    out = []
    bench = []
    # Only a benchmark with k>=2 is a POOLED estimate. A k=1 benchmark record IS the trial, so
    # matching it is expected, not a finding - that over-fired on FOURIER and CLEAR Outcomes.
    for m in re.finditer(r"estimate\s*:\s*(\.?\d+\.?\d*)\s*,\s*lci\s*:\s*(\.?\d+\.?\d*)\s*,"
                         r"\s*uci\s*:\s*(\.?\d+\.?\d*)\s*,\s*k\s*:\s*(\d+)", c.text):
        if _num(m.group(4)) and _num(m.group(4)) >= 2:
            bench.append(tuple(_num(m.group(i)) for i in (1, 2, 3)))
    for nct, t in c.trials.items():
        eff = _num(t.get("publishedHR"))
        lci, uci = _num(t.get("hrLCI")), _num(t.get("hrUCI"))
        if eff is None:
            continue
        for be, bl, bu in bench:
            if be is None:
                continue
            if abs(eff - be) < 1e-9 and (lci is None or bl is None or abs(lci - bl) < 0.02):
                out.append(f"{t.get('name') or nct}: trial-level effect {eff} equals a stored "
                           f"benchmark POOLED estimate {be} ({bl}-{bu})")
        txt = _evidence_text(t).lower()
        if eff is not None and re.search(r"pooled|meta-analys|two[- ]trial|combined analysis", txt):
            out.append(f"{t.get('name') or nct}: its own evidence prose describes a pooled/meta "
                       f"analysis while {eff} is displayed as this trial's effect")
    return out


# ======================================================== D12 citation metadata mismatch

@detector("RM-D12", "Citation volume/issue/page metadata mismatch", "P1")
def d_d12(c: Ctx):
    """Two different volume(issue):pages strings for the same trial inside one app is a
    self-evident mismatch; the source check itself is SOURCE-class."""
    out = []
    for nct, t in c.trials.items():
        blob = str(t.get("snippet") or "") + " " + _evidence_text(t)
        cites = set(re.findall(r"\b(\d{1,4})\s*\(\s*(\d{1,3})\s*\)\s*:\s*(\d{1,5})[-–](\d{1,5})", blob))
        if len(cites) > 1:
            out.append(f"{t.get('name') or nct}: {len(cites)} different citations for one trial: " +
                       "; ".join(f"{a}({b}):{d}-{e}" for a, b, d, e in list(cites)[:3]))
    return out


# ================================================= E03 registry watchlist is the wrong drug

WATCHLIST_TRIALS = {
    "finerenone": ["FIDELIO-DKD", "FIGARO-DKD", "FINEARTS-HF", "ARTS-DN", "FINE-ONE", "CONFIDENCE"],
    "sacubitril": ["PARADIGM-HF", "PARAGON-HF", "PARADISE-MI", "PARAGLIDE-HF"],
    "sglt2": ["DAPA-HF", "EMPEROR-Reduced", "EMPEROR-Preserved", "DELIVER", "EMPA-REG"],
}


@detector("RM-E03", "Registry/monitoring watchlist tracks the wrong drug class", "P0")
def d_e03(c: Ctx):
    """Distinct from RM-E01 (prose residue) and RM-E02 (alias table): this is the app's LIVE
    monitoring surface — the trials it says it is watching for new evidence."""
    out = []
    m = re.search(r"CTGOV_EVIDENCE_REGISTRY\s*=\s*\{", c.text)
    if not m:
        return out
    balanced_span = _BASE.balanced_span
    end = balanced_span(c.text, m.end() - 1)
    blob = c.text[m.end() - 1:end] if end > 0 else c.text[m.end() - 1:m.end() + 4000]
    topic = " ".join(c.topic_tokens)
    for owner, trials in WATCHLIST_TRIALS.items():
        if owner in topic:
            continue
        hits = [tr for tr in trials if tr.lower() in blob.lower()]
        if hits:
            labels = re.findall(r'label\s*:\s*"([^"]{1,40})"', blob)
            out.append(f"the monitored registry watchlist tracks {owner.upper()} trials {hits} in an "
                       f"app about '{c.title[:60]}' — full watchlist: {labels[:8]}")
    return out


# ============================================ B08 under-inclusion vs an external synthesis

@detector("RM-B08", "Search under-inclusion vs a known external synthesis", "P1")
def d_b08(c: Ctx):
    """k far below a synthesis the app itself cites. String-grep cannot find an ABSENT trial;
    the benchmark's own k is the only static handle on completeness."""
    out = []
    ks = [int(x) for x in re.findall(r"\bk\s*:\s*(\d{1,4})", c.text)]
    if not ks or c.k == 0:
        return out
    biggest = max(ks)
    if biggest >= max(5, 2 * c.k) and biggest > c.k:
        out.append(f"the app pools k={c.k} while a benchmark record in the same file declares "
                   f"k={biggest} — verify the search, and record an explicit include/exclude "
                   f"decision for every eligible trial (omitting one silently is selection bias)")
    return out


# ================================= G03 RoB display contradicts the app's own extraction evidence

ROB_LEVEL_RE = re.compile(r"\b(low|some[- ]concerns?|high|serious|critical|unclear|moderate)\b", re.I)
ROB_NORM = {"low": "low", "some-concerns": "some", "some concerns": "some", "unclear": "some",
            "moderate": "some", "high": "high", "serious": "high", "critical": "high"}


@detector("RM-G03", "RoB chip contradicts the trial's own extraction evidence", "P1")
def d_g03(c: Ctx):
    out = []
    for nct, t in c.trials.items():
        rob = t.get("rob")
        if not isinstance(rob, list) or not rob:
            continue
        text = _evidence_text(t)
        for m in re.finditer(r"\bD([1-5])\b[^.;]{0,40}?" + ROB_LEVEL_RE.pattern, text, re.I):
            idx = int(m.group(1)) - 1
            claimed = ROB_NORM.get(m.group(2).lower().replace("concern", "concerns").replace("concernss", "concerns"))
            if claimed is None or idx >= len(rob):
                continue
            shown = ROB_NORM.get(str(rob[idx]).lower(), str(rob[idx]).lower())
            if shown and claimed and shown != claimed:
                out.append(f"{t.get('name') or nct}: evidence says D{idx+1} = '{m.group(2)}' but the "
                           f"chart chip shows '{rob[idx]}'")
    if re.search(r"majority[^.<]{0,40}high[^.<]{0,30}D1", c.text, re.I):
        d1 = [str(t.get("rob")[0]).lower() for t in c.trials.values()
              if isinstance(t.get("rob"), list) and t.get("rob")]
        if d1 and all(x == "low" for x in d1):
            out.append(f"GRADE text claims the majority are high on D1 while the RoB table shows "
                       f"D1 = low in all {len(d1)} trials")
    return out


# ======================================== J07 integrity gate passes over a fail-closed condition

@detector("RM-J07", "Integrity gate passes over a fail-closed condition", "P0")
def d_j07(c: Ctx):
    """The verdict/badge asserts a pass while a condition that must FAIL CLOSED is present:
    a null/NULLED trial id, a NaN or impossible rendered value, or trial counts that disagree
    across surfaces."""
    out = []
    conditions = []
    if any(str(k).upper().startswith("NULLED") or not str(k).strip() for k in c.realdata):
        conditions.append("a NULLED/empty trial id in the ledger")
    if re.search(r">\s*NaN\s*<|:\s*NaN\b|NaN\s*[-–]\s*NaN", c.text):
        conditions.append("a rendered NaN")
    for nct, t in c.trials.items():
        for f in ("publishedHR", "pubHR", "hrLCI", "hrUCI"):
            v = _num(t.get(f))
            if v is not None and (v <= 0 or v > 100):
                conditions.append(f"an impossible ratio {t.get('name') or nct}.{f}={v}")
                break
    counts = set()
    seen = (c.verdict.get("counts") or {}).get("n_trials_seen")
    if seen is not None:
        counts.add(int(seen))
    if c.k:
        counts.add(c.k)
    m = re.search(r"Trials?\s*:\s*(?:<[^>]*>\s*)?(\d+)", c.badge or "")
    if m:
        counts.add(int(m.group(1)))
    if len(counts) > 1:
        conditions.append(f"trial counts disagreeing across surfaces {sorted(counts)}")
    if not conditions:
        return out
    badge = (c.badge or "").lower()
    asserts_pass = ("checks passed" in badge or "#15803d" in badge or "#0a7d33" in badge
                    or re.search(r"fabrication[- ]risk[^<]{0,40}0\.\d", badge or "")
                    or re.search(r"integrity[^<]{0,20}100", badge or ""))
    if asserts_pass:
        out.append("the visible gate asserts a pass while these fail-closed conditions hold: "
                   + "; ".join(conditions[:4]))
    else:
        out.append("fail-closed conditions present (gate does not currently claim a pass, but no "
                   "gate blocks on them): " + "; ".join(conditions[:4]))
    return out


# ============================================ V01 displayed value contradicts a verified fixture

import json as _json          # noqa: E402
from pathlib import Path as _Path  # noqa: E402

_FIXTURES = None


def _fixtures():
    """Labelled test cases with source-verified truth. A hard-coded table inside a detector is an
    anti-pattern; this lives in tests/fixtures/ so the batch runs can use it as their acceptance
    target too."""
    global _FIXTURES
    if _FIXTURES is None:
        f = _Path(__file__).resolve().parent.parent / "tests" / "fixtures" / "rapidmeta_error_fixtures.json"
        try:
            _FIXTURES = _json.loads(f.read_text(encoding="utf-8"))
        except Exception:
            _FIXTURES = {}
    return _FIXTURES


@detector("RM-V01", "Displayed value contradicts the source-verified fixture", "P0")
def d_v01(c: Ctx):
    """For an app with a fixture, compare every displayed value against the verified truth.
    Fires only where a discrepancy is RECORDED, so it is exact rather than heuristic."""
    fx = _fixtures().get(c.path.name)
    if not fx:
        return []
    out = []
    for key, spec in (fx.get("trials") or {}).items():
        row = c.realdata.get(key)
        if not isinstance(row, dict):
            # a fixture key the app no longer carries is itself a finding
            if key not in c.text:
                out.append(f"fixture trial '{key}' ({spec.get('name')}) is absent from the ledger")
            continue
        disp, truth = spec.get("displayed") or {}, spec.get("truth") or {}
        for field, want in disp.items():
            if not isinstance(want, (int, float)) or isinstance(want, bool):
                continue
            got = _num(row.get(field))
            if got is not None and abs(got - float(want)) > 1e-9:
                out.append(f"{spec.get('name')}.{field}: ledger {got} vs fixture-recorded display {want} "
                           f"— the app has changed since the fixture was written; re-verify")
        arm = truth.get("ARM_REVERSAL")
        if arm and _num(row.get("tN")) is not None:
            if abs((_num(row.get("tN")) or 0) - float(arm.get("control_n", -1))) < 1e-9:
                out.append(f"{spec.get('name')}: ARM REVERSAL — tN={row.get('tN')} is the CONTROL n "
                           f"({arm.get('control_n')}); the device arm is {arm.get('device_n')} "
                           f"[verified: {spec.get('verified_by') or fx.get('why')}]"[:300])
        for err in spec.get("errors") or []:
            pass
        wrong = truth.get("correct_nct")
        if wrong and str(key).replace("NULLED:", "") != wrong:
            out.append(f"{spec.get('name')}: ledger carries {str(key).replace('NULLED:', '')}, the "
                       f"verified identifier is {wrong} — {str(truth.get('wrong_nct_resolves_to'))[:160]}")
        cc = truth.get("correct_citation")
        if cc:
            shown = str((disp or {}).get("citation") or "")
            if shown and shown.replace(" ", "") not in cc.replace(" ", ""):
                out.append(f"{spec.get('name')}: displays \"{shown}\"; verified citation is \"{cc}\"")
    return out

# ================================ B09 persisted state can resurrect a withdrawn row

@detector("RM-B09", "Persisted state can resurrect a withdrawn or absent row", "P0")
def d_b09(c: Ctx):
    """The returning-visitor trap. Found by RENDERING, not by reading the file (9d37dce08):
    emptying `realData` stops a FRESH visitor pooling withdrawn rows, but the engine persists
    `state.trials` to localStorage, so a reader who opened the page before the fix keeps the old
    auto-seeded rows and is still shown the withdrawn estimate.

    A per-app migration (_migrated_vNNN_quarantine_purge) only covers ids that app already knows
    are quarantined. The general fix is a ledger-fingerprint reconciliation on hydrate (G21)."""
    out = []
    persists = re.search(r"localStorage\.setItem\([^)]{0,80}JSON\.stringify\(\s*this\.state", c.text)
    if not persists:
        return out
    has_fingerprint = re.search(r"ledgerFingerprint|_rm_ledger_fp", c.text)
    if has_fingerprint:
        return out                      # the general reconciliation is present
    quarantined = re.search(r"__quarantinedTrials", c.text)
    purge_migration = re.search(r"_migrated_[A-Za-z0-9_]{0,30}(quarantine|purge)", c.text)
    empty_ledger = (c.k == 0 and re.search(r"\brealData\s*[:=]\s*\{\s*\}", c.text))

    if quarantined or empty_ledger:
        if purge_migration:
            out.append("persists state.trials to localStorage and ships a one-off purge migration "
                       "(" + purge_migration.group(0) + ") — covers THIS withdrawal only; a later "
                       "ledger change is not reconciled, and no ledger fingerprint is stored")
        else:
            out.append("persists state.trials to localStorage and has withdrawn/quarantined rows "
                       "with NO purge migration and NO ledger fingerprint — a returning visitor "
                       "keeps the pre-fix rows and can still be shown the withdrawn estimate")
    else:
        out.append("persists state.trials to localStorage with no ledger fingerprint — any future "
                   "correction to this app's ledger will not reach a returning visitor")
    return out