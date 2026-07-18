#!/usr/bin/env python
"""Gate: count/effect fields written in scientific notation must parse correctly.

The card<->object guard's `_num` regex matched `-?(?:\\d+\\.?\\d*|\\.\\d+)` with no
exponent group, so a JS numeric literal in scientific notation matched the
MANTISSA ONLY and returned a value off by orders of magnitude -- silently, with
no error raised anywhere:

    cN:1e3   -> 1       TIRZEPATIDE_T2D_REVIEW        (true 1000)
    tN:95e3  -> 95      AZITHROMYCIN_CHILD_MORTALITY  (true 95000)

Consequences of the TIRZEPATIDE case, traced end to end: a 997-vs-1 arm split
makes the 0.5 continuity correction fabricate a 665-fold effect (y = -6.4998)
against the other trial's y = -0.0021, driving tau2 = 16.77 / I2 = 79.5%. The
HKSJ t-interval at k=2 (df=1, t=12.706) then lands the bound at +/-4481 on the
log scale, past exp()'s 709 limit, rendering as [0, Infinity].

So the "[0, inf] CI" was never a formatter bug. It was a parser bug three
layers upstream. Fixing the display would have hidden it.
"""
import glob
import io
import os
import re
import sys

import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "scripts"))

import assert_count_effect_consistency as gate  # noqa: E402

FIELDS = ("tE", "tN", "cE", "cN", "publishedHR")

SCI = re.compile(
    r'(?<![A-Za-z_])["\']?(' + "|".join(FIELDS) + r')["\']?\s*:\s*'
    r'(-?(?:\d+\.?\d*|\.\d+)[eE][+-]?\d+)'
)


@pytest.mark.parametrize("literal,expected", [
    ("cN:1e3", 1000.0),
    ("tN:95e3", 95000.0),
    ("cN:1E3", 1000.0),
    ("tN:1.5e2", 150.0),
    ("cE:2e-1", 0.2),
    ("publishedHR:7.8e-1", 0.78),
    ("tN:1000", 1000.0),        # plain integers still work
    ("publishedHR:.78", 0.78),  # leading-dot decimals still work
    ("cE:-3", -3.0),
])
def test_num_parses_scientific_notation(literal, expected):
    key = literal.split(":")[0]
    got = gate._num("{" + literal + "}", key)
    assert got == pytest.approx(expected), (
        f"_num parsed {literal!r} as {got}, expected {expected}. "
        f"A mantissa-only match is an order-of-magnitude silent error."
    )


def test_null_still_returns_none():
    assert gate._num("{cN:null}", "cN") is None


def test_the_two_known_live_apps_parse_correctly():
    """Regression on the actual shipped values that exposed this."""
    cases = {
        # anchor on the TRIAL OBJECT, not the first mention of the id -- the id
        # also appears in include-lists and prose earlier in the file.
        "TIRZEPATIDE_T2D_REVIEW.html": ('NCT03730662:{name:"SURPASS-4"', "cN", 1000.0),
        "AZITHROMYCIN_CHILD_MORTALITY_REVIEW.html": ("tN:95e3", "tN", 95000.0),
    }
    for fname, (anchor_str, field, expected) in cases.items():
        path = os.path.join(ROOT, fname)
        if not os.path.exists(path):
            pytest.skip(f"{fname} not present")
        src = io.open(path, "r", encoding="latin-1", newline="").read()
        anchor = src.find(anchor_str)
        assert anchor >= 0, f"anchor {anchor_str!r} not found in {fname}"
        seg = src[anchor:anchor + 3000]
        got = gate._num(seg, field)
        assert got == pytest.approx(expected), (
            f"{fname}: {field} parsed as {got}, expected {expected}"
        )


def test_no_app_silently_loses_an_exponent():
    """Corpus sweep: every scientific-notation literal must round-trip.

    This is the check that would have caught it originally -- it compares the
    regex's answer against Python's own float() on the same literal.
    """
    bad = []
    for path in glob.glob(os.path.join(ROOT, "*_REVIEW.html")):
        try:
            src = io.open(path, "r", encoding="latin-1", newline="").read()
        except OSError:
            continue
        for field, literal in SCI.findall(src):
            truth = float(literal)
            got = gate._num("{" + field + ":" + literal + "}", field)
            if got != pytest.approx(truth):
                bad.append((os.path.basename(path), field, literal, got, truth))
    assert not bad, (
        "scientific-notation literals parsed incorrectly:\n"
        + "\n".join(f"  {a}: {f}:{lit} -> {g} (true {t})" for a, f, lit, g, t in bad)
    )
