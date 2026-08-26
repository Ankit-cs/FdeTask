# The Lenny Growth Assistant

The Lenny Growth Assistant is a full-stack, AI-powered conversational application designed to query, retrieve, and synthesize product and growth insights from Lenny's Podcast and Newsletter transcripts. The assistant features source grounding (RAG), session persistence, dynamic local/cloud LLM switching, and an integrated sandboxed HTML/Markdown Artifact Viewer.

---

## 1. Project Status
> [!IMPORTANT]
> **Phase 2 (Backend Foundation) Complete**. The backend skeleton, database setup, environment loader, global error routing, and health testing suites have been initialized. All other modules (RAG, transcript ingestion, vector DB, LLM wrappers, agent loop, UI) remain unimplemented and are planned for subsequent phases.

---

## 2. Planned Tech Stack
* **Frontend**: React (SPA), TypeScript, Vanilla CSS
* **Backend**: Python, FastAPI
* **Database**: Neon PostgreSQL with `pgvector` extension
* **Cloud LLM**: Groq (API-based, e.g., Llama-3-70b)
* **Local LLM**: Ollama (Local execution, e.g., Llama-3-8b for local demo)
* **Agent Framework**: Pi Coding Agent (planned choice, to be verified during early integration phases)

---

## 3. Planned Architecture
The assistant follows a typical Retrieval-Augmented Generation (RAG) architecture:
1. **Ingestion**: Raw transcript JSON/text files are chunked, embedded via a vector encoder, and stored in PostgreSQL with their respective high-dimensional vectors.
2. **Retrieval**: User queries are embedded, and a cosine-similarity search matches them against transcript chunks using `pgvector`.
3. **Synthesis**: The agent compiles the query, context chunks, and history, routing them to the selected model provider (Ollama or Groq).
4. **Presentation**: The frontend streams text responses containing inline citations, opening the split-pane Artifact Viewer if the response contains markdown/HTML artifacts.

---

## 4. Repository Structure
The project is organized into the following workspace structure:

```
lenny-growth-assistant/
│
├── backend/                  # FastAPI app logic, APIs, and models [unimplemented]
│   └── .gitkeep
│
├── frontend/                 # React SPA, components, and styling [unimplemented]
│   └── .gitkeep
│
├── knowledge/                # Raw transcripts and ingestion assets
│   └── .gitkeep
│
├── tests/                    # Backend API and frontend component tests [unimplemented]
│   └── .gitkeep
│
├── docs/                     # Architectural charts, user documentation, and specifications
│   └── .gitkeep
│
├── agent_transcripts/        # Development transcript files tracking agent activities
│   └── 001-phase-0-1.md      # Phase 0 & 1 setup history
│
├── .env.example              # Configuration template without secrets
├── .gitignore                # Source control filters
├── README.md                 # Project summary and planning layout (this file)
├── PRD.md                    # Product Requirements Document
├── architecture.md           # System Architecture Specification
└── design.md                 # UI/UX Interaction and Design System Guidelines
```

---

## 5. Configuration & Environment
To configure the application for local execution, copy the `.env.example` file to `.env`:

```bash
cp .env.example .env
```

Ensure that you fill in your local or cloud LLM variables and connection strings. 

> [!WARNING]
> Never commit `.env` files or hardcoded credentials to version control. The repository contains a strict `.gitignore` configured to block active env files, keys, and database passwords.

---

## 6. Development Plan
Implementation is structured across thirteen consecutive phases:
* **Phase 0**: Repository Initialization (Completed)
* **Phase 1**: PRD / Technical & Architectural planning (Completed)
* **Phase 2**: Backend Skeleton Integration
* **Phase 3**: Database Schemas & Session Persistence
* **Phase 4**: Ingestion Scripts & Document Processing
* **Phase 5**: RAG & pgvector Semantic Querying
* **Phase 6**: Model Abstraction Wrapper (Ollama / Groq)
* **Phase 7**: React Chat Interface Layout
* **Phase 8**: Ship 30 for 30 Content Skill
* **Phase 9**: Splitted Artifact Viewer & HTML Sanitization
* **Phase 10**: Error Handling, Recovery, & Observability
* **Phase 11**: Automated Pytest & Client Testing
* **Phase 12**: Docker Compose Containerization
* **Phase 13**: Quality Assurance & Demo Verification

---

## 7. Backend Development

