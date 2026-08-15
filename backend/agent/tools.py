"""
backend/agent/tools.py

LangChain tools for the agent.
Here we wrap our RAGQueryService into a tool that an LLM agent can use to search the PDFs.
"""

from __future__ import annotations

from typing import Any
from pydantic import BaseModel, Field

from langchain_core.tools import BaseTool

from backend.services.query import RAGQueryService


class PDFSearchInput(BaseModel):
    query: str = Field(description="The search query to look up in the uploaded PDF documents")


class PDFSearchTool(BaseTool):
    """Tool that allows an agent to search the ingested PDF documents."""
    name: str = "pdf_search"
    description: str = (
        "Search the uploaded PDF documents for information. "
        "Input should be a clear, specific search query. "
        "Returns excerpts from the documents that best match the query."
    )
    args_schema: type[BaseModel] = PDFSearchInput

    # We store the service instance here (ignored by Pydantic validation)
    query_service: Any = Field(exclude=True)

    def _run(self, query: str, run_manager: Any = None) -> str:
        """Execute the tool."""
        response = self.query_service.query(question=query)
        
        # If no documents are found, return a clear message
        if not response.sources:
            return "No relevant information was found in the documents."
            
        # Format the context block to feed back to the agent
        return f"Found the following information in documents:\n\n{response.answer}"
