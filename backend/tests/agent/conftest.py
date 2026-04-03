"""Setup mocks for agent module tests to avoid heavy dependencies."""

import sys
from unittest.mock import MagicMock

# Mock all heavy dependencies before any agent modules are imported
# This must happen at conftest load time, before test collection

_mocks = {
    # LangChain and LangGraph
    "langchain": MagicMock(),
    "langchain_core": MagicMock(),
    "langchain_core.tools": MagicMock(),
    "langchain_core.messages": MagicMock(),
    "langchain_community": MagicMock(),
    "langchain_ollama": MagicMock(),
    "langgraph": MagicMock(),
    "langgraph.prebuilt": MagicMock(),
    # LLM config
    "llm": MagicMock(),
    "llm.config": MagicMock(),
    "llm.ollama_client": MagicMock(),
    # FHIR and cache
    "cache": MagicMock(),
    "cache.fhir_cache": MagicMock(),
    "fhir_client": MagicMock(),
    "fhir_client.client": MagicMock(),
    # De-identification
    "deidentification": MagicMock(),
    # Agent (to prevent __init__.py from executing)
    "agent": MagicMock(),
}

# Create a mock @tool decorator that returns the function unchanged
def mock_tool(func):
    return func

_mocks["langchain_core.tools"].tool = mock_tool

for mod_name, mock in _mocks.items():
    if mod_name not in sys.modules:
        sys.modules[mod_name] = mock
