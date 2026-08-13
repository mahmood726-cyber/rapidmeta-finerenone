#!/usr/bin/env python
"""Text-layer aware extraction and OCR fallback for FDA review PDFs.

Classification is based on text extracted per page, not file size. A page is
treated as having a text layer when extraction yields at least
TEXT_LAYER_MIN_VISIBLE_CHARS_PER_PAGE normalized visible characters. The default
threshold is 50 because real FDA medical/statistical review pages with a text
layer usually produce hundreds or thousands of extractable characters, while
scanned pages produce zero; 50 prevents headers, footers, page numbers, and
stray artifacts from being misclassified as usable text.
"""

from __future__ import annotations

import argparse
import dataclasses
import enum
import hashlib
import importlib.util
import json
import os
import shutil
import subprocess
import sys
import tempfile
import time
from pathlib import Path
from typing import Any, Iterable


TEXT_LAYER_MIN_VISIBLE_CHARS_PER_PAGE = 50
DEFAULT_DPI = 300
CACHE_VERSION = 1
PAGE_SEPARATOR = "\n\n\f\n\n"


class PdfClassification(str, enum.Enum):
    HAS_TEXT_LAYER = "HAS_TEXT_LAYER"
    SCANNED = "SCANNED"
    MIXED = "MIXED"
    UNREADABLE = "UNREADABLE"


class FDAOcrError(RuntimeError):
    """Base error for FDA OCR pipeline failures."""


class OCREngineUnavailable(FDAOcrError):
    """Raised when a scanned or mixed PDF needs OCR but no engine is usable."""


class ExtractionFailed(FDAOcrError):
    """Raised when extraction would otherwise return empty text as success."""


@dataclasses.dataclass(frozen=True)
class TextLayerPage:
    page_number: int
    text: str
    chars: int
    error: str | None = None


@dataclasses.dataclass(frozen=True)
class ClassificationReport:
    pages: int
    classification: PdfClassification
    extractor: str
    per_page_chars: list[int]
    textful_pages: int
    total_text_layer_chars: int
    threshold: int
    errors: list[str]

    def to_json_dict(self) -> dict[str, Any]:
        data = dataclasses.asdict(self)
        data["classification"] = self.classification.value
        return data


@dataclasses.dataclass(frozen=True)
class OCRCapabilities:
    pymupdf_rasterize: bool
    pytesseract_package: bool
    tesseract_cmd: str | None
    easyocr_package: bool
    paddleocr_package: bool
    available_engines: list[str]
    notes: list[str]

    def to_json_dict(self) -> dict[str, Any]:
        return dataclasses.asdict(self)


@dataclasses.dataclass(frozen=True)
class ExtractionResult:
    path: str
    sha256: str
    pages: int
    classification: PdfClassification
    chars_extracted: int
    ocr_engine_used: str
    seconds: float
    cache_status: str
    cache_dir: str
    text_path: str
    metadata_path: str
    threshold: int
    text_layer_extractor: str
    errors: list[str]
    pages_extracted: int | None = None
    pages_blocked: int | None = None

    def to_json_dict(self) -> dict[str, Any]:
        data = dataclasses.asdict(self)
        data["classification"] = self.classification.value
        return data


def normalized_visible_char_count(text: str | None) -> int:
    """Count non-whitespace, non-NUL characters for text-layer detection."""
    if not text:
        return 0
    return sum(1 for char in text if char != "\x00" and not char.isspace())


def normalize_extracted_text(text: str | None) -> str:
    if not text:
        return ""
    return text.replace("\x00", "").replace("\r\n", "\n").replace("\r", "\n").strip()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _module_available(module_name: str) -> bool:
    return importlib.util.find_spec(module_name) is not None


