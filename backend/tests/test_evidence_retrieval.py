from services.rag_store import retrieve_relevant_chunks


def test_retrieve_relevant_chunks_ranks_matching_citation():
    citations = [
        {
            "citation_id": "c1",
            "title": "Deep Neural Network Accuracy Study",
            "abstract": "Evaluates neural network accuracy on vision datasets.",
            "doi": "10.1000/test1",
            "year": 2024,
            "is_retracted": False,
            "open_access_url": None,
        },
        {
            "citation_id": "c2",
            "title": "Soil Chemistry Survey",
            "abstract": "Measures nitrogen levels in agricultural fields.",
            "doi": None,
            "year": 2022,
            "is_retracted": False,
            "open_access_url": None,
        },
    ]
    results = retrieve_relevant_chunks("neural network accuracy", citations, top_k=2)
    assert len(results) == 1
    assert results[0]["citation_id"] == "c1"
    assert results[0]["score"] > 0


def test_attach_evidence_adds_snippets_and_score():
    from services.claim_verifier import _attach_evidence

    claim = {"claim": "Neural network accuracy improves on vision tasks."}
    citations = [
        {
            "citation_id": "c1",
            "title": "Vision Neural Network Accuracy",
            "abstract": "Evaluates neural network accuracy across vision benchmarks.",
            "doi": "10.1000/vis1",
            "year": 2025,
            "is_retracted": False,
            "open_access_url": None,
        }
    ]
    result = _attach_evidence(claim, citations)
    assert result["claim"] == claim["claim"]
    assert result["retrieval_score"] > 0
    assert len(result["evidence_snippets"]) == 1
