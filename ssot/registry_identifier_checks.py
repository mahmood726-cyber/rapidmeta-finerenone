"""Render registry-identifier provenance banners from measured SSOT data."""
from __future__ import annotations

import html as html_lib
import json
import os
import re


HERE = os.path.dirname(os.path.abspath(__file__))
STORE = os.path.join(HERE, "registry_identifier_checks.json")

BANNER_RE = re.compile(
    r'<div\s+id=["\']overmind-provenance-banner["\'][^>]*>.*?</div>\s*',
    re.IGNORECASE | re.DOTALL,
)
BODY_RE = re.compile(r"<body\b[^>]*>", re.IGNORECASE)

WEAK_WORDING = (
    "may be real",
    "could not be verified",
    "UNVERIFIED registry ID",
)

_STYLE = (
    "position:fixed;bottom:0;left:0;right:0;z-index:2147483647;"
    "font-family:system-ui,Segoe UI,Arial,sans-serif;font-size:13px;"
    "line-height:1.45;background:#0d1117;color:#e6edf3;border-top:3px solid #ff6a69;"
    "padding:8px 14px;box-shadow:0 -2px 10px rgba(0,0,0,.5);"
    "max-height:34vh;overflow:auto"
)


def load(path: str = STORE) -> dict:
    if not os.path.exists(path):
        return {"pages": {}}
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def _page_keys(page: str) -> list[str]:
    base = os.path.basename(str(page))
    stem, ext = os.path.splitext(base)
    keys = [str(page), base, stem]
    if ext.lower() != ".html":
        keys.append(base + ".html")
    return list(dict.fromkeys(keys))


def page_record(page: str, store: dict | None = None) -> dict | list | None:
    data = store if store is not None else load()
    pages = data.get("pages") or {}
    for key in _page_keys(page):
        if key in pages:
            return pages[key]
    return None


def rows_for_page(page: str, store: dict | None = None) -> list[dict]:
    record = page_record(page, store)
    if isinstance(record, dict):
        rows = record.get("identifiers") or []
    elif isinstance(record, list):
        rows = record
    else:
        rows = []
    return [row for row in rows if isinstance(row, dict)]


def _latest(row: dict) -> dict:
    for key in ("lane_z_current", "current", "measurement"):
        value = row.get(key)
        if isinstance(value, dict):
            return value
    measurements = row.get("measurements")
    if isinstance(measurements, list) and measurements:
        latest = measurements[-1]
        if isinstance(latest, dict):
            return latest
    return {}


def _hit_count(measurement: dict, name: str):
    value = measurement.get(name)
    if value is None:
        value = measurement.get(name.replace("_hits", "_count"))
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def classify(row: dict) -> str:
    measurement = _latest(row)
    if not measurement:
        return "not_checked"
    status = measurement.get("http_status")
    try:
        status = int(status)
    except (TypeError, ValueError):
        status = None
    if status == 200:
        return "200"
    if status == 404:
        return "404"
    if measurement.get("error"):
        return "error"
    return "not_checked"


def _checked_label(rows: list[dict]) -> str:
    values = []
    for row in rows:
        checked = str(_latest(row).get("checked_utc") or "").strip()
        if checked:
            values.append(checked)
    if not values:
        return "not checked"
    value = sorted(set(values))[-1]
    if "T" in value:
        value = value.replace("T", " ", 1)
    if value.endswith("Z"):
        value = value[:-1] + " UTC"
    if "." in value:
        value = value.split(".", 1)[0] + " UTC"
    return value


def _ids(rows: list[dict]) -> list[str]:
    out = []
    for row in rows:
        nct = str(row.get("nct") or row.get("id") or "").strip().upper()
        if nct:
            out.append(nct)
    return out


