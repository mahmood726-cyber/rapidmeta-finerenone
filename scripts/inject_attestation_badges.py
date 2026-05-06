"""Codemod: inject attestation badges (screening + extraction + lock)
next to the verdict badge in every review.

Idempotent. Skips files that already contain `vendor/attestation-badges.js`.
Reads from existing RapidMeta.state schema; no new state fields added.
"""
from __future__ import annotations
import sys, io, argparse, re
from pathlib import Path
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

REPO = Path(__file__).resolve().parent.parent

VERDICT_INCLUDE_RE = re.compile(r'<script\s+src="vendor/verdict-badge\.js"\s*></script>')
HEAD_CLOSE_RE = re.compile(r'</head>')

SCRIPT_TAG = (
    '\n    <!-- Attestation badges: dual screening + dual extraction + review-lock -->\n'
    '    <script src="vendor/attestation-badges.js"></script>\n'
)

VERDICT_CONTAINER_RE = re.compile(
    r'<div id="verdictBadgeContainer"></div>'
)

NEW_CONTAINER = (
    '<div id="verdictBadgeContainer"></div>'
    '<div id="attestationBadgesContainer"></div>'
)

# Append render call after existing VerdictBadge render
EXISTING_RENDER_RE = re.compile(
    r"if \(window\.VerdictBadge && document\.getElementById\('verdictBadgeContainer'\)\) \{\s*\n"
    r"\s*window\.VerdictBadge\.render\('#verdictBadgeContainer'\);\s*\n"
    r"\s*\}",
    re.MULTILINE,
)

NEW_RENDER = (
    "if (window.VerdictBadge && document.getElementById('verdictBadgeContainer')) {\n"
    "            window.VerdictBadge.render('#verdictBadgeContainer');\n"
    "        }\n"
    "        if (window.AttestationBadges && document.getElementById('attestationBadgesContainer')) {\n"
    "            window.AttestationBadges.render('#attestationBadgesContainer');\n"
    "        }"
)


def patch(text: str):
    if 'vendor/attestation-badges.js' in text:
        return text, "ALREADY"
    # Insert script tag after verdict-badge include
    vb = VERDICT_INCLUDE_RE.search(text)
    if vb:
        text = text[:vb.end()] + SCRIPT_TAG + text[vb.end():]
    else:
        head = HEAD_CLOSE_RE.search(text)
        if not head:
            return text, "NO_HEAD"
        text = text[:head.start()] + SCRIPT_TAG + text[head.start():]

    # Add new container next to verdictBadgeContainer
    if '<div id="attestationBadgesContainer">' not in text:
        text = VERDICT_CONTAINER_RE.sub(NEW_CONTAINER, text, count=1)

    # Wire render call
    text = EXISTING_RENDER_RE.sub(NEW_RENDER, text, count=1)

    return text, "PATCHED"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    files = sorted(REPO.glob("*_REVIEW.html"))
    print(f"Patching {len(files)} review HTMLs ...")
    counts = {"PATCHED": 0, "ALREADY": 0, "NO_HEAD": 0}
    for hp in files:
        text = hp.read_text(encoding="utf-8", errors="replace")
        new_text, status = patch(text)
        counts[status] = counts.get(status, 0) + 1
        if status == "PATCHED":
            if not args.dry_run:
                hp.write_text(new_text, encoding="utf-8")
            if counts["PATCHED"] <= 5:
                print(f"  PATCH    {hp.name}")
    print(f"\n=== Summary ===")
    for k, v in counts.items():
        print(f"  {k:15s} {v}")
    if args.dry_run:
        print("  DRY RUN — no files written.")


if __name__ == "__main__":
    main()
