"""Command-line entry point for converting scanned book chapters to text."""
from __future__ import annotations

import logging
from pathlib import Path

from config import Settings
from src.ocr import process_book


def main() -> int:
    settings = Settings.from_environment()
    settings.output_dir.mkdir(parents=True, exist_ok=True)
    logging.basicConfig(
        level=getattr(logging, settings.log_level.upper(), logging.INFO),
        format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    )
    logger = logging.getLogger(__name__)
    try:
        process_book(settings)
    except Exception:
        logger.exception("OCR processing failed")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
