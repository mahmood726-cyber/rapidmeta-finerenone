"""Idempotency tests for the post-audit40 fixer scripts.

Each script must satisfy:
    run(fixer, fixture) -> output_1
    run(fixer, output_1) -> output_2
    assert output_2 == output_1   # second run is a no-op

Same contract as scripts/tests/test_idempotency.py — this file just adds
coverage for the scripts shipped after the initial set:

    propagate_pi_k1.py
    fix_integrity_badge_contrast.py
    fix_conf_btn_contrast.py
    fix_card_meta_contrast.py
    fix_pico_input_labels.py
    fix_heading_order_lite.py
    externalize_plotly_inline.py
"""
from __future__ import annotations
import importlib.util
import sys
from pathlib import Path

import pytest

HERE = Path(__file__).resolve().parent.parent.parent
SCRIPTS = HERE / "scripts"
sys.path.insert(0, str(SCRIPTS))


def _load(modname: str):
    spec = importlib.util.spec_from_file_location(modname, SCRIPTS / f"{modname}.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


@pytest.fixture
def tmp_html(tmp_path):
    return tmp_path / "FIXTURE.html"


def _run_twice(fixer, path: Path) -> tuple[str, str]:
    fixer(path)
    a = path.read_text(encoding="utf-8")
    fixer(path)
    b = path.read_text(encoding="utf-8")
    return a, b


# ---------------------------------------------------------------------------
# fixtures
# ---------------------------------------------------------------------------
INTEGRITY_BADGE_HTML = """<!doctype html>
<html lang="en"><head><title>fx</title></head><body>
<div id="rapidmeta-integrity-badge" role="status" style="background:#16a34a;color:#fff;padding:12px 20px;font-family:system-ui;font-size:13.5px;border-bottom:3px solid #15803d;line-height:1.55;">
<div><strong>TRUSTWORTHY</strong><span style="font-size:11.5px;opacity:0.92;">x</span></div>
<div style="margin-top:6px;font-size:12.5px;opacity:0.95;">y</div>
<div><span style="background:rgba(255,255,255,0.18);padding:2px 6px;border-radius:3px;font-size:10.5px;">z</span></div>
<div style="margin-top:6px;font-size:10.5px;opacity:0.75;">w</div>
</div>
</body></html>
"""

CONF_BTN_HTML = """<!doctype html>
<html lang="en"><head><title>fx</title>
<style>.conf-btn { font-size: 10px; font-weight: 700; padding: 4px 12px; border-radius: 8px; background: transparent; color: #64748b; cursor: pointer; }</style>
</head><body><button class="conf-btn">90%</button></body></html>
"""

CARD_META_HTML = """<!doctype html>
<html lang="en"><head><title>fx</title>
<style>.card .pub{font-size:.7rem;color:#888;font-family:monospace}</style>
</head><body><div class="card"><span class="pub">x</span></div></body></html>
"""

PICO_INPUT_HTML = """<!doctype html>
<html lang="en"><head><title>fx</title></head><body>
<tbody><tr><td class="p-4"><input id="p-pop" class="w-full" value="Adults"></td></tr></tbody>
</body></html>
"""

LITE_H3_HTML = """<!doctype html>
<html lang="en"><head><title>fx</title></head><body>
<h1>Page title</h1>
<section id="tab-protocol">
<h3 style="color:#7dd3fc;font-size:14px;">PICO</h3>
<p>x</p>
</section>
</body></html>
"""


# ---------------------------------------------------------------------------
# tests
# ---------------------------------------------------------------------------
def test_propagate_pi_k1_idempotent(tmp_html):
    """tQuantile(..., k - 2) -> k - 1 should run once and then no-op."""
    tmp_html.write_text(
        "const tCritPI = (k >= 3) ? tQuantile(1 - (1 - confLevel) / 2, k - 2) : NaN;",
        encoding="utf-8",
    )
    mod = _load("propagate_pi_k1")
    a, b = _run_twice(lambda p: mod.patch_file(p), tmp_html)
    assert a == b
    assert "k - 1" in a and "k - 2" not in a


def test_fix_integrity_badge_contrast_idempotent(tmp_html):
    tmp_html.write_text(INTEGRITY_BADGE_HTML, encoding="utf-8")
    mod = _load("fix_integrity_badge_contrast")
    a, b = _run_twice(lambda p: mod.patch_file(p), tmp_html)
    assert a == b
    # Bg bumped, opacity attenuators removed
    assert "#15803d;color:#fff" in a
    assert "opacity:0.92" not in a
    assert "opacity:0.95" not in a
    assert "opacity:0.75" not in a


def test_fix_conf_btn_contrast_idempotent(tmp_html):
    tmp_html.write_text(CONF_BTN_HTML, encoding="utf-8")
    mod = _load("fix_conf_btn_contrast")
    a, b = _run_twice(lambda p: mod.patch_file(p), tmp_html)
    assert a == b
    assert "color: #94a3b8" in a or "color:#94a3b8" in a
    assert "color: #64748b" not in a


def test_fix_card_meta_contrast_idempotent(tmp_html):
    tmp_html.write_text(CARD_META_HTML, encoding="utf-8")
    mod = _load("fix_card_meta_contrast")
    a, b = _run_twice(lambda p: mod.patch_file(p), tmp_html)
    assert a == b
    assert "color:#666;" in a
    assert "color:#888;" not in a


def test_fix_pico_input_labels_idempotent(tmp_html):
    tmp_html.write_text(PICO_INPUT_HTML, encoding="utf-8")
    mod = _load("fix_pico_input_labels")
    a, b = _run_twice(lambda p: mod.patch_file(p), tmp_html)
    assert a == b
    assert 'aria-label="Population (PICO)"' in a


def test_fix_heading_order_lite_idempotent(tmp_html):
    """h3 -> h2 promotion should run once and then no-op."""
    # The fixer only operates on *_AUTO_REVIEW.html (filename suffix).
    p = tmp_html.parent / "FIXTURE_AUTO_REVIEW.html"
    p.write_text(LITE_H3_HTML, encoding="utf-8")
    mod = _load("fix_heading_order_lite")
    a, b = _run_twice(lambda fp: mod.patch_file(fp), p)
    assert a == b
    assert "<h2 style=" in a or "<h2>" in a
    assert "<h3" not in a


def test_minify_engine_block_idempotent(tmp_path):
    """Running minify_all_engines.mjs twice on the same page produces
    identical output the second time. We invoke it on a synthetic minimal
    HTML fixture so the test stays fast and offline."""
    import shutil
    import subprocess
    # HERE = tests parent dir's parent dir = repo root. (see top of file)
    repo = HERE

    fixture = tmp_path / "FIXTURE_REVIEW.html"
    # Build a synthetic page with a ~100+ KB engine block of redundant JS
    # that terser will compress significantly on pass 1 and ~not at all on pass 2.
    big_body = ("\n".join(
        f"  var __unused_{i} = 1 + 1; // comment {i}" for i in range(8000)
    )) + "\n  window.RapidMeta = { hello: function() { return 'hi'; } };\n"
    html = (
        "<!doctype html><html><head><title>fx</title></head><body>\n"
        f"<script>{big_body}</script>\n"
        "</body></html>\n"
    )
    fixture.write_text(html, encoding="utf-8")

    # Run minify_one_in_place via node — the script's batch entry point
    # only handles repo-root files. Use a one-shot wrapper instead.
    NODE = shutil.which("node") or "node.exe"
    one_shot = repo / "scripts" / "minify_engine_block.mjs"
    if not one_shot.exists():
        pytest.skip("minify_engine_block.mjs not present (terser not installed?)")
    out1 = tmp_path / "FIXTURE_REVIEW.pass1.html"
    out2 = tmp_path / "FIXTURE_REVIEW.pass2.html"
    p1 = subprocess.run(
        [NODE, str(one_shot), str(fixture), str(out1)],
        capture_output=True, text=True, timeout=60,
        cwd=str(repo),
    )
    if p1.returncode != 0:
        if "Cannot find package 'terser'" in p1.stderr:
            pytest.skip("terser not installed")
        raise AssertionError(f"pass-1 failed: {p1.stderr[:200]}")
    p2 = subprocess.run(
        [NODE, str(one_shot), str(out1), str(out2)],
        capture_output=True, text=True, timeout=60,
        cwd=str(repo),
    )
    assert p2.returncode == 0, f"pass-2 failed: {p2.stderr[:200]}"
    # Output bytes should be identical (or within a handful of bytes —
    # terser's behaviour is deterministic given fixed input).
    assert out1.read_bytes() == out2.read_bytes(), (
        "second minify pass changed the output — not idempotent"
    )


def test_fix_mojibake_em_dash_idempotent(tmp_html):
    """cp1252-roundtrip em-dash mojibake should be replaced on pass 1 and no-op on pass 2."""
    # Construct the mojibake byte sequence directly in the file.
    moji = b"\xc3\xa2\xe2\x82\xac\xe2\x80\x9d"   # cp1252 em-dash mojibake
    pre = b"library(metafor)  # validation (DL + HKSJ + Bayesian) "
    post = b" HR\r\nlibrary(meta)\r\n"
    tmp_html.write_bytes(pre + moji + post)
    mod = _load("fix_mojibake_em_dash")
    changed1, n1 = mod.patch_file(tmp_html)
    bytes_after_first = tmp_html.read_bytes()
    changed2, n2 = mod.patch_file(tmp_html)
    bytes_after_second = tmp_html.read_bytes()
    assert changed1 is True and n1 == 1
    assert changed2 is False and n2 == 0
    assert bytes_after_first == bytes_after_second
    # The em-dash UTF-8 (\xe2\x80\x94) should be present once.
    assert b"\xe2\x80\x94" in bytes_after_first
    # The mojibake should be gone.
    assert moji not in bytes_after_first
