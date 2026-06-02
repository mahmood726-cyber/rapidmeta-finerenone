"""Shared I/O utilities for the cardiology mortality atlas pipeline.

Centralizes UTF-8 stdout wrapping (Windows cp1252 crashes on unicode prints)
and Markdown table cell escaping (formula injection guard for Excel/Sheets,
plus literal `|` escape so trial titles don't break tables).
"""
import io
import re
import sys
from pathlib import Path

# All scripts share this base directory — resolved from this module's location
BASE_DIR = Path(__file__).resolve().parent


def ensure_utf8_stdout():
    """Wrap sys.stdout in UTF-8 with errors='replace'.

    Idempotent: safe to call multiple times. Required on Windows where the
    default cp1252 codec crashes on unicode characters in print().
    """
    if not isinstance(sys.stdout, io.TextIOWrapper):
        return
    if sys.stdout.encoding and sys.stdout.encoding.lower().replace('-', '') == 'utf8':
        return
    try:
        sys.stdout = io.TextIOWrapper(
            sys.stdout.buffer, encoding='utf-8', errors='replace'
        )
    except (AttributeError, ValueError):
        pass  # already wrapped or non-buffer stdout (test capture)


# Cells starting with these characters are interpreted as formulas by
# Excel/Google Sheets if a Markdown table is pasted into a spreadsheet.
# Per OWASP "CSV Injection" advice, prepend a single quote.
_FORMULA_PREFIXES = ('=', '+', '@', '\t', '\r')


def md_cell(value):
    """Escape a value for safe inclusion in a Markdown table cell.

    Handles:
      - None / non-string values via str() coercion
      - Literal pipe `|` (would break table columns) → `\\|`
      - Newlines / carriage returns → space
      - Formula injection (cells starting with =,+,@,\\t,\\r) → prepend `'`
    """
    if value is None:
        return ''
    s = str(value)
    # Strip newlines first (would break the row)
    s = s.replace('\r', ' ').replace('\n', ' ')
    # Escape pipes
    s = s.replace('|', '\\|')
    # Formula injection guard
    if s and s[0] in _FORMULA_PREFIXES:
        s = "'" + s
    return s


# NCT identifier validation — used by mining script before URL construction
_NCT_RE = re.compile(r'^NCT\d{8}$')


def is_valid_nct(nct_id):
    """Return True iff `nct_id` is a well-formed CT.gov NCT identifier."""
    return bool(nct_id) and isinstance(nct_id, str) and _NCT_RE.match(nct_id) is not None


# ────────────────────────────────────────────────────────────
# Quantile functions (shared — the single correct implementation)
#
# History: cardiology_mortality_atlas.py and umbrella_review.py each carried a
# local Beasley-Springer-Moro normal-quantile whose TAIL branch fed the tail
# argument q=sqrt(-2*ln(p)) into the CENTRAL-region a/b polynomials. That is the
# wrong rational for the tails, so qnorm(0.975) returned ~0.013 instead of
# 1.95996 and every prediction interval those scripts emitted was wrong by
# ~150x. Both now import from here. norm_ppf uses the correct three-region BSM
# (separate c/d tail polynomials); t_quantile inverts the exact Student-t CDF
# (incomplete beta) so it is accurate at low df — Cornish-Fisher is unusable at
# df=1 (returns ~7.2 where the true t_{0.975,1}=12.706).
# ────────────────────────────────────────────────────────────

import math

# Beasley-Springer-Moro coefficients
_BSM_A = (-3.969683028665376e1, 2.209460984245205e2, -2.759285104469687e2,
          1.383577518672690e2, -3.066479806614716e1, 2.506628277459239e0)
_BSM_B = (-5.447609879822406e1, 1.615858368580409e2, -1.556989798598866e2,
          6.680131188771972e1, -1.328068155288572e1)
_BSM_C = (-7.784894002430293e-3, -3.223964580411365e-1, -2.400758277161838,
          -2.549732539343734, 4.374664141464968, 2.938163982698783)
_BSM_D = (7.784695709041462e-3, 3.224671290700398e-1, 2.445134137142996,
          3.754408661907416)
_BSM_P_LOW = 0.02425
_BSM_P_HIGH = 1 - _BSM_P_LOW


