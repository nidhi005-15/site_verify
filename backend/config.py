from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path


def _env_bool(name: str, default: bool) -> bool:
    raw = os.getenv(name)
    if raw is None:
        return default
    return raw.strip().lower() in {"1", "true", "yes", "on"}


def _env_int(name: str, default: int) -> int:
    raw = os.getenv(name)
    if raw is None:
        return default
    try:
        return int(raw.strip())
    except ValueError:
        return default


def _env_float(name: str, default: float) -> float:
    raw = os.getenv(name)
    if raw is None:
        return default
    try:
        return float(raw.strip())
    except ValueError:
        return default


@dataclass(frozen=True)
class Settings:
    app_name: str
    llm_enabled: bool
    llm_provider: str
    llm_model: str
    llm_api_key: str
    llm_base_url: str
    llm_timeout_sec: float
    llm_max_retries: int
    local_nlp_enabled: bool
    local_embedding_model: str
    local_nli_model: str
    cache_dir: Path
    verification_cache_path: Path
    openalex_cache_path: Path
    openalex_timeout_sec: float
    openalex_max_retries: int
    openalex_min_title_sim: float
    openalex_min_author_overlap: float
    openalex_max_year_diff: int
    max_upload_bytes: int
    max_pdf_pages: int
    sample_corpus_dir: Path
    random_seed: int


def load_settings() -> Settings:
    backend_root = Path(__file__).resolve().parent
    cache_dir = Path(os.getenv("CITEVERIFY_CACHE_DIR", str(backend_root / ".cache"))).resolve()
    cache_dir.mkdir(parents=True, exist_ok=True)

    provider = os.getenv("CITEVERIFY_LLM_PROVIDER", "none").strip().lower()
    if provider == "gemini":
        api_key = os.getenv("GEMINI_API_KEY", "").strip()
    elif provider == "openai":
        api_key = os.getenv("OPENAI_API_KEY", "").strip()
    elif provider == "anthropic":
        api_key = os.getenv("ANTHROPIC_API_KEY", "").strip()
    else:
        api_key = os.getenv("CITEVERIFY_LLM_API_KEY", "").strip()

    default_models = {
        "gemini": "gemini-2.5-flash",
        "openai": "gpt-4o-mini",
        "anthropic": "claude-3-5-haiku-latest",
        "none": "",
    }
    model = os.getenv("CITEVERIFY_LLM_MODEL", "").strip() or default_models.get(provider, "")
    llm_enabled = _env_bool("CITEVERIFY_LLM_ENABLED", False) and provider in {
        "gemini",
        "openai",
        "anthropic",
    }

    corpus_raw = os.getenv(
        "CITEVERIFY_SAMPLE_CORPUS_DIR", str(backend_root / "tests" / "sample_corpus")
    )
    return Settings(
        app_name="CiteVerify",
        llm_enabled=llm_enabled,
        llm_provider=provider,
        llm_model=model,
        llm_api_key=api_key,
        llm_base_url=os.getenv("CITEVERIFY_LLM_BASE_URL", "").strip(),
        llm_timeout_sec=_env_float("CITEVERIFY_LLM_TIMEOUT_SEC", 15.0),
        llm_max_retries=max(0, _env_int("CITEVERIFY_LLM_MAX_RETRIES", 2)),
        local_nlp_enabled=_env_bool("CITEVERIFY_LOCAL_NLP_ENABLED", False),
        local_embedding_model=os.getenv(
            "CITEVERIFY_LOCAL_EMBEDDING_MODEL", "sentence-transformers/all-MiniLM-L6-v2"
        ).strip(),
        local_nli_model=os.getenv(
            "CITEVERIFY_LOCAL_NLI_MODEL", "cross-encoder/nli-deberta-v3-small"
        ).strip(),
        cache_dir=cache_dir,
        verification_cache_path=Path(
            os.getenv("CITEVERIFY_VERIFICATION_CACHE", str(cache_dir / "verification_cache.sqlite"))
        ).resolve(),
        openalex_cache_path=Path(
            os.getenv("CITEVERIFY_OPENALEX_CACHE", str(cache_dir / "openalex_cache.json"))
        ).resolve(),
        openalex_timeout_sec=_env_float("CITEVERIFY_OPENALEX_TIMEOUT_SEC", 8.0),
        openalex_max_retries=max(0, _env_int("CITEVERIFY_OPENALEX_MAX_RETRIES", 2)),
        openalex_min_title_sim=_env_float("CITEVERIFY_OPENALEX_MIN_TITLE_SIM", 0.65),
        openalex_min_author_overlap=_env_float("CITEVERIFY_OPENALEX_MIN_AUTHOR_OVERLAP", 0.40),
        openalex_max_year_diff=max(0, _env_int("CITEVERIFY_OPENALEX_MAX_YEAR_DIFF", 1)),
        max_upload_bytes=max(
            1024 * 1024, _env_int("CITEVERIFY_MAX_UPLOAD_BYTES", 15 * 1024 * 1024)
        ),
        max_pdf_pages=max(1, _env_int("CITEVERIFY_MAX_PDF_PAGES", 60)),
        sample_corpus_dir=Path(corpus_raw).resolve(),
        random_seed=_env_int("CITEVERIFY_RANDOM_SEED", 42),
    )


settings: Settings = load_settings()
