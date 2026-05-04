"""More robust fix for negative-HR -> MD estimandType. Iterates each line; if a
line has `publishedHR:` AND any of publishedHR/hrLCI/hrUCI is negative, ensure
the same line has `estimandType: 'MD',` (insert if absent, replace if 'HR').
"""
from __future__ import annotations
import sys, io, re
from pathlib import Path
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

REPO = Path("C:/Projects/Finrenone")

# Match a SINGLE LINE like "...publishedHR: X, hrLCI: Y, hrUCI: Z..."
LINE_RE = re.compile(
    r"publishedHR:\s*(-?[\d.eE+]+),\s*hrLCI:\s*(-?[\d.eE+]+),\s*hrUCI:\s*(-?[\d.eE+]+)"
)


def main():
    review_files = sorted(REPO.glob("*_REVIEW.html"))
    n_changed = 0
    files_modified = 0

    for hp in review_files:
        text = hp.read_text(encoding="utf-8", errors="replace")
        lines = text.splitlines(keepends=True)
        modified = False

        for i, line in enumerate(lines):
            m = LINE_RE.search(line)
            if not m:
                continue
            try:
                ph = float(m.group(1))
                lci = float(m.group(2))
                uci = float(m.group(3))
            except ValueError:
                continue
            if ph >= 0 and lci >= 0 and uci >= 0:
                continue  # all positive — skip

            # Has any negative -> ensure estimandType: 'MD' is on this line
            if "estimandType: 'MD'" in line:
                continue  # already fixed
            if re.search(r"estimandType:\s*'HR'", line):
                # Replace HR with MD
                lines[i] = re.sub(r"estimandType:\s*'HR'", "estimandType: 'MD'", line)
                modified = True
                n_changed += 1
                # Find name for log
                name_m = re.search(r"name:\s*'([^']+)'", line)
                name = name_m.group(1) if name_m else "(unknown)"
                print(f"  REPLACE-ET {hp.name}::{name} (HR->MD)")
                continue
            # No estimandType in line — insert before publishedHR
            new_line = line[:m.start()] + "estimandType: 'MD', " + line[m.start():]
            lines[i] = new_line
            modified = True
            n_changed += 1
            name_m = re.search(r"name:\s*'([^']+)'", line)
            name = name_m.group(1) if name_m else "(unknown)"
            print(f"  INSERT-ET  {hp.name}::{name}")

        if modified:
            hp.write_text("".join(lines), encoding="utf-8")
            files_modified += 1

    print(f"\n=== Summary ===")
    print(f"  Files modified: {files_modified}")
    print(f"  Trial blocks fixed: {n_changed}")


if __name__ == "__main__":
    main()
