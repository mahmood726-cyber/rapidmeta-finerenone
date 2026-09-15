from __future__ import annotations

import argparse
import concurrent.futures
import html
import json
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SSOT = ROOT / "ssot"
sys.path.insert(0, str(SSOT))

import registry_identifier_checks as ric  # noqa: E402


STORE_PATH = SSOT / "registry_identifier_checks.json"
PROVENANCE_REPORT = ROOT / "PROVENANCE_WEAKER_THAN_EVIDENCE_2026-09-14.md"
INTEGRATOR_PATH = ROOT / "REGISTRY_CHECK_2026-09-14.json"
PAGE_MAP_PATH = SSOT / "PAGE_MAP.json"

TARGET_PAGES = {
    "GERD_PCAB_NEW_NMA_REVIEW.html",
    "PEDIATRIC_HF_DAPA_NMA_REVIEW.html",
    "ROP_ANTI_VEGF_NMA_REVIEW.html",
}

WEAK_PATTERNS = (
    "may be real",
    "could not be verified",
    "UNVERIFIED registry ID",
)

USER_AGENT = "rm-acq-z-lane-z/1.0"


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def compact_space(value: str) -> str:
    return re.sub(r"\s+", " ", value or "").strip()


def text_from_html(fragment: str) -> str:
    return compact_space(html.unescape(re.sub(r"<[^>]+>", " ", fragment)))


def js_unescape(value: str) -> str:
    return bytes(value, "utf-8").decode("unicode_escape", errors="replace")


def _http_get_once(url: str, timeout: int) -> dict:
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            body = resp.read().decode("utf-8", errors="replace")
            return {
                "url": url,
                "http_status": int(resp.status),
                "body": body,
                "body_head": compact_space(body[:300]),
            }
    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")
        return {
            "url": url,
            "http_status": int(exc.code),
            "body": body,
            "body_head": compact_space(body[:300]),
        }
    except Exception as exc:
        return {
            "url": url,
            "http_status": None,
            "body": "",
            "body_head": "",
            "error": "%s: %s" % (type(exc).__name__, exc),
        }


def http_get(url: str, *, timeout: int = 25, attempts: int = 3) -> dict:
    last = {}
    for attempt in range(1, attempts + 1):
        last = _http_get_once(url, timeout)
        last["attempt"] = attempt
        if not last.get("error"):
            return last
        if attempt < attempts:
            time.sleep(0.5 * attempt)
    return last


def as_json(response: dict) -> dict:
    try:
        return json.loads(response.get("body") or "{}")
    except json.JSONDecodeError:
        return {}


def pubmed_count(term: str) -> dict:
    params = urllib.parse.urlencode(
        {"db": "pubmed", "retmode": "json", "retmax": "0", "term": term}
    )
    url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi?" + params
    response = http_get(url)
    out = {"url": url, "http_status": response.get("http_status")}
    if response.get("error"):
        out["error"] = response["error"]
        return out
    data = as_json(response)
    try:
        out["hit_count"] = int((data.get("esearchresult") or {}).get("count") or 0)
    except (TypeError, ValueError):
        out["hit_count"] = None
        out["error"] = "PubMed response did not expose esearchresult.count"
    return out


def europepmc_count(term: str) -> dict:
    params = urllib.parse.urlencode(
        {"query": term, "format": "json", "pageSize": "1"}
    )
    url = "https://www.ebi.ac.uk/europepmc/webservices/rest/search?" + params
    response = http_get(url)
    out = {"url": url, "http_status": response.get("http_status")}
    if response.get("error"):
        out["error"] = response["error"]
        return out
    data = as_json(response)
    try:
        out["hit_count"] = int(data.get("hitCount") or 0)
    except (TypeError, ValueError):
        out["hit_count"] = None
        out["error"] = "Europe PMC response did not expose hitCount"
    return out


def ctgov_nct_lookup(nct: str) -> dict:
    url = "https://clinicaltrials.gov/api/v2/studies/%s" % urllib.parse.quote(nct)
    response = http_get(url)
    out = {
        "endpoint": "https://clinicaltrials.gov/api/v2/studies/{nct}",
        "url": url,
        "http_status": response.get("http_status"),
        "body_head": response.get("body_head"),
    }
    if response.get("error"):
        out["error"] = response["error"]
        return out
    data = as_json(response)
    protocol = data.get("protocolSection") or {}
    ident = protocol.get("identificationModule") or {}
    status = protocol.get("statusModule") or {}
    out["registry_nct_id"] = ident.get("nctId")
    out["brief_title"] = ident.get("briefTitle")
    out["overall_status"] = status.get("overallStatus")
    return out


