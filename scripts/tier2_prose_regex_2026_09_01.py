"""Tier 2: body-prose regex extraction from cached PMC XML.

This script deliberately separates proposal from comparison:

* propose_from_prose() reads only local source metadata and PMC XML.
* compare_to_sample() loads sample20.json afterwards and scores proposals.

It does not choose sentences by matching stored tE/tN/cE/cN values.
"""
from __future__ import annotations

import io
import json
import os
import re
import sys
import xml.etree.ElementTree as ET
from collections import Counter
from dataclasses import dataclass
from pathlib import Path
from statistics import mean


if hasattr(sys.stdout, "buffer") and (sys.stdout.encoding or "").lower() != "utf-8":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")


ROOT = Path(__file__).resolve().parent.parent
RUN_ID = "b63dd13c-19b4-4446-b1fb-7dd044761eca"
CONTEXT_CHARS = 120

DIGIT = r"(?:\d{1,3}(?:,\d{3})+|\d+)"
OF_RE = re.compile(
    rf"(?<![\w.])(?P<events>{DIGIT})\s+of\s+(?P<den>{DIGIT})(?![\w.])",
    re.IGNORECASE,
)
SLASH_RE = re.compile(
    rf"(?<![\w.])(?P<events>{DIGIT})\s*/\s*(?P<den>{DIGIT})"
    rf"\s*\(\s*(?P<pct>\d+(?:\.\d+)?)\s*%\s*\)",
    re.IGNORECASE,
)
DENOM_FIRST_RE = re.compile(
    rf"(?<![\w.])(?:of\s+)?(?P<den>{DIGIT})\s+"
    rf"(?:patients?|participants?|subjects?|individuals?|persons?)\b"
    rf"(?P<middle>.{{0,180}}?)"
    rf"(?P<events>{DIGIT})\s+"
    rf"(?:reached|reach|met|meet|had|have|experienced|experience|reported|"
    rf"report|achieved|achieve|attained|attain|developed|develop|died|die|"
    rf"responded|respond|were|was|with|events?|endpoints?|outcomes?)\b",
    re.IGNORECASE,
)

EVENT_CUE_RE = re.compile(
    r"\b("
    r"adverse event|event|endpoint|outcome|death|deaths|died|mortality|"
    r"responded|responder|responders|response|achieved|reached|met|"
    r"remission|relapse|exacerbation|infection|thrombotic|thrombosis|"
    r"stroke|mace|progression|sustained virologic response|svr|"
    r"discontinuation|hospitali[sz]ation|complete response|partial response"
    r")\b",
    re.IGNORECASE,
)
COMPARISON_CUE_RE = re.compile(
    r"\b("
    r"randomi[sz]ed|assigned|allocated|placebo|control|comparator|compared|"
    r"versus|vs\.?|group|arm|treatment|treated|patients?|participants?|subjects?"
    r")\b",
    re.IGNORECASE,
)
ARM_DENOMINATOR_AFTER_RE = re.compile(
    r"\b("
    r"patients?|participants?|subjects?|individuals?|persons?|assigned|"
    r"allocated|randomi[sz]ed|placebo|control|comparator|group|arm|"
    r"treatment|treated"
    r")\b",
    re.IGNORECASE,
)


@dataclass(frozen=True)
class PairProposal:
    events: int
    denominator: int
    pattern: str
    pmc_file: str
    pmid: str
    start: int
    context: str

    @property
    def pair(self) -> tuple[int, int]:
        return self.events, self.denominator


def compact_ws(text: str) -> str:
    return re.sub(r"\s+", " ", text.replace("\xa0", " ")).strip()


def local_name(tag: str) -> str:
    return tag.rsplit("}", 1)[-1]


def parse_int(raw: str) -> int:
    return int(raw.replace(",", ""))


def candidate_scratchpads() -> list[Path]:
    env = os.environ.get("TIER2_SCRATCHPAD")
    out: list[Path] = []
    if env:
        out.append(Path(env))

    out.extend(
        [
            ROOT / RUN_ID / "scratchpad",
            ROOT / "scratchpad",
            ROOT.parent / RUN_ID / "scratchpad",
        ]
    )

    repo_hints = {
        f"F--{ROOT.name}",
        f"C--{ROOT.name}",
        f"D--{ROOT.name}",
        "F--rapidmeta-finerenone",
        "C--rapidmeta-finerenone",
        "D--rapidmeta-finerenone",
    }
    for drive in ("F", "C", "D"):
        base = Path(f"{drive}:/") / "claude-temp" / "claude"
        for hint in sorted(repo_hints):
            out.append(base / hint / RUN_ID / "scratchpad")
    return out


