import {
  forwardRef,
  useCallback,
  useLayoutEffect,
  useRef,
  useState,
  type ComponentProps,
} from "react";
import { createRoot, type Root } from "react-dom/client";
import { cn } from "@/lib/utils";
import { MentionChip } from "./mention-chip";
import {
  getContentEditableSelectionRange,
  setContentEditableSelectionRange,
} from "./mention-utils";
import type { Token } from "./mention-types";
import { useMentionPickerContext } from "./mention-picker";
import {
  type EditableHistorySnapshot,
  useEditableHistory,
} from "./use-editable-history";

export type MentionInputEditableProps = Omit<
  ComponentProps<"div">,
  "onChange" | "contentEditable"
> & {
  className?: string;
  placeholder?: string;
};

interface DisplayPart {
  type: "text" | "mention";
  value: string;
  start?: number;
  end?: number;
}

const ENABLE_MENTION_DEBUG_LOGS = false;

function debugMentionEditable(event: string, payload: Record<string, unknown>) {
  if (!ENABLE_MENTION_DEBUG_LOGS) return;
  console.debug(`[MentionInputEditable] ${event}`, payload);
}

function buildDisplayParts(tokens: Token[]): DisplayPart[] {
  const parts: DisplayPart[] = [];
  let cursor = 0;

  for (let index = 0; index < tokens.length; index += 1) {
    const token = tokens[index];

    if (token.type === "text") {
      if (token.value.length > 0) {
        parts.push({
          type: "text",
          value: token.value,
        });
        cursor += token.value.length;
      }
      continue;
    }

    const mentionDisplayValue = `${token.triggerChar}${token.label}`;

    parts.push({
      type: "mention",
      value: token.label,
      start: cursor,
      end: cursor + mentionDisplayValue.length,
    });

    cursor += mentionDisplayValue.length;

    const nextToken = tokens[index + 1];
    const hasLeadingSpaceInNextText =
      nextToken?.type === "text" && nextToken.value.startsWith(" ");

    if (!hasLeadingSpaceInNextText) {
      parts.push({
        type: "text",
        value: " ",
      });
      cursor += 1;
    }
  }

  return parts;
}

function insertPlainTextAtCursor(text: string) {
  if (document.queryCommandSupported?.("insertText")) {
    document.execCommand("insertText", false, text);
    return;
  }

  const selection = window.getSelection();
  if (!selection || selection.rangeCount === 0) return;

  const range = selection.getRangeAt(0);
  range.deleteContents();
  range.insertNode(document.createTextNode(text));
  range.collapse(false);

  selection.removeAllRanges();
  selection.addRange(range);
}

export const MentionInputEditable = forwardRef<
  HTMLDivElement,
  MentionInputEditableProps
