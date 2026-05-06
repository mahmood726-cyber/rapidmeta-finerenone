"""Make every review's `save()` self-heal on QuotaExceededError.

Pattern in every review:

    save() {
        try {
            localStorage.setItem('rapid_meta_<topic>_v1_0', JSON.stringify(this.state));
        } catch(e) {
            if (e.name === 'QuotaExceededError') showToast('Storage quota exceeded. Clear old version snapshots.');
        }

After patch:

    save() {
        try {
            localStorage.setItem('<MY_KEY>', JSON.stringify(this.state));
        } catch(e) {
            if (e.name === 'QuotaExceededError') {
                if (RapidMeta._pruneOtherReviews && RapidMeta._pruneOtherReviews('<MY_KEY>')) {
                    try { localStorage.setItem('<MY_KEY>', JSON.stringify(this.state)); }
                    catch(e2) { showToast('Storage quota exceeded. Clear old version snapshots.'); }
                } else {
                    showToast('Storage quota exceeded. Clear old version snapshots.');
                }
            }
        }
        ...

The `_pruneOtherReviews` helper is added near the top of RapidMeta. It
removes other reviews' rapid_meta_* keys (largest first) until ~1.5 MB
free, returns true on success.

Idempotent: skip if already patched (looks for `_pruneOtherReviews` ref).
"""
from __future__ import annotations
import sys, io, re
from pathlib import Path
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

REPO = Path(__file__).resolve().parent.parent

# Match both single-line and multi-line save() bodies. Whitespace tolerant.
SAVE_RE = re.compile(
    r"save\(\)\s*\{\s*"
    r"try\s*\{\s*"
    r"localStorage\.setItem\(\s*'([^']+)'\s*,\s*JSON\.stringify\(this\.state\)\s*\);\s*"
    r"\}\s*catch\s*\(e\)\s*\{\s*"
    r"if\s*\(\s*e\.name\s*===\s*'QuotaExceededError'\s*\)\s*"
    r"showToast\s*\(\s*'Storage quota exceeded\. Clear old version snapshots\.'\s*\);\s*"
    r"\}\s*\}",
    re.DOTALL,
)

# Helper to inject into RapidMeta object — placed right after the opening { of RapidMeta
HELPER_TAG = "/* AUTOPRUNE-HELPER-v1 */"
HELPER_JS = """
            /* AUTOPRUNE-HELPER-v1 */
            _pruneOtherReviews(myKey) {
                try {
                    const items = [];
                    for (let i = 0; i < localStorage.length; i++) {
                        const k = localStorage.key(i);
                        if (k === myKey) continue;
                        if (!k.startsWith('rapid_meta_')) continue;
                        items.push({ k, sz: (localStorage.getItem(k) || '').length });
                    }
                    items.sort((a, b) => b.sz - a.sz);
                    let freed = 0, removed = 0;
                    const TARGET = 1500 * 1024;
                    for (const it of items) {
                        localStorage.removeItem(it.k);
                        freed += it.sz;
                        removed++;
                        if (freed >= TARGET) break;
                    }
                    if (removed > 0 && typeof showToast === 'function') {
                        showToast('Auto-pruned ' + removed + ' other-review snapshots ('
                            + (freed/1024).toFixed(0) + ' kB) — saved successfully.');
                    }
                    return removed > 0;
                } catch (err) { return false; }
            },
"""

# Locator for "const RapidMeta = {" — we inject right after the opening {
RAPIDMETA_DECL_RE = re.compile(r"(const\s+RapidMeta\s*=\s*\{\s*\n)")


def patch_save(text: str) -> tuple[str, int]:
    def replace_save(m):
        key = m.group(1)
        # One-liner replacement — preserves single-line layout when source was single-line
        return (
            "save() { try { localStorage.setItem('" + key + "', JSON.stringify(this.state)); } "
            "catch(e) { if (e.name === 'QuotaExceededError') { "
            "if (this._pruneOtherReviews && this._pruneOtherReviews('" + key + "')) { "
            "try { localStorage.setItem('" + key + "', JSON.stringify(this.state)); } "
            "catch(e2) { showToast('Storage quota exceeded. Clear old version snapshots.'); } "
            "} else { showToast('Storage quota exceeded. Clear old version snapshots.'); } "
            "} } }"
        )

    text2, n = SAVE_RE.subn(replace_save, text)
    return text2, n


def patch_helper(text: str) -> tuple[str, int]:
    if HELPER_TAG in text:
        return text, 0
    new = RAPIDMETA_DECL_RE.sub(lambda m: m.group(1) + HELPER_JS, text, count=1)
    return new, 1 if new != text else 0


def main():
    files = sorted(REPO.glob("*_REVIEW.html"))
    n_save = 0
    n_helper = 0
    n_files = 0
    for hp in files:
        text = hp.read_text(encoding="utf-8", errors="replace")
        new = text
        new, ns = patch_save(new)
        new, nh = patch_helper(new)
        # Idempotent: skip if save() already rewritten AND helper already present
        if ns == 0 and nh == 0 and "_pruneOtherReviews && this._pruneOtherReviews" in text:
            continue
        if ns > 0 or nh > 0:
            hp.write_text(new, encoding="utf-8")
            n_save += ns
            n_helper += nh
            n_files += 1
    print(f"Files patched: {n_files}")
    print(f"  save() rewrites:    {n_save}")
    print(f"  helper insertions:  {n_helper}")


if __name__ == "__main__":
    main()
