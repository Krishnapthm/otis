import { Check, X } from "lucide-react";
import { cn } from "@/lib/utils";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";

export interface ValidationRule {
  id: string;
  label: string;
  isValid: boolean;
}

interface ValidationChecklistProps {
  title?: string;
  rules: ValidationRule[];
  className?: string;
  showOnlyWhenActive?: boolean;
}

function ValidationBadge({ isValid }: { isValid: boolean }) {
  return (
    <span
      className={cn(
        "inline-flex items-center justify-center size-3.5 rounded-full shrink-0 transition-colors duration-200",
        isValid
          ? "bg-green-500/10 text-green-500"
          : "bg-red-500/10 text-red-500",
      )}
    >
      {isValid ? (
        <Check className="size-3" strokeWidth={2} />
      ) : (
        <X className="size-3" strokeWidth={2} />
      )}
    </span>
  );
}

function ValidationChecklist({
  title,
  rules,
  className,
}: ValidationChecklistProps) {
  const hasAnyInvalid = rules.some((rule) => !rule.isValid);

  return (
    <Card
      className={cn(
        "transition-colors duration-200",
        hasAnyInvalid
          ? "border-destructive/50 bg-destructive/2"
          : "border-green-500 bg-green-500/2",
        className,
      )}
    >
      {title && (
        <CardHeader className="px-4 pb-1 pt-3">
          <CardTitle className=" font-medium text-muted-foreground">
            {title}
          </CardTitle>
        </CardHeader>
      )}
      <CardContent className={cn("px-4 ", !title && "")}>
        <div className="flex flex-col gap-2">
          {rules.map((rule) => (
            <div
              key={rule.id}
              className={cn(
                "flex items-center gap-2 text-sm leading-none transition-colors duration-200",
                rule.isValid ? "text-foreground" : "text-muted-foreground",
              )}
            >
              <ValidationBadge isValid={rule.isValid} />
              <span className="leading-none">{rule.label}</span>
            </div>
          ))}
        </div>
      </CardContent>
    </Card>
  );
}

export { ValidationChecklist, ValidationBadge };
