"""Locate stored 2x2 values in cached PMC JATS table cells.

This is stricter than a number-presence scan: it parses each <table-wrap> into
a grid, records the row label and column header for each numeric cell, and only
reports LOCATED_WITH_LABELS when one parsed table can account for all four
stored values with recoverable labels.

No network calls are made. The scratchpad is discovered from the current drive,
F:, C:, or D:, or can be supplied with --scratch / RAPIDMETA_TIER1_SCRATCH.
"""
from __future__ import annotations

import argparse
import io
import json
import os
import re
import sys
import xml.etree.ElementTree as ET
from collections import Counter
from dataclasses import dataclass
from itertools import product
from pathlib import Path
from typing import Iterable


if hasattr(sys.stdout, "buffer") and (sys.stdout.encoding or "").lower() != "utf-8":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")


SCRATCH_RELATIVE = Path("claude-temp") / "claude" / "F--rapidmeta-finerenone" / (
    "b63dd13c-19b4-4446-b1fb-7dd044761eca"
) / "scratchpad"
VALUE_KEYS = ("tE", "tN", "cE", "cN")
INTEGER_RE = re.compile(r"(?<![A-Za-z0-9_.+-])[-+]?(?:\d{1,3}(?:,\d{3})+|\d+)(?![A-Za-z0-9_.])")
SPACE_GROUPED_DECIMAL_RE = re.compile(r"(?<!\d)\d{1,3}(?:\s\d{3})+\.\d+")


@dataclass(frozen=True)
class GridCell:
    text: str
    tag: str
    section: str
    row: int
    col: int
    rowspan: int
    colspan: int
    attrs: tuple[tuple[str, str], ...]


@dataclass(frozen=True)
class LocatedCell:
    pmid: str
    pmcid: str
    xml_name: str
    table_id: str
    table_label: str
    table_caption: str
    table_ordinal: int
    row: int
    col: int
    row_label: str
    col_header: str
    cell_text: str

    @property
    def has_labels(self) -> bool:
        return bool(self.row_label.strip()) and bool(self.col_header.strip())

    @property
    def source_label(self) -> str:
        table_name = self.table_label or self.table_id or f"table#{self.table_ordinal}"
        return f"{self.pmcid or self.xml_name}:{table_name}"


@dataclass
class ParsedTable:
    pmid: str
    pmcid: str
    xml_name: str
    table_id: str
    table_label: str
    table_caption: str
    table_ordinal: int
    all_text: str
    all_values: set[int]
    cells: list[tuple[GridCell, str, str, set[int]]]


@dataclass
class TrialEvaluation:
    verdict: str
    scope: str
    best_table: ParsedTable | None
    hits: dict[str, LocatedCell | None]
    cell_hit_counts: dict[str, int]
    text_hit_counts: dict[str, int]


def local_name(tag: str) -> str:
    return tag.rsplit("}", 1)[-1] if "}" in tag else tag


def normalize_ws(text: str) -> str:
    return re.sub(r"\s+", " ", text.replace("\u00a0", " ")).strip()


def text_content(element: ET.Element) -> str:
    return normalize_ws(" ".join(t for t in element.itertext() if t))


def first_desc_text(element: ET.Element, name: str) -> str:
    for child in element.iter():
        if child is not element and local_name(child.tag) == name:
            return text_content(child)
    return ""


def int_attr(element: ET.Element, name: str, default: int = 1) -> int:
    raw = element.attrib.get(name)
    if not raw:
        return default
    try:
        value = int(raw)
    except ValueError:
        return default
    return max(value, 1)


def integer_values(text: str) -> list[int]:
    text = SPACE_GROUPED_DECIMAL_RE.sub(lambda match: " " * len(match.group(0)), text)
    out: list[int] = []
    for match in INTEGER_RE.finditer(text):
        raw = match.group(0).replace(",", "")
        try:
            out.append(int(raw))
        except ValueError:
            continue
    return out


