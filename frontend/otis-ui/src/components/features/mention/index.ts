// Mention Picker — Public API
// ============================================================================

export { MentionPicker, useMentionPickerContext } from "./mention-picker";
export type { MentionPickerProps } from "./mention-picker";

export { MentionInput } from "./mention-input";
export type { MentionInputProps } from "./mention-input";

export { MentionInputEditable } from "./mention-input-editable";
export type { MentionInputEditableProps } from "./mention-input-editable";

export { MentionDropdown } from "./mention-dropdown";
export type { MentionDropdownProps } from "./mention-dropdown";

export { MentionItem } from "./mention-item";
export type { MentionItemProps } from "./mention-item";

export { useMentionPicker } from "./use-mention-picker";
export type {
  UseMentionPickerOptions,
  UseMentionPickerReturn,
} from "./use-mention-picker";

export type {
  Token,
  TextToken,
  MentionToken,
  MentionItem as MentionItemData,
  TriggerConfig,
  ActiveTrigger,
  CaretCoords,
  MentionPayload,
  MentionStatus,
} from "./mention-types";

export {
  parse,
  serialize,
  toDisplayString,
  toPlainText,
  toApiPayload,
  detectTrigger,
  filterItems,
  getCaretCoords,
} from "./mention-utils";
