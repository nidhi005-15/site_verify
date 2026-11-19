import httpx

def _reconstruct_abstract(inverted_index):
    if not inverted_index:
        return None
    positions = {}
    for word, indices in inverted_index.items():
        for idx in indices:
            positions[idx] = word
    if not positions:
        return None
    return " ".join(positions[i] for i in sorted(positions))

def enrich_citation_via_openalex(citation, timeout=8.0):
    doi = citation.get("doi")
    if not doi:
        return citation
    url = f"https://api.openalex.org/works/https://doi.org/{doi}"
    try:
        with httpx.Client(timeout=timeout) as client:
            resp = client.get(url, params={"mailto": "citeverify@example.org"})
            if resp.status_code != 200:
                return citation
            data = resp.json()
    except Exception:
        return citation
    authors = [a.get("author", {}).get("display_name") for a in data.get("authorships", []) if a.get("author", {}).get("display_name")]
    oa = data.get("open_access") or {}
    citation["title"] = data.get("title") or citation.get("title")
    citation["authors"] = authors or citation.get("authors", [])
    citation["year"] = data.get("publication_year") or citation.get("year")
    citation["source_provider"] = "OpenAlex"
    citation["source_url"] = data.get("doi") or citation.get("source_url")
    citation["is_retracted"] = bool(data.get("is_retracted", False))
    citation["abstract"] = _reconstruct_abstract(data.get("abstract_inverted_index"))
    citation["open_access_url"] = oa.get("oa_url")
    return citation
