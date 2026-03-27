import { useState } from "react";
import { ChevronDown, ChevronRight, Wrench, CheckCircle } from "lucide-react";
import { cn } from "@/lib/utils";
import type { ReasoningStep } from "@/hooks/useAssistant";

interface ReasoningStepsProps {
  steps: ReasoningStep[];
  defaultExpanded?: boolean;
}

export function ReasoningSteps({
  steps,
  defaultExpanded = false,
}: ReasoningStepsProps) {
  const [isExpanded, setIsExpanded] = useState(defaultExpanded);

  if (steps.length === 0) {
    return null;
  }

  // Group tool calls with their results
  const groupedSteps: Array<{
    call: ReasoningStep;
    result?: ReasoningStep;
  }> = [];

  for (const step of steps) {
    if (step.type === "tool_call") {
      groupedSteps.push({ call: step });
    } else if (step.type === "tool_result" && groupedSteps.length > 0) {
      const lastGroup = groupedSteps[groupedSteps.length - 1];
      if (!lastGroup.result) {
        lastGroup.result = step;
      }
    }
  }

  return (
    <div className="mt-2">
      <button
        onClick={() => setIsExpanded(!isExpanded)}
        className="flex items-center gap-1 text-xs text-muted-foreground hover:text-foreground transition-colors"
      >
        {isExpanded ? (
          <ChevronDown className="h-3 w-3" />
        ) : (
          <ChevronRight className="h-3 w-3" />
        )}
        View reasoning ({groupedSteps.length} steps)
      </button>

      {isExpanded && (
        <div className="mt-2 space-y-2 pl-4 border-l-2 border-muted">
          {groupedSteps.map((group, index) => (
            <div key={index} className="text-xs">
              <div className="flex items-start gap-2">
                <Wrench className="h-3 w-3 mt-0.5 text-muted-foreground shrink-0" />
                <div>
                  <span className="font-medium">{group.call.tool}</span>
                  {group.call.args && (
                    <pre className="mt-1 p-2 bg-muted rounded text-xs overflow-x-auto">
                      {JSON.stringify(group.call.args, null, 2)}
                    </pre>
                  )}
                </div>
              </div>

              {group.result && (
                <div className="flex items-start gap-2 mt-1 ml-4">
                  <CheckCircle className="h-3 w-3 mt-0.5 text-green-500 shrink-0" />
                  <div className="text-muted-foreground">
                    {typeof group.result.result === "object" ? (
                      <details>
                        <summary className="cursor-pointer hover:text-foreground">
                          Result received
                        </summary>
                        <pre className="mt-1 p-2 bg-muted rounded text-xs overflow-x-auto max-h-40">
                          {JSON.stringify(group.result.result, null, 2)}
                        </pre>
                      </details>
                    ) : (
                      <span>Result: {String(group.result.result)}</span>
                    )}
                  </div>
                </div>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