def _tesseract_version_ok(command: str) -> bool:
    try:
        proc = subprocess.run(
            [command, "--version"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            timeout=5,
            check=False,
        )
    except (OSError, subprocess.SubprocessError):
        return False
    return proc.returncode == 0


def find_tesseract_command() -> str | None:
    candidates: list[str] = []
    env_cmd = os.environ.get("TESSERACT_CMD")
    if env_cmd:
        candidates.append(env_cmd)

    which_cmd = shutil.which("tesseract")
    if which_cmd:
        candidates.append(which_cmd)

    for env_var in ("ProgramFiles", "ProgramFiles(x86)", "LOCALAPPDATA"):
        base = os.environ.get(env_var)
        if base:
            candidates.append(str(Path(base) / "Tesseract-OCR" / "tesseract.exe"))

    seen: set[str] = set()
    for candidate in candidates:
        if candidate in seen:
            continue
        seen.add(candidate)
        candidate_path = Path(candidate)
        if candidate_path.exists() and _tesseract_version_ok(str(candidate_path)):
            return str(candidate_path)
        if shutil.which(candidate) and _tesseract_version_ok(candidate):
            return candidate
    return None


def detect_ocr_capabilities(preferred_engine: str = "auto") -> OCRCapabilities:
    pymupdf_available = _module_available("fitz")
    pytesseract_available = _module_available("pytesseract")
    easyocr_available = _module_available("easyocr")
    paddleocr_available = _module_available("paddleocr")
    tesseract_cmd = find_tesseract_command() if pytesseract_available else None

    notes: list[str] = []
    engines: list[str] = []
    if not pymupdf_available:
        notes.append("PyMuPDF is missing, so PDF pages cannot be rasterized for OCR.")
    else:
        if pytesseract_available and tesseract_cmd:
            engines.append("pytesseract+tesseract")
        elif pytesseract_available:
            notes.append("pytesseract is installed but the tesseract executable is missing.")

        if easyocr_available:
            engines.append("easyocr")
        if paddleocr_available:
            engines.append("paddleocr")

    if preferred_engine != "auto":
        engine_map = {
            "tesseract": "pytesseract+tesseract",
            "pytesseract": "pytesseract+tesseract",
            "easyocr": "easyocr",
            "paddleocr": "paddleocr",
        }
        requested = engine_map.get(preferred_engine)
        if requested is None:
            notes.append(f"Unknown OCR engine requested: {preferred_engine}")
            engines = []
        elif requested in engines:
            engines = [requested]
        else:
            notes.append(f"Requested OCR engine is not available: {preferred_engine}")
            engines = []

    return OCRCapabilities(
        pymupdf_rasterize=pymupdf_available,
        pytesseract_package=pytesseract_available,
        tesseract_cmd=tesseract_cmd,
        easyocr_package=easyocr_available,
        paddleocr_package=paddleocr_available,
        available_engines=engines,
        notes=notes,
    )


def no_ocr_install_message(capabilities: OCRCapabilities) -> str:
    detected = json.dumps(capabilities.to_json_dict(), indent=2, sort_keys=True)
    return (
        "OCR is required for this PDF, but no usable OCR engine is available.\n"
        "Detected OCR capability state:\n"
        f"{detected}\n\n"
        "Install one working OCR path on Windows, then rerun:\n"
        "  winget install --id UB-Mannheim.TesseractOCR -e\n"
        "  python -m pip install pymupdf pytesseract\n\n"
        "Alternative pure-Python OCR packages, if you prefer them:\n"
        "  python -m pip install pymupdf easyocr\n"
        "  python -m pip install pymupdf paddleocr\n\n"
        "If Tesseract is installed outside PATH, set TESSERACT_CMD to the "
        "tesseract executable before running this script."
    )


def _extract_with_pdfplumber(pdf_path: Path) -> tuple[list[TextLayerPage], list[str]]:
    errors: list[str] = []
    if not _module_available("pdfplumber"):
        return [], ["pdfplumber is not installed"]
    try:
        import pdfplumber  # type: ignore
    except Exception as exc:  # pragma: no cover - importlib handles normal absence
        return [], [f"pdfplumber import failed: {type(exc).__name__}: {exc}"]

    pages: list[TextLayerPage] = []
    try:
        with pdfplumber.open(str(pdf_path)) as pdf:
            for page_index, page in enumerate(pdf.pages):
                error = None
                try:
                    text = normalize_extracted_text(page.extract_text() or "")
                except Exception as exc:
                    text = ""
                    error = f"page {page_index + 1}: {type(exc).__name__}: {exc}"
                    errors.append(error)
                pages.append(
                    TextLayerPage(
                        page_number=page_index + 1,
                        text=text,
                        chars=normalized_visible_char_count(text),
                        error=error,
                    )
                )
    except Exception as exc:
        return [], [f"pdfplumber open failed: {type(exc).__name__}: {exc}"]
    return pages, errors


def _extract_with_pypdf(pdf_path: Path) -> tuple[list[TextLayerPage], list[str]]:
    errors: list[str] = []
    if not _module_available("pypdf"):
        return [], ["pypdf is not installed"]
    try:
        from pypdf import PdfReader  # type: ignore
    except Exception as exc:  # pragma: no cover - importlib handles normal absence
        return [], [f"pypdf import failed: {type(exc).__name__}: {exc}"]

    pages: list[TextLayerPage] = []
    try:
        reader = PdfReader(str(pdf_path))
        if getattr(reader, "is_encrypted", False):
            try:
                reader.decrypt("")
            except Exception as exc:
                errors.append(f"pypdf decrypt failed: {type(exc).__name__}: {exc}")
        for page_index, page in enumerate(reader.pages):
            error = None
            try:
                text = normalize_extracted_text(page.extract_text() or "")
            except Exception as exc:
                text = ""
                error = f"page {page_index + 1}: {type(exc).__name__}: {exc}"
                errors.append(error)
            pages.append(
                TextLayerPage(
                    page_number=page_index + 1,
                    text=text,
                    chars=normalized_visible_char_count(text),
                    error=error,
                )
            )
    except Exception as exc:
        return [], [f"pypdf open failed: {type(exc).__name__}: {exc}"]
    return pages, errors


def _extract_with_pymupdf(pdf_path: Path) -> tuple[list[TextLayerPage], list[str]]:
    errors: list[str] = []
    if not _module_available("fitz"):
        return [], ["PyMuPDF/fitz is not installed"]
    try:
        import fitz  # type: ignore
    except Exception as exc:  # pragma: no cover - importlib handles normal absence
        return [], [f"PyMuPDF import failed: {type(exc).__name__}: {exc}"]

    pages: list[TextLayerPage] = []
    try:
        with fitz.open(str(pdf_path)) as doc:
            for page_index in range(doc.page_count):
                error = None
                try:
                    page = doc.load_page(page_index)
                    text = normalize_extracted_text(page.get_text("text") or "")
                except Exception as exc:
                    text = ""
                    error = f"page {page_index + 1}: {type(exc).__name__}: {exc}"
                    errors.append(error)
                pages.append(
                    TextLayerPage(
                        page_number=page_index + 1,
                        text=text,
                        chars=normalized_visible_char_count(text),
                        error=error,
                    )
                )
    except Exception as exc:
        return [], [f"PyMuPDF open failed: {type(exc).__name__}: {exc}"]
    return pages, errors


def extract_text_layer_pages(
    pdf_path: Path,
    preferred_extractor: str = "auto",
) -> tuple[str, list[TextLayerPage], list[str]]:
    extractor_map = {
        "pdfplumber": _extract_with_pdfplumber,
        "pypdf": _extract_with_pypdf,
        "pymupdf": _extract_with_pymupdf,
    }
    extractors = [
        ("pdfplumber", _extract_with_pdfplumber),
        ("pypdf", _extract_with_pypdf),
        ("pymupdf", _extract_with_pymupdf),
    ]
    if preferred_extractor != "auto":
        if preferred_extractor not in extractor_map:
            return "none", [], [f"unknown text extractor requested: {preferred_extractor}"]
        pages, errors = extractor_map[preferred_extractor](pdf_path)
        return preferred_extractor if pages else "none", pages, errors

    attempts: list[tuple[str, list[TextLayerPage], list[str]]] = []
    for name, extractor in extractors:
        pages, errors = extractor(pdf_path)
        if pages:
            attempts.append((name, pages, errors))
        else:
            attempts.append((name, [], errors))

    usable = [attempt for attempt in attempts if attempt[1]]
    if not usable:
        all_errors = [f"{name}: {'; '.join(errors) or 'no pages'}" for name, _, errors in attempts]
        return "none", [], all_errors

    best_name, best_pages, best_errors = max(
        usable,
        key=lambda attempt: sum(page.chars for page in attempt[1]),
    )
    other_errors = [
        f"{name}: {'; '.join(errors)}"
        for name, _, errors in attempts
        if name != best_name and errors
    ]
    return best_name, best_pages, best_errors + other_errors


def classify_pdf(
    pdf_path: Path,
    threshold: int = TEXT_LAYER_MIN_VISIBLE_CHARS_PER_PAGE,
    preferred_extractor: str = "auto",
) -> tuple[ClassificationReport, list[TextLayerPage]]:
    extractor, pages, errors = extract_text_layer_pages(
        pdf_path, preferred_extractor=preferred_extractor
    )
    if not pages:
        report = ClassificationReport(
            pages=0,
            classification=PdfClassification.UNREADABLE,
            extractor=extractor,
            per_page_chars=[],
            textful_pages=0,
            total_text_layer_chars=0,
            threshold=threshold,
            errors=errors,
        )
        return report, []

    per_page_chars = [page.chars for page in pages]
    textful_pages = sum(chars >= threshold for chars in per_page_chars)
    total_chars = sum(per_page_chars)
    if textful_pages == len(pages):
        classification = PdfClassification.HAS_TEXT_LAYER
    elif textful_pages == 0:
        classification = PdfClassification.SCANNED
    else:
        classification = PdfClassification.MIXED

    report = ClassificationReport(
        pages=len(pages),
        classification=classification,
        extractor=extractor,
        per_page_chars=per_page_chars,
        textful_pages=textful_pages,
        total_text_layer_chars=total_chars,
        threshold=threshold,
        errors=errors,
    )
    return report, pages


def _atomic_write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(
        "w",
        encoding="utf-8",
        newline="\n",
        delete=False,
        dir=str(path.parent),
    ) as handle:
        handle.write(text)
        temp_name = handle.name
    os.replace(temp_name, path)


def _atomic_write_json(path: Path, payload: dict[str, Any]) -> None:
    text = json.dumps(payload, indent=2, sort_keys=True) + "\n"
    _atomic_write_text(path, text)


def _page_cache_path(pages_dir: Path, page_number: int) -> Path:
    return pages_dir / f"page_{page_number:04d}.txt"


def _read_nonempty_text(path: Path) -> str | None:
    if not path.exists():
        return None
    text = path.read_text(encoding="utf-8", errors="replace")
    if normalized_visible_char_count(text) == 0:
        return None
    return text


def _manifest_to_result(
    pdf_path: Path,
    sha256: str,
    cache_pdf_dir: Path,
    manifest_path: Path,
    text_path: Path,
    seconds: float,
) -> ExtractionResult:
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    text = text_path.read_text(encoding="utf-8", errors="replace")
    chars = normalized_visible_char_count(text)
    if chars == 0 and int(manifest.get("pages_extracted", manifest["pages"])) > 0:
        raise ExtractionFailed(
            f"Cached final text is empty for {pdf_path}; delete {cache_pdf_dir} or rerun with --force."
        )
    pages = int(manifest["pages"])
    page_sources = [str(source) for source in manifest.get("page_sources", [])]
    pages_extracted = int(
        manifest.get(
            "pages_extracted",
            sum(
                1
                for source in page_sources
                if source == "text_layer" or source == "cache" or source.startswith("ocr:")
            )
            or pages,
        )
    )
    pages_blocked = int(manifest.get("pages_blocked", max(0, pages - pages_extracted)))
    return ExtractionResult(
        path=str(pdf_path),
        sha256=sha256,
        pages=pages,
        classification=PdfClassification(manifest["classification"]),
        chars_extracted=chars,
        ocr_engine_used=str(manifest.get("ocr_engine_used", "none")),
        seconds=seconds,
        cache_status="hit",
        cache_dir=str(cache_pdf_dir),
        text_path=str(text_path),
        metadata_path=str(manifest_path),
        threshold=int(manifest.get("threshold", TEXT_LAYER_MIN_VISIBLE_CHARS_PER_PAGE)),
        text_layer_extractor=str(manifest.get("text_layer_extractor", "unknown")),
        errors=list(manifest.get("errors", [])),
        pages_extracted=pages_extracted,
        pages_blocked=pages_blocked,
    )


def _render_page_to_png(doc: Any, page_index: int, output_png: Path, dpi: int) -> None:
    import fitz  # type: ignore

    page = doc.load_page(page_index)
    scale = dpi / 72.0
    matrix = fitz.Matrix(scale, scale)
    pix = page.get_pixmap(matrix=matrix, colorspace=fitz.csRGB, alpha=False)
    pix.save(str(output_png))


def _ocr_with_tesseract(image_path: Path, capabilities: OCRCapabilities) -> str:
    import pytesseract  # type: ignore

    if capabilities.tesseract_cmd:
        pytesseract.pytesseract.tesseract_cmd = capabilities.tesseract_cmd
    return normalize_extracted_text(
        pytesseract.image_to_string(
            str(image_path),
            lang="eng",
            config="--oem 1 --psm 3",
        )
    )


def _ocr_with_easyocr(image_path: Path, state: dict[str, Any]) -> str:
    import easyocr  # type: ignore

    reader = state.get("easyocr_reader")
    if reader is None:
        reader = easyocr.Reader(["en"], gpu=False)
        state["easyocr_reader"] = reader
    chunks = reader.readtext(str(image_path), detail=0, paragraph=True)
    return normalize_extracted_text("\n".join(str(chunk) for chunk in chunks))


def _extract_paddle_text(result: Any) -> list[str]:
    texts: list[str] = []
    if isinstance(result, str):
        return [result]
    if isinstance(result, (list, tuple)):
        # Common PaddleOCR shape: [[box, (text, score)], ...].
        if len(result) >= 2 and isinstance(result[1], (list, tuple)) and result[1]:
            maybe_text = result[1][0]
            if isinstance(maybe_text, str):
                texts.append(maybe_text)
        for item in result:
            texts.extend(_extract_paddle_text(item))
    return texts


def _ocr_with_paddleocr(image_path: Path, state: dict[str, Any]) -> str:
    from paddleocr import PaddleOCR  # type: ignore

    ocr = state.get("paddleocr")
    if ocr is None:
        try:
            ocr = PaddleOCR(use_angle_cls=True, lang="en", show_log=False)
        except TypeError:
            ocr = PaddleOCR(use_angle_cls=True, lang="en")
        state["paddleocr"] = ocr
    try:
        result = ocr.ocr(str(image_path), cls=True)
    except TypeError:
        result = ocr.ocr(str(image_path))
    return normalize_extracted_text("\n".join(_extract_paddle_text(result)))


def _ocr_image(
    image_path: Path,
    capabilities: OCRCapabilities,
    state: dict[str, Any],
) -> tuple[str, str]:
    failures: list[str] = []
    for engine in capabilities.available_engines:
        try:
            if engine == "pytesseract+tesseract":
                text = _ocr_with_tesseract(image_path, capabilities)
            elif engine == "easyocr":
                text = _ocr_with_easyocr(image_path, state)
            elif engine == "paddleocr":
                text = _ocr_with_paddleocr(image_path, state)
            else:
                failures.append(f"{engine}: unsupported engine name")
                continue
        except Exception as exc:
            failures.append(f"{engine}: {type(exc).__name__}: {exc}")
            continue
        return text, engine
    raise ExtractionFailed("All OCR engines failed: " + "; ".join(failures))


def _ocr_page(
    doc: Any,
    page_index: int,
    cache_pdf_dir: Path,
    dpi: int,
    capabilities: OCRCapabilities,
    state: dict[str, Any],
) -> tuple[str, str]:
    with tempfile.TemporaryDirectory(prefix="render_", dir=str(cache_pdf_dir)) as tmp_dir:
        image_path = Path(tmp_dir) / f"page_{page_index + 1:04d}.png"
        _render_page_to_png(doc, page_index, image_path, dpi)
        return _ocr_image(image_path, capabilities, state)


def _load_completed_cache(
    pdf_path: Path,
    sha256: str,
    cache_pdf_dir: Path,
    manifest_path: Path,
    text_path: Path,
    force: bool,
    start_time: float,
) -> ExtractionResult | None:
    if force or not manifest_path.exists() or not text_path.exists():
        return None
    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    if not manifest.get("completed"):
        return None
    if manifest.get("sha256") != sha256:
        return None
    seconds = time.perf_counter() - start_time
    return _manifest_to_result(pdf_path, sha256, cache_pdf_dir, manifest_path, text_path, seconds)


def extract_pdf(
    pdf_path: Path | str,
    cache_dir: Path | str = Path("outputs") / "fda_ocr_cache",
    threshold: int = TEXT_LAYER_MIN_VISIBLE_CHARS_PER_PAGE,
    dpi: int = DEFAULT_DPI,
    preferred_engine: str = "auto",
    force: bool = False,
    text_layer_only: bool = False,
    text_layer_extractor: str = "auto",
) -> ExtractionResult:
    start = time.perf_counter()
    source_path = Path(pdf_path)
    if not source_path.exists():
        raise FileNotFoundError(source_path)
    if source_path.suffix.lower() != ".pdf":
        raise ValueError(f"Not a PDF: {source_path}")

    digest = sha256_file(source_path)
    cache_pdf_dir = Path(cache_dir) / digest
    pages_dir = cache_pdf_dir / "pages"
    manifest_path = cache_pdf_dir / "manifest.json"
    partial_manifest_path = cache_pdf_dir / "manifest.partial.json"
    text_path = cache_pdf_dir / "text.txt"
    cache_pdf_dir.mkdir(parents=True, exist_ok=True)
    pages_dir.mkdir(parents=True, exist_ok=True)

    cached = _load_completed_cache(
        source_path,
        digest,
        cache_pdf_dir,
        manifest_path,
        text_path,
        force,
        start,
    )
    if cached:
        return cached

    classification, text_layer_pages = classify_pdf(
        source_path,
        threshold=threshold,
        preferred_extractor=text_layer_extractor,
    )
    if classification.classification == PdfClassification.UNREADABLE:
        raise ExtractionFailed(
            f"PDF is unreadable: {source_path}. Errors: {'; '.join(classification.errors)}"
        )

    partial_manifest = {
        "cache_version": CACHE_VERSION,
        "completed": False,
        "sha256": digest,
        "source_name": source_path.name,
        "source_size_bytes": source_path.stat().st_size,
        "pages": classification.pages,
        "classification": classification.classification.value,
        "threshold": threshold,
        "threshold_rationale": (
            f"A page is text-layer positive at {threshold} normalized visible characters; "
            "FDA text-layer review pages are usually far above this, while scans "
            "return zero or near-zero extraction."
        ),
        "text_layer_only": text_layer_only,
        "text_layer_extractor": classification.extractor,
        "per_page_text_layer_chars": classification.per_page_chars,
        "errors": classification.errors,
    }
    _atomic_write_json(partial_manifest_path, partial_manifest)

    capabilities: OCRCapabilities | None = None
    if (
        classification.classification in {PdfClassification.SCANNED, PdfClassification.MIXED}
        and not text_layer_only
    ):
        capabilities = detect_ocr_capabilities(preferred_engine=preferred_engine)
        if not capabilities.available_engines:
            raise OCREngineUnavailable(no_ocr_install_message(capabilities))

    page_texts: list[str] = []
    page_sources: list[str] = []
    ocr_engines_used: list[str] = []
    ocr_state: dict[str, Any] = {}
    pages_extracted = 0
    blocked_pages: list[int] = []

    doc = None
    try:
        if capabilities:
            import fitz  # type: ignore

            doc = fitz.open(str(source_path))
        for page in text_layer_pages:
            page_cache = _page_cache_path(pages_dir, page.page_number)
            cached_page = None if force else _read_nonempty_text(page_cache)
            if cached_page is not None:
                page_texts.append(cached_page)
                page_sources.append("cache")
                pages_extracted += 1
                continue

            needs_ocr = page.chars < threshold
            if needs_ocr:
                if text_layer_only:
                    page_texts.append("")
                    page_sources.append("blocked:no_text_layer")
                    blocked_pages.append(page.page_number)
                    continue
                if not capabilities or doc is None:
                    raise OCREngineUnavailable(
                        "Internal error: OCR was required but no OCR capabilities were prepared."
                    )
                text, engine = _ocr_page(
                    doc=doc,
                    page_index=page.page_number - 1,
                    cache_pdf_dir=cache_pdf_dir,
                    dpi=dpi,
                    capabilities=capabilities,
                    state=ocr_state,
                )
                page_sources.append(f"ocr:{engine}")
                if engine not in ocr_engines_used:
                    ocr_engines_used.append(engine)
            else:
                text = page.text
                page_sources.append("text_layer")

            _atomic_write_text(page_cache, text)
            page_texts.append(text)
            if normalized_visible_char_count(text) > 0:
                pages_extracted += 1
    finally:
        if doc is not None:
            doc.close()

    final_text = PAGE_SEPARATOR.join(page_texts).strip()
    final_chars = normalized_visible_char_count(final_text)
    if final_chars == 0 and not text_layer_only:
        raise ExtractionFailed(f"No text extracted from {source_path}; refusing empty-text success.")

    _atomic_write_text(text_path, final_text + "\n")
    seconds = time.perf_counter() - start
    if ocr_engines_used:
        ocr_engine_used = ",".join(ocr_engines_used)
    elif text_layer_only and blocked_pages:
        ocr_engine_used = "not_attempted"
    else:
        ocr_engine_used = "none"
    final_manifest = {
        **partial_manifest,
        "completed": True,
        "chars_extracted": final_chars,
        "pages_extracted": pages_extracted,
        "pages_blocked": len(blocked_pages),
        "blocked_pages": blocked_pages,
        "ocr_engine_used": ocr_engine_used,
        "ocr_capabilities": capabilities.to_json_dict() if capabilities else None,
        "page_sources": page_sources,
        "seconds": seconds,
        "text_file": text_path.name,
    }
    _atomic_write_json(manifest_path, final_manifest)
    try:
        partial_manifest_path.unlink()
    except FileNotFoundError:
        pass

    return ExtractionResult(
        path=str(source_path),
        sha256=digest,
        pages=classification.pages,
        classification=classification.classification,
        chars_extracted=final_chars,
        ocr_engine_used=ocr_engine_used,
        seconds=seconds,
        cache_status="miss" if not force else "forced",
        cache_dir=str(cache_pdf_dir),
        text_path=str(text_path),
        metadata_path=str(manifest_path),
        threshold=threshold,
        text_layer_extractor=classification.extractor,
        errors=classification.errors,
        pages_extracted=pages_extracted,
        pages_blocked=len(blocked_pages),
    )


def discover_pdfs(paths: Iterable[str]) -> list[Path]:
    discovered: list[Path] = []
    seen: set[Path] = set()
    for raw_path in paths:
        path = Path(raw_path)
        if path.is_file() and path.suffix.lower() == ".pdf":
            candidates = [path]
        elif path.is_dir():
            candidates = []
            for root, _, files in os.walk(path, onerror=lambda _: None):
                root_path = Path(root)
                for filename in files:
                    candidate = root_path / filename
                    if candidate.suffix.lower() == ".pdf":
                        candidates.append(candidate)
            candidates.sort()
        else:
            candidates = []
        for candidate in candidates:
            resolved = candidate.resolve()
            if resolved not in seen:
                seen.add(resolved)
                discovered.append(candidate)
    return discovered


def _format_result_line(result: ExtractionResult) -> str:
    pages_extracted = result.pages_extracted if result.pages_extracted is not None else result.pages
    pages_blocked = result.pages_blocked if result.pages_blocked is not None else 0
    return (
        f"{Path(result.path).name}\t"
        f"pages={result.pages}\t"
        f"pages_extracted={pages_extracted}\t"
        f"pages_blocked={pages_blocked}\t"
        f"classification={result.classification.value}\t"
        f"chars={result.chars_extracted}\t"
        f"ocr={result.ocr_engine_used}\t"
        f"seconds={result.seconds:.3f}\t"
        f"cache={result.cache_status}"
    )


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Extract FDA review PDF text with text-layer classification, OCR fallback, "
            "SHA-256 cache, and per-page resumability."
        )
    )
    parser.add_argument(
        "paths",
        nargs="*",
        help="PDF files or directories to scan recursively. Defaults to the current directory.",
    )
    parser.add_argument(
        "--cache-dir",
        default=str(Path("outputs") / "fda_ocr_cache"),
        help="Directory for SHA-256 keyed cache output.",
    )
    parser.add_argument(
        "--threshold",
        type=int,
        default=TEXT_LAYER_MIN_VISIBLE_CHARS_PER_PAGE,
        help="Minimum normalized visible chars per page for text-layer-positive classification.",
    )
    parser.add_argument("--dpi", type=int, default=DEFAULT_DPI, help="Rasterization DPI for OCR pages.")
    parser.add_argument(
        "--engine",
        choices=["auto", "tesseract", "pytesseract", "easyocr", "paddleocr"],
        default="auto",
        help="Preferred OCR engine. Auto uses the first usable detected engine.",
    )
    parser.add_argument("--force", action="store_true", help="Ignore completed cache and re-extract.")
    parser.add_argument(
        "--text-layer-only",
        action="store_true",
        help=(
            "Cache only pages that already have a text layer. Pages below the "
            "threshold are marked blocked and OCR is not attempted."
        ),
    )
    parser.add_argument(
        "--text-extractor",
        choices=["auto", "pdfplumber", "pypdf", "pymupdf"],
        default="auto",
        help="Text-layer extractor to use before any OCR decision.",
    )
    parser.add_argument("--json", action="store_true", help="Emit one JSON object per input PDF.")
    parser.add_argument(
        "--explain-threshold",
        action="store_true",
        help="Print the default threshold rationale before processing.",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_arg_parser()
    args = parser.parse_args(argv)
    if args.explain_threshold:
        print(
            "Threshold: "
            f"{args.threshold} normalized visible chars/page. "
            "Rationale: FDA text-layer pages usually produce hundreds or thousands "
            "of characters, while scans return zero; this cutoff avoids treating "
            "headers, footers, page numbers, or stray artifacts as a real text layer."
        )

    input_paths = args.paths or ["."]
    pdfs = discover_pdfs(input_paths)
    if not pdfs:
        print("No PDF files found.", file=sys.stderr)
        return 1

    failures = 0
    for pdf_path in pdfs:
        try:
            result = extract_pdf(
                pdf_path=pdf_path,
                cache_dir=args.cache_dir,
                threshold=args.threshold,
                dpi=args.dpi,
                preferred_engine=args.engine,
                force=args.force,
                text_layer_only=args.text_layer_only,
                text_layer_extractor=args.text_extractor,
            )
        except Exception as exc:
            failures += 1
            if args.json:
                payload = {
                    "path": str(pdf_path),
                    "ok": False,
                    "error_type": type(exc).__name__,
                    "error": str(exc),
                }
                print(json.dumps(payload, sort_keys=True))
            else:
                print(f"ERROR\t{pdf_path}\t{type(exc).__name__}: {exc}", file=sys.stderr)
            continue

        if args.json:
            payload = {"ok": True, **result.to_json_dict()}
            print(json.dumps(payload, sort_keys=True))
        else:
            print(_format_result_line(result))
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
