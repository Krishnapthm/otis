import type {
  ComponentProps,
  KeyboardEventHandler,
  MouseEventHandler,
} from "react";
import { toast } from "sonner";
import { Badge } from "@/components/ui/badge";
import { cn } from "@/lib/utils";

export type MentionChipProps = Omit<ComponentProps<"span">, "children"> & {
  label: string;
  variant?: "input" | "chat";
  removable?: boolean;
  onRemove?: () => void;
  includeHiddenTriggerChar?: boolean;
};

export const MentionChip = ({
  label,
  variant = "input",
  removable = false,
  onRemove,
  includeHiddenTriggerChar = false,
  className,
  onClick,
  onKeyDown,
  ...props
}: MentionChipProps) => {
  const handleClick: MouseEventHandler<HTMLSpanElement> = (event) => {
    // TODO: Replace this toast interaction with opening the PDF viewer.
    toast.info(`Open document: ${label}`);
    onClick?.(event);
  };

  const handleRemove: MouseEventHandler<HTMLButtonElement> = (event) => {
    event.preventDefault();
    event.stopPropagation();
    onRemove?.();
  };

  const handleKeyDown: KeyboardEventHandler<HTMLSpanElement> = (event) => {
    if (event.key === "Enter" || event.key === " ") {
      event.preventDefault();
      // TODO: Replace this toast interaction with opening the PDF viewer.
      toast.info(`Open document: ${label}`);
      return;
    }
    onKeyDown?.(event);
  };

  const variantClassName =
    variant === "chat"
      ? "border-transparent bg-primary-foreground/10 text-primary-foreground"
      : "border-transparent bg-primary/10 text-primary";

  return (
    <Badge
      className={cn(
        "group relative rounded-sm px-1.5 py-0.5 text-xs",
        "transition-colors",
        variantClassName,
        className,
      )}
      variant="secondary"
    >
      <span
        aria-label={`Referenced document ${label}`}
        className="relative inline-flex items-center"
        onClick={handleClick}
        onKeyDown={handleKeyDown}
        role="button"
        tabIndex={0}
        {...props}
      >
        {includeHiddenTriggerChar && <span className="sr-only">@</span>}
        <span>{label}</span>
        {/* {removable && (
          <button
            aria-label={`Remove ${label}`}
            className="absolute top-1/2 right-0 inline-flex size-3 -translate-y-1/2 items-center justify-center rounded-full bg-background/70 text-[10px] leading-none"
            onClick={handleRemove}
            tabIndex={-1}
            type="button"
          >
            ×
          </button>
        )} */}
      </span>
    </Badge>
  );
};
