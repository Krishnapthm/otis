import { useCallback, useEffect, useMemo, useReducer, useRef } from "react";
import type {
  ActiveTrigger,
  CaretCoords,
  MentionItem,
  MentionPayload,
  MentionStatus,
  MentionToken,
  Token,
  TriggerConfig,
} from "./mention-types";
import {
  buildInsertedDisplayValue,
  getCaretCoordsFromContentEditable,
  getContentEditableSelectionRange,
  getContentEditableText,
  detectTrigger,
  filterItems,
  getCaretCoords,
  getMentionRangeBeforeCursor,
  setContentEditableSelectionRange,
  toApiPayload,
  toDisplayString,
  parse,
  serialize,
} from "./mention-utils";

// ============================================================================
// State shape & Reducer
// ============================================================================

interface MentionPickerState {
  /** Plain display string (what's shown in the textarea) */
  displayValue: string;
  /** Structured tokens — source of truth */
  tokens: Token[];
  /** Whether the dropdown is open */
  isOpen: boolean;
  /** Currently active trigger session */
  activeTrigger: ActiveTrigger | null;
  /** Index of highlighted dropdown item */
  activeIndex: number;
  /** Filtered items currently shown in dropdown */
  filteredItems: MentionItem[];
  /** Caret pixel coordinates for dropdown anchoring */
  caretCoords: CaretCoords | null;
  /** Async status */
  status: MentionStatus;
}

type MentionPickerAction =
  | {
      type: "INPUT_CHANGE";
      displayValue: string;
      activeTrigger: ActiveTrigger | null;
      filteredItems: MentionItem[];
      caretCoords: CaretCoords | null;
    }
  | { type: "CLOSE_DROPDOWN" }
  | { type: "SET_ACTIVE_INDEX"; index: number }
  | { type: "MOVE_INDEX"; delta: 1 | -1 }
  | {
      type: "INSERT_MENTION";
      displayValue: string;
      tokens: Token[];
    }
  | {
      type: "SET_TOKENS";
      tokens: Token[];
    }
  | { type: "SET_STATUS"; status: MentionStatus };

function reducer(
  state: MentionPickerState,
  action: MentionPickerAction,
): MentionPickerState {
  switch (action.type) {
    case "INPUT_CHANGE":
      return {
        ...state,
        displayValue: action.displayValue,
        activeTrigger: action.activeTrigger,
        filteredItems: action.filteredItems,
        isOpen: action.activeTrigger !== null,
        caretCoords: action.caretCoords,
        activeIndex: 0,
      };

    case "CLOSE_DROPDOWN":
      return {
        ...state,
        isOpen: false,
        activeTrigger: null,
        filteredItems: [],
        activeIndex: 0,
        caretCoords: null,
      };

    case "SET_ACTIVE_INDEX":
      return { ...state, activeIndex: action.index };

    case "MOVE_INDEX": {
      const len = state.filteredItems.length;
      if (len === 0) return state;
      const next = (state.activeIndex + action.delta + len) % len;
      return { ...state, activeIndex: next };
    }

    case "INSERT_MENTION":
      return {
        ...state,
        displayValue: action.displayValue,
        tokens: action.tokens,
        isOpen: false,
        activeTrigger: null,
        filteredItems: [],
        activeIndex: 0,
        caretCoords: null,
      };

    case "SET_TOKENS":
      return {
        ...state,
        tokens: action.tokens,
      };

    case "SET_STATUS":
      return { ...state, status: action.status };

    default:
      return state;
  }
}

// ============================================================================
// Hook
// ============================================================================

export interface UseMentionPickerOptions {
  triggers: TriggerConfig[];
  initialValue?: string;
  onValueChange?: (displayValue: string, tokens: Token[]) => void;
  getDisplayValue?: (element: MentionInputElement) => string;
  getSelectionRange?: (
    element: MentionInputElement,
    displayValue: string,
  ) => { start: number; end: number };
  setSelectionRange?: (
    element: MentionInputElement,
    start: number,
    end: number,
  ) => void;
  getCaretCoordinates?: (
    element: MentionInputElement,
    caretIndex: number,
  ) => CaretCoords;
}

export type MentionInputElement = HTMLTextAreaElement | HTMLDivElement;

export interface UseMentionPickerReturn {
  // State
  displayValue: string;
  tokens: Token[];
  isOpen: boolean;
  activeTrigger: ActiveTrigger | null;
  activeIndex: number;
  filteredItems: MentionItem[];
  caretCoords: CaretCoords | null;
  status: MentionStatus;

  // Derived
  getApiPayload: () => MentionPayload;
  getWireValue: () => string;

  // Handlers (to be spread onto the editable element)
  handleChange: (
    e: React.ChangeEvent<HTMLTextAreaElement> | React.FormEvent<HTMLDivElement>,
  ) => void;
  handleKeyDown: (e: React.KeyboardEvent<MentionInputElement>) => void;
  handleClick: () => void;

