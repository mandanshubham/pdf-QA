"""
backend/services/query.py

RAG Query Service — the core of the question-answering pipeline.

Pipeline:
    User question
        → embed question (EmbeddingAdapter)
        → similarity search (VectorStore → top-K chunks)
        → build context prompt
        → LLM call (LLMAdapter)
        → answer + source citations

What you learn here:
    - How retrieval-augmented generation works end-to-end
    - Why prompt engineering matters (system prompt structure)
    - Grounding: only answering from retrieved context (no hallucination)
    - Streaming: how to yield LLM tokens as they arrive
    - Source attribution: mapping answers back to document pages
"""

from __future__ import annotations

from collections.abc import Iterator

from langchain_core.messages import HumanMessage, SystemMessage

from backend.adapters.llm.base import BaseLLMAdapter
from backend.config.settings import RetrievalSettings
from backend.models.chat import ChatResponse, SourceCitation, StreamChunk
from backend.storage.vector_store import SearchResult, VectorStore


# ── System prompt ─────────────────────────────────────────────────────────────

_SYSTEM_PROMPT = """\
You are a precise document assistant. Your job is to answer questions \
strictly based on the document context provided below.

Rules:
- Only use information from the CONTEXT section to answer.
- If the context does not contain the answer, say: \
  "I couldn't find relevant information in the provided documents."
- Be concise and factual. Do not add information you were not given.
- Do NOT include manual citations, file names, or page numbers in your text response (e.g., avoid writing "Based on the provided document..." or "(Shubham_Mandan_Resume.pdf, Page 1)"). The system will automatically append source badges.
"""

_CONTEXT_TEMPLATE = """\
CONTEXT (retrieved from your documents):
{context_blocks}

---
QUESTION: {question}

ANSWER:"""


class RAGQueryService:
    """
    Orchestrates the full RAG query pipeline.

    Usage:
        service = RAGQueryService(vector_store, llm_adapter, retrieval_settings)

        # Standard (non-streaming)
        response = service.query("What is the main topic of the document?")
        print(response.answer)
        for source in response.sources:
            print(f"  [{source.filename} p.{source.page}]")

        # Streaming
        for event in service.stream_query("Summarise the key points"):
            if event.type == "token":
                print(event.content, end="", flush=True)
            elif event.type == "sources":
                print(event.sources)
    """

    def __init__(
        self,
        vector_store: VectorStore,
        llm_adapter: BaseLLMAdapter,
        retrieval_settings: RetrievalSettings,
    ) -> None:
        self._store = vector_store
        self._llm = llm_adapter
        self._retrieval = retrieval_settings

    # ── Public API ────────────────────────────────────────────────────────────

    def query(
        self,
        question: str,
        top_k: int | None = None,
        doc_ids: list[str] | None = None,
    ) -> ChatResponse:
        """
        Run a full RAG query and return the complete answer.

        Args:
            question: The user's question as a plain string.
            top_k: Override the config top_k for this request.
            doc_ids: Restrict search to these document IDs only.

        Returns:
            ChatResponse with answer text and source citations.
        """
        k = top_k or self._retrieval.top_k
        threshold = self._retrieval.score_threshold

        # Step 1: Retrieve relevant chunks
        results = self._store.search(question, top_k=k, score_threshold=threshold, doc_ids=doc_ids)

        # Step 2: Build LangChain messages
        messages = self._build_messages(question, results)

        # Step 3: Call LLM
        if results:
            answer = self._llm.chat(messages)
        else:
            answer = (
                "I couldn't find relevant information in the provided documents. "
                "Please upload a PDF first and try again."
            )

        # Step 4: Build source citations
        sources = self._build_citations(results)

        return ChatResponse(
            question=question,
            answer=answer,
            sources=sources,
            chunks_searched=len(results),
        )

    def stream_query(
        self,
        question: str,
        top_k: int | None = None,
        doc_ids: list[str] | None = None,
    ) -> Iterator[StreamChunk]:
        """
        Stream the RAG query response token by token via SSE.

        Yields StreamChunk events in this order:
          1. type="token"  — one per LLM token (content = the token text)
          2. type="sources" — after the answer is complete (content = citations)
          3. type="done"   — signals the stream is finished

        Args:
            question: The user's question.
            top_k: Override config top_k.
            doc_ids: Restrict to specific documents.
        """
        k = top_k or self._retrieval.top_k
        threshold = self._retrieval.score_threshold

        # Retrieve
        results = self._store.search(question, top_k=k, score_threshold=threshold, doc_ids=doc_ids)

        if not results:
            yield StreamChunk(
                type="token",
                content=(
                    "I couldn't find relevant information in the provided documents. "
                    "Please upload a PDF first and try again."
                ),
            )
            yield StreamChunk(type="sources", sources=[])
            yield StreamChunk(type="done")
            return

        # Build messages and stream LLM tokens
        messages = self._build_messages(question, results)
        for token in self._llm.stream(messages):
            yield StreamChunk(type="token", content=token)

        # After streaming completes, emit sources then done
        yield StreamChunk(type="sources", sources=self._build_citations(results))
        yield StreamChunk(type="done")

    # ── Private helpers ───────────────────────────────────────────────────────

    def _build_messages(self, question: str, results: list[SearchResult]) -> list:
        """
        Build the LangChain message list for the LLM call.

        Structure:
          SystemMessage — role and grounding rules
          HumanMessage  — context blocks + question
        """
        context_blocks = self._format_context(results)
        human_content = _CONTEXT_TEMPLATE.format(
            context_blocks=context_blocks,
            question=question,
        )
        return [
            SystemMessage(content=_SYSTEM_PROMPT),
            HumanMessage(content=human_content),
        ]

    @staticmethod
    def _format_context(results: list[SearchResult]) -> str:
        """
        Format retrieved chunks into a numbered context block.

        Each block shows:
          [1] Source: filename.pdf (Page 3) | Score: 0.87
          <chunk text>
        """
        if not results:
            return "(No relevant context found)"

        blocks = []
        for i, r in enumerate(results, start=1):
            filename = r.metadata.get("filename", "unknown")
            page = r.metadata.get("page", "?")
            blocks.append(
                f"[{i}] Source: {filename} (Page {page}) | Relevance: {r.score:.2f}\n"
                f"{r.text}"
            )
        return "\n\n---\n\n".join(blocks)

    @staticmethod
    def _build_citations(results: list[SearchResult]) -> list[SourceCitation]:
        """Convert SearchResult objects into SourceCitation objects for the response."""
        seen: set[str] = set()
        citations: list[SourceCitation] = []

        for r in results:
            # Deduplicate: one citation per (filename, page) pair
            key = f"{r.metadata.get('filename')}:{r.metadata.get('page')}"
            if key in seen:
                continue
            seen.add(key)

            citations.append(
                SourceCitation(
                    filename=r.metadata.get("filename", "unknown"),
                    page=r.metadata.get("page", 0),
                    score=r.score,
                    snippet=r.text[:200],
                    doc_id=r.doc_id,
                )
            )
        return citations