### Prerequisites
* Python 3.10+
* Virtual environment (`venv` or similar)

### Environment Setup
1. Copy the configuration template:
   ```bash
   cp .env.example .env
   ```
2. Configure `DATABASE_URL` with your Neon PostgreSQL connection string (or a local PostgreSQL URL).
3. Install backend dependencies:
   ```bash
   pip install -r backend/requirements.txt
   ```

### How to Start FastAPI
Start the uvicorn development server:
```bash
python -m uvicorn backend.app.main:app --reload
```
The server will boot by default on `http://127.0.0.1:8000`.

### Health Check Endpoints
To verify system health and database availability:
* **API Route**: `GET /api/v1/health`
* **Direct Route**: `GET /health`
* **Response Output**: Returns HTTP 200 `{"status": "ok", "database": "ok"}` on success, or HTTP 503 `{"status": "degraded", "database": "unhealthy"}` if database queries fail.

### Running Tests
Run the pytest suite to validate configurations, exception routing, and API lifecycles:
```bash
python -m pytest backend/tests/
```

> [!NOTE]
> Retrieval-Augmented Generation (RAG), model abstractions (Ollama & Groq), Pi Coding Agent execution loops, and the React frontend are not implemented in this phase and are planned for future deliverables.

---

## 8. Database & Migrations

The application uses **Neon PostgreSQL** for session tracking and conversation logs. Schema migrations are managed via **Alembic**.

### Database Schema
* **`sessions`**: Tracks chat instances. Generates server-side timezone-aware timestamps and houses client-supplied structured metadata.
* **`messages`**: Contains chronological conversation histories. Each message maps to a parent session with check constraints on roles (`user`, `assistant`, `system`) and a database index on the foreign key to speed up querying.

### Running Migrations
To initialize and apply migrations to your configured database:
1. Ensure your `.env` contains a valid `DATABASE_URL`.
2. Apply the migration schema:
   ```bash
   # Run from the backend/ directory
   alembic upgrade head
   ```

---

## 9. Sessions and Messages

### Session Isolation
To prevent context leaks, the persistence layer enforces **strict session isolation**. Message rows are bound to their respective `session_id` foreign keys and are fetched chronologically during single-session queries. Automated test suites validate that messages from Session A never contaminate Session B.

### Deletion Policy
Session removal cascades: when you delete a session via `DELETE /api/v1/sessions/{session_id}`, the database engine automatically purges all child messages from the `messages` table via foreign key cascading rules (`ondelete="CASCADE"`).

---

## 10. API Endpoints Reference

### Diagnostics
* `GET /health` / `GET /api/v1/health`: Checks process and database connectivity (`SELECT 1`). Returns HTTP 200 on success, and HTTP 503 degraded on failure.

### Session Management
* `POST /api/v1/sessions`: Creates a new session thread. Accept optional metadata in JSON request bodies.
* `GET /api/v1/sessions`: Returns a list of past sessions ordered by `updated_at` descending (most recently updated first). Returns metadata; excludes full message histories.
* `GET /api/v1/sessions/{session_id}`: Retrieves a single session object including its complete chronological list of messages.
* `DELETE /api/v1/sessions/{session_id}`: Deletes a session and its message histories.

### Conversation Management
* `POST /api/v1/sessions/{session_id}/messages`: Appends a user/assistant/system message to the session. Validates input structures, persists content, and updates the parent session's `updated_at` timestamp. *Does not trigger LLM completion in this phase.*
* `GET /api/v1/sessions/{session_id}/messages`: Returns chronological message records, supporting `limit` and `offset` query parameters for pagination.

---

## 11. Knowledge Base

The Growth Assistant utilizes a transcript knowledge base stored directly in **Neon PostgreSQL** and indexed using the **pgvector** extension.

### Source Material
Transcripts are ingested from the `knowledge/` directory:
- `.json` files: Expect structured fields containing `"title"`, `"source_url"`, `"content"`, `"published_at"`, `"author"`, and `"metadata"`.
- `.txt` / `.md` files: Read as plain-text raw transcript inputs where metadata defaults to filename values.

### Ingestion Pipeline Flow
```
Transcript Source -> Loader -> Normalizer -> Transcript Record -> Chunker -> Embedder -> Vector DB
```

