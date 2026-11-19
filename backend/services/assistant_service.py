from __future__ import annotations

from typing import Any


def answer_research_question(question: str, context: dict[str, Any]) -> dict[str, Any]:
    q = (question or "").strip()
    if not q:
        return {
            "answer": "Please provide a question about the analyzed publication, claims, citations, or scores.",
            "grounded_items": [],
        }

    q_lower = q.lower()
    claims = context.get("claims") or []
    verified_claims = context.get("verified_claims") or []
    citations = context.get("citations") or []
    scores = context.get("scores") or {}
    integrity = context.get("integrity") or {}

    if "score" in q_lower or "originality" in q_lower:
        return {
            "answer": (
                f"Claim Verification Score: {scores.get('claim_verification_score', 'N/A')} | "
                f"Originality Score: {integrity.get('originality_score', 'N/A')}. "
                f"{integrity.get('limitation_note', '')}"
            ).strip(),
            "grounded_items": [scores, integrity],
        }

    if "contradict" in q_lower or "unverified" in q_lower or "unsupported" in q_lower or "discrepanc" in q_lower:
        flagged = [
            v for v in verified_claims
            if v.get("verification_status") not in {"supported"} or v.get("discrepancies", {}).get("flags")
        ]
        summary_lines = [
            f"- [{v.get('verification_status')}] {v.get('claim_text', '')[:140]}"
            for v in flagged[:5]
        ]
        return {
            "answer": (
                f"Found {len(flagged)} claim(s) with non-supported status or discrepancy flags:\n"
                + ("\n".join(summary_lines) if summary_lines else "No flagged claims found.")
            ),
            "grounded_items": flagged[:5],
        }

    if "citation" in q_lower or "reference" in q_lower or "doi" in q_lower:
        refs = [
            f"- {c.get('title') or c.get('raw_reference', '')[:120]} (DOI: {c.get('doi') or 'none'})"
            for c in citations[:5]
        ]
        return {
            "answer": (
                f"Extracted {len(citations)} reference(s):\n"
                + ("\n".join(refs) if refs else "No citations extracted.")
            ),
            "grounded_items": citations[:5],
        }

    sample_claims = [c.get("claim_text", "")[:140] for c in claims[:3]]
    return {
        "answer": (
            f"Document has {len(claims)} extracted claim(s) and {len(citations)} reference(s). "
            f"Sample claims: {'; '.join(sample_claims) if sample_claims else 'None'}."
        ),
        "grounded_items": verified_claims[:3],
    }