def resolve_scratchpad() -> Path:
    for scratch in candidate_scratchpads():
        if (scratch / "sample20.json").exists() and any((scratch / "pmc_cache").glob("PMC*.xml")):
            return scratch
    searched = "\n  ".join(str(p) for p in candidate_scratchpads())
    raise FileNotFoundError("Could not find sample20.json plus pmc_cache/PMC*.xml. Searched:\n  " + searched)


def text_no_table_wraps(node: ET.Element) -> str:
    parts: list[str] = []

    def walk(el: ET.Element) -> None:
        if local_name(el.tag) == "table-wrap":
            return
        if el.text:
            parts.append(el.text)
        for child in list(el):
            walk(child)
            if child.tail:
                parts.append(child.tail)

    walk(node)
    return compact_ws(" ".join(parts))


def first_child_by_name(root: ET.Element, name: str) -> ET.Element | None:
    for el in root.iter():
        if local_name(el.tag) == name:
            return el
    return None


def article_id(root: ET.Element, id_type: str) -> str:
    for el in root.iter():
        if local_name(el.tag) == "article-id" and el.get("pub-id-type") == id_type:
            return compact_ws(el.text or "")
    return ""


def body_paragraphs(root: ET.Element) -> list[str]:
    body = first_child_by_name(root, "body")
    if body is None:
        return []
    out: list[str] = []

    def walk(el: ET.Element) -> None:
        if local_name(el.tag) == "table-wrap":
            return
        if local_name(el.tag) == "p":
            text = text_no_table_wraps(el)
            if text:
                out.append(text)
            return
        for child in list(el):
            walk(child)

    walk(body)
    return out


def statement_window(text: str, start: int, end: int) -> str:
    left_marks = [text.rfind(mark, 0, start) for mark in ".!?"]
    left = max(left_marks)
    if left == -1:
        left = 0
    else:
        left += 1
    right_candidates = [text.find(mark, end) for mark in ".!?" if text.find(mark, end) != -1]
    right = min(right_candidates) + 1 if right_candidates else len(text)
    return text[left:right].strip()


def context_window(text: str, start: int, end: int) -> str:
    left = max(0, start - CONTEXT_CHARS)
    right = min(len(text), end + CONTEXT_CHARS)
    return compact_ws(text[left:right])


def percentage_agrees(events: int, denominator: int, pct_raw: str) -> bool:
    if denominator <= 0:
        return False
    try:
        observed = float(pct_raw)
    except ValueError:
        return False
    expected = 100.0 * events / denominator
    return abs(expected - observed) <= 0.6


def relevant_statement(statement: str) -> bool:
    return bool(EVENT_CUE_RE.search(statement) and COMPARISON_CUE_RE.search(statement))


def valid_pair(events: int, denominator: int) -> bool:
    return denominator > 0 and 0 <= events <= denominator


def add_match(
    out: list[PairProposal],
    seen_spans: set[tuple[int, int, str]],
    match: re.Match[str],
    text: str,
    pattern: str,
    pmc_file: str,
    pmid: str,
) -> None:
    events = parse_int(match.group("events"))
    denominator = parse_int(match.group("den"))
    if not valid_pair(events, denominator):
        return
    if pattern == "N/M (P%)" and not percentage_agrees(events, denominator, match.group("pct")):
        return
    if pattern in {"N of M", "N/M (P%)"}:
        after_denominator = text[match.end() : match.end() + 80]
        if not ARM_DENOMINATOR_AFTER_RE.search(after_denominator):
            return
    if pattern == "M patients ... N events":
        before_events = text[max(0, match.start("events") - 45) : match.start("events")].lower()
        if re.search(r"\b(trial|study|studies|table|figure|fig\.?)\s*$", before_events):
            return
        if re.search(r"\bgroups?\b.{0,25}\bthrough\s*$", before_events):
            return
    statement = statement_window(text, match.start(), match.end())
    if not relevant_statement(statement):
        return
    key = (match.start(), match.end(), pattern)
    if key in seen_spans:
        return
    seen_spans.add(key)
    out.append(
        PairProposal(
            events=events,
            denominator=denominator,
            pattern=pattern,
            pmc_file=pmc_file,
            pmid=pmid,
            start=match.start(),
            context=context_window(text, match.start(), match.end()),
        )
    )


