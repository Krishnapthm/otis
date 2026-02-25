import { useState, useCallback, useEffect, useRef, useMemo } from "react";
import { useParams } from "react-router-dom";
import { useQueryClient } from "@tanstack/react-query";
import {
  GlobeIcon,
  MessageSquareIcon,
  PaperclipIcon,
  Upload,
} from "lucide-react";
import type { ChatMessage as ChatMessageType } from "@/lib/chat-types";
import {
  Conversation,
  ConversationContent,
  ConversationEmptyState,
  ConversationScrollButton,
} from "@/components/ai-elements/conversation";
import {
  PromptInput,
  PromptInputBody,
  PromptInputFooter,
  type PromptInputMessage,
  PromptInputSubmit,
  PromptInputTools,
  PromptInputButton,
  PromptInputActionMenu,
  PromptInputActionMenuTrigger,
  PromptInputActionMenuContent,
  PromptInputActionAddAttachments,
} from "@/components/ai-elements/prompt-input";
import { DropdownMenuItem } from "@/components/ui/dropdown-menu";
import { ChatMessage } from "@/components/features/chat/chat-message";
import {
  MentionPicker,
  MentionDropdown,
  MentionInputEditable,
  useMentionPicker,
} from "@/components/features/mention";
import type { Token, TriggerConfig } from "@/components/features/mention";
import { chatApi } from "@/api/chatApi";
import { getAllUserDocuments, type Document } from "@/api/docApi";
import { queryKeys } from "@/api/queryKeys";
import { useDocuments } from "@/hooks/useDocuments";
import { useUploadDocument } from "@/hooks/useUploadDocument";
import { toast } from "sonner";

// ============================================================================
// Helpers
// ============================================================================

function apiMessageToLocal(msg: {
  message_id: string;
  role: string;
  content: string | null;
  created_at: string;
}): ChatMessageType {
  return {
    id: msg.message_id,
    role: msg.role as "user" | "assistant",
    content: msg.content ?? "",
    createdAt: msg.created_at,
  };
}

function buildTokenizedMentionMessage(
  tokens: Token[],
  fallbackText: string,
): string {
  if (tokens.length === 0) {
    return fallbackText;
  }

  return tokens
    .map((token) =>
      token.type === "mention" ? `[mention: ${token.label}]` : token.value,
    )
    .join("");
}

function resolveDocIdsFromNames(
  mentionNames: string[],
  documents: Document[],
): { docIds: string[]; unresolvedNames: string[] } {
  const byFilename = new Map<string, string>();

  for (const document of documents) {
    const normalized = document.filename.trim().toLowerCase();
    if (!byFilename.has(normalized)) {
      byFilename.set(normalized, document.doc_id);
    }
  }

  const dedupedNames = [...new Set(mentionNames.map((name) => name.trim()))];
  const docIds = new Set<string>();
  const unresolvedNames: string[] = [];

  for (const name of dedupedNames) {
    const resolved = byFilename.get(name.toLowerCase());
    if (resolved) {
      docIds.add(resolved);
    } else {
      unresolvedNames.push(name);
    }
  }

  return {
    docIds: [...docIds],
    unresolvedNames,
  };
}

// ============================================================================
// Chat Page
// ============================================================================

