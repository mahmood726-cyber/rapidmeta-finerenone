"""Extract `realData` (and `NMA_CONFIG` if present) JS objects from every
*_REVIEW.html into JSON files for downstream audit.

Strategy: locate `var realData = { ... };` (or const/let), then balance braces
respecting JS strings. Convert the JS object literal to JSON via a small
JS5-style cleaner (single-quoted strings → double-quoted; trailing commas
removed; unquoted keys quoted; comments stripped).

Output: outputs/extraction_audit/data/<REVIEW_NAME>.json  (per-review)
        outputs/extraction_audit/data/_index.json          (manifest)
"""
from __future__ import annotations
import io, json, re, sys
from pathlib import Path

if __name__ == "__main__" and sys.platform == "win32" and hasattr(sys.stdout, "buffer"):
    try:
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    except Exception:
        pass

REPO = Path(__file__).resolve().parent.parent
OUT_DIR = REPO / "outputs" / "extraction_audit" / "data"
OUT_DIR.mkdir(parents=True, exist_ok=True)


def find_balanced_object(text: str, start: int) -> int:
    """Return index AFTER the closing `}` of the object beginning at text[start]=='{'."""
    assert text[start] == "{", f"expected '{{' at {start}, got {text[start]!r}"
    depth = 0
    i = start
    in_str: str | None = None
    while i < len(text):
        c = text[i]
        if in_str is not None:
            if c == "\\":
                i += 2
                continue
            if c == in_str:
                in_str = None
        else:
            if c in ('"', "'", "`"):
                in_str = c
            elif c == "/" and i + 1 < len(text) and text[i + 1] == "/":
                # line comment
                j = text.find("\n", i)
                i = j if j != -1 else len(text)
                continue
            elif c == "/" and i + 1 < len(text) and text[i + 1] == "*":
                j = text.find("*/", i + 2)
                i = (j + 2) if j != -1 else len(text)
                continue
            elif c == "{":
                depth += 1
            elif c == "}":
                depth -= 1
                if depth == 0:
                    return i + 1
        i += 1
    return -1


def js_object_to_json(s: str) -> str:
    """Convert a JS object literal to JSON via a character-level walker that
    knows the difference between strings and code positions:
    - converts ' and ` strings to "..."
    - strips // and /* */ comments
    - quotes unquoted identifier keys (only at code positions)
    - strips trailing commas
    - replaces undefined / NaN / Infinity with null
    """
    out: list[str] = []
    i = 0
    n = len(s)

    def append_string(open_quote: str) -> int:
        """Walk a string literal starting at s[i]==open_quote; emit JSON-quoted form."""
        nonlocal i
        j = i + 1
        buf = ['"']
        # JSON allows: \" \\ \/ \b \f \n \r \t \uXXXX. Anything else is illegal.
        json_ok = set('"\\/bfnrtu')
        while j < n:
            c = s[j]
            if c == "\\" and j + 1 < n:
                nxt = s[j + 1]
                if nxt in json_ok:
                    # Valid JSON escape — pass through verbatim. (Includes \" inside
                    # double-quoted strings, which is the most common case.)
                    buf.append(s[j:j+2]); j += 2; continue
                if nxt == open_quote:
                    # \' inside '...' or \` inside `...` — emit literal char (the
                    # JSON output uses double-quotes, so the JS-specific same-quote
                    # escape is not meaningful and would just be passed through).
                    buf.append(nxt); j += 2; continue
                # JS-only escape (e.g. \<, \>, \?, \xNN): JS treats as literal char.
                # Emit just the char (drop the backslash).
                buf.append(nxt); j += 2; continue
            if c == open_quote:
                buf.append('"'); j += 1; break
            if c == '"' and open_quote != '"':
                buf.append('\\"'); j += 1; continue
            if c == "\\":
                buf.append("\\\\"); j += 1; continue
            if c == "\n":
                buf.append("\\n"); j += 1; continue
            if c == "\r":
                buf.append("\\r"); j += 1; continue
            if c == "\t":
                buf.append("\\t"); j += 1; continue
            # Strip control chars that JSON disallows
            if ord(c) < 0x20:
                buf.append("\\u%04x" % ord(c)); j += 1; continue
            buf.append(c); j += 1
        out.append("".join(buf))
        return j

    while i < n:
        c = s[i]
        # Comments (only at code position)
        if c == "/" and i + 1 < n and s[i + 1] == "/":
            j = s.find("\n", i)
            i = j if j != -1 else n
            continue
        if c == "/" and i + 1 < n and s[i + 1] == "*":
            j = s.find("*/", i + 2)
            i = (j + 2) if j != -1 else n
            continue
        # Strings
        if c == '"':
            i = append_string('"'); continue
        if c == "'":
            i = append_string("'"); continue
        if c == "`":
            i = append_string("`"); continue
        # Identifier key? Look back through `out` (in reverse) to confirm we're at a key
        # position: previous non-space code char should be `{` or `,`.
        if c.isalpha() or c == "_" or c == "$":
            # Read identifier
            j = i + 1
            while j < n and (s[j].isalnum() or s[j] in "_$"):
                j += 1
            ident = s[i:j]
            # Look ahead: is the next non-space char a colon?
            k = j
            while k < n and s[k] in " \t\r\n":
                k += 1
            is_key = k < n and s[k] == ":"
            # Look back at `out` to find previous non-space char
            prev_code = None
            for blob in reversed(out):
                t = blob.rstrip(" \t\r\n")
                if not t:
                    continue
                prev_code = t[-1]
                break
            if is_key and prev_code in ("{", ",", None):
                out.append('"' + ident + '"')
                i = j
                continue
            # Identifier as value? Replace JS literals with JSON literals.
            if ident == "undefined" or ident == "NaN" or ident == "Infinity":
                out.append("null"); i = j; continue
            if ident == "true" or ident == "false" or ident == "null":
                out.append(ident); i = j; continue
            # Fallback: treat as bareword string (defensive, rare)
            out.append('"' + ident + '"'); i = j; continue
        # Comma handling.
        if c == ",":
            j = i + 1
            while j < n and s[j] in " \t\r\n":
                j += 1
            if j < n and s[j] in "}]":
                # Trailing comma — drop it.
                i = j; continue
            if j < n and s[j] == ",":
                # Consecutive commas (sparse-array hole). Insert null.
                out.append(","); out.append("null"); i = j; continue
        # Leading comma after `[` (sparse array). E.g. `[,{...}]` → `[null,{...}]`.
        if c == "[":
            j = i + 1
            while j < n and s[j] in " \t\r\n":
                j += 1
            if j < n and s[j] == ",":
                out.append("[null"); i = j; continue
        out.append(c); i += 1
    return "".join(out)


