"""PDF page rendering using PyMuPDF."""
from __future__ import annotations

from pathlib import Path
from typing import Iterator

import fitz


def page_images(pdf_path: Path, dpi: int, max_dimension: int = 3200) -> Iterator[tuple[int, object]]:
    """Yield (one-based page number, PIL image) without retaining all pages."""
    from PIL import Image
    with fitz.open(pdf_path) as document:
        scale = dpi / 72
        matrix = fitz.Matrix(scale, scale)
        for index, page in enumerate(document):
            pixmap = page.get_pixmap(matrix=matrix, alpha=False)
            image = Image.frombytes("RGB", [pixmap.width, pixmap.height], pixmap.samples)
            # Very high-DPI scans can consume hundreds of MB during PaddleOCR
            # preprocessing. Downscale oversized pages while preserving aspect ratio.
            largest = max(image.size)
            if largest > max_dimension:
                scale = max_dimension / largest
                image = image.resize(
                    (max(1, round(image.width * scale)), max(1, round(image.height * scale))),
                    Image.Resampling.LANCZOS,
                )
            yield index + 1, image


def page_count(pdf_path: Path) -> int:
    with fitz.open(pdf_path) as document:
        return len(document)
