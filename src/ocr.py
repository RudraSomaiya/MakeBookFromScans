"""PaddleOCR orchestration with compatibility for supported PaddleOCR APIs."""
from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

from tqdm import tqdm

from config import Settings
from .cleaner import clean_pages
from .pdf_loader import page_count, page_images
from .report import write_report
from .utils import timer

LOGGER = logging.getLogger(__name__)


def _find_ocr_fields(value: Any) -> tuple[list[Any], list[Any]]:
    """Find PaddleOCR 3.x recognition fields in any supported result wrapper."""
    if isinstance(value, dict):
        if "rec_texts" in value:
            return value.get("rec_texts", []), value.get("rec_scores", [])
        for child in value.values():
            texts, scores = _find_ocr_fields(child)
            if texts:
                return texts, scores
    elif isinstance(value, (list, tuple)):
        for child in value:
            texts, scores = _find_ocr_fields(child)
            if texts:
                return texts, scores
    return [], []


class LocalOcr:
    """Lazy PaddleOCR wrapper; no image or text leaves the local process."""
    def __init__(self, settings: Settings) -> None:
        try:
            import paddle  # noqa: F401
        except ImportError as exc:
            raise RuntimeError(
                "PaddlePaddle is not installed in this Python environment. "
                "Install paddlepaddle-gpu in the active .venv. Do not use "
                "'uv add paddle'; the required package is paddlepaddle-gpu."
            ) from exc
        from paddleocr import PaddleOCR
        # PaddleOCR 2.x uses ``use_gpu`` while PaddleOCR 3.x uses ``device``
        # and rejects older options such as ``show_log``. Try the modern API
        # first, then fall back for installations pinned to the 2.x API.
        if settings.use_gpu:
            try:
                self.engine = PaddleOCR(lang=settings.language, device="gpu")
            except (TypeError, ValueError):
                self.engine = PaddleOCR(lang=settings.language, use_gpu=True)
        else:
            try:
                self.engine = PaddleOCR(lang=settings.language, device="cpu")
            except (TypeError, ValueError):
                self.engine = PaddleOCR(lang=settings.language, use_gpu=False)

    def lines(self, image: Any, min_confidence: float = 0.30) -> tuple[list[str], float]:
        # PaddleOCR 3.x exposes predict() and returns OCRResult objects;
        # PaddleOCR 2.x exposes ocr(..., cls=True) and nested lists.
        if hasattr(self.engine, "predict"):
            # PaddleOCR 3.x accepts a NumPy array or path, but not PIL.Image.
            import numpy as np
            if hasattr(image, "convert"):
                image = np.asarray(image.convert("RGB"))
            result = list(self.engine.predict(image))
            lines, scores = [], []
            for item in result:
                data = item.json if hasattr(item, "json") else item
                if callable(data):
                    data = data()
                if isinstance(data, str):
                    import json
                    data = json.loads(data)
                # PaddleOCR 3.x uses these fields in its OCRResult JSON.
                texts, item_scores = _find_ocr_fields(data)
                for index, text in enumerate(texts):
                    score = float(item_scores[index]) if index < len(item_scores) else 1.0
                    if str(text).strip() and score >= min_confidence:
                        lines.append(str(text))
                        scores.append(score)
            return lines, (sum(scores) / len(scores) if scores else 0.0)

        result = self.engine.ocr(image, cls=True)
        # PaddleOCR 2.x returns [[[[box], (text, score)], ...]].
        entries = result[0] if result and isinstance(result[0], list) else result or []
        lines, scores = [], []
        for entry in entries:
            if len(entry) < 2:
                continue
            text_score = entry[1]
            if isinstance(text_score, (tuple, list)) and len(text_score) >= 2:
                text, score = str(text_score[0]), float(text_score[1])
                lines.append(text)
                scores.append(score)
        return lines, (sum(scores) / len(scores) if scores else 0.0)


def process_book(settings: Settings) -> None:
    pdfs = sorted(settings.book_dir.glob("*.pdf"))
    if not pdfs:
        raise FileNotFoundError(f"No PDF files found in {settings.book_dir.resolve()}")
    ocr = LocalOcr(settings)
    reports: list[dict[str, Any]] = []
    for pdf in pdfs:
        failed, warnings, pages, confidence = [], [], [], []
        with timer() as elapsed:
            for page_no, image in tqdm(page_images(pdf, settings.render_dpi, settings.max_image_dimension), total=page_count(pdf), desc=pdf.name):
                for attempt in range(settings.max_retries + 1):
                    try:
                        lines, score = ocr.lines(image, settings.min_confidence)
                        if not lines:
                            raise RuntimeError("OCR returned no text; input may have been ignored")
                        pages.append(lines); confidence.append(score)
                        break
                    except Exception as exc:
                        if attempt == settings.max_retries:
                            failed.append(page_no); warnings.append(f"Page {page_no}: {exc}")
                            pages.append([])
                        else:
                            LOGGER.warning("Retrying %s page %s", pdf.name, page_no)
        text, clean_warnings = clean_pages(pages); warnings.extend(clean_warnings)
        output = settings.output_dir / f"{pdf.stem}.txt"
        output.write_text(text, encoding="utf-8")
        reports.append({"chapter_name": pdf.stem, "page_count": page_count(pdf), "ocr_confidence": round(sum(confidence) / len(confidence), 4) if confidence else 0.0, "processing_time_seconds": round(elapsed(), 3), "failed_pages": failed, "warnings": warnings})
    write_report(settings.output_dir / "OCR_Report.json", reports)
