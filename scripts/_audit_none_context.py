"""Audit every bare `None` in FULL_REVIEW files to confirm it sits in JS object-value position."""
import re
from pathlib import Path

None_word_re = re.compile(r'\bNone\b')
# JS object value or list element position: preceded by ':' or ',', followed by ',' '}' ']' or newline.
ok_pos_re = re.compile(r"[:,]\s*None\s*(?=[,}\]\n])")


def mask_strings(t: str) -> str:
    """Replace contents of single/double-quoted strings with blanks."""
    out = []
    i = 0
    n = len(t)
    while i < n:
        c = t[i]
        if c in ("'", '"'):
            quote = c
            j = i + 1
            while j < n and t[j] != quote:
                if t[j] == "\\":
                    j += 2
                else:
                    j += 1
            out.append(" " * max(1, j - i + 1))
            i = j + 1
        else:
            out.append(c)
            i += 1
    return "".join(out)


def main():
    files = sorted(Path(".").glob("*_FULL_REVIEW.html"))
    issue = safe = 0
    unsafe_samples = []
    for p in files:
        txt = p.read_text(encoding="utf-8", errors="replace")
        masked = mask_strings(txt)
        for m in None_word_re.finditer(masked):
            s = max(0, m.start() - 14)
            e = min(len(masked), m.end() + 14)
            ctx = masked[s:e]
            # check context centred on the None we just found
            local = txt[s:e]
            if ok_pos_re.search(masked, s, e) is None:
                issue += 1
                if len(unsafe_samples) < 8:
                    unsafe_samples.append((p.name, local))
            else:
                safe += 1
    print(f"files: {len(files):,}, safe-positioned `None` (=>null): {safe:,}, unsafe (other): {issue}")
    for fn, ctx in unsafe_samples:
        print("UNSAFE:", fn, "->", repr(ctx))


if __name__ == "__main__":
    main()
