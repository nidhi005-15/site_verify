from __future__ import annotations

import re
from pathlib import Path
from typing import Any

from config import Settings, settings
from services.verifier import normalize_whitespace


def compute_honest_repetition_and_integrity(
    full_text: str,
    claims: list[dict[str, Any]],
    verified_references: list[dict[str, Any]],
    cfg: Settings = settings,
) -> dict[str, Any]:
    sentences = [
        normalize_whitespace(s).lower()
        for s in re.split(r"(?<=[.!?])\s+", full_text)
        if len(normalize_whitespace(s)) >= 25
    ]
    total_sents = len(sentences)
    unique_sents = len(set(sentences))
    internal_repetition_ratio = (
        round((total_sents - unique_sents) / total_sents, 3) if total_sents > 0 else 0.0
    )

    tokens = re.findall(r"[a-z0-9]+", full_text.lower())
    ngrams = [" ".join(tokens[i : i + 5]) for i in range(max(0, len(tokens) - 4))]
    ngram_dup_ratio = (
        round((len(ngrams) - len(set(ngrams))) / len(ngrams), 3) if len(ngrams) > 0 else 0.0
    )

    raw_score = 1.0 - min(1.0, internal_repetition_ratio * 0.6 + ngram_dup_ratio * 0.4)
    internal_similarity_score = round(max(0.0, min(100.0, raw_score * 100.0)), 1)

    local_corpus_matches: list[dict[str, Any]] = []
    corpus_dir: Path = cfg.sample_corpus_dir
    if corpus_dir.exists() and corpus_dir.is_dir():
        doc_token_set = set(tokens)
        for p in sorted(corpus_dir.glob("*.txt"))[:25]:
            try:
                sample_tokens = set(
                    re.findall(r"[a-z0-9]+", p.read_text(encoding="utf-8", errors="ignore").lower())
                )
                if doc_token_set and sample_tokens:
                    jaccard = len(doc_token_set & sample_tokens) / len(doc_token_set | sample_tokens)
                    if jaccard >= 0.15:
                        local_corpus_matches.append(
                            {"sample_file": p.name, "token_jaccard": round(jaccard, 3)}
                        )
            except Exception:
                continue

    total_claims = len(claims)
    verifiable_claims = sum(1 for c in claims if c.get("verification_status") != "unverifiable")
    supported_claims = sum(1 for c in claims if c.get("verification_status") == "supported")
    contradicted_claims = sum(1 for c in claims if c.get("verification_status") == "contradicted")
    insufficient_claims = sum(
        1 for c in claims if c.get("verification_status") == "insufficient_evidence"
    )
    unverifiable_claims = sum(1 for c in claims if c.get("verification_status") == "unverifiable")
    verified_refs_count = sum(1 for r in verified_references if r.get("verified_reference"))

    verifiable_share_pct = (
        round((verifiable_claims / total_claims) * 100.0, 1) if total_claims > 0 else 0.0
    )
    supported_among_verifiable_pct = (
        round((supported_claims / verifiable_claims) * 100.0, 1) if verifiable_claims > 0 else 0.0
    )

    return {
        "metric_name": "Internal Repetition and Similarity Score",
        "disclaimer": (
            "No external plagiarism corpus is connected. This score measures internal repetition "
            "within the uploaded PDF only and does not verify originality against external works."
        ),
        "internal_repetition_and_similarity_score": internal_similarity_score,
        "internal_repetition_ratio": internal_repetition_ratio,
        "repeated_5gram_ratio": ngram_dup_ratio,
        "local_sample_corpus_used": bool(corpus_dir.exists() and corpus_dir.is_dir()),
        "local_sample_matches": local_corpus_matches,
        "verifiable_claims_summary": f"{verifiable_claims} of {total_claims} claims verifiable",
        "verifiable_claims": verifiable_claims,
        "total_claims": total_claims,
        "verifiable_share_pct": verifiable_share_pct,
        "supported_among_verifiable_pct": supported_among_verifiable_pct,
        "supported_claims": supported_claims,
        "contradicted_claims": contradicted_claims,
        "insufficient_evidence_claims": insufficient_claims,
        "unverifiable_claims": unverifiable_claims,
        "verified_references_count": verified_refs_count,
        "total_references_count": len(verified_references),
    }