def child_rows(table: ET.Element) -> list[tuple[str, ET.Element]]:
    rows: list[tuple[str, ET.Element]] = []
    for child in list(table):
        name = local_name(child.tag)
        if name in {"thead", "tbody", "tfoot"}:
            for grandchild in list(child):
                if local_name(grandchild.tag) == "tr":
                    rows.append((name, grandchild))
        elif name == "tr":
            rows.append(("tbody", child))
    if rows:
        return rows

    # Fallback for malformed exports where rows are not direct table children.
    for node in table.iter():
        if node is not table and local_name(node.tag) == "tr":
            rows.append(("tbody", node))
    return rows


def ensure_grid_row(grid: list[dict[int, GridCell]], row_index: int) -> None:
    while len(grid) <= row_index:
        grid.append({})


def parse_grid(table: ET.Element) -> tuple[list[dict[int, GridCell]], dict[int, list[GridCell]]]:
    grid: list[dict[int, GridCell]] = []
    origins_by_row: dict[int, list[GridCell]] = {}
    rows = child_rows(table)

    for row_index, (section, tr) in enumerate(rows):
        ensure_grid_row(grid, row_index)
        col = 0
        origins_by_row[row_index] = []
        for child in list(tr):
            tag = local_name(child.tag)
            if tag not in {"th", "td"}:
                continue
            while col in grid[row_index]:
                col += 1
            rowspan = int_attr(child, "rowspan")
            colspan = int_attr(child, "colspan")
            cell = GridCell(
                text=text_content(child),
                tag=tag,
                section=section,
                row=row_index,
                col=col,
                rowspan=rowspan,
                colspan=colspan,
                attrs=tuple(sorted((str(k), str(v)) for k, v in child.attrib.items())),
            )
            origins_by_row[row_index].append(cell)
            for rr in range(row_index, row_index + rowspan):
                ensure_grid_row(grid, rr)
                for cc in range(col, col + colspan):
                    grid[rr][cc] = cell
            col += colspan
    return grid, origins_by_row


def infer_header_rows(origins_by_row: dict[int, list[GridCell]]) -> set[int]:
    explicit = {
        row
        for row, cells in origins_by_row.items()
        if cells and all(cell.section == "thead" for cell in cells)
    }
    if explicit:
        return explicit

    inferred: set[int] = set()
    for row in sorted(origins_by_row):
        cells = origins_by_row[row]
        if len(cells) < 2:
            break
        has_numbers = any(integer_values(cell.text) for cell in cells)
        all_header_tags = all(cell.tag == "th" for cell in cells)
        if all_header_tags or not has_numbers:
            inferred.add(row)
            continue
        break
    return inferred


def unique_join(parts: Iterable[str]) -> str:
    seen: set[str] = set()
    out: list[str] = []
    for part in parts:
        clean = normalize_ws(part)
        if not clean or clean in seen:
            continue
        seen.add(clean)
        out.append(clean)
    return " | ".join(out)


def cell_attr(cell: GridCell, name: str) -> str:
    attrs = dict(cell.attrs)
    return attrs.get(name, "")


def column_header_for(
    cell: GridCell,
    header_by_col: dict[int, list[str]],
    id_to_header: dict[str, str],
) -> str:
    header_ids = cell_attr(cell, "headers")
    if header_ids:
        by_id = [id_to_header.get(part, "") for part in header_ids.split()]
        joined = unique_join(by_id)
        if joined:
            return joined

    labels: list[str] = []
    for col in range(cell.col, cell.col + cell.colspan):
        labels.extend(header_by_col.get(col, []))
    return unique_join(labels)


def row_label_for(cell: GridCell, grid: list[dict[int, GridCell]]) -> str:
    if cell.row >= len(grid):
        return ""
    row_cells = grid[cell.row]
    candidates: list[GridCell] = []
    seen: set[tuple[int, int, str]] = set()
    for col in sorted(c for c in row_cells if c < cell.col):
        candidate = row_cells[col]
        key = (candidate.row, candidate.col, candidate.text)
        if candidate is cell or key in seen:
            continue
        seen.add(key)
        if candidate.text:
            candidates.append(candidate)
    return candidates[0].text if candidates else ""


