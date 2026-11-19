from __future__ import annotations

import re
from typing import Any

WORD_RE = re.compile(r"[a-z0-9]{3,}")


def _sentences(text: str) -> list[str]:
    parts = re.split(r"(?<=[.!?])\s+|\n+", text or "")
    return [p.strip() for p in parts if len(p.strip().split()) >= 5]


def _token_set(text: str) -> set[str]:
    return set(WORD_RE.findall((text or "").lower()))


def assess_originality_and_integrity(
    full_text: str,
    citations: list[dict[str, Any]],
    verified_claims: list[dict[str, Any]],
) -> dict[str, Any]:
    sents = _sentences(full_text)
    seen_normalized: dict[str, str] = {}
    exact_duplicates: list[str] = []
    high_overlap_pairs: list[dict[str, Any]] = []

    token_sets = [(s, _token_set(s)) for s in sents[:200]]
    for idx, (s, ts) in enumerate(token_sets):
        norm = re.sub(r"\s+", " ", s.lower()).strip()
        if norm in seen_normalized:
            exact_duplicates.append(s[:220])
        else:
            seen_normalized[norm] = s

        if not ts:
            continue
        for jdx in range(idx + 1, min(idx + 25, len(token_sets))):
            other_s, other_ts = token_sets[jdx]
            if not other_ts:
                continue
            union = ts | other_ts
            if not union:
                continue
            jaccard = len(ts & other_ts) / len(union)
            if jaccard >= 0.72 and norm != re.sub(r"\s+", " ", other_s.lower()).strip():
                high_overlap_pairs.append({
                    "similarity": round(jaccard, 3),
                    "passage_a": s[:180],
                    "passage_b": other_s[:180],
                })

    total_sents = max(1, len(token_sets))
    dup_ratio = (len(exact_duplicates) + 0.5 * len(high_overlap_pairs)) / total_sents
    originality_score = round(max(0.0, min(100.0, (1.0 - min(1.0, dup_ratio * 2.5)) * 100.0)), 2)

    retracted_count = sum(1 for c in citations if c.get("is_retracted"))
    missing_doi_count = sum(1 for c in citations if not c.get("doi"))
    unsupported_count = sum(
        1 for v in verified_claims
        if v.get("verification_status") in {"unverified", "unsupported", "contradictory"}
    )

    indicators: list[str] = []
    if retracted_count > 0:
        indicators.append(f"{retracted_count} cited source(s) flagged as retracted.")
    if citations and missing_doi_count == len(citations):
        indicators.append("None of the extracted references include a DOI; manual verification recommended.")
    if unsupported_count > 0:
        indicators.append(f"{unsupported_count} claim(s) lack strong direct citation support.")
    if exact_duplicates or high_overlap_pairs:
        indicators.append("Internal repeated or near-duplicate phrasing detected within the document.")

    return {
        "originality_score": originality_score,
        "exact_duplicate_count": len(exact_duplicates),
        "high_overlap_count": len(high_overlap_pairs),
        "high_overlap_examples": high_overlap_pairs[:5],
        "retracted_citations_count": retracted_count,
        "integrity_indicators": indicators,
        "limitation_note": (
            "Originality and integrity metrics are heuristic indicators based on internal text overlap, "
            "citation metadata, and claim support—not an exhaustive external corpus search or proof of AI authorship."
        ),
    }
