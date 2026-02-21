import { memo } from "react";
import { FileTextIcon } from "lucide-react";
import { cn } from "@/lib/utils";
import type { MentionItem as MentionItemType } from "./mention-types";

// ============================================================================
// MentionItem
// ============================================================================

export interface MentionItemProps {
    item: MentionItemType;
    isActive: boolean;
    index: number;
    onSelect: (item: MentionItemType) => void;
    onMouseEnter: (index: number) => void;
}

/**
 * MentionItem — a single row in the MentionDropdown.
 *
 * Wrapped in React.memo to avoid re-rendering siblings when activeIndex changes.
 */
export const MentionItem = memo(function MentionItem({
    item,
    isActive,
    index,
    onSelect,
    onMouseEnter,
}: MentionItemProps) {
    return (
        <div
            id={`mention-item-${index}`}
            role="option"
            aria-selected={isActive}
            data-active={isActive}
            className={cn(
                "flex items-center gap-2.5 px-2.5 py-2 cursor-pointer rounded-md",
                "text-sm text-foreground transition-colors",
                "select-none",
                isActive
                    ? "bg-accent text-accent-foreground"
                    : "hover:bg-accent/60 hover:text-accent-foreground"
            )}
            onMouseDown={(e) => {
                // Prevent textarea blur before we can select
                e.preventDefault();
            }}
            onClick={() => onSelect(item)}
            onMouseEnter={() => onMouseEnter(index)}
        >
            <FileTextIcon className="size-3.5 shrink-0 text-muted-foreground" />
            <span className="truncate flex-1 font-medium">{item.label}</span>
        </div>
    );
});
