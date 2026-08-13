import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "scripts"))

import fda_ocr  # noqa: E402


def test_text_layer_only_caches_textful_pages_and_marks_blocked_pages(tmp_path, monkeypatch):
    pdf_path = tmp_path / "mixed.pdf"
    pdf_path.write_bytes(b"%PDF-1.4\n% dummy fixture\n")

    pages = [
        fda_ocr.TextLayerPage(page_number=1, text="first page has enough visible text", chars=30),
        fda_ocr.TextLayerPage(page_number=2, text="", chars=0),
        fda_ocr.TextLayerPage(page_number=3, text="third page has enough visible text", chars=30),
    ]
    report = fda_ocr.ClassificationReport(
        pages=3,
        classification=fda_ocr.PdfClassification.MIXED,
        extractor="test",
        per_page_chars=[30, 0, 30],
        textful_pages=2,
        total_text_layer_chars=60,
        threshold=10,
        errors=[],
    )

    monkeypatch.setattr(fda_ocr, "classify_pdf", lambda *args, **kwargs: (report, pages))

    result = fda_ocr.extract_pdf(
        pdf_path,
        cache_dir=tmp_path / "cache",
        threshold=10,
        text_layer_only=True,
        force=True,
    )

    assert result.pages == 3
    assert result.pages_extracted == 2
    assert result.pages_blocked == 1
    assert result.ocr_engine_used == "not_attempted"

    cache_dir = Path(result.cache_dir)
    assert (cache_dir / "pages" / "page_0001.txt").read_text(encoding="utf-8")
    assert not (cache_dir / "pages" / "page_0002.txt").exists()
    assert (cache_dir / "pages" / "page_0003.txt").read_text(encoding="utf-8")

    manifest = (cache_dir / "manifest.json").read_text(encoding="utf-8")
    assert '"blocked_pages": [' in manifest
    assert '"pages_extracted": 2' in manifest