  // Programmatic controls
  selectItem: (item: MentionItem) => void;
  closeDropdown: () => void;
  setActiveIndex: (index: number) => void;
  reset: () => void;
  replaceDisplayValue: (
    nextDisplayValue: string,
    selection?: { start: number; end: number },
  ) => void;

  // Ref to attach to the editable element
  textareaRef: React.RefObject<MentionInputElement | null>;
}

export function useMentionPicker(
  options: UseMentionPickerOptions,
): UseMentionPickerReturn {
  const {
    triggers,
    initialValue = "",
    onValueChange,
    getDisplayValue: customGetDisplayValue,
    getSelectionRange: customGetSelectionRange,
    setSelectionRange: customSetSelectionRange,
    getCaretCoordinates: customGetCaretCoordinates,
  } = options;

  const initialTokens = useMemo(() => parse(initialValue), [initialValue]);

  const [state, dispatch] = useReducer(reducer, {
    displayValue: toDisplayString(initialTokens),
    tokens: initialTokens,
    isOpen: false,
    activeTrigger: null,
    activeIndex: 0,
    filteredItems: [],
    caretCoords: null,
    status: "idle",
  });

  const textareaRef = useRef<MentionInputElement | null>(null);

  const getDisplayValue = useCallback(
    (element: MentionInputElement): string => {
      if (customGetDisplayValue) {
        return customGetDisplayValue(element);
      }
      if (element instanceof HTMLTextAreaElement) {
        return element.value;
      }
      return getContentEditableText(element);
    },
    [customGetDisplayValue],
  );

  const getSelectionRange = useCallback(
    (element: MentionInputElement, displayValue: string) => {
      if (customGetSelectionRange) {
        return customGetSelectionRange(element, displayValue);
      }
      if (element instanceof HTMLTextAreaElement) {
        const start = element.selectionStart ?? displayValue.length;
        const end = element.selectionEnd ?? start;
        return { start, end };
      }
      return getContentEditableSelectionRange(element);
    },
    [customGetSelectionRange],
  );

  const setSelectionRange = useCallback(
    (element: MentionInputElement, start: number, end: number) => {
      if (customSetSelectionRange) {
        customSetSelectionRange(element, start, end);
        return;
      }

      if (element instanceof HTMLTextAreaElement) {
        element.setSelectionRange(start, end);
        return;
      }

      setContentEditableSelectionRange(element, start, end);
    },
    [customSetSelectionRange],
  );

  const getCaretCoordinates = useCallback(
    (element: MentionInputElement, caretIndex: number): CaretCoords => {
      if (customGetCaretCoordinates) {
        return customGetCaretCoordinates(element, caretIndex);
      }
      if (element instanceof HTMLTextAreaElement) {
        return getCaretCoords(element, caretIndex);
      }
      return getCaretCoordsFromContentEditable(element, caretIndex);
    },
    [customGetCaretCoordinates],
  );

  // Notify parent when value changes
  const prevDisplayRef = useRef(state.displayValue);
  useEffect(() => {
    if (state.displayValue !== prevDisplayRef.current) {
      prevDisplayRef.current = state.displayValue;
      onValueChange?.(state.displayValue, state.tokens);
    }
  }, [state.displayValue, state.tokens, onValueChange]);

  // -------------------------------------------------------------------------
  // handleChange
  // -------------------------------------------------------------------------
  const handleChange = useCallback(
    (
      e:
        | React.ChangeEvent<HTMLTextAreaElement>
        | React.FormEvent<HTMLDivElement>,
    ) => {
      const inputElement = e.currentTarget as MentionInputElement;
      const newDisplayValue = getDisplayValue(inputElement);
      const selection = getSelectionRange(inputElement, newDisplayValue);
      const cursorPos = selection.start;

      // Detect whether a trigger is active at the cursor
      const detected = detectTrigger(newDisplayValue, cursorPos, triggers);

      let coords: CaretCoords | null = null;
      let items: MentionItem[] = [];

      if (detected) {
        try {
          coords = getCaretCoordinates(inputElement, detected.triggerStart);
        } catch {
          // measurement can fail in tests/SSR — degrade gracefully
        }
        items = filterItems(detected.config.items ?? [], detected.query);
      }

      // Rebuild token array from new display value
      // We re-derive tokens by merging: preserve existing mention tokens
      // that still appear in newDisplayValue, rest is text.
      const newTokens = rebuildTokens(newDisplayValue, state.tokens);

      // Push token update without triggering onValueChange loop
      // (we'll notify via the effect above)
      dispatch({
        type: "INPUT_CHANGE",
        displayValue: newDisplayValue,
        activeTrigger: detected,
        filteredItems: items,
        caretCoords: coords,
      });

      dispatch({
        type: "SET_TOKENS",
        tokens: newTokens,
      });
    },
    [
      triggers,
      state.tokens,
      getDisplayValue,
      getSelectionRange,
      getCaretCoordinates,
    ],
  );

  // -------------------------------------------------------------------------
  // selectItem — inserts a mention token
  // -------------------------------------------------------------------------
  const selectItem = useCallback(
    (item: MentionItem) => {
      const inputElement = textareaRef.current;
      if (!inputElement || !state.activeTrigger) return;

      const trigger = state.activeTrigger;
      const cursorPos = getSelectionRange(
        inputElement,
        state.displayValue,
      ).start;

      const mentionToken: MentionToken = {
        type: "mention",
        id: item.id,
        label: item.label,
        triggerChar: trigger.config.char,
      };

      const { newValue, newCursorPos } = buildInsertedDisplayValue(
        state.displayValue,
        trigger.triggerStart,
        cursorPos,
        mentionToken,
      );

      // Rebuild full token list
      const newTokens = rebuildTokens(newValue, [
        ...state.tokens,
        mentionToken,
      ]);

      dispatch({
        type: "INSERT_MENTION",
        displayValue: newValue,
        tokens: newTokens,
      });

      // Restore focus + set cursor after the inserted mention
      requestAnimationFrame(() => {
        if (textareaRef.current) {
          textareaRef.current.focus();
          setSelectionRange(textareaRef.current, newCursorPos, newCursorPos);
        }
      });

      onValueChange?.(newValue, newTokens);
    },
    [
      state.activeTrigger,
      state.displayValue,
      state.tokens,
      onValueChange,
      getSelectionRange,
      setSelectionRange,
    ],
  );

  // -------------------------------------------------------------------------
  // handleKeyDown — intercept arrow/enter/escape when dropdown is open
  // -------------------------------------------------------------------------
  const handleKeyDown = useCallback(
    (e: React.KeyboardEvent<MentionInputElement>) => {
      if (!state.isOpen) {
        // Backspace: if cursor is right after a mention chip, delete whole chip
        if (e.key === "Backspace") {
          const inputElement = e.currentTarget;
          const selection = getSelectionRange(inputElement, state.displayValue);
          const cursorPos = selection.start;
          const selEnd = selection.end;

          // Only intercept when no text is selected and we have tokens
          if (cursorPos === selEnd) {
            const range = getMentionRangeBeforeCursor(cursorPos, state.tokens);
            if (range) {
              e.preventDefault();
              const newDisplay =
                state.displayValue.slice(0, range.start) +
                state.displayValue.slice(range.end);
              const newTokens = rebuildTokens(newDisplay, state.tokens);
              dispatch({
                type: "INSERT_MENTION",
                displayValue: newDisplay,
                tokens: newTokens,
              });
              requestAnimationFrame(() => {
                if (textareaRef.current) {
                  setSelectionRange(
                    textareaRef.current,
                    range.start,
                    range.start,
                  );
                }
              });
              onValueChange?.(newDisplay, newTokens);
            }
          }
        }
        return;
      }

      switch (e.key) {
        case "ArrowDown":
          e.preventDefault();
          dispatch({ type: "MOVE_INDEX", delta: 1 });
          break;
        case "ArrowUp":
          e.preventDefault();
          dispatch({ type: "MOVE_INDEX", delta: -1 });
          break;
        case "Enter":
        case "Tab": {
          e.preventDefault();
          const item = state.filteredItems[state.activeIndex];
          if (item) selectItem(item);
          break;
        }
        case "Escape":
          e.preventDefault();
          dispatch({ type: "CLOSE_DROPDOWN" });
          break;
      }
    },
    [
      state.isOpen,
      state.filteredItems,
      state.activeIndex,
      state.displayValue,
      state.tokens,
      selectItem,
      onValueChange,
      getSelectionRange,
      setSelectionRange,
    ],
  );

  const handleClick = useCallback(() => {
    // Re-evaluate trigger at new cursor (in case user clicked mid-mention)
    const inputElement = textareaRef.current;
    if (!inputElement) return;
    const cursorPos = getSelectionRange(inputElement, state.displayValue).start;
    const detected = detectTrigger(state.displayValue, cursorPos, triggers);
    if (!detected && state.isOpen) {
      dispatch({ type: "CLOSE_DROPDOWN" });
    }
  }, [state.displayValue, state.isOpen, triggers, getSelectionRange]);

  const closeDropdown = useCallback(() => {
    dispatch({ type: "CLOSE_DROPDOWN" });
  }, []);

  const setActiveIndex = useCallback((index: number) => {
    dispatch({ type: "SET_ACTIVE_INDEX", index });
  }, []);

  const reset = useCallback(() => {
    dispatch({
      type: "INSERT_MENTION",
      displayValue: "",
      tokens: [],
    });
  }, []);

  const getApiPayload = useCallback(
    () => toApiPayload(state.tokens),
    [state.tokens],
  );

  const getWireValue = useCallback(
    () => serialize(state.tokens),
    [state.tokens],
  );

  const replaceDisplayValue = useCallback(
    (nextDisplayValue: string, selection?: { start: number; end: number }) => {
      const inputElement = textareaRef.current;
      if (!inputElement) return;

      const caretStart = Math.max(
        0,
        Math.min(
          selection?.start ?? nextDisplayValue.length,
          nextDisplayValue.length,
        ),
      );
      const caretEnd = Math.max(
        caretStart,
        Math.min(selection?.end ?? caretStart, nextDisplayValue.length),
      );

      const detected = detectTrigger(nextDisplayValue, caretStart, triggers);

      let coords: CaretCoords | null = null;
      let items: MentionItem[] = [];

      if (detected) {
        try {
          coords = getCaretCoordinates(inputElement, detected.triggerStart);
        } catch {
          // measurement can fail in tests/SSR — degrade gracefully
        }
        items = filterItems(detected.config.items ?? [], detected.query);
      }

      const newTokens = rebuildTokens(nextDisplayValue, state.tokens);

      dispatch({
        type: "INPUT_CHANGE",
        displayValue: nextDisplayValue,
        activeTrigger: detected,
        filteredItems: items,
        caretCoords: coords,
      });

      dispatch({
        type: "SET_TOKENS",
        tokens: newTokens,
      });

      requestAnimationFrame(() => {
        if (textareaRef.current) {
          textareaRef.current.focus();
          setSelectionRange(textareaRef.current, caretStart, caretEnd);
        }
      });
    },
    [triggers, getCaretCoordinates, state.tokens, setSelectionRange],
  );

  return {
    displayValue: state.displayValue,
    tokens: state.tokens,
    isOpen: state.isOpen,
    activeTrigger: state.activeTrigger,
    activeIndex: state.activeIndex,
    filteredItems: state.filteredItems,
    caretCoords: state.caretCoords,
    status: state.status,
    getApiPayload,
    getWireValue,
    handleChange,
    handleKeyDown,
    handleClick,
    selectItem,
    closeDropdown,
    setActiveIndex,
    reset,
    replaceDisplayValue,
    textareaRef,
  };
}

