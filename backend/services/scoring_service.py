from __future__ import annotations

from typing import Any

WEIGHTS = {
    "supported": 1.0,
    "partially_supported": 0.5,
    "potentially_outdated": 0.5,
    "unverified": 0.0,
    "unsupported": 0.0,
    "contradictory": 0.0,
}


def compute_verification_summary(verified_claims: list[dict[str, Any]], citations: list[dict[str, Any]]) -> dict[str, Any]:
    if not verified_claims:
        return {
            "claim_verification_score": 0.0,
            "total_claims": 0,
            "status_counts": {},
            "citations_total": len(citations),
            "citations_with_doi": sum(1 for c in citations if c.get("doi")),
            "citations_enriched": sum(1 for c in citations if c.get("source_provider")),
        }

    status_counts: dict[str, int] = {}
    points = 0.0
    for item in verified_claims:
        status = str(item.get("verification_status") or "unverified").lower()
        status_counts[status] = status_counts.get(status, 0) + 1
        points += WEIGHTS.get(status, 0.0)

    score = round((points / len(verified_claims)) * 100.0, 2)
    return {
        "claim_verification_score": score,
        "total_claims": len(verified_claims),
        "status_counts": status_counts,
        "citations_total": len(citations),
        "citations_with_doi": sum(1 for c in citations if c.get("doi")),
        "citations_enriched": sum(1 for c in citations if c.get("source_provider")),
    }