def extract_pairs_from_paragraph(text: str, pmc_file: str = "CONTROL", pmid: str = "") -> list[PairProposal]:
    out: list[PairProposal] = []
    seen_spans: set[tuple[int, int, str]] = set()
    for regex, pattern in (
        (SLASH_RE, "N/M (P%)"),
        (OF_RE, "N of M"),
        (DENOM_FIRST_RE, "M patients ... N events"),
    ):
        for match in regex.finditer(text):
            add_match(out, seen_spans, match, text, pattern, pmc_file, pmid)
    out.sort(key=lambda p: p.start)
    return out


def dedupe_proposals(props: list[PairProposal]) -> list[PairProposal]:
    seen: set[tuple[int, int]] = set()
    out: list[PairProposal] = []
    for prop in props:
        if prop.pair in seen:
            continue
        seen.add(prop.pair)
        out.append(prop)
    return out


def run_controls() -> bool:
    positive = (
        "Of 4187 patients assigned to treatment, 914 reached the primary endpoint, "
        "compared with 1117 of 4212 assigned to placebo."
    )
    negative = (
        "Of four thousand one hundred eighty seven patients assigned to treatment, "
        "nine hundred fourteen reached the primary endpoint, compared with one "
        "thousand one hundred seventeen of four thousand two hundred twelve "
        "assigned to placebo."
    )
    controls = [
        ("POSITIVE", [(914, 4187), (1117, 4212)], positive),
        ("NEGATIVE", [], negative),
    ]
    ok = True
    for name, expected, text in controls:
        observed = [p.pair for p in extract_pairs_from_paragraph(text)]
        passed = observed == expected
        ok = ok and passed
        print(f"CONTROL {name} expected={expected} observed={observed} {'PASS' if passed else 'FAIL'}")
    return ok


def pmid_to_cached_xml(cache: Path) -> dict[str, list[tuple[Path, ET.Element]]]:
    out: dict[str, list[tuple[Path, ET.Element]]] = {}
    for xml_path in sorted(cache.glob("PMC*.xml")):
        try:
            root = ET.parse(xml_path).getroot()
        except ET.ParseError:
            continue
        pmid = article_id(root, "pmid")
        if pmid:
            out.setdefault(pmid, []).append((xml_path, root))
    return out


def load_source_trial_pmids(scratch: Path) -> dict[str, list[str]]:
    resolved_path = scratch / "pmids_resolved.json"
    if not resolved_path.exists():
        raise FileNotFoundError(f"Missing source-publication map: {resolved_path}")
    payload = json.loads(resolved_path.read_text(encoding="utf-8"))
    resolved = payload.get("resolved") or {}
    return {str(nct): [str(pmid) for pmid in pmids] for nct, pmids in resolved.items()}


def propose_from_prose(scratch: Path) -> tuple[dict[str, list[PairProposal]], dict[str, int]]:
    """Read source metadata and XML only; do not read sample20.json here."""
    cache = scratch / "pmc_cache"
    trial_pmids = load_source_trial_pmids(scratch)
    pmid_xml = pmid_to_cached_xml(cache)
    proposals: dict[str, list[PairProposal]] = {}
    body_text_trials = 0
    cached_xml_trials = 0
    parsed_xml_files = 0

    for nct, pmids in sorted(trial_pmids.items()):
        trial_props: list[PairProposal] = []
        had_cached_xml = False
        had_body_text = False
        for pmid in pmids:
            for xml_path, root in pmid_xml.get(pmid, []):
                had_cached_xml = True
                parsed_xml_files += 1
                paragraphs = body_paragraphs(root)
                nonempty = [p for p in paragraphs if p]
                if nonempty:
                    had_body_text = True
                for paragraph in nonempty:
                    trial_props.extend(extract_pairs_from_paragraph(paragraph, xml_path.name, pmid))
        if had_cached_xml:
            cached_xml_trials += 1
        if had_body_text:
            body_text_trials += 1
        proposals[nct] = dedupe_proposals(trial_props)

    stats = {
        "source_trials": len(trial_pmids),
        "cached_xml_files": len(list(cache.glob("PMC*.xml"))),
        "pmids_mapped_from_xml": len(pmid_xml),
        "cached_xml_trials": cached_xml_trials,
        "body_text_trials": body_text_trials,
        "parsed_trial_xml_links": parsed_xml_files,
    }
    return proposals, stats


def table_wrap_texts(root: ET.Element) -> list[str]:
    out: list[str] = []
    for el in root.iter():
        if local_name(el.tag) == "table-wrap":
            out.append(compact_ws(" ".join(el.itertext())))
    return out