// ============================================================================
// Token Rebuilder
// ============================================================================

/**
 * After any edit action, re-derive the token array from the current display string.
 *
 * Strategy: scan the display string; for each known mention (triggerChar + label + space)
 * that appears as a contiguous block, emit a MentionToken, else TextToken.
 *
 * This keeps mentions as atomic units through edits without needing contenteditable.
 */
function rebuildTokens(displayValue: string, knownTokens: Token[]): Token[] {
  // Collect all known mentions from previous token list
  const knownMentions = knownTokens.filter(
    (t): t is MentionToken => t.type === "mention",
  );

  if (knownMentions.length === 0) {
    return [{ type: "text", value: displayValue }];
  }

  const tokens: Token[] = [];
  const globalOffset = 0;

  // Build a map: displayFragment -> MentionToken
  // A mention occupies "@Label " in the display string
  const mentionDisplayMap = new Map<string, MentionToken>();
  for (const m of knownMentions) {
    const fragment = `${m.triggerChar}${m.label} `;
    mentionDisplayMap.set(fragment, m);
  }

  // Sort mentions by order of appearance in displayValue
  const sortedFragments = [...mentionDisplayMap.keys()].sort((a, b) => {
    const ia = displayValue.indexOf(a, globalOffset);
    const ib = displayValue.indexOf(b, globalOffset);
    return ia - ib;
  });

  let pos = 0;
  // Walk through displayValue looking for mention fragments
  while (pos < displayValue.length) {
    // Try to find the earliest mention fragment from current pos
    let earliestIdx = -1;
    let earliestFrag: string | null = null;

    for (const frag of sortedFragments) {
      const idx = displayValue.indexOf(frag, pos);
      if (idx !== -1 && (earliestIdx === -1 || idx < earliestIdx)) {
        earliestIdx = idx;
        earliestFrag = frag;
      }
    }

    if (earliestFrag === null || earliestIdx === -1) {
      // No more mentions; rest is text
      const textVal = displayValue.slice(pos);
      if (textVal) tokens.push({ type: "text", value: textVal });
      break;
    }

    // Text before this mention
    if (earliestIdx > pos) {
      tokens.push({
        type: "text",
        value: displayValue.slice(pos, earliestIdx),
      });
    }

    // The mention token itself
    tokens.push(mentionDisplayMap.get(earliestFrag)!);
    pos = earliestIdx + earliestFrag.length;
  }

  return tokens.length > 0 ? tokens : [{ type: "text", value: displayValue }];
}
