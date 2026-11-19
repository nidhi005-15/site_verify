from __future__ import annotations

import io
import re
from dataclasses import dataclass
from typing import Any

from config import Settings, settings
from services.verifier import normalize_whitespace


@dataclass
class ExtractedPage:
    page_number: int
    text: str
    garbled_ratio: float


@dataclass
class ExtractedDocument:
    filename: str
    total_pages: int
    processed_pages: int
    language: str
    full_text: str
    pages: list[ExtractedPage]
    claims: list[dict[str, Any]]
    references: list[dict[str, Any]]
    warnings: list[str]
    is_scanned_likely: bool


def _garbled_score(text: str) -> float:
    if not text:
        return 1.0
    non_print = sum(1 for ch in text if ord(ch) < 32 and ch not in "\n\r\t")
    replacement = text.count("\ufffd")
    weird_symbols = len(re.findall(r"[^\w\s.,;:!?()\-–—'\"/%$@#&*+=/\\\[\]]", text))
    total = max(1, len(text))
    return min(1.0, (non_print * 5 + replacement * 4 + weird_symbols * 0.5) / total)


def _extract_raw_pages(pdf_bytes: bytes, max_pages: int) -> tuple[list[str], list[str]]:
    warnings: list[str] = []
    raw_pages: list[str] = []
    last_exc: Exception | None = None

    try:
        import pymupdf  # type: ignore

        doc = pymupdf.open(stream=pdf_bytes, filetype="pdf")
        try:
            if getattr(doc, "is_encrypted", False):
                raise ValueError("Encrypted or password-protected PDFs are not supported.")
            total = len(doc)
            if total == 0:
                raise ValueError("PDF contains no pages.")
            if total > max_pages:
                warnings.append(
                    f"Document has {total} pages; only the first {max_pages} pages were processed."
                )
            for idx in range(min(total, max_pages)):
                raw_pages.append(doc[idx].get_text("text") or "")
            return raw_pages, warnings
        finally:
            doc.close()
    except ValueError:
        raise
    except Exception as exc:
        last_exc = exc

    try:
        import pypdf  # type: ignore

        reader = pypdf.PdfReader(io.BytesIO(pdf_bytes))
        if getattr(reader, "is_encrypted", False):
            try:
                reader.decrypt("")
            except Exception:
                raise ValueError("Encrypted or password-protected PDFs are not supported.")
        total = len(reader.pages)
        if total == 0:
            raise ValueError("PDF contains no pages.")
        if total > max_pages:
            warnings.append(
                f"Document has {total} pages; only the first {max_pages} pages were processed."
            )
        for page in reader.pages[:max_pages]:
            try:
                txt = page.extract_text(extraction_mode="layout") or page.extract_text() or ""
            except TypeError:
                txt = page.extract_text() or ""
            raw_pages.append(txt)
        return raw_pages, warnings
    except ValueError:
        raise
    except Exception as exc:
        last_exc = exc

    err_name = type(last_exc).__name__ if last_exc else "ParseError"
    raise ValueError(f"Could not parse PDF file: {err_name}")


def _clean_page_text(raw: str) -> str:
    dehyphenated = re.sub(r"([A-Za-z]{2,})-\s*\n\s*([a-z]{2,})", r"\1\2", raw)
    lines = []
    for line in dehyphenated.splitlines():
        compact = re.sub(r"[ \t]{2,}", " ", line).strip()
        if compact:
            lines.append(compact)
    return "\n".join(lines)


def _detect_language(text: str) -> str:
    sample = text[:2000].lower()
    if not sample.strip():
        return "unknown"
    english_markers = len(
        re.findall(r"\b(the|and|of|to|in|for|with|that|is|are|this|from|by|on)\b", sample)
    )
    return "en" if english_markers >= 4 else "other"


def _split_sections_and_sentences(text: str) -> list[tuple[str, str]]:
    section = "Body"
    pairs: list[tuple[str, str]] = []
    heading_re = re.compile(
        r"^(abstract|introduction|background|related work|methods?|methodology|experiments?|results?|discussion|conclusion|references?|bibliography)\b.*$",
        re.IGNORECASE,
    )
    for line in text.splitlines():
        clean_line = normalize_whitespace(line)
        if not clean_line:
            continue
        if len(clean_line) <= 70 and heading_re.match(clean_line):
            section = clean_line[:60]
            continue
        sentences = re.split(r"(?<=[.!?])\s+(?=[A-Z0-9\"(])", clean_line)
        for sent in sentences:
            s = normalize_whitespace(sent)
            if len(s) >= 25:
                pairs.append((section, s))
    return pairs


