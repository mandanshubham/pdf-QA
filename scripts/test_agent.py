"""
scripts/test_agent.py

Phase 6 CLI test for Agentic Enhancements.
Starts a conversational session with the ReAct agent, allowing multi-hop queries.
"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from langchain_core.messages import HumanMessage, AIMessage

from backend.config import get_settings
from backend.adapters.embeddings.factory import EmbeddingAdapterFactory
from backend.adapters.llm.factory import LLMAdapterFactory
from backend.services.query import RAGQueryService
from backend.storage.vector_store import VectorStore
from backend.agent.react import AgentService

def main():
    print("\n" + "=" * 60)
    print("  PDF-QA - Agentic Chat CLI")
    print("=" * 60)

    print("Loading config and initializing agent...", end=" ")
    cfg = get_settings()
    
    # Initialize Core Services
    embedder = EmbeddingAdapterFactory.create(cfg)
    llm = LLMAdapterFactory.create(cfg)
    store = VectorStore(cfg.vector_store, embedder)
    query_service = RAGQueryService(store, llm, cfg.retrieval)
    
    # Initialize Agent
    agent_service = AgentService(llm, query_service)
    print("OK\n")
    
    docs = store.list_documents()
    if not docs:
        print("Warning: No documents indexed. The agent won't find any context.")
        print("Run `python scripts/ingest_pdf.py <your.pdf>` first.\n")
    else:
        print(f"Indexed {len(docs)} document(s): {[d.filename for d in docs]}\n")

    print("You can ask complex questions that require multiple searches.")
    print("Type 'exit' or 'quit' to stop.\n")

    chat_history = []
    
    while True:
        try:
            user_input = input("You: ").strip()
            if user_input.lower() in ('exit', 'quit'):
                break
            if not user_input:
                continue
                
            print("Agent is thinking...", flush=True)
            result = agent_service.chat(user_input, chat_history)
            
            answer = result["output"]
            print(f"\nAgent: {answer}\n")
            
            # Update history
            chat_history.append(HumanMessage(content=user_input))
            chat_history.append(AIMessage(content=answer))
            
        except (KeyboardInterrupt, EOFError):
            print("\nExiting...")
            break
        except Exception as e:
            print(f"\nError: {e}\n")

if __name__ == "__main__":
    main()
