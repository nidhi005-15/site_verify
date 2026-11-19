# CiteVerify

## Project description

CiteVerify is an AI-powered, multilingual research integrity platform that verifies academic papers instead of just summarizing them. It extracts claims and citations from uploaded PDFs, retrieves the cited sources, and checks each claim against the evidence using RAG and LLMs, classifying it as Supported, Partially Supported, Unsupported, Contradictory, or Potentially Outdated.

It also assesses originality separately from claim accuracy, and includes a grounded AI research assistant and exportable reports. The backend is built with Python and FastAPI, with a separate frontend.

Scientific Claim and Citation Verification System built with FastAPI. CiteVerify parses uploaded PDF publications, extracts reference citations and cue-matched claims, enriches citation metadata via OpenAlex, retrieves relevant evidence snippets, and evaluates claim support.

## Team members

- P Amrutha Varshini
- Nidhi V Aathreya
- Charanya NV

## Project Structure

- `backend/main.py` — FastAPI application entrypoint, CORS configuration, and router registration.
- `backend/config.py` — Environment and `.env` configuration loader (`Settings` and `get_settings()`).
- `backend/routes/upload.py` — `POST /upload` endpoint orchestrating PDF extraction, citation extraction/enrichment, claim extraction, and claim verification.
- `backend/services/pdf_extractor.py` — Extracts per-page and full text from PDF bytes using PyMuPDF.
- `backend/services/citation_extractor.py` — Parses reference sections, DOIs, and publication years.
- `backend/services/research_retriever.py` — Enriches citations with title, authors, year, retraction status, abstract, and open-access URLs from OpenAlex.
- `backend/services/claim_extractor.py` — Identifies claim sentences using length bounds and `CLAIM_CUES`.
- `backend/services/rag_store.py` — Ranks citation snippets by lexical overlap (`retrieve_relevant_chunks`) and provides optional LLM verification (`llm_verify_claim`).
- `backend/services/claim_verifier.py` — Scores overlap between claims and citations (`supported`, `partially_supported`, `unverified`) and optionally applies LLM verification results.
- `backend/tests/` — Automated `pytest` test suite covering the upload pipeline, evidence retrieval, and claim verification.
- `frontend/` — Landing page (`index.html`), upload page (`upload.html`) and results page (`results.html`), sharing `style.css` and `script.js`.

## Setup & Running Locally

### Backend

```bash
cd backend
python -m venv .venv
# Activate .venv (Windows Git Bash: source .venv/Scripts/activate | Linux/macOS: source .venv/bin/activate)
pip install -r requirements.txt pytest
python -m pytest -v
uvicorn main:app --reload
```