def parse_table_cells(
    table_node: ET.Element,
    pmid: str,
    pmcid: str,
    xml_name: str,
    table_id: str,
    table_label: str,
    table_caption: str,
    table_ordinal: int,
    table_text: str,
) -> ParsedTable:
    grid, origins_by_row = parse_grid(table_node)
    header_rows = infer_header_rows(origins_by_row)
    header_by_col: dict[int, list[str]] = {}
    id_to_header: dict[str, str] = {}

    for row_index, cells in origins_by_row.items():
        for cell in cells:
            cell_id = cell_attr(cell, "id")
            if cell_id and cell.tag == "th":
                id_to_header[cell_id] = cell.text
        if row_index not in header_rows:
            continue
        for col, header_cell in sorted(grid[row_index].items()):
            if header_cell.text:
                header_by_col.setdefault(col, []).append(header_cell.text)

    parsed_cells: list[tuple[GridCell, str, str, set[int]]] = []
    for row_index in sorted(origins_by_row):
        if row_index in header_rows:
            continue
        for cell in origins_by_row[row_index]:
            values = set(integer_values(cell.text))
            if not values:
                continue
            row_label = row_label_for(cell, grid)
            col_header = column_header_for(cell, header_by_col, id_to_header)
            parsed_cells.append((cell, row_label, col_header, values))

    return ParsedTable(
        pmid=pmid,
        pmcid=pmcid,
        xml_name=xml_name,
        table_id=table_id,
        table_label=table_label,
        table_caption=table_caption,
        table_ordinal=table_ordinal,
        all_text=table_text,
        all_values=set(integer_values(table_text)),
        cells=parsed_cells,
    )


def article_ids(root: ET.Element, xml_name: str) -> tuple[str, str]:
    pmid = ""
    pmcid = ""
    for element in root.iter():
        if local_name(element.tag) != "article-id":
            continue
        kind = (element.attrib.get("pub-id-type") or "").lower()
        value = text_content(element)
        if kind == "pmid" and value:
            pmid = value
        elif kind == "pmcid" and value:
            pmcid = value
    if not pmcid and xml_name.upper().startswith("PMC"):
        pmcid = Path(xml_name).stem
    return pmid, pmcid


def descendant_tables(table_wrap: ET.Element) -> list[ET.Element]:
    return [node for node in table_wrap.iter() if node is not table_wrap and local_name(node.tag) == "table"]


def parse_xml_tables(xml_bytes: bytes, xml_name: str) -> list[ParsedTable]:
    root = ET.fromstring(xml_bytes)
    pmid, pmcid = article_ids(root, xml_name)
    parsed: list[ParsedTable] = []
    table_ordinal = 0
    for table_wrap in root.iter():
        if local_name(table_wrap.tag) != "table-wrap":
            continue
        table_text = text_content(table_wrap)
        table_id = table_wrap.attrib.get("id", "")
        table_label = first_desc_text(table_wrap, "label")
        table_caption = first_desc_text(table_wrap, "caption")
        tables = descendant_tables(table_wrap)
        if not tables:
            table_ordinal += 1
            parsed.append(
                ParsedTable(
                    pmid=pmid,
                    pmcid=pmcid,
                    xml_name=xml_name,
                    table_id=table_id,
                    table_label=table_label,
                    table_caption=table_caption,
                    table_ordinal=table_ordinal,
                    all_text=table_text,
                    all_values=set(integer_values(table_text)),
                    cells=[],
                )
            )
            continue
        for table_node in tables:
            table_ordinal += 1
            parsed.append(
                parse_table_cells(
                    table_node=table_node,
                    pmid=pmid,
                    pmcid=pmcid,
                    xml_name=xml_name,
                    table_id=table_id,
                    table_label=table_label,
                    table_caption=table_caption,
                    table_ordinal=table_ordinal,
                    table_text=table_text,
                )
            )
    return parsed


