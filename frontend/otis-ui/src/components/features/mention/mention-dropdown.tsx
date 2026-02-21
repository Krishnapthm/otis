import { useCallback, useEffect, useRef } from "react";
import { createPortal } from "react-dom";
import { Loader2Icon, AlertCircleIcon } from "lucide-react";
import { cn } from "@/lib/utils";
import { useMentionPickerContext } from "./mention-picker";
import { MentionItem } from "./mention-item";
import type { MentionItem as MentionItemType } from "./mention-types";

// ============================================================================
// MentionDropdown
// ============================================================================

export interface MentionDropdownProps {
    /** Maximum visible items before scroll kicks in. Default 6. */
    maxVisibleItems?: number;
    className?: string;
}

/**
 * MentionDropdown — portal-based floating panel that renders ABOVE the
 * textarea. Position is computed from the textarea's bounding rect so it
 * always sits directly above the input, left-aligned with the caret x.
 */
export function MentionDropdown({
    maxVisibleItems = 6,
    className,
}: MentionDropdownProps) {
    const {
        isOpen,
        filteredItems,
        activeIndex,
        caretCoords,
        selectItem,
        setActiveIndex,
        closeDropdown,
        activeTrigger,
        status,
        textareaRef,
    } = useMentionPickerContext();

    const dropdownRef = useRef<HTMLDivElement | null>(null);

    // Auto-scroll to active item
    useEffect(() => {
        if (!isOpen) return;
        const el = dropdownRef.current?.querySelector(
            `[id="mention-item-${activeIndex}"]`
        ) as HTMLElement | null;
        el?.scrollIntoView({ block: "nearest" });
    }, [activeIndex, isOpen]);

    // Close on outside click
    useEffect(() => {
        if (!isOpen) return;

        const handlePointerDown = (e: PointerEvent) => {
            const target = e.target as Node;
            if (
                !dropdownRef.current?.contains(target) &&
                !textareaRef.current?.contains(target)
            ) {
                closeDropdown();
            }
        };

        document.addEventListener("pointerdown", handlePointerDown);
        return () => document.removeEventListener("pointerdown", handlePointerDown);
    }, [isOpen, closeDropdown, textareaRef]);

    const handleSelect = useCallback(
        (item: MentionItemType) => selectItem(item),
        [selectItem]
    );

    const handleMouseEnter = useCallback(
        (index: number) => setActiveIndex(index),
        [setActiveIndex]
    );

    if (!isOpen || !caretCoords) return null;

    const textarea = textareaRef.current;
    if (!textarea) return null;

    // Position: always above the textarea, left-aligned with the caret x
    const textareaRect = textarea.getBoundingClientRect();
    const DROPDOWN_GAP = 8;
    const ITEM_HEIGHT = 36;
    const MAX_HEIGHT = maxVisibleItems * ITEM_HEIGHT + 16;
    const dropdownHeight = Math.min(
        MAX_HEIGHT,
        (filteredItems.length || 1) * ITEM_HEIGHT + 16
    );

    const top = textareaRect.top - dropdownHeight - DROPDOWN_GAP;
    const left = Math.max(8, caretCoords.x); // clamp to viewport edge

    const dropdown = (
        <div
            ref={dropdownRef}
            role="listbox"
            aria-label={
                activeTrigger
                    ? `${activeTrigger.config.type} suggestions`
                    : "Suggestions"
            }
            style={{
                position: "fixed",
                top: Math.max(8, top), // don't go above viewport
                left,
                zIndex: 9999,
                maxHeight: MAX_HEIGHT,
                minWidth: "200px",
                maxWidth: "320px",
            }}
            className={cn(
                "overflow-y-auto rounded-lg border border-border bg-popover shadow-xl",
                "p-1.5",
                "animate-in fade-in-0 zoom-in-95 duration-100",
                className
            )}
        >
            {status === "loading" && <DropdownLoading />}
            {status === "error" && <DropdownError />}
            {status !== "loading" &&
                status !== "error" &&
                filteredItems.length === 0 && (
                    <DropdownEmpty query={activeTrigger?.query ?? ""} />
                )}
            {status !== "loading" &&
                status !== "error" &&
                filteredItems.map((item, index) => (
                    <MentionItem
                        key={item.id}
                        item={item}
                        isActive={index === activeIndex}
                        index={index}
                        onSelect={handleSelect}
                        onMouseEnter={handleMouseEnter}
                    />
                ))}
        </div>
    );

    return createPortal(dropdown, document.body);
}

// ---------------------------------------------------------------------------
// Async State Sub-components
// ---------------------------------------------------------------------------

function DropdownLoading() {
    return (
        <div className="flex items-center gap-2 px-2.5 py-3 text-sm text-muted-foreground">
            <Loader2Icon className="size-3.5 animate-spin" />
            <span>Loading…</span>
        </div>
    );
}

function DropdownError() {
    return (
        <div className="flex items-center gap-2 px-2.5 py-3 text-sm text-destructive">
            <AlertCircleIcon className="size-3.5" />
            <span>Failed to load suggestions</span>
        </div>
    );
}

function DropdownEmpty({ query }: { query: string }) {
    return (
        <div className="px-2.5 py-3 text-sm text-muted-foreground">
            {query
                ? `No matches found for "${query}"`
                : "No items available"}
        </div>
    );
}
