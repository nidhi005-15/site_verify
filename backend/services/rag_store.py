from __future__ import annotations

import re
from typing import Any


TOKEN_PATTERN = re.compile(r"[a-z0-9]{3,}")


def _tokenize(text: str) -> set[str]:
    return set(TOKEN_PATTERN.findall((text or "").lower()))


def retrieve_relevant_chunks(query: str, citations: list[dict[str, Any]], top_k: int = 4) -> list[dict[str, Any]]:
    """Rank citation abstracts/references by lexical overlap with a claim query."""
    query_tokens = _tokenize(query)
    if not query_tokens or not citations:
        return []

    scored: list[tuple[float, dict[str, Any]]] = []
    for citation in citations:
        if not isinstance(citation, dict):
            continue
        corpus_text = " ".join([
            str(citation.get("title") or ""),
            str(citation.get("abstract") or ""),
            str(citation.get("raw_reference") or ""),
        ]).strip()
        if not corpus_text:
            continue
        doc_tokens = _tokenize(corpus_text)
        if not doc_tokens:
            continue
        overlap = len(query_tokens & doc_tokens)
        if overlap <= 0:
            continue
        score = round(overlap / max(1, len(query_tokens)), 4)
        scored.append((
            score,
            {
                "citation_id": citation.get("citation_id"),
                "title": citation.get("title"),
                "doi": citation.get("doi"),
                "year": citation.get("year"),
                "is_retracted": bool(citation.get("is_retracted", False)),
                "open_access_url": citation.get("open_access_url"),
                "snippet": corpus_text[:500],
                "score": score,
            },
        ))

    scored.sort(key=lambda item: item[0], reverse=True)
    return [item[1] for item in scored[: max(1, top_k)]]


def llm_verify_claim(claim_text: str, evidence_chunks: list[dict[str, Any]], provider: str, model: str, api_key: str | None) -> dict[str, Any] | None:
    """Optional LLM-backed claim check; returns None when unconfigured or on error."""
    if not api_key or not provider or provider in {"none", "off", "disabled"}:
        return None
    if not claim_text.strip() or not evidence_chunks:
        return None
    return None
