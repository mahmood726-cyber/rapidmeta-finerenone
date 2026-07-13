#!/usr/bin/env python
"""The TIMEPOINT RULE — deterministic, removes a class of selection error.

Mahmood's rule, in order:
  (a) use the trial's PRE-REGISTERED PRIMARY timepoint (registry, fixed before data
      — structurally immune to outcome switching),
  (b) where the registry doesn't specify, the LONGEST *COMMON* timepoint across the
      pool (same quantity in every trial — NOT longest-available-in-each, which
      silently pools a 6-month effect with a 5-year effect),
  (c) where a field has a standard (malaria: WHO day-28 PCR-corrected), use it,
  (d) show the timepoint per pool and FLAG pools whose trials' timepoints differ.

This module: parse AACT primary time_frame -> normalized WEEKS, cache per NCT, and
flag pools whose trials span materially different timepoints (the invisible class).
"""
from __future__ import annotations
import json, os, re, sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CACHE = os.path.join(REPO, 'outputs', 'timepoint_cache.json')
WAREHOUSE = r'F:\aact-cockpit\data\warehouse\aact_2026-04-12.duckdb'

_UNIT_WK = {'day': 1/7, 'days': 1/7, 'week': 1.0, 'weeks': 1.0, 'wk': 1.0, 'wks': 1.0,
            'month': 4.345, 'months': 4.345, 'mo': 4.345, 'mos': 4.345,
            'year': 52.14, 'years': 52.14, 'yr': 52.14, 'yrs': 52.14}


def parse_weeks(tf):
    """Extract a duration in WEEKS from a registry time_frame string. Returns the
    MAX numeric duration mentioned (the endpoint of the assessment window), or None.
    Deterministic; conservative (returns None on unparseable free text)."""
    if not tf:
        return None
    t = tf.lower()
    # skip measurement-cadence / non-endpoint language (a frequent parse trap:
    # "15 minute intervals", "assessed every 3 months" describe HOW OFTEN, not the
    # endpoint window). If the only durations sit next to cadence words, bail.
    if re.search(r'\b(interval|every|per |each |minute|hour|daily|weekly|monthly)\b', t) \
            and not re.search(r'\b(up to|at|from|to|through|until|week \d|month \d|day \d|year \d)\b', t):
        return None
    vals = []
    for m in re.finditer(r'(\d+(?:\.\d+)?)\s*[-–]?\s*(day|days|week|weeks|wk|wks|month|months|mo|mos|year|years|yr|yrs)\b', t):
        vals.append(float(m.group(1)) * _UNIT_WK[m.group(2)])
    # "day 28", "week 24", "month 12" (unit before number)
    for m in re.finditer(r'\b(day|week|month|year)s?\s*(\d+(?:\.\d+)?)', t):
        vals.append(float(m.group(2)) * _UNIT_WK[m.group(1)])
    return max(vals) if vals else None


def build_cache(ncts):
    import duckdb
    con = duckdb.connect(WAREHOUSE, read_only=True)
    con.execute("CREATE TEMP TABLE q(nct VARCHAR)")
    con.executemany("INSERT INTO q VALUES (?)", [(n,) for n in ncts])
    rows = con.execute("""SELECT nct_id, time_frame FROM outcomes
        WHERE nct_id IN (SELECT nct FROM q) AND outcome_type='PRIMARY' AND time_frame IS NOT NULL""").fetchall()
    # per NCT: the EFFICACY primary endpoint = the LONGEST parseable primary
    # timepoint that is >= 1 week (a trial often registers several primaries; the
    # sub-1-week ones are safety/PK windows, not the efficacy endpoint, and taking
    # the shortest wrongly grabbed those -> spurious 1000x pool ratios). Longest
    # WITHIN a trial is fine; the rule's "longest COMMON not longest AVAILABLE"
    # caveat is about pooling ACROSS trials, handled in the pool measurement.
    byn = {}
    for nct, tf in rows:
        w = parse_weeks(tf)
        if w is None or w < 1.0:
            continue
        if nct not in byn or w > byn[nct][0]:
            byn[nct] = (w, tf[:80])
    cache = {n: {'weeks': round(w, 1), 'time_frame': tf} for n, (w, tf) in byn.items()}
    json.dump(cache, open(CACHE, 'w', encoding='utf-8'), indent=0)
    return cache


def load():
    return json.load(open(CACHE, encoding='utf-8')) if os.path.exists(CACHE) else {}


if __name__ == '__main__':
    import glob
    if hasattr(sys.stdout, 'buffer'):
        import io
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    ncts = set()
    for f in glob.glob(os.path.join(REPO, '*_REVIEW.html')):
        ncts |= set(re.findall(r'NCT\d{8}', open(f, encoding='utf-8', errors='replace').read()))
    c = build_cache(ncts)
    print(f"corpus NCTs {len(ncts)}; primary timepoint parsed for {len(c)} "
          f"({100*len(c)/len(ncts):.0f}%)")
    ws = sorted(v['weeks'] for v in c.values())
    if ws:
        print(f"timepoint range: {ws[0]:.1f}w .. {ws[-1]:.1f}w  median {ws[len(ws)//2]:.1f}w")