def prior_tier_hits(scratch: Path, sample: dict[str, dict[str, object]]) -> dict[str, set[str]]:
    hits: dict[str, set[str]] = {nct: set() for nct in sample}

    tier0_path = scratch / "tier0_result.json"
    if tier0_path.exists():
        tier0 = json.loads(tier0_path.read_text(encoding="utf-8"))
        for row in tier0.get("rows", []):
            if len(row) < 4:
                continue
            nct, _verdict, _note, prop = row[:4]
            if nct not in sample or not isinstance(prop, dict):
                continue
            stored = sample[nct]
            for key in ("tE", "cE"):
                if str(prop.get(key)) == str(stored.get(key)):
                    hits[nct].add(key)

    # Reconstruct tier-1 per-cell hits from the cached table-wrap text only.
    # This is comparison bookkeeping; it is intentionally outside prose proposal.
    cache = scratch / "pmc_cache"
    trial_pmids = load_source_trial_pmids(scratch)
    pmid_xml = pmid_to_cached_xml(cache)
    num_re = re.compile(r"\b\d+(?:\.\d+)?\b")
    for nct, stored in sample.items():
        nums: set[str] = set()
        for pmid in trial_pmids.get(nct, []):
            for _xml_path, root in pmid_xml.get(pmid, []):
                for text in table_wrap_texts(root):
                    nums.update(num_re.findall(text))
        for key in ("tE", "tN", "cE", "cN"):
            val = stored.get(key)
            if val is None:
                continue
            try:
                as_float = float(val)
            except (TypeError, ValueError):
                continue
            forms = {f"{as_float:g}"}
            if abs(as_float - int(as_float)) < 1e-9:
                forms.add(str(int(as_float)))
            if nums.intersection(forms):
                hits[nct].add(key)
    return hits


def compare_to_sample(
    scratch: Path,
    proposals: dict[str, list[PairProposal]],
    proposal_stats: dict[str, int],
) -> dict[str, object]:
    sample = json.loads((scratch / "sample20.json").read_text(encoding="utf-8"))
    prior_hits = prior_tier_hits(scratch, sample)
    rows: list[dict[str, object]] = []
    aggregate = Counter()
    distribution = Counter()
    independent_cells = 0
    body_text_ncts = set()

    # Identify body-text availability for the sample denominator.
    source_props, source_stats = proposals, proposal_stats
    cache = scratch / "pmc_cache"
    trial_pmids = load_source_trial_pmids(scratch)
    pmid_xml = pmid_to_cached_xml(cache)
    for nct in sample:
        for pmid in trial_pmids.get(nct, []):
            for _xml_path, root in pmid_xml.get(pmid, []):
                if body_paragraphs(root):
                    body_text_ncts.add(nct)
                    break
            if nct in body_text_ncts:
                break

    for nct, stored in sorted(sample.items()):
        stored_pairs = {
            "t": (int(stored["tE"]), int(stored["tN"])),
            "c": (int(stored["cE"]), int(stored["cN"])),
        }
        props = source_props.get(nct, [])
        exact_cells: set[str] = set()
        matched_pairs: set[tuple[int, int]] = set()
        mismatch_pairs: list[tuple[int, int]] = []
        for prop in props:
            if prop.pair == stored_pairs["t"]:
                exact_cells.update({"tE", "tN"})
                matched_pairs.add(prop.pair)
            elif prop.pair == stored_pairs["c"]:
                exact_cells.update({"cE", "cN"})
                matched_pairs.add(prop.pair)
            else:
                mismatch_pairs.append(prop.pair)

        needed_verdicts = {
            key: ("EXACT_MATCH" if key in exact_cells else "NOT_FOUND")
            for key in ("tE", "tN", "cE", "cN")
        }
        exact_count = len(exact_cells)
        mismatch_count = 2 * len(mismatch_pairs)
        not_found_count = 4 - exact_count
        aggregate["EXACT_MATCH"] += exact_count
        aggregate["MISMATCH"] += mismatch_count
        aggregate["NOT_FOUND"] += not_found_count
        distribution[exact_count] += 1
        independent = len(exact_cells - prior_hits.get(nct, set()))
        independent_cells += independent
        precision_den = exact_count + mismatch_count
        rows.append(
            {
                "nct": nct,
                "name": stored.get("name"),
                "body_text": nct in body_text_ncts,
                "proposals": props,
                "matched_pairs": sorted(matched_pairs),
                "mismatch_pairs": mismatch_pairs,
                "needed_verdicts": needed_verdicts,
                "exact_cells": exact_count,
                "mismatch_cells": mismatch_count,
                "not_found_cells": not_found_count,
                "precision": None if precision_den == 0 else exact_count / precision_den,
                "recall": exact_count / 4.0,
                "independent_cells": independent,
            }
        )

    exact = aggregate["EXACT_MATCH"]
    mismatch = aggregate["MISMATCH"]
    precision = None if exact + mismatch == 0 else exact / (exact + mismatch)
    recalls = [row["recall"] for row in rows]
    summary = {
        "sample_trials": len(sample),
        "body_text_sample_trials": len(body_text_ncts),
        "proposal_stats": source_stats,
        "aggregate_verdicts": dict(aggregate),
        "distribution_exact_cells": dict(distribution),
        "precision": precision,
        "recall_macro": mean(recalls) if recalls else 0.0,
        "tier2_independent_cells": independent_cells,
        "rows": rows,
    }
    return summary


