import fitz
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)


def test_upload_rejects_non_pdf():
    resp = client.post("/upload", files={"file": ("notes.txt", b"hello", "text/plain")})
    assert resp.status_code == 400


def test_upload_extracts_citations_claims_and_verification():
    doc = fitz.open()
    page = doc.new_page()
    page.insert_text(
        (72, 72),
        "Our tests show that higher temperature increases thermometry accuracy in living cells.\nReferences\n[1] Kucsko et al. (2013) Nanometre-scale thermometry in a living cell https://doi.org/10.1038/nature12373.",
    )
    pdf_bytes = doc.tobytes()
    doc.close()

    resp = client.post("/upload", files={"file": ("paper.pdf", pdf_bytes, "application/pdf")})
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "success"
    assert data["citations_count"] >= 1
    assert data["claims_count"] >= 1
    first_claim = data["claims"][0]
    assert "verification_status" in first_claim
    assert "confidence" in first_claim


def test_upload_rejects_empty_file():
    resp = client.post("/upload", files={"file": ("empty.pdf", b"", "application/pdf")})
    assert resp.status_code == 400


def test_upload_rejects_blank_pdf():
    doc = fitz.open()
    doc.new_page()
    pdf_bytes = doc.tobytes()
    doc.close()

    resp = client.post("/upload", files={"file": ("blank.pdf", pdf_bytes, "application/pdf")})
    assert resp.status_code == 422


def test_claim_verifier_statuses():
    from services.claim_verifier import verify_claims_against_citations

    claims = [
        {"claim_id": "c1", "claim_text": "Our experiments show thermal accuracy improves inside living cells."},
        {"claim_id": "c2", "claim_text": "Our experiments show quantum coherence persists in cells."},
        {"claim_id": "c3", "claim_text": "Our experiments show unrelated optical scattering behavior."},
    ]
    citations = [
        {"title": "Thermal accuracy in living cells", "raw_reference": "Nanometre thermometry in living cells"},
    ]
    results = verify_claims_against_citations(claims, citations)
    assert len(results) == 3
    assert results[0]["verification_status"] == "supported"
    assert results[1]["verification_status"] == "partially_supported"
    assert results[2]["verification_status"] == "unverified"