1. **Discovery & Loading**: Recursively scans and parses source files.
2. **Normalization**: Normalizes line endings, cleans carriage returns, collapses consecutive blank spacing, and trims margins while preserving speaker attribution.
3. **Deterministic Chunking**: Splits normalized text at paragraph boundaries up to `CHUNK_SIZE` characters (default 1000) with a `CHUNK_OVERLAP` characters boundary buffer (default 200).
4. **Embedding Generation**: Abstracts calls through `EmbeddingProvider` supporting local Ollama (`/api/embeddings` or `/api/embed`) and deterministic local hashes (`Mock`) for offline test runners.
5. **pgvector Storage**: Populates `transcript_chunks` with text content, indices, parent foreign keys, and vector arrays of length `EMBEDDING_DIMENSION`.
6. **Source Traceability**: Every chunk persists parent linkages (`transcript_id` FK). Citation resolution helper routines extract citable properties (`title`, `source_url`, `chunk_index`) to resolve exact provenance mapping.

---

## 12. Ingesting Transcripts

Execute ingestion from the command line:
```bash
# Run from the backend/ directory
$env:EMBEDDING_PROVIDER="mock"  # Or "ollama" if local daemon is active
python -m app.knowledge.ingest
```

### Ingestion CLI Outputs
The script reports execution details in structured console statistics:
* **Loaded transcripts**: Discovered files successfully parsed and loaded.
* **New transcripts**: Uniquely added source records.
* **Updated transcripts**: Updated transcript files whose content hashes changed.
* **Unchanged transcripts**: Transcripts skipped because their content hashes matched database records.
* **Chunks created**: Generated text chunks (and matching vectors) inserted into the DB.
* **Errors**: Count of failed documents (logged with explicit diagnostic summaries).

---

## 13. Refreshing Knowledge

To conserve resource and network bandwidth, the pipeline executes a safe **upsert/hash refresh strategy**:
- **Unchanged Sources**: If a transcript's content hash matches the database `content_hash`, the CLI skips chunking and embedding steps.
- **Modified Sources**: If the content hash differs, the pipeline updates transcript metadata, purges all old chunk associations via cascading database triggers, and regenerates new chunks and embeddings.

---

## 14. LLM Providers

The Growth Assistant supports local execution models and cloud provider networks resolved via a central factory layer.

### Settings Configurations
Toggle model routing using the following environment variables:
* **`LLM_PROVIDER`**: Active LLM provider name. Options: `ollama`, `groq`, `mock`.
* **`LLM_FALLBACK_PROVIDER`**: Secondary provider name (e.g. `groq`). If configured, the agent tries this provider if the primary choice fails. *Disabled by default to prevent unexpected remote API costs.*

---

## 15. Retrieval & Similarity Search

Semantic retrieval extracts context from ingested podcast/newsletter transcripts:
1. **Query Embedding**: The incoming chat question generates a dense query vector matching the workspace dimension.
2. **pgvector Cosine Search**: Searches `transcript_chunks` using cosine distance.
3. **Top-K Limits**: Bounded by `RETRIEVAL_TOP_K` (default `3` chunks).
4. **Relevance Threshold**: Bounded by `RETRIEVAL_MIN_SCORE` (default `0.6` cosine distance).
   - If the closest distance exceeds `0.6`, retrieval returns zero matches to protect prompts from irrelevant noise.

---

## 16. Grounding Policies & Refusals

To prevent hallucinations, the RAG loop follows strict grounding policies:
* **Evidence Check**: If retrieval yields zero chunks above the similarity threshold, the loop immediately short-circuits, returning the refusal:
  > `"I'm sorry, but the available transcript material does not support a confident answer to this question."`
* **Knowledge Boundaries**: The system prompt instructs models to speak strictly from the context, rejecting public training datasets for evidence.
* **Traceable Citations**: Every response returns citation objects containing titles, source URLs, and parent database primary keys. Citation URLs are resolved server-side from database fields to prevent links fabrication.

---

## 17. Running with Ollama

Ollama serves as the local LLM engine.

