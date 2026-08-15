# Developer Guide

---

## First-time Setup

```bash
# 1. Clone / open the project
cd pdf-QA

# 2. Create virtual environment
python -m venv .venv

# 3. Activate it
# Windows
.venv\Scripts\activate
# macOS / Linux
source .venv/bin/activate

# 4. Install all dependencies (including dev tools)
pip install -e ".[dev]"

# 5. Copy the env template and add your API key
cp .env.example .env
# Edit .env → set GOOGLE_API_KEY (or whichever provider you use)

# 6. Verify config loaded correctly
python -m backend.config
```

---

## Running the API Server

```bash
# Development mode (auto-reloads on file changes)
uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000
```

Interactive API docs available at:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

---

## CLI Scripts (Phases 2–4)

Each phase ships a CLI script so you can test the feature without a browser.

```bash
# Phase 2 — Test the LLM adapter
python scripts/test_llm.py

# Phase 3 — Ingest a PDF
python scripts/ingest_pdf.py path/to/document.pdf

# Phase 4 — Ask a question
python scripts/ask.py "What are the key findings of this document?"

# Phase 6 — Multi-hop agent query
python scripts/agent.py "Compare the conclusions in document A and document B"
```

---

## Running Tests

```bash
# Run all tests
pytest -v

# Run a specific phase's tests
pytest backend/tests/test_config.py -v      # Phase 1
pytest backend/tests/test_adapters.py -v    # Phase 2
pytest backend/tests/test_ingestion.py -v   # Phase 3
pytest backend/tests/test_query.py -v       # Phase 4

# Run with output (useful for debugging)
pytest -v -s
```

---

## Phase Verification Checklist

Run these in order to confirm each phase is working end-to-end:

**Phase 1**
```bash
python -m backend.config              # Should print full resolved config
pytest backend/tests/test_config.py   # 6/6 should pass
```

**Phase 2**
```bash
python scripts/test_llm.py            # LLM should respond to a test prompt
curl http://localhost:8000/api/health  # Should return JSON with provider info
```

**Phase 3**
```bash
python scripts/ingest_pdf.py sample.pdf
curl http://localhost:8000/api/documents   # Should list the uploaded doc
```

**Phase 4**
```bash
python scripts/ask.py "What is this document about?"
# Should print: answer + source citations (file name + page number)
```

**Phase 5**
```bash
cd frontend && npm run dev   # Open http://localhost:3000 in browser
# Upload a PDF, ask a question, verify streaming response + source cards appear
```

---

## Switching LLM Providers

1. Edit `config.yaml`:
   ```yaml
   llm:
     provider: "openai"
   embeddings:
     provider: "openai"
   ```
2. Ensure the API key is in `.env`
3. Restart the server / re-run the script

If you changed the **embedding** provider, you must wipe the vector store and re-ingest:
```bash
# Delete ChromaDB data
Remove-Item -Recurse -Force .chroma_db   # Windows PowerShell
rm -rf .chroma_db                        # macOS / Linux

# Re-ingest your PDFs
python scripts/ingest_pdf.py your_doc.pdf
```

---

## Project Conventions

### File naming
- Python files: `snake_case.py`
- Classes: `PascalCase`
- Constants: `UPPER_SNAKE_CASE`

### Imports
- Always import `get_settings()` from `backend.config`, never read files directly
- Adapters should never be imported directly — always go through their Factory

### Adding a new LLM provider
1. Create `backend/adapters/llm/<provider>.py` implementing `BaseLLMAdapter`
2. Add the provider case to `LLMAdapterFactory.create()`
3. Add the provider to the `Literal` type in `LLMSettings`
4. Add default model to `LLMModels` and `EmbeddingModels`
5. Update `docs/llm-providers.md`

### Adding a new API route
1. Create or edit a file in `backend/api/`
2. Register the router in `backend/main.py`
3. Add request/response models to `backend/models/`

---

## Linting & Formatting

```bash
# Check for issues
ruff check .

# Auto-fix issues
ruff check . --fix

# Format code
ruff format .
```

---

## Folder Purposes at a Glance

```
backend/config/      → Settings only. Nothing else imports from here except get_settings().
backend/adapters/    → Pure provider wrappers. No business logic here.
backend/services/    → Business logic: ingestion pipeline, RAG query pipeline.
backend/api/         → HTTP concerns only: parse request, call service, return response.
backend/models/      → Pydantic schemas for API request/response bodies.
backend/storage/     → ChromaDB wrapper. Services use this, never import chromadb directly.
backend/tests/       → One test file per phase.
scripts/             → CLI entrypoints for manual testing. Not imported by the app.
docs/                → You are here.
frontend/            → Next.js app. Talks to the API, knows nothing about the backend internals.
```
