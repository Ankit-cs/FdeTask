"""Provider resolution and engine lookup.

Resolution happens exactly once, at session creation (see Settings.resolve_provider):
  - explicit "anthropic" → requires a configured key
  - explicit "local"     → requires reachable Ollama with the model pulled
  - "auto" (default)     → anthropic if configured, else local, else nothing
The resolved provider is stamped on the session row and shown in the UI badge.
There is NO silent mid-conversation fallback: if a session's provider fails at
reply time, the stream carries a typed error event and the user chooses what
to do (retry, or start a new session on the other provider). Grounding and
cost transparency beat availability theater.
"""

import asyncpg

from src.util.config import Provider, Settings
from src.models.domain import AgentEngine
from src.service.engines.local_engine import LocalRagEngine
from src.service.engines.gemini_engine import GeminiAgentEngine
from src.service.engines.groq_engine import GroqAgentEngine
from src.service.engines.bit_engine import BitNetEngine

class EngineRouter:
    def __init__(self, settings: Settings, pool: asyncpg.Pool):
        self._settings = settings
        self._engines: dict[str, AgentEngine] = {
            "local": LocalRagEngine(settings, pool),
            "gemini": GeminiAgentEngine(settings, pool),
            "groq": GroqAgentEngine(settings, pool),
            "bitnet": BitNetEngine(settings, pool),
        }

    def engine_for(self, provider: str) -> AgentEngine:
        return self._engines[provider]

    def model_for(self, provider: Provider, requested_model: str | None = None) -> str:
        if requested_model:
            return requested_model
        if provider == "gemini":
            return self._settings.gemini_model
        if provider == "groq":
            return self._settings.groq_model
        return self._settings.ollama_model

    async def resolve(self, requested: str | None) -> Provider | None:
        """Apply the documented fallback chain. Ollama reachability is only
        probed when the decision needs it (never spends an API call)."""
        choice = requested or self._settings.default_provider
        needs_ollama_check = choice in ("local", "auto") and not (
            choice == "auto" and (self._settings.gemini_configured or self._settings.groq_configured)
        )
        ollama_ok = False
        if needs_ollama_check:
            ollama_ok = (await self._engines["local"].check()).ok
        return self._settings.resolve_provider(requested, ollama_ok)

    async def health(self) -> dict:
        return {name: await engine.check() for name, engine in self._engines.items()}