def extract_var(text: str, varname: str) -> str | None:
    """Locate `<varname> = { ... }` or `<varname>: { ... }` (object-literal property).
    Skips the rare prop-access reference (this.<varname>) by requiring no `.` before the name.
    """
    # Try: top-level declaration first
    pat_decl = re.compile(r"(?:const|var|let)\s+" + re.escape(varname) + r"\s*=\s*(?=\{)")
    m = pat_decl.search(text)
    if m:
        start = m.end()
        end = find_balanced_object(text, start)
        if end > 0:
            return text[start:end]
    # Fallback: property declaration `<varname>: { ... }` not preceded by `.`
    pat_prop = re.compile(r"(?<![\w.])" + re.escape(varname) + r"\s*:\s*(?=\{)")
    for m in pat_prop.finditer(text):
        start = m.end()
        end = find_balanced_object(text, start)
        if end > 0:
            block = text[start:end]
            # Heuristic: must contain at least one NCT key OR look big enough
            if "NCT" in block or len(block) > 300:
                return block
    return None


def extract_review(html_path: Path) -> dict | None:
    text = html_path.read_text(encoding="utf-8", errors="replace")
    rd_src = extract_var(text, "realData")
    nma_src = extract_var(text, "NMA_CONFIG")
    out: dict = {"file": html_path.name}

    def _try_parse(src: str, label: str) -> tuple[bool, object, str]:
        try:
            json_src = js_object_to_json(src)
            parsed = json.loads(json_src)
            return True, parsed, ""
        except Exception as e:
            return False, None, f"{type(e).__name__}: {e}"

    if rd_src:
        ok, parsed, err = _try_parse(rd_src, "realData")
        if ok:
            out["realData"] = parsed
        else:
            out["realData_parse_error"] = err
    else:
        out["realData_missing"] = True

    if nma_src:
        ok, parsed, err = _try_parse(nma_src, "NMA_CONFIG")
        if ok:
            out["NMA_CONFIG"] = parsed
        else:
            out["NMA_CONFIG_parse_error"] = err

    # Capture <title> + h1 for context
    title_m = re.search(r"<title>([^<]+)</title>", text)
    if title_m:
        out["title"] = title_m.group(1).strip()
    h1_m = re.search(r"<h1[^>]*>([^<]+)</h1>", text)
    if h1_m:
        out["h1"] = h1_m.group(1).strip()
    return out


def main() -> None:
    review_files = sorted(p for p in REPO.glob("*_REVIEW.html") if ".bak." not in p.name and ".pre_" not in p.name)
    print(f"Found {len(review_files)} review files")
    manifest: list[dict] = []
    n_ok, n_partial, n_fail = 0, 0, 0
    for hp in review_files:
        try:
            data = extract_review(hp)
        except Exception as e:
            data = {"file": hp.name, "extract_error": f"{type(e).__name__}: {e}"}
        out_path = OUT_DIR / (hp.stem + ".json")
        out_path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
        has_rd = "realData" in data
        has_pe = any(k.endswith("_parse_error") for k in data)
        if has_rd and not has_pe:
            n_ok += 1
        elif has_rd:
            n_partial += 1
        else:
            n_fail += 1
        manifest.append({
            "file": hp.name,
            "stem": hp.stem,
            "has_realData": has_rd,
            "has_NMA_CONFIG": "NMA_CONFIG" in data,
            "trials": len(data.get("realData") or {}) if has_rd else 0,
            "errors": [k for k in data if k.endswith("_error") or k.endswith("_missing")],
        })
    (OUT_DIR / "_index.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    print(f"OK: {n_ok}  partial: {n_partial}  fail: {n_fail}")


if __name__ == "__main__":
    main()