def _extract_references(text: str) -> list[dict[str, Any]]:
    refs: list[dict[str, Any]] = []
    seen: set[str] = set()

    ref_split = re.split(r"\n(?:references|bibliography)\s*\n", text, maxsplit=1, flags=re.IGNORECASE)
    ref_block = ref_split[1] if len(ref_split) > 1 else ""

    lines = [normalize_whitespace(ln) for ln in ref_block.splitlines() if normalize_whitespace(ln)]
    merged: list[str] = []
    for ln in lines:
        if re.match(r"^(\[\d+\]|\d+\.|[A-Z][a-z]+,\s+[A-Z])", ln) or not merged:
            merged.append(ln)
        else:
            merged[-1] = f"{merged[-1]} {ln}"

    for idx, entry in enumerate(merged, start=1):
        if len(entry) < 12:
            continue
        key = entry.lower()
        if key in seen:
            continue
        seen.add(key)

        year_match = re.search(r"\b(19|20)\d{2}\b", entry)
        year = int(year_match.group(0)) if year_match else None
        doi_match = re.search(r"\b10\.\d{4,9}/[-._;()/:A-Za-z0-9]+\b", entry)
        doi = doi_match.group(0).rstrip(".,)") if doi_match else None
        quoted = re.search(r"[\"“]([^\"”]{8,180})[\"”]", entry)
        title = quoted.group(1).strip() if quoted else None

        refs.append(
            {
                "ref_id": f"ref-{idx}",
                "raw_reference": entry,
                "title": title,
                "year": year,
                "doi": doi,
                "authors": [],
            }
        )
    return refs


def extract_pdf_document(
    filename: str,
    pdf_bytes: bytes,
    cfg: Settings = settings,
) -> ExtractedDocument:
    if not pdf_bytes:
        raise ValueError("Uploaded file is empty (0 bytes).")
    if len(pdf_bytes) > cfg.max_upload_bytes:
        max_mb = round(cfg.max_upload_bytes / (1024 * 1024), 1)
        raise ValueError(f"File exceeds the maximum allowed size of {max_mb} MB.")
    if not filename.lower().endswith(".pdf") and not pdf_bytes.startswith(b"%PDF-"):
        raise ValueError("Only PDF (.pdf) files are supported.")

    raw_pages, warnings = _extract_raw_pages(pdf_bytes, cfg.max_pdf_pages)
    if not raw_pages:
        raise ValueError("No pages could be read from this PDF.")

    pages: list[ExtractedPage] = []
    usable_chunks: list[str] = []
    garbled_pages = 0
    empty_pages = 0

    for idx, raw in enumerate(raw_pages, start=1):
        cleaned = _clean_page_text(raw)
        g_score = _garbled_score(cleaned)
        if len(cleaned) < 20:
            empty_pages += 1
            pages.append(ExtractedPage(page_number=idx, text="", garbled_ratio=g_score))
            continue
        if g_score >= 0.25:
            garbled_pages += 1
            warnings.append(f"Page {idx} contained garbled characters and was skipped.")
            pages.append(ExtractedPage(page_number=idx, text="", garbled_ratio=g_score))
            continue
        pages.append(ExtractedPage(page_number=idx, text=cleaned, garbled_ratio=g_score))
        usable_chunks.append(f"[Page {idx}]\n{cleaned}")

    is_scanned_likely = (empty_pages + garbled_pages) == len(raw_pages) and len(usable_chunks) == 0
    if is_scanned_likely:
        raise ValueError(
            "This PDF appears to be scanned or image-only with no extractable text layer. "
            "Please upload a text-based PDF or run OCR first."
        )

    full_text = "\n\n".join(usable_chunks)
    if len(normalize_whitespace(full_text)) < 30:
        raise ValueError("Document contains too little readable text to analyze.")

    language = _detect_language(full_text)
    references = _extract_references(full_text)
    if not references:
        warnings.append("No reference or bibliography section was detected in this document.")

    claims: list[dict[str, Any]] = []
    claim_idx = 0
    for p in pages:
        if not p.text:
            continue
        for section, sent in _split_sections_and_sentences(p.text):
            if re.match(r"^(references?|bibliography)\b", section, re.IGNORECASE):
                continue
            if re.match(r"^(\[\d+\]|\d+\.)\s+[A-Z][a-z]+,", sent) and re.search(r"\b(19|20)\d{2}\b", sent):
                continue
            claim_idx += 1
            claims.append(
                {
                    "claim_id": f"claim-{claim_idx}",
                    "claim_text": sent,
                    "page": p.page_number,
                    "section": section,
                }
            )

    if len(full_text) < 250 or len(claims) < 2:
        warnings.append("Document is very short; extracted claims and references may be limited.")

    return ExtractedDocument(
        filename=filename,
        total_pages=len(raw_pages),
        processed_pages=len(usable_chunks),
        language=language,
        full_text=full_text,
        pages=pages,
        claims=claims,
        references=references,
        warnings=warnings,
        is_scanned_likely=False,
    )


def _serialize_pages(doc: ExtractedDocument) -> list[dict[str, Any]]:
    return [
        {
            "page_number": p.page_number,
            "text": p.text,
            "garbled_ratio": p.garbled_ratio,
        }
        for p in doc.pages
    ]


def extract_pdf_text(
    pdf_bytes: bytes,
    filename: str = "uploaded.pdf",
    cfg: Settings = settings,
) -> dict[str, Any]:
    """Extract PDF content and return a dictionary compatible with upload routes."""
    doc = extract_pdf_document(filename=filename, pdf_bytes=pdf_bytes, cfg=cfg)
    return {
        "filename": doc.filename,
        "full_text": doc.full_text,
        "total_pages": doc.total_pages,
        "processed_pages": doc.processed_pages,
        "language": doc.language,
        "pages": _serialize_pages(doc),
        "claims": doc.claims,
        "references": doc.references,
        "warnings": doc.warnings,
    }
