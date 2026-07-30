#!/usr/bin/env python
"""Inject (or re-inject) the app-local validity layer into RIVAROXABAN_VASC_REVIEW.html.

Idempotent: if the marked block is already present it is replaced, so this can be
re-run after editing scripts/rivaroxaban_vasc_validity_layer.js. Run from repo root.
"""
import io
import sys
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

TARGET = Path("RIVAROXABAN_VASC_REVIEW.html")
SOURCE = Path("scripts/rivaroxaban_vasc_validity_layer.js")
START = "<!-- /* RIVAROXABAN_VALIDITY_LAYER */ -->"
END = "<!-- /* END RIVAROXABAN_VALIDITY_LAYER */ -->"
OPEN_TAG = "<scr" + "ipt>"
CLOSE_TAG = "</scr" + "ipt>"


def main():
    if not TARGET.exists() or not SOURCE.exists():
        print("FAIL: run from repo root; target or source missing")
        return 1

    js = SOURCE.read_text(encoding="utf-8")
    if CLOSE_TAG in js:
        print("FAIL: literal close tag inside JS would terminate the script block early")
        return 1

    html = TARGET.read_text(encoding="utf-8")
    block = "\n".join([START, OPEN_TAG, js, CLOSE_TAG, END, ""])

    if START in html:
        i = html.index(START)
        j = html.index(END) + len(END)
        html = html[:i] + block.rstrip("\n") + html[j:]
        action = "replaced"
    else:
        i = html.rfind("</body>")
        if i < 0:
            print("FAIL: no </body> found")
            return 1
        html = html[:i] + "\n" + block + html[i:]
        action = "inserted"

    TARGET.write_text(html, encoding="utf-8", newline="\n")

    opens = html.count("<div ") + html.count("<div>")
    closes = html.count("</div>")
    print(f"OK: validity layer {action}; div open={opens} close={closes} "
          f"{'BALANCED' if opens == closes else 'IMBALANCED'}")
    return 0 if opens == closes else 1


if __name__ == "__main__":
    raise SystemExit(main())
