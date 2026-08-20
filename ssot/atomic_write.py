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


def merge_not_overwrite(obj, key, new, stamp):
    """Merge `new` into obj[key], keeping anything the new value does not carry.

    `obj["risk_of_bias"] = {...}` DELETES whatever was there. On
    bococizumab-lipid-review that removed five leaf values -- the prior tool, state, why,
    consequence_carried_into_grade and what_would_close_it, which were the record of what
    the topic said BEFORE it was assessed. A net deletion from an SSOT object breaks one of
    the five genuinely enforced standing rules, and it was broken by the author who had
    spent the night writing about it.

    THE GUARD HELD AND THE WRITER DID NOT. What caught it was a leaf-by-leaf comparison
    against HEAD, not this applier and not the pre-commit hook -- which would have caught it
    one step later, at commit time.

    Measured across the four appliers written that night: the wholesale pattern was in ALL
    FOUR and caused a real loss in ONE. The other three were spared by luck -- two replaced
    an empty field and one re-authored identical content. WHOLESALE REPLACEMENT IS THE
    NATURAL WAY TO WRITE AN APPLIER AND IT WILL BE WRITTEN AGAIN, so the merge is a
    function rather than a habit.

    Any key the prior value held and the new one does not is preserved under
    `superseded_state_<stamp>`, so a reader comparing the two learns something a single
    current value cannot tell them.
    """
    prior = obj.get(key)
    obj[key] = new
    if not isinstance(prior, dict) or not prior:
        return 0
    kept = dict((k, v) for k, v in prior.items() if k not in new)
    if not kept:
        return 0
    new["superseded_state_%s" % stamp] = {
        "_why_this_is_kept": (
            "The prior value of `%s` held %d key(s) this assessment does not carry. "
            "Replacing a subtree wholesale DELETES them, and a net deletion from an SSOT "
            "object breaks a standing rule whether or not what replaced it is better. The "
            "prior state is the record of what this topic said before it was assessed."
            % (key, len(kept))),
        "prior": kept,
    }
    return len(kept)
