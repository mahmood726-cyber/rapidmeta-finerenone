from __future__ import annotations

import re
from pathlib import Path


ROOT = Path(__file__).resolve().parent
PUBLISHED_HTML_FILES = [
    ROOT / "index.html",
    ROOT / "e156-submission" / "index.html",
    *sorted((ROOT / "e156-submission" / "assets").glob("*.html")),
]
URL_PATTERN = re.compile(r"""(?:href|src)=["']([^"']+)["']""", re.IGNORECASE)
SKIP_PREFIXES = ("http://", "https://", "mailto:", "tel:", "data:", "javascript:", "#")
SKIP_SUBSTRINGS = ("${", "{{", "}}")
STALE_URL_FRAGMENTS = (
    "github.com/mahmood726-cyber/finrenone",
    "mahmood726-cyber.github.io/finrenone/",
)


def iter_issues() -> list[str]:
    root_resolved = ROOT.resolve()
    issues: list[str] = []
    for html_path in PUBLISHED_HTML_FILES:
        text = html_path.read_text(encoding="utf-8", errors="ignore")
        rel_html = html_path.relative_to(ROOT)

        for fragment in STALE_URL_FRAGMENTS:
            if fragment in text:
                issues.append(f"{rel_html} contains stale URL fragment: {fragment}")

        for match in URL_PATTERN.finditer(text):
            url = match.group(1).strip()
            if not url or url.startswith(SKIP_PREFIXES) or any(token in url for token in SKIP_SUBSTRINGS):
                continue

            relative_target = url.split("?", 1)[0].split("#", 1)[0]
            target = (html_path.parent / relative_target).resolve()
            try:
                target.relative_to(root_resolved)
            except ValueError:
                continue

            if not target.exists():
                issues.append(f"{rel_html} -> {url} [missing: {target.relative_to(ROOT)}]")

    return issues


def main() -> int:
    issues = iter_issues()
    if issues:
        print("Pages link validation failed:")
        for issue in issues:
            print(f"- {issue}")
        return 1

    print(f"Pages link validation passed for {len(PUBLISHED_HTML_FILES)} HTML files.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
