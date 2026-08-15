# PDF-QA 📄🤖

> An agentic AI learning project — PDF Question-Answering with configurable cloud LLMs, RAG pipeline, and a Next.js UI.

## Project Structure

```
pdf-QA/
├── backend/            # Python FastAPI backend
│   ├── config/         # Pydantic settings, config loader
│   ├── adapters/       # LLM & embedding adapters (Phase 2)
│   ├── services/       # Ingestion & RAG query (Phases 3–4)
│   ├── api/            # FastAPI route handlers (Phases 2–4)
│   ├── models/         # Pydantic request/response schemas
│   ├── storage/        # ChromaDB vector store wrapper
│   └── tests/          # Pytest smoke tests
├── frontend/           # Next.js UI (Phase 5)
├── scripts/            # CLI smoke test scripts
├── docs/               # Architecture notes
├── config.yaml         # Master configuration
├── .env.example        # API key template
└── pyproject.toml      # Python dependencies
```

## Quick Start

### 1. Set up Python environment

```bash
python -m venv .venv
# Windows
.venv\Scripts\activate
# macOS / Linux
source .venv/bin/activate

pip install -e ".[dev]"
```

### 2. Configure API keys

```bash
cp .env.example .env
# Edit .env and add your GOOGLE_API_KEY (or other provider key)
```

### 3. Verify configuration (Phase 1)

```bash
python -m backend.config
```

### 4. Run tests

```bash
pytest backend/tests/ -v
```

### 5. Start the API server (Phase 2+)

```bash
uvicorn backend.main:app --reload
```

## Configuration

All settings live in [`config.yaml`](config.yaml). Override any value via environment variables using the format:

```
PDF_QA__<SECTION>__<KEY>=value
```

### Switching LLM providers

Edit `config.yaml`:
```yaml
llm:
  provider: "openai"   # gemini | openai | anthropic | ollama
```

Or set an env var: `PDF_QA__LLM__PROVIDER=openai`

## Build Phases

| Phase | What Gets Built | Verify With |
|---|---|---|
| 1 ✅ | Scaffold, config system | `python -m backend.config` |
| 2 | LLM adapters, `/api/health` | `python scripts/test_llm.py` |
| 3 | PDF ingestion, ChromaDB | `python scripts/ingest_pdf.py` |
| 4 | RAG query pipeline | `python scripts/ask.py "..."` |
| 5 | Next.js chat UI | Browser |
| 6 | ReAct agent, memory | CLI multi-hop query |

## Supported LLM Providers

| Provider | Models | Needs Key |
|---|---|---|
| **Gemini** (default) | `gemini-1.5-flash`, `gemini-1.5-pro` | `GOOGLE_API_KEY` (free tier) |
| **OpenAI** | `gpt-4o-mini`, `gpt-4o` | `OPENAI_API_KEY` |
| **Anthropic** | `claude-3-haiku`, `claude-3-5-sonnet` | `ANTHROPIC_API_KEY` |
| **Ollama** | any local model | none (local) |
