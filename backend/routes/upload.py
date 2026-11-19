from fastapi import APIRouter, File, HTTPException, UploadFile
from services.pdf_extractor import extract_pdf_text

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

        return {
            "filename": file.filename,
            "status": "success",
            "total_pages": result["total_pages"],
            "extracted_text": result["full_text"],
            "pages": result["pages"],
        }

    except HTTPException:
        raise
    except Exception as error:
        raise HTTPException(
            status_code=500,
            detail=f"Processing error: {str(error)}",
        )
