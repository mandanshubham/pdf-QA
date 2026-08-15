"""
backend/agent/react.py

ReAct Agent implementation for Phase 6.
Provides an agent that uses tools (like PDFSearchTool) to answer questions,
allowing for multi-hop reasoning (e.g. searching, synthesizing, then searching again).
"""

from __future__ import annotations

from typing import Any

from langchain_core.messages import BaseMessage, SystemMessage, HumanMessage
from langgraph.prebuilt import create_react_agent

from backend.adapters.llm.base import BaseLLMAdapter
from backend.services.query import RAGQueryService
from backend.agent.tools import PDFSearchTool


_AGENT_SYSTEM_PROMPT = """\
You are an intelligent document research assistant. 
You can search the user's uploaded PDF documents using the `pdf_search` tool.

Guidelines:
1. If the user asks a question about the documents, ALWAYS use the `pdf_search` tool to find the information.
2. If you need to make multiple searches to synthesize an answer, do so.
3. Base your answers strictly on the search results. If the information is not in the documents, state that clearly.
4. Be concise, accurate, and professional.
5. Do NOT include manual citations, file names, or page numbers in your text response. The system handles citations automatically.
"""

class AgentService:
    """
    Orchestrates the ReAct Agent using Tool Calling via langgraph.
    """
    
    def __init__(self, llm_adapter: BaseLLMAdapter, query_service: RAGQueryService):
        self._llm = llm_adapter.get_llm()
        self._query_service = query_service
        self._tools = [PDFSearchTool(query_service=query_service)]
        
        # Create agent using langgraph
        self._agent = create_react_agent(
            model=self._llm,
            tools=self._tools,
            prompt=_AGENT_SYSTEM_PROMPT
        )

    def chat(self, user_input: str, chat_history: list[BaseMessage] | None = None) -> dict[str, Any]:
        """
        Send a message to the agent and get the response.
        
        Returns a dict containing 'output' (the final answer).
        """
        if chat_history is None:
            chat_history = []
            
        messages = chat_history + [HumanMessage(content=user_input)]
        
        # invoke returns a dict with "messages" key which contains the full updated message list
        result = self._agent.invoke({"messages": messages})
        
        # The last message is the AI's final response
        last_message = result["messages"][-1]
        
        return {"output": last_message.content}

