// ============================================================================
// Mention Utils — pure functions, no React imports
// ============================================================================

import type {
    ActiveTrigger,
    CaretCoords,
    MentionItem,
    MentionPayload,
    MentionToken,
    Token,
    TriggerConfig,
} from "./mention-types";

// ---------------------------------------------------------------------------
// Wire format
// Token wire format: [mention:@:Label:id]
// ---------------------------------------------------------------------------

const MENTION_REGEX = /\[mention:([^:]+):([^:]+):([^\]]+)\]/g;

/**
 * Parse a wire-format string into a Token array.
 */
export function parse(wire: string): Token[] {
    const tokens: Token[] = [];
    let lastIndex = 0;

    for (const match of wire.matchAll(MENTION_REGEX)) {
        const [fullMatch, triggerChar, label, id] = match;
        const matchStart = match.index!;

        // Text before this mention
        if (matchStart > lastIndex) {
            tokens.push({ type: "text", value: wire.slice(lastIndex, matchStart) });
        }

        tokens.push({ type: "mention", id, label, triggerChar });
        lastIndex = matchStart + fullMatch.length;
    }

    // Remaining text
    if (lastIndex < wire.length) {
        tokens.push({ type: "text", value: wire.slice(lastIndex) });
    }

    return tokens;
}

/**
 * Serialize a Token array back to wire format.
 */
export function serialize(tokens: Token[]): string {
    return tokens
        .map((t) =>
            t.type === "mention"
                ? `[mention:${t.triggerChar}:${t.label}:${t.id}]`
                : t.value
        )
        .join("");
}

/**
 * Derive the display string from tokens (shown in the textarea / mirror).
 * Mentions appear as "@Label".
 */
export function toDisplayString(tokens: Token[]): string {
    return tokens
        .map((t) =>
            t.type === "mention" ? `${t.triggerChar}${t.label}` : t.value
        )
        .join("");
}

/**
 * Get plain text (no mention syntax, no trigger chars).
 */
export function toPlainText(tokens: Token[]): string {
    return tokens.map((t) => (t.type === "mention" ? t.label : t.value)).join("");
}

/**
 * Get structured API payload from tokens.
 */
export function toApiPayload(tokens: Token[]): MentionPayload {
    const mentions: MentionPayload["mentions"] = [];
    const plainText = tokens
        .map((t) => {
            if (t.type === "mention") {
                mentions.push({ id: t.id, label: t.label, triggerChar: t.triggerChar });
                return t.label;
            }
            return t.value;
        })
        .join("");

    return { plainText, mentions };
}

// ---------------------------------------------------------------------------
// Trigger Detection
// ---------------------------------------------------------------------------

/**
 * Given the current textarea value and cursor position, detect whether an
 * active trigger session should be opened/updated.
 *
 * Trigger fires ONLY when preceded by: start-of-string OR whitespace.
 * Prevents triggering inside email@example.com.
 */
export function detectTrigger(
    value: string,
    cursorPos: number,
    triggers: TriggerConfig[]
): ActiveTrigger | null {
    // Only look at the text before the cursor
    const textBeforeCursor = value.slice(0, cursorPos);

    for (const config of triggers) {
        const escaped = config.char.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
        // Match trigger char at start OR after whitespace; capture query after it
        const pattern = new RegExp(`(?:^|\\s)(${escaped})(\\S*)$`);
        const match = textBeforeCursor.match(pattern);

        if (match) {
            const triggerChar = match[1];
            const query = match[2];
            // Find where in the full string this trigger char actually sits
            const fullMatchStart = textBeforeCursor.lastIndexOf(triggerChar + query);

            return {
                config,
                query,
                triggerStart: fullMatchStart,
            };
        }
    }

    return null;
}

// ---------------------------------------------------------------------------
// Item Filtering
// ---------------------------------------------------------------------------

/**
 * Filter items by query string using case-insensitive substring match.
 * Swap this function for fuzzy search in the future (e.g. fuse.js).
 */
export function filterItems(items: MentionItem[], query: string): MentionItem[] {
    if (!query) return items;
    const lower = query.toLowerCase();
    return items.filter((item) => item.label.toLowerCase().includes(lower));
}

// ---------------------------------------------------------------------------
// Caret Coordinates — Mirror Div Technique
// ---------------------------------------------------------------------------

// Styles to copy from textarea to the mirror div for accurate measurement
const MIRROR_STYLE_PROPS: (keyof CSSStyleDeclaration)[] = [
    "borderTopWidth",
    "borderRightWidth",
    "borderBottomWidth",
    "borderLeftWidth",
    "paddingTop",
    "paddingRight",
    "paddingBottom",
    "paddingLeft",
    "fontSize",
    "fontFamily",
    "fontWeight",
    "fontStyle",
    "lineHeight",
    "letterSpacing",
    "textTransform",
    "wordSpacing",
    "wordBreak",
    "wordWrap",
    "whiteSpace",
    "tabSize",
    "boxSizing",
];