def _is_prompt_injection(question: str) -> bool:
    q = question.lower()
    patterns = [
        r"ignore\s+(all\s+)?(previous|prior|above)?\s*(instructions|rules|prompts)",
        r"system\s+prompt",
        r"jailbreak",
        r"say\s+(all\s+)?claims\s+are\s+(verified|supported)",
        r"pretend\s+you\s+are",
        r"act\s+as\s+",
        r"override\s+(verification|rules|policy)",
    ]
    return any(re.search(p, q) for p in patterns)


def answer_grounded_question(
    question: str,
    report: dict[str, Any] | None,
) -> dict[str, Any]:
    cleaned_q = normalize_whitespace(question or "")
    if not cleaned_q or _is_prompt_injection(cleaned_q) or not report:
        return {
            "answer": "I can't find that in this document.",
            "grounded_items": [],
            "sources_used": [],
        }

    claims: list[dict[str, Any]] = report.get("claims") or []
    citations: list[dict[str, Any]] = report.get("citations") or []

    q_terms = {w for w in re.findall(r"[a-z0-9]+", cleaned_q.lower()) if len(w) > 2}
    if not q_terms:
        return {
            "answer": "I can't find that in this document.",
            "grounded_items": [],
            "sources_used": [],
        }

    scored_claims: list[tuple[int, dict[str, Any]]] = []
    for c in claims:
        hay = f"{c.get('claim_text', '')} {c.get('explanation', '')} {c.get('evidence_quote', '')}".lower()
        hits = sum(1 for t in q_terms if t in hay)
        if hits > 0:
            scored_claims.append((hits, c))
    scored_claims.sort(key=lambda pair: (-pair[0], str(pair[1].get("claim_id", ""))))
    top_claims = [c for _hits, c in scored_claims[:4]]

    scored_refs: list[tuple[int, dict[str, Any]]] = []
    for r in citations:
        hay = f"{r.get('raw_reference', '')} {r.get('title', '')} {r.get('doi', '')}".lower()
        hits = sum(1 for t in q_terms if t in hay)
        if hits > 0:
            scored_refs.append((hits, r))
    scored_refs.sort(key=lambda pair: (-pair[0], str(pair[1].get("ref_id", ""))))
    top_refs = [r for _hits, r in scored_refs[:2]]

    if not top_claims and not top_refs:
        return {
            "answer": "I can't find that in this document.",
            "grounded_items": [],
            "sources_used": [],
        }

    grounded_items: list[dict[str, Any]] = []
    sources_used: list[str] = []
    lines: list[str] = []

    for c in top_claims:
        cid = str(c.get("claim_id", "claim"))
        status = str(c.get("verification_status", "unverifiable"))
        ctext = str(c.get("claim_text", ""))
        quote = c.get("evidence_quote")
        reason = str(c.get("explanation", ""))
        sources_used.append(cid)
        grounded_items.append(
            {
                "claim_id": cid,
                "claim_text": ctext,
                "verification_status": status,
                "evidence_quote": quote,
                "source_type": "extracted_claim",
            }
        )
        quote_part = f' Quote: "{quote}".' if quote else ""
        lines.append(f"[{cid} · {status}] {ctext} — {reason}{quote_part}")

    for r in top_refs:
        rid = str(r.get("ref_id", "reference"))
        rtext = str(r.get("title") or r.get("raw_reference") or "")
        rstatus = "verified_metadata" if r.get("verified_reference") else "unverified_reference"
        sources_used.append(rid)
        grounded_items.append(
            {
                "claim_id": rid,
                "claim_text": rtext,
                "verification_status": rstatus,
                "source_type": "reference",
            }
        )
        lines.append(f"[{rid} · {rstatus}] {rtext}")

    answer_text = (
        f"Based strictly on this document ({', '.join(sources_used)}): " + " ".join(lines)
    )
    return {
        "answer": answer_text,
        "grounded_items": grounded_items,
        "sources_used": sources_used,
    }