>(function MentionInputEditable(
  {
    className,
    placeholder = "What would you like to know?",
    onPaste,
    onInput,
    onKeyDown,
    onClick,
    ...props
  },
  externalRef,
) {
  const {
    displayValue,
    tokens,
    handleChange,
    handleKeyDown,
    handleClick,
    replaceDisplayValue,
    textareaRef,
    isOpen,
    activeTrigger,
    filteredItems,
  } = useMentionPickerContext();

  const [isComposing, setIsComposing] = useState(false);
  const editableRef = useRef<HTMLDivElement | null>(null);
  const desiredSelectionRef = useRef<{ start: number; end: number } | null>(
    null,
  );
  const mentionChipRootsRef = useRef<Root[]>([]);
  const isRestoringRef = useRef(false);
  const history = useEditableHistory({ maxEntries: 250, coalesceMs: 350 });

  const cleanupMentionChipRoots = useCallback(() => {
    const rootsToUnmount = [...mentionChipRootsRef.current];
    mentionChipRootsRef.current = [];

    requestAnimationFrame(() => {
      for (const root of rootsToUnmount) {
        root.unmount();
      }
    });
  }, []);

  const snapshotFromElement = useCallback(
    (element: HTMLDivElement): EditableHistorySnapshot => {
      const selection = getContentEditableSelectionRange(element);
      return {
        value: displayValue,
        selection,
      };
    },
    [displayValue],
  );

  const setEditableRef = useCallback(
    (node: HTMLDivElement | null) => {
      editableRef.current = node;
      textareaRef.current = node;
      if (typeof externalRef === "function") {
        externalRef(node);
      } else if (externalRef) {
        externalRef.current = node;
      }
    },
    [externalRef, textareaRef],
  );

  const removeMentionAtRange = useCallback(
    (start: number, end: number) => {
      const target = editableRef.current;
      if (target) {
        history.capture(snapshotFromElement(target), true);
      }

      const nextDisplayValue = `${displayValue.slice(0, start)}${displayValue.slice(end)}`;
      desiredSelectionRef.current = { start, end: start };
      replaceDisplayValue(nextDisplayValue, { start, end: start });
    },
    [displayValue, history, replaceDisplayValue, snapshotFromElement],
  );

  useLayoutEffect(() => {
    const target = editableRef.current;
    if (!target || isComposing) {
      return;
    }

    cleanupMentionChipRoots();

    const wasFocused = document.activeElement === target;
    const fallbackSelection = wasFocused
      ? getContentEditableSelectionRange(target)
      : null;

    const parts = buildDisplayParts(tokens);
    const fragment = document.createDocumentFragment();

    debugMentionEditable("render", {
      displayValue,
      parts,
      tokens,
    });

    for (const part of parts) {
      if (part.type === "mention") {
        const mentionHost = document.createElement("span");
        mentionHost.contentEditable = "false";
        const mentionRoot = createRoot(mentionHost);
        mentionRoot.render(
          <MentionChip
            includeHiddenTriggerChar
            label={part.value}
            onRemove={() =>
              removeMentionAtRange(part.start ?? 0, part.end ?? 0)
            }
            removable
            tabIndex={-1}
            variant="input"
          />,
        );
        mentionChipRootsRef.current.push(mentionRoot);
        fragment.appendChild(mentionHost);
        continue;
      }

      fragment.appendChild(document.createTextNode(part.value));
    }

    target.replaceChildren(fragment);

    const desired = desiredSelectionRef.current ?? fallbackSelection;
    if (desired && wasFocused) {
      setContentEditableSelectionRange(target, desired.start, desired.end);
    }
    desiredSelectionRef.current = null;

    if (!history.canUndo && !history.canRedo) {
      history.initialize({
        value: displayValue,
        selection: desired ?? getContentEditableSelectionRange(target),
      });
    }
  }, [
    displayValue,
    tokens,
    isComposing,
    history,
    cleanupMentionChipRoots,
    removeMentionAtRange,
  ]);

  useLayoutEffect(
    () => () => {
      cleanupMentionChipRoots();
    },
    [cleanupMentionChipRoots],
  );

  useLayoutEffect(() => {
    const target = editableRef.current;
    if (!target || isComposing || isRestoringRef.current) {
      return;
    }

    history.capture(
      {
        value: displayValue,
        selection: getContentEditableSelectionRange(target),
      },
      false,
    );
  }, [displayValue, isComposing, history]);

  const activeDescendantId =
    isOpen && filteredItems.length > 0 ? `mention-item-0` : undefined;

  const handleInput = useCallback(
    (e: React.FormEvent<HTMLDivElement>) => {
      desiredSelectionRef.current = getContentEditableSelectionRange(
        e.currentTarget,
      );
      debugMentionEditable("input", {
        domText: e.currentTarget.textContent,
        selection: desiredSelectionRef.current,
      });

      if (!isRestoringRef.current) {
        history.capture(snapshotFromElement(e.currentTarget), false);
      }

      handleChange(e);
      onInput?.(e);
    },
    [handleChange, history, onInput, snapshotFromElement],
  );

  const restoreSnapshot = useCallback(
    (snapshot: EditableHistorySnapshot | null) => {
      if (!snapshot) {
        return;
      }

      isRestoringRef.current = true;
      desiredSelectionRef.current = snapshot.selection;
      replaceDisplayValue(snapshot.value, snapshot.selection);

      requestAnimationFrame(() => {
        isRestoringRef.current = false;
      });
    },
    [replaceDisplayValue],
  );

  const handleEditableKeyDown = useCallback(
    (e: React.KeyboardEvent<HTMLDivElement>) => {
      debugMentionEditable("keydown", {
        key: e.key,
        isComposing,
        hasSelection: (window.getSelection()?.toString()?.length ?? 0) > 0,
      });

      const isModifier = e.metaKey || e.ctrlKey;
      if (isModifier && !e.altKey) {
        const key = e.key.toLowerCase();

        if (key === "z") {
          e.preventDefault();
          if (e.shiftKey) {
            restoreSnapshot(history.redo());
          } else {
            restoreSnapshot(history.undo());
          }
          return;
        }

        if (key === "y") {
          e.preventDefault();
          restoreSnapshot(history.redo());
          return;
        }
      }

      handleKeyDown(e);
      onKeyDown?.(e);

      if (e.defaultPrevented) {
        return;
      }

      if (e.key === "Enter") {
        if (isComposing || e.nativeEvent.isComposing || e.shiftKey) {
          return;
        }

        e.preventDefault();

        const form = e.currentTarget.closest("form");
        const submitButton = form?.querySelector(
          'button[type="submit"]',
        ) as HTMLButtonElement | null;

        if (submitButton?.disabled) {
          return;
        }

        form?.requestSubmit();
      }
    },
    [handleKeyDown, onKeyDown, isComposing, history, restoreSnapshot],
  );

  const handleEditablePaste = useCallback(
    (e: React.ClipboardEvent<HTMLDivElement>) => {
      e.preventDefault();
      const text = e.clipboardData.getData("text/plain");
      debugMentionEditable("paste", {
        text,
      });
      history.capture(snapshotFromElement(e.currentTarget), true);
      insertPlainTextAtCursor(text);
      desiredSelectionRef.current = getContentEditableSelectionRange(
        e.currentTarget,
      );
      handleChange(e);
      onPaste?.(e);
    },
    [handleChange, history, onPaste, snapshotFromElement],
  );

  const handleEditableClick = useCallback(
    (e: React.MouseEvent<HTMLDivElement>) => {
      handleClick();
      onClick?.(e);
    },
    [handleClick, onClick],
  );

  const handleEditableCut = useCallback(
    (e: React.ClipboardEvent<HTMLDivElement>) => {
      const selectedText = window.getSelection()?.toString() ?? "";
      if (selectedText.length > 0) {
        e.preventDefault();
        debugMentionEditable("cut", {
          selectedText,
        });
        history.capture(snapshotFromElement(e.currentTarget), true);
        e.clipboardData.setData("text/plain", selectedText);
        insertPlainTextAtCursor("");
        desiredSelectionRef.current = getContentEditableSelectionRange(
          e.currentTarget,
        );
        handleChange(e);
      }
    },
    [handleChange, history, snapshotFromElement],
  );

  return (
    <div className="relative w-full">
      <div
        ref={setEditableRef}
        contentEditable
        suppressContentEditableWarning
        data-placeholder={placeholder}
        data-slot="input-group-control"
        role="combobox"
        aria-expanded={isOpen}
        aria-haspopup="listbox"
        aria-autocomplete="list"
        aria-activedescendant={activeDescendantId}
        aria-label={
          activeTrigger ? `Mention ${activeTrigger.config.type}` : undefined
        }
        className={cn(
          "flex-1 min-h-16 max-h-48 overflow-y-auto whitespace-pre-wrap wrap-break-word",
          "rounded-none border-0 bg-transparent py-3 shadow-none",
          "focus:outline-none focus-visible:outline-none",
          "empty:before:content-[attr(data-placeholder)] empty:before:text-muted-foreground empty:before:pointer-events-none",
          "text-sm leading-relaxed text-left",
          className,
        )}
        spellCheck={false}
        onInput={handleInput}
        onKeyDown={handleEditableKeyDown}
        onClick={handleEditableClick}
        onPaste={handleEditablePaste}
        onCut={handleEditableCut}
        onCompositionStart={() => setIsComposing(true)}
        onCompositionEnd={() => setIsComposing(false)}
        {...props}
      />

      <input type="hidden" name="message" value={displayValue} readOnly />
    </div>
  );
});

MentionInputEditable.displayName = "MentionInputEditable";
