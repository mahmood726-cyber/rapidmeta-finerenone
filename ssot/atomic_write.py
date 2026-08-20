"""Write an SSOT object or a delivered page so it is never briefly nothing.

WHY. On 2026-08-20 an applier ran `io.open(path, "w", encoding="utf-8", newline="\\\\n")`.
Python opened the file -- WHICH TRUNCATES IT -- and then raised `ValueError: illegal
newline value` while building the TextIOWrapper. THE FAILURE LANDED AFTER THE DESTRUCTION
AND BEFORE THE WRITE, and `apixaban-vte-prophylaxis.json` was zero bytes. It came back only
because it had been committed.

EVERY GUARD IN THIS PROJECT COMPARES NEW CONTENT TO OLD. `ssot_net_deletion_check.py` walks
both key sets; the appliers diff `_walk()`; `manuscript_guard.py` refuses a shrunken
manuscript. THERE WAS NO NEW CONTENT TO COMPARE. A zero-byte file does not parse, so a
checker that loads both sides raises before it reaches its comparison -- and on an `--apply`
run that had already crashed, nobody was reading.

DETECTABLE IS WEAKER THAN IMPOSSIBLE. The bytes are built COMPLETELY, in memory, before
anything on disk is touched. Then: temp sibling, flush, fsync, `os.replace`. `os.replace` is
atomic on NTFS and on POSIX, so the target holds either the old bytes or the new bytes and
never none. A failure at any earlier point leaves the original exactly as it was.

THE NEWLINE IS VALIDATED BEFORE THE TEMP FILE IS OPENED, because that is the exact argument
that caused the incident, and a helper that reproduced it would be worse than none.
"""
import io
import json
import os
import tempfile

VALID_NEWLINES = (None, "", "\n", "\r", "\r\n")


def detect_newline(path, default="\n"):
    """The line ending the file already uses. Per file -- alirocumab is CRLF, others LF."""
    if not os.path.exists(path):
        return default
    with io.open(path, "rb") as fh:
        head = fh.read(8192)
    return "\r\n" if b"\r\n" in head else "\n"


def write_text(path, text, newline=None):
    """Replace `path` with `text`, atomically. Returns the number of bytes written."""
    if newline is None:
        newline = detect_newline(path)
    if newline not in VALID_NEWLINES:
        raise ValueError(
            "newline %r is not one of %r. THIS IS THE ARGUMENT THAT TRUNCATED AN OBJECT ON "
            "2026-08-20: the open() succeeded, the file was emptied, and the ValueError "
            "arrived afterwards. It is checked HERE, before anything on disk is touched."
            % (newline, VALID_NEWLINES))
    if not isinstance(text, str):
        raise TypeError("write_text needs the complete string, not %r" % type(text))

    d = os.path.dirname(os.path.abspath(path)) or "."
    fd, tmp = tempfile.mkstemp(prefix=".atomic-", suffix=".tmp", dir=d)
    os.close(fd)
    try:
        with io.open(tmp, "w", encoding="utf-8", newline=newline) as fh:
            fh.write(text)
            fh.flush()
            os.fsync(fh.fileno())
        size = os.path.getsize(tmp)
        if size == 0 and text:
            raise IOError("the temp file is empty and the content was not. Refusing to "
                          "rename it over %s." % path)
        os.replace(tmp, path)          # atomic; target is old bytes or new bytes, never none
        return size
    finally:
        if os.path.exists(tmp):
            os.remove(tmp)


def write_json(path, obj, indent=1, newline=None, trailing_newline=True):
    """Serialise FIRST, then write atomically. The order is the point."""
    text = json.dumps(obj, indent=indent, ensure_ascii=False)
    if trailing_newline:
        text += "\n"
    return write_text(path, text, newline=newline)
