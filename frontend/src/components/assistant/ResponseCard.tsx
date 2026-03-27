import { User, Bot, Loader2 } from "lucide-react";
import { cn } from "@/lib/utils";
import { ReasoningSteps } from "./ReasoningSteps";
import type { ChatMessage } from "@/hooks/useAssistant";

interface ResponseCardProps {
  message: ChatMessage;
}

export function ResponseCard({ message }: ResponseCardProps) {
  const isUser = message.role === "user";

  return (
    <div
      className={cn(
        "flex gap-3",
        isUser ? "flex-row-reverse" : "flex-row"
      )}
    >
      <div
        className={cn(
          "flex h-8 w-8 shrink-0 items-center justify-center rounded-full",
          isUser ? "bg-primary" : "bg-muted"
        )}
      >
        {isUser ? (
          <User className="h-4 w-4 text-primary-foreground" />
        ) : (
          <Bot className="h-4 w-4 text-muted-foreground" />
        )}
      </div>

      <div
        className={cn(
          "flex max-w-[80%] flex-col gap-1 rounded-lg px-4 py-2",
          isUser ? "bg-primary text-primary-foreground" : "bg-muted"
        )}
      >
        <div className="text-sm whitespace-pre-wrap">
          {message.content || (message.isStreaming && (
            <span className="flex items-center gap-2 text-muted-foreground">
              <Loader2 className="h-3 w-3 animate-spin" />
              Thinking...
            </span>
          ))}
        </div>

        {!isUser && message.reasoningSteps && message.reasoningSteps.length > 0 && (
          <ReasoningSteps steps={message.reasoningSteps} />
        )}

        {message.isStreaming && message.content && (
          <span className="inline-block h-2 w-1 animate-pulse bg-current" />
        )}
      </div>
    </div>
  );
}
