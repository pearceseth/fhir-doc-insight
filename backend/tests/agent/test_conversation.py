"""Tests for agent/conversation.py

Mocks for heavy dependencies (langchain, llm, etc.) are set up in conftest.py.
"""

import importlib.util
import sys
from pathlib import Path

import pytest

# Import the actual conversation module after mocks are set up by conftest.py
# We use importlib to load it fresh with our mocks in place
_conv_path = Path(__file__).parent.parent.parent / "agent" / "conversation.py"
_spec = importlib.util.spec_from_file_location("agent.conversation_test", _conv_path)
_agent_conv = importlib.util.module_from_spec(_spec)
sys.modules["agent.conversation_test"] = _agent_conv
_spec.loader.exec_module(_agent_conv)

ConversationStore = _agent_conv.ConversationStore
Message = _agent_conv.Message


class TestMessage:
    """Tests for Message dataclass."""

    def test_to_dict_includes_all_fields(self):
        """to_dict should include role, content, and timestamp."""
        message = Message(role="user", content="Hello")
        result = message.to_dict()

        assert result["role"] == "user"
        assert result["content"] == "Hello"
        assert "timestamp" in result

    def test_to_langchain_returns_role_and_content(self):
        """to_langchain should return only role and content."""
        message = Message(role="assistant", content="Hi there")
        result = message.to_langchain()

        assert result == {"role": "assistant", "content": "Hi there"}
        assert "timestamp" not in result


class TestConversationStore:
    """Tests for ConversationStore class."""

    @pytest.fixture
    def store(self):
        """Create a fresh ConversationStore for each test."""
        return ConversationStore(max_messages=20)

    async def test_get_conversation_returns_empty_for_new_id(self, store):
        """get_conversation should return empty list for unknown conversation."""
        result = await store.get_conversation("new-id")
        assert result == []

    async def test_append_message_creates_conversation(self, store):
        """append_message should create conversation if it doesn't exist."""
        message = await store.append_message("conv-1", "user", "Hello")

        assert message.role == "user"
        assert message.content == "Hello"

        messages = await store.get_conversation("conv-1")
        assert len(messages) == 1

    async def test_append_message_adds_to_existing_conversation(self, store):
        """append_message should add to existing conversation."""
        await store.append_message("conv-1", "user", "Hello")
        await store.append_message("conv-1", "assistant", "Hi there")

        messages = await store.get_conversation("conv-1")
        assert len(messages) == 2
        assert messages[0].role == "user"
        assert messages[1].role == "assistant"

    async def test_fifo_trimming_at_max_messages(self):
        """Messages should be trimmed FIFO when exceeding max_messages."""
        store = ConversationStore(max_messages=3)

        await store.append_message("conv-1", "user", "Message 1")
        await store.append_message("conv-1", "assistant", "Message 2")
        await store.append_message("conv-1", "user", "Message 3")
        await store.append_message("conv-1", "assistant", "Message 4")

        messages = await store.get_conversation("conv-1")
        assert len(messages) == 3
        # First message should have been trimmed
        assert messages[0].content == "Message 2"
        assert messages[2].content == "Message 4"

    async def test_get_history_for_llm_returns_langchain_format(self, store):
        """get_history_for_llm should return LangChain formatted messages."""
        await store.append_message("conv-1", "user", "Hello")
        await store.append_message("conv-1", "assistant", "Hi")

        history = await store.get_history_for_llm("conv-1")

        assert history == [
            {"role": "user", "content": "Hello"},
            {"role": "assistant", "content": "Hi"},
        ]

    async def test_get_history_for_llm_empty_conversation(self, store):
        """get_history_for_llm should return empty list for new conversation."""
        history = await store.get_history_for_llm("nonexistent")
        assert history == []

    async def test_clear_conversation_removes_messages(self, store):
        """clear_conversation should remove all messages."""
        await store.append_message("conv-1", "user", "Hello")
        await store.append_message("conv-1", "assistant", "Hi")

        await store.clear_conversation("conv-1")

        messages = await store.get_conversation("conv-1")
        assert messages == []

    async def test_clear_nonexistent_conversation_no_error(self, store):
        """clear_conversation should not error for nonexistent conversation."""
        # Should not raise
        await store.clear_conversation("nonexistent")

    async def test_conversation_isolation(self, store):
        """Different conversation IDs should be independent."""
        await store.append_message("conv-1", "user", "Hello from conv 1")
        await store.append_message("conv-2", "user", "Hello from conv 2")

        messages_1 = await store.get_conversation("conv-1")
        messages_2 = await store.get_conversation("conv-2")

        assert len(messages_1) == 1
        assert len(messages_2) == 1
        assert messages_1[0].content == "Hello from conv 1"
        assert messages_2[0].content == "Hello from conv 2"

    async def test_list_conversations_returns_all_ids(self, store):
        """list_conversations should return all active conversation IDs."""
        await store.append_message("conv-1", "user", "Hello")
        await store.append_message("conv-2", "user", "Hello")
        await store.append_message("conv-3", "user", "Hello")

        conversations = await store.list_conversations()

        assert set(conversations) == {"conv-1", "conv-2", "conv-3"}

    async def test_list_conversations_empty_when_no_conversations(self, store):
        """list_conversations should return empty list when no conversations."""
        conversations = await store.list_conversations()
        assert conversations == []

    def test_get_conversation_summary(self, store):
        """get_conversation_summary should return summary info."""
        # Need to use sync internals since this is a sync method
        store._conversations["conv-1"] = [
            Message(role="user", content="Hello"),
            Message(role="assistant", content="Hi"),
        ]

        summary = store.get_conversation_summary("conv-1")

        assert summary["conversation_id"] == "conv-1"
        assert summary["message_count"] == 2
        assert summary["last_message"]["content"] == "Hi"

    def test_get_conversation_summary_empty(self, store):
        """get_conversation_summary should handle empty conversation."""
        summary = store.get_conversation_summary("nonexistent")

        assert summary["conversation_id"] == "nonexistent"
        assert summary["message_count"] == 0
        assert summary["last_message"] is None

    async def test_append_returns_message_object(self, store):
        """append_message should return the created Message object."""
        message = await store.append_message("conv-1", "system", "System message")

        assert isinstance(message, Message)
        assert message.role == "system"
        assert message.content == "System message"
        assert message.timestamp is not None
