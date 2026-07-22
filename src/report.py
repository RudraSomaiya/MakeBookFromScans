"""JSON report writing."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def write_report(path: Path, chapters: list[dict[str, Any]]) -> None:
    path.write_text(json.dumps({"chapters": chapters}, indent=2, ensure_ascii=False), encoding="utf-8")
