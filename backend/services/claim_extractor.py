import re
import uuid


CLAIM_CUES = (
    "demonstrate",
    "demonstrates",
    "demonstrated",
    "show",
    "shows",
    "showed",
    "indicate",
    "indicates",
    "indicated",
    "suggest",
    "suggests",
    "suggested",
    "find",
    "finds",
    "found",
    "confirm",
    "confirms",
    "confirmed",
    "prove",
    "proves",
    "proved",
    "increase",
    "increases",
    "increased",
    "decrease",
    "decreases",
    "decreased",
    "correlate",
    "correlates",
    "correlated",
    "associated with",
)


def extract_claims_from_text(document_id: str, full_text: str, max_claims: int = 25) -> list[dict]:
    cleaned_text = re.sub(r"\s+", " ", full_text or "").strip()
    if not cleaned_text:
        return []

    sentences = re.split(r"(?<=[.!?])\s+", cleaned_text)
    claims: list[dict] = []

    for idx, sentence in enumerate(sentences):
        s = sentence.strip()
        if len(s) < 35 or len(s) > 400:
            continue
        lowered = s.lower()
        if any(cue in lowered for cue in CLAIM_CUES):
            claims.append({
                "claim_id": f"{document_id}-c{len(claims) + 1}-{str(uuid.uuid4())[:6]}",
                "document_id": document_id,
                "sentence_index": idx,
                "claim_text": s,
            })
        if len(claims) >= max_claims:
            break

    return claims
