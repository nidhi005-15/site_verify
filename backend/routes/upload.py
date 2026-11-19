from fastapi import APIRouter, File, HTTPException, UploadFile
import uuid

from services.citation_extractor import extract_references_from_text
from services.claim_extractor import extract_claims_from_text
from services.claim_verifier import verify_claims_against_citations
from services.pdf_extractor import extract_pdf_text
from services.research_retriever import enrich_citation_via_openalex

router = APIRouter()


@router.post("/upload")
async def upload_publication(file: UploadFile = File(...)):
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
        result = extract_pdf_text(pdf_bytes)
        if not result["full_text"].strip():
            raise HTTPException(
                status_code=422,
                detail="No readable text found. OCR support is needed.",
            )

        document_id = str(uuid.uuid4())
        raw_citations = extract_references_from_text(document_id, result["full_text"])
        enriched_citations = [enrich_citation_via_openalex(c) for c in raw_citations]
        extracted_claims = extract_claims_from_text(document_id, result["full_text"])
        verified_claims = verify_claims_against_citations(extracted_claims, enriched_claims := enriched_citations)

        return {
            "filename": file.filename,
            "status": "success",
            "total_pages": result["total_pages"],
            "extracted_text": result["full_text"],
            "pages": result["pages"],
            "citations_count": len(enriched_citations),
            "citations": enriched_citations,
            "claims_count": len(verified_claims),
            "claims": verified_claims,
        }

    except HTTPException:
        raise
    except Exception as error:
        raise HTTPException(
            status_code=500,
            detail=f"Processing error: {str(error)}",
        )
