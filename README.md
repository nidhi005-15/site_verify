# CiteVerify

Scientific Claim and Citation Verification System built with FastAPI. CiteVerify parses uploaded PDF publications, extracts reference citations and cue-matched claims, enriches citation metadata via OpenAlex, retrieves relevant evidence snippets, and evaluates claim support.

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
- `frontend/` — Frontend workspace directory.

## Setup & Running Locally

### 1. Backend Dependencies & Test Suite

```bash
cd backend
python -m venv .venv
# Activate .venv (Windows Git Bash: source .venv/Scripts/activate | Linux/macOS: source .venv/bin/activate)
pip install -r requirements.txt pytest
python -m pytest -v
cd backend
uvicorn main:app --reload
