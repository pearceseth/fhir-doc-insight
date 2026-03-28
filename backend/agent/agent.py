"""LangGraph ReAct agent orchestrator for clinical documentation analysis."""

import json
import logging
from dataclasses import dataclass
from typing import AsyncGenerator, Callable

from langgraph.prebuilt import create_react_agent
from langchain_ollama import ChatOllama
from langchain_core.messages import HumanMessage, AIMessage

from llm.config import llm_config
from llm.ollama_client import get_ollama_client
from deidentification import DeidentificationPipeline
from .tools import get_all_tools
from .prompts import get_system_prompt
from .conversation import ConversationStore, conversation_store

logger = logging.getLogger(__name__)


@dataclass
class AgentEvent:
    """Event emitted during agent execution."""

    event_type: str  # "thought", "tool_call", "tool_result", "answer", "error", "done"
    data: dict

    def to_sse(self) -> str:
        """Format as Server-Sent Event."""
        return f"data: {json.dumps({'event': self.event_type, **self.data})}\n\n"


class ClinDocAgent:
    """
    LangGraph ReAct agent for clinical documentation queries.
    Streams reasoning steps and final answers via SSE.
    """

    def __init__(
        self,
        conversation_store: ConversationStore | None = None,
        deidentification_pipeline: DeidentificationPipeline | None = None,
    ):
        self.conversation_store = conversation_store or globals()["conversation_store"]
        self.deid = deidentification_pipeline or DeidentificationPipeline(enable_freetext=False)
        self._llm = None
        self._agent = None

    def _get_llm(self):
        """Lazy-load the Ollama Chat LLM."""
        if self._llm is None:
            self._llm = ChatOllama(
                base_url=llm_config.ollama_base_url,
                model=llm_config.ollama_model,
                temperature=llm_config.ollama_temperature,
            )
        return self._llm

    def _create_agent(self):
        """Create the ReAct agent with tools."""
        if self._agent is not None:
            return self._agent

        llm = self._get_llm()
        tools = get_all_tools()

        system_prompt = get_system_prompt()
        logger.info("=== SYSTEM PROMPT ===")
        logger.info(system_prompt)
        logger.info("=== END SYSTEM PROMPT ===")

        # Create the ReAct agent using langgraph
        self._agent = create_react_agent(
            llm,
            tools,
            prompt=system_prompt,
        )

        return self._agent

    async def query(
        self,
        user_query: str,
        conversation_id: str,
        on_step: Callable[[AgentEvent], None] | None = None,
    ) -> AsyncGenerator[AgentEvent, None]:
        """
        Process a user query and stream agent reasoning via events.

        Args:
            user_query: The user's question
            conversation_id: Session ID for conversation history
            on_step: Optional callback for each step

        Yields:
            AgentEvent objects for each step of the reasoning process
        """
        # Add user message to conversation
        await self.conversation_store.append_message(
            conversation_id, "user", user_query
        )

        # Get conversation history
        history = await self.conversation_store.get_history_for_llm(conversation_id)

        # Convert to LangChain message format
        messages = []
        for msg in history[:-1]:  # Exclude current message
            if msg["role"] == "user":
                messages.append(HumanMessage(content=msg["content"]))
            elif msg["role"] == "assistant":
                messages.append(AIMessage(content=msg["content"]))

        # Add current query
        messages.append(HumanMessage(content=user_query))

        logger.info("=== USER QUERY ===")
        logger.info(f"Query: {user_query}")
        logger.info(f"Conversation history: {len(messages) - 1} previous messages")
        logger.info("=== END USER QUERY ===")

        try:
            # Create agent
            agent = self._create_agent()

            # Stream events from agent
            step_count = 0
            final_answer = None

            async for event in agent.astream_events(
                {"messages": messages},
                version="v2",
            ):
                event_kind = event.get("event")
                event_data = event.get("data", {})

                # Handle different event types
                if event_kind == "on_chat_model_stream":
                    # Streaming token from LLM
                    chunk = event_data.get("chunk")
                    if chunk:
                        content = getattr(chunk, "content", "")
                        if content:
                            yield AgentEvent("thought", {"content": content, "step": step_count})

                elif event_kind == "on_tool_start":
                    # Tool being called
                    step_count += 1
                    tool_input = event_data.get("input", {})
                    agent_event = AgentEvent(
                        "tool_call",
                        {
                            "tool": event.get("name", "unknown"),
                            "args": tool_input,
                            "step": step_count,
                        },
                    )
                    yield agent_event
                    if on_step:
                        on_step(agent_event)

                elif event_kind == "on_tool_end":
                    # Tool returned result
                    output = event_data.get("output")
                    agent_event = AgentEvent(
                        "tool_result",
                        {
                            "tool": event.get("name", "unknown"),
                            "result": output if isinstance(output, (dict, list, str)) else str(output),
                            "step": step_count,
                        },
                    )
                    yield agent_event
                    if on_step:
                        on_step(agent_event)

                elif event_kind == "on_chain_end":
                    # Agent finished - extract final message
                    output = event_data.get("output", {})
                    if isinstance(output, dict) and "messages" in output:
                        msgs = output["messages"]
                        if msgs and hasattr(msgs[-1], "content"):
                            final_answer = msgs[-1].content

            # If we got a final answer, emit it
            if final_answer:
                await self.conversation_store.append_message(
                    conversation_id, "assistant", final_answer
                )
                yield AgentEvent("answer", {"content": final_answer})

            yield AgentEvent("done", {})

        except Exception as e:
            logger.error(f"Agent query failed: {e}", exc_info=True)
            error_msg = f"I encountered an error processing your question: {str(e)}"
            yield AgentEvent("error", {"message": error_msg})
            yield AgentEvent("done", {})

    async def simple_query(self, user_query: str, conversation_id: str) -> str:
        """
        Non-streaming version that returns the final answer.
        """
        final_answer = ""
        async for event in self.query(user_query, conversation_id):
            if event.event_type == "answer":
                final_answer = event.data.get("content", "")
            elif event.event_type == "error":
                return event.data.get("message", "An error occurred")
        return final_answer

    async def check_health(self) -> dict:
        """Check if the agent is ready (Ollama available, etc.)."""
        try:
            client = get_ollama_client()
            is_healthy = await client.check_health()
            if is_healthy:
                return {
                    "status": "healthy",
                    "model": llm_config.ollama_model,
                    "base_url": llm_config.ollama_base_url,
                }
            else:
                return {
                    "status": "unhealthy",
                    "error": f"Model '{llm_config.ollama_model}' not available",
                    "model": llm_config.ollama_model,
                    "base_url": llm_config.ollama_base_url,
                }
        except Exception as e:
            return {
                "status": "unhealthy",
                "error": str(e),
                "model": llm_config.ollama_model,
                "base_url": llm_config.ollama_base_url,
            }


# Singleton instance
clindoc_agent = ClinDocAgent()