def hits_in_table(table: ParsedTable, value: int) -> list[LocatedCell]:
    hits: list[LocatedCell] = []
    for cell, row_label, col_header, values in table.cells:
        if value not in values:
            continue
        hits.append(
            LocatedCell(
                pmid=table.pmid,
                pmcid=table.pmcid,
                xml_name=table.xml_name,
                table_id=table.table_id,
                table_label=table.table_label,
                table_caption=table.table_caption,
                table_ordinal=table.table_ordinal,
                row=cell.row + 1,
                col=cell.col + 1,
                row_label=row_label,
                col_header=col_header,
                cell_text=cell.text,
            )
        )
    hits.sort(key=lambda hit: (not hit.has_labels, hit.source_label, hit.row, hit.col, hit.cell_text))
    return hits


def evaluate_trial(tables: list[ParsedTable], trial: dict[str, object]) -> TrialEvaluation:
    values = {key: int(trial[key]) for key in VALUE_KEYS}
    cell_hits_by_table: list[tuple[ParsedTable, dict[str, list[LocatedCell]]]] = []
    text_hits_by_table: list[tuple[ParsedTable, dict[str, bool]]] = []

    for table in tables:
        cell_hits = {key: hits_in_table(table, value) for key, value in values.items()}
        text_hits = {key: value in table.all_values for key, value in values.items()}
        cell_hits_by_table.append((table, cell_hits))
        text_hits_by_table.append((table, text_hits))

    def make_eval(verdict: str, scope: str, table: ParsedTable | None, hits: dict[str, LocatedCell | None]) -> TrialEvaluation:
        return TrialEvaluation(
            verdict=verdict,
            scope=scope,
            best_table=table,
            hits=hits,
            cell_hit_counts={
                key: sum(len(hits_in_table(table_rec, values[key])) for table_rec in tables)
                for key in VALUE_KEYS
            },
            text_hit_counts={
                key: sum(1 for table_rec in tables if values[key] in table_rec.all_values)
                for key in VALUE_KEYS
            },
        )

    labelled_candidates: list[tuple[int, ParsedTable, dict[str, LocatedCell | None]]] = []
    unlabelled_candidates: list[tuple[int, ParsedTable, dict[str, LocatedCell | None]]] = []
    for table, cell_hits in cell_hits_by_table:
        if not all(cell_hits[key] for key in VALUE_KEYS):
            continue
        chosen_labelled = first_coherent_hits(cell_hits)
        if chosen_labelled:
            caption_bonus = 1 if table.table_caption else 0
            labelled_candidates.append((caption_bonus, table, chosen_labelled))
        else:
            chosen_any = {key: cell_hits[key][0] for key in VALUE_KEYS}
            label_count = sum(1 for hit in chosen_any.values() if hit and hit.has_labels)
            unlabelled_candidates.append((label_count, table, chosen_any))

    if labelled_candidates:
        labelled_candidates.sort(key=lambda item: (-item[0], item[1].xml_name, item[1].table_ordinal))
        _, best_table, hits = labelled_candidates[0]
        return make_eval("LOCATED_WITH_LABELS", "single_table", best_table, hits)

    if unlabelled_candidates:
        unlabelled_candidates.sort(key=lambda item: (-item[0], item[1].xml_name, item[1].table_ordinal))
        _, best_table, hits = unlabelled_candidates[0]
        return make_eval("LOCATED_UNLABELLED", "single_table", best_table, hits)

    aggregate_hits = {key: [] for key in VALUE_KEYS}
    for table, cell_hits in cell_hits_by_table:
        for key in VALUE_KEYS:
            aggregate_hits[key].extend(cell_hits[key])
    if all(aggregate_hits[key] for key in VALUE_KEYS):
        hits = {key: aggregate_hits[key][0] for key in VALUE_KEYS}
        return make_eval("LOCATED_UNLABELLED", "scattered_cells", None, hits)

    aggregate_text_hits = {
        key: any(text_hits[key] for _, text_hits in text_hits_by_table) for key in VALUE_KEYS
    }
    if all(aggregate_text_hits.values()):
        return make_eval("NUMBER_ONLY", "table_text", None, {key: None for key in VALUE_KEYS})

    return make_eval("NOT_IN_TABLES", "missing_values", None, {key: None for key in VALUE_KEYS})


