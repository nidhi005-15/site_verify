from __future__ import annotations

import re
from typing import Any


def detect_language(text: str) -> str:
    sample = text or ""
    if re.search(r"[\u3040-\u30ff]", sample):
        return "ja"
    if re.search(r"[\u4e00-\u9fff]", sample):
        return "zh"
    if re.search(r"[\u0900-\u097f]", sample):
        return "hi"
    if re.search(r"[\u0c80-\u0cff]", sample):
        return "kn"
    if re.search(r"[\u0c00-\u0c7f]", sample):
        return "te"
    if re.search(r"[\u0b80-\u0bff]", sample):
        return "ta"
    if re.search(r"[\u0400-\u04ff]", sample):
        return "ru"
    if re.search(r"[äöüßÄÖÜ]", sample):
        return "de"
    if re.search(r"[àâçéèêëîïôùûüÿœæÀÂÇÉÈÊËÎÏÔÙÛÜŸŒAE]", sample):
        return "fr"
    return "en"


def build_multilingual_passage(
    passage: str,
    target_language: str = "en",
    source_language: str | None = None,
) -> dict[str, Any]:
    src_lang = source_language or detect_language(passage)
    tgt_lang = (target_language or "en").lower()
    needs_translation = bool(passage.strip()) and src_lang != tgt_lang

    return {
        "original_text": passage,
        "source_language": src_lang,
        "target_language": tgt_lang,
        "translation_needed": needs_translation,
        "translated_text": passage if not needs_translation else f"[{tgt_lang.upper()} translation pending external translator] {passage}",
        "requires_human_review": needs_translation,
    }
