"""Heuristics for turning OCR lines into readable book prose."""
from __future__ import annotations

import re
import unicodedata
from collections import Counter


def _norm(s: str) -> str:
    s = unicodedata.normalize("NFKC", s).replace("\u00ad", "")
    # Keep typographic quotation marks; they are useful downstream formatting.
    return s


def clean_pages(pages: list[list[str]]) -> tuple[str, list[str]]:
    """Remove likely running furniture/page numbers and join lines into paragraphs."""
    warnings: list[str] = []
    normalized = [[_norm(x).strip() for x in lines if _norm(x).strip()] for lines in pages]
    candidates = Counter(
        line for lines in normalized for line in lines
        if len(line) <= 100 and not re.search(r"[.!?]$", line)
    )
    repeated = {line for line, count in candidates.items() if count >= max(3, len(pages) // 3)}
    out: list[str] = []
    for lines in normalized:
        kept = [line for line in lines if line not in repeated and not re.fullmatch(r"[-–—]?\s*\d+\s*[-–—]?", line)]
        # A decorative drop-cap is often emitted as a separate one-letter line.
        # Join it to the following lowercase word (e.g. ``A`` + ``laric``).
        if len(kept) >= 2 and re.fullmatch(r"[A-Z]", kept[0]) and kept[1][:1].islower():
            kept[1] = kept[0] + kept[1]
            kept.pop(0)
        paragraph = ""
        for line in kept:
            if not paragraph:
                paragraph = line
            elif paragraph.endswith("-") and len(paragraph) > 1 and line[:1].islower():
                paragraph = paragraph[:-1] + line
            elif re.search(r"[.!?:;\"')\]]$", paragraph) and line[:1].isupper():
                out.append(paragraph)
                paragraph = line
            else:
                paragraph += " " + line
        if paragraph:
            out.append(paragraph)
    # A page break can split a sentence after a comma or an OCR line break.
    merged: list[str] = []
    for paragraph in out:
        if merged and re.search(r"[,;:]$", merged[-1]) and paragraph[:1].islower():
            merged[-1] += " " + paragraph
        else:
            merged.append(paragraph)
    text = "\n\n".join(merged)
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text).strip()
    if repeated:
        warnings.append(f"Removed {len(repeated)} likely repeated header/footer lines")
    return text + ("\n" if text else ""), warnings
