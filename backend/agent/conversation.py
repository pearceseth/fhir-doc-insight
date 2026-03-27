"""Conversation history management for multi-turn interactions."""

import logging
from dataclasses import dataclass, field
from datetime import datetime
from typing import Literal

logger = logging.getLogger(__name__)

MessageRole = Literal["user", "assistant", "system"]


@dataclass
class Message:
    """A single message in a conversation."""

    role: MessageRole
    content: str
    timestamp: datetime = field(default_factory=datetime.now)

    def to_dict(self) -> dict:
        return {
            "role": self.role,
            "content": self.content,
            "timestamp": self.timestamp.isoformat(),
        }

    def to_langchain(self) -> dict:
        """Convert to LangChain message format."""
        return {"role": self.role, "content": self.content}


class ConversationStore:
    """
    In-memory conversation history storage.
    Maintains per-session conversation history.
    """

    def __init__(self, max_messages: int = 20):
        self._conversations: dict[str, list[Message]] = {}
        self._max_messages = max_messages

    async def get_conversation(self, conversation_id: str) -> list[Message]:
        """Get all messages for a conversation."""
        return self._conversations.get(conversation_id, [])

    async def get_history_for_llm(self, conversation_id: str) -> list[dict]:
        """Get conversation history formatted for LLM."""
        messages = await self.get_conversation(conversation_id)
        return [msg.to_langchain() for msg in messages]

    async def append_message(
        self,
        conversation_id: str,
        role: MessageRole,
        content: str,
    ) -> Message:
        """Add a message to a conversation."""
        if conversation_id not in self._conversations:
            self._conversations[conversation_id] = []

        message = Message(role=role, content=content)
        self._conversations[conversation_id].append(message)

        # Trim to max messages to avoid context overflow
        if len(self._conversations[conversation_id]) > self._max_messages:
            self._conversations[conversation_id] = self._conversations[conversation_id][
                -self._max_messages:
            ]

        return message

    async def clear_conversation(self, conversation_id: str) -> None:
        """Clear a conversation's history."""
        if conversation_id in self._conversations:
            del self._conversations[conversation_id]

    async def list_conversations(self) -> list[str]:
        """List all active conversation IDs."""
        return list(self._conversations.keys())

    def get_conversation_summary(self, conversation_id: str) -> dict:
        """Get summary info about a conversation."""
        messages = self._conversations.get(conversation_id, [])
        return {
            "conversation_id": conversation_id,
            "message_count": len(messages),
            "last_message": messages[-1].to_dict() if messages else None,
        }


# Singleton instance
conversation_store = ConversationStore()
