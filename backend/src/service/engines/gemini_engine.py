"""GeminiAgentEngine — the Google Gemini provider.

Runs a deterministic RAG pipeline.
"""

import time
from typing import AsyncIterator

import asyncpg

from src.service.artifacts.extractor import ArtifactStreamFilter, ExtractedArtifact
from src.service.artifacts.store import save_artifact
from src.util.config import Settings
from src.db.repos import ArtifactRepo
from src.service.engines.intents import Intent, classify
from src.util.logging import EVT_ENGINE_ERROR, EVT_MODEL_CALL, EVT_MODEL_TIMEOUT, get_logger
from src.models.domain import (
    ArtifactEvent, CitationEvent, DoneEvent, EngineEvent, EngineHealth,
    ErrorEvent, Message, RetrievedChunk, Session, TokenEvent, ToolUseEvent, Usage,
)
from src.service.rag.citations import extract_citations, fallback_citations_by_guest
from src.service.rag.embedder import embed_query_async
from src.service.rag.search import hybrid_search
from src.service.skills.loader import ship30_prompt

# Reuse constants and prompt pieces from local_engine
from src.service.engines.local_engine import (
    _CHUNK_CHAR_LIMIT, _CHAT_CHUNKS, _ESSAY_CHUNKS, _HISTORY_MESSAGES, _HISTORY_CHAR_LIMIT,
    _GROUNDING_SYSTEM, _ARTIFACT_INSTRUCTION, _promote_to_artifact, _render_excerpts
)

log = get_logger(__name__)

