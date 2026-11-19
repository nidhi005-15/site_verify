from dataclasses import dataclass
import os
from pathlib import Path


def _load_dotenv_if_present() -> None:
    env_path = Path(__file__).resolve().parent / ".env"
    if not env_path.exists() or not env_path.is_file():
        return
    try:
        for raw_line in env_path.read_text(encoding="utf-8").splitlines():
            line = raw_line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, value = line.split("=", 1)
            key = key.strip()
            value = value.strip().strip("\"").strip("\x27")
            if key and key not in os.environ:
                os.environ[key] = value
    except OSError:
        return


@dataclass(frozen=True)
class Settings:
    app_name: str = "CiteVerify"
    app_version: str = "1.0.0"
    openalex_mailto: str = "citeverify@example.org"
    openalex_api_key: str | None = None
    openalex_timeout_seconds: float = 8.0
    llm_provider: str = "none"
    llm_model: str = ""
    llm_api_key: str | None = None
    embedding_model: str = "intfloat/multilingual-e5-base"
    vector_db_dir: str = "./chroma_data"
    rag_top_k: int = 4
    max_upload_bytes: int = 25 * 1024 * 1024


def _parse_int(env_name: str, default: int) -> int:
    raw = os.getenv(env_name)
    if raw is None or not raw.strip():
        return default
    try:
        return int(raw.strip())
    except ValueError:
        return default


def _parse_float(env_name: str, default: float) -> float:
    raw = os.getenv(env_name)
    if raw is None or not raw.strip():
        return default
    try:
        return float(raw.strip())
    except ValueError:
        return default


def get_settings() -> Settings:
    _load_dotenv_if_present()
    llm_key = os.getenv("LLM_API_KEY") or os.getenv("OPENAI_API_KEY") or os.getenv("GEMINI_API_KEY")
    openalex_key = os.getenv("OPENALEX_API_KEY")
    return Settings(
        openalex_mailto=os.getenv("OPENALEX_MAILTO", "citeverify@example.org").strip() or "citeverify@example.org",
        openalex_api_key=openalex_key.strip() if openalex_key and openalex_key.strip() else None,
        openalex_timeout_seconds=_parse_float("OPENALEX_TIMEOUT_SECONDS", 8.0),
        llm_provider=os.getenv("LLM_PROVIDER", "none").strip().lower() or "none",
        llm_model=os.getenv("LLM_MODEL", "").strip(),
        llm_api_key=llm_key.strip() if llm_key and llm_key.strip() else None,
        embedding_model=os.getenv("EMBEDDING_MODEL", "intfloat/multilingual-e5-base").strip() or "intfloat/multilingual-e5-base",
        vector_db_dir=os.getenv("VECTOR_DB_DIR", "./chroma_data").strip() or "./chroma_data",
        rag_top_k=max(1, _parse_int("RAG_TOP_K", 4)),
        max_upload_bytes=max(1024 * 1024, _parse_int("MAX_UPLOAD_BYTES", 25 * 1024 * 1024)),
    )
