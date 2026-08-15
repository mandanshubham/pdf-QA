# Configuration Guide

All configuration lives in two places:

| File | Purpose |
|---|---|
| `config.yaml` | Human-readable defaults for every setting |
| `.env` | Secrets (API keys) and local overrides |

Environment variables override both. The format is: `PDF_QA__<SECTION>__<KEY>=value`

---

## Full config.yaml Reference

```yaml
llm:
  provider: "gemini"          # Which LLM to use
  model: ""                   # Leave empty = use provider default below
  models:
    gemini:    "gemini-1.5-flash"
    openai:    "gpt-4o-mini"
    anthropic: "claude-3-haiku-20240307"
    ollama:    "llama3.2"
  temperature: 0.2            # 0.0 = deterministic, 1.0 = creative
  max_tokens: 2048            # Max tokens in the LLM response

embeddings:
  provider: "gemini"          # Which model generates embeddings
  model: ""                   # Leave empty = use provider default below
  models:
    gemini:      "models/text-embedding-004"        # 768-dim, free
    openai:      "text-embedding-3-small"           # 1536-dim
    huggingface: "sentence-transformers/all-MiniLM-L6-v2"  # local
    ollama:      "nomic-embed-text"                 # local

retrieval:
  top_k: 5                    # How many chunks to retrieve per question
  score_threshold: 0.3        # Minimum similarity score (0.0–1.0)

chunking:
  chunk_size: 1000            # Characters per chunk
  chunk_overlap: 200          # Overlap between adjacent chunks

vector_store:
  persist_directory: ".chroma_db"    # Where ChromaDB stores its data
  collection_name: "pdf_qa_docs"     # Name of the ChromaDB collection

api:
  host: "0.0.0.0"            # Bind address
  port: 8000                  # Port
  cors_allow_all: true        # Allow all origins (set false in production)
```

---

## LLM Provider Options

### `provider: "gemini"` (default)
- Free tier available at [aistudio.google.com](https://aistudio.google.com)
- Requires: `GOOGLE_API_KEY` in `.env`
- Default model: `gemini-1.5-flash` (fast, free)
- Better model: `gemini-1.5-pro` (more capable, still free tier)

### `provider: "openai"`
- Requires: `OPENAI_API_KEY` in `.env`
- Default model: `gpt-4o-mini` (cheap, fast)
- Better model: `gpt-4o`

### `provider: "anthropic"`
- Requires: `ANTHROPIC_API_KEY` in `.env`
- Default model: `claude-3-haiku-20240307` (cheapest)
- Better model: `claude-3-5-sonnet-20241022`

### `provider: "ollama"` (local, no API key)
- Requires Ollama installed and running: `ollama serve`
- Default model: `llama3.2`
- Pull a model first: `ollama pull llama3.2`

---

## Embedding Provider Options

> **Important**: The embedding provider used during ingestion must match the one used during querying. If you re-index documents, change the provider in config and wipe `.chroma_db/`.

| Provider | Model | Dimensions | Cost |
|---|---|---|---|
| `gemini` | `text-embedding-004` | 768 | Free |
| `openai` | `text-embedding-3-small` | 1536 | ~$0.02/1M tokens |
| `huggingface` | `all-MiniLM-L6-v2` | 384 | Free (local CPU) |
| `ollama` | `nomic-embed-text` | 768 | Free (local) |

---

## Tuning Tips

### Retrieval quality is poor?

1. **Increase `top_k`** (try 8–10) — retrieve more chunks
2. **Lower `score_threshold`** (try 0.1) — less strict filtering
3. **Decrease `chunk_size`** (try 500) — finer-grained chunks
4. **Increase `chunk_overlap`** (try 100) — better context at boundaries

### Answers are too slow?

1. Switch to a faster model (`gemini-1.5-flash`, `gpt-4o-mini`)
2. Lower `max_tokens`
3. Lower `top_k` (fewer chunks = shorter context = faster response)

### Answers are hallucinating?

1. Lower `temperature` (try 0.0)
2. Lower `score_threshold` (discard low-confidence chunks)
3. Check your prompt in `backend/services/query.py`

---

## Environment Variable Override Examples

```bash
# Switch to OpenAI without touching config.yaml
PDF_QA__LLM__PROVIDER=openai

# Use a specific model
PDF_QA__LLM__MODEL=gpt-4o

# Retrieve more chunks
PDF_QA__RETRIEVAL__TOP_K=8

# Use a different ChromaDB path
PDF_QA__VECTOR_STORE__PERSIST_DIRECTORY=./my_vectors
```

Set these in `.env` or export them in your shell before running.