class GeminiAgentEngine:
    name = "gemini"

    def __init__(self, settings: Settings, pool: asyncpg.Pool):
        self._settings = settings
        self._pool = pool
        self._artifact_repo = ArtifactRepo(pool)

    async def check(self) -> EngineHealth:
        if self._settings.gemini_configured:
            return EngineHealth(ok=True, detail="Gemini API key configured")
        return EngineHealth(ok=False, detail="GEMINI_API_KEY not set")

    async def stream_reply(
        self, session: Session, history: list[Message], user_content: str
    ) -> AsyncIterator[EngineEvent]:
        started = time.perf_counter()
        try:
            intent = classify(user_content)

            # 1. Retrieval
            yield ToolUseEvent(tool="search_transcripts", summary=f'"{user_content[:80]}"')
            embedding = await embed_query_async(user_content, self._settings.embedding_model)
            top_k = min(
                self._settings.retrieval_top_k,
                _ESSAY_CHUNKS if intent == "essay" else _CHAT_CHUNKS,
            )
            chunks = await hybrid_search(self._pool, embedding, user_content, top_k)
            yield ToolUseEvent(
                tool="search_transcripts",
                summary=f"{len(chunks)} transcript excerpts retrieved",
            )
            
            if not chunks or chunks[0].score < self._settings.rag_similarity_threshold:
                yield TokenEvent(text="The transcripts don't cover this.")
                usage = Usage(provider=self.name, model=self._settings.gemini_model)
                usage.latency_ms = int((time.perf_counter() - started) * 1000)
                yield DoneEvent(usage=usage)
                return

            # 2. Prompt assembly
            prompt_text = self._build_prompt(intent, history, user_content, chunks)

            # 3. Stream from Gemini via google-genai
            from google import genai
            from google.genai import types
            import asyncio
            
            client = genai.Client(api_key=self._settings.gemini_api_key)

            buffer_visible = intent != "chat"
            artifact_filter = ArtifactStreamFilter()
            full_text = ""
            visible_text = ""
            usage = Usage(provider=self.name, model=self._settings.gemini_model)
            
            try:
                # Wrap the sync generation with timeout if needed, but aio is native
                response = await client.aio.models.generate_content_stream(
                    model=self._settings.gemini_model,
                    contents=prompt_text,
                    config=types.GenerateContentConfig(
                        temperature=0.3 if intent == "chat" else 0.7,
                    )
                )
                async for chunk in response:
                    delta = chunk.text or ""
                    if delta:
                        full_text += delta
                        visible = artifact_filter.feed(delta)
                        if visible:
                            visible_text += visible
                            if not buffer_visible:
                                yield TokenEvent(text=visible)
            except Exception as e:
                if "timeout" in str(e).lower():
                    raise TimeoutError()
                raise e
            
            tail = artifact_filter.flush()
            if tail:
                visible_text += tail
                if not buffer_visible:
                    yield TokenEvent(text=tail)

            if buffer_visible:
                if not artifact_filter.artifacts and visible_text.strip():
                    artifact_filter.artifacts.append(_promote_to_artifact(intent, visible_text))
                    yield TokenEvent(text="I've written it up — see the artifact viewer.")
                else:
                    yield TokenEvent(text=visible_text)

            # 4. Citations
            citations = extract_citations(full_text, chunks)
            if not citations and chunks:
                citations = fallback_citations_by_guest(full_text, chunks)
                if citations:
                    log.info("citation.fallback_by_guest", count=len(citations))
                    
            from src.service.rag.citations import ensure_citation_footer
            footer = ensure_citation_footer(full_text, chunks)
            if footer:
                yield TokenEvent(text=footer)
                
            for citation in citations:
                yield CitationEvent(citation=citation)

            # 5. Artifacts
            for extracted in artifact_filter.artifacts:
                if intent == "essay" and extracted.kind == "markdown":
                    from src.service.artifacts.validator import validate_ship_30_essay
                    errors = validate_ship_30_essay(extracted.content)
                    if errors:
                        err_msg = "Validation failed for Ship 30 essay. Missing constraints:\n- " + "\n- ".join(errors)
                        yield ErrorEvent(code="validation_failed", message=err_msg, recoverable=True)
                        continue
                        
                artifact = await save_artifact(
                    self._artifact_repo, session.id,
                    extracted.kind, extracted.title, extracted.content,
                )
                yield ArtifactEvent(artifact_id=artifact.id, kind=artifact.kind, title=artifact.title)

            # Usage estimation
            usage.input_tokens = int(len(prompt_text) / 4)
            usage.output_tokens = int(len(full_text) / 4)
            usage.latency_ms = int((time.perf_counter() - started) * 1000)
            
            log.info(EVT_MODEL_CALL, provider=self.name, model=usage.model,
                     latency_ms=usage.latency_ms, ok=True, intent=intent)
            yield DoneEvent(usage=usage)

        except TimeoutError:
            log.error(EVT_MODEL_TIMEOUT, provider=self.name, model=self._settings.gemini_model, timeout_s=self._settings.model_timeout_s)
            if self._settings.allow_extractive_fallback and chunks:
                fallback_text = "I am currently offline or experiencing a timeout, but here are the exact quotes I found from Lenny's podcast regarding your question:\n\n"
                fallback_text += _render_excerpts(chunks)
                yield TokenEvent(text=fallback_text)
                usage.latency_ms = int((time.perf_counter() - started) * 1000)
                yield DoneEvent(usage=usage)
                return
            yield ErrorEvent(
                code="model_timeout",
                message="The Gemini model run exceeded its time budget. Try again.",
                recoverable=True,
            )
        except Exception as exc:
            log.error(EVT_ENGINE_ERROR, provider=self.name, code="gemini_error", detail=str(exc))
            if self._settings.allow_extractive_fallback and chunks:
                fallback_text = "I am currently offline or experiencing an API error, but here are the exact quotes I found from Lenny's podcast regarding your question:\n\n"
                fallback_text += _render_excerpts(chunks)
                yield TokenEvent(text=fallback_text)
                usage.latency_ms = int((time.perf_counter() - started) * 1000)
                yield DoneEvent(usage=usage)
                return
            yield ErrorEvent(code="gemini_error", message=f"Gemini API error: {str(exc)}", recoverable=True)


    # ── internals ────────────────────────────────────────────────────────────

    def _build_prompt(
        self, intent: Intent, history: list[Message],
        user_content: str, chunks: list[RetrievedChunk],
    ) -> str:
        system = _GROUNDING_SYSTEM
        if intent == "essay":
            system += "\n\n# Essay task\n" + ship30_prompt() + \
                      "\n\n" + _ARTIFACT_INSTRUCTION.replace("{kind}", "markdown")
        elif intent == "artifact_html":
            system += "\n\n" + _ARTIFACT_INSTRUCTION.replace("{kind}", "html")
        elif intent == "artifact_markdown":
            system += "\n\n" + _ARTIFACT_INSTRUCTION.replace("{kind}", "markdown")

        hist_text = ""
        for m in history[-_HISTORY_MESSAGES:]:
            hist_text += f"{m.role.capitalize()}: {m.content[:_HISTORY_CHAR_LIMIT]}\n"

        excerpts = _render_excerpts(chunks) if chunks else "(no relevant excerpts found)"
        reminder = (
            "(Cite excerpts inline with [n] markers after each claim; "
            "if the excerpts don't cover it, say so.)"
        )
        
        prompt = f"System instructions:\n{system}\n\n"
        if hist_text:
            prompt += f"Chat history:\n{hist_text}\n\n"
            
        prompt += f"Transcript excerpts:\n\n{excerpts}\n\n---\nRequest: {user_content}\n{reminder}"
        return prompt