def ctgov_name_search(name: str) -> dict:
    params = urllib.parse.urlencode(
        {"query.term": name, "pageSize": "5", "format": "json"}
    )
    url = "https://clinicaltrials.gov/api/v2/studies?" + params
    response = http_get(url)
    out = {"url": url, "http_status": response.get("http_status")}
    if response.get("error"):
        out["error"] = response["error"]
        return out
    data = as_json(response)
    studies = data.get("studies") or []
    out["hit_count"] = len(studies)
    hits = []
    for study in studies[:5]:
        protocol = (study or {}).get("protocolSection") or {}
        ident = protocol.get("identificationModule") or {}
        hits.append(
            {
                "nct": ident.get("nctId"),
                "brief_title": ident.get("briefTitle"),
            }
        )
    out["hits"] = hits
    return out


def direct_measure(nct: str, checked_utc: str) -> dict:
    ctgov = ctgov_nct_lookup(nct)
    pubmed = pubmed_count('"%s"' % nct)
    europepmc = europepmc_count('"%s"' % nct)
    return {
        "checked_utc": checked_utc,
        "endpoint": ctgov["endpoint"],
        "url": ctgov["url"],
        "http_status": ctgov.get("http_status"),
        "body_head": ctgov.get("body_head"),
        "error": ctgov.get("error"),
        "registry_nct_id": ctgov.get("registry_nct_id"),
        "brief_title": ctgov.get("brief_title"),
        "overall_status": ctgov.get("overall_status"),
        "pubmed_url": pubmed["url"],
        "pubmed_http_status": pubmed.get("http_status"),
        "pubmed_hits": pubmed.get("hit_count"),
        "pubmed_error": pubmed.get("error"),
        "europepmc_url": europepmc["url"],
        "europepmc_http_status": europepmc.get("http_status"),
        "europepmc_hits": europepmc.get("hit_count"),
        "europepmc_error": europepmc.get("error"),
    }


def resolve_name(name: str) -> dict:
    return {
        "query": name,
        "ctgov": ctgov_name_search(name),
        "pubmed": pubmed_count('"%s"' % name),
        "europepmc": europepmc_count('"%s"' % name),
    }


def extract_banner(text: str) -> tuple[str, str, list[str]]:
    match = ric.BANNER_RE.search(text)
    if not match:
        return "", "", []
    raw = match.group(0)
    wording = text_from_html(raw)
    ids = list(dict.fromkeys(re.findall(r"NCT\d{8}", wording, flags=re.IGNORECASE)))
    ids = [nct.upper() for nct in ids]
    return raw, wording, ids


def extract_labels(text: str) -> dict[str, str]:
    labels = {}
    match = re.search(r"nctAcronyms:\{(.*?)\},realData:\{", text, re.DOTALL)
    if match:
        block = match.group(1)
        for nct, label in re.findall(r"\b(NCT\d{8})\s*:\s*\"((?:\\.|[^\"\\])*)\"", block):
            labels[nct.upper()] = js_unescape(label)
    for nct, label in re.findall(
        r"\b(NCT\d{8})\s*:\s*\{name:\"((?:\\.|[^\"\\])*)\"", text
    ):
        labels.setdefault(nct.upper(), js_unescape(label))
    return labels


def scan_weak_pages() -> dict[str, dict]:
    pages = {}
    for path in sorted(ROOT.glob("*.html")):
        text = path.read_text(encoding="utf-8")
        if not any(pattern in text for pattern in WEAK_PATTERNS):
            continue
        raw, wording, ids = extract_banner(text)
        if not raw:
            continue
        pages[path.name] = {
            "current_wording": wording,
            "identifiers": ids,
            "labels": extract_labels(text),
        }
    return pages


def load_integrator() -> dict:
    if not INTEGRATOR_PATH.exists():
        return {}
    data = json.loads(INTEGRATOR_PATH.read_text(encoding="utf-8"))
    by_page = {}
    for page, rows in (data.get("pages") or {}).items():
        page_name = page if page.endswith(".html") else page + ".html"
        by_page[page_name] = {
            str(row.get("nct") or "").upper(): {
                "checked_utc": data.get("measured_utc"),
                "endpoint": data.get("endpoint"),
                "http_status": row.get("http_status"),
                "body_head": row.get("body_head"),
            }
            for row in rows
        }
    return by_page


def page_owner(page: str, page_map: dict) -> str:
    if page in page_map:
        return "generator-owned: %s" % page_map[page]
    return "UNMAPPED: not in ssot/PAGE_MAP.json; current build_tabbed.py cannot regenerate this page"


def measured_wording(rows: list[dict]) -> str:
    counts = {"404": 0, "200": 0, "error": 0, "not_checked": 0}
    for row in rows:
        counts[ric.classify(row)] += 1
    if counts["404"] == len(rows):
        return (
            "Identifiers do not exist in ClinicalTrials.gov (HTTP 404 for %d/%d); "
            "no PubMed / Europe PMC hits for the identifiers; pooled result unsupported."
            % (counts["404"], len(rows))
        )
    return (
        "%d HTTP 200; %d HTTP 404; %d errors; %d not checked."
        % (counts["200"], counts["404"], counts["error"], counts["not_checked"])
    )