def norm_ppf(p):
    """Standard normal inverse CDF (Beasley-Springer-Moro, three-region)."""
    if not (0.0 < p < 1.0):
        return float('nan')
    a, b, c, d = _BSM_A, _BSM_B, _BSM_C, _BSM_D
    if p < _BSM_P_LOW:
        q = math.sqrt(-2 * math.log(p))
        return (((((c[0] * q + c[1]) * q + c[2]) * q + c[3]) * q + c[4]) * q + c[5]) / \
               ((((d[0] * q + d[1]) * q + d[2]) * q + d[3]) * q + 1)
    if p <= _BSM_P_HIGH:
        q = p - 0.5
        r = q * q
        return (((((a[0] * r + a[1]) * r + a[2]) * r + a[3]) * r + a[4]) * r + a[5]) * q / \
               (((((b[0] * r + b[1]) * r + b[2]) * r + b[3]) * r + b[4]) * r + 1)
    q = math.sqrt(-2 * math.log(1 - p))
    return -(((((c[0] * q + c[1]) * q + c[2]) * q + c[3]) * q + c[4]) * q + c[5]) / \
            ((((d[0] * q + d[1]) * q + d[2]) * q + d[3]) * q + 1)


# Backward-compatible aliases for the two call sites that used these names.
qnorm = norm_ppf
normal_quantile = norm_ppf


def _betacf(a, b, x):
    """Continued-fraction core of the regularized incomplete beta (NR §6.4)."""
    MAXIT, EPS, FPMIN = 200, 3.0e-16, 1.0e-300
    qab, qap, qam = a + b, a + 1.0, a - 1.0
    c = 1.0
    d = 1.0 - qab * x / qap
    if abs(d) < FPMIN:
        d = FPMIN
    d = 1.0 / d
    h = d
    for m in range(1, MAXIT + 1):
        m2 = 2 * m
        aa = m * (b - m) * x / ((qam + m2) * (a + m2))
        d = 1.0 + aa * d
        if abs(d) < FPMIN:
            d = FPMIN
        c = 1.0 + aa / c
        if abs(c) < FPMIN:
            c = FPMIN
        d = 1.0 / d
        h *= d * c
        aa = -(a + m) * (qab + m) * x / ((a + m2) * (qap + m2))
        d = 1.0 + aa * d
        if abs(d) < FPMIN:
            d = FPMIN
        c = 1.0 + aa / c
        if abs(c) < FPMIN:
            c = FPMIN
        d = 1.0 / d
        delta = d * c
        h *= delta
        if abs(delta - 1.0) < EPS:
            break
    return h


def betai(a, b, x):
    """Regularized incomplete beta I_x(a, b)."""
    if x <= 0.0:
        return 0.0
    if x >= 1.0:
        return 1.0
    lbeta = math.lgamma(a + b) - math.lgamma(a) - math.lgamma(b)
    bt = math.exp(lbeta + a * math.log(x) + b * math.log(1.0 - x))
    if x < (a + 1.0) / (a + b + 2.0):
        return bt * _betacf(a, b, x) / a
    return 1.0 - bt * _betacf(b, a, 1.0 - x) / b


def t_cdf(t, df):
    """Student-t CDF P(T <= t) for df > 0, exact via incomplete beta."""
    x = df / (df + t * t)
    ib = betai(df / 2.0, 0.5, x)
    return 1.0 - 0.5 * ib if t > 0 else 0.5 * ib


def t_quantile(p, df):
    """Student-t inverse CDF: the t such that P(T <= t) = p.

    Exact (incomplete-beta CDF inverted by bisection), so it is correct at low
    df — unlike the Cornish-Fisher expansion that the atlas/umbrella scripts
    previously used, which is wildly off for df<=3 (t_{0.975,1}=12.706, not 7.2).
    Returns NaN for df < 1 or p outside (0, 1).
    """
    if df < 1 or not (0.0 < p < 1.0):
        return float('nan')
    if p == 0.5:
        return 0.0
    if p > 0.5:
        a, b = 0.0, 1.0
        while t_cdf(b, df) < p and b < 1e6:
            b *= 2.0
    else:
        a, b = -1.0, 0.0
        while t_cdf(a, df) > p and a > -1e6:
            a *= 2.0
    for _ in range(200):
        m = 0.5 * (a + b)
        if t_cdf(m, df) < p:
            a = m
        else:
            b = m
    return 0.5 * (a + b)