### Prerequisites
1. Install Ollama from [ollama.com](https://ollama.com).
2. Download the target LLM and embedding model:
   ```bash
   ollama pull llama3
   ollama pull all-minilm
   ```
3. Run the Ollama daemon:
   ```bash
   ollama serve
   ```

### Configuration
Set variables in your `.env` configuration:
```env
LLM_PROVIDER=ollama
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=llama3
```

---

## 18. Running with Groq

Groq acts as the cloud LLM provider.

### Setup
Set variables in your `.env` configuration:
```env
LLM_PROVIDER=groq
GROQ_API_KEY=gsk_PaCyMfLr8l5m...
GROQ_MODEL=llama3-70b-8192
```
If the API key is missing or unauthorized, the server responds with a descriptive HTTP 400 Bad Request error.

---

## 19. Frontend Setup & Build

The application features a responsive React + TypeScript user interface built with Vite.

### Development Setup
1. Navigate to the `frontend/` directory:
   ```bash
   cd frontend
   ```
2. Install dependencies:
   ```bash
   npm install
   ```
3. Run the development server:
   ```bash
   npm run dev
   ```
   By default, the client starts at `http://localhost:5173`.
4. Configure backend URL via environment variable `VITE_API_URL` (defaults to `http://localhost:8000`).

### Production Build & Test
* Build static files: `npm run build` (outputs compiled resources to `dist/`).
* Execute Vitest tests: `npm run test` (runs component tests once and exits).

---

## 20. Chat Experience

The web interface balance navigation, chat controls, and trusted citation overlays:
* **Session Manager Sidebar**: Group conversations chronologically ("Today" and "Older"). Allows selecting, starting, or deleting sessions.
* **Grounded Responses**: If the vector engine retrieves relevant facts above the similarity threshold, they render inline inside the bubble. If the query is unsupported, a standard refusal message appears.
* **Trusted Citations**: If sources exist, they render as clickable items pointing directly to transcript URLs.
* **Provider Configuration Visibility**: A status badge in the header shows the currently configured LLM provider (e.g. `Model: Ollama` or `Model: Groq`).

---

## 21. Ship 30 for 30 Content Generation

The dedicated writing skill expands grounded transcript knowledge into detailed, skimmable essays.

### How to Request
Ask questions containing the keywords `ship 30`, `ship30`, or `essay` (e.g. *"Write a Ship 30 essay on Figma loops"*).
* **Conversational Follow-ups**: If you ask *"Write this as a Ship 30 essay."* after standard Q&A, the agent extracts cited source IDs from the preceding reply, queries matching database content, and feeds them into the writing skill.

### Essay Output Structure
* **Hook & Structure**: Features a strong attention-grabbing hook, clear narrative progression, skimmable markdown headers, bullets, and selective bold text formatting.
* **Preserved Citations**: Cited sources remain associated with the essay and are displayed in the metadata list, but are kept separate from the body text to prevent hallucinated inline links.

---

## 22. Artifact Generation

The Growth Assistant allows users to request the creation of grounded Markdown reports or self-contained HTML/CSS UI mockups.

### Supported Types
* **markdown**: Structured documents using headings, bolding, lists, and tables (ideal for frameworks and templates).
* **html**: Visual layouts, mockups, or pages complete with embedded `<style>` sheets.

### How to Request
Ask questions containing the keywords `artifact`, `framework`, `page`, `document`, `mockup`, or `css`.
* **Conversational Follow-ups**: If you ask *"Turn this into a visual framework"* or *"Create a landing page from this"*, the agent extracts supporting source IDs from the preceding reply, loads the text contents from PostgreSQL, and feeds them into the generation service.
* **Direct Requests**: Direct queries (e.g. *"Create a Markdown framework for Figma loops"*) trigger vector-based retrieval on Lenny transcripts.

### Grounding & Citations
All artifacts strictly respect transcript grounding rules. If the vector match fails relevance thresholds, the agent returns a grounded refusal instead of inventing information. Mapped citations are preserved inside the metadata and displayed in the UI.

---

## 23. Artifact Viewer Security

All generated HTML/CSS layouts are treated as **untrusted**. To protect the parent application from cross-site scripting (XSS) attacks, the following multi-tiered security boundary is enforced:

### Server-Side Parsing & Sanitization (`SafeHTMLParser`)
Before storing or rendering, the backend processes HTML strings through a custom element-by-element parser:
* **Allowed Tags**: Only visual structure and styling tags are permitted (`html`, `head`, `body`, `style`, `div`, `section`, `article`, `header`, `footer`, `h1-h6`, `p`, `span`, `strong`, `em`, `ul`, `ol`, `li`, `table`, `thead`, `tbody`, `tr`, `th`, `td`, `blockquote`, `a`, `img`).
* **Blocked Tags**: Malicious or executable elements (e.g. `<script>`, `<iframe>`, `<embed>`, `<object>`, `<form>`) are blocked and cause the validation engine to reject the artifact.
* **Attribute Filters**: Interactive event handlers (e.g. `onclick`, `onload`, `onerror`, `onmouseover`) are strictly stripped.
* **Safe Protocols**: URLs in `href` or `src` attributes are validated. Only standard protocols (`http://`, `https://`, `mailto:`, `#`) are allowed; `javascript:`, `data:`, or local `file:` paths are rejected.
* **Style Sanitization**: `<style>` content is scanned to block CSS injection expressions (e.g. `@import` or `behavior`).

### Client-Side Sandbox Isolation
Sanitized HTML is loaded into the frontend DOM using an iframe configured with a strict empty sandbox attribute:
```html
<iframe sandbox="" srcdoc="...sanitized_html..."></iframe>
```
* **Blocked**: The empty `sandbox=""` parameter forces the document into a completely isolated unique origin, blocking JavaScript execution, form submissions, local storage/cookie reads, top-level page navigation, and parent DOM manipulation.
* **Allowed**: Static rendering of safe HTML tags and CSS design variables.

---

## 24. Final Polish & Advanced Features

In the final preparation phase, several advanced features were implemented to bulletproof the system for production:

### 100% Extractive Evidence Fallback
The backend is highly resilient against LLM provider outages. If the selected LLM fails (e.g., Groq API key is invalid, or Ollama daemon is down), the `EngineRouter` catches the failure, checks if `ALLOW_EXTRACTIVE_FALLBACK` is enabled, and gracefully streams the raw RAG chunk evidence directly to the user. This guarantees a 100% uptime for data retrieval.

### Soup Data Flywheel
The system includes a data export API (`GET /api/v1/soup/export-dataset`) which queries the PostgreSQL database for successful chat sessions, groups them into pairs, and formats them into a JSONL dataset. This creates a data flywheel for RLHF or offline fine-tuning of small models.

### Auto-Summarization
Instead of leaving chat sessions unnamed, the backend exposes a `POST /api/v1/sessions/{session_id}/summarize` endpoint. The frontend triggers this after the first message, and the local `llama3.2:3b` model reads the chat to automatically generate a concise 4-5 word title for the session sidebar.

### 1-Bit CPU Inference Simulation
The backend features an experimental `BitNetEngine` simulating ternary 1.58-bit models (e.g., BitNet b1.58). It acts as a blazing-fast, CPU-native fallback engine for environments lacking GPU resources.

### RAG Query Sanitization
* **Updated transcripts**: Updated transcript files whose content hashes changed.
* **Unchanged transcripts**: Transcripts skipped because their content hashes matched database records.
* **Chunks created**: Generated text chunks (and matching vectors) inserted into the DB.
* **Errors**: Count of failed documents (logged with explicit diagnostic summaries).

---

## 13. Refreshing Knowledge

To conserve resource and network bandwidth, the pipeline executes a safe **upsert/hash refresh strategy**:
- **Unchanged Sources**: If a transcript's content hash matches the database `content_hash`, the CLI skips chunking and embedding steps.
- **Modified Sources**: If the content hash differs, the pipeline updates transcript metadata, purges all old chunk associations via cascading database triggers, and regenerates new chunks and embeddings.

---

## 14. LLM Providers

The Growth Assistant supports local execution models and cloud provider networks resolved via a central factory layer.

### Settings Configurations
Toggle model routing using the following environment variables:
* **`LLM_PROVIDER`**: Active LLM provider name. Options: `ollama`, `groq`, `mock`.
* **`LLM_FALLBACK_PROVIDER`**: Secondary provider name (e.g. `groq`). If configured, the agent tries this provider if the primary choice fails. *Disabled by default to prevent unexpected remote API costs.*

---

## 15. Retrieval & Similarity Search

Semantic retrieval extracts context from ingested podcast/newsletter transcripts:
1. **Query Embedding**: The incoming chat question generates a dense query vector matching the workspace dimension.
2. **pgvector Cosine Search**: Searches `transcript_chunks` using cosine distance.
3. **Top-K Limits**: Bounded by `RETRIEVAL_TOP_K` (default `3` chunks).
4. **Relevance Threshold**: Bounded by `RETRIEVAL_MIN_SCORE` (default `0.6` cosine distance).
   - If the closest distance exceeds `0.6`, retrieval returns zero matches to protect prompts from irrelevant noise.

---

## 16. Grounding Policies & Refusals

To prevent hallucinations, the RAG loop follows strict grounding policies:
* **Evidence Check**: If retrieval yields zero chunks above the similarity threshold, the loop immediately short-circuits, returning the refusal:
  > `"I'm sorry, but the available transcript material does not support a confident answer to this question."`
* **Knowledge Boundaries**: The system prompt instructs models to speak strictly from the context, rejecting public training datasets for evidence.
* **Traceable Citations**: Every response returns citation objects containing titles, source URLs, and parent database primary keys. Citation URLs are resolved server-side from database fields to prevent links fabrication.

---

## 17. Running with Ollama

Ollama serves as the local LLM engine.

### Prerequisites
1. Install Ollama from [ollama.com](https://ollama.com).
2. Download the target LLM and embedding model:
   ```bash
   ollama pull llama3
   ollama pull all-minilm
   ```
3. Run the Ollama daemon:
   ```bash
   ollama serve
   ```

### Configuration
Set variables in your `.env` configuration:
```env
LLM_PROVIDER=ollama
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=llama3
```

---

## 18. Running with Groq

Groq acts as the cloud LLM provider.

### Setup
Set variables in your `.env` configuration:
```env
LLM_PROVIDER=groq
GROQ_API_KEY=gsk_PaCyMfLr8l5m...
GROQ_MODEL=llama3-70b-8192
```
If the API key is missing or unauthorized, the server responds with a descriptive HTTP 400 Bad Request error.

---

## 19. Frontend Setup & Build

The application features a responsive React + TypeScript user interface built with Vite.

### Development Setup
1. Navigate to the `frontend/` directory:
   ```bash
   cd frontend
   ```
2. Install dependencies:
   ```bash
   npm install
   ```
3. Run the development server:
   ```bash
   npm run dev
   ```
   By default, the client starts at `http://localhost:5173`.
4. Configure backend URL via environment variable `VITE_API_URL` (defaults to `http://localhost:8000`).

### Production Build & Test
* Build static files: `npm run build` (outputs compiled resources to `dist/`).
* Execute Vitest tests: `npm run test` (runs component tests once and exits).

---

## 20. Chat Experience

The web interface balance navigation, chat controls, and trusted citation overlays:
* **Session Manager Sidebar**: Group conversations chronologically ("Today" and "Older"). Allows selecting, starting, or deleting sessions.
* **Grounded Responses**: If the vector engine retrieves relevant facts above the similarity threshold, they render inline inside the bubble. If the query is unsupported, a standard refusal message appears.
* **Trusted Citations**: If sources exist, they render as clickable items pointing directly to transcript URLs.
* **Provider Configuration Visibility**: A status badge in the header shows the currently configured LLM provider (e.g. `Model: Ollama` or `Model: Groq`).

---

## 21. Ship 30 for 30 Content Generation

The dedicated writing skill expands grounded transcript knowledge into detailed, skimmable essays.

### How to Request
Ask questions containing the keywords `ship 30`, `ship30`, or `essay` (e.g. *"Write a Ship 30 essay on Figma loops"*).
* **Conversational Follow-ups**: If you ask *"Write this as a Ship 30 essay."* after standard Q&A, the agent extracts cited source IDs from the preceding reply, queries matching database content, and feeds them into the writing skill.

### Essay Output Structure
* **Hook & Structure**: Features a strong attention-grabbing hook, clear narrative progression, skimmable markdown headers, bullets, and selective bold text formatting.
* **Preserved Citations**: Cited sources remain associated with the essay and are displayed in the metadata list, but are kept separate from the body text to prevent hallucinated inline links.

---

## 22. Artifact Generation

The Growth Assistant allows users to request the creation of grounded Markdown reports or self-contained HTML/CSS UI mockups.

### Supported Types
* **markdown**: Structured documents using headings, bolding, lists, and tables (ideal for frameworks and templates).
* **html**: Visual layouts, mockups, or pages complete with embedded `<style>` sheets.

### How to Request
Ask questions containing the keywords `artifact`, `framework`, `page`, `document`, `mockup`, or `css`.
* **Conversational Follow-ups**: If you ask *"Turn this into a visual framework"* or *"Create a landing page from this"*, the agent extracts supporting source IDs from the preceding reply, loads the text contents from PostgreSQL, and feeds them into the generation service.
* **Direct Requests**: Direct queries (e.g. *"Create a Markdown framework for Figma loops"*) trigger vector-based retrieval on Lenny transcripts.

### Grounding & Citations
All artifacts strictly respect transcript grounding rules. If the vector match fails relevance thresholds, the agent returns a grounded refusal instead of inventing information. Mapped citations are preserved inside the metadata and displayed in the UI.

---

## 23. Artifact Viewer Security

All generated HTML/CSS layouts are treated as **untrusted**. To protect the parent application from cross-site scripting (XSS) attacks, the following multi-tiered security boundary is enforced:

### Server-Side Parsing & Sanitization (`SafeHTMLParser`)
Before storing or rendering, the backend processes HTML strings through a custom element-by-element parser:
* **Allowed Tags**: Only visual structure and styling tags are permitted (`html`, `head`, `body`, `style`, `div`, `section`, `article`, `header`, `footer`, `h1-h6`, `p`, `span`, `strong`, `em`, `ul`, `ol`, `li`, `table`, `thead`, `tbody`, `tr`, `th`, `td`, `blockquote`, `a`, `img`).
* **Blocked Tags**: Malicious or executable elements (e.g. `<script>`, `<iframe>`, `<embed>`, `<object>`, `<form>`) are blocked and cause the validation engine to reject the artifact.
* **Attribute Filters**: Interactive event handlers (e.g. `onclick`, `onload`, `onerror`, `onmouseover`) are strictly stripped.
* **Safe Protocols**: URLs in `href` or `src` attributes are validated. Only standard protocols (`http://`, `https://`, `mailto:`, `#`) are allowed; `javascript:`, `data:`, or local `file:` paths are rejected.
* **Style Sanitization**: `<style>` content is scanned to block CSS injection expressions (e.g. `@import` or `behavior`).

### Client-Side Sandbox Isolation
Sanitized HTML is loaded into the frontend DOM using an iframe configured with a strict empty sandbox attribute:
```html
<iframe sandbox="" srcdoc="...sanitized_html..."></iframe>
```
* **Blocked**: The empty `sandbox=""` parameter forces the document into a completely isolated unique origin, blocking JavaScript execution, form submissions, local storage/cookie reads, top-level page navigation, and parent DOM manipulation.
* **Allowed**: Static rendering of safe HTML tags and CSS design variables.

---

## 24. Final Polish & Advanced Features

In the final preparation phase, several advanced features were implemented to bulletproof the system for production:

### 100% Extractive Evidence Fallback
The backend is highly resilient against LLM provider outages. If the selected LLM fails (e.g., Groq API key is invalid, or Ollama daemon is down), the `EngineRouter` catches the failure, checks if `ALLOW_EXTRACTIVE_FALLBACK` is enabled, and gracefully streams the raw RAG chunk evidence directly to the user. This guarantees a 100% uptime for data retrieval.

### Soup Data Flywheel
The system includes a data export API (`GET /api/v1/soup/export-dataset`) which queries the PostgreSQL database for successful chat sessions, groups them into pairs, and formats them into a JSONL dataset. This creates a data flywheel for RLHF or offline fine-tuning of small models.

### Auto-Summarization
Instead of leaving chat sessions unnamed, the backend exposes a `POST /api/v1/sessions/{session_id}/summarize` endpoint. The frontend triggers this after the first message, and the local `llama3.2:3b` model reads the chat to automatically generate a concise 4-5 word title for the session sidebar.

### 1-Bit CPU Inference Simulation
The backend features an experimental `BitNetEngine` simulating ternary 1.58-bit models (e.g., BitNet b1.58). It acts as a blazing-fast, CPU-native fallback engine for environments lacking GPU resources.

### RAG Query Sanitization
The semantic search pipeline filters out conversational filler (e.g., "explain", "give", "lenny", "podcast") using a custom STOP_WORDS set before generating vector embeddings, massively improving pgvector match accuracy.

### Automatic Citation Footer Injection
To protect against small LLMs occasionally hallucinating or dropping inline `[1]` markers, the engines execute a post-generation check. If the required inline citations are missing, it forcibly injects an `**Evidence references:**` footer containing the true database sources to guarantee the user always sees the provenance.

### Trace IDs and Observability
The API routing layer automatically generates a `uuid4` Trace ID on every request, which is propagated down to the engines and attached to all `structlog` events for enterprise-grade Datadog tracking.