def quoted(text: str, limit: int = 84) -> str:
    clean = normalize_ws(text)
    if len(clean) > limit:
        clean = clean[: limit - 3].rstrip() + "..."
    return json.dumps(clean, ensure_ascii=False)


def format_hit(key: str, hit: LocatedCell | None) -> str:
    if hit is None:
        return f"{key}=MISS"
    row = quoted(hit.row_label)
    col = quoted(hit.col_header)
    cell = quoted(hit.cell_text, 52)
    return f"{key}@{hit.source_label}[r{hit.row}c{hit.col}] row={row} col={col} cell={cell}"


def comparable_label(text: str) -> str:
    return re.sub(r"\s+", " ", text.casefold()).strip()


def same_nonempty_label(left: str, right: str) -> bool:
    left_norm = comparable_label(left)
    right_norm = comparable_label(right)
    return bool(left_norm) and left_norm == right_norm


def different_nonempty_label(left: str, right: str) -> bool:
    left_norm = comparable_label(left)
    right_norm = comparable_label(right)
    return bool(left_norm) and bool(right_norm) and left_norm != right_norm


def coherent_2x2(hits: dict[str, LocatedCell | None]) -> bool:
    t_event = hits.get("tE")
    t_total = hits.get("tN")
    c_event = hits.get("cE")
    c_total = hits.get("cN")
    if not all((t_event, t_total, c_event, c_total)):
        return False
    assert t_event is not None and t_total is not None and c_event is not None and c_total is not None
    if not all(hit.has_labels for hit in (t_event, t_total, c_event, c_total)):
        return False

    # Pattern 1: outcome row, treatment/control columns; counts can be a/N in
    # one cell or split within the same arm-specific header.
    columns_are_arms = (
        same_nonempty_label(t_event.row_label, t_total.row_label)
        and same_nonempty_label(t_event.row_label, c_event.row_label)
        and same_nonempty_label(t_event.row_label, c_total.row_label)
        and same_nonempty_label(t_event.col_header, t_total.col_header)
        and same_nonempty_label(c_event.col_header, c_total.col_header)
        and different_nonempty_label(t_event.col_header, c_event.col_header)
    )
    if columns_are_arms:
        return True

    # Pattern 2: treatment/control rows, either one outcome column containing
    # a/N or two shared event/total columns.
    rows_are_arms = (
        same_nonempty_label(t_event.row_label, t_total.row_label)
        and same_nonempty_label(c_event.row_label, c_total.row_label)
        and different_nonempty_label(t_event.row_label, c_event.row_label)
        and (
            (
                same_nonempty_label(t_event.col_header, t_total.col_header)
                and same_nonempty_label(c_event.col_header, c_total.col_header)
                and same_nonempty_label(t_event.col_header, c_event.col_header)
            )
            or (
                same_nonempty_label(t_event.col_header, c_event.col_header)
                and same_nonempty_label(t_total.col_header, c_total.col_header)
                and different_nonempty_label(t_event.col_header, t_total.col_header)
            )
        )
    )
    return rows_are_arms


def first_coherent_hits(cell_hits: dict[str, list[LocatedCell]]) -> dict[str, LocatedCell | None] | None:
    labelled_lists: list[list[LocatedCell]] = []
    for key in VALUE_KEYS:
        labelled = [hit for hit in cell_hits[key] if hit.has_labels]
        if not labelled:
            return None
        labelled_lists.append(labelled[:12])
    for combo in product(*labelled_lists):
        chosen = dict(zip(VALUE_KEYS, combo))
        if coherent_2x2(chosen):
            return chosen
    return None