/**
 * Returns the pixel coordinates (relative to the viewport) of the caret at
 * `caretIndex` inside the given textarea element.
 *
 * Uses the mirror-div technique:
 * 1. Creates a hidden div with identical layout to the textarea, placed at the
 *    textarea's exact viewport position (position: fixed).
 * 2. Fills it with the text up to the caret + a zero-width marker span.
 * 3. Measures the marker's getBoundingClientRect() → viewport coords.
 * 4. Subtracts the textarea's scrollTop so mid-scroll positions are correct.
 */
export function getCaretCoords(
    textarea: HTMLTextAreaElement,
    caretIndex: number
): CaretCoords {
    const textareaRect = textarea.getBoundingClientRect();
    const computed = window.getComputedStyle(textarea);

    const mirror = document.createElement("div");
    mirror.setAttribute("aria-hidden", "true");

    const style = mirror.style;

    // Copy every layout-relevant style from the textarea
    for (const prop of MIRROR_STYLE_PROPS) {
        style.setProperty(prop as string, computed.getPropertyValue(prop as string));
    }

    // ⬇ Position the mirror at exactly the same viewport location as the textarea.
    // Using position:fixed + the textarea's rect means marker rects come out
    // as proper viewport coords without any extra offset arithmetic.
    style.position = "fixed";
    style.top = `${textareaRect.top}px`;
    style.left = `${textareaRect.left}px`;
    style.width = `${textareaRect.width}px`;
    style.height = `${textareaRect.height}px`;

    // Clip to the visible area of the textarea (respect its scroll)
    style.overflow = "hidden";
    style.whiteSpace = "pre-wrap";
    style.wordWrap = "break-word";
    style.visibility = "hidden";
    style.pointerEvents = "none";
    // zIndex irrelevant since visibility:hidden, but keep it out of the way
    style.zIndex = "-9999";

    // Text before the caret — we replicate the textarea's scrollTop so the
    // marker ends up at the right visual line even when the textarea is scrolled.
    const textBeforeCaret = textarea.value.slice(0, caretIndex);

    const escaped = textBeforeCaret
        .replace(/&/g, "&amp;")
        .replace(/</g, "&lt;")
        .replace(/>/g, "&gt;")
        .replace(/\n/g, "<br>");

    // Zero-width space inside the marker so it has measurable dimensions
    mirror.innerHTML = `${escaped}<span id="__mention_caret_marker__">\u200B</span>`;

    document.body.appendChild(mirror);

    // Shift the mirror's text up by the textarea's scroll amount so the marker
    // lands on the correct visual line
    mirror.scrollTop = textarea.scrollTop;

    const marker = mirror.querySelector(
        "#__mention_caret_marker__"
    ) as HTMLElement;
    const markerRect = marker.getBoundingClientRect();
    const lineHeightValue = parseFloat(computed.lineHeight) || 20;

    document.body.removeChild(mirror);

    return {
        x: markerRect.left,
        y: markerRect.top,
        lineHeight: lineHeightValue,
    };
}

// ---------------------------------------------------------------------------
// Token Mutation Helpers
// ---------------------------------------------------------------------------

/**
 * Insert a mention into the display string at the given range
 * (replaces from triggerStart to cursorPos), and return the new display value
 * plus the cursor position after the inserted mention + trailing space.
 */
export function buildInsertedDisplayValue(
    displayValue: string,
    triggerStart: number,
    cursorPos: number,
    mention: MentionToken
): { newValue: string; newCursorPos: number } {
    const insertion = `${mention.triggerChar}${mention.label} `;
    const newValue =
        displayValue.slice(0, triggerStart) +
        insertion +
        displayValue.slice(cursorPos);
    const newCursorPos = triggerStart + insertion.length;
    return { newValue, newCursorPos };
}

/**
 * Check if the cursor is immediately after a mention in the display string.
 * Returns the range [start, end] of that mention display text, or null.
 *
 * We scan backwards from cursorPos looking for a trigger char preceded by
 * start-of-string or whitespace, then check that the span has no spaces
 * (i.e. it's an inserted mention label, not partial typed text).
 */
export function getMentionRangeBeforeCursor(
    displayValue: string,
    cursorPos: number,
    tokens: Token[]
): { start: number; end: number } | null {
    // Rebuild display positions for each token
    let pos = 0;
    for (const token of tokens) {
        const display =
            token.type === "mention"
                ? `${token.triggerChar}${token.label} `
                : token.value;
        const end = pos + display.length;

        if (token.type === "mention" && cursorPos === end) {
            return { start: pos, end };
        }
        pos = end;
    }
    return null;
}
