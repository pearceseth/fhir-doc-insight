/**
 * Assistant API client with SSE streaming support.
 */

export interface AssistantEvent {
  event: "thought" | "tool_call" | "tool_result" | "answer" | "error" | "done";
  content?: string;
  step?: number;
  tool?: string;
  args?: Record<string, unknown>;
  result?: unknown;
  message?: string;
}

export interface Message {
  role: "user" | "assistant" | "system";
  content: string;
  timestamp: string;
}

export interface ConversationResponse {
  conversation_id: string;
  messages: Message[];
  count: number;
}

export interface AssistantHealthResponse {
  status: "healthy" | "unhealthy";
  model?: string;
  base_url?: string;
  error?: string;
}

/**
 * Stream a query to the assistant and yield events as they arrive.
 */
export async function* streamQuery(
  query: string,
  conversationId?: string
): AsyncGenerator<AssistantEvent> {
  const response = await fetch("/api/assistant/query", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      query,
      conversation_id: conversationId,
    }),
  });

  if (!response.ok) {
    yield {
      event: "error",
      message: `Request failed: ${response.statusText}`,
    };
    yield { event: "done" };
    return;
  }

  // Extract conversation ID from response headers
  const newConversationId = response.headers.get("X-Conversation-Id");

  const reader = response.body?.getReader();
  if (!reader) {
    yield { event: "error", message: "No response body" };
    yield { event: "done" };
    return;
  }

  const decoder = new TextDecoder();
  let buffer = "";

  while (true) {
    const { done, value } = await reader.read();
    if (done) break;

    buffer += decoder.decode(value, { stream: true });
    const lines = buffer.split("\n");

    // Keep the last partial line in the buffer
    buffer = lines.pop() || "";

    for (const line of lines) {
      if (line.startsWith("data: ")) {
        try {
          const data = JSON.parse(line.slice(6));
          // Include conversation ID in first event
          if (newConversationId && !data.conversation_id) {
            data.conversation_id = newConversationId;
          }
          yield data as AssistantEvent;
        } catch {
          // Skip invalid JSON lines
        }
      }
    }
  }

  // Process any remaining data in buffer
  if (buffer.startsWith("data: ")) {
    try {
      yield JSON.parse(buffer.slice(6)) as AssistantEvent;
    } catch {
      // Skip invalid JSON
    }
  }
}

/**
 * Get conversation history.
 */
export async function fetchConversation(
  conversationId: string
): Promise<ConversationResponse> {
  const response = await fetch(
    `/api/assistant/conversations/${conversationId}`
  );
  if (!response.ok) {
    throw new Error(`Failed to fetch conversation: ${response.statusText}`);
  }
  return response.json();
}

/**
 * Clear conversation history.
 */
export async function clearConversation(
  conversationId: string
): Promise<void> {
  const response = await fetch(
    `/api/assistant/conversations/${conversationId}`,
    { method: "DELETE" }
  );
  if (!response.ok) {
    throw new Error(`Failed to clear conversation: ${response.statusText}`);
  }
}

/**
 * Check assistant health.
 */
export async function checkAssistantHealth(): Promise<AssistantHealthResponse> {
  const response = await fetch("/api/assistant/health");
  return response.json();
}
