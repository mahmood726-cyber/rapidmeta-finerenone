"""An object-backed review page must not be a tiny stub.

DEFECT (found 2026-09-07): a root *_REVIEW.html page can claim an SSOT object while
serving only a placeholder-sized shell. A tiny page with no object is only a plain
placeholder; the failure is the combination of an object backing and a page too small
and structurally trivial to hold the review it claims.
"""
from __future__ import annotations

import glob
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _harness as H  # noqa: E402

BYTE_FLOOR = 8000
STRUCTURE_FLOOR = 2
STRUCTURE_MARKERS = ('class="panel"', "<table", "<h2")


def check_page(size, has_object, structure_count):
    """True means: object-backed, below the byte floor, and structurally trivial."""
    return bool(has_object) and int(size) < BYTE_FLOOR and int(structure_count) < STRUCTURE_FLOOR


def slug_for_page(name):
    return name[:-5].lower().replace("_", "-")


def structure_count(html_bytes):
    text = html_bytes.decode("utf-8", "replace").lower()
    return sum(text.count(marker) for marker in STRUCTURE_MARKERS)


def root_review_pages(repo):
    return sorted(
        os.path.basename(path)
        for path in glob.glob(os.path.join(repo, "*_REVIEW.html"))
        if os.path.isfile(path)
    )


def load_page_map(repo, gate):
    path = os.path.join(repo, "ssot", "PAGE_MAP.json")
    try:
        with open(path, "r", encoding="utf-8") as fh:
            raw = json.load(fh)
    except Exception as exc:
        gate.broken("ssot/PAGE_MAP.json could not be read: %s" % exc)
        return {}
    if not isinstance(raw, dict):
        gate.broken("ssot/PAGE_MAP.json is not a page -> object mapping")
        return {}
    return {os.path.basename(str(page)): str(obj) for page, obj in raw.items() if obj}


def object_path_for_page(repo, page_map, name):
    mapped = page_map.get(name)
    if mapped:
        return mapped.replace("\\", "/"), "PAGE_MAP"
    slug = slug_for_page(name)
    rel = os.path.join("ssot", slug, slug + ".json")
    if os.path.exists(os.path.join(repo, rel)):
        return rel.replace("\\", "/"), "slug"
    return "", ""


def main(argv):
    gate = H.Gate("STUB WITH OBJECT",
                  "an object-backed root *_REVIEW.html page is below a review-sized floor")
    case = gate.expect_case("__synthetic_3kb_object_backed_stub__",
                            "a 3KB object-backed page with no review structure must fire")
    gate.requires_control()

    positive_fires = check_page(3000, True, 0)
    negative_silent = not check_page(400 * 1024, True, 3)
    if positive_fires:
        gate.saw(case)
    else:
        gate.broken("the positive control did not fire for a 3KB object-backed stub")
    gate.control(1, 0 if negative_silent else 1,
                 [] if negative_silent else ["400KB object-backed page with panels was flagged"],
                 accuses=True)
    if not negative_silent:
        gate.broken("the negative control flagged a 400KB object-backed page with panels")

    repo = H.repo_root()
    pages = root_review_pages(repo)
    if not pages:
        gate.broken("no root *_REVIEW.html pages found; this gate would be vacuous")
        gate.kinds({"root *_REVIEW.html pages": 0})
        gate.coverage(0, 0, "no root review pages exist outside the scan")
        return gate.report(denominator="0 root *_REVIEW.html pages scanned")

    page_map = load_page_map(repo, gate)
    rows = []
    counts = {
        "object-backed root review page": 0,
        "object-backed page below byte floor with trivial structure": 0,
        "object-backed page below byte floor with nontrivial structure": 0,
        "object-backed page at or above byte floor": 0,
        "tiny page with NO object (plain placeholder -- not a finding)": 0,
        "no-object page at or above byte floor": 0,
    }

    for name in pages:
        path = os.path.join(repo, name)
        try:
            with open(path, "rb") as fh:
                html = fh.read()
        except Exception as exc:
            gate.broken("%s could not be read: %s" % (name, exc))
            continue

        size = len(html)
        sections = structure_count(html)
        object_path, source = object_path_for_page(repo, page_map, name)
        has_object = bool(object_path)

        if has_object:
            counts["object-backed root review page"] += 1
            if size < BYTE_FLOOR:
                if sections < STRUCTURE_FLOOR:
                    counts["object-backed page below byte floor with trivial structure"] += 1
                else:
                    counts["object-backed page below byte floor with nontrivial structure"] += 1
            else:
                counts["object-backed page at or above byte floor"] += 1
        elif size < BYTE_FLOOR:
            counts["tiny page with NO object (plain placeholder -- not a finding)"] += 1
        else:
            counts["no-object page at or above byte floor"] += 1

        if check_page(size, has_object, sections):
            rows.append((name, size, sections, object_path, source))

    gate.kinds({
        "root *_REVIEW.html pages": len(pages),
        **counts,
    })
    gate.coverage(len(pages), len(pages),
                  "no root *_REVIEW.html pages are outside this filesystem scan")

    for name, size, sections, object_path, source in rows:
        gate.finding(
            name,
            "object-backed by %s via %s, but served %d bytes with %d panel/table/h2 "
            "marker(s); floor is %d bytes and %d markers"
            % (object_path, source, size, sections, BYTE_FLOOR, STRUCTURE_FLOOR),
            numerator=len(rows),
            denominator=counts["object-backed root review page"],
        )

    return gate.report(denominator="%d root *_REVIEW.html pages scanned" % len(pages))


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