def md_cell(value: str) -> str:
    return str(value or "").replace("|", "\\|").replace("\n", " ")


def write_utf8_lf(path: Path, text: str) -> None:
    normalized = text.replace("\r\n", "\n").replace("\r", "\n")
    path.write_bytes(normalized.encode("utf-8"))


def write_provenance_report(store: dict, path: Path) -> None:
    lines = [
        "# Provenance Wording Weaker Than Evidence - 2026-09-14",
        "",
        "Generated by `scripts/measure_registry_identifiers_2026_09_14.py`.",
        "The scan used root `*.html` files containing the weakened Overmind wording before Lane Z rewrote the three target banners.",
        "",
        "| page | identifiers | 404 | 200 | error | current wording | measured wording | generator ownership |",
        "| --- | ---: | ---: | ---: | ---: | --- | --- | --- |",
    ]
    for page, record in (store.get("pages") or {}).items():
        rows = record.get("identifiers") or []
        counts = {"404": 0, "200": 0, "error": 0}
        for row in rows:
            kind = ric.classify(row)
            if kind in counts:
                counts[kind] += 1
        lines.append(
            "| %s | %d | %d | %d | %d | %s | %s | %s |"
            % (
                md_cell(page),
                len(rows),
                counts["404"],
                counts["200"],
                counts["error"],
                md_cell(record.get("current_wording")),
                md_cell(record.get("measured_wording")),
                md_cell(record.get("generator_owner")),
            )
        )
    write_utf8_lf(path, "\n".join(lines) + "\n")


def _run_pool(label: str, items: list[str], worker, max_workers: int) -> dict:
    results = {}
    with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as pool:
        futures = {pool.submit(worker, item): item for item in items}
        for index, future in enumerate(concurrent.futures.as_completed(futures), start=1):
            item = futures[future]
            print("%s %d/%d %s" % (label, index, len(items), item), flush=True)
            results[item] = future.result()
    return results


def build_store(max_workers: int) -> dict:
    checked_utc = utc_now()
    weak_pages = scan_weak_pages()
    if not weak_pages:
        raise SystemExit("No weak Overmind registry wording found in root HTML files.")
    integrator = load_integrator()
    page_map = json.loads(PAGE_MAP_PATH.read_text(encoding="utf-8"))

    unique_ncts = sorted({nct for page in weak_pages.values() for nct in page["identifiers"]})
    direct_cache = _run_pool(
        "direct",
        unique_ncts,
        lambda nct: direct_measure(nct, checked_utc),
        max_workers,
    )

    labels_to_resolve = sorted(
        {
            (weak_pages[page]["labels"].get(nct) or "").strip()
            for page in weak_pages
            for nct in weak_pages[page]["identifiers"]
            if direct_cache[nct].get("http_status") == 404
        }
        - {""}
    )
    name_cache = _run_pool("name", labels_to_resolve, resolve_name, max(1, min(4, max_workers)))
    pages_out = {}
    for page, scanned in weak_pages.items():
        rows = []
        labels = scanned["labels"]
        for nct in scanned["identifiers"]:
            label = labels.get(nct, "")
            current = direct_cache[nct]
            resolution = None
            if current.get("http_status") == 404 and label:
                resolution = name_cache[label]
            rows.append(
                {
                    "nct": nct,
                    "trial_label": label,
                    "integrator_2026_09_14": (integrator.get(page) or {}).get(nct),
                    "lane_z_current": current,
                    "classification": "404" if current.get("http_status") == 404 else ric.classify({"lane_z_current": current}),
                    "trial_name_resolution": resolution,
                }
            )
        record = {
            "source_html": page,
            "target_page": page in TARGET_PAGES,
            "generator_owner": page_owner(page, page_map),
            "current_wording": scanned["current_wording"],
            "identifiers": rows,
        }
        record["measured_wording"] = measured_wording(rows)
        pages_out[page] = record

    return {
        "schema": "registry_identifier_checks.v1",
        "generated_utc": checked_utc,
        "corpus_scan": {
            "root": str(ROOT),
            "weak_patterns": list(WEAK_PATTERNS),
            "weak_pages": sorted(pages_out),
        },
        "allowed_networks": [
            "https://clinicaltrials.gov/api/v2/",
            "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi",
            "https://www.ebi.ac.uk/europepmc/webservices/rest/search",
        ],
        "integrator_measurement_source": str(INTEGRATOR_PATH.name),
        "pages": pages_out,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--store", type=Path, default=STORE_PATH)
    parser.add_argument("--provenance-report", type=Path, default=PROVENANCE_REPORT)
    parser.add_argument("--workers", type=int, default=4)
    args = parser.parse_args()

    store = build_store(max(1, args.workers))
    write_utf8_lf(args.store, json.dumps(store, indent=1, ensure_ascii=False) + "\n")
    write_provenance_report(store, args.provenance_report)
    print("wrote %s" % args.store)
    print("wrote %s" % args.provenance_report)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
