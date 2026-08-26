"""Application settings. The single module that reads the environment —
everything else receives typed values from here."""

from functools import lru_cache
from typing import Literal

from pydantic_settings import BaseSettings, SettingsConfigDict

Provider = Literal["local", "gemini", "groq"]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    database_url: str = "postgresql://user:password@localhost:5432/chatdb"

    default_provider: Literal["auto", "local", "gemini", "groq"] = "auto"
    
    gemini_api_key: str = ""
    gemini_model: str = "gemini-2.5-flash"
    groq_api_key: str = ""
    groq_model: str = "llama3-70b-8192"

    ollama_base_url: str = "http://host.docker.internal:11434"
    # llama3.2:3b: no thinking mode, ~2GB, fast enough for interactive use on
    # an 8GB machine. qwen3:4b was measured at ~4.5 tok/s with reasoning
    # preambles leaking into answers — see architecture.md#local-model-choice.
    ollama_model: str = "llama3.2:3b"

    embedding_model: str = "BAAI/bge-small-en-v1.5"
    embedding_dim: int = 384
    transcripts_dir: str = "/data/transcripts"
    retrieval_top_k: int = 8
    rag_similarity_threshold: float = 0.5
    allow_extractive_fallback: bool = True

    model_timeout_s: float = 120.0
    max_concurrent_agent_sessions: int = 2
    log_level: str = "INFO"
    cors_origins: str = "http://localhost:3000"

    experimental_sdk_via_ollama: bool = False
        
    @property
    def gemini_configured(self) -> bool:
        return bool(self.gemini_api_key)
        
    @property
    def groq_configured(self) -> bool:
        return bool(self.groq_api_key)

    def resolve_provider(self, requested: str | None, ollama_ok: bool) -> Provider | None:
        """Resolve a session's provider exactly once, at session creation.

        Returns None when nothing usable is available (caller maps this to a
        structured 503). A session is stamped with the resolved provider and
        never switches silently afterwards.
        """
        choice = requested or self.default_provider
        if choice == "gemini":
            return "gemini" if self.gemini_configured else None
        if choice == "groq":
            return "groq" if self.groq_configured else None
        if choice == "local":
            return "local" if ollama_ok else None
        # auto: prefer cloud when configured, else local when reachable
        if self.gemini_configured:
            return "gemini"
        if self.groq_configured:
            return "groq"
        if ollama_ok:
            return "local"
        return None


@lru_cache
def get_settings() -> Settings:
    return Settings()
