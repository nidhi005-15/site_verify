import re


STOPWORDS = {
    "the", "and", "for", "with", "that", "this", "from", "into", "were", "was",
    "are", "have", "has", "had", "been", "their", "which", "using", "used", "study",
    "results", "show", "shows", "showed", "found", "indicate", "indicates", "suggests",
}


def _tokenize(text: str) -> set[str]:
    tokens = re.findall(r"[a-z0-9]{3,}", (text or "").lower())
    return {t for t in tokens if t not in STOPWORDS}


def verify_claims_against_citations(claims: list[dict], citations: list[dict]) -> list[dict]:
    verified_claims: list[dict] = []

    for claim in claims:
        claim_text = claim.get("claim_text", "")
        claim_tokens = _tokenize(claim_text)

        best_citation = None
        best_overlap = 0
        best_shared: list[str] = []

        for citation in citations:
            ref_parts = [
                str(citation.get("title") or ""),
                str(citation.get("raw_text") or ""),
                str(citation.get("venue") or ""),
            ]
            ref_tokens = _tokenize(" ".join(ref_parts))
            shared = sorted(claim_tokens & ref_tokens)
            if len(shared) > best_overlap:
                best_overlap = len(shared)
                best_citation = citation
                best_shared = shared

        if best_overlap >= 2 and best_citation is not None:
            status = "supported"
            confidence = round(min(0.95, 0.45 + 0.12 * best_overlap), 2)
            reason = f"Matched {best_overlap} key terms ({", ".join(best_shared[:4])}) with cited work."
        elif best_overlap == 1 and best_citation is not None:
            status = "partially_supported"
            confidence = 0.5
            reason = f"Weak overlap on 1 term ({best_shared[0]}) with cited work."
        else:
            status = "unverified"
            confidence = 0.2
            reason = "No sufficient term overlap found with extracted citations."

        verified_claims.append({
            **claim,
            "verification_status": status,
            "confidence": confidence,
            "matched_citation_title": best_citation.get("title") if isinstance(best_citation, dict) else None,
            "verification_reason": reason,
        })

    return verified_claims