def _name_resolutions(rows: list[dict]) -> list[str]:
    """'LABEL (NCT-on-page) -> NCTxxxx' for every row whose trial NAME resolves in ClinicalTrials.gov.
    Read from the measured store only; a row with no name search recorded contributes nothing."""
    out = []
    for row in rows:
        res = row.get("trial_name_resolution") or {}
        ctgov = res.get("ctgov") or {}
        hits = ctgov.get("hits") or []
        try:
            n = int(ctgov.get("hit_count") or 0)
        except (TypeError, ValueError):
            n = 0
        if n <= 0 or not hits:
            continue
        label = str(row.get("trial_label") or res.get("query") or "").strip()
        first = str((hits[0] or {}).get("nct") or "").strip().upper()
        page_id = str(row.get("nct") or "").strip().upper()
        if label and first:
            out.append("%s (%s on this page): name search returns %s%s" % (label, page_id, first,
                                                                          " and %d more" % (n - 1) if n > 1 else ""))
    return out


def _all_zero_literature(rows: list[dict]) -> bool:
    for row in rows:
        measurement = _latest(row)
        if _hit_count(measurement, "pubmed_hits") != 0:
            return False
        if _hit_count(measurement, "europepmc_hits") != 0:
            return False
    return True


def _banner(status_text: str, detail_text: str) -> str:
    status = html_lib.escape(status_text)
    detail = html_lib.escape(detail_text).replace(" -- ", " &mdash; ")
    return (
        '<div id="overmind-provenance-banner" style="%s">'
        '<b style="color:#f0b429">&#128269; Provenance check (registry)</b>'
        ' &nbsp; &nbsp;&middot;&nbsp; '
        '<span style="color:#ff6a69;font-weight:bold">&#9940; %s</span> '
        '<span style="opacity:.9">&mdash; %s</span></div>\n'
        % (_STYLE, status, detail)
    )


def render_banner(page: str, store: dict | None = None) -> str:
    rows = rows_for_page(page, store)
    if not rows:
        return ""
    ids = _ids(rows)
    counts = {kind: 0 for kind in ("404", "200", "error", "not_checked")}
    for row in rows:
        counts[classify(row)] += 1

    if counts["404"] and _all_zero_literature(
            [row for row in rows if classify(row) == "404"]):
        detail = (
            "%d of %d trial identifiers on this page "
            "returned HTTP 404 from ClinicalTrials.gov (checked %s), and 0 hits in PubMed / "
            "Europe PMC: these identifiers do not exist in the registry of record. The trials "
            "they label are not shown to exist under these identifiers; the pooled result that "
            "rests on them is UNSUPPORTED. Identifiers: %s"
            % (counts["404"], len(rows), _checked_label(rows), ", ".join(ids))
        )
        # Per identifier, never blanket: where the trial NAME resolves in the registry, say so and
        # name what it resolves to. The identifier printed on the page is still not that trial's
        # registration (b59a07c5d generalised this per-page fact into 'may be real' on all eight).
        resolved = _name_resolutions(rows)
        if resolved:
            detail += (
                ". A registry search by trial NAME returns records for some labels (a name hit is NOT "
                "verified to be the same trial and does not validate the identifier printed here): " + "; ".join(resolved)
                + ""
            )
        banner = _banner("Registry identifiers NOT FOUND", detail)
    elif counts["not_checked"] == len(rows):
        detail = (
            "Registry identifiers NOT CHECKED -- not observed, never absent. Identifiers: %s"
            % ", ".join(ids)
        )
        banner = _banner("Registry identifiers NOT CHECKED", detail)
    else:
        detail = (
            "Registry identifier check incomplete -- %d HTTP 200, %d HTTP 404, %d errors, "
            "%d not checked. Identifiers: %s"
            % (
                counts["200"],
                counts["404"],
                counts["error"],
                counts["not_checked"],
                ", ".join(ids),
            )
        )
        banner = _banner("Registry identifier check incomplete", detail)

    if any(word in banner for word in WEAK_WORDING):
        raise ValueError("refusing to render weakened registry wording")
    return banner


def strip_banner(html_text: str) -> str:
    return BANNER_RE.sub("", html_text)


def inject(html_text: str, page: str, store: dict | None = None) -> str:
    banner = render_banner(page, store)
    if not banner:
        return html_text
    without = strip_banner(html_text)
    match = BODY_RE.search(without)
    if not match:
        return banner + without
    return without[:match.end()] + banner + without[match.end():]


def inject_registry_banner(html_text: str, page: str, store: dict | None = None) -> str:
    return inject(html_text, page, store)