def find_scratch(cli_value: str | None) -> Path:
    candidates: list[Path] = []
    if cli_value:
        candidates.append(Path(cli_value))
    env_value = os.environ.get("RAPIDMETA_TIER1_SCRATCH")
    if env_value:
        candidates.append(Path(env_value))

    anchors: list[str] = []
    cwd_anchor = Path.cwd().anchor
    if cwd_anchor:
        anchors.append(cwd_anchor)
    anchors.extend([f"{drive}:\\" for drive in ("F", "C", "D")])
    for anchor in anchors:
        path = Path(anchor) / SCRATCH_RELATIVE
        if path not in candidates:
            candidates.append(path)

    for candidate in candidates:
        if (candidate / "sample20.json").exists() and (candidate / "pmids_resolved.json").exists():
            return candidate
    rendered = ", ".join(str(path) for path in candidates)
    raise FileNotFoundError(f"could not find scratchpad with sample20.json and pmids_resolved.json; tried: {rendered}")


def load_json(path: Path) -> object:
    return json.loads(path.read_text(encoding="utf-8"))


def build_xml_index(cache: Path) -> tuple[dict[str, list[ParsedTable]], list[str]]:
    by_pmid: dict[str, list[ParsedTable]] = {}
    errors: list[str] = []
    for xml_path in sorted(cache.glob("PMC*.xml")):
        try:
            tables = parse_xml_tables(xml_path.read_bytes(), xml_path.name)
        except Exception as exc:  # noqa: BLE001 - report and continue across a cache.
            errors.append(f"ERROR xml_parse {xml_path.name}: {type(exc).__name__}: {exc}")
            continue
        pmids = sorted({table.pmid for table in tables if table.pmid})
        if not pmids:
            try:
                root = ET.fromstring(xml_path.read_bytes())
                pmid, _ = article_ids(root, xml_path.name)
            except Exception:
                pmid = ""
            pmids = [pmid] if pmid else []
        for pmid in pmids:
            by_pmid.setdefault(pmid, []).extend(tables)
    return by_pmid, errors


def source_summary(eval_result: TrialEvaluation) -> str:
    if eval_result.best_table is None:
        return f"scope={eval_result.scope}"
    table = eval_result.best_table
    label = table.table_label or table.table_id or f"table#{table.table_ordinal}"
    caption = quoted(table.table_caption, 70)
    return f"scope={eval_result.scope} source={table.pmcid or table.xml_name}:{label} caption={caption}"


def run_control(name: str, xml: bytes, trial: dict[str, int], expected: str) -> tuple[bool, TrialEvaluation]:
    tables = parse_xml_tables(xml, f"CONTROL_{name}.xml")
    observed = evaluate_trial(tables, trial)
    exact_labels_ok = True
    if name == "synthetic":
        expected_labels = {
            "tE": ("Primary endpoint", "Treatment"),
            "tN": ("Primary endpoint", "Treatment"),
            "cE": ("Primary endpoint", "Placebo"),
            "cN": ("Primary endpoint", "Placebo"),
        }
        for key, (row, col) in expected_labels.items():
            hit = observed.hits.get(key)
            if hit is None or hit.row_label != row or hit.col_header != col:
                exact_labels_ok = False
    ok = observed.verdict == expected and exact_labels_ok
    print(f"CONTROL {name} expected={expected} observed={observed.verdict} {'PASS' if ok else 'FAIL'}")
    return ok, observed


