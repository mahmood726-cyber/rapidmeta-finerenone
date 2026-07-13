#!/usr/bin/env python
"""Offline AACT registry lookup for the identity gate — no network.

Reads the local AACT 2026-04-12 duckdb warehouse and caches, per NCT:
  arms       = number of registered design groups (arm_count)
  enrollment = registered enrollment N
  has_results = whether posted result_groups exist
into outputs/aact_cache.json so the identity sweep is fast and repeatable.

The arm_count is the Nix-TB signal: a trial registered with ONE arm that an app
presents with a populated comparator arm has a fabricated-or-external control.
"""
from __future__ import annotations
import json, os, sys

WAREHOUSE = r'F:\aact-cockpit\data\warehouse\aact_2026-04-12.duckdb'
REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CACHE = os.path.join(REPO, 'outputs', 'aact_cache.json')


def build_cache(ncts):
    import duckdb
    con = duckdb.connect(WAREHOUSE, read_only=True)
    ncts = sorted(set(ncts))
    con.execute("CREATE TEMP TABLE q(nct VARCHAR)")
    con.executemany("INSERT INTO q VALUES (?)", [(n,) for n in ncts])
    arms = dict(con.execute(
        "SELECT nct_id, count(*) FROM design_groups WHERE nct_id IN (SELECT nct FROM q) GROUP BY nct_id").fetchall())
    enrol = dict(con.execute(
        "SELECT nct_id, enrollment FROM studies WHERE nct_id IN (SELECT nct FROM q)").fetchall())
    res = set(r[0] for r in con.execute(
        "SELECT DISTINCT nct_id FROM result_groups WHERE nct_id IN (SELECT nct FROM q)").fetchall())
    cache = {n: {'arms': arms.get(n), 'enrollment': enrol.get(n),
                 'has_results': n in res, 'in_registry': n in arms or n in enrol}
             for n in ncts}
    json.dump(cache, open(CACHE, 'w', encoding='utf-8'), indent=0)
    return cache


def load():
    return json.load(open(CACHE, encoding='utf-8')) if os.path.exists(CACHE) else {}


if __name__ == '__main__':
    import glob, re
    if hasattr(sys.stdout, 'buffer'):
        import io
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    ncts = set()
    for f in glob.glob(os.path.join(REPO, '*_REVIEW.html')):
        ncts |= set(re.findall(r'NCT\d{8}', open(f, encoding='utf-8', errors='replace').read()))
    print(f"corpus NCTs: {len(ncts)}")
    cache = build_cache(ncts)
    found = sum(1 for v in cache.values() if v['in_registry'])
    single = sum(1 for v in cache.values() if v['arms'] == 1)
    print(f"in AACT: {found}/{len(cache)}  |  single-arm registered: {single}  |  with posted results: {sum(1 for v in cache.values() if v['has_results'])}")
    print(f"-> {CACHE}")
