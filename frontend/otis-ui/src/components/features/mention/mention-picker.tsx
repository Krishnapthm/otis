import {
    createContext,
    useContext,
    type ReactNode,
} from "react";
import type { UseMentionPickerReturn, UseMentionPickerOptions } from "./use-mention-picker";
import { useMentionPicker } from "./use-mention-picker";

// ============================================================================
// Context
// ============================================================================

const MentionPickerContext = createContext<UseMentionPickerReturn | null>(null);

export function useMentionPickerContext(): UseMentionPickerReturn {
    const ctx = useContext(MentionPickerContext);
    if (!ctx) {
        throw new Error(
            "useMentionPickerContext must be used within a <MentionPicker>"
        );
    }
    return ctx;
}

// ============================================================================
// Root Component
// ============================================================================

export interface MentionPickerProps extends Partial<UseMentionPickerOptions> {
    /**
     * Optionally pass an already-created picker instance (from `useMentionPicker`)
     * to share its state with parents. When provided, the hook options are ignored.
     */
    externalPicker?: UseMentionPickerReturn;
    children: ReactNode;
}

/**
 * MentionPicker — root context provider.
 *
 * Two usage modes:
 *
 * 1. Self-managed (simple):
 * ```tsx
 * <MentionPicker triggers={[...]} onValueChange={...}>
 *   <MentionInput />
 *   <MentionDropdown />
 * </MentionPicker>
 * ```
 *
 * 2. External picker (e.g. to use with PromptInputTextarea):
 * ```tsx
 * const picker = useMentionPicker({ triggers: [...] });
 * <MentionPicker externalPicker={picker}>
 *   <PromptInputTextarea ref={picker.textareaRef} onChange={picker.handleChange} ... />
 *   <MentionDropdown />
 * </MentionPicker>
 * ```
 */
export function MentionPicker({
    children,
    externalPicker,
    triggers = [],
    initialValue,
    onValueChange,
}: MentionPickerProps) {
    // Only run internal hook when no external picker is provided.
    // This hook call is always made (rules of hooks) but its result is discarded
    // when externalPicker is provided.
    const internalPicker = useMentionPicker({ triggers, initialValue, onValueChange });
    const picker = externalPicker ?? internalPicker;

    return (
        <MentionPickerContext.Provider value={picker}>
            {children}
        </MentionPickerContext.Provider>
    );
}
