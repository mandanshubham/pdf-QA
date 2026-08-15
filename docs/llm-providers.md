# LLM Providers Guide

This project supports four LLM providers through a unified adapter interface. You can switch providers by changing a single line in `config.yaml` — no code changes needed.

---

## Quick Setup by Provider

### Gemini (Recommended — Free Tier)

1. Go to [aistudio.google.com](https://aistudio.google.com)
2. Click **Get API Key** → Create API key
3. Add to `.env`:
   ```
   GOOGLE_API_KEY=your_key_here
   ```
4. Set in `config.yaml`:
   ```yaml
   llm:
     provider: "gemini"
   embeddings:
     provider: "gemini"
   ```

**Available models** (verified with this key)

| Model | Speed | Quality | Notes |
|---|---|---|---|
| `gemini-flash-latest` | Fast | Good | ✅ Default — works, free |
| `gemini-pro-latest` | Medium | Excellent | Available |
| `gemini-2.5-flash` | Fast | Very good | Available |
| `gemini-2.5-pro` | Slower | Excellent | Available |

> **Note**: `gemini-1.5-flash` and `gemini-2.0-flash` are deprecated for new API keys.
> Use `gemini-flash-latest` or check `docs/llm-providers.md` for the current list.

**Active embedding model**: `models/gemini-embedding-001` (3072-dim)

---

### OpenAI

1. Go to [platform.openai.com](https://platform.openai.com)
2. API keys → Create new secret key
3. Add to `.env`:
   ```
   OPENAI_API_KEY=your_key_here
   ```
4. Set in `config.yaml`:
   ```yaml
   llm:
     provider: "openai"
   embeddings:
     provider: "openai"
   ```

**Available models**

| Model | Speed | Quality | Cost (per 1M tokens) |
|---|---|---|---|
| `gpt-4o-mini` | Fast | Good | ~$0.15 in / $0.60 out |
| `gpt-4o` | Medium | Excellent | ~$5 in / $15 out |

---

### Anthropic (Claude)

1. Go to [console.anthropic.com](https://console.anthropic.com)
2. API Keys → Create Key
3. Add to `.env`:
   ```
   ANTHROPIC_API_KEY=your_key_here
   ```
4. Set in `config.yaml`:
   ```yaml
   llm:
     provider: "anthropic"
   ```
   > **Note**: Anthropic does not offer an embedding API. Keep `embeddings.provider` as `gemini` or `openai`.

**Available models**

| Model | Speed | Quality | Cost (per 1M tokens) |
|---|---|---|---|
| `claude-3-haiku-20240307` | Very fast | Good | ~$0.25 in / $1.25 out |
| `claude-3-5-sonnet-20241022` | Medium | Excellent | ~$3 in / $15 out |

---

### Ollama (Local — No API Key)

Use this for fully offline, private, zero-cost inference.

1. Install Ollama: [ollama.com/download](https://ollama.com/download)
2. Start the server:
   ```bash
   ollama serve
   ```
3. Pull a model:
   ```bash
   ollama pull llama3.2        # ~2GB, fast
   ollama pull nomic-embed-text  # embedding model
   ```
4. Set in `config.yaml`:
   ```yaml
   llm:
     provider: "ollama"
   embeddings:
     provider: "ollama"
   ```

**No `.env` changes needed.**

---

## Switching Providers

### Option A: Edit config.yaml
```yaml
llm:
  provider: "openai"   # was "gemini"
```
Restart the server (`uvicorn` or `python scripts/...`).

### Option B: Environment variable (no restart for scripts)
```bash
# PowerShell
$env:PDF_QA__LLM__PROVIDER = "openai"
python scripts/test_llm.py
```

### Option C: .env file
```
PDF_QA__LLM__PROVIDER=anthropic
PDF_QA__LLM__MODEL=claude-3-5-sonnet-20241022
```

---

## Embedding Provider Compatibility

> Re-indexing required if you change the embedding provider.

If you switch embedding providers, the old vectors in ChromaDB are incompatible (different dimensions/models). You must:

1. Delete `.chroma_db/`
2. Re-upload and re-index all PDFs

| LLM Provider | Compatible Embedding Providers |
|---|---|
| Gemini | gemini, openai, huggingface |
| OpenAI | openai, gemini, huggingface |
| Anthropic | gemini, openai, huggingface (Anthropic has no embeddings API) |
| Ollama | ollama, huggingface |

---

## Testing a Provider

After setting up a provider, verify it works:
```bash
python scripts/test_llm.py
```

Expected output:
```
Testing LLM adapter...
Provider : gemini
Model    : gemini-1.5-flash
Prompt   : "Say hello in one sentence."
Response : Hello! I'm Gemini, happy to help you today.

>> LLM adapter working correctly.
```
