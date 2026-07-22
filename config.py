"""Configuration for the local OCR pipeline.

Values can be overridden with environment variables prefixed with OCR_;
for example OCR_RENDER_DPI=250 or OCR_USE_GPU=true.
"""
from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path


def _bool(name: str, default: bool) -> bool:
    return os.getenv(name, str(default)).lower() in {"1", "true", "yes", "on"}


@dataclass(frozen=True)
class Settings:
    book_dir: Path = Path("Book")
    output_dir: Path = Path("Output")
    render_dpi: int = 220
    max_image_dimension: int = 3200
    min_confidence: float = 0.30
    use_gpu: bool = False
    max_retries: int = 2
    workers: int = 1  # PaddleOCR models are large; one worker is safest by default.
    log_level: str = "INFO"
    language: str = "en"

    @classmethod
    def from_environment(cls) -> "Settings":
        return cls(
            book_dir=Path(os.getenv("OCR_BOOK_DIR", "Book")),
            output_dir=Path(os.getenv("OCR_OUTPUT_DIR", "Output")),
            render_dpi=int(os.getenv("OCR_RENDER_DPI", "220")),
            max_image_dimension=int(os.getenv("OCR_MAX_IMAGE_DIMENSION", "3200")),
            min_confidence=float(os.getenv("OCR_MIN_CONFIDENCE", "0.30")),
            use_gpu=_bool("OCR_USE_GPU", False),
            max_retries=int(os.getenv("OCR_MAX_RETRIES", "2")),
            workers=max(1, int(os.getenv("OCR_WORKERS", "1"))),
            log_level=os.getenv("OCR_LOG_LEVEL", "INFO"),
            language=os.getenv("OCR_LANGUAGE", "en"),
        )
