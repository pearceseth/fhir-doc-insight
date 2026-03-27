import { Lightbulb } from "lucide-react";
import { Button } from "@/components/ui/button";

interface SuggestedQueriesProps {
  onSelect: (query: string) => void;
}

const SUGGESTED_QUERIES = [
  "What percentage of finished encounters have clinical notes?",
  "Which encounters are missing vital signs documentation?",
  "Show me the medication reconciliation status for recent encounters",
  "How many encounters from the last week have complete documentation?",
];

export function SuggestedQueries({ onSelect }: SuggestedQueriesProps) {
  return (
    <div className="space-y-3">
      <div className="flex items-center gap-2 text-sm text-muted-foreground">
        <Lightbulb className="h-4 w-4" />
        <span>Try asking:</span>
      </div>
      <div className="flex flex-wrap gap-2">
        {SUGGESTED_QUERIES.map((query, index) => (
          <Button
            key={index}
            variant="outline"
            size="sm"
            onClick={() => onSelect(query)}
            className="text-left h-auto py-2 px-3 whitespace-normal"
          >
            {query}
          </Button>
        ))}
      </div>
    </div>
  );
}
