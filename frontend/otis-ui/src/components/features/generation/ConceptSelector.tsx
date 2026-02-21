import { Button } from "@/components/ui/button";
import { ScrollArea } from "@/components/ui/scroll-area";
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from "@/components/ui/tooltip";
import type { Concept, Overview } from "@/api/agentApi";
import { cn } from "@/lib/utils";

interface ConceptSelectorProps {
  overviews: Overview[];
  selectedConcepts: Concept[];
  onSelectionChange: (concepts: Concept[]) => void;
  disabled?: boolean;
  className?: string;
}

/**
 * Interactive concept selection component for HITL
 * Displays concepts as toggle buttons (outline when unselected, default when selected)
 */
export function ConceptSelector({
  overviews,
  selectedConcepts,
  onSelectionChange,
  disabled = false,
  className,
}: ConceptSelectorProps) {
  // Helper to check if a concept is selected
  const isSelected = (concept: Concept): boolean => {
    return selectedConcepts.some(
      (c) => c.name === concept.name && c.summary === concept.summary,
    );
  };

  // Toggle concept selection
  const toggleConcept = (concept: Concept) => {
    if (disabled) return;

    if (isSelected(concept)) {
      // Remove from selection
      onSelectionChange(
        selectedConcepts.filter(
          (c) => !(c.name === concept.name && c.summary === concept.summary),
        ),
      );
    } else {
      // Add to selection
      onSelectionChange([...selectedConcepts, concept]);
    }
  };

  // Select all concepts
  const selectAll = () => {
    const allConcepts = overviews.flatMap((o) => o.concepts);
    onSelectionChange(allConcepts);
  };

  // Clear selection
  const clearSelection = () => {
    onSelectionChange([]);
  };

  const totalConcepts = overviews.reduce(
    (acc, o) => acc + o.concepts.length,
    0,
  );

  if (overviews.length === 0) {
    return null;
  }

  return (
    <div className={cn("space-y-4", className)}>
      {/* Header with selection controls */}
      <div className="flex items-center justify-between">
        <div className="text-sm text-muted-foreground">
          {selectedConcepts.length} of {totalConcepts} concepts selected
        </div>
        <div className="flex gap-2">
          <Button
            variant="ghost"
            size="sm"
            onClick={selectAll}
            disabled={disabled || selectedConcepts.length === totalConcepts}
          >
            Select All
          </Button>
          <Button
            variant="ghost"
            size="sm"
            onClick={clearSelection}
            disabled={disabled || selectedConcepts.length === 0}
          >
            Clear
          </Button>
        </div>
      </div>

      {/* Concepts grouped by document */}
      <ScrollArea className="max-h-[400px]">
        <div className="space-y-6 pr-4">
          {overviews.map((overview, idx) => (
            <div key={idx} className="space-y-3">
              {/* Document name */}
              <h4 className="text-sm font-semibold text-foreground border-b pb-1">
                {overview.doc_name}
              </h4>

              {/* Concept buttons */}
              <div className="flex flex-wrap gap-2">
                <TooltipProvider delayDuration={300}>
                  {overview.concepts.map((concept, conceptIdx) => {
                    const selected = isSelected(concept);
                    return (
                      <Tooltip key={conceptIdx}>
                        <TooltipTrigger asChild>
                          <Button
                            variant={selected ? "default" : "outline"}
                            size="sm"
                            onClick={() => toggleConcept(concept)}
                            disabled={disabled}
                            className={cn(
                              "transition-all",
                              selected && "ring-2 ring-primary/20",
                            )}
                          >
                            {concept.name}
                          </Button>
                        </TooltipTrigger>
                        <TooltipContent
                          side="bottom"
                          className="max-w-[300px] text-sm"
                        >
                          <p>{concept.summary}</p>
                        </TooltipContent>
                      </Tooltip>
                    );
                  })}
                </TooltipProvider>
              </div>
            </div>
          ))}
        </div>
      </ScrollArea>
    </div>
  );
}
