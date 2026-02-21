import { forwardRef, type ComponentProps } from "react";
import { cn } from "@/lib/utils";
import { useMentionPickerContext } from "./mention-picker";

// ============================================================================
// MentionInput
// ============================================================================

export type MentionInputProps = Omit<
    ComponentProps<"textarea">,
    "value" | "onChange" | "onKeyDown" | "onClick"
> & {
    /** Extra className merged into the textarea */
    className?: string;
};

/**
 * MentionInput — a controlled textarea wired to the nearest MentionPicker
 * context. Drop this in wherever you'd normally place a `<textarea>`.
 *
 * All mention-related event handling is injected automatically.
 */
export const MentionInput = forwardRef<HTMLTextAreaElement, MentionInputProps>(
    function MentionInput({ className, ...props }, _externalRef) {
        const {
            displayValue,
            handleChange,
            handleKeyDown,
            handleClick,
            textareaRef,
            isOpen,
            activeTrigger,
            filteredItems,
        } = useMentionPickerContext();

        // Keep track of active-descendant for ARIA
        const activeDescendantId =
            isOpen && filteredItems.length > 0
                ? `mention-item-0`
                : undefined;

        return (
            <div className="relative w-full">
                <textarea
                    ref={textareaRef}
                    // Required so PromptInput's form can read value via formData.get("message")
                    name="message"
                    value={displayValue}
                    onChange={handleChange}
                    onKeyDown={handleKeyDown}
                    onClick={handleClick}
                    // ARIA attributes
                    role="combobox"
                    aria-expanded={isOpen}
                    aria-haspopup="listbox"
                    aria-autocomplete="list"
                    aria-activedescendant={activeDescendantId}
                    aria-label={activeTrigger ? `Mention ${activeTrigger.config.type}` : undefined}
                    className={cn(
                        "w-full resize-none bg-transparent text-foreground placeholder:text-muted-foreground",
                        "focus:outline-none focus-visible:outline-none",
                        "min-h-[2.25rem] text-sm leading-relaxed",
                        className
                    )}
                    {...props}
                />
            </div>
        );
    }
);

MentionInput.displayName = "MentionInput";
