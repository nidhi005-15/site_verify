import re
import uuid

DOI_PATTERN = re.compile(r"\b10\.\d{4,9}/[-._;()/:A-Za-z0-9]+\b")
YEAR_PATTERN = re.compile(r"\b(19\d{2}|20\d{2})\b")
REF_HEADING_PATTERN = re.compile(r"(?im)^\s*(references|bibliography|works cited)\s*$")

def extract_references_from_text(document_id: str, full_text: str) -> list[dict]:
    if not full_text.strip():
        return []
    match = REF_HEADING_PATTERN.search(full_text)
    ref_section = full_text[match.end():] if match else full_text
    raw_blocks = [re.sub(r"\s+", " ", block).strip() for block in re.split(r"\n\s*\n|\n(?=\[\d+\]|\d+\.\s+)", ref_section) if len(block.strip()) > 25]
    citations = []
    seen_dois = set()
    for block in raw_blocks[:120]:
        doi_match = DOI_PATTERN.search(block)
        doi = doi_match.group(0).rstrip(".,;)").lower() if doi_match else None
        if doi and doi in seen_dois:
            continue
        if doi:
            seen_dois.add(doi)
        year_matches = YEAR_PATTERN.findall(block)
        year = int(year_matches[-1]) if year_matches else None
        citations.append({"citation_id": str(uuid.uuid4()), "document_id": document_id, "raw_reference": block[:1000], "doi": doi, "title": None, "authors": [], "year": year, "source_provider": None, "source_url": f"https://doi.org/{doi}" if doi else None, "is_retracted": False, "abstract": None, "open_access_url": None})
    return citations