def fmt_rate(value: object) -> str:
    if value is None:
        return "NA"
    return f"{float(value):.3f}"


def fmt_pairs(pairs: list[tuple[int, int]]) -> str:
    if not pairs:
        return "-"
    return ", ".join(f"({e},{n})" for e, n in pairs)


def print_summary(scratch: Path, summary: dict[str, object]) -> None:
    sample_trials = int(summary["sample_trials"])
    body_text_trials = int(summary["body_text_sample_trials"])
    prop_stats = summary["proposal_stats"]
    aggregate = Counter(summary["aggregate_verdicts"])
    distribution = Counter(summary["distribution_exact_cells"])
    rows = summary["rows"]

    print(f"SCRATCHPAD {scratch}")
    print(f"PMC XML FILES {prop_stats['cached_xml_files']}")
    print(
        "DISTRIBUTION DENOMINATOR "
        f"{body_text_trials}/{sample_trials} sample trials had >=1 cached PMC XML with <body> paragraph text"
    )
    print("DISTRIBUTION EXACT CELLS PER TRIAL")
    for exact_cells in (0, 1, 2, 3, 4):
        print(f"  exact_cells={exact_cells}: {distribution.get(exact_cells, 0)}")
    print("CELL VERDICTS")
    print(f"  EXACT_MATCH {aggregate['EXACT_MATCH']}")
    print(f"  MISMATCH {aggregate['MISMATCH']}")
    print(f"  NOT_FOUND {aggregate['NOT_FOUND']}")
    exact = aggregate["EXACT_MATCH"]
    mismatch = aggregate["MISMATCH"]
    print(f"PRECISION {exact}/{exact + mismatch} = {fmt_rate(summary['precision'])}")
    print(f"RECALL_MACRO mean(EXACT_MATCH/4 per trial) = {fmt_rate(summary['recall_macro'])}")
    print(
        "TIER2_INDEPENDENT_CONTRIBUTION "
        f"{summary['tier2_independent_cells']} cells resolved by tier 2 that tiers 0 and 1 did not"
    )
    print("PER TRIAL")
    for row in rows:
        verdicts = row["needed_verdicts"]
        matched = fmt_pairs(row["matched_pairs"])
        mismatched = fmt_pairs(row["mismatch_pairs"])
        print(
            f"  {row['nct']} body={'Y' if row['body_text'] else 'N'} "
            f"props={len(row['proposals'])} exact={row['exact_cells']} "
            f"mismatch={row['mismatch_cells']} not_found={row['not_found_cells']} "
            f"precision={fmt_rate(row['precision'])} recall={fmt_rate(row['recall'])} "
            f"cells=tE:{verdicts['tE']} tN:{verdicts['tN']} "
            f"cE:{verdicts['cE']} cN:{verdicts['cN']} "
            f"matched={matched} mismatched={mismatched}"
        )
        for prop in row["proposals"]:
            print(
                f"      proposal ({prop.events},{prop.denominator}) "
                f"{prop.pattern} {prop.pmc_file} PMID:{prop.pmid} context=\"{prop.context}\""
            )


def main() -> int:
    controls_ok = run_controls()
    if not controls_ok:
        print("Controls failed; aborting real corpus.")
        return 2
    scratch = resolve_scratchpad()
    proposals, stats = propose_from_prose(scratch)
    summary = compare_to_sample(scratch, proposals, stats)
    print_summary(scratch, summary)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
