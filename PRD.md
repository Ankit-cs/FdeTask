# Product Requirements Document: The Lenny Growth Assistant

**Status:** implementation audit, 25 August 2026. This records the implemented product against the supplied assignment PRD and does not substitute unmeasured outcomes for evidence.

## 1. Product / Problem

The primary user is a product manager, growth practitioner, founder, research-oriented team member, or evaluator who needs practical product and growth insight from Lenny's Podcast. They want to ask questions, discover relevant episodes and expert perspectives, and turn grounded material into reusable writing or small artifacts. The assistant removes manual transcript search, prompt construction, provider complexity, and unsupported corpus claims.

## 2. Success Metric

| Metric | Target metric | Measured result |
| --- | --- | --- |
| Grounded answer accuracy | Define an evaluator-labelled answer benchmark before submission. | **Not measured at answer level:** Local generation completed 0/1 requests. Retrieval proxy: 1/6 expected top-guest matches (16.7%) on the existing supported-query benchmark. |
| Source citation rate | Supported domain answers should include retrieved source metadata. | **Partially measured:** a live supported Gemini response included 5 retrieved source records. The full benchmark citation rate remains unmeasured. |
| Unsupported-question refusal rate | 100% of evaluated unsupported prompts should refuse rather than assert corpus claims. | **1/1 (100%) live check:** an unsupported black-hole prompt returned zero sources and an explicit corpus-limited refusal. The larger benchmark remains unmeasured. |
| Successful request completion | Track successful chat requests by provider. | **Cloud Gemini:** 2/2 successful HTTP chat requests on 26 August 2026; one supported response carried five sources. **Local Ollama:** 1/1 successful HTTP chat request after automatic `llama3.2` provisioning. |
| Retrieval/model/database failure rate | Track failures by dependency during evaluator runs. | Retrieval transport: 0/7 HTTP failures (all returned 200), but 6/7 benchmark relevance/refusal checks failed. Model: Local Ollama 1/1 failed; its `/api/tags` response had no models. Database: 0 observed faults across seven retrieval requests plus one `/health/db` check; no failure was injected. |
| Evaluator setup time | Record fresh-machine setup time. | Not measured: the Docker stack was already running, so this was not a fresh-machine trial. |
| Critical-workflow coverage | Cover API, retrieval, sessions, artifacts, frontend, and production config. | **78/78 passed** on 26 August 2026 using `backend/.venv`; coverage includes API, retrieval, sessions, artifacts, frontend contracts, and production configuration. |

### Measurement conditions — 26 August 2026

The running local stack reported `ready`, with 297 episodes and 14,933 chunks. The retrieval sample used the repository's seven existing benchmark prompts through `POST /retrieval/search` with `top_k=5` and topic boosting enabled. Mean client-observed endpoint latency was **2,407.1 ms** across the seven requests; this includes local HTTP and application overhead and is not a database-only latency measurement. Gemini completed two live chat checks, including a supported response with five sources and an unsupported-prompt refusal. The Docker-managed Ollama initializer then provisioned `llama3.2`, and a Local chat request completed successfully. These are limited live checks, not a complete evaluator benchmark.

## 3. User Job-to-be-Done

“When I am trying to solve a product or growth problem, I want to find relevant Lenny's Podcast insights and turn them into a grounded answer or reusable artifact, so that I can make a better-informed decision without manually searching the corpus.”

## 4. Assumptions

- A single product/growth user or evaluator runs the app locally; there is no authentication or identity boundary.
- The supplied transcript corpus is the only knowledge source and is only as fresh as checked-in data.
- Sessions persist until deleted or their PostgreSQL volume is removed.
- Gemini needs a user-provided API key. Ollama and `llama3.2` must be installed/pulled and reachable.
- The local machine can run Docker, PostgreSQL, Node, Python, and an Ollama model; local quality/latency vary with hardware.
- Generated artifact types are Markdown and HTML/CSS. Artifacts are returned with a chat response, not stored in a separate table.
- Transcripts, conversation text, and generated HTML are untrusted data.
- Evaluation occurs locally at `http://localhost:8000` using Compose and `.env`.

