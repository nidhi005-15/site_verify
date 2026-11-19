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


def test_upload_enrichment_assistant_and_report_endpoints():
    doc = fitz.open()
    page = doc.new_page()
    page.insert_text(
        (72, 72),
        "Our model reduces infection rates by 40% in adults.\n"
        "However, the method does not apply to all groups.\n"
        "References\n[1] Smith et al. (2010) Infection study in adults.",
    )
    pdf_bytes = doc.tobytes()
    doc.close()

    upload_resp = client.post("/upload", files={"file": ("study.pdf", pdf_bytes, "application/pdf")})
    assert upload_resp.status_code == 200
    payload = upload_resp.json()

    assert "document_id" in payload
    assert payload["language"] == "en"
    assert "claim_verification_score" in payload["scores"]
    assert "originality_score" in payload["integrity"]
    assert "integrity_indicators" in payload["integrity"]

    if payload["claims"]:
        assert "discrepancies" in payload["claims"][0]
        assert "multilingual" in payload["claims"][0]

    doc_id = payload["document_id"]
    report_resp = client.get(f"/report/{doc_id}")
    assert report_resp.status_code == 200
    assert report_resp.json()["document_id"] == doc_id

    missing_report = client.get("/report/nonexistent-id-check")
    assert missing_report.status_code == 404

    assistant_resp = client.post(
        "/assistant",
        json={"question": "What are the scores and any discrepancies?", "document_id": doc_id},
    )
    assert assistant_resp.status_code == 200
    assert "answer" in assistant_resp.json()
