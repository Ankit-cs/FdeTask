# Architecture: The Lenny Growth Assistant

## System architecture

`Browser → FastAPI → Pi Agent → Gemini/Ollama`

`FastAPI → PostgreSQL`

FastAPI serves the static browser application, handles REST/session/retrieval/artifact validation, and calls the private Pi Agent. The Pi Agent performs skill matching and model invocation. PostgreSQL stores both the knowledge base and session messages.

## Frontend component boundaries

The vanilla frontend is split by responsibility rather than a component framework: `index.html` defines the hero/nav, conversation workspace, session drawer, artifact modal, confirmation/rename dialogs, and live regions. `js/app.js` manages API state, provider selection, sessions, chat rendering, artifact viewing/download, and keyboard events. `css/style.css` implements visual and responsive behavior. `marked.min.js` is vendored for Markdown rendering.

## FastAPI endpoints

| Method | Path | Purpose | Request | Response / errors |
| --- | --- | --- | --- | --- |
| GET | `/` | Serve app shell | None | `index.html`; fallback message if missing. |
| GET | `/health` | Detailed system readiness probe | None | service status, dependency readiness, and corpus counts. |
| GET | `/status` | Readiness state | None | DB/Pi/Ollama readiness and corpus counts. |
| GET | `/health/db` | PostgreSQL probe | None | `200` database status; `503` on database exception. |
| GET | `/sessions` | List sessions | None | Session summaries, newest first. |
| POST | `/sessions` | Create a session | optional `{metadata}` | `201` session summary. |
| GET | `/sessions/{session_id}` | Fetch session metadata | Path ID | `200` summary; `404` unknown ID. |
| PATCH | `/sessions/{session_id}` | Rename/update metadata | `{title?, metadata?}` | `200` summary; `404` unknown ID. |
| DELETE | `/sessions/{session_id}` | Delete one session | Path ID | `200`; cascading messages; `404` unknown ID. |
| DELETE | `/sessions` | Delete all sessions | None | deleted count. |
| GET | `/sessions/{session_id}/messages` | Fetch chronological messages | Path ID | messages; `404` unknown ID. |
| POST | `/retrieval/search` | Search corpus | `{query, top_k: 1..20, topic_boost}` | source items; validation `422`. |
| POST | `/chat` | Retrieve, generate, validate artifact, persist | `{prompt, session_id?, provider?, model?}` | response/sources/skill/content/artifact; `400` empty/invalid provider, `404` unknown session, `503` Pi connection failure, or Pi status error. |

## PostgreSQL schema

- `sessions`: integer primary key plus unique indexed public `session_id`, timestamps, and JSON metadata. One-to-many `messages` with cascading deletion.
- `messages`: public session-ID foreign key, role, content, timestamp index, and JSON metadata for provider/sources/content/artifacts.
- `episodes`: transcript episode metadata, unique/indexed slug and guest index.
- `transcript_chunks`: episode foreign key, timestamps, text, metadata, and PostgreSQL `TSVECTOR`; GIN index `ix_chunks_search_vector` supports FTS.
- `topic_indexes`: curated topic metadata keyed by topic.
- `topic_episode_links`: topic foreign key to episode slug mappings; unique `(topic, episode_slug)` index.

## Knowledge ingestion

`data/source/lennys-podcast-transcripts` → validation → normalization → chunking → `data/processed` JSON → PostgreSQL.

Validation accepts transcript frontmatter/structure, normalization preserves episode metadata and timestamps, speaker turns are grouped into chunks, and the loader inserts episodes/topics/chunks before building vectors and the GIN index. Source tracing remains in chunk guest, episode, speaker, timestamp, and YouTube URL fields. The checked-in source repository commit is `be8ab89a890a833cbba2c892178f823fff178c65`. The validator excludes non-transcript/invalid files according to its validation rules; this audit did not rerun ingestion.

## Retrieval

`query → PostgreSQL FTS → topic/guest boosting → relevance threshold → retrieved context → Pi`

The retriever removes meta stopwords, expands selected acronyms (such as PMF/MVP), searches `search_vector` with plain and OR `tsquery` forms, boosts curated topic and named-guest episodes, and refuses empty/weak results below `0.08`. The chat route retries retrieval for a low-result follow-up using the prior user message. The agent keeps sources at a stricter `0.12` threshold.

## Agent routing and model selection

Pi loads `agent/skills/*/SKILL.md`, selects a triggered skill, builds a prompt that treats retrieved transcripts and history as untrusted data, and uses retrieved context plus the last eight persisted messages. **Local** routes to Ollama using `OLLAMA_BASE_URL`/`OLLAMA_MODEL`; **Cloud** routes to Gemini using `GEMINI_API_KEY`. There is no cross-provider fallback: missing Gemini credentials or unavailable Ollama produces an error for the chosen provider.

## Sessions

`session creation → message persistence → context retrieval → isolation`

`/chat` creates a session when no ID is supplied, loads messages only where their `session_id` matches, sends the latest eight as context, then persists user and assistant messages. IDs are checked before read/update/delete; cascades remove associated messages.

## Artifact architecture

`generation → backend validation/sanitization → frontend isolated rendering → download`

Pi identifies Markdown/HTML artifacts from skills/prompt/output. FastAPI validates HTML with `nh3`, either sanitizing it or rejecting it according to `ARTIFACT_SANITIZATION_MODE`. The frontend uses `srcdoc` in an iframe with `sandbox="allow-same-origin"` and no `allow-scripts`; it renders Markdown in the modal and creates client-side download blobs. Artifact content is stored in assistant message JSON metadata, not a dedicated table.

## Security

- Transcript and conversation material is explicitly untrusted in the agent system prompt.
- HTML uses a tag/attribute/URL-scheme allowlist, unsafe CSS filtering, and optional strict rejection.
- The iframe sandbox prevents script permission.
- Gemini keys come from environment variables; `.env` is ignored and `.env.example` uses placeholders.
- CORS is configurable via `ALLOWED_ORIGINS`; Compose currently sets `*` for local evaluation.
- Pi Agent and PostgreSQL are private Compose-network services; PostgreSQL binds only to `127.0.0.1` in production Compose.

## Deployment

The local production topology is PostgreSQL + Pi Agent + FastAPI/static frontend + an Ollama service on `lenny-network`. Start it with:

```bash
docker compose -f docker-compose.prod.yml up --build
```

`backend` is the only app service published at `:8000`; Ollama is published at `:11434` and PostgreSQL is loopback-bound at `:5432`. On a fresh Docker volume, the one-shot `ollama-init` service pulls `OLLAMA_MODEL` (default `llama3.2`) before Pi Agent and backend startup. The named volume retains the model for subsequent startups.