def run_controls() -> bool:
    trial = {"tE": 914, "tN": 4187, "cE": 1117, "cN": 4212}
    synthetic = b"""<article><front><article-meta><article-id pub-id-type="pmid">0</article-id><article-id pub-id-type="pmcid">PMC0</article-id></article-meta></front><body><table-wrap id="ctl1"><label>Table C1</label><caption><p>Control table</p></caption><table><thead><tr><th>Outcome</th><th>Treatment</th><th>Placebo</th></tr></thead><tbody><tr><th>Primary endpoint</th><td>914/4187</td><td>1117/4212</td></tr></tbody></table></table-wrap></body></article>"""
    mangled = b"""<article><front><article-meta><article-id pub-id-type="pmid">0</article-id><article-id pub-id-type="pmcid">PMC0</article-id></article-meta></front><body><table-wrap id="ctl2"><table><tbody><tr><td>914</td><td>4187</td><td>1117</td><td>4212</td></tr></tbody></table></table-wrap></body></article>"""
    ok1, _ = run_control("synthetic", synthetic, trial, "LOCATED_WITH_LABELS")
    ok2, _ = run_control("mangled", mangled, trial, "LOCATED_UNLABELLED")
    return ok1 and ok2


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--scratch", help="Scratchpad containing sample20.json, pmids_resolved.json, and pmc_cache/")
    args = parser.parse_args()

    controls_ok = run_controls()
    if not controls_ok:
        print("CONTROL_FAILURE stopping before real trials")
        return 2

    scratch = find_scratch(args.scratch)
    cache = scratch / "pmc_cache"
    sample = load_json(scratch / "sample20.json")
    resolved_doc = load_json(scratch / "pmids_resolved.json")
    if not isinstance(sample, dict):
        raise TypeError("sample20.json must be a JSON object keyed by NCT")
    if not isinstance(resolved_doc, dict) or not isinstance(resolved_doc.get("resolved"), dict):
        raise TypeError("pmids_resolved.json must contain a resolved object")
    resolved = resolved_doc["resolved"]

    by_pmid, xml_errors = build_xml_index(cache)
    for err in xml_errors:
        print(err)

    rows: list[tuple[str, TrialEvaluation, int, int]] = []
    cached_trials = 0
    verdicts: Counter[str] = Counter()
    for nct in sorted(sample):
        trial = sample[nct]
        pmids = [str(pmid) for pmid in resolved.get(nct, [])]
        tables: list[ParsedTable] = []
        cached_xml_names: set[str] = set()
        for pmid in pmids:
            for table in by_pmid.get(pmid, []):
                tables.append(table)
                cached_xml_names.add(table.xml_name)
        if not tables:
            eval_result = TrialEvaluation(
                verdict="NO_XML",
                scope="no_cached_xml",
                best_table=None,
                hits={key: None for key in VALUE_KEYS},
                cell_hit_counts={key: 0 for key in VALUE_KEYS},
                text_hit_counts={key: 0 for key in VALUE_KEYS},
            )
            cached_xml_count = 0
        else:
            cached_trials += 1
            eval_result = evaluate_trial(tables, trial)
            cached_xml_count = len(cached_xml_names)
        verdicts[eval_result.verdict] += 1
        rows.append((nct, eval_result, len(pmids), cached_xml_count))

    print(f"CACHED_XML_DENOMINATOR {cached_trials}/{len(sample)} trials have >=1 cached XML")
    print("VERDICT_DISTRIBUTION denominator=20")
    for verdict in ("LOCATED_WITH_LABELS", "LOCATED_UNLABELLED", "NUMBER_ONLY", "NOT_IN_TABLES", "NO_XML"):
        print(f"  {verdict} {verdicts.get(verdict, 0)}")
    print("PER_TRIAL")
    for nct, eval_result, pmid_count, cached_xml_count in rows:
        trial = sample[nct]
        name = quoted(str(trial.get("name", "")), 32)
        counts = ",".join(
            f"{key}=cell{eval_result.cell_hit_counts[key]}/text{eval_result.text_hit_counts[key]}"
            for key in VALUE_KEYS
        )
        details = " | ".join(format_hit(key, eval_result.hits.get(key)) for key in VALUE_KEYS)
        print(
            f"{nct} name={name} verdict={eval_result.verdict} pmids={pmid_count} "
            f"cached_xml={cached_xml_count} {source_summary(eval_result)} hits={counts} :: {details}"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
