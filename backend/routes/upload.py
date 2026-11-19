from fastapi import APIRouter, File, HTTPException, UploadFile
from pydantic import BaseModel
import uuid

from services.assistant_service import answer_research_question
from services.citation_extractor import extract_references_from_text
from services.claim_extractor import extract_claims_from_text
from services.claim_verifier import verify_claims_against_citations
from services.discrepancy_analyzer import analyze_claim_discrepancies
from services.integrity_analyzer import assess_originality_and_integrity
from services.multilingual_service import build_multilingual_passage, detect_language
from services.pdf_extractor import extract_pdf_text
from services.research_retriever import enrich_citation_via_openalex
from services.scoring_service import compute_verification_summary

router = APIRouter()

DOCUMENT_STORE: dict[str, dict] = {}
LATEST_DOC_ID: str | None = None


class AssistantRequest(BaseModel):
    question: str
    document_id: str | None = None


@router.post("/upload")
async def upload_publication(file: UploadFile = File(...)):
    global LATEST_DOC_ID

    if not file.filename or not file.filename.lower().endswith(".pdf"):
        raise HTTPException(
            status_code=400,
            detail="Please upload a PDF publication.",
        )

    pdf_bytes = await file.read()
    if not pdf_bytes:
        raise HTTPException(
            status_code=400,
            detail="The uploaded file is empty.",
        )

    try:
        result = extract_pdf_text(pdf_bytes, filename=file.filename or "uploaded.pdf")
        if not result["full_text"].strip():
            raise HTTPException(
                status_code=422,
                detail="No readable text found. OCR support is needed.",
            )

        document_id = str(uuid.uuid4())
        full_text = result["full_text"]
        detected_language = detect_language(full_text)

        raw_citations = extract_references_from_text(document_id, full_text)
        enriched_citations = [enrich_citation_via_openalex(c) for c in raw_citations]
        extracted_claims = extract_claims_from_text(document_id, full_text)
        verified_claims = verify_claims_against_citations(extracted_claims, enriched_citations)

        for item in verified_claims:
            matched = item.get("matched_citations") or []
            ev_text = " ".join(str(m.get("snippet") or "") for m in matched)
            first_year = next((m.get("year") for m in matched if m.get("year")), None)
            discrepancies = analyze_claim_discrepancies(
                str(item.get("claim_text") or ""),
                ev_text,
                citation_year=first_year,
            )
            item["discrepancies"] = discrepancies
            if discrepancies["contradiction_signal"] and item.get("verification_status") == "unverified":
                item["verification_status"] = "contradictory"
            elif discrepancies["potentially_outdated"] and item.get("verification_status") == "supported":
                item["verification_status"] = "potentially_outdated"

            claim_str = str(item.get("claim_text") or "")
            item["multilingual"] = build_multilingual_passage(
                claim_str,
                target_language="en",
                source_language=detected_language,
            )

        scores = compute_verification_summary(verified_claims, enriched_citations)
        integrity = assess_originality_and_integrity(full_text, enriched_citations, verified_claims)
        report = {
            "document_id": document_id,
            "filename": file.filename,
            "language": detected_language,
            "total_pages": result["total_pages"],
            "scores": scores,
            "integrity": integrity,
            "claims_count": len(verified_claims),
            "citations_count": len(enriched_citations),
            "claims": verified_claims,
            "citations": enriched_citations,
        }

        DOCUMENT_STORE[document_id] = {
            "document_id": document_id,
            "filename": file.filename,
            "language": detected_language,
            "citations": enriched_citations,
            "claims": extracted_claims,
            "verified_claims": verified_claims,
            "scores": scores,
            "integrity": integrity,
            "report": report,
        }
        LATEST_DOC_ID = document_id

        return {
            "document_id": document_id,
            "filename": file.filename,
            "status": "success",
            "language": detected_language,
            "total_pages": result["total_pages"],
            "extracted_text": full_text,
            "pages": result["pages"],
            "citations_count": len(enriched_citations),
            "citations": enriched_citations,
            "claims_count": len(verified_claims),
            "claims": verified_claims,
            "scores": scores,
            "integrity": integrity,
            "report": report,
        }

    except HTTPException:
        raise
    except ValueError as error:
        raise HTTPException(status_code=422, detail=str(error))
    except Exception as error:
        raise HTTPException(
            status_code=500,
            detail=f"Processing error: {str(error)}",
        )


@router.post("/assistant")
def ask_research_assistant(payload: AssistantRequest):
    doc_id = payload.document_id or LATEST_DOC_ID
    if not doc_id or doc_id not in DOCUMENT_STORE:
        raise HTTPException(status_code=404, detail="No analyzed document available.")
    return answer_research_question(payload.question, DOCUMENT_STORE[doc_id])


@router.get("/report/{document_id}")
def get_assessment_report(document_id: str):
    doc = DOCUMENT_STORE.get(document_id)
    if not doc:
        raise HTTPException(status_code=404, detail="Document report not found.")
    return doc["report"]
