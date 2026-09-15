from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SSOT = ROOT / "ssot"
sys.path.insert(0, str(SSOT))

import registry_identifier_checks as ric  # noqa: E402


def _source_bytes(page: Path, from_head: bool) -> bytes:
    if not from_head:
        return page.read_bytes()
    rel = page.relative_to(ROOT).as_posix()
    return subprocess.check_output(["git", "show", "HEAD:%s" % rel], cwd=str(ROOT))


def _write_preserving_newlines(page: Path, text: str, source: bytes) -> None:
    newline = "\r\n" if b"\r\n" in source else "\n"
    normalized = text.replace("\r\n", "\n").replace("\r", "\n")
    if newline == "\r\n":
        normalized = normalized.replace("\n", "\r\n")
    page.write_bytes(normalized.encode("utf-8"))


def update_page(page: Path, store: dict, apply: bool, from_head: bool) -> dict:
    source = _source_bytes(page, from_head)
    before = source.decode("utf-8")
    after = ric.inject(before, page.name, store)
    changed = before != after
    non_banner_equal = ric.strip_banner(before) == ric.strip_banner(after)
    if changed and not non_banner_equal:
        raise SystemExit("Refusing %s: non-banner bytes would change" % page)
    if changed and apply:
        _write_preserving_newlines(page, after, source)
    return {
        "page": page.name,
        "changed": changed,
        "applied": bool(changed and apply),
        "non_banner_bytes_equal": non_banner_equal,
        "banner_count": after.count('id="overmind-provenance-banner"'),
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("pages", nargs="*")
    parser.add_argument("--store", default=str(SSOT / "registry_identifier_checks.json"))
    parser.add_argument("--apply", action="store_true")
    parser.add_argument("--all", action="store_true")
    parser.add_argument("--from-head", action="store_true")
    args = parser.parse_args()

    store = json.loads(Path(args.store).read_text(encoding="utf-8"))
    if args.all:
        pages = sorted((store.get("pages") or {}).keys())
    else:
        pages = args.pages
    if not pages:
        raise SystemExit("Pass page names or --all.")

    # Positive property first (the exclusion-by-absence gate): every named page must be a file
    # under ROOT before any banner is rendered; a missing one is a refusal, not a skip.
    present = [ROOT / page_name for page_name in pages if (ROOT / page_name).is_file()]
    if len(present) != len(pages):
        missing = sorted(set(pages) - {p.name for p in present})
        raise SystemExit("No such page(s): %s" % ", ".join(missing))
    results = [update_page(page, store, args.apply, args.from_head) for page in present]

    print(json.dumps(results, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
