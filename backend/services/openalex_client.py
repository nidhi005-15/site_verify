from __future__ import annotations

import hashlib
import json
import re
import threading
import time
import urllib.error
import urllib.parse
import urllib.request
from difflib import SequenceMatcher
from pathlib import Path
from typing import Any

from config import Settings, settings
from services.verifier import normalize_whitespace


def _normalize_title(t: str) -> str:
    return re.sub(r"[^a-z0-9 ]+", " ", normalize_whitespace(t).lower()).strip()


def _title_similarity(a: str | None, b: str | None) -> float:
    na = _normalize_title(a or "")
    nb = _normalize_title(b or "")
    if not na or not nb:
        return 0.0
    return SequenceMatcher(None, na, nb).ratio()


def _author_last_names(authors: list[str] | None) -> set[str]:
    names: set[str] = set()
    for a in authors or []:
        parts = re.findall(r"[a-z]+", (a or "").lower())
        if parts:
            names.add(parts[-1] if len(parts[-1]) > 1 else parts[0])
    return names


def _author_overlap(expected: list[str] | None, candidate: list[str] | None) -> float:
    exp = _author_last_names(expected)
    cand = _author_last_names(candidate)
    if not exp or not cand:
        return 0.0
    return len(exp & cand) / max(1, min(len(exp), len(cand)))


def _reconstruct_abstract(inv_index: dict[str, list[int]] | None) -> str:
    if not isinstance(inv_index, dict) or not inv_index:
        return ""
    positions: dict[int, str] = {}
    for word, idxs in inv_index.items():
        if isinstance(idxs, list):
            for pos in idxs:
                if isinstance(pos, int):
                    positions[pos] = word
    if not positions:
        return ""
    ordered = [positions[k] for k in sorted(positions.keys())]
    return normalize_whitespace(" ".join(ordered))


