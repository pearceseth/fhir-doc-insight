import { useEffect, useRef, useState } from "react";
import { AlertCircle, Trash2, RefreshCw } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { QueryInput } from "@/components/assistant/QueryInput";
import { ResponseCard } from "@/components/assistant/ResponseCard";
import { SuggestedQueries } from "@/components/assistant/SuggestedQueries";
import { useAssistant } from "@/hooks/useAssistant";
import { checkAssistantHealth, type AssistantHealthResponse } from "@/api/assistant";

export function Assistant() {
  const {
    messages,
    isLoading,
    error,
    sendMessage,
    clearChat,
    stopStreaming,
  } = useAssistant();

  const [health, setHealth] = useState<AssistantHealthResponse | null>(null);
  const [healthLoading, setHealthLoading] = useState(true);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  // Check assistant health on mount
  useEffect(() => {
    async function checkHealth() {
      setHealthLoading(true);
      try {
        const result = await checkAssistantHealth();
        setHealth(result);
      } catch {
        setHealth({ status: "unhealthy", error: "Failed to connect to assistant" });
      } finally {
        setHealthLoading(false);
      }
    }
    checkHealth();
  }, []);

  // Auto-scroll to bottom when messages change
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  const isHealthy = health?.status === "healthy";

  return (
    <div className="container mx-auto h-full flex flex-col max-w-4xl py-6 px-4">
      <div className="flex items-center justify-between mb-4">
        <div>
          <h1 className="text-2xl font-bold">Clinical Documentation Assistant</h1>
          <p className="text-sm text-muted-foreground mt-1">
            Ask questions about documentation patterns and completeness
          </p>
        </div>
        {messages.length > 0 && (
          <Button
            variant="outline"
            size="sm"
            onClick={clearChat}
            className="gap-2"
          >
            <Trash2 className="h-4 w-4" />
            Clear
          </Button>
        )}
      </div>

      {/* Health Status Banner */}
      {!healthLoading && !isHealthy && (
        <Card className="mb-4 border-destructive/50 bg-destructive/10">
          <CardContent className="flex items-center gap-3 py-3">
            <AlertCircle className="h-5 w-5 text-destructive" />
            <div className="flex-1">
              <p className="text-sm font-medium text-destructive">
                Assistant Unavailable
              </p>
              <p className="text-xs text-muted-foreground">
                {health?.error || "The LLM service is not responding. Make sure Ollama is running."}
              </p>
            </div>
            <Button
              variant="outline"
              size="sm"
              onClick={() => window.location.reload()}
              className="gap-2"
            >
              <RefreshCw className="h-4 w-4" />
              Retry
            </Button>
          </CardContent>
        </Card>
      )}

      {/* Chat Messages Area */}
      <Card className="flex-1 flex flex-col min-h-0">
        <CardContent className="flex-1 overflow-y-auto p-4 space-y-4">
          {messages.length === 0 ? (
            <div className="h-full flex flex-col items-center justify-center text-center">
              <div className="max-w-md space-y-6">
                <div>
                  <h2 className="text-lg font-medium mb-2">
                    Welcome to the Clinical Documentation Assistant
                  </h2>
                  <p className="text-sm text-muted-foreground">
                    I can help you analyze documentation patterns, identify gaps,
                    and answer questions about your clinical data. All data is
                    de-identified before analysis.
                  </p>
                </div>
                <SuggestedQueries onSelect={sendMessage} />
              </div>
            </div>
          ) : (
            <>
              {messages.map((message) => (
                <ResponseCard key={message.id} message={message} />
              ))}
              <div ref={messagesEndRef} />
            </>
          )}
        </CardContent>

        {/* Error Display */}
        {error && (
          <div className="px-4 pb-2">
            <div className="flex items-center gap-2 text-sm text-destructive bg-destructive/10 rounded-lg p-2">
              <AlertCircle className="h-4 w-4" />
              {error}
            </div>
          </div>
        )}

        {/* Input Area */}
        <div className="p-4 border-t">
          <QueryInput
            onSubmit={sendMessage}
            onStop={stopStreaming}
            isLoading={isLoading}
            placeholder={
              isHealthy
                ? "Ask a question about your clinical data..."
                : "Assistant unavailable - check Ollama status"
            }
          />
          {health && (
            <p className="text-xs text-muted-foreground mt-2 text-center">
              Powered by {health.model || "Ollama"} - All data is de-identified
            </p>
          )}
        </div>
      </Card>
    </div>
  );
}