## 5. Scope

### In scope

- Grounded transcript answers with source links.
- PostgreSQL-backed isolated sessions and recent context.
- Ship 30 skill, structured content, Markdown, and HTML/CSS artifacts.
- Local Ollama and Cloud Gemini selection.
- HTML sanitization/rejection, iframe sandboxing, health endpoints, Compose setup, tests, and documentation.

### Out of scope

- General web search or knowledge outside the supplied corpus.
- Autonomous external actions.
- Multi-user collaboration, authentication, and persistent user profiles.
- Production-scale traffic or public cloud deployment.
- Complex document editing.

These exclusions preserve the assignment's grounded, local-evaluation boundary.

## 6. User Flows

- **Flow A — Ask a Question:** New Chat → Ask Question → Retrieve Knowledge → Generate Answer → Show Sources.
- **Flow B — Follow-up:** Existing Session → Follow-up → Session Context + Relevant Knowledge → Answer.
- **Flow C — Generate Ship 30 Essay:** Conversation → Request Essay → Grounded Generation → Display Result.
- **Flow D — Generate Artifact:** Conversation → Request Artifact → Generate Markdown/HTML → Artifact Viewer.
- **Flow E — Unsupported Question:** Question → Insufficient Knowledge → Explain Limitation → Avoid Unsupported Claim.

The visible selector chooses Local (Ollama) or Cloud (Gemini). A new session is explicit or created on the first chat request without a session ID. Accepted artifacts open in a modal and download as `.md` or `.html`.

## 7. Acceptance Criteria

- Users can create, list, rename, select, delete, and retrieve isolated sessions and messages.
- Domain queries retrieve transcript chunks and return source metadata for grounded responses.
- Insufficient retrieval context yields a corpus-limited refusal.
- The provider selector sends `ollama` or `gemini`; invalid providers return HTTP 400.
- A Ship 30 request invokes the checked-in dedicated skill.
- Markdown/HTML artifacts can be returned; accepted HTML is sanitized or valid, rejected HTML has no downloadable content.
- HTML renders in an iframe without scripts; Escape closes the artifact modal.
- Health/status/database endpoints and documented Compose startup exist.

## 8. Risks & Trade-offs

| Risk | Impact | Mitigation | Current status |
| --- | --- | --- | --- |
| Hallucination | Unsupported advice | Retrieved context, sources, refusal prompt | Implemented; accuracy unmeasured. |
| Retrieval failure | Missed evidence/refusal | PostgreSQL FTS, topic/guest boosts, threshold | Implemented; benchmark unrun. |
| Latency | Slow chat | Local retrieval; 90-second Pi request timeout | Unmeasured. |
| Cloud cost | Variable spend | Named provider choice and BYO Gemini key | No cost telemetry. |
| Local model quality | Weak output | Configurable Ollama model | Hardware/model dependent. |
| Data leakage/prompt injection | Unsafe instructions or sensitive corpus | Untrusted-data system instruction | No authentication. |
| Unsafe HTML | Browser compromise | `nh3` allowlist, reject mode, iframe sandbox | Implemented. |
| Sanitization | Benign markup removed | Valid/sanitized/rejected states | Expected trade-off. |
| Ollama unavailable | Local request failure | Readiness checks and UI error | No cloud fallback. |
| PostgreSQL dependency | Session/retrieval unavailable | Health check and Compose dependencies | Recovery unverified. |

## 9. Implementation Plan

1. **Foundation** — FastAPI, frontend shell, Compose, environment configuration.
2. **Knowledge Base / RAG** — validation, normalization, chunks, PostgreSQL FTS, topic indexes.
3. **Sessions / Persistence** — PostgreSQL sessions/messages and context retrieval.
4. **Skills / Artifacts / Security** — Pi skills, artifacts, sanitization, sandboxing.
5. **Frontend** — hero, selector, chat, drawer, artifact modal.
6. **Production / Deployment / Deliverables** — local production Compose, health checks, tests, and audit docs.

The phases describe existing repository material. Test execution, clean startup, public repository, demo, upload, and submission remain unverified completion tasks.