export default function ChatPage() {
  const { chatId } = useParams<{ chatId?: string }>();
  const queryClient = useQueryClient();

  const [messages, setMessages] = useState<ChatMessageType[]>([]);
  const [isLoadingMessages, setIsLoadingMessages] = useState(false);
  const [useWebSearch, setUseWebSearch] = useState(false);
  const [isDragging, setIsDragging] = useState(false);

  // Track which chatId we last loaded so we don't double-fetch on re-renders
  const loadedChatId = useRef<string | undefined>(undefined);
  const fileInputRef = useRef<HTMLInputElement>(null);

  // Documents from TanStack Query cache — shared with data library
  const { documents } = useDocuments();
  const { uploadDocuments, isUploading } = useUploadDocument();

  // Build mention triggers from cached documents
  const mentionTriggers: TriggerConfig[] = useMemo(
    () => [
      {
        char: "@",
        type: "document",
        items: documents.map((doc) => ({
          id: doc.doc_id,
          label: doc.filename,
        })),
      },
    ],
    [documents],
  );

  const picker = useMentionPicker({ triggers: mentionTriggers });

  // --- Document Upload (to backend library) ---
  const handleDocUpload = useCallback(
    async (files: File[]) => {
      if (files.length === 0) return;
      try {
        const uploaded = await uploadDocuments(files);
        toast.success(`Uploaded ${uploaded.length} document(s) to library`);
      } catch (error: any) {
        if (error?.response?.status === 409) {
          toast.error("Duplicate document(s) detected");
        } else {
          toast.error("Failed to upload document");
        }
      }
    },
    [uploadDocuments],
  );

  const handleDocFileInput = useCallback(
    (e: React.ChangeEvent<HTMLInputElement>) => {
      if (e.target.files) {
        handleDocUpload(Array.from(e.target.files));
        e.target.value = "";
      }
    },
    [handleDocUpload],
  );

  // --- Drag and Drop ---
  const handleDragOver = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragging(true);
  }, []);

  const handleDragLeave = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragging(false);
  }, []);

  const handleDrop = useCallback(
    (e: React.DragEvent) => {
      e.preventDefault();
      e.stopPropagation();
      setIsDragging(false);
      const files = Array.from(e.dataTransfer.files);
      handleDocUpload(files);
    },
    [handleDocUpload],
  );

  // Load messages whenever chatId changes
  useEffect(() => {
    if (!chatId) {
      setMessages([]);
      loadedChatId.current = undefined;
      return;
    }

    if (loadedChatId.current === chatId) return;
    loadedChatId.current = chatId;

    setIsLoadingMessages(true);
    chatApi.messages
      .list(chatId, { limit: 200 })
      .then((apiMessages) => {
        setMessages(apiMessages.map(apiMessageToLocal));
      })
      .catch((err) => {
        console.error("Failed to load chat messages:", err);
      })
      .finally(() => {
        setIsLoadingMessages(false);
      });
  }, [chatId]);

  const handleSubmit = useCallback(
    async (message: PromptInputMessage) => {
      const text = message.text ?? "";
      if (!text.trim()) return;

      const mentionPayload = picker.getApiPayload();
      const mentionNames = mentionPayload.mentions.map(
        (mention) => mention.label,
      );
      const tokenizedText = buildTokenizedMentionMessage(picker.tokens, text);

      let docsForResolution =
        queryClient.getQueryData<Document[]>(queryKeys.documents.all) ??
        documents;

      let { docIds, unresolvedNames } = resolveDocIdsFromNames(
        mentionNames,
        docsForResolution,
      );

      if (unresolvedNames.length > 0) {
        docsForResolution = await queryClient.fetchQuery({
          queryKey: queryKeys.documents.all,
          queryFn: getAllUserDocuments,
          staleTime: 5 * 60 * 1000,
        });

        ({ docIds, unresolvedNames } = resolveDocIdsFromNames(
          mentionNames,
          docsForResolution,
        ));
      }

      if (unresolvedNames.length > 0) {
        console.warn("Unresolved mention names", unresolvedNames);
      }

      const payload = {
        message: tokenizedText,
        doc_ids: docIds,
      };

      console.log("Resolved chat payload", payload);

      // Optimistically show the user message
      const optimisticUserMsg: ChatMessageType = {
        id: `optimistic-user-${Date.now()}`,
        role: "user",
        content: tokenizedText,
        createdAt: new Date().toISOString(),
      };
      setMessages((prev) => [...prev, optimisticUserMsg]);
      picker.reset();

      // TEMPORARY: chat backend invoke call disabled while validating mention resolution payload.
      // chatApi.messages.stream(resolvedChatId, payload.message, handlers, payload.doc_ids)
    },
    [documents, picker, queryClient],
  );

  return (
    <div
      className="flex flex-col h-full relative"
      onDragOver={handleDragOver}
      onDragLeave={handleDragLeave}
      onDrop={handleDrop}
    >
      {/* Hidden file input for document upload */}
      <input
        ref={fileInputRef}
        type="file"
        multiple
        className="hidden"
        onChange={handleDocFileInput}
        accept=".pdf,.txt,.doc,.docx,.md"
      />

      <Conversation className="flex-1">
        <ConversationContent className="mx-auto w-full max-w-2xl">
          {isLoadingMessages ? (
            <ConversationEmptyState
              title="Loading conversation…"
              description=""
            />
          ) : messages.length === 0 ? (
            <ConversationEmptyState
              title="What can I help you with?"
              description="Ask me anything about your projects, documents, or data."
              icon={
                <MessageSquareIcon className="size-10 text-muted-foreground/40" />
              }
            />
          ) : (
            messages.map((msg) => <ChatMessage key={msg.id} message={msg} />)
          )}
        </ConversationContent>
        <ConversationScrollButton />
      </Conversation>

      {/* Input area */}
      <div className="px-3 py-2">
        <div className="mx-auto w-full max-w-2xl">
          <MentionPicker externalPicker={picker}>
            <MentionDropdown />
            <PromptInput onSubmit={handleSubmit} className="px-4">
              <PromptInputBody className="">
                <MentionInputEditable className="px-4 min-h-9 text-sm " />
              </PromptInputBody>

              <PromptInputFooter>
                <PromptInputTools>
                  <PromptInputActionMenu>
                    <PromptInputActionMenuTrigger
                      tooltip={{ content: "Attach files" }}
                    >
                      <PaperclipIcon className="size-4" />
                    </PromptInputActionMenuTrigger>
                    <PromptInputActionMenuContent>
                      <PromptInputActionAddAttachments />
                      <DropdownMenuItem
                        onSelect={(e) => {
                          e.preventDefault();
                          fileInputRef.current?.click();
                        }}
                        disabled={isUploading}
                      >
                        <Upload className="mr-2 size-4" />
                        {isUploading ? "Uploading…" : "Upload to library"}
                      </DropdownMenuItem>
                    </PromptInputActionMenuContent>
                  </PromptInputActionMenu>

                  <PromptInputButton
                    onClick={() => setUseWebSearch(!useWebSearch)}
                    tooltip={{ content: "Search the web" }}
                    variant={useWebSearch ? "default" : "ghost"}
                  >
                    <GlobeIcon className="size-4" />
                    <span>Search</span>
                  </PromptInputButton>
                </PromptInputTools>

                <PromptInputSubmit disabled={!picker.displayValue.trim()} />
              </PromptInputFooter>
            </PromptInput>
          </MentionPicker>
          <p className="mt-1.5 text-center text-[11px] text-muted-foreground">
            Otis may produce inaccurate information. Verify important details.
          </p>
        </div>
      </div>

      {/* Drag overlay for document upload */}
      {isDragging && (
        <div className="absolute inset-0 z-100 flex items-center justify-center border-4 border-dashed border-primary bg-primary/10 pointer-events-none">
          <div className="bg-background p-8 rounded-lg shadow-lg">
            <Upload className="h-16 w-16 text-primary mx-auto mb-4" />
            <p className="text-xl font-semibold">Drop files to upload</p>
          </div>
        </div>
      )}
    </div>
  );
}
