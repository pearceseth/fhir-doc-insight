import { useState, useCallback, useRef } from "react";
import {
  streamQuery,
  type AssistantEvent,
  type Message,
} from "@/api/assistant";

export interface ReasoningStep {
  type: "thought" | "tool_call" | "tool_result";
  content: string;
  step: number;
  tool?: string;
  args?: Record<string, unknown>;
  result?: unknown;
}

export interface ChatMessage {
  id: string;
  role: "user" | "assistant";
  content: string;
  timestamp: Date;
  reasoningSteps?: ReasoningStep[];
  isStreaming?: boolean;
}

export function useAssistant() {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [conversationId, setConversationId] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  const abortControllerRef = useRef<AbortController | null>(null);

  const sendMessage = useCallback(
    async (query: string) => {
      if (!query.trim() || isLoading) return;

      setError(null);
      setIsLoading(true);

      // Add user message
      const userMessage: ChatMessage = {
        id: `user-${Date.now()}`,
        role: "user",
        content: query,
        timestamp: new Date(),
      };

      // Create placeholder for assistant response
      const assistantMessageId = `assistant-${Date.now()}`;
      const assistantMessage: ChatMessage = {
        id: assistantMessageId,
        role: "assistant",
        content: "",
        timestamp: new Date(),
        reasoningSteps: [],
        isStreaming: true,
      };

      setMessages((prev) => [...prev, userMessage, assistantMessage]);

      try {
        let currentContent = "";
        const reasoningSteps: ReasoningStep[] = [];

        for await (const event of streamQuery(query, conversationId || undefined)) {
          // Capture conversation ID from first event
          if ("conversation_id" in event && event.conversation_id) {
            setConversationId(event.conversation_id as string);
          }

          switch (event.event) {
            case "thought":
              if (event.content) {
                currentContent += event.content;
                setMessages((prev) =>
                  prev.map((msg) =>
                    msg.id === assistantMessageId
                      ? { ...msg, content: currentContent }
                      : msg
                  )
                );
              }
              break;

            case "tool_call":
              reasoningSteps.push({
                type: "tool_call",
                content: `Calling ${event.tool}`,
                step: event.step || reasoningSteps.length + 1,
                tool: event.tool,
                args: event.args,
              });
              setMessages((prev) =>
                prev.map((msg) =>
                  msg.id === assistantMessageId
                    ? { ...msg, reasoningSteps: [...reasoningSteps] }
                    : msg
                )
              );
              break;

            case "tool_result":
              reasoningSteps.push({
                type: "tool_result",
                content: `Result from ${event.tool}`,
                step: event.step || reasoningSteps.length + 1,
                tool: event.tool,
                result: event.result,
              });
              setMessages((prev) =>
                prev.map((msg) =>
                  msg.id === assistantMessageId
                    ? { ...msg, reasoningSteps: [...reasoningSteps] }
                    : msg
                )
              );
              break;

            case "answer":
              if (event.content) {
                currentContent = event.content;
                setMessages((prev) =>
                  prev.map((msg) =>
                    msg.id === assistantMessageId
                      ? { ...msg, content: currentContent }
                      : msg
                  )
                );
              }
              break;

            case "error":
              setError(event.message || "An error occurred");
              break;

            case "done":
              setMessages((prev) =>
                prev.map((msg) =>
                  msg.id === assistantMessageId
                    ? { ...msg, isStreaming: false }
                    : msg
                )
              );
              break;
          }
        }
      } catch (err) {
        setError(err instanceof Error ? err.message : "Failed to send message");
        // Remove the streaming message on error
        setMessages((prev) =>
          prev.filter((msg) => msg.id !== assistantMessageId)
        );
      } finally {
        setIsLoading(false);
      }
    },
    [conversationId, isLoading]
  );

  const clearChat = useCallback(() => {
    setMessages([]);
    setConversationId(null);
    setError(null);
  }, []);

  const stopStreaming = useCallback(() => {
    if (abortControllerRef.current) {
      abortControllerRef.current.abort();
      abortControllerRef.current = null;
    }
    setIsLoading(false);
  }, []);

  return {
    messages,
    isLoading,
    error,
    conversationId,
    sendMessage,
    clearChat,
    stopStreaming,
  };
}