class OpenAlexVerifier:
    def __init__(self, cfg: Settings = settings) -> None:
        self.cfg = cfg
        self.cache_path: Path = cfg.openalex_cache_path
        self.cache_path.parent.mkdir(parents=True, exist_ok=True)
        self._lock = threading.Lock()
        self._cache: dict[str, Any] = self._load_cache()

    def _load_cache(self) -> dict[str, Any]:
        if not self.cache_path.exists():
            return {}
        try:
            data = json.loads(self.cache_path.read_text(encoding="utf-8"))
            return data if isinstance(data, dict) else {}
        except Exception:
            return {}

    def _save_cache(self) -> None:
        with self._lock:
            self.cache_path.write_text(
                json.dumps(self._cache, indent=2, sort_keys=True), encoding="utf-8"
            )

    def _cache_key(self, ref: dict[str, Any]) -> str:
        raw = json.dumps(
            {
                "doi": (ref.get("doi") or "").lower().strip(),
                "title": _normalize_title(ref.get("title") or ""),
                "raw": normalize_whitespace(ref.get("raw_reference") or "").lower(),
                "year": ref.get("year"),
            },
            sort_keys=True,
        )
        return hashlib.sha256(raw.encode("utf-8")).hexdigest()

    def _query_openalex(self, ref: dict[str, Any]) -> tuple[dict[str, Any] | None, str | None]:
        doi = (ref.get("doi") or "").strip()
        title = (ref.get("title") or "").strip()
        raw_ref = normalize_whitespace(ref.get("raw_reference") or "")

        if doi:
            url = f"https://api.openalex.org/works/https://doi.org/{urllib.parse.quote(doi)}"
        else:
            query = title or raw_ref[:140]
            if not query:
                return None, "No title, DOI, or reference text available for lookup."
            url = f"https://api.openalex.org/works?search={urllib.parse.quote(query)}&per-page=3"

        last_err: Exception | None = None
        for attempt in range(self.cfg.openalex_max_retries + 1):
            try:
                req = urllib.request.Request(
                    url,
                    headers={"User-Agent": "CiteVerify/1.0 (mailto:research-eval@example.org)"},
                    method="GET",
                )
                with urllib.request.urlopen(req, timeout=self.cfg.openalex_timeout_sec) as resp:
                    payload = json.loads(resp.read().decode("utf-8"))
                if isinstance(payload, dict) and "results" in payload:
                    results = payload.get("results") or []
                    return (results[0] if results else None), None
                return (payload if isinstance(payload, dict) else None), None
            except (urllib.error.URLError, TimeoutError, json.JSONDecodeError, ValueError) as exc:
                last_err = exc
                if attempt < self.cfg.openalex_max_retries:
                    time.sleep(0.2 * (attempt + 1))

        return None, f"OpenAlex lookup unavailable ({type(last_err).__name__}); returning unverified reference."

    def verify_reference(self, ref: dict[str, Any]) -> dict[str, Any]:
        key = self._cache_key(ref)
        with self._lock:
            if key in self._cache:
                return dict(self._cache[key])

        candidate, err_note = self._query_openalex(ref)
        expected_title = ref.get("title") or ref.get("raw_reference") or ""
        expected_year = ref.get("year")
        expected_authors: list[str] = ref.get("authors") or []

        matched = False
        reason = err_note or "Reference not found or did not meet title, author, and year agreement thresholds."
        cand_title = None
        cand_year = None
        cand_doi = None
        cand_url = None
        cand_abstract = ""
        title_sim = 0.0
        author_ov = 0.0

        if isinstance(candidate, dict) and candidate.get("id"):
            cand_title = normalize_whitespace(str(candidate.get("title") or ""))
            cand_year = candidate.get("publication_year")
            raw_doi = str(candidate.get("doi") or "")
            cand_doi = raw_doi.replace("https://doi.org/", "").strip() or None
            cand_url = (
                candidate.get("primary_location", {}).get("landing_page_url")
                if isinstance(candidate.get("primary_location"), dict)
                else candidate.get("id")
            )
            cand_abstract = _reconstruct_abstract(candidate.get("abstract_inverted_index"))
            cand_authors = [
                a.get("author", {}).get("display_name", "")
                for a in (candidate.get("authorships") or [])
                if isinstance(a, dict)
            ]

            title_sim = _title_similarity(expected_title, cand_title)
            author_ov = _author_overlap(expected_authors, cand_authors)
            year_ok = True
            if expected_year is not None and cand_year is not None:
                year_ok = abs(int(expected_year) - int(cand_year)) <= self.cfg.openalex_max_year_diff

            doi_exact = bool(ref.get("doi") and cand_doi and ref["doi"].lower().strip() == cand_doi.lower().strip())
            author_ok = True if not expected_authors else (author_ov >= self.cfg.openalex_min_author_overlap)

            if (doi_exact and year_ok) or (
                title_sim >= self.cfg.openalex_min_title_sim and year_ok and author_ok
            ):
                matched = True
                reason = "Matched OpenAlex metadata within title, year, and author thresholds (abstract/metadata only)."
            else:
                reason = "Reference not found / unverified: candidate record failed strict title, year, or author agreement."

        result = {
            "ref_id": ref.get("ref_id"),
            "raw_reference": ref.get("raw_reference"),
            "verified_reference": matched,
            "reference_status": "verified_metadata" if matched else "reference_not_found_unverified",
            "reason": reason,
            "evidence_scope": "abstract_and_metadata_only" if matched else "none",
            "title": cand_title if matched else ref.get("title"),
            "year": cand_year if matched else ref.get("year"),
            "doi": cand_doi if matched else ref.get("doi"),
            "url": cand_url if matched else None,
            "abstract": cand_abstract if matched else "",
            "title_similarity": round(title_sim, 3),
            "author_overlap": round(author_ov, 3),
        }

        with self._lock:
            self._cache[key] = dict(result)
        self._save_cache()
        return result